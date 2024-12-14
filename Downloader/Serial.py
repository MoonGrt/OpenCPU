from PyQt5.QtWidgets import QDialog, QFormLayout, QComboBox, QPushButton, QApplication
from PyQt5.QtGui import QIcon
import serial, sys
import serial.tools.list_ports

class Serial(QDialog):
    def __init__(self):
        super().__init__()
        self.serial_com = serial.Serial()
        self.init_ui()

    def init_ui(self):
        # 设置主窗口属性
        self.resize(200, 200)  # 默认居中
        self.setWindowTitle('Serial')

        layout = QFormLayout()
        self.setWindowIcon(QIcon('icons/serial.svg'))

        # COM端口选择
        self.com_line_edit = QComboBox()
        self.com_line_edit.addItems([])
        layout.addRow('COM Port:', self.com_line_edit)

        # 波特率选择
        self.baud_combo_box = QComboBox()
        self.baud_combo_box.addItems(['4800', '9600', '19200', '115200', '230400'])  # Add your desired baud rates
        self.baud_combo_box.setCurrentText('115200')  # Default value
        layout.addRow('Baud Rate:', self.baud_combo_box)

        # 数据位选择
        self.data_bits_combo_box = QComboBox()
        self.data_bits_combo_box.addItems(['5', '6', '7', '8', '9', '10'])  # Add your desired data bits
        self.data_bits_combo_box.setCurrentText('8')  # Default value
        layout.addRow('Data Bits:', self.data_bits_combo_box)

        # 校验位选择
        self.parity_combo_box = QComboBox()
        self.parity_combo_box.addItems(['None', 'Odd', 'Even', 'Mark'])  # Add your desired parity options
        self.parity_combo_box.setCurrentText('None')  # Default value
        layout.addRow('Parity:', self.parity_combo_box)

        # 停止位选择
        self.stop_bit_combo_box = QComboBox()
        self.stop_bit_combo_box.addItems(['1', '1.5', '2'])  # Add your desired stop bits
        self.stop_bit_combo_box.setCurrentText('1')  # Default value
        layout.addRow('Stop Bit:', self.stop_bit_combo_box)

        # 确定按钮
        ok_button = QPushButton('确定')
        ok_button.clicked.connect(self.accept)

        # 刷新按钮
        refresh_button = QPushButton('刷新')
        refresh_button.clicked.connect(self.refresh_ports)
        self.refresh_ports()

        layout.addRow(refresh_button, ok_button)
        self.setLayout(layout)

    def get_config(self):
        # 获取串口设置
        return {
            'port': self.com_line_edit.currentText(),
            'baud_rate': int(self.baud_combo_box.currentText()),
            'data_bits': int(self.data_bits_combo_box.currentText()),
            'parity': self.parity_combo_box.currentText(),
            'stop_bit': float(self.stop_bit_combo_box.currentText())
        }
    
    def refresh_ports(self):
        # 清除 com_line_edit 下拉框中的现有项
        self.com_line_edit.clear()
        # 使用 pyserial 的 list_ports 获取可用的 COM 端口列表
        ports = [port.device for port in serial.tools.list_ports.comports()]
        # 将端口添加到下拉框中
        self.com_line_edit.addItems(ports)

    def serial_init(self, param):
        # 串口参数映射
        if 'port' in param:
            self.serial_com.port = param.get('port')
        if 'baud_rate' in param:
            self.serial_com.baudrate = param.get('baud_rate')
        if 'data_bits' in param:
            # 将字符串映射为相应的 serial 模块的常量
            bytesize_mapping = {'5': serial.FIVEBITS, '6': serial.SIXBITS, '7': serial.SEVENBITS, '8': serial.EIGHTBITS}
            self.serial_com.bytesize = bytesize_mapping.get(param.get('data_bits'), serial.EIGHTBITS)
        if 'parity' in param:
            # 将字符串映射为相应的 serial 模块的常量
            parity_mapping = {'None': serial.PARITY_NONE, 'Even': serial.PARITY_EVEN, 'Odd': serial.PARITY_ODD}
            self.serial_com.parity = parity_mapping.get(param.get('parity'), serial.PARITY_NONE)
        if 'stop_bit' in param:
            # 将字符串映射为相应的 serial 模块的常量
            stopbits_mapping = {'1': serial.STOPBITS_ONE, '1.5': serial.STOPBITS_ONE_POINT_FIVE, '2': serial.STOPBITS_TWO}
            self.serial_com.stopbits = stopbits_mapping.get(param.get('stop_bit'), serial.STOPBITS_ONE)

    def serial_open(self):
        # 打开串口
        try:
            if not self.serial_com.is_open:
                self.serial_com.open()
                return self.serial_com.is_open
            return False
        except:
            print("Serial open error!")

    def serial_close(self):
        # 关闭串口
        if self.serial_com.is_open:
            self.serial_com.close()

    # def serial_send(self):
    #     # 串口发送
    #     if self.serial_com.is_open:
    #         self.serial_com.close()

    # def serial_recv(self):
    #     # 串口接收
    #     if self.serial_com.is_open:
    #         self.serial_com.close()

    # def receive_data(self):
    #     # 接收串口数据的线程函数
    #     while not self.stop_event.is_set():
    #         if self.serial_com.is_open:
    #             try:
    #                 received_data = self.serial_com.readline().decode('utf-8').strip()
    #                 print(f"Received data: {received_data}")
    #                 # 在这里添加对接收数据的处理
    #             except serial.SerialException as e:
    #                 print(f"Error reading from serial port: {e}")
    #         else:
    #             print("Port not open.")
    #         # 添加小延迟以避免高CPU使用率
    #         threading.Event().wait(0.1)

    # def start_receiving(self):
    #     # 启动接收线程
    #     if not self.is_receiving:
    #         self.is_receiving = True
    #         self.stop_event.clear()  # Clear the stop_event before starting the thread
    #         self.receive_thread = threading.Thread(target=self.receive_data)
    #         self.receive_thread.start()

    # def stop_receiving(self):
    #     # 停止接收线程
    #     self.is_receiving = False
    #     if self.receive_thread:
    #         self.stop_event.set()  # Set the stop_event to signal the thread to stop
    #         self.receive_thread.join()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    serial_dialog = Serial()
    serial_dialog.exec_()

    # 在窗口关闭后获取用户选择的配置
    config = serial_dialog.get_config()
    print('Selected Serial Configuration:', config)

    sys.exit()