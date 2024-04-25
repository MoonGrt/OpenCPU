import re

"""
词法分析(Lexical Analysis): 也称为扫描器,负责将源代码分割成词法单元(token),比如关键字、标识符、常量等。这一阶段通常使用正则表达式和有限自动机。
语法分析(Syntax Analysis): 又称为解析器,负责将词法单元组成的序列转换为语法树(Parse Tree)。这一阶段通常使用文法规则和上下文无关文法。
语义分析(Semantic Analysis): 在语法分析的基础上,进一步检查程序的语义是否符合语言规范,进行类型检查等。这一阶段通常包括建立符号表和语义树。
中间代码生成(Intermediate Code Generation): 将语法树或语义树转换为中间代码,这种代码更容易进行优化和后续步骤的处理。
代码优化(Code Optimization): 对生成的中间代码进行优化,以提高程序的性能和效率。
代码生成(Code Generation): 将优化后的中间代码转换为目标机器代码。这一阶段的目标是生成高效且符合目标计算机架构的代码。
代码解释和执行: 将生成的目标代码在计算机上执行，或者通过解释器逐行执行源代码。
"""

# 词法分析器
def lexer(program):
    pattern = r'\b(?:print|if|else|for|while|return|def)\b|\d+|\w+|"[^"]*"|[-+*/<>=;(){}#,]'
    tokens = [match.group(0) for match in re.finditer(pattern, program)]
    return tokens

# 语法分析器
# 解析表达式
def parse_expression(tokens, start):
    expression = ''
    i = start
    while i < len(tokens) and tokens[i] not in (';', ')'):
        expression += tokens[i]
        i += 1
    return expression, i + 1  # 跳过 '}' 可能越界

# 解析代码块
def parse_block(tokens, start):
    block = ''
    bracket_cnt = 0
    i = start + 1  # 跳过'{'
    while i < len(tokens):
        if tokens[i] == '{':
            bracket_cnt += 1
        elif tokens[i] == '}':
            if not bracket_cnt:
                break
            else:
                bracket_cnt -= 1
        block += tokens[i] + ' '
        i += 1
    return block, i + 1  # 跳过'}'

# 解析函数定义
def parse_function(tokens, start):
    i = start + 3  # 跳过'def'、函数名和'('
    parameters = []
    while tokens[i] != ')':
        if tokens[i] != ',':
            parameters.append(tokens[i])
        i += 1
    i += 1  # 跳过')'
    body, i = parse_block(tokens, i)
    return ('function', tokens[start + 1], parameters, body.strip()), i  # 去除尾部空格

# 解析语句
def parse_statement(tokens, i, function_list):
    if tokens[i] == '#':
        abandon, i = parse_expression(tokens, i)  # 跳过语句
        return ('comment',), i
    elif tokens[i] == '/' and tokens[i + 1] == '/':
        abandon, i = parse_expression(tokens, i)  # 跳过语句
        return ('comment',), i
    elif tokens[i] == 'print':
        i += 1
        expression, i = parse_expression(tokens, i)
        return ('print', expression), i
    elif tokens[i] == 'if':
        i += 2  # 跳过'if'、'('
        condition, i = parse_expression(tokens, i)
        if_body, i = parse_block(tokens, i)
        else_body, i = parse_block(tokens, i + 1) if i < len(tokens) and tokens[i] == 'else' else ('', i)
        return ('if', condition, if_body, else_body), i
    elif tokens[i] == 'while':
        i += 2  # 跳过'while'、'('
        condition, i = parse_expression(tokens, i)
        while_body, i = parse_block(tokens, i)
        return ('while', condition, while_body), i
    elif tokens[i] == 'for':
        i += 2  # 跳过'for'、'('
        init, i = parse_expression(tokens, i)
        condition, i = parse_expression(tokens, i)
        update, i = parse_expression(tokens, i)
        body, i = parse_block(tokens, i)
        return ('for', init, condition, update, body), i
    elif tokens[i] == 'return':
        expression, i = parse_expression(tokens, i + 1)  # 跳过'return'
        return ('return', expression), i
    elif tokens[i] == 'def':
        return parse_function(tokens, i)
    elif tokens[i] in function_list and tokens[i+1] == '(':
        function_name = tokens[i]
        i += 2  # 跳过函数名、'('
        arguments = []
        while tokens[i] != ')':
            if tokens[i] != ',':
                arguments.append(int(tokens[i]))
            i += 1
        i += 2  # 跳过')'、';'
        return ('function_call', function_name, arguments), i
    else:
        # 默认为赋值语句
        variable = tokens[i]
        i += 2  # 跳过变量、等号
        value = ''
        while i < len(tokens) and tokens[i] != ';':
            value += tokens[i]
            i += 1
        return ('ASSIGN', variable, value), i + 1  # 跳过分号

