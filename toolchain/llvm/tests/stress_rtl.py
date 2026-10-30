#!/usr/bin/env python3
"""Seeded UART/RTL stress with independent program oracles.

Every random ISA case compares every retirement and all RAM with the software
CPU, then checks separately calculated Python register/memory/CSR results.
Peripheral cases compare stable contracts because logical software ticks are
deliberately different from the Verilator clock/baud parameters.
"""
import argparse
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "software"))
from opencpu.core.peripherals import PeripheralModel  # noqa: E402
from opencpu.core.simulator import Simulator  # noqa: E402
from opencpu.core.toolchain import Toolchain  # noqa: E402


@dataclass
class Case:
    name: str
    seed: int
    source: str
    expected_ram: dict
    expected_regs: dict = field(default_factory=dict)
    expected_csrs: dict = field(default_factory=dict)
    mode: str = "halt"
    category: str = "random"
    options: dict = field(default_factory=dict)
    coverage: dict = field(default_factory=dict)


class ResourceLimit(RuntimeError):
    """An unexpected execution budget exhaustion, kept distinct from a pass."""


def signed(value):
    return value if value < 32768 else value - 65536


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def nonzero_ram(memory):
    return {str(address): value for address, value in memory.items() if value and 0 <= address < 1024}


def random_case(seed, index):
    case_seed = (seed + index * 0x9E3779B97F4A7C15) & ((1 << 64) - 1)
    rng = random.Random(case_seed)
    edges = (0, 1, 2, 15, 16, 17, 31, 127, 128, 255, 256, 32767, 32768, 65534, 65535)
    regs = {register: rng.choice(edges) if rng.randrange(2) else rng.randrange(65536)
            for register in range(1, 5)}
    memory, csrs, coverage = {}, {address: 0 for address in range(2, 8)}, Counter()
    source = [f"# seed={seed} case_seed={case_seed} index={index}", "main:",
              "    li fp, 512", "    li sp, 1024"]
    source += [f"    li r{register}, {value}" for register, value in regs.items()]
    helper_delta = rng.choice((-128, -1, 1, 127))
    source += ["first_call:", "    call helper"]
    regs[4] = (regs[4] + helper_delta) & 65535
    coverage["call"] += 1
    target = 145 if index % 5 == 0 else rng.randrange(65, 140)

    def count():
        return sum(bool(line.strip()) and not line.lstrip().startswith("#")
                   and not line.endswith(":") for line in source)

    sequence = 0
    while count() < target - 9:
        sequence += 1
        rd, rs = rng.randint(1, 4), rng.randint(1, 4)
        operation = rng.choice(("add", "sub", "mul", "and", "or", "xor", "sll", "srl",
                                "addi", "subi", "muli", "andi", "ori", "xori", "slli", "srli",
                                "li", "lui", "memory", "csr", "branch", "call", "unsigned"))
        if operation in ("add", "sub", "mul", "and", "or", "xor", "sll", "srl"):
            a, b = regs[rd], regs[rs]
            functions = {"add": lambda: a + b, "sub": lambda: a - b, "mul": lambda: a * b,
                         "and": lambda: a & b, "or": lambda: a | b, "xor": lambda: a ^ b,
                         "sll": lambda: a << b if b < 16 else 0,
                         "srl": lambda: a >> b if b < 16 else 0}
            source.append(f"    {operation} r{rd}, r{rs}")
            regs[rd] = functions[operation]() & 65535
        elif operation in ("addi", "subi", "muli", "andi", "ori", "xori", "slli", "srli"):
            amount = (rng.choice((-128, -1, 0, 1, 127)) if operation in ("addi", "subi", "muli")
                      else rng.randrange(16) if operation in ("slli", "srli") else rng.randrange(256))
            a = regs[rd]
            functions = {"addi": lambda: a + amount, "subi": lambda: a - amount,
                         "muli": lambda: a * amount, "andi": lambda: a & amount,
                         "ori": lambda: a | amount, "xori": lambda: a ^ amount,
                         "slli": lambda: a << amount, "srli": lambda: a >> amount}
            source.append(f"    {operation} r{rd}, {amount}")
            regs[rd] = functions[operation]() & 65535
        elif operation == "li":
            regs[rd] = rng.choice(edges) if rng.randrange(2) else rng.randrange(65536)
            source.append(f"    li r{rd}, {regs[rd]}")
        elif operation == "lui":
            amount = rng.randrange(256)
            source.append(f"    lui r{rd}, {amount}")
            regs[rd] = amount * 256
        elif operation == "memory":
            offset = rng.randrange(-16, 16)
            if rng.randrange(2):
                source.append(f"    sw r{rd}, {offset}(fp)")
                memory[512 + offset] = regs[rd]
                coverage["store"] += 1
            else:
                source.append(f"    lw r{rd}, {offset}(fp)")
                regs[rd] = memory.get(512 + offset, 0)
                coverage["load"] += 1
        elif operation == "csr":
            address = rng.choice((2, 3, 4, 5, 6, 7, 8, 31))
            if rng.randrange(2):
                source.append(f"    csrw r{rd}, {address}")
                if address < 8:
                    csrs[address] = regs[rd]
            else:
                source.append(f"    csrr r{rd}, {address}")
                regs[rd] = csrs.get(address, 0)
        elif operation == "call":
            source.append("    call helper")
            regs[4] = (regs[4] + helper_delta) & 65535
        elif operation == "unsigned" and count() < target - 23:
            a, b = rng.sample(range(1, 5), 2)
            yes = regs[a] < regs[b]
            false_delta, true_delta = rng.randrange(-128, 128), rng.randrange(-128, 128)
            source += ["    li ra, 32768", f"    xor r{a}, ra", f"    xor r{b}, ra",
                       f"    blt r{a}, r{b}, unsigned_yes_{sequence}",
                       f"    xor r{a}, ra", f"    xor r{b}, ra", f"    addi r{rd}, {false_delta}",
                       f"    j unsigned_end_{sequence}", f"unsigned_yes_{sequence}:",
                       f"    xor r{a}, ra", f"    xor r{b}, ra", f"    addi r{rd}, {true_delta}",
                       f"unsigned_end_{sequence}:"]
            regs[rd] = (regs[rd] + (true_delta if yes else false_delta)) & 65535
            coverage["unsigned_true" if yes else "unsigned_false"] += 1
        elif operation == "branch" and count() < target - 16:
            kind = rng.choice(("beq", "blt"))
            yes = regs[rd] == regs[rs] if kind == "beq" else signed(regs[rd]) < signed(regs[rs])
            false_delta, true_delta = rng.randrange(-128, 128), rng.randrange(-128, 128)
            distance = 23 if count() < target - 39 and rng.randrange(3) == 0 else 0
            source += [f"    {kind} r{rd}, r{rs}, branch_yes_{sequence}",
                       f"    addi r{rd}, {false_delta}", f"    j branch_end_{sequence}"]
            source += ["    nop"] * distance
            source += [f"branch_yes_{sequence}:", f"    addi r{rd}, {true_delta}", f"branch_end_{sequence}:"]
            regs[rd] = (regs[rd] + (true_delta if yes else false_delta)) & 65535
            coverage["far_branch" if distance else "short_branch"] += 1
            coverage["branch_true" if yes else "branch_false"] += 1
        else:
            source.append("    li zero, 65535")
            coverage["zero_write"] += 1
        coverage[operation] += 1

    for register in range(1, 5):
        source.append(f"    sw r{register}, {register - 1}(zero)")
        memory[register - 1] = regs[register]
    mode = ("illegal" if index % 25 == 22 else "fetch" if index % 25 == 23
            else "timeout" if index % 25 == 24 else "halt")
    source.append("terminal:")
    if mode == "illegal":
        instruction = rng.choice((14, 15, 0x8000, 0x002A))
        source.append(f"    .word {instruction}")
    elif mode == "fetch":
        source.append("    j 1024")
    elif mode == "timeout":
        source.append("    j terminal")
    else:
        source.append("    halt")
    source += ["helper:", f"    addi r4, {helper_delta}", "    ret"]
    expected_regs = {0: 0, **regs, 5: 512, 7: 1024}
    coverage["source_instructions"] = count()
    return Case(f"random-{index:05d}", case_seed, "\n".join(source) + "\n", memory,
                expected_regs, csrs, mode, coverage=dict(coverage))


