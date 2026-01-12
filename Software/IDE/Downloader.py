import serial, threading

# 下载器
class downloader:
    def __init__(self):
        self.serial_com = serial.Serial()
        # self.receive_thread = None
        # self.stop_event = threading.Event()  # 用于通知接收线程停止的事件
        # self.is_receiving = False
    
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
        if not self.serial_com.is_open:
            self.serial_com.open()
            return self.serial_com.is_open
        return False

    def serial_close(self):
        # 关闭串口
        if self.serial_com.is_open:
            self.serial_com.close()

    def download(self, code):
        # 下载数据到串口
        if self.serial_com.is_open:
            lines = [line.strip() for line in code.splitlines() if line.strip()]
            for line in lines:
                if all(bit in '01' for bit in line):
                    decimal_number = int(line, 2)
                    hex_string = hex(decimal_number)[2:].zfill(4)
                    byte_data = bytes.fromhex(hex_string)
                    self.serial_com.write(byte_data)
                    # print(hex_string)
                else:
                    print(f"Invalid binary string in the file: {line}")
        else:
            print("Failed\n")

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

if __name__ == "__main__":
    param = {
            'port': 'COM24',
            'baud_rate': 115200,
            'data_bits': 8,
            'parity': None,
            'stop_bit': 1
        }

    code = """
    0000101000111001
    0010100000111000
    0000111100111001
    0011000000111000
    0010100000110111
    0011000001010111
    0110001000101000
    0010100000110111
    0011000001010111
    0000001000100001
    0010100000111000
    0001000000011010
    0011000000110111
    0010100001010111
    0000001000100001
    0011000000111000
    """

    Downloader = downloader()
    Downloader.serial_init(param)

    Downloader.serial_open()

    Downloader.start_receiving()
    Downloader.download(code)
    Downloader.download(code)
    Downloader.stop_receiving()

    Downloader.serial_close()
