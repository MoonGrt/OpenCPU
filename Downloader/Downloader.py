import serial, threading, sys, time
from PyQt5.QtWidgets import QDialog, QApplication
from Serial import Serial

# 下载器
class downloader:
    def __init__(self):
        self.Serial = Serial()

    def download_setting(self):
        # 打开串口配置窗口
        if self.Serial.exec_() == QDialog.Accepted:
            # 配置串口
            self.Serial.serial_init(self.Serial.get_config())

    def download_open(self):
        return self.Serial.serial_open()

    def download_close(self):
        self.Serial.serial_close()

    def download(self, code, HEX=False):
        # 下载数据到串口
        if self.Serial.serial_com.is_open:
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
                    self.Serial.serial_com.write(data)
                    print(byte_str)
                    # time.sleep(0.005)  # 等待片刻以确保数据传输完成


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
    Downloader = downloader()

    # Downloader.download_setting()
    Downloader.Serial.serial_init(param)
    if Downloader.download_open():
        print("Port open successful\n")
        Downloader.download(code_b)
        Downloader.download_close()
    else:
        print("Port occupied\n")

    sys.exit()