def tx_case(seed, index, overflow):
    rng = random.Random(seed + 100000 + index)
    values = rng.sample(range(256), 24) if overflow else [0, 255] + [rng.randrange(256) for _ in range(46)]
    lines = ["li r4, 0xff40", "li r1, 56", "sw r1, 2(r4)"]
    for number, value in enumerate(values):
        if not overflow:
            lines += [f"ready_{number}:", "lw r2, 1(r4)", "andi r2, 2",
                      f"beq r2, zero, ready_{number}"]
        lines += [f"li r1, {value}", "sw r1, 0(r4)"]
    lines += ["lw r2, 2(r4)", "sw r2, 0(zero)"]
    if overflow:
        lines += ["li r1, 16", "sw r1, 2(r4)", "lw r2, 2(r4)", "sw r2, 1(zero)"]
    else:
        lines += ["drain:", "lw r2, 1(r4)", "andi r2, 4", "beq r2, zero, done", "j drain", "done:"]
    lines += ["halt"]
    return Case(f"uart-{'overflow' if overflow else 'burst'}-{index}", seed + 100000 + index,
                "\n".join(lines) + "\n", {0: 16 if overflow else 0, 1: 0},
                category="uart-overflow" if overflow else "uart-burst",
                options={"tx_bytes": values, "max_cycles": 40000})


