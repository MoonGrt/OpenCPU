"""The shared command-line application; no GUI dependencies."""
import argparse
from contextlib import nullcontext
from dataclasses import replace
import json
from pathlib import Path
import sys

from .core.disassembler import Disassembler
from .core.image import ROM_WORDS, format_binary, parse_binary
from .core.isa import OPCODES, REGISTER_NAMES
from .core.simulator import Simulator
from .core.peripherals import PeripheralModel
from .core.toolchain import Toolchain


def _output(text, path):
    if path:
        path.write_text(text, encoding="utf-8")
    else:
        print(text, end="" if text.endswith("\n") else "\n")


def _compile(args):
    toolchain = Toolchain()
    if args.project:
        from .core.compiler.llvm import CProject
        if args.input:
            raise ValueError("Use either --project or source inputs, not both")
        if args.backend not in (None, "llvm") or args.language not in ("auto", "c"):
            raise ValueError("C projects require the LLVM C backend")
        project = CProject.load(args.project)
        project = replace(project, include_dirs=project.include_dirs + tuple(path.expanduser().resolve() for path in args.include_dirs),
                          defines=project.defines + tuple(args.defines))
        return toolchain.compile_project(project, llvm_bin_dir=args.llvm_bin_dir)
    if not args.input:
        raise ValueError("compile requires source inputs or --project")
    first = args.input[0]
    backend = args.backend or ("llvm" if args.language != "auto" or first.suffix.lower() in (".c", ".ll") else "simple")
    if len(args.input) > 1:
        from .core.compiler.llvm import CProject
        if backend != "llvm" or args.language == "llvm-ir":
            raise ValueError("Multiple source inputs require the LLVM C backend")
        project = CProject(sources=tuple(args.input), include_dirs=tuple(args.include_dirs), defines=tuple(args.defines))
        return toolchain.compile_project(project, llvm_bin_dir=args.llvm_bin_dir)
    return toolchain.compile(
        first.read_text(encoding="utf-8"), backend=backend, source_name=str(first),
        language=args.language, include_dirs=args.include_dirs, defines=args.defines,
        llvm_bin_dir=args.llvm_bin_dir,
    )


def _run_program(args, source):
    if not 0 <= args.entry < 1024:
        raise ValueError("entry must be a word address in 0..1023")
    if any(not 0 <= address < 1024 for address in args.breakpoints):
        raise ValueError("breakpoints must be ROM word addresses in 0..1023")
    devices = PeripheralModel(
        buttons=args.buttons, switches=args.switches,
        uart_frame_ticks=args.uart_frame_ticks,
        enable_uart=not args.disable_uart, enable_timer=not args.disable_timer,
        enable_display=not args.disable_display,
    )
    model = Simulator(args.entry, history_limit=0, peripherals=devices)
    model.inst_mem = parse_binary(source)
    if args.uart_rx is not None:
        model.inject_uart(args.uart_rx.encode("utf-8"))
    elif args.uart_rx_hex is not None:
        model.inject_uart(bytes.fromhex(args.uart_rx_hex))
    if args.trace and args.trace.resolve() == args.input.resolve():
        raise ValueError("trace output must differ from the input image")
    if args.drain_ticks is not None and args.drain_ticks < 0:
        raise ValueError("drain ticks must be nonnegative")
    output = args.trace.open("w", encoding="utf-8") if args.trace else nullcontext(None)
    with output as trace_file:
        trace = ((lambda record: trace_file.write(json.dumps(record) + "\n"))
                 if trace_file is not None else None)
        model.run(args.max_steps, breakpoints=args.breakpoints, trace=trace)
    if args.drain_ticks is not None:
        model.advance_ticks(args.drain_ticks)
    elif model.halted:
        # HALT stops the CPU. The UART completes already queued frames.
        uart = devices.snapshot(include_output=False)["uart"]
        if uart["busy"]:
            remaining = uart["remaining_ticks"] + uart["tx_count"] * uart["frame_ticks"]
            model.advance_ticks(remaining)
    print(json.dumps({
        "isa": "OpenCPU v2", "pc": model.pc,
        "halted": model.halted, "faulted": model.faulted,
        "fault_reason": model.fault_reason,
        "fault_pc": model.fault_pc, "fault_inst": model.fault_inst,
        "fault_code": model.fault_code,
        "stop_reason": model.stop_reason, "breakpoint_hit": model.breakpoint_hit,
        "limit_reached": model.limit_reached,
        "instructions_retired": model.instructions_retired,
        "ticks": devices.ticks, "cycle": model.cycle,
        "pending_interrupts": model.pending_interrupts,
        "registers": dict(zip(REGISTER_NAMES, model.registers)),
        "memory": {str(address): value for address, value in sorted(model.data_mem.items())},
        "peripherals": devices.snapshot(),
        "uart_tx": list(devices.uart_output),
        "uart_tx_text": bytes(devices.uart_output).decode("utf-8", errors="replace"),
    }, indent=2))
    return 2 if model.faulted else 3 if model.limit_reached else 0


