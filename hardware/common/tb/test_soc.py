#!/usr/bin/env python3
"""Self-check the already-built, pin-level UART/SoC Verilator testbench.

The Makefile builds the executable before running this file. These tests use
only Python's standard library and the Qt-free software reference model.
OPENCPU_SIM may select an executable built in a different build directory.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY / "software"))

from opencpu.core.simulator import Simulator  # noqa: E402
from opencpu.core.toolchain import Toolchain  # noqa: E402


ROM_DEPTH = RAM_DEPTH = 1024
CSR_ADDRESSES = (2, 3, 4, 5, 6, 7)


class SocTests(unittest.TestCase):
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

    def test_current_examples_match_reference_at_every_retirement(self):
        examples = REPOSITORY / "software/examples"
        expected_variables = {
            "loops.oc": {"X": 15, "Y": 11, "i": 3},
            "functions.oc": {"result": 120},
        }
        for name in ("isa.asm", "loops.oc", "functions.oc"):
            with self.subTest(example=name):
                source = (examples / name).read_text()
                build = Toolchain().assemble(source) if name.endswith(".asm") else Toolchain().compile(source)
                state = self.assert_matches_reference(build)
                if name == "isa.asm":
                    self.assertEqual(self.memory(state, 0), 0xABCC)
                for variable, expected in expected_variables.get(name, {}).items():
                    self.assertEqual(self.memory(state, 1022 + build.variable_offsets[variable]), expected)

    def test_alu_signed_addressing_branches_and_csrs_match_reference(self):
        build = Toolchain().assemble("""
            li r1, 0xffff
            addi r1, 1
            subi r1, 1
            muli r1, -128
            li r2, 3
            mul r1, r2
            add r1, r2
            sub r1, r2
            li r3, 255
            and r1, r3
            or r1, r3
            xor r1, r3
            li r1, 1
            sll r1, r2
            srl r1, r2
            slli r1, 15
            srli r1, 15
            ori r1, 128
            andi r1, 129
            xori r1, 129
            sw r1, 4(zero)
            li r2, 16
            li r1, 1
            sll r1, r2
            li r1, 0xffff
            srl r1, r2
            li zero, 0xffff
            add zero, r3
            li r1, 0x1234
            csrw r1, 7
            csrr r2, 7
            sw r2, 6(zero)
            csrw r1, 2
            csrw r1, 3
            csrw r1, 4
            li r1, 165
            csrw r1, 5
            li r1, 128
            csrw r1, 6
            csrr r3, 2
            csrw r1, 31
            csrr r4, 31
            rc
            li sp, 32
            li r1, 0xbeef
            sw r1, -16(sp)
            lw r2, -16(sp)
            sw r2, 15(sp)
            li sp, 1
            sw r2, -1(sp)
            li sp, 1024
            sw r2, 0(sp)
            lw r3, 0(sp)
            li r1, -1
            blt r1, zero, negative
            .word 14
        negative:
            li r2, 3
        loop:
            addi r2, -1
            blt zero, r2, loop
            beq r2, zero, taken
            .word 15
        taken:
            j finish
            li r2, 99
            sw r2, 8(zero)
        finish:
            halt
        """)
        state = self.assert_matches_reference(build)
        for address in (0, 16, 47):
            self.assertEqual(self.memory(state, address), 0xBEEF)
        self.assertEqual(self.memory(state, 6), 0x1234)
        self.assertEqual(self.memory(state, 8), 0, "redirect must squash younger stores")

    def test_gpio_display_and_uart_transmit(self):
        _, state, _ = self.run_assembly("""
            li r4, 0xff00
            li r1, 6
            sw r1, 0(r4)
            lw r2, 0(r4)
            sw r2, 0(zero)
            addi r4, 16
            lw r2, 0(r4)
            sw r2, 1(zero)
            addi r4, 16
            lw r2, 0(r4)
            sw r2, 2(zero)
            addi r4, 16
            li r1, 0x1234
            sw r1, 0(r4)
            lw r2, 0(r4)
            sw r2, 3(zero)
            addi r4, 16
            li r1, 79
            sw r1, 0(r4)
            li r1, 75
            sw r1, 0(r4)
        wait_tx:
            lw r1, 1(r4)
            andi r1, 4
            beq r1, zero, done
            j wait_tx
        done:
            halt
        """, buttons=3, switches=12)
        self.assertEqual([self.memory(state, address) for address in range(4)], [6, 3, 12, 0x1234])
        self.assertEqual(state["led"], 9, "board LED pins are active low")
        self.assertEqual(state["uart_tx"], [79, 75])
        self.assertEqual(state["display_value"], 0x1234)
        digit_masks = (14, 13, 11, 7)
        self.assertIn(state["digit_enable"], digit_masks)
        digit = digit_masks.index(state["digit_enable"])
        glyphs = (0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07,
                  0x7F, 0x6F, 0x77, 0x7C, 0x39, 0x5E, 0x79, 0x71)
        nibble = (0x1234 >> (digit * 4)) & 15
        self.assertEqual(state["segments"], 0x80 | (~glyphs[nibble] & 0x7F))

    def test_uart_transmit_finishes_after_cpu_halt(self):
        _, state, records = self.run_assembly("""
            li r4, 0xff40
            sw zero, 0(r4)
            li r1, 255
            sw r1, 0(r4)
            halt
        """)
        self.assertTrue(state["halted"])
        self.assertFalse(state["faulted"])
        self.assertEqual(state["uart_tx"], [0, 255])
        self.assertEqual(records[-1]["inst"], 10, "TX drain must not retire instructions after HALT")

    def test_runtime_uart_receive_interrupt_and_mret(self):
        build, state, records = self.run_assembly("""
            li r4, 0xff40
            la r1, handler
            csrw r1, 2
            li r1, 2
            csrw r1, 5
            li r1, 8
            csrw r1, 6
        wait_rx:
            li r2, 1
            beq r5, r2, done
            j wait_rx
        done:
            sw r5, 2(zero)
            csrr r1, 3
            sw r1, 3(zero)
            csrr r1, 6
            sw r1, 4(zero)
            halt
        handler:
            lw r1, 0(r4)
            sw r1, 0(zero)
            csrr r2, 4
            sw r2, 1(zero)
            addi r5, 1
            mret
        """, rx_bytes=(0xA5,))
        self.assert_interrupt_return(state, records, cause=1)
        self.assertEqual(state["csrs"][0], build.labels["handler"])
        self.assertEqual(self.memory(state, 0), 0xA5)
        self.assertEqual(self.memory(state, 1), state["csrs"][2])
        self.assertEqual(self.memory(state, 2), 1)
        self.assertEqual(self.memory(state, 3), 1)
        self.assertEqual(self.memory(state, 4), 0x88)

    def test_timer_interrupt_elapsed_clear_and_mret(self):
        build, state, records = self.run_assembly("""
            li r4, 0xff50
            la r1, handler
            csrw r1, 2
            sw zero, 2(r4)
            li r1, 40
            sw r1, 0(r4)
            sw zero, 1(r4)
            li r1, 1
            csrw r1, 5
            li r1, 8
            csrw r1, 6
            li r1, 1
            sw r1, 2(r4)
        wait_timer:
            li r2, 1
            beq r5, r2, done
            j wait_timer
        done:
            sw r5, 2(zero)
            halt
        handler:
            lw r1, 5(r4)
            sw r1, 0(zero)
            li r1, 1
            sw r1, 5(r4)
            lw r1, 5(r4)
            sw r1, 3(zero)
            lw r1, 2(r4)
            sw r1, 4(zero)
            addi r5, 1
            mret
        """)
        self.assert_interrupt_return(state, records, cause=0)
        self.assertEqual(state["csrs"][0], build.labels["handler"])
        self.assertEqual(self.memory(state, 0), 1, "Timer expiry must set elapsed")
        self.assertEqual(self.memory(state, 2), 1)
        self.assertEqual(self.memory(state, 3), 0, "W1C must clear elapsed")
        self.assertEqual(self.memory(state, 4), 0, "one-shot expiry must disable Timer")

    def test_illegal_encoding_fault(self):
        for instruction in (14, 15, 0x8000, 0x002A):
            with self.subTest(instruction=f"0x{instruction:04x}"):
                state, records = self.run_image([instruction, 10], expected_code=2)
                self.assertTrue(state["faulted"])
                self.assertFalse(state["halted"])
                self.assertEqual(state["fault_code"], 1)
                self.assertEqual(state["fault_pc"], 0)
                self.assertEqual(state["fault_inst"], instruction)
                self.assertEqual(records, [])
                self.assertEqual(state["memory"], {})

    def test_instruction_fetch_outside_rom_fault(self):
        _, state, records = self.run_assembly("j 1024", expected_code=2)
        self.assertTrue(state["faulted"])
        self.assertFalse(state["halted"])
        self.assertEqual(state["fault_code"], 2)
        self.assertEqual(state["fault_pc"], ROM_DEPTH)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["next_pc"], ROM_DEPTH)

    def test_infinite_loop_exits_with_timeout(self):
        _, state, records = self.run_assembly("loop: j loop", expected_code=3, max_cycles=128)
        self.assertFalse(state["halted"])
        self.assertFalse(state["faulted"])
        self.assertGreater(len(records), 0)
        self.assertTrue(all(record["pc"] == 0 and record["next_pc"] == 0 for record in records))
        self.assertEqual(state["memory"], {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
