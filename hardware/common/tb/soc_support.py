"""Shared real-SoC driver and architectural comparison assertions."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

REPOSITORY = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY / "software"))
from opencpu.core.simulator import Simulator
from opencpu.core.toolchain import Toolchain

ROM_DEPTH = RAM_DEPTH = 1024
CSR_ADDRESSES = (2, 3, 4, 5, 6, 7)


class SocDriverMixin:
    @classmethod
    def setUpClass(cls):
        cls.executable = Path(os.environ.get(
            "OPENCPU_SIM", str(Path(__file__).resolve().parent / "build/obj_dir/Vtb_soc")
        )).expanduser().resolve()
        if not cls.executable.is_file():
            raise RuntimeError(
                f"Verilator executable is missing: {cls.executable}; "
                "build it with hardware/common/tb/Makefile before running tests"
            )

    def run_image(self, words, *, expected_code=0, max_cycles=10000,
                  rx_bytes=(), buttons=0xA, switches=0x5):
        """Run a new SoC process and keep no generated files in the source tree."""
        with tempfile.TemporaryDirectory(prefix="opencpu-soc-") as directory:
            directory = Path(directory)
            image = directory / "program.bin"
            retirement = directory / "retirement.jsonl"
            image.write_text("".join(f"{word:016b}\n" for word in words), encoding="ascii")
            command = [
                str(self.executable), "--image", str(image),
                "--max-cycles", str(max_cycles), "--retire-log", str(retirement),
                "--buttons", str(buttons), "--switches", str(switches),
            ]
            for byte in rx_bytes:
                command.extend(("--rx-byte", str(byte)))
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            diagnostic = (
                f"command: {' '.join(command)}\nreturn code: {result.returncode}"
                f"\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
            )
            self.assertEqual(result.returncode, expected_code, diagnostic)
            try:
                state = json.loads(result.stdout)
            except json.JSONDecodeError as error:
                self.fail(f"testbench stdout must be a single JSON object: {error}\n{diagnostic}")
            self.assertIsInstance(state, dict, diagnostic)
            self.assertTrue(retirement.is_file(), "testbench did not create the requested retire log")
            records = [json.loads(line) for line in retirement.read_text().splitlines() if line.strip()]
            self.assertEqual(state["retired"], len(records), diagnostic)
            self.assertEqual(len(state["registers"]), 8)
            self.assertEqual(len(state["csrs"]), 6)
            self.assertEqual(state["registers"][0], 0, "zero register must stay hardwired to zero")
            return state, records

    def run_assembly(self, source, **options):
        build = Toolchain().assemble(source)
        state, records = self.run_image(build.words, **options)
        return build, state, records

    @staticmethod
    def memory(state, address):
        return state["memory"].get(str(address), 0)

    def assert_matches_reference(self, build):
        """Compare every architectural retirement, excluding clock-count CSRs."""
        state, records = self.run_image(build.words)
        reference = Simulator(rom_depth=ROM_DEPTH, ram_depth=RAM_DEPTH)
        reference.inst_mem = build.words
        for index, actual in enumerate(records):
            context = f"retirement {index}, pc={reference.pc}"
            old_pc = reference.pc
            instruction = build.words[old_pc] if old_pc < len(build.words) else 10
            self.assertTrue(reference.step(), context)
            expected = {
                "pc": old_pc,
                "inst": instruction,
                "next_pc": reference.pc,
                "irq": False,
                "irq_ack": 0,
                "registers": reference.registers,
                "csrs": [reference.read_csr(address) for address in CSR_ADDRESSES],
                "in_interrupt": reference.in_interrupt,
            }
            for key, value in expected.items():
                self.assertEqual(actual[key], value, f"{context}: {key}")
        self.assertTrue(reference.halted, "RTL retired fewer instructions than the reference program")
        self.assertTrue(state["halted"])
        self.assertFalse(state["faulted"])
        self.assertFalse(state["in_interrupt"])
        self.assertEqual(state["irq_entries"], 0)
        self.assertEqual(state["pc"], reference.pc)
        self.assertEqual(state["registers"], reference.registers)
        self.assertEqual(state["csrs"], [reference.read_csr(address) for address in CSR_ADDRESSES])
        self.assertEqual(
            state["memory"],
            {str(address): value for address, value in reference.data_mem.items() if value},
        )
        return state

    def assert_interrupt_return(self, state, records, *, cause):
        self.assertTrue(state["halted"])
        self.assertFalse(state["faulted"])
        self.assertFalse(state["in_interrupt"])
        self.assertEqual(state["irq_entries"], 1)
        entries = [record for record in records if record["irq"]]
        returns = [record for record in records if record["inst"] == 11]
        self.assertEqual(len(entries), 1)
        self.assertEqual(len(returns), 1)
        entry, returning = entries[0], returns[0]
        self.assertEqual(entry["irq_ack"], 1 << cause)
        self.assertEqual(entry["next_pc"], entry["csrs"][0])
        self.assertEqual(entry["csrs"][1], cause)
        self.assertTrue(entry["in_interrupt"])
        self.assertEqual(entry["csrs"][4] & 0x88, 0x80)
        self.assertEqual(returning["next_pc"], returning["csrs"][2])
        self.assertFalse(returning["in_interrupt"])
        self.assertEqual(returning["csrs"][4] & 0x88, 0x88)
        self.assertEqual(state["csrs"][1], cause)
        self.assertEqual(state["csrs"][4] & 0x88, 0x88)
