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
        return ('comment', abandon), i
    elif tokens[i] == '/' and tokens[i + 1] == '/':
        abandon, i = parse_expression(tokens, i)  # 跳过语句
        return ('comment', abandon), i
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
                arguments.append(tokens[i])
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
        return ('assign', variable, value), i + 1  # 跳过分号

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
        if statement[0] == 'assign':
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
reg = set(f'a{i}' for i in range(1, 8))  # r1到r7被视为临时寄存器 r0为saved_reg， r6为sp， r7为ra
variable_mem = {}
variable_list = []

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

def allocate_memory(func_name, parameter, variable):
    variable_mem = {}
    if func_name:
        variable = [item for item in variable if item not in parameter]
        # 基础长度
        function_base_mem_lenth = 16
        # 计算 parameters 长度增加的部分
        parameter_mem_lenth = ((len(parameter) - 1) // 4 + 1) * 16
        # 计算 variable 长度增加的部分
        variable_mem_lenth = ((len(variable) - 1) // 4 + 1) * 16
        # 总长度
        function_mem_lenth = function_base_mem_lenth + parameter_mem_lenth + variable_mem_lenth

        offset = -1 * function_mem_lenth + 12
        for var in parameter:
            variable_mem[var] = f"{offset}(s0)"
            offset -= 4
        offset = -20
        for var in variable:
            variable_mem[var] = f"{offset}(s0)"
            offset -= 4
        return variable_mem, function_mem_lenth
    else:
        offset = -20
        for var in variable:
            variable_mem[var] = f"{offset}(s0)"
            offset -= 4
        return variable_mem, 0
    # TODO: s0

def hidden_var(code, variable_mem):
    pattern = re.compile(r'\b(?:' + '|'.join(map(re.escape, variable_mem.keys())) + r')\b')
    try:
        hidden_var = pattern.sub(lambda match: variable_mem[match.group(0)], code)
    except:
        hidden_var = code
    return hidden_var

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

def hide_label(code, label_dict):
    for key, value in label_dict.items():
        code = code.replace(key, f"L{value}")
    return code

def generate_jump(code, label):
    jump_code = ""
    lines = code.split('\n')
    last_line = lines[-2]
    
    try:
        last_label = re.search(r'\.(.*):', last_line).group(1)
        lines = [line for line in lines if line.strip() != last_line and line.strip()]

        # 使用正则表达式匹配
        pattern = r'\..*' + re.escape(last_label) + '$'
        replace_label = re.findall(pattern, code, re.MULTILINE)

        lines = [line for line in lines if line.strip() != last_line and line.strip()]
        
        for line in lines:
            replaced_line = line.replace(replace_label[0], label)
            jump_code += f"{replaced_line}\n"

        jump_code += f"    j       {label}\n"
    except:
        jump_code = code
        jump_code += f"    j       {label}\n"
        
    return jump_code

def generate_expression(expression, left_reg, right_reg, variable_list):
    expression_code = ""
    op = ""
    # 检查值是否为整数或浮点数
    if expression.isdigit():
        expression_code = f"\tli\t\t{left_reg}, {expression}\n"
    else:
        expression_token = lexer(expression)
        if(len(expression_token) == 1):
            var = expression_token[0]
            if var not in variable_list and not var.isdigit():
                variable_list.append(var)
                expression_code += f"\tli\t\t{left_reg}, 0\n"
                expression_code += f"\tsw\t\t{left_reg}, {var}\n"
            expression_code += f"\tlw\t\t{left_reg}, {var}\n"

        elif(len(expression_token) == 3):
            # 如果是二元运算,递归处理左右操作数
            op = expression_token[1]
            left_operand, right_operand = expression_token[0], expression_token[2]
            # 将expression中的变量添加到variable_list中,设置为0
            for var in {left_operand, right_operand}:
                if var not in variable_list and not var.isdigit():
                    variable_list.append(var)
                    expression_code += f"\tli\t\t{left_reg}, 0\n"
                    expression_code += f"\tsw\t\t{left_reg}, {var}\n"

            if not left_operand.isdigit():
                expression_code += f"\tlw\t\t{left_reg}, {left_operand}\n"
                if not right_operand.isdigit():
                    expression_code += f"\tlw\t\t{right_reg}, {right_operand}\n"
                    if op in ('+', '-'):
                        expression_code += operate(op, left_reg, right_reg, 0)
                else:
                    if op in ('+', '-'):
                        expression_code += operate(op, left_reg, right_operand, 1)
                    elif op == '<':
                        expression_code += f"\tli\t\t{right_reg}, {right_operand}\n"
                    elif op == '>':
                        expression_code += f"\tli\t\t{right_reg}, {right_operand}\n"
            else:
                expression_code += f"\tli\t\t{left_reg}, {left_operand}\n"
                if not right_operand.isdigit():
                    expression_code += f"\tlw\t\t{right_reg}, {right_operand}\n"
                    if op in ('+', '-'):
                        expression_code += operate(op, left_reg, right_reg, 0)
                else:
                    if op in ('+', '-'):
                        expression_code += operate(op, left_reg, right_operand, 1)
                    elif op == '<':
                        expression_code += f"\tli\t\t{right_reg}, {right_operand}\n"
                    elif op == '>':
                        expression_code += f"\tli\t\t{right_reg}, {right_operand}\n"
    return expression_code, op

def generate_function(func_name, function_mem_lenth, parameter, code):
    function_code = ""
    # print(function_mem_lenth)

    if func_name:
        if func_name == 'main':
            function_code += f"main:\n"
            # function_code += f".text\n.globl main\nmain:\n"
            # function_code += f"\taddi\tsp, sp, -{function_mem_lenth}\n" # 分配栈空间，用于存储局部变量和临时数据。
            # function_code += f"\tsw\t\tra, {function_mem_lenth-4}(sp)\n" # 保存返回地址到栈空间。
            # function_code += f"\tsw\t\ts0, {function_mem_lenth-8}(sp)\n" # 保存调用者保存的寄存器到栈空间。
            # function_code += f"\taddi\ts0, sp, {function_mem_lenth}\n" # 将s0指向栈的顶部。

            function_code += code

            # function_code += f"\tli\t\ta1, 0\n" # 寄存器归零
            # function_code += f"\tlw\t\tra, {function_mem_lenth-4}(sp)\n" # 从栈上加载保存的返回地址到寄存器ra。
            # function_code += f"\tlw\t\ts0, {function_mem_lenth-8}(sp)\n" # 从栈上加载保存的调用者保存的寄存器s0的值到寄存器s0。
            # function_code += f"\taddi\tsp, sp, {function_mem_lenth}\n" # 释放栈空间。
            # function_code += f"\tjr\t\tra\n" # 跳转到保存的返回地址，即返回到调用该函数的地方。
        else:
            function_code += f"add:\n"
            function_code += f"\taddi\tsp, sp, -{function_mem_lenth}\n" # 分配栈空间，用于存储局部变量和临时数据。
            function_code += f"\tsw\t\tra, {function_mem_lenth-4}(sp)\n" # 保存返回地址到栈空间。
            function_code += f"\tsw\t\ts0, {function_mem_lenth-8}(sp)\n" # 保存调用者保存的寄存器到栈空间。
            function_code += f"\taddi\ts0, sp, {function_mem_lenth}\n" # 将s0指向栈的顶部。
            para_cnt = 0
            for para in parameter:
                function_code += f"\tsw\t\ta{para_cnt+1}, {para}\n"
                para_cnt += 1

            function_code += code

            # function_code += f"\tnop\n" # 空指令，不执行任何操作。==> 调整指令流水线（Pipeline）以防止流水线中的冲突
            function_code += f"\tlw\t\tra, {function_mem_lenth-4}(sp)\n" # 从栈上加载保存的返回地址到寄存器ra。
            function_code += f"\tlw\t\ts0, {function_mem_lenth-8}(sp)\n" # 从栈上加载保存的调用者保存的寄存器s0的值到寄存器s0。
            function_code += f"\taddi\tsp, sp, {function_mem_lenth}\n" # 释放栈空间。
            function_code += f"\tjr\t\tra\n" # 跳转到保存的返回地址，即返回到调用该函数的地方。
    else:
        function_code = code

    return function_code

if_cnt = 1 # 计数if
for_cnt = 1 # 计数for
while_cnt = 1 # 计数while
label_cnt = 2 # 计数循环标签
label_dict = {}

def compiler(func_name, statements, variable_list):
    global label_cnt, if_cnt, while_cnt, for_cnt, label_dict
    code = ""
    func_code = ""
    parameter_list = list(variable_list)

    for statement in statements:
        if statement[0] == 'assign':
            variable, expression = statement[1], statement[2]
            if variable not in variable_list: # 如果变量在变量列表中不存在,则初始化为0
                variable_list.append(variable)
            temp_reg1, temp_reg2 = get_reg(2)
            expression_code,op = generate_expression(expression, temp_reg1, temp_reg2, variable_list)
            func_code += expression_code
            func_code += f"\tsw\t\t{temp_reg1}, {variable}\n"
            release_reg(temp_reg1, temp_reg2)
        elif statement[0] == 'print':
            pass
            # TODO: print函数
        elif statement[0] == 'if':
            condition, if_body, else_body = statement[1], statement[2], statement[3]
            # 生成条件评估的代码
            temp_reg1, temp_reg2 = get_reg(2)
            expression_code, op = generate_expression(condition, temp_reg1, temp_reg2, variable_list) 
            func_code += expression_code
            if op == '<':
                func_code += f"\tble\t\t{temp_reg2}, {temp_reg1}, .else{if_cnt}\n"
            elif op == '>':
                func_code += f"\tble\t\t{temp_reg1}, {temp_reg2}, .else{if_cnt}\n"
            label_dict[f"else{if_cnt}"] = label_cnt # 记录label
            label_cnt += 1
            release_reg(temp_reg1, temp_reg2)
            # 生成if体的代码
            func_code += compiler("", parser(lexer(if_body)), variable_list)
            if(else_body):
                func_code = generate_jump(func_code, f".if{if_cnt}")
                label_dict[f"if{if_cnt}"] = label_cnt # 记录label
                label_cnt += 1
            # 开始else语句的唯一标签
            func_code += f".else{if_cnt}:\n"
            # 生成else体的代码
            func_code += compiler("", parser(lexer(else_body)), variable_list)
            if(else_body):
                func_code += f".if{if_cnt}:\n"
            if_cnt += 1
        elif statement[0] == 'while':
            condition, body = statement[1], statement[2]
            # 跳到循环体的结束标签
            func_code = generate_jump(func_code, f".while{while_cnt}")
            label_dict[f"while{while_cnt}"] = label_cnt # 记录label
            label_cnt += 1
            # 循环体的唯一标签
            func_code += f".whilebody{while_cnt}:\n"
            # 生成循环体的代码
            func_code += compiler("", parser(lexer(body)), variable_list)
            # 开始while循环的唯一标签
            func_code += f".while{while_cnt}:\n"
            # 生成条件评估的代码
            temp_reg1, temp_reg2 = get_reg(2)
            expression_code, op = generate_expression(condition, temp_reg1, temp_reg2, variable_list) 
            func_code += expression_code
            if op == '>':
                func_code += f"\tble\t\t{temp_reg2}, {temp_reg1}, .whilebody{while_cnt}\n"
            elif op == '<':
                func_code += f"\tble\t\t{temp_reg1}, {temp_reg2}, .whilebody{while_cnt}\n"
            label_dict[f"whilebody{while_cnt}"] = label_cnt # 记录label
            label_cnt += 1
            release_reg(temp_reg1, temp_reg2)
            while_cnt += 1
        elif statement[0] == 'for':
            initialization, condition, update, body = statement[1], statement[2], statement[3], statement[4]
            # 生成初始化的代码
            func_code += compiler("", parser(lexer(initialization)), variable_list)
            # 跳到循环体的结束标签
            func_code = generate_jump(func_code, f".for{for_cnt}")
            label_dict[f"for{for_cnt}"] = label_cnt # 记录label
            label_cnt += 1
            # 循环体的唯一标签
            func_code += f".forbody{for_cnt}:\n"
            # 生成循环体的代码
            func_code += compiler("", parser(lexer(body)), variable_list)
            # 生成更新的代码
            func_code += compiler("", parser(lexer(update)), variable_list)
            # 开始for循环的唯一标签
            func_code += f".for{for_cnt}:\n"
            # 生成条件评估的代码
            temp_reg1, temp_reg2 = get_reg(2)
            expression_code, op = generate_expression(condition, temp_reg1, temp_reg2, variable_list)
            func_code += expression_code
            if op == '>':
                func_code += f"\tble\t\t{temp_reg2}, {temp_reg1}, .forbody{for_cnt}\n"
            elif op == '<':
                func_code += f"\tble\t\t{temp_reg1}, {temp_reg2}, .forbody{for_cnt}\n"
            label_dict[f"forbody{for_cnt}"] = label_cnt # 记录label
            label_cnt += 1
            release_reg(temp_reg1, temp_reg2)
            for_cnt += 1
        elif statement[0] == 'function':
            function_name, parameters, body = statement[1], statement[2], statement[3]
            functions[function_name] = {'parameters': list(parameters), 'body': body}
            # 生成函数体的代码
            code += compiler(function_name, parser(lexer(body)), parameters)
        elif statement[0] == 'return':
            pass
        elif statement[0] == 'function_call':
            function_name, arguments = statement[1], statement[2]
            temp_reg1, temp_reg2 = get_reg(2)
            expression_code, op = generate_expression(arguments[0], temp_reg1, '', variable_list)
            func_code += expression_code
            expression_code, op = generate_expression(arguments[1], temp_reg2, '', variable_list)
            func_code += expression_code
            func_code += f"\tcall\t{function_name}"
            
    variable_mem, function_mem_lenth = allocate_memory(func_name, parameter_list, variable_list)
    code += generate_function(func_name, function_mem_lenth, parameter_list, func_code)
    code = hidden_var(code, variable_mem)

    return code # TODO: 变量作用域


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

# r0为saved_reg r1到r5被视为函数寄存器 r6为sp r7为ra
reg_dict = {
    's0' : 0,
    'a1' : 1,
    'a2' : 2,
    'a3' : 3,
    'a4' : 4,
    'a5' : 5,
    'sp' : 6,
    'ra' : 7
}

def assembler(instruction):
    global opcode_dict
    machine_code = ""
    machine_code_list = []
    machine_code_tuple = ()
    labels = {}
    address = 0

    # 遍历指令，提取标签和地址
    for line in instruction.strip().split('\n'):
        line = line.strip()
        if line:
            if line.endswith(':'):
                labels[line[:-1]] = address
            else:
                address += 1

    address = 0
    for line in instruction.strip().split('\n'):
        line = line.strip()
        if line:
            components = line.replace(',', '').split()

            # 排除标签行不进行操作码处理
            if not line.endswith(':'):
                rd = '000'
                rs = '000'
                imm = '00000'
                Imm = '00000000'

                opcode = components[0]
                if opcode in {'add', 'sub', 'and', 'or', 'xor', 'sll', 'srl'}:
                    rd = components[1]
                    rs = components[3]
                    machine_code_tuple = (address, opcode, rd, rs, 0)
                    rd = bin(reg_dict.get(rd))[2:].zfill(3)
                    rs = bin(reg_dict.get(rs))[2:].zfill(3)
                    opcode = opcode_dict.get(opcode)
                    machine_code += imm + rs + rd + opcode + '\n'
                elif opcode in {'addi', 'subi', 'andi', 'ori', 'xori', 'slli', 'srli'}:
                    rd = components[1]
                    rs = rd
                    imm = -1 * int(components[3])//4
                    machine_code_tuple = (address, opcode, rd, rs, imm)
                    rd = bin(reg_dict.get(rd))[2:].zfill(3)
                    rs = rd
                    imm = bin(imm)[2:].zfill(5)
                    opcode = opcode_dict.get(opcode)
                    machine_code += imm + rs + rd + opcode + '\n'
                elif opcode in {'lw', 'sw'}:
                    rd = components[1]
                    imm, rs = components[2][:-1].split('(')
                    imm = -1 * int(imm)//4
                    machine_code_tuple = (address, opcode, rd, rs, imm)
                    rd = bin(reg_dict.get(rd))[2:].zfill(3)
                    rs = bin(reg_dict.get(rs))[2:].zfill(3)
                    imm = bin(imm)[2:].zfill(5)
                    opcode = opcode_dict.get(opcode)
                    machine_code += imm + rs + rd + opcode + '\n'
                elif opcode in {'ble', 'beq'}:
                    rd = components[1]
                    rs = components[2]
                    imm = labels[components[3]]
                    machine_code_tuple = (address, opcode, rd, rs, imm)
                    rd = bin(reg_dict.get(rd))[2:].zfill(3)
                    rs = bin(reg_dict.get(rs))[2:].zfill(3)
                    imm = bin(imm)[2:].zfill(5)
                    opcode = opcode_dict.get(opcode)
                    machine_code += imm + rs + rd + opcode + '\n'
                elif opcode == 'li':
                    rd = components[1]
                    Imm = int(components[2])
                    machine_code_tuple = (address, opcode, rd, Imm)
                    rd = bin(reg_dict.get(rd))[2:].zfill(3)
                    Imm = bin(Imm)[2:].zfill(8)
                    opcode = opcode_dict.get(opcode)
                    machine_code += Imm + rd + opcode + '\n'
                elif opcode == 'j':
                    Imm = labels[components[1]]
                    machine_code_tuple = (address, opcode, rd, Imm)
                    Imm = bin(Imm)[2:].zfill(8)
                    opcode = opcode_dict.get(opcode)
                    machine_code += Imm + '000' + opcode + '\n'
                    # TODO: 现在cpu不支持j
            
                if machine_code_tuple:
                    address += 1
                    machine_code_list.append(machine_code_tuple)

    # 重新从头处理指令，生成机器码
    print(machine_code_list)
    return machine_code

    # TODO: 现在cpu不支持('sw', 'rd', 'rs', -7)：sw默认为'rs'与imm相加
    #       现在cpu不支持'addi rd, rs, imm'：现在addi只能将rd指向的值与imm相加，并将结果放入rd指向的寄存器中

# 从文件读取程序
def read_program_from_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()
    
program_file_path = 'F:\Project\Python\Project\Compiler\code.txt'
program = read_program_from_file(program_file_path)

# program = """
#     X = 10;
#     Y = 15;
#     if(X > Y)
#     {
#         X = X - Y;
#     }
#     else
#     {
#         Y = Y - X;
#     }
# """

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
#         # print X;
#     }
# """

# program = """
#     Y = 15;
#     for(i = 0; i < 3; i = i + 1)
#     {
#         Y = Y + 2;
#     }
# """

# program = """
#     X = 14;
#     Y = 15;
#     for(i = 0; i < 3; i = i + 1)
#     {
#         if(X < Y)
#         {
#             X = X + 1;
#         }
#         else
#         {
#             Y = Y + 2;
#         }
#     }
# """

program = """
    def add(X, Y)
    {
        Z = X + Y;
        print Z;
    }
    a = 1;
    b = 2;
    add(a, b);
"""

tokens = lexer(program)
# print(tokens)
statements = parser(tokens)
# print(statements)
# interpreter(statements, variables)

assembly_code = compiler("main", statements, variable_list)
assembly_code = hide_label(assembly_code, label_dict)
print(assembly_code.expandtabs(4)) # 指定制表符扩展的宽度
machine_code = assembler(assembly_code)
print(machine_code)

# with open('Test/code.s', 'w') as file:
#     # 将汇编码写入文件
#     file.write(assembly_code)

# with open('Test/code.bin', 'w') as file:
#     # 将汇编码写入文件
#     file.write(machine_code)

# TODO: <的反面是>=
# TODO: 有时候会编译错误，少一行
# TODO: 添加链接功能