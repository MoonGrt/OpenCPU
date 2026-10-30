"""Functional CPU/peripheral simulation and reversible debugger regressions."""
from pathlib import Path
import sys
import unittest
from unittest import mock

REPOSITORY = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY / "software"))

from opencpu.core.assembler import Assembler
from opencpu.core.peripherals import PeripheralModel
from opencpu.core.simulator import (
    CSR_CYCLE, CSR_CYCLEH, CSR_MEPC, CSR_MIE, CSR_MSTATUS, CSR_MTVEC,
    Simulator,
)


class SimulatorTests(unittest.TestCase):
    def model(self, source, **options):
        model = Simulator(**options)
        model.inst_mem = [int(line, 2) for line in Assembler().assemble(source).splitlines()]
        return model

    def test_fault_is_reversible_without_undoing_the_previous_instruction(self):
        model = self.model("li a1, 42\n.word 14")
        self.assertTrue(model.step())
        before = model.snapshot()
        self.assertFalse(model.step())
        self.assertEqual(model.fault_code, 1)
        self.assertEqual(model.fault_pc, 1)
        self.assertEqual(model.fault_inst, 14)
        self.assertEqual(model.stop_reason, "fault")
        self.assertEqual(model.instructions_retired, 1)
        self.assertEqual(model.cycle, 1)
        self.assertTrue(model.run_undo())
        self.assertEqual(model.snapshot(), before)
        self.assertTrue(model.run_undo())
        self.assertEqual(model.registers[1], 0)

    def test_fetch_fault_and_malformed_word_do_not_retire(self):
        model = self.model("j 1024")
        model.step()
        self.assertFalse(model.step())
        self.assertEqual((model.fault_code, model.fault_pc, model.fault_inst), (2, 1024, None))
        self.assertEqual(model.instructions_retired, 1)
        self.assertTrue(model.run_undo())
        self.assertFalse(model.faulted)
        self.assertEqual(model.pc, 1024)
        model.inst_mem = [True]
        model.pc = 0
        self.assertFalse(model.step())
        self.assertEqual(model.fault_code, 2)

    def test_halt_memory_and_last_retire_all_undo(self):
        model = self.model("li a1, 42\nsw a1, 0(zero)\nhalt")
        states = [model.snapshot()]
        for _ in range(3):
            model.step()
            states.append(model.snapshot())
        self.assertEqual(model.stop_reason, "halt")
        self.assertEqual(model.last_retire["instruction"], 10)
        self.assertEqual(model.data_mem, {0: 42})
        for expected in reversed(states[:-1]):
            self.assertTrue(model.run_undo())
            self.assertEqual(model.snapshot(), expected)
        self.assertFalse(model.run_undo())

    def test_history_is_bounded_or_explicitly_unlimited(self):
        model = self.model("loop: j loop", history_limit=3)
        model.run(1000)
        self.assertEqual(model.history_size, 3)
        for _ in range(3):
            self.assertTrue(model.run_undo())
        self.assertFalse(model.can_undo)
        self.assertEqual(model.instructions_retired, 997)
        model = self.model("loop: j loop", history_limit=None)
        model.run(20)
        self.assertEqual(model.history_size, 20)
        model.clear_history()
        self.assertFalse(model.can_undo)

    def test_disabled_history_never_builds_checkpoints(self):
        model = self.model("li a1, 42\nhalt", history_limit=0)
        with mock.patch.object(model, "_capture_control", side_effect=AssertionError("control copy")), \
                mock.patch.object(model.peripherals, "checkpoint", side_effect=AssertionError("device copy")):
            self.assertEqual(model.run(), 2)
            model.inject_uart(b"X")
            model.set_inputs(buttons=3)
            model.advance_ticks(2)
            self.assertEqual(model.read_data(0xff40, side_effects=True), ord("X"))
        self.assertFalse(model.can_undo)
        self.assertEqual(model.history_size, 0)

    def test_breakpoints_stop_before_execute_and_run_resumes_once(self):
        model = self.model("loop: addi a1, 1\nj loop")
        model.breakpoints = {0}
        self.assertEqual(model.run(20), 0)
        self.assertEqual((model.stop_reason, model.breakpoint_hit, model.pc), ("breakpoint", 0, 0))
        self.assertEqual(model.registers[1], 0)
        self.assertEqual(model.run(20), 2)
        self.assertEqual(model.registers[1], 1)
        self.assertEqual(model.breakpoint_hit, 0)
        self.assertTrue(model.step())
        self.assertEqual(model.registers[1], 2)
        self.assertEqual(model.pc, 1)
        self.assertIsNone(model.breakpoint_hit)
        self.assertEqual(model.run(20), 1)
        self.assertEqual(model.stop_reason, "breakpoint")

    def test_limits_stop_and_trace_are_distinct(self):
        model = self.model("loop: addi a1, 1\nj loop")
        records = []
        self.assertEqual(model.run(5, trace=records.append), 5)
        self.assertEqual(model.stop_reason, "limit")
        self.assertTrue(model.limit_reached)
        self.assertEqual(len(records), 5)
        self.assertEqual([record["pc"] for record in records], [0, 1, 0, 1, 0])
        self.assertEqual(records[-1]["registers"][1], 3)
        records[-1]["registers"][1] = 999
        self.assertEqual(model.last_retire["registers"][1], 3)
        model.stop()
        self.assertEqual(model.stop_reason, "stopped")
        self.assertFalse(model.step())
        self.assertEqual(model.run(1), 1)
        self.assertEqual(model.stop_reason, "limit")

    def test_full_peripheral_page_has_priority_over_large_ram(self):
        model = self.model("li a1, 0xff01\nli a2, 42\nsw a2, 0(a1)\nhalt", ram_depth=65536)
        model.run()
        self.assertEqual(model.peek_data(0xff01), 0)
        self.assertNotIn(0xff01, model.data_mem)
        self.assertEqual(model.peek_data(0xfffe), 0)
        self.assertEqual(model.peek_data(0x400), 0)

    def test_gpio_mmio_masks_led_bits_and_preserves_read_only_inputs(self):
        model = self.model("li a1, 0xff00\nli a2, 0xabcd\nsw a2, 0(a1)\n"
                           "li a1, 0xff10\nsw a2, 0(a1)\nlw a3, 0(a1)\nhalt")
        model.set_inputs(buttons=6, switches=9)
        model.run()
        self.assertEqual(model.peek_data(0xff00), 13)
        self.assertEqual(model.peek_data(0xff10), 6)
        self.assertEqual(model.peek_data(0xff20), 9)
        self.assertEqual(model.registers[3], 6)
        self.assertEqual(model.data_mem, {})

    def test_uart_debug_peek_is_non_destructive_and_load_undo_restores_fifo(self):
        model = self.model("li a1, 0xff40\nlw a2, 0(a1)\nhalt")
        model.inject_uart(b"AB")
        self.assertEqual(model.peek_data(0xff40), 65)
        self.assertEqual(model.read_data(0xff40), 65)
        self.assertEqual(model.peripherals.snapshot()["uart"]["rx_count"], 2)
        model.run(2)  # Full-width LI expands to LUI/ORI before the consuming LW.
        before = model.snapshot()
        model.step()
        self.assertEqual(model.registers[2], 65)
        self.assertEqual(model.peek_data(0xff40), 66)
        self.assertTrue(model.run_undo())
        self.assertEqual(model.snapshot(), before)

    def test_idle_ticks_can_drain_uart_after_halt_and_undo_output(self):
        device = PeripheralModel(uart_frame_ticks=3)
        model = self.model("li a1, 0xff40\nli a2, 65\nsw a2, 0(a1)\nhalt", peripherals=device)
        model.run()
        before = model.snapshot()
        retired, pc = model.instructions_retired, model.pc
        model.advance_ticks(10)
        self.assertEqual(bytes(device.uart_output), b"A")
        self.assertEqual((model.instructions_retired, model.pc), (retired, pc))
        self.assertEqual(model.stop_reason, "halt")
        self.assertTrue(model.run_undo())
        self.assertEqual(model.snapshot(), before)

    def test_external_events_are_undoable_without_retiring(self):
        model = self.model("halt")
        before = model.snapshot()
        model.set_inputs(buttons=7, switches=12)
        self.assertTrue(model.run_undo())
        self.assertEqual(model.snapshot(), before)
        model.inject_uart(b"AB")
        self.assertTrue(model.run_undo())
        self.assertEqual(model.snapshot(), before)
        model.request_interrupt(4)
        self.assertEqual(model.pending_interrupts, 4)
        self.assertTrue(model.run_undo())
        self.assertEqual(model.snapshot(), before)

    def test_new_device_irq_wins_acknowledgement_of_same_pending_source(self):
        model = self.model("nop\nnop\nhalt")
        model.write_csr(CSR_MTVEC, 1)
        model.write_csr(CSR_MIE, 2)
        model.write_csr(CSR_MSTATUS, 8)
        model.request_interrupt(2)
        model.inject_uart(b"A")
        model.step()
        self.assertTrue(model.irq_taken)
        self.assertEqual(model.last_retire["irq_ack"], 2)
        self.assertEqual(model.pending_interrupts, 2)
        self.assertEqual(model.read_csr(CSR_MEPC), 1)
        self.assertEqual(model.pc, 1)

    def test_irq_uses_committed_csr_and_branch_destination(self):
        model = self.model("li a1, 8\ncsrw a1, 6\nj 8")
        model.write_csr(CSR_MTVEC, 7)
        model.write_csr(CSR_MIE, 1)
        model.request_interrupt(1)
        model.step()
        self.assertFalse(model.irq_taken)
        model.step()
        self.assertTrue(model.irq_taken)
        self.assertEqual(model.read_csr(CSR_MEPC), 2)
        model = self.model("j 8")
        model.write_csr(CSR_MTVEC, 7)
        model.write_csr(CSR_MIE, 1)
        model.write_csr(CSR_MSTATUS, 8)
        model.step(irq=1)
        self.assertEqual(model.read_csr(CSR_MEPC), 8)
        self.assertEqual(model.pc, 7)

    def test_mret_and_halt_do_not_accept_irq_on_the_same_retirement(self):
        model = self.model("mret\nhalt")
        model.write_csr(CSR_MEPC, 1)
        model.write_csr(CSR_MSTATUS, 128)
        model.write_csr(CSR_MIE, 1)
        model.request_interrupt(1)
        model.step()
        self.assertFalse(model.irq_taken)
        self.assertEqual(model.read_csr(CSR_MSTATUS), 136)
        model.step()
        self.assertTrue(model.halted)
        self.assertFalse(model.irq_taken)
        self.assertEqual(model.pending_interrupts, 1)

    def test_cycle_csr_wrap_and_idle_tick_undo(self):
        model = self.model("nop\nhalt")
        model.cycle = 0xffffffff
        model.step()
        self.assertEqual(model.read_csr(CSR_CYCLE), 0)
        self.assertEqual(model.read_csr(CSR_CYCLEH), 0)
        model.advance_ticks(65537)
        self.assertEqual((model.read_csr(CSR_CYCLE), model.read_csr(CSR_CYCLEH)), (1, 1))
        self.assertTrue(model.run_undo())
        self.assertEqual(model.cycle, 0)

    def test_timer_expiry_interrupt_w1c_and_mret_execute_together(self):
        model = self.model("""
            li a4, 0xff50
            la a1, handler
            csrw a1, 2
            li a1, 1
            csrw a1, 5
            li a1, 8
            csrw a1, 6
            li a1, 2
            sw a1, 0(a4)
            li a1, 1
            sw a1, 2(a4)
        loop:
            li a2, 1
            beq a3, a2, done
            j loop
        done:
            halt
        handler:
            lw a1, 5(a4)
            sw a1, 5(a4)
            addi a3, 1
            mret
        """)
        records = []
        model.run(100, trace=records.append)
        self.assertTrue(model.halted)
        self.assertFalse(model.in_interrupt)
        self.assertEqual(model.registers[1], 1, "handler must observe elapsed")
        self.assertEqual(model.registers[3], 1, "one-shot must interrupt once")
        self.assertEqual(sum(record["irq_ack"] == 1 for record in records), 1)
        self.assertEqual(model.peek_data(0xff55), 0, "W1C must clear elapsed")
        self.assertEqual(model.peek_data(0xff52), 0, "one-shot expiry must disable timer")
        self.assertEqual(model.read_csr(CSR_MSTATUS), 136)

    def test_trace_can_pause_run_after_a_committed_instruction(self):
        model = self.model("loop: addi a1, 1\nj loop")
        def trace(record):
            if record["registers"][1] == 3:
                model.stop()
        self.assertEqual(model.run(100, trace=trace), 5)
        self.assertEqual(model.instructions_retired, 5)
        self.assertEqual(model.stop_reason, "stopped")
        self.assertFalse(model.limit_reached)

    def test_lightweight_snapshot_omits_completed_uart_output(self):
        model = self.model("halt")
        model.peripherals.uart_output.extend(b"test")
        state = model.snapshot(include_output=False)
        self.assertNotIn("output", state["peripherals"]["uart"])
        self.assertEqual(state["peripherals"]["uart"]["output_length"], 4)
        self.assertEqual(model.snapshot()["peripherals"]["uart"]["output"], list(b"test"))

    def test_invalid_debug_arguments_do_not_run(self):
        for limit in (-1, True, 1.5):
            with self.assertRaises(ValueError):
                Simulator(history_limit=limit)
        model = self.model("halt")
        for value in (-1, True, 1.5):
            with self.assertRaises(ValueError):
                model.run(value)
        for points in ({-1}, {65536}, {True}):
            with self.assertRaises(ValueError):
                model.run(breakpoints=points)
        with self.assertRaises(ValueError):
            model.run(trace=[])
        self.assertEqual(model.instructions_retired, 0)
        for address in (-1, 65536, True):
            with self.assertRaises(ValueError):
                model.peek_data(address)


if __name__ == "__main__":
    unittest.main(verbosity=2)
