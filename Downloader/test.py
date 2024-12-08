import serial
import time

def send_hex_data(serial_port, baud_rate, hex_data):
    """
    通过串口发送十六进制数据，每个字节逐个发送。
    
    :param serial_port: 串口号
    :param baud_rate: 波特率
    :param hex_data: 十六进制数据字符串，每行数据用空格分隔
    """
    # 打开串口
    with serial.Serial(serial_port, baud_rate, timeout=1) as ser:
        # 处理数据
        lines = [line.strip() for line in hex_data.strip().split('\n') if line.strip()]
        
        # 逐字节发送
        for hex_str in lines:
            for i in range(0, len(hex_str), 2):
                byte_str = hex_str[i:i+2]
                data = bytes.fromhex(byte_str)
                
                # 发送数据
                ser.write(data)
                print(f"Sent: {byte_str}")
                
                # 等待片刻以确保数据传输完成
                time.sleep(0.01)

# 数据
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

# 使用函数发送数据
send_hex_data('COM12', 115200, code_h)