def rx_case(seed, index):
    rng = random.Random(seed + 200000 + index)
    data = [rng.randrange(256) for _ in range(17)]
    source = """
        li r4, 0xff40
        la r1, handler
        csrw r1, 2
        csrw zero, 5
        csrw zero, 6
    wait_overflow:
        lw r1, 2(r4)
        andi r1, 8
        beq r1, zero, wait_overflow
        li r1, 2
        csrw r1, 5
        li r1, 8
        csrw r1, 6
    wait_done:
        li r1, 1
        beq r5, r1, done
        j wait_done
    done:
        csrr r1, 3
        sw r1, 4(zero)
        csrr r1, 6
        sw r1, 5(zero)
        halt
    handler:
        li r2, 0
        li r3, 0
    consume:
        lw r1, 1(r4)
        andi r1, 1
        beq r1, zero, consumed
        lw r1, 0(r4)
        add r2, r1
        addi r3, 1
        j consume
    consumed:
        sw r2, 0(zero)
        sw r3, 1(zero)
        lw r1, 2(r4)
        sw r1, 2(zero)
        li r1, 8
        sw r1, 2(r4)
        lw r1, 2(r4)
        sw r1, 3(zero)
        li r5, 1
        mret
    """
    return Case(f"uart-rx-coalesce-{index}", seed + 200000 + index, source,
                {0: sum(data[:16]), 1: 16, 2: 8, 3: 0, 4: 1, 5: 136},
                category="uart-rx", options={"rx_bytes": data, "max_cycles": 15000})


