def binary_to_hex(input_file, output_file):
    try:
        # 打开输入文件和输出文件
        with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
            # 逐行读取输入文件
            for line in infile:
                # 去除换行符和空白字符，并确保行不是空的
                binary_data = line.strip()
                if binary_data:
                    try:
                        # 将二进制转换为十六进制
                        hex_value = f'{int(binary_data, 2):x}'
                        # 计算所需的十六进制字符长度，每4个二进制位对应1个十六进制字符
                        hex_len = (len(binary_data) + 3) // 4
                        # 用0填充至计算出的十六进制字符长度
                        hex_value = hex_value.zfill(hex_len)
                        outfile.write(hex_value + '\n')
                    except ValueError:
                        print(f"无法将以下行转换为十六进制: {binary_data}")
        print(f"十六进制数据已成功逐行写入到 {output_file} 文件中。")
    except FileNotFoundError:
        print(f"文件 {input_file} 未找到，请检查文件路径。")
    except Exception as e:
        print(f"发生错误: {e}")

# 调用函数示例
binary_to_hex('lw_sw', 'output')
