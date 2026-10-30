"""Nonblocking serial transfers, including short writes and disconnect errors."""
from PyQt5.QtCore import QIODevice, QObject, QTimer, pyqtSignal
from PyQt5.QtSerialPort import QSerialPort

from ..core.image import encode_image


class SerialTransport(QObject):
    received = pyqtSignal(bytes)
    connection_changed = pyqtSignal(bool)
    error = pyqtSignal(str)
    download_finished = pyqtSignal(int)
    progress = pyqtSignal(int, int)

    def __init__(self, parent=None, port=None, timeout_ms=5000):
        super().__init__(parent)
        self.port = port if port is not None else QSerialPort(self)
        self._payload = b""
        self._queued = self._written = 0
        self._closing = False
        self._opening = False
        self._last_error = None
        self._timeout_ms = timeout_ms
        self._timeout = QTimer(self)
        self._timeout.setSingleShot(True)
        self._timeout.timeout.connect(lambda: self._fail('Serial write timed out'))
        self._retry = QTimer(self)
        self._retry.setSingleShot(True)
        self._retry.timeout.connect(self._pump)
        self.port.readyRead.connect(self._read)
        self.port.bytesWritten.connect(self._bytes_written)
        self.port.errorOccurred.connect(self._port_error)

    @property
    def is_open(self):
        return self.port.isOpen()

    @property
    def busy(self):
        return bool(self._payload)

    def open(self, settings):
        self.close()
        self._opening = True
        try:
            settings.validate()
            self.port.setPortName(settings.port)
            choices = (
                (self.port.setBaudRate, settings.baud_rate),
                (self.port.setDataBits, {5: QSerialPort.Data5, 6: QSerialPort.Data6,
                                         7: QSerialPort.Data7, 8: QSerialPort.Data8}[settings.data_bits]),
                (self.port.setParity, {'None': QSerialPort.NoParity, 'Odd': QSerialPort.OddParity,
                                      'Even': QSerialPort.EvenParity, 'Mark': QSerialPort.MarkParity,
                                      'Space': QSerialPort.SpaceParity}[settings.parity]),
                (self.port.setStopBits, {'1': QSerialPort.OneStop, '1.5': QSerialPort.OneAndHalfStop,
                                        '2': QSerialPort.TwoStop}[str(settings.stop_bits)]),
                (self.port.setFlowControl, QSerialPort.NoFlowControl),
            )
            for setter, value in choices:
                if setter(value) is False:
                    raise ValueError(self.port.errorString() or 'The port rejected the selected settings')
            if not self.port.open(QIODevice.ReadWrite):
                raise OSError(self.port.errorString() or 'Unable to open the serial port')
        except (OSError, ValueError, RuntimeError) as error:
            self.error.emit(str(error))
            return False
        finally:
            self._opening = False
        self.connection_changed.emit(True)
        return True

    def close(self):
        was_open = self.is_open
        cancelled = self.busy
        self._closing = True
        try:
            self._clear_transfer()
            if was_open:
                self.port.close()
        finally:
            self._closing = False
        if was_open:
            self.connection_changed.emit(False)
        if cancelled:
            self.error.emit('Download cancelled because the port was closed')

    def _clear_transfer(self):
        self._timeout.stop()
        self._retry.stop()
        self._payload = b""
        self._queued = self._written = 0

    def download(self, binary, hexadecimal=False):
        # Validate every word before touching the device; never send a valid prefix.
        payload = encode_image(binary, hexadecimal=hexadecimal)
        if not self.is_open:
            raise ValueError('Open a serial port before downloading')
        if self.busy:
            raise ValueError('A download is already in progress')
        self._payload = payload
        self._queued = self._written = 0
        self._last_error = None
        self.progress.emit(0, len(payload))
        self._timeout.start(self._timeout_ms)
        self._pump()
        if self._last_error:
            raise RuntimeError(self._last_error)
        return len(payload)

    def _pump(self):
        if not self.busy or self._queued >= len(self._payload):
            return
        try:
            count = self.port.write(self._payload[self._queued:])
            if not self.busy:
                return  # A synchronous error signal may already have cancelled it.
            if count < 0:
                self._fail(self.port.errorString() or 'Serial write failed')
            elif count == 0:
                self._retry.start(10)
            else:
                self._queued += count
                if self._queued < len(self._payload):
                    self._retry.start(0)
        except (OSError, RuntimeError) as error:
            self._fail(str(error))

    def _bytes_written(self, count):
        if not self.busy:
            return
        self._written = min(len(self._payload), self._written + count)
        self.progress.emit(self._written, len(self._payload))
        self._timeout.start(self._timeout_ms)
        if self._written == len(self._payload):
            total = len(self._payload)
            self._clear_transfer()
            self.download_finished.emit(total)
        else:
            self._pump()

    def _read(self):
        try:
            data = bytes(self.port.readAll())
            if data:
                self.received.emit(data)
        except (OSError, RuntimeError) as error:
            self._fail(str(error))

    def _port_error(self, code):
        if code == QSerialPort.NoError or self._closing or self._opening:
            return
        if code in (QSerialPort.ResourceError, QSerialPort.DeviceNotFoundError,
                    QSerialPort.PermissionError, QSerialPort.WriteError, QSerialPort.ReadError):
            self._fail(self.port.errorString() or 'Serial device error')

    def _fail(self, message):
        self._last_error = message
        self._clear_transfer()
        self.close()
        self.error.emit(message)