def main(argv=None):
    arguments = argparse.ArgumentParser(description="Assemble, disassemble, compile and run OpenCPU ISA v2.")
    commands = arguments.add_subparsers(dest="command", required=True)
    for name in ("assemble", "disassemble", "compile", "run"):
        command = commands.add_parser(name)
        if name == "compile":
            command.add_argument("input", type=Path, nargs="*", help="one .oc/.ll source, or one or more .c files")
        else:
            command.add_argument("input", type=Path)
        if name != "run":
            command.add_argument("-o", "--output", type=Path)
        if name in ("assemble", "compile"):
            command.add_argument("--pad-rom", action="store_true", help="fill the 1024-word ROM image with trailing HALTs")
        if name == "compile":
            command.add_argument("--assembly", type=Path, help="also save generated assembly")
            command.add_argument("--backend", choices=("simple", "llvm"),
                                 help="default: LLVM for .c/.ll, simple for other source files")
            command.add_argument("--language", choices=("auto", "c", "llvm-ir"), default="auto")
            command.add_argument("--project", type=Path, help="build a version 1 .opencpu.json C project")
            command.add_argument("-I", dest="include_dirs", type=Path, action="append", default=[], help="C header directory (repeatable)")
            command.add_argument("-D", dest="defines", action="append", default=[], help="C definition NAME or NAME=value (repeatable)")
            command.add_argument("--llvm-bin-dir", type=Path, help="directory containing OpenCPU LLVM 23.1.4 tools")
        if name == "run":
            command.add_argument("--entry", type=lambda value: int(value, 0), default=0)
            command.add_argument("--max-steps", type=int, default=Simulator.DEFAULT_MAX_STEPS)
            command.add_argument("--buttons", type=lambda value: int(value, 0), default=0,
                                 help="four-bit simulated button input")
            command.add_argument("--switches", type=lambda value: int(value, 0), default=0,
                                 help="four-bit simulated switch input")
            incoming = command.add_mutually_exclusive_group()
            incoming.add_argument("--uart-rx", help="inject a burst of UTF-8 bytes into simulated RX")
            incoming.add_argument("--uart-rx-hex", help="inject hexadecimal bytes, e.g. '41 00 ff'")
            command.add_argument("--uart-frame-ticks", type=int, default=10,
                                 help="abstract simulation ticks per UART frame (default: 10)")
            command.add_argument("--drain-ticks", type=int,
                                 help="advance devices after execution; default: drain TX after HALT")
            command.add_argument("--disable-uart", action="store_true")
            command.add_argument("--disable-timer", action="store_true")
            command.add_argument("--disable-display", action="store_true")
            command.add_argument("--breakpoint", dest="breakpoints", type=lambda value: int(value, 0),
                                 action="append", default=[], help="stop before a PC word address (repeatable)")
            command.add_argument("--trace", type=Path, help="write retired instructions as JSON Lines")
    args = arguments.parse_args(argv)
    try:
        source = args.input.read_text(encoding="utf-8") if args.command != "compile" else None
        if args.command == "disassemble":
            parse_binary(source)
            text = Disassembler().disassemble(source)
            _output(text + ("\n" if text else ""), args.output)
        elif args.command in ("assemble", "compile"):
            toolchain = Toolchain()
            result = _compile(args) if args.command == "compile" else toolchain.assemble(source)
            words = list(result.words)
            if args.pad_rom:
                words += [OPCODES["halt"]] * (ROM_WORDS - len(words))
            if args.command == "compile" and args.assembly:
                _output(result.assembly, args.assembly)
            _output(format_binary(words), args.output)
        else:
            return _run_program(args, source)
    except (OSError, ValueError, TypeError) as error:
        print(f"opencpu: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
