"""Register-level device behavior independent of LLVM and Qt."""
import json
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "software"))
from opencpu.core.peripherals import PeripheralModel  # noqa: E402


class PeripheralTests(unittest.TestCase):
    def test_gpio_and_display_only_decode_exact_registers(self):
        model = PeripheralModel(buttons=10, switches=5)
        model.write(0xFF00, 0xABCD)
        self.assertEqual(model.read(0xFF00), 13)
        self.assertEqual(model.snapshot()["gpio"]["led_pins"], 2)
        model.write(0xFF10, 0)
        model.write(0xFF20, 0)
        self.assertEqual(model.read(0xFF10), 10)
        self.assertEqual(model.read(0xFF20), 5)
        model.write(0xFF30, 0x1234)
        self.assertEqual(model.read(0xFF30), 0x1234)
        for address in (0xFF01, 0xFF11, 0xFF31, 0xFF43, 0xFF56, 0xFF60, 0xFFFF):
            model.write(address, 0xFFFF)
            self.assertEqual(model.read(address), 0)

    def test_rx_peek_is_non_destructive_and_events_coalesce(self):
        model = PeripheralModel()
        model.inject_uart(b"AB")
        self.assertEqual(model.peek(0xFF40), 65)
        self.assertEqual(model.snapshot()["uart"]["rx_count"], 2)
        self.assertEqual(model.tick(0), 0)
        self.assertEqual(model.tick(), 2)
        self.assertEqual(model.tick(), 0)
        self.assertEqual(model.read(0xFF40), 65)
        self.assertEqual(model.read(0xFF40), 66)
        self.assertEqual(model.read(0xFF40), 0)

    def test_rx_overflow_retains_bytes_and_still_generates_irq(self):
        model = PeripheralModel(fifo_depth=2)
        model.inject_uart(b"ABC")
        self.assertEqual(model.snapshot()["uart"]["rx"], [65, 66])
        self.assertEqual(model.peek(0xFF42), 8)
        self.assertEqual(model.tick(), 2)
        model.inject_uart(b"D")
        self.assertEqual(model.tick(), 2)
        self.assertEqual(model.snapshot()["uart"]["rx"], [65, 66])

    def test_uart_error_w1c_and_new_error_priority(self):
        model = PeripheralModel(fifo_depth=1)
        model.inject_uart(b"AB")
        model.write(0xFF42, 8)
        self.assertEqual(model.peek(0xFF42), 0)
        model.tick()
        self.assertEqual(model.peek(0xFF42), 8)
        model.write(0xFF42, 8)
        model.tick()
        self.assertEqual(model.peek(0xFF42), 0)
        model.inject_uart(b"X", framing_error=True)
        self.assertEqual(model.tick(), 0)
        self.assertEqual(model.peek(0xFF42), 32)
        self.assertEqual(model.snapshot()["uart"]["rx"], [65])
        model.write(0xFF42, 1)
        self.assertEqual(model.peek(0xFF42), 32)
        model.write(0xFF42, 32)
        self.assertEqual(model.peek(0xFF42), 0)

    def test_uart_frames_finish_in_order_and_low_byte_is_sent(self):
        model = PeripheralModel(uart_frame_ticks=3)
        self.assertEqual(model.peek(0xFF41), 2)
        model.write(0xFF40, 0x141)
        model.write(0xFF40, 66)
        self.assertTrue(model.peek(0xFF41) & 4)
        model.tick(2)
        self.assertEqual(model.uart_output, b"")
        model.tick()
        self.assertEqual(model.uart_output, b"A")
        self.assertTrue(model.uart_busy)
        model.tick(3)
        self.assertEqual(model.uart_output, b"AB")
        self.assertFalse(model.uart_busy)
        self.assertEqual(model.peek(0xFF41), 2)

    def test_tx_capacity_includes_ready_pop_but_excludes_active_byte(self):
        model = PeripheralModel(fifo_depth=2, uart_frame_ticks=10)
        for byte in b"AB":
            model.write(0xFF40, byte)
        self.assertTrue(model.peek(0xFF41) & 2)
        model.write(0xFF40, 67)  # Simultaneous ready-pop and push on full queue.
        self.assertEqual(model.snapshot()["uart"]["active"], 65)
        self.assertEqual(model.snapshot()["uart"]["tx"], [66, 67])
        self.assertFalse(model.peek(0xFF41) & 2)
        model.write(0xFF40, 68)
        self.assertEqual(model.peek(0xFF42), 16)
        model.tick(30)
        self.assertEqual(model.uart_output, b"ABC")

    def test_timer_reconfigure_does_not_count_and_oneshot_disables(self):
        model = PeripheralModel()
        model.write(0xFF50, 3)
        model.write(0xFF52, 1)
        self.assertEqual(model.tick(), 0)
        self.assertEqual(model.read(0xFF53), 0)
        self.assertEqual(model.tick(2), 0)
        self.assertEqual(model.read(0xFF53), 2)
        self.assertEqual(model.tick(), 1)
        self.assertEqual(model.read(0xFF55), 1)
        self.assertEqual(model.read(0xFF52), 0)
        self.assertEqual(model.tick(20), 0)

    def test_timer_periodic_w1c_and_expiry_priority(self):
        model = PeripheralModel()
        model.write(0xFF50, 2)
        model.write(0xFF52, 3)
        model.tick()
        self.assertEqual(model.tick(2), 1)
        model.write(0xFF55, 1)
        self.assertEqual(model.read(0xFF55), 0)
        self.assertEqual(model.tick(), 0)
        model.write(0xFF55, 1)
        self.assertEqual(model.tick(), 1)
        self.assertEqual(model.read(0xFF55), 1)
        model.write(0xFF50, 4)
        self.assertEqual(model.tick(), 0)
        self.assertEqual(model.read(0xFF53), 0)
        self.assertEqual(model.read(0xFF55), 1)

    def test_timer_zero_and_upper_period_register(self):
        model = PeripheralModel()
        model.write(0xFF52, 0xFFFF)
        model.tick(100)
        self.assertEqual(model.read(0xFF52), 3)
        self.assertEqual(model.read(0xFF53), 0)
        self.assertEqual(model.read(0xFF55), 0)
        model.write(0xFF51, 1)
        model.write(0xFF50, 2)
        model.tick(3)
        self.assertEqual(model.read(0xFF50), 2)
        self.assertEqual(model.read(0xFF51), 1)
        self.assertEqual(model.read(0xFF53), 2)
        model.write(0xFF53, 0xFFFF)
        self.assertEqual(model.read(0xFF53), 2)

    def test_disabled_peripherals_ignore_io_and_events(self):
        model = PeripheralModel(enable_uart=False, enable_timer=False, enable_display=False)
        model.inject_uart(b"AB", framing_error=True)
        for address in (0xFF30, 0xFF40, 0xFF42, 0xFF50, 0xFF52):
            model.write(address, 0xFFFF)
            self.assertEqual(model.read(address), 0)
        self.assertEqual(model.tick(100), 0)
        self.assertEqual(model.uart_output, b"")

    def test_checkpoint_restores_fifo_timer_inputs_and_truncates_output(self):
        model = PeripheralModel(uart_frame_ticks=1)
        model.inject_uart(b"Z")
        model.write(0xFF40, 65)
        model.write(0xFF50, 2)
        model.write(0xFF52, 3)
        before = model.snapshot()
        checkpoint = model.checkpoint()
        model.read(0xFF40)
        model.tick(5)
        model.set_inputs(3, 4)
        model.write(0xFF00, 5)
        self.assertEqual(model.uart_output, b"A")
        model.restore(checkpoint)
        self.assertEqual(model.snapshot(), before)
        self.assertEqual(model.tick(), 2)
        self.assertEqual(model.uart_output, b"A")

    def test_checkpoint_does_not_copy_unbounded_uart_output(self):
        model = PeripheralModel()
        model.uart_output.extend(b"A" * 100000)
        checkpoint = model.checkpoint()
        self.assertEqual(checkpoint.output_length, 100000)
        self.assertLess(len(repr(checkpoint)), 800)
        snapshot = model.snapshot()
        json.dumps(snapshot)
        snapshot["uart"]["output"].clear()
        self.assertEqual(len(model.uart_output), 100000)

    def test_reset_retains_configured_external_inputs(self):
        model = PeripheralModel(buttons=9, switches=6)
        model.inject_uart(b"A")
        model.write(0xFF00, 15)
        model.tick()
        model.reset()
        self.assertEqual(model.read(0xFF10), 9)
        self.assertEqual(model.read(0xFF20), 6)
        self.assertEqual(model.read(0xFF00), 0)
        self.assertEqual(model.snapshot()["uart"]["rx"], [])
        self.assertEqual(model.ticks, 0)

    def test_frequent_snapshot_can_omit_unbounded_output(self):
        class OutputWithoutIteration(bytearray):
            def __iter__(self):
                raise AssertionError("lightweight snapshot must not copy TX history")

        model = PeripheralModel()
        model.uart_output = OutputWithoutIteration(b"A" * 100000)
        state = model.snapshot(include_output=False)
        self.assertEqual(state["uart"]["output_length"], 100000)
        self.assertNotIn("output", state["uart"])
        self.assertLess(len(json.dumps(state)), 1000)

    def test_batch_time_matches_single_ticks_and_large_advances_are_bounded(self):
        batch, single = PeripheralModel(), PeripheralModel()
        generator = random.Random(426)
        for _ in range(300):
            address = generator.choice((0xFF40, 0xFF42, 0xFF50, 0xFF51, 0xFF52, 0xFF55))
            value = generator.randrange(10)
            for model in (batch, single):
                model.write(address, value)
            if generator.randrange(3) == 0:
                payload = bytes(generator.randrange(256) for _ in range(generator.randrange(4)))
                for model in (batch, single):
                    model.inject_uart(payload)
            ticks = generator.randrange(40)
            expected_events = 0
            for _ in range(ticks):
                expected_events |= single.tick()
            self.assertEqual(batch.tick(ticks), expected_events)
            self.assertEqual(batch.snapshot(), single.snapshot())
        batch.reset()
        batch.write(0xFF50, 7)
        batch.write(0xFF52, 3)
        batch.write(0xFF40, 65)
        self.assertEqual(batch.tick(10**12), 1)
        self.assertEqual(batch.read(0xFF53), (10**12 - 1) % 7)
        self.assertEqual(batch.uart_output, b"A")

    def test_invalid_inputs_are_rejected_without_partial_changes(self):
        for arguments in ({"fifo_depth": 0}, {"fifo_depth": True}, {"uart_frame_ticks": 0},
                          {"enable_uart": 1}, {"enable_timer": "yes"}, {"buttons": 16}, {"switches": -1}):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                PeripheralModel(**arguments)
        model = PeripheralModel()
        for data in (b"A" + bytes([1]),):
            model.inject_uart(data)
        before = model.snapshot()
        with self.assertRaises(ValueError):
            model.inject_uart([65, 256])
        self.assertEqual(model.snapshot(), before)
        with self.assertRaises(ValueError):
            model.set_inputs(3, 16)
        self.assertEqual(model.snapshot(), before)
        for invalid in (-1, True, 1.5):
            with self.assertRaises(ValueError):
                model.tick(invalid)
        with self.assertRaises(ValueError):
            model.read(65536)
        with self.assertRaises(ValueError):
            model.write(0xFF40, 65536)


if __name__ == "__main__":
    unittest.main(verbosity=2)