# 解析器
def parser(tokens):
    i = 0
    statements = []
    function_list = []
    while i < len(tokens):
        statement, i = parse_statement(tokens, i, function_list)
        statements.append(statement)
        if statement[0] == 'function':
            function_list.append(statement[1])
    return statements


# 解释器
variables = {}
functions = {}

# 求解表达式
def evaluate(expression, vars):
    expression_variables = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', expression))
    for var in expression_variables:
        if var not in vars:
            vars[var] = 0
    return eval(expression, vars)

# 执行解释器
def interpreter(statements, variables):
    global functions
    for statement in statements:
        if statement[0] == 'ASSIGN':
            variable, value = statement[1], statement[2]
            variables[variable] = evaluate(value, variables)
        elif statement[0] == 'print':
            expression = statement[1]
            print(evaluate(expression, variables))
        elif statement[0] == 'if':
            condition, if_body, else_body = statement[1], statement[2], statement[3]
            if evaluate(condition, variables):
                interpreter(parser(lexer(if_body)), variables)
            else:
                interpreter(parser(lexer(else_body)), variables)
        elif statement[0] == 'while':
            condition, body = statement[1], statement[2]
            while evaluate(condition, variables):
                interpreter(parser(lexer(body)), variables)
        elif statement[0] == 'for':
            initialization, condition, update, body = statement[1], statement[2], statement[3], statement[4]
            variables[initialization.split('=')[0]] = evaluate(initialization.split('=')[1], variables)
            while evaluate(condition, variables):
                interpreter(parser(lexer(body)), variables)
                variables[update.split('=')[0]] = evaluate(update.split('=')[1], variables)
        elif statement[0] == 'function':
            function_name, parameters, body = statement[1], statement[2], statement[3]
            functions[function_name] = {'parameters': parameters, 'body': body}
        elif statement[0] == 'return':
            return_value = evaluate(statement[1], variables)
            return return_value
        elif statement[0] == 'function_call':
            function_name, arguments = statement[1], statement[2]
            function = functions.get(function_name)
            if function:
                function_vars = dict(zip(function['parameters'], arguments))
                interpreter(parser(lexer(function['body'])), function_vars)


# 编译器
reg = set(f'a{i}' for i in range(1, 8))  # r1到r7被视为临时寄存器 r0为saved_reg
variable_mem = {}

def get_reg(num_regs=1):
    global reg
    if len(reg) >= num_regs:
        allocated_regs = sorted(reg)[:num_regs]
        reg.difference_update(allocated_regs)
        return tuple(allocated_regs)
    else:
        raise Exception("寄存器用尽")

def release_reg(*released_regs):
    global reg
    reg.update(released_regs)

def allocate_memory(variable_mem):
    offset = -20
    for var in variable_mem:
        variable_mem[var] = f"{offset}(s0)"
        offset -= 4
    # TODO: s0

def release_memory(variable_mem, variable_name):
    if variable_name in variable_mem:
        del variable_mem[variable_name]
    else:
        raise Exception(f"变量 {variable_name} 未分配存储")

def hidden_literal(code, variable_mem):
    allocate_memory(variable_mem)
    pattern = re.compile(r'\b(?:' + '|'.join(map(re.escape, variable_mem.keys())) + r')\b')
    replaced_str = pattern.sub(lambda match: variable_mem[match.group(0)], code)
    return replaced_str

def operate(op, left, right, imm):
    # 根据运算符生成相应的汇编指令
    code = ''
    if(op == '+'):
        if(imm):
            code = f"\taddi\t{left}, {left}, {right}\n"
        else:
            code = f"\tadd\t\t{left}, {left}, {right}\n"
    elif(op == '-'):
        if(imm):
            code = f"\taddi\t{left}, {left}, {right}\n"
        else:
            code = f"\tsub\t\t{left}, {left}, {right}\n"
    return code

