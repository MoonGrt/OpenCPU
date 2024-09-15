def hex_to_binary(input_file, output_file):
    # 打开输入文件和输出文件
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        # 逐行读取输入文件
        for line in infile:
            # 去除换行符和空白字符，并确保行不是空的
            hex_data = line.strip()
            if hex_data:
                # 将十六进制转换为整数
                decimal_value = int(hex_data, 16)
                # 将整数转换为二进制字符串（去掉前缀 '0b'），并确保是8位数
                binary_value = f'{decimal_value:08b}'
                outfile.write(binary_value + '\n')
    print(f"二进制数据已成功逐行写入到 {output_file} 文件中。")

# 调用函数示例
hex_to_binary('init_memh', 'output')
