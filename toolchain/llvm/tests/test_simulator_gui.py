"""Qt simulation controls exercise the real CPU and virtual peripherals."""
import os
from pathlib import Path
import sys
import time
import unittest
from unittest import mock

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'software'))

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication
from opencpu.gui.ide import IDEWindow


class _SerialBoundary(QObject):
    received = pyqtSignal(bytes)
    connection_changed = pyqtSignal(bool)
    error = pyqtSignal(str)
    download_finished = pyqtSignal(int)
    progress = pyqtSignal(int, int)
    is_open = False
    busy = False

    def __init__(self):
        super().__init__()
        self.downloads = []
        self.open_attempts = 0

    def download(self, binary):
        self.downloads.append(binary)

    def open(self, settings):
        self.open_attempts += 1
        raise AssertionError('virtual simulation must never open a real port')

    def close(self):
        self.is_open = False


class SimulatorGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self):
        self.transport = _SerialBoundary()
        self.window = IDEWindow(transport=self.transport)
        self.window._confirm_all_documents = lambda: True
        self.window._confirm_close = lambda _editor: True

    def tearDown(self):
        self.window.close()
        self.application.processEvents()

    def build(self, assembly):
        self.window.new_file(text=assembly, kind='assembly')
        self.assertTrue(self.window.assemble(), self.window.message_tab.toPlainText())
        return self.window.simulator

    def wait_until(self, predicate):
        deadline = time.monotonic() + 3
        while not predicate() and time.monotonic() < deadline:
            QTest.qWait(5)
        self.assertTrue(predicate(), self.window.message_tab.toPlainText())

    def run_until_paused(self):
        self.window.run()
        self.wait_until(lambda: not self.window.running)

    def test_simulation_window_without_image_is_read_only(self):
        dialog = self.window.open_simulation()
        self.assertIs(dialog, self.window.open_simulation())
        self.assertTrue(dialog.isVisible())
        self.assertFalse(dialog.inject_button.isEnabled())
        self.assertFalse(dialog.advance_button.isEnabled())
        self.assertFalse(dialog.buttons_input.isEnabled())
        self.assertIn('Assemble', dialog.state_label.text())

    def test_breakpoint_stops_before_instruction_and_run_continues_once(self):
        model = self.build('li a1, 0\nloop: addi a1, 1\nj loop\n')
        pc = self.window.build_result.labels['loop']
        self.window.set_breakpoints({pc})
        self.run_until_paused()
        self.assertEqual((model.pc, model.registers[1], model.instructions_retired), (pc, 0, 1))
        self.assertEqual((model.stop_reason, model.breakpoint_hit), ('breakpoint', pc))
        self.assertTrue(self.window.run_action.isEnabled())
        self.assertIn('Breakpoint at PC=', self.window.message_tab.toPlainText())
        self.run_until_paused()
        self.assertEqual((model.pc, model.registers[1], model.instructions_retired), (pc, 1, 3))
        self.window.run_step()
        self.assertEqual((model.pc, model.registers[1]), (pc + 1, 2))
        self.assertIsNone(model.stop_reason)

    def test_breakpoint_at_batch_boundary_is_not_skipped(self):
        model = self.build('nop\n' * 64 + 'target: li a1, 9\nhalt\n')
        self.window.set_breakpoints({64})
        self.run_until_paused()
        self.assertEqual(model.instructions_retired, 64)
        self.assertEqual(model.pc, 64)
        self.assertEqual(model.registers[1], 0)
        self.assertFalse(model.limit_reached)
        self.assertEqual(model.stop_reason, 'breakpoint')

    def test_pc_management_validates_and_reset_keeps_breakpoints(self):
        model = self.build('li a1, 1\nhalt\n')
        with mock.patch('opencpu.gui.ide.QInputDialog.getText', return_value=('0x1, 0', True)):
            self.assertTrue(self.window.edit_breakpoints())
        self.assertEqual(model.breakpoints, {0, 1})
        self.assertTrue(self.window.toggle_breakpoint(pc=0))
        self.assertEqual(model.breakpoints, {1})
        with mock.patch('opencpu.gui.ide.QInputDialog.getText', return_value=('1024', True)):
            self.assertFalse(self.window.edit_breakpoints())
        self.assertEqual(model.breakpoints, {1})
        self.window.reset()
        self.assertEqual(model.breakpoints, {1})
        self.assertFalse(self.window.toggle_breakpoint(pc=1024))
        self.window.clear_breakpoints_action.trigger()
        self.assertEqual(model.breakpoints, set())

    def test_gpio_inputs_are_undoable_and_separate_from_real_serial(self):
        model = self.build('halt\n')
        dialog = self.window.open_simulation()
        dialog.buttons_input.setValue(10)
        dialog.switches_input.setValue(5)
        self.assertEqual((model.peek_data(0xff10), model.peek_data(0xff20)), (10, 5))
        self.assertEqual(model.history_size, 2)
        self.assertTrue(self.window.run_undo_action.isEnabled())
        self.window.run_undo()
        self.assertEqual((dialog.buttons_input.value(), dialog.switches_input.value()), (10, 0))
        self.window.reset()
        self.assertEqual(model.history_size, 0)
        self.assertEqual(dialog.buttons_input.value(), 10)
        self.assertFalse(self.window.run_undo_action.isEnabled())
        self.assertEqual((self.transport.open_attempts, self.transport.downloads), (0, []))

    def test_rx_refresh_and_memory_table_never_consume_fifo(self):
        model = self.build('halt\n')
        dialog = self.window.open_simulation()
        dialog.rx_format.setCurrentIndex(1)
        dialog.rx_input.setText('41 42')
        self.assertTrue(dialog.inject_rx())
        before = model.snapshot()
        with mock.patch.object(model.peripherals, 'read', wraps=model.peripherals.read) as read:
            for _ in range(3):
                dialog.refresh_state()
                self.window._refresh_execution()
            self.assertTrue(read.call_args_list)
            self.assertTrue(all(not item.kwargs.get('side_effects', False) for item in read.call_args_list))
        self.assertEqual(model.snapshot(), before)
        self.assertEqual(model.peripherals.snapshot()['uart']['rx'], [65, 66])
        self.assertIn('"rx_count": 2', dialog.peripheral_state.toPlainText())
        self.assertEqual(self.window.serial_tab.toPlainText(), '')
        self.window.run_undo()
        self.assertEqual(model.peripherals.snapshot()['uart']['rx_count'], 0)

    def test_rx_hex_errors_and_framing_errors_have_visible_feedback(self):
        model = self.build('halt\n')
        dialog = self.window.open_simulation()
        dialog.rx_format.setCurrentIndex(1)
        dialog.rx_input.setText('xyz')
        self.assertFalse(dialog.inject_rx())
        self.assertEqual(model.history_size, 0)
        self.assertIn('RX input error', dialog.operation_label.text())
        dialog.rx_format.setCurrentIndex(0)
        dialog.rx_input.setText('X')
        dialog.framing_error.setChecked(True)
        self.assertTrue(dialog.inject_rx())
        self.assertEqual(model.peek_data(0xff42), 32)
        self.assertEqual(model.peripherals.snapshot()['uart']['rx_count'], 0)

    def test_halted_uart_can_drain_and_undo_without_retiring_cpu(self):
        model = self.build('li a1, 0xff40\nli a2, 65\nsw a2, 0(a1)\nhalt\n')
        dialog = self.window.open_simulation()
        self.run_until_paused()
        self.assertTrue(model.halted)
        self.assertEqual(model.peripherals.uart_output, b'')
        pc, retired, cycle = model.pc, model.instructions_retired, model.cycle
        self.assertTrue(dialog.advance_button.isEnabled())
        dialog.ticks_input.setValue(20)
        self.assertTrue(dialog.advance_ticks())
        self.assertEqual((model.pc, model.instructions_retired, model.cycle), (pc, retired, cycle + 20))
        self.assertEqual((dialog.tx_output.toPlainText(), dialog.tx_hex.text()), ('A', '41'))
        self.assertEqual(model.stop_reason, 'halt')
        self.window.run_undo()
        self.assertEqual(model.peripherals.uart_output, b'')
        self.assertEqual(dialog.tx_output.toPlainText(), '')
        self.assertEqual(model.cycle, cycle)
        self.assertEqual(self.window.serial_tab.toPlainText(), '')

    def test_peripheral_controls_disable_while_running_and_step_resumes_stop(self):
        model = self.build('loop: j loop\n')
        dialog = self.window.open_simulation()
        self.window.run()
        self.assertFalse(dialog.inject_button.isEnabled())
        self.assertFalse(dialog.advance_button.isEnabled())
        self.assertFalse(self.window.breakpoints_menu.isEnabled())
        dialog.buttons_input.setValue(5)
        self.assertEqual(model.peek_data(0xff10), 0)
        self.assertFalse(dialog.inject_rx())
        self.assertFalse(dialog.advance_ticks())
        self.window.stop()
        self.assertEqual(model.stop_reason, 'stopped')
        self.assertTrue(dialog.inject_button.isEnabled())
        previous = model.instructions_retired
        self.window.run_step()
        self.assertEqual(model.instructions_retired, previous + 1)

    def test_fault_context_is_visible_and_fault_is_undoable(self):
        model = self.build('.word 14\n')
        self.run_until_paused()
        self.assertTrue(model.faulted)
        self.assertEqual(model.instructions_retired, 0)
        message = self.window.message_tab.toPlainText()
        self.assertIn('Execution fault:', message)
        self.assertIn('PC=0x0000', message)
        self.assertIn('instruction=0x000E', message)
        self.assertFalse(self.window.run_action.isEnabled())
        self.assertTrue(self.window.run_undo_action.isEnabled())
        self.window.run_undo()
        self.assertFalse(model.faulted)
        self.assertEqual(model.pc, 0)
        self.assertTrue(self.window.run_action.isEnabled())

    def test_terminal_is_bounded_and_state_dump_omits_full_output(self):
        model = self.build('halt\n')
        dialog = self.window.open_simulation()
        model.peripherals.uart_output.extend(b'A' * 5000 + b'B')
        with mock.patch.object(model.peripherals, 'snapshot', wraps=model.peripherals.snapshot) as snapshot:
            dialog.refresh_state()
        snapshot.assert_called_once_with(include_output=False)
        self.assertEqual(len(dialog.tx_output.toPlainText()), 4096)
        self.assertTrue(dialog.tx_output.toPlainText().endswith('B'))
        self.assertLess(len(dialog.peripheral_state.toPlainText()), 1500)
        self.assertIn('"output_length": 5001', dialog.peripheral_state.toPlainText())

    def test_dialog_tracks_invalidated_images_and_closes_with_owner(self):
        self.build('halt\n')
        dialog = self.window.open_simulation()
        self.window.current_editor.setPlainText('li a1, 9\nhalt\n')
        self.assertIsNone(self.window.simulator)
        self.assertFalse(dialog.inject_button.isEnabled())
        dialog.refresh_state()
        self.assertIn('Assemble', dialog.state_label.text())
        self.window.close()
        self.application.processEvents()
        self.assertFalse(dialog.isVisible())
        self.assertFalse(dialog._refresh_timer.isActive())


if __name__ == '__main__':
    unittest.main(verbosity=2)