def timer_case(seed, index, periodic):
    period = (1, 7, 40, 255)[index % 4]
    setup = f"li r1, {period}\nsw r1, 0(r4)\nsw zero, 1(r4)\n"
    if periodic:
        setup += """li r1, 3
        sw r1, 2(r4)
        li r3, 100
    delay:
        addi r3, -1
        blt zero, r3, delay
        sw zero, 2(r4)
        nop
        nop
        """
    else:
        setup += "li r1, 1\nsw r1, 2(r4)\n"
    source = """li r4, 0xff50
        la r1, handler
        csrw r1, 2
        csrw zero, 6
        li r1, 1
        csrw r1, 5
    """ + setup + """
        li r1, 8
        csrw r1, 6
    wait:
        li r2, 1
        beq r5, r2, done
        j wait
    done:
        sw r5, 2(zero)
        csrr r1, 3
        sw r1, 3(zero)
        csrr r1, 6
        sw r1, 5(zero)
        halt
    handler:
        lw r1, 5(r4)
        sw r1, 0(zero)
        li r1, 1
        sw r1, 5(r4)
        lw r1, 5(r4)
        sw r1, 1(zero)
        lw r1, 2(r4)
        sw r1, 4(zero)
        li r5, 1
        mret
    """
    return Case(f"timer-{'periodic-coalesce' if periodic else 'oneshot'}-{index}", seed + index,
                source, {0: 1, 1: 0, 2: 1, 3: 0, 4: 0, 5: 136},
                category="timer", options={"max_cycles": 10000})


