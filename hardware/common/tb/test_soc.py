#!/usr/bin/env python3
"""Self-check the already-built, pin-level UART/SoC Verilator testbench.

The Makefile builds the executable before running this file. These tests use
only Python's standard library and the Qt-free software reference model.
OPENCPU_SIM may select an executable built in a different build directory.
"""

import unittest

from soc_support import REPOSITORY, ROM_DEPTH, SocDriverMixin
from opencpu.core.toolchain import Toolchain


class SocTests(SocDriverMixin, unittest.TestCase):
    def test_current_examples_match_reference_at_every_retirement(self):
        examples = REPOSITORY / "software/examples/simple"
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