def generate_expression_code(expression, left_reg, right_reg):
    global variable_mem
    code = ""
    op = ""
    # 检查值是否为整数或浮点数
    if expression.isdigit():
        code = f"\tli\t\t{left_reg}, {expression}\n"
    else:
        expression_token = lexer(expression)
        # 如果是二元运算,递归处理左右操作数
        op = expression_token[1]
        left_operand, right_operand = expression_token[0], expression_token[2]
        # 将expression中的变量添加到variables中,设置为0
        for var in {left_operand, right_operand}:
            if var not in variable_mem and not var.isdigit():
                variable_mem[var] = 0
                code += f"\tli\t\t{left_reg}, 0\n"
                code += f"\tsw\t\t{left_reg}, {var}\n"

        if not left_operand.isdigit():
            code += f"\tlw\t\t{left_reg}, {left_operand}\n"
            if not right_operand.isdigit():
                code += f"\tlw\t\t{right_reg}, {right_operand}\n"
                if op in ('+', '-'):
                    code += operate(op, left_reg, right_reg, 0)
            else:
                if op in ('+', '-'):
                    code += operate(op, left_reg, right_operand, 1)
                elif op == '<':
                    code += f"\tli\t\t{right_reg}, {right_operand}\n"
                elif op == '>':
                    code += f"\tli\t\t{right_reg}, {right_operand}\n"
        else:
            code += f"\tli\t\t{left_reg}, {left_operand}\n"
            if not right_operand.isdigit():
                code += f"\tlw\t\t{right_reg}, {right_operand}\n"
                if op in ('+', '-'):
                    code += operate(op, left_reg, right_reg, 0)
            else:
                if op in ('+', '-'):
                    code += operate(op, left_reg, right_operand, 1)
                elif op == '<':
                    code += f"\tli\t\t{right_reg}, {right_operand}\n"
                elif op == '>':
                    code += f"\tli\t\t{right_reg}, {right_operand}\n"
    return code, op

def generate_jump(code, label):
    output_lines = ""
    lines = code.split('\n')
    last_line = lines[-2]
    
    try:
        last_label = re.search(r'\.L(.*):', last_line).group(1)
        lines = [line for line in lines if line.strip() != last_line and line.strip()]

        for line in lines:
            replaced_line = line.replace(f".L{last_label}", f".L{label}")
            output_lines += f"{replaced_line}\n"

        output_lines += f"\tj\t\t.L{label}\n"
    except:
        output_lines = code
        output_lines += f"\tj\t\t.L{label}\n"
        
    return output_lines

if_cnt = 1 #计数if
for_cnt = 1 #计数for
while_cnt = 1 #计数while
label_cnt = 2 # 用于生成唯一的循环标签

