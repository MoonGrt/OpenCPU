"""User-visible simulator CLI behavior, independent of LLVM and Qt."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

REPOSITORY = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY / "software"))
from opencpu.cli import main
from opencpu.core.toolchain import Toolchain
from opencpu.core.simulator import Simulator


class SimulatorCLITests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="opencpu-simulator-cli-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.image = self.directory / "program.bin"

    def run_cli(self, source, *options):
        self.image.write_text(Toolchain().assemble(source).binary)
        output, error = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(error):
            code = main(["run", str(self.image), *options])
        return code, json.loads(output.getvalue()) if output.getvalue() else None, error.getvalue()

    def test_echo_preserves_binary_bytes_and_drains_after_halt(self):
        source = (REPOSITORY / "software/examples/simple/uart_echo.asm").read_text()
        code, state, error = self.run_cli(source, "--uart-rx-hex", "41 00 ff")
        self.assertEqual(code, 0, error)
        self.assertTrue(state["halted"])
        self.assertEqual(state["stop_reason"], "halt")
        self.assertEqual(state["uart_tx"], [65, 0, 255])
        self.assertFalse(state["peripherals"]["uart"]["busy"])
        self.assertEqual(state["peripherals"]["uart"]["rx_count"], 0)
        self.assertTrue(all(int(address) < 1024 for address in state["memory"]))

    def test_gpio_inputs_and_logical_leds_are_distinct_from_board_pins(self):
        code, state, error = self.run_cli("""
            li a4, 0xff00
            li a1, 0xffff
            sw a1, 0(a4)
            lw a1, 0(a4)
            sw a1, 0(zero)
            addi a4, 16
            lw a1, 0(a4)
            sw a1, 1(zero)
            addi a4, 16
            lw a1, 0(a4)
            sw a1, 2(zero)
            halt
        """, "--buttons", "0x3", "--switches", "12")
        self.assertEqual(code, 0, error)
        self.assertEqual([state["memory"][str(i)] for i in range(3)], [15, 3, 12])
        self.assertEqual(state["peripherals"]["gpio"]["led_pins"], 0)

    def test_large_frame_duration_drains_in_one_advance_without_extra_idle_time(self):
        advance = Simulator.advance_ticks
        calls = []
        def checked(model, ticks):
            self.assertGreater(ticks, 1, "CLI must batch idle advancement")
            calls.append(ticks)
            return advance(model, ticks)
        frame_ticks = 10**12
        with mock.patch.object(Simulator, "advance_ticks", checked):
            code, state, error = self.run_cli(
                "li a4, 0xff40\nli a1, 65\nsw a1, 0(a4)\nhalt",
                "--uart-frame-ticks", str(frame_ticks))
        self.assertEqual(code, 0, error)
        self.assertEqual(len(calls), 1)
        self.assertEqual(state["uart_tx"], [65])
        self.assertEqual(state["instructions_retired"], 5)
        self.assertEqual(state["ticks"], frame_ticks + 3)
        self.assertEqual(state["cycle"], (frame_ticks + 3) & 0xffffffff)

    def test_breakpoint_and_streaming_trace_stop_before_instruction(self):
        trace = self.directory / "trace.jsonl"
        code, state, error = self.run_cli("li a1, 42\naddi a1, 1\nhalt", "--breakpoint", "2", "--trace", str(trace))
        self.assertEqual(code, 0, error)
        self.assertFalse(state["halted"])
        self.assertEqual(state["stop_reason"], "breakpoint")
        self.assertEqual(state["breakpoint_hit"], 2)
        self.assertEqual(state["registers"]["a1"], 43)
        records = [json.loads(line) for line in trace.read_text().splitlines()]
        self.assertEqual([record["pc"] for record in records], [0, 1])
        self.assertEqual(state["instructions_retired"], len(records))

    def test_fault_details_and_exit_status(self):
        code, state, error = self.run_cli(".word 14")
        self.assertEqual(code, 2, error)
        self.assertEqual((state["fault_pc"], state["fault_inst"], state["fault_code"]), (0, 14, 1))
        self.assertEqual(state["stop_reason"], "fault")
        self.assertEqual(state["instructions_retired"], 0)

    def test_disabled_peripherals_and_explicit_idle_ticks(self):
        code, state, error = self.run_cli("halt", "--disable-uart", "--disable-timer", "--disable-display", "--drain-ticks", "7")
        self.assertEqual(code, 0, error)
        self.assertEqual(state["instructions_retired"], 1)
        self.assertEqual(state["ticks"], 8)
        self.assertFalse(state["peripherals"]["uart"]["enabled"])
        self.assertFalse(state["peripherals"]["timer"]["available"])
        self.assertFalse(state["peripherals"]["display"]["enabled"])

    def test_timer_interrupt_example(self):
        source = (REPOSITORY / "software/examples/simple/timer_irq.asm").read_text()
        code, state, error = self.run_cli(source)
        self.assertEqual(code, 0, error)
        self.assertTrue(state["halted"])
        self.assertEqual(state["memory"]["0"], 1)
        self.assertFalse(state["peripherals"]["timer"]["enabled"])
        self.assertFalse(state["peripherals"]["timer"]["elapsed"])

    def test_invalid_inputs_and_trace_collision_are_actionable(self):
        for options in (("--buttons", "16"), ("--uart-rx-hex", "zz"),
                        ("--drain-ticks", "-1"), ("--uart-frame-ticks", "0"),
                        ("--breakpoint", "1024"), ("--trace", str(self.image))):
            with self.subTest(options=options):
                code, state, error = self.run_cli("halt", *options)
                self.assertEqual(code, 2)
                self.assertIsNone(state)
                self.assertTrue(error)
                self.assertEqual(self.image.read_text(), Toolchain().assemble("halt").binary)


if __name__ == "__main__":
    unittest.main(verbosity=2)
