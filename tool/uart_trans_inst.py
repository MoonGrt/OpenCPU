import sys
import serial
import time

serial_com = serial.Serial()

# 串口初始化
# 串口参数：115200, 8 N 1
def serial_init():
    serial_com.port = sys.argv[1]
    serial_com.baudrate = 115200
    serial_com.bytesize = serial.EIGHTBITS
    serial_com.parity = serial.PARITY_NONE
    serial_com.stopbits = serial.STOPBITS_ONE
    serial_com.xonxoff = False
    serial_com.rtscts = False
    serial_com.dsrdtr = False

    if serial_com.is_open == False:
        serial_com.open()
        if serial_com.is_open:
            return 0
    else:
        return -1

def serial_deinit():
    if serial_com.is_open == True:
        serial_com.close()

# 主函数
def main():
    if serial_init() == 0:
        with open(sys.argv[2], 'r') as file:
            for line in file:
                binary_string = line.strip()

                # 检查二进制字符串是否只包含0和1
                if all(bit in '01' for bit in binary_string):
                    decimal_number = int(binary_string, 2)
                    hex_string = hex(decimal_number)[2:]    # 转化为16进制并去除前缀'0x'
                    hex_string = hex_string.zfill(4)        # 填充到4位

                    byte_data = bytes.fromhex(hex_string)   # 将16进制字符串转化为字节
                    serial_com.write(byte_data)# 发送字节数据到UART
                    print(hex_string)
                    time.sleep(0.001)
                    # break
                else:
                    print(f"文件包含无效的二进制字符串: {binary_string}")
    else:
        print('!!! serial init failed !!!')

    serial_deinit()

# 程序入口
if __name__ == "__main__":
    if (len(sys.argv) != 3):
        print('Usage: python ' + sys.argv[0] + ' COMx ' + 'inst_file')
    else:
        main()
