"""Nonmodal controls for virtual peripherals, independent of physical serial I/O."""
import json

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QPlainTextEdit, QPushButton, QSpinBox, QVBoxLayout,
)


class SimulationDialog(QDialog):
    """Observe through snapshots/peek only; mutations use Simulator's undoable API."""

    TERMINAL_BYTES = 4096

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.setWindowTitle('Simulation')
        self.resize(640, 650)
        layout = QVBoxLayout(self)
        self.state_label = QLabel('Assemble a program to start simulation.')
        layout.addWidget(self.state_label)
        form = QFormLayout()
        self.buttons_input = self._input_mask()
        self.switches_input = self._input_mask()
        form.addRow('Buttons (4 bits)', self.buttons_input)
        form.addRow('Switches (4 bits)', self.switches_input)
        self.led_value = QLabel('—')
        self.display_value = QLabel('—')
        self.fifo_value = QLabel('—')
        form.addRow('LED logical value', self.led_value)
        form.addRow('Hex display', self.display_value)
        form.addRow('UART status / errors', self.fifo_value)
        layout.addLayout(form)
        self.buttons_input.valueChanged.connect(self._apply_inputs)
        self.switches_input.valueChanged.connect(self._apply_inputs)

        receive = QHBoxLayout()
        self.rx_format = QComboBox()
        self.rx_format.addItems(('Text (UTF-8)', 'Hex'))
        self.rx_input = QLineEdit()
        self.rx_input.setPlaceholderText('Virtual RX bytes')
        self.inject_button = QPushButton('Inject RX')
        receive.addWidget(self.rx_format)
        receive.addWidget(self.rx_input, 1)
        receive.addWidget(self.inject_button)
        layout.addLayout(receive)
        self.framing_error = QCheckBox('Simulate a framing error')
        layout.addWidget(self.framing_error)
        self.inject_button.clicked.connect(self.inject_rx)
        self.rx_input.returnPressed.connect(self.inject_rx)
        self.tx_output = QPlainTextEdit()
        self.tx_output.setReadOnly(True)
        self.tx_output.setPlaceholderText('Virtual UART TX output')
        self.tx_output.setMaximumBlockCount(512)
        layout.addWidget(QLabel('Virtual TX terminal (most recent 4096 bytes)'))
        layout.addWidget(self.tx_output)
        self.tx_hex = QLineEdit()
        self.tx_hex.setReadOnly(True)
        form = QFormLayout()
        form.addRow('TX hex', self.tx_hex)
        layout.addLayout(form)
        advance = QHBoxLayout()
        self.ticks_input = QSpinBox()
        self.ticks_input.setRange(1, 1000000)
        self.ticks_input.setValue(1000)
        self.advance_button = QPushButton('Advance ticks')
        self.advance_button.clicked.connect(self.advance_ticks)
        advance.addWidget(self.ticks_input)
        advance.addWidget(self.advance_button)
        advance.addWidget(QLabel('Peripherals can advance after HALT.'))
        layout.addLayout(advance)
        self.peripheral_state = QPlainTextEdit()
        self.peripheral_state.setReadOnly(True)
        self.peripheral_state.setMaximumHeight(170)
        layout.addWidget(QLabel('Peripheral state'))
        layout.addWidget(self.peripheral_state)
        self.operation_label = QLabel('Virtual controls do not access a physical serial port.')
        self.operation_label.setWordWrap(True)
        layout.addWidget(self.operation_label)
        self._last_output = None
        self._last_state = None
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(100)
        self._refresh_timer.timeout.connect(self.refresh_state)
        self.sync_controls()

    @staticmethod
    def _input_mask():
        widget = QSpinBox()
        widget.setRange(0, 15)
        widget.setDisplayIntegerBase(16)
        widget.setPrefix('0x')
        return widget

    def _model(self, *, mutate=False):
        model = self.owner.simulator
        if model is None or self.owner._closing:
            return None
        if mutate and (self.owner.running or self.owner.compiling or not self.owner._ensure_build_current()):
            return None
        return model

    def sync_controls(self):
        enabled = (self.owner.simulator is not None and not self.owner._closing
                   and not self.owner.running and not self.owner.compiling)
        for widget in (self.buttons_input, self.switches_input, self.rx_format, self.rx_input,
                       self.framing_error, self.inject_button, self.ticks_input, self.advance_button):
            widget.setEnabled(enabled)

    def _apply_inputs(self, _value=None):
        model = self._model(mutate=True)
        if model is None:
            return
        model.set_inputs(buttons=self.buttons_input.value(), switches=self.switches_input.value())
        self.owner._refresh_execution()
        self.owner._sync_actions()

    def inject_rx(self, _checked=False):
        model = self._model(mutate=True)
        if model is None:
            return False
        try:
            data = (bytes.fromhex(self.rx_input.text()) if self.rx_format.currentIndex() == 1
                    else self.rx_input.text().encode('utf-8'))
            if not data:
                raise ValueError('Enter at least one byte')
            model.inject_uart(data, framing_error=self.framing_error.isChecked())
        except (ValueError, TypeError) as error:
            self.operation_label.setText(f'RX input error: {error}')
            return False
        self.operation_label.setText(f'Injected {len(data)} virtual RX bytes.')
        self.rx_input.clear()
        self.owner._refresh_execution()
        self.owner._sync_actions()
        return True

    def advance_ticks(self, _checked=False):
        model = self._model(mutate=True)
        if model is None:
            return False
        model.advance_ticks(self.ticks_input.value())
        self.operation_label.setText(f'Advanced {self.ticks_input.value()} peripheral ticks.')
        self.owner._refresh_execution()
        self.owner._sync_actions()
        return True

    def refresh_state(self):
        self.sync_controls()
        model = self._model()
        if model is None:
            self.state_label.setText('Assemble a program to start simulation.')
            self.led_value.setText('—')
            self.display_value.setText('—')
            self.fifo_value.setText('—')
            self.peripheral_state.clear()
            self.tx_output.clear()
            self.tx_hex.clear()
            self._last_output = None
            self._last_state = None
            return
        reason = 'running' if self.owner.running else (model.stop_reason or 'ready')
        self.state_label.setText(
            f'PC=0x{model.pc:04X}   {reason}   retired={model.instructions_retired}   '
            f'ticks={model.cycle}   undo={model.history_size}')
        self.led_value.setText(f'0x{model.peek_data(0xff00) & 15:X}')
        self.display_value.setText(f'0x{model.peek_data(0xff30):04X}')
        self.fifo_value.setText(f'0x{model.peek_data(0xff41):04X} / 0x{model.peek_data(0xff42):04X}')
        state = model.peripherals.snapshot(include_output=False)
        # The TX terminal is bounded separately; avoid duplicating its full log
        # in a periodically rendered state dump.
        state = {key: value for key, value in state.items() if key not in ('uart_output', 'tx_output')}
        if isinstance(state.get('uart'), dict):
            state['uart'] = {key: value for key, value in state['uart'].items()
                             if key not in ('output', 'uart_output', 'tx_output')}
        uart = state['uart']
        self.fifo_value.setText(
            f'RX {uart["rx_count"]}/{uart["fifo_depth"]}, TX {uart["tx_count"]}/{uart["fifo_depth"]}, '
            f'{"busy" if uart["busy"] else "idle"}; status=0x{uart["status"]:02X}, errors=0x{uart["errors"]:02X}')
        rendered = json.dumps(state, indent=2, sort_keys=True)
        if rendered != self._last_state:
            self._last_state = rendered
            self.peripheral_state.setPlainText(rendered)
        output = bytes(model.peripherals.uart_output[-self.TERMINAL_BYTES:])
        if output != self._last_output:
            self._last_output = output
            self.tx_output.setPlainText(output.decode('utf-8', errors='replace'))
            self.tx_hex.setText(output.hex(' '))
            self.tx_output.verticalScrollBar().setValue(self.tx_output.verticalScrollBar().maximum())
        gpio = state.get('gpio', state)
        for widget, name in ((self.buttons_input, 'buttons'), (self.switches_input, 'switches')):
            value = gpio.get(name)
            if value is not None:
                widget.blockSignals(True)
                widget.setValue(int(value) & 15)
                widget.blockSignals(False)

    def showEvent(self, event):
        self.refresh_state()
        self._refresh_timer.start()
        super().showEvent(event)

    def hideEvent(self, event):
        self._refresh_timer.stop()
        super().hideEvent(event)
