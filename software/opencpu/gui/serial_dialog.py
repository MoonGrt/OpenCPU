"""The one serial settings dialog shared by the two existing window layouts."""
from PyQt5.QtSerialPort import QSerialPortInfo
from PyQt5.QtWidgets import QComboBox, QDialog, QFormLayout, QPushButton

from ..transport.settings import SerialSettings
from .resources import icon


class SerialDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(200, 200)
        self.setWindowTitle("Serial")
        self.setWindowIcon(icon("serial.svg"))
        layout = QFormLayout(self)
        self.port_combo = QComboBox()
        self.baud_combo = self._combo(['4800', '9600', '19200', '115200', '230400'], '115200')
        self.data_bits_combo = self._combo(['5', '6', '7', '8', '9', '10'], '8')
        self.parity_combo = self._combo(['None', 'Odd', 'Even', 'Mark'], 'None')
        self.stop_bits_combo = self._combo(['1', '1.5', '2'], '1')
        for label, widget in (("COM Port:", self.port_combo), ("Baud Rate:", self.baud_combo),
                              ("Data Bits:", self.data_bits_combo), ("Parity:", self.parity_combo),
                              ("Stop Bit:", self.stop_bits_combo)):
            layout.addRow(label, widget)
        refresh = QPushButton('刷新')
        refresh.clicked.connect(self.refresh_ports)
        accept = QPushButton('确定')
        accept.clicked.connect(self.accept)
        layout.addRow(refresh, accept)
        self.refresh_ports()

    @staticmethod
    def _combo(values, current):
        combo = QComboBox()
        combo.addItems(values)
        combo.setCurrentText(current)
        return combo

    def refresh_ports(self):
        selected = self.port_combo.currentText()
        names = [port.portName() for port in QSerialPortInfo.availablePorts()]
        self.port_combo.clear()
        self.port_combo.addItems(names)
        if selected:
            if selected not in names:
                self.port_combo.addItem(selected)
            self.port_combo.setCurrentText(selected)

    def set_settings(self, settings):
        for combo, value in ((self.port_combo, settings.port), (self.baud_combo, str(settings.baud_rate)),
                             (self.data_bits_combo, str(settings.data_bits)), (self.parity_combo, settings.parity),
                             (self.stop_bits_combo, str(settings.stop_bits))):
            if value and combo.findText(value) < 0:
                combo.addItem(value)
            combo.setCurrentText(value)

    def settings(self):
        return SerialSettings(self.port_combo.currentText(), int(self.baud_combo.currentText()),
                              int(self.data_bits_combo.currentText()), self.parity_combo.currentText(),
                              self.stop_bits_combo.currentText())
