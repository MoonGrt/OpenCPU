def coe_to_mi(coe_filename, mif_filename):
    head = ''
    depth = 0
    radix = 0
    # 打开 .coe 文件并读取内容
    with open(coe_filename, 'r') as coe_file:
        # 将内容写入 .mif 文件
        with open(mif_filename, 'w') as mif_file:
            coe_lines = coe_file.readlines()
            data = 0
            # 过滤出 .coe 文件中的数据行
            for line in coe_lines:
                line = line.strip()
                if line.startswith('memory_initialization_radix='):
                    radix = int(line.split('=')[1].strip(';'))
                elif line.startswith('memory_initialization_vector='):
                    # gain the next line data
                    pass
                else:
                    depth += 1
                    data = line.split(';')[0].split(',')[0]
                    mif_file.write(str(data)+'\n')
            if (radix == 2):
                head += '#File_format=Bin\n'
                width = f'#Data_width={len(data)}\n'
            elif (radix == 16):
                head += '#File_format=Hex\n'
                width = f'#Data_width={len(data)*4}\n'
            head += f'#Address_depth={depth}\n'
            head += width

    # 写入文件头
    with open(mif_filename, 'r') as file:
        data = file.read()
    with open(mif_filename, 'w') as file:
        file.write(head + data)


coe_filename = 'tao.coe'
mif_filename = 'tao.mi'

coe_to_mi(coe_filename, mif_filename)
