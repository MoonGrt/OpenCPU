import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit, QComboBox, QLineEdit, QLabel, QHBoxLayout
from PyQt5.QtCore import QIODevice, QByteArray
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo

class SerialComm(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()
        self.serial_port = QSerialPort()
        self.serial_port.readyRead.connect(self.read_data)  # 连接 readyRead 信号到 read_data 槽

    def initUI(self):
        self.setWindowTitle('串口通信软件')
        self.setGeometry(100, 100, 500, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # 选择 COM 端口
        self.port_combo = QComboBox()
        self.refresh_ports()
        layout.addWidget(QLabel("选择 COM 端口:"))
        layout.addWidget(self.port_combo)

        # 选择波特率
        self.baud_rate_combo = QComboBox()
        self.baud_rate_combo.addItems(["9600", "19200", "38400", "57600", "115200"])
        layout.addWidget(QLabel("选择波特率:"))
        layout.addWidget(self.baud_rate_combo)

        # 选择数据位
        self.data_bits_combo = QComboBox()
        self.data_bits_combo.addItems(["5", "6", "7", "8"])
        layout.addWidget(QLabel("选择数据位:"))
        layout.addWidget(self.data_bits_combo)

        # 选择校验位
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(["None", "Odd", "Even"])
        layout.addWidget(QLabel("选择校验位:"))
        layout.addWidget(self.parity_combo)

        # 选择停止位
        self.stop_bits_combo = QComboBox()
        self.stop_bits_combo.addItems(["1", "1.5", "2"])
        layout.addWidget(QLabel("选择停止位:"))
        layout.addWidget(self.stop_bits_combo)

        self.open_button = QPushButton('打开串口')
        self.open_button.clicked.connect(self.toggle_port)
        layout.addWidget(self.open_button)

        self.send_edit = QLineEdit()
        layout.addWidget(self.send_edit)

        self.send_button = QPushButton('发送')
        self.send_button.clicked.connect(self.send_data)
        layout.addWidget(self.send_button)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

    def refresh_ports(self):
        """刷新可用的 COM 端口"""
        self.port_combo.clear()
        ports = QSerialPortInfo.availablePorts()
        for port in ports:
            self.port_combo.addItem(port.portName())

    def toggle_port(self):
        """打开或关闭串口"""
        if not self.serial_port.isOpen():
            port_name = self.port_combo.currentText()
            baud_rate = int(self.baud_rate_combo.currentText())
            data_bits = int(self.data_bits_combo.currentText())
            parity = self.parity_combo.currentText()
            stop_bits = self.stop_bits_combo.currentText()

            self.serial_port.setPortName(port_name)
            self.serial_port.setBaudRate(baud_rate)

            # 设置数据位
            if data_bits == 5:
                self.serial_port.setDataBits(QSerialPort.Data5)
            elif data_bits == 6:
                self.serial_port.setDataBits(QSerialPort.Data6)
            elif data_bits == 7:
                self.serial_port.setDataBits(QSerialPort.Data7)
            else:
                self.serial_port.setDataBits(QSerialPort.Data8)

            # 设置校验位
            if parity == "None":
                self.serial_port.setParity(QSerialPort.NoParity)
            elif parity == "Odd":
                self.serial_port.setParity(QSerialPort.OddParity)
            else:
                self.serial_port.setParity(QSerialPort.EvenParity)

            # 设置停止位
            if stop_bits == "1":
                self.serial_port.setStopBits(QSerialPort.OneStop)
            elif stop_bits == "1.5":
                self.serial_port.setStopBits(QSerialPort.OneAndHalfStop)
            else:
                self.serial_port.setStopBits(QSerialPort.TwoStop)

            self.serial_port.setFlowControl(QSerialPort.NoFlowControl)
            try:
                if self.serial_port.open(QIODevice.ReadWrite):
                    self.open_button.setText('关闭串口')
                    self.text_edit.append(f"串口 {port_name} 已打开")
                else:
                    self.text_edit.append(f"打开串口失败: {self.serial_port.errorString()}")
            except Exception as e:
                self.text_edit.append(f"打开串口失败: {e}")
        else:
            self.serial_port.close()
            self.open_button.setText('打开串口')
            self.text_edit.append(f"串口 {self.serial_port.portName()} 已关闭")

    def send_data(self):
        """发送数据"""
        if self.serial_port.isOpen():
            data = self.send_edit.text()  # 获取用户输入的文本
            try:
                byte_array = QByteArray()
                byte_array.append(data.encode('ascii'))  # 将文本编码为 ASCII 字符
                self.serial_port.write(byte_array)
                self.text_edit.append(f"发送数据: {data}")
            except UnicodeEncodeError as ue:
                self.text_edit.append(f"发送数据失败: 输入包含非 ASCII 字符 ({ue})")
            except Exception as e:
                self.text_edit.append(f"发送数据失败: {e}")

    def read_data(self):
        """读取接收的数据"""
        if self.serial_port.isOpen():
            try:
                data = self.serial_port.readAll()
                if not data.isEmpty():
                    self.text_edit.append(f"接收到数据 ({len(data)} bytes): {data.toHex().data().decode('utf-8')}")
            except Exception as e:
                self.text_edit.append(f"读取数据失败: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SerialComm()
    window.show()
    sys.exit(app.exec_())