def compiler(statements):
    global variable_mem, label_cnt, if_cnt, while_cnt, for_cnt
    code = ""

    for statement in statements:
        if statement[0] == 'ASSIGN':
            variable, expression = statement[1], statement[2]
            if variable not in variable_mem: # 如果变量在变量字典中不存在,则初始化为0
                variable_mem[variable] = 0
            temp_reg1, temp_reg2 = get_reg(2)
            expression_code,op = generate_expression_code(expression, temp_reg1, temp_reg2)
            code += expression_code
            code += f"\tsw\t\t{temp_reg1}, {variable}\n"
            release_reg(temp_reg1, temp_reg2)
        elif statement[0] == 'print':
            expression = statement[1]
            # code += f"\tli a0, {expression}\n"
            # code += "\tcall print\n"
        elif statement[0] == 'if':
            condition, if_body, else_body = statement[1], statement[2], statement[3]
            # 生成条件评估的代码
            temp_reg1, temp_reg2 = get_reg(2)
            expression_code, op = generate_expression_code(condition, temp_reg1, temp_reg2) 
            code += expression_code
            if full_label:  # 成立不跳转
                if op == '<':
                    code += f"\tble\t\t{temp_reg2}, {temp_reg1}, .L{label_cnt}_else{if_cnt}\n"
                elif op == '>':
                    code += f"\tble\t\t{temp_reg1}, {temp_reg2}, .L{label_cnt}_else{if_cnt}\n"
            else:
                if op == '<':
                    code += f"\tble\t\t{temp_reg2}, {temp_reg1}, .L{label_cnt}\n"
                elif op == '>':
                    code += f"\tble\t\t{temp_reg1}, {temp_reg2}, .L{label_cnt}\n"
            release_reg(temp_reg1, temp_reg2)
            # 生成if体的代码
            code += compiler(parser(lexer(if_body)))
            if(else_body):
                if full_label:
                    code = generate_jump(code, f"{label_cnt+1}_if{if_cnt}")
                else:
                    code = generate_jump(code, label_cnt+1)
            # 开始else语句的唯一标签
            code += f".L{label_cnt}_else{if_cnt}:\n" if full_label else f".L{label_cnt}:\n"
            # 生成else体的代码
            code += compiler(parser(lexer(else_body)))    
            if(else_body):
                code += f".L{label_cnt+1}_if{if_cnt}:\n" if full_label else f".L{label_cnt+1}:\n"
                label_cnt += 2
            else:
                label_cnt += 1
            if_cnt += 1
        elif statement[0] == 'while':
            condition, body = statement[1], statement[2]
            # 跳到循环体的结束标签
            if full_label:
                code = generate_jump(code, f"{label_cnt}_while{while_cnt}")
            else:
                code = generate_jump(code, label_cnt)
            # 循环体的唯一标签
            code += f".L{label_cnt+1}_whilebody{while_cnt}:\n" if full_label else f".L{label_cnt+1}:\n"
            # 生成循环体的代码
            code += compiler(parser(lexer(body)))
            # 开始while循环的唯一标签
            code += f".L{label_cnt}_while{while_cnt}:\n" if full_label else f".L{label_cnt}:\n"
            # 生成条件评估的代码
            temp_reg1, temp_reg2 = get_reg(2)
            expression_code, op = generate_expression_code(condition, temp_reg1, temp_reg2) 
            code += expression_code
            if full_label:  # 成立不跳转
                if op == '>':
                    code += f"\tble\t\t{temp_reg2}, {temp_reg1}, .L{label_cnt+1}_whilebody{while_cnt}\n"
                elif op == '<':
                    code += f"\tble\t\t{temp_reg1}, {temp_reg2}, .L{label_cnt+1}_whilebody{while_cnt}\n"
            else:
                if op == '>':
                    code += f"\tble\t\t{temp_reg2}, {temp_reg1}, .L{label_cnt+1}\n"
                elif op == '<':
                    code += f"\tble\t\t{temp_reg1}, {temp_reg2}, .L{label_cnt+1}\n"
            release_reg(temp_reg1, temp_reg2)
            label_cnt += 2
            while_cnt += 1
        elif statement[0] == 'for':
            initialization, condition, update, body = statement[1], statement[2], statement[3], statement[4]
            # 生成初始化的代码
            code += compiler(parser(lexer(initialization)))
            # 跳到循环体的结束标签
            if full_label:
                code = generate_jump(code, f"{label_cnt}_for{for_cnt}")
            else:
                code = generate_jump(code, label_cnt)
            # 循环体的唯一标签
            code += f".L{label_cnt+1}_forbody{for_cnt}:\n" if full_label else f".L{label_cnt+1}:\n"
            # 生成循环体的代码
            code += compiler(parser(lexer(body)))
            # 生成更新的代码
            code += compiler(parser(lexer(update)))
            # 开始for循环的唯一标签
            code += f".L{label_cnt}_for{for_cnt}:\n" if full_label else f".L{label_cnt}:\n"
            # 生成条件评估的代码
            temp_reg1, temp_reg2 = get_reg(2)
            expression_code, op = generate_expression_code(condition, temp_reg1, temp_reg2) 
            code += expression_code
            if full_label:  # 成立不跳转
                if op == '>':
                    code += f"\tble\t\t{temp_reg2}, {temp_reg1}, .L{label_cnt+1}_forbody{for_cnt}\n"
                elif op == '<':
                    code += f"\tble\t\t{temp_reg1}, {temp_reg2}, .L{label_cnt+1}_forbody{for_cnt}\n"
            else:
                if op == '>':
                    code += f"\tble\t\t{temp_reg2}, {temp_reg1}, .L{label_cnt+1}\n"
                elif op == '<':
                    code += f"\tble\t\t{temp_reg1}, {temp_reg2}, .L{label_cnt+1}\n"
            
            release_reg(temp_reg1, temp_reg2)
            label_cnt += 2
            for_cnt += 1
            # TODO: 变量作用域
    return code

# 汇编器
opcode_dict = {
    'add' : '00000',    'addi': '10000',
    'sub' : '00001',    'subi': '10001',
    'and' : '00010',    'andi': '10010',
    'or'  : '00011',    'ori' : '10011',
    'xor' : '00100',    'xori': '10100',
    'sll' : '00101',    'slli': '10101',
    'srl' : '00110',    'srli': '10110',
    'beq' : '00111',    'lw'  : '10111',
    'ble' : '01000',    'sw'  : '11000',

    'li'  : '11001',
    'j'   : '11010'
}