def execute(case, executable, output):
    directory = output / "cases" / case.name
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "failure.json").unlink(missing_ok=True)
    (directory / "program.asm").write_text(case.source)
    (directory / "case.json").write_text(json.dumps({"name": case.name, "case_seed": case.seed,
        "category": case.category, "mode": case.mode, "expected_ram": case.expected_ram,
        "expected_registers": case.expected_regs, "expected_csrs": case.expected_csrs,
        "options": case.options}, indent=2))
    build = Toolchain().assemble(case.source)
    image, retirement = directory / "program.bin", directory / "retire.jsonl"
    image.write_text(build.binary)
    command = [str(executable), "--image", str(image), "--retire-log", str(retirement),
               "--max-cycles", str(case.options.get("max_cycles", 3000 if case.mode == "timeout" else 10000))]
    for byte in case.options.get("rx_bytes", []):
        command += ["--rx-byte", str(byte)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    (directory / "stdout.txt").write_text(result.stdout)
    (directory / "stderr.txt").write_text(result.stderr)
    expected_exit = 3 if case.mode == "timeout" else 2 if case.mode in ("illegal", "fetch") else 0
    if result.returncode == 3 and expected_exit != 3:
        raise ResourceLimit(f"RTL reached its cycle budget while expecting exit {expected_exit}")
    require(result.returncode == expected_exit, f"RTL exit {result.returncode}, expected {expected_exit}: {result.stderr}")
    state = json.loads(result.stdout)
    (directory / "rtl.json").write_text(json.dumps(state, indent=2))
    records = [json.loads(line) for line in retirement.read_text().splitlines()]
    require(state["retired"] == len(records), "RTL retirement count disagrees with trace")
    devices = PeripheralModel(uart_frame_ticks=5000 if case.category == "uart-overflow" else 10)
    model = Simulator(history_limit=0, peripherals=devices)
    model.inst_mem = build.words
    compared = 0
    if case.category == "random":
        for index, actual in enumerate(records):
            pc = model.pc
            instruction = build.words[pc] if pc < len(build.words) else 10
            require(model.step(), f"software stopped before RTL retirement {index}")
            expected = {"pc": pc, "inst": instruction, "next_pc": model.pc,
                        "registers": model.registers, "csrs": [model.read_csr(a) for a in range(2, 8)],
                        "irq": 0, "irq_ack": 0, "in_interrupt": 0}
            for key, value in expected.items():
                require(actual[key] == value, f"retirement {index}, pc={pc}, {key}: RTL={actual[key]} software={value}")
            compared += 1
        if case.mode in ("illegal", "fetch"):
            require(not model.step() and model.faulted, "expected software fault after matching retirements")
        require(model.registers == state["registers"], "final software/RTL registers differ")
        require(model.pc == state["pc"], "final software/RTL PC differs")
        require([model.read_csr(a) for a in range(2, 8)] == state["csrs"], "final software/RTL CSRs differ")
        require(nonzero_ram(model.data_mem) == state["memory"], "complete software/RTL RAM differs")
        for register, expected in case.expected_regs.items():
            require(state["registers"][register] == expected, f"independent r{register} expected {expected}")
        for address, expected in case.expected_csrs.items():
            require(state["csrs"][address - 2] == expected, f"independent CSR{address} expected {expected}")
        if case.mode == "halt":
            require(model.halted and state["halted"], "expected HALT")
        elif case.mode == "illegal":
            require(state["fault_code"] == model.fault_code == 1, "wrong illegal fault code")
            require(state["fault_pc"] == model.fault_pc == build.labels["terminal"], "wrong illegal fault PC")
            require(state["fault_inst"] == model.fault_inst == build.words[build.labels["terminal"]], "wrong illegal word")
        elif case.mode == "fetch":
            require(state["fault_code"] == model.fault_code == 2, "wrong fetch fault code")
            require(state["fault_pc"] == model.fault_pc == 1024, "wrong fetch fault address")
        else:
            require(not state["halted"] and not state["faulted"], "timeout unexpectedly stopped")
    else:
        if case.category == "uart-rx":
            model.inject_uart(bytes(case.options["rx_bytes"]))
        model.run(max_steps=100000)
        require(model.halted and not model.faulted, f"software peripheral program failed: {model.stop_reason}")
        if model.peripherals.uart_busy:
            model.advance_ticks((model.peripherals.fifo_depth + 1) * model.peripherals.uart_frame_ticks)
        require(nonzero_ram(model.data_mem) == state["memory"], "software/RTL stable peripheral RAM differs")
        if case.category.startswith("uart-") and case.category != "uart-rx":
            expected_tx = case.options["tx_bytes"]
            actual_tx = state["uart_tx"]
            software_tx = list(model.peripherals.uart_output)
            if case.category == "uart-burst":
                require(actual_tx == expected_tx == software_tx, "polling TX burst lost/reordered bytes")
            else:
                # FIFO capacity excludes the active frame. Timing may allow
                # later writes; accepted bytes must preserve their input order.
                require(actual_tx[:17] == expected_tx[:17], "overflow damaged previously accepted FIFO bytes")
                require(software_tx == expected_tx[:17], "conservative software burst did not saturate the FIFO")
                indices = [expected_tx.index(byte) for byte in actual_tx]
                require(indices == sorted(set(indices)), "overflow duplicated or reordered TX bytes")
                require(17 <= len(actual_tx) < len(expected_tx), "overflow case did not lose excess new bytes")
        elif case.category in ("uart-rx", "timer"):
            cause = 1 if case.category == "uart-rx" else 0
            require(state["irq_entries"] == 1, "masked/coalesced events must lead to exactly one ISR")
            require(state["csrs"][1] == model.read_csr(3) == cause, "wrong peripheral IRQ source")
            require(state["csrs"][4] == model.read_csr(6) == 136, "MRET did not restore MIE/MPIE")
            require(not state["in_interrupt"] and not model.in_interrupt and model.pending_interrupts == 0,
                    "ISR/pending did not finish")
    require(state["memory"] == nonzero_ram(case.expected_ram), "RTL RAM disagrees with independent generator oracle")
    require(nonzero_ram(model.data_mem) == nonzero_ram(case.expected_ram), "software RAM disagrees with independent generator oracle")
    (directory / "software.json").write_text(json.dumps(model.snapshot(), indent=2))
    return {"words": len(build.words), "rtl_retired": state["retired"], "retirements_compared": compared,
            "far_call": build.labels.get("helper", 0) - build.labels.get("first_call", 0) > 128,
            "rtl_cycles": state["cycles"], "coverage": case.coverage}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=lambda value: int(value, 0), default=20261030)
    parser.add_argument("--cases", type=int, default=250)
    parser.add_argument("--case", action="append", help="replay only matching case names")
    parser.add_argument("--output", type=Path, default=ROOT / "build/stress/latest/rtl")
    parser.add_argument("--executable", type=Path, default=Path(os.environ.get("OPENCPU_SIM", ROOT / "hardware/common/tb/build/obj_dir/Vtb_soc")))
    args = parser.parse_args(argv)
    if args.cases <= 0:
        parser.error("--cases must be positive")
    executable = args.executable.expanduser().resolve()
    if not executable.is_file():
        parser.error(f"Verilator executable is missing: {executable}; run make -C hardware build")
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    start = time.monotonic()
    report = {"suite": "rtl", "seed": args.seed, "requested_random_cases": args.cases,
              "started_at": datetime.now(timezone.utc).isoformat(), "executable": str(executable),
              "passed": 0, "failed": 0, "resource_limits": 0, "expected_timeouts": 0,
              "expected_faults": 0, "validated_total": 0, "cases_total": 0,
              "retirements_compared": 0, "uploaded_words": 0, "far_call_cases": 0,
              "source_instruction_bounds": {},
              "coverage": {}, "case_counts": {}, "failures": []}
    cases = [random_case(args.seed, index) for index in range(args.cases)]
    cases += [tx_case(args.seed, index, overflow) for index in range(3) for overflow in (False, True)]
    cases += [rx_case(args.seed, index) for index in range(3)]
    cases += [timer_case(args.seed, index, False) for index in range(4)]
    cases += [timer_case(args.seed, index, True) for index in (1, 2)]
    if args.case:
        cases = [case for case in cases if case.name in args.case]
        if {case.name for case in cases} != set(args.case):
            parser.error("--case contains a name not generated by this seed/--cases")
    sizes = [case.coverage["source_instructions"] for case in cases if case.category == "random"]
    if sizes:
        report["source_instruction_bounds"] = {"minimum": min(sizes), "maximum": max(sizes)}
    counts, coverage = Counter(), Counter()
    with (output / "results.jsonl").open("w") as results:
        for number, case in enumerate(cases, 1):
            report["cases_total"] += 1
            counts[case.category] += 1
            case_start = time.monotonic()
            row = {"case": case.name, "case_seed": case.seed, "category": case.category, "mode": case.mode}
            try:
                detail = execute(case, executable, output)
                row.update(detail)
                report["validated_total"] += 1
                if case.mode == "timeout":
                    row["status"] = "expected_timeout"
                    report["expected_timeouts"] += 1
                else:
                    row["status"] = "passed"
                    report["passed"] += 1
                    report["expected_faults"] += int(case.mode in ("illegal", "fetch"))
                report["retirements_compared"] += detail["retirements_compared"]
                report["uploaded_words"] += detail["words"]
                report["far_call_cases"] += int(detail["far_call"])
                coverage.update(detail["coverage"])
            except Exception as error:
                resource = isinstance(error, (subprocess.TimeoutExpired, ResourceLimit)) or (isinstance(error, ValueError) and "ROM" in str(error))
                row["status"] = "resource_limit" if resource else "failed"
                row["error"] = f"{type(error).__name__}: {error}"
                report["resource_limits" if resource else "failed"] += 1
                report["failures"].append(dict(row))
                (output / "cases" / case.name / "failure.json").write_text(json.dumps(row, indent=2))
                print(f"FAIL {case.name}: {row['error']}", flush=True)
            row["duration_seconds"] = round(time.monotonic() - case_start, 6)
            results.write(json.dumps(row) + "\n")
            results.flush()
            if number % 25 == 0:
                print(f"RTL stress: {number}/{len(cases)} cases, {report['failed']} failures", flush=True)
    report["coverage"] = dict(coverage)
    report["case_counts"] = dict(counts)
    report["duration_seconds"] = round(time.monotonic() - start, 3)
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 1 if report["failed"] or report["resource_limits"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
