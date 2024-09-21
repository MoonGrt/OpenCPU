import sys
from PyQt5.QtWidgets import QDialog, QApplication
from SerialConfig import SerialConfig
from PyQt5.QtCore import QIODevice, QByteArray
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo

# 串口
class Serial:
    def __init__(self):
        self.serial_port = QSerialPort()
        # self.serial_port.readyRead.connect(self.read_data)  # 连接 readyRead 信号到 read_data 槽
        self.SerialConfig = SerialConfig()

    def download_setting(self):
        # 打开串口配置窗口
        self.SerialConfig.exec_()

    def serial_init(self):
        param = self.SerialConfig.get_config()
        if not self.serial_port.isOpen():
            port_name = param["port"]
            baud_rate = param["baud_rate"]
            data_bits = param["data_bits"]
            parity = param["parity"]
            stop_bits = param["stop_bit"]

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


    def open(self):
        # 打开串口
        self.serial_init()
        try:
            if self.serial_port.open(QIODevice.ReadWrite):
                return self.serial_port.isOpen()
            else:
                print(f"打开串口失败: {self.serial_port.errorString()}")
                return False
        except Exception as e:
            print(f"打开串口失败: {e}")

    def close(self):
        # 关闭串口        
        if self.serial_port.isOpen():
            self.serial_port.close()

    def download(self, code, HEX=False):
        # 下载数据到串口
        if self.serial_port.isOpen():
            if not HEX and code:
                code = self.binary_to_hex(code)
            self.send_hex_data(code)
        else:
            print("Download failed!")

    def binary_to_hex(self, binary_str):
        try:
            # 去除多余的空白字符和换行符，并将数据按行分割
            lines = binary_str.strip().split('\n')
            hex_lines = []
            for line in lines:
                # 去除每行的空白字符
                binary_data = line.strip()
                if not all(bit in '01' for bit in binary_data):
                    raise ValueError("某一行不是有效的二进制数")
                # 将二进制字符串转换为十六进制字符串
                hex_value = f'{int(binary_data, 2):X}'
                # 计算十六进制字符长度，每4个二进制位对应1个十六进制字符
                hex_len = (len(binary_data) + 3) // 4
                # 用0填充至计算出的十六进制字符长度
                hex_value = hex_value.zfill(hex_len)
                hex_lines.append(hex_value)
            return '\n'.join(hex_lines)
        except ValueError as e:
            print(f"错误: {e}")
            return None

    def send_hex_data(self, hex_data):
            # 处理数据
            lines = [line.strip() for line in hex_data.strip().split('\n') if line.strip()]
            # 逐字节发送
            for hex_str in lines:
                for i in range(0, len(hex_str), 2):
                    byte_str = hex_str[i:i+2]
                    data = bytes.fromhex(byte_str)
                    # 发送数据
                    self.serial_port.write(data)
                    print(byte_str)
                    # time.sleep(0.005)  # 等待片刻以确保数据传输完成

    def read_data(self):
        """读取接收的数据"""
        if self.serial_port.isOpen():
            try:
                data = self.serial_port.readAll()
                if not data.isEmpty():
                    print(f"recv ({len(data)} bytes): {data.toHex().data().decode('utf-8')}")
            except Exception as e:
                print(f"Error: {e}")


if __name__ == "__main__":
    code_b = """
        0000000000011111
        1111111100111110
        0100000000110110
        0001000001011110
        0000000101000000
        0000001001011000
        0000100001011001
        0000100001111000
        0111100001110101
        0000000101111001
        0000000000011100
        0000000000000000
    """
    code_h = """
        001f
        ff3e
        4036
        105e
        0140
        0258
        0859
        0878
        7875
        0179
        001c
        0000
    """
    param = {
            'port': 'COM12',
            'baud_rate': 115200,
            'data_bits': 8,
            'parity': None,
            'stop_bit': 1
        }

    app = QApplication(sys.argv)
    serial_port = Serial()

    serial_port.download_setting()  # 可以不设置，直接打开
    if serial_port.open():
        print("Port open successful\n")
        serial_port.download(code_b)
        serial_port.close()
        print("Port close\n")
    else:
        print("Port occupied\n")

    sys.exit()