def assembler(instruction):
    global opcode_dict
    machine_code = ""
    labels = {}
    address = 1

    # 遍历指令，提取标签和地址
    for line in instruction.strip().split('\n'):
        line = line.strip()
        if line:
            if line.endswith(':'):
                labels[line[:-1]] = address
            else:
                address += 1

    # 重新从头处理指令，生成机器码
    for line in instruction.strip().split('\n'):
        line = line.strip()
        if line:
            components = line.replace(',', '').split()

            # 排除标签行不进行操作码处理
            if not line.endswith(':'):
                opcode = opcode_dict.get(components[0])
                if opcode is None:
                    raise ValueError(f"未知操作码: {components[0]}")

                rd = '000'
                rs = '000'
                imm = '00000'
                Imm = '00000000'

                if components[0] in {'add', 'sub', 'and', 'or', 'xor', 'sll', 'srl'}:
                    rd = bin(int(components[1][1:]))[2:].zfill(3)
                    rs = bin(int(components[3][1:]))[2:].zfill(3)
                elif components[0] in {'addi', 'subi', 'andi', 'ori', 'xori', 'slli', 'srli'}:
                    rd = bin(int(components[1][1:]))[2:].zfill(3)
                    rs = rd
                    imm = bin(int(components[3]))[2:].zfill(5)
                elif components[0] in {'lw', 'sw'}:
                    rd = bin(int(components[1][1:]))[2:].zfill(3)
                    imm, rs = components[2][:-1].split('(')
                    imm = bin(abs(int(imm)) - 20)[2:].zfill(5)
                    rs = bin(int(rs[1:]))[2:].zfill(3)
                elif components[0] in {'ble', 'beq'}:
                    rd = bin(int(components[1][1:]))[2:].zfill(3)
                    rs = bin(int(components[2][1:]))[2:].zfill(3)
                    imm = bin(labels[components[3]])[2:].zfill(5)
                elif components[0] == 'li':
                    rd = bin(int(components[1][1:]))[2:].zfill(3)
                    Imm = bin(int(components[2]))[2:].zfill(8)
                elif components[0] == 'j':
                    Imm = bin(labels[components[1]])[2:].zfill(8)

                if components[0] == 'li':
                    machine_code += Imm + rd + opcode + '\n'
                elif components[0] == 'j':
                    machine_code += Imm + '000' + opcode + '\n'
                elif components[0] == 'ble':
                    machine_code += imm + rs + rd + opcode + '\n'
                else:
                    machine_code += imm + rs + rd + opcode + '\n'

    return machine_code

# 从文件读取程序
def read_program_from_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()
    
program_file_path = 'F:\Project\Python\Project\Compiler\code.txt'
program = read_program_from_file(program_file_path)

program = """
    X = 10;
    Y = 15;
    if(X > Y)
    {
        X = X - Y;
    }
    else
    {
        Y = Y - X;
    }
"""

# program = """
#     X = 10;
#     Y = 15;
#     if(X > Y)
#     {
#         X = X - Y;
#     }
# """ 

# program = """
#     X = 10;
#     while(X < 15)
#     {
#         X = X + 1;
#     }
# """

# program = """
#     Y = 15;
#     for(i = 0; i < 3; i = i + 1)
#     {
#         Y = Y + 2;
#     }
# """

program = """
    X = 14;
    Y = 15;
    for(i = 0; i < 3; i = i + 1)
    {
        if(X < Y)
        {
            X = X + 1;
            # print X;
        }
        else
        {
            Y = Y + 2;
            # print Y;
        }
    }
"""
# TODO: 嵌套标签还有问题 ==> 将if for while计数改为字典，左边是第几个，右边是label值

# program = """
#     def add(X, Y)
#     {
#         X = X + 1;
#         Z = X + Y;
#         print Z;
#     }
#     add(3,4);
# """


# program = """
#     X = 1;
#     # print X;
# """

full_label = True
# full_label = False

tokens = lexer(program)
statements = parser(tokens)
# interpreter(statements, variables)

assembly_code = "main:\n"
# assembly_code = ".text\n.globl main\nmain:\n"
assembly_code += compiler(statements)
assembly_code = hidden_literal(assembly_code, variable_mem)
print(assembly_code.expandtabs(4)) # 指定制表符扩展的宽度
machine_code = assembler(assembly_code)
print(machine_code.expandtabs(4)) # 指定制表符扩展的宽度

with open('Test/code.s', 'w') as file:
    # 将汇编码写入文件
    file.write(assembly_code)

with open('Test/code.bin', 'w') as file:
    # 将汇编码写入文件
    file.write(machine_code)
