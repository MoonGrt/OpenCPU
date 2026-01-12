import re
from Lexer import lexer
from Parser import parser

class compiler:
    def __init__(self):
        self.reg = set(f'a{i}' for i in range(1, 8)) # r1到r7被视为临时寄存器 r0为saved_reg， r6为sp， r7为ra
        self.variable_mem = {}
        self.variable_list = []
        self.label_cnt = 2
        self.label_dict = {}
        self.if_cnt = 1
        self.for_cnt = 1
        self.while_cnt = 1
        self.functions = {}

    def get_reg(self, num_regs=1):
        if len(self.reg) >= num_regs:
            allocated_regs = sorted(self.reg)[:num_regs]
            self.reg.difference_update(allocated_regs)
            return tuple(allocated_regs)
        else:
            raise Exception("寄存器用尽")

    def release_reg(self, *released_regs):
        self.reg.update(released_regs)

    def allocate_memory(self, func_name, parameter, variable):
        variable_mem = {}
        if func_name:
            variable = [item for item in variable if item not in parameter]
            # 基础长度
            function_base_mem_lenth = 16
            # 计算 parameters 长度增加的部分
            parameter_mem_length = ((len(parameter) - 1) // 4 + 1) * 16
            # 计算 variable 长度增加的部分
            variable_mem_length = ((len(variable) - 1) // 4 + 1) * 16
            # 总长度
            function_mem_length = function_base_mem_lenth + parameter_mem_length + variable_mem_length

            offset = -1 * function_mem_length + 12
            for var in parameter:
                variable_mem[var] = f"{offset}(s0)"
                offset -= 4
            offset = -20
            for var in variable:
                variable_mem[var] = f"{offset}(s0)"
                offset -= 4
            return variable_mem, function_mem_length
        else:
            offset = -20
            for var in variable:
                variable_mem[var] = f"{offset}(s0)"
                offset -= 4
            return variable_mem, 0

    def hide_var(self, code, label_dict):
        pattern = re.compile(r'\b(?:' + '|'.join(map(re.escape, label_dict.keys())) + r')\b')
        try:
            hidden_var = pattern.sub(lambda match: label_dict[match.group(0)], code)
        except:
            hidden_var = code
        return hidden_var

    def operate(self, op, left, right, imm):
        # 根据运算符生成相应的汇编指令
        code = ''
        if op == '+':
            if imm:
                code = f"\taddi\t{left}, {left}, {right}\n"
            else:
                code = f"\tadd\t\t{left}, {left}, {right}\n"
        elif op == '-':
            if imm:
                code = f"\taddi\t{left}, {left}, {right}\n"
            else:
                code = f"\tsub\t\t{left}, {left}, {right}\n"
        return code

    def hide_label(self, code):
        for key, value in self.label_dict.items():
            code = code.replace(key, f"L{value}")
        return code

    def generate_jump(self, code, label):
        jump_code = ""
        lines = code.split('\n')
        last_line = lines[-2]

        try:
            last_label = re.search(r'\.(.*):', last_line).group(1)
            lines = [line for line in lines if line.strip() != last_line and line.strip()]

            pattern = r'\..*' + re.escape(last_label) + '$'
            replace_label = re.findall(pattern, code, re.MULTILINE)

            lines = [line for line in lines if line.strip() != last_line and line.strip()]

            for line in lines:
                replaced_line = line.replace(replace_label[0], label)
                jump_code += f"{replaced_line}\n"

            jump_code += f"\tj\t\t{label}\n"
        except:
            jump_code = code
            jump_code += f"\tj\t\t{label}\n"

        return jump_code

    def generate_expression(self, expression, left_reg, right_reg, variable_list):
        expression_code = ""
        op = ""
        # 检查值是否为整数或浮点数
        if expression.isdigit():
            expression_code = f"\tli\t\t{left_reg}, {expression}\n"
        else:
            expression_token = lexer().lexe(expression)
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
                            expression_code += self.operate(op, left_reg, right_reg, 0)
                    else:
                        if op in ('+', '-'):
                            expression_code += self.operate(op, left_reg, right_operand, 1)
                        elif op == '<':
                            expression_code += f"\tli\t\t{right_reg}, {right_operand}\n"
                        elif op == '>':
                            expression_code += f"\tli\t\t{right_reg}, {right_operand}\n"
                else:
                    expression_code += f"\tli\t\t{left_reg}, {left_operand}\n"
                    if not right_operand.isdigit():
                        expression_code += f"\tlw\t\t{right_reg}, {right_operand}\n"
                        if op in ('+', '-'):
                            expression_code += self.operate(op, left_reg, right_reg, 0)
                    else:
                        if op in ('+', '-'):
                            expression_code += self.operate(op, left_reg, right_operand, 1)
                        elif op == '<':
                            expression_code += f"\tli\t\t{right_reg}, {right_operand}\n"
                        elif op == '>':
                            expression_code += f"\tli\t\t{right_reg}, {right_operand}\n"
        return expression_code, op

    def generate_function(self, func_name, function_mem_length, parameter, code):
        function_code = ""

        if func_name:
            if func_name == 'main':
                function_code += f"main:\n"
                # function_code += f".text\n.globl main\nmain:\n"
                # function_code += f"\taddi\tsp, sp, -{function_mem_length}\n" # 分配栈空间，用于存储局部变量和临时数据。
                # function_code += f"\tsw\t\tra, {function_mem_length-4}(sp)\n" # 保存返回地址到栈空间。
                # function_code += f"\tsw\t\ts0, {function_mem_length-8}(sp)\n" # 保存调用者保存的寄存器到栈空间。
                # function_code += f"\taddi\ts0, sp, {function_mem_length}\n" # 将s0指向栈的顶部。

                function_code += code

                # function_code += f"\tli\t\ta1, 0\n" # 寄存器归零
                # function_code += f"\tlw\t\tra, {function_mem_length-4}(sp)\n" # 从栈上加载保存的返回地址到寄存器ra。
                # function_code += f"\tlw\t\ts0, {function_mem_length-8}(sp)\n" # 从栈上加载保存的调用者保存的寄存器s0的值到寄存器s0。
                # function_code += f"\taddi\tsp, sp, {function_mem_length}\n" # 释放栈空间。
                # function_code += f"\tjr\t\tra\n" # 跳转到保存的返回地址，即返回到调用该函数的地方。
            else:
                function_code += f"add:\n"
                function_code += f"\taddi\tsp, sp, -{function_mem_length}\n" # 分配栈空间，用于存储局部变量和临时数据。
                function_code += f"\tsw\t\tra, {function_mem_length-4}(sp)\n" # 保存返回地址到栈空间。
                function_code += f"\tsw\t\ts0, {function_mem_length-8}(sp)\n" # 保存调用者保存的寄存器到栈空间。
                function_code += f"\taddi\ts0, sp, {function_mem_length}\n" # 将s0指向栈的顶部。
                para_cnt = 0
                for para in parameter:
                    function_code += f"\tsw\t\ta{para_cnt+1}, {para}\n"
                    para_cnt += 1

                function_code += code

                # function_code += f"\tnop\n" # 空指令，不执行任何操作。==> 调整指令流水线（Pipeline）以防止流水线中的冲突
                function_code += f"\tlw\t\tra, {function_mem_length-4}(sp)\n" # 从栈上加载保存的返回地址到寄存器ra。
                function_code += f"\tlw\t\ts0, {function_mem_length-8}(sp)\n" # 从栈上加载保存的调用者保存的寄存器s0的值到寄存器s0。
                function_code += f"\taddi\tsp, sp, {function_mem_length}\n" # 释放栈空间。
                function_code += f"\tjr\t\tra\n" # 跳转到保存的返回地址，即返回到调用该函数的地方。
        else:
            function_code = code

        return function_code

    def compiler(self, func_name, statements, variable_list):
        code = ""
        func_code = ""
        parameter_list = list(variable_list)

        for statement in statements:
            if statement[0] == 'assign':
                variable, expression = statement[1], statement[2]
                if variable not in variable_list:
                    variable_list.append(variable)
                temp_reg1, temp_reg2 = self.get_reg(2)
                expression_code, op = self.generate_expression(expression, temp_reg1, temp_reg2, variable_list)
                func_code += expression_code
                func_code += f"\tsw\t\t{temp_reg1}, {variable}\n"
                self.release_reg(temp_reg1, temp_reg2)
            elif statement[0] == 'print':
                pass
                # TODO: print函数
            elif statement[0] == 'if':
                condition, if_body, else_body = statement[1], statement[2], statement[3]
                # 生成条件评估的代码
                temp_reg1, temp_reg2 = self.get_reg(2)
                expression_code, op = self.generate_expression(condition, temp_reg1, temp_reg2, variable_list) 
                func_code += expression_code
                if op == '<':
                    func_code += f"\tble\t\t{temp_reg2}, {temp_reg1}, .else{self.if_cnt}\n"
                elif op == '>':
                    func_code += f"\tble\t\t{temp_reg1}, {temp_reg2}, .else{self.if_cnt}\n"
                self.label_dict[f"else{self.if_cnt}"] = self.label_cnt # 记录label
                self.label_cnt += 1
                self.release_reg(temp_reg1, temp_reg2)
                # 生成if体的代码
                func_code += self.compiler("", parser().parse(lexer().lexe(if_body)), variable_list)
                if(else_body):
                    func_code = self.generate_jump(func_code, f".if{self.if_cnt}")
                    self.label_dict[f"if{self.if_cnt}"] = self.label_cnt # 记录label
                    self.label_cnt += 1
                # 开始else语句的唯一标签
                func_code += f".else{self.if_cnt}:\n"
                # 生成else体的代码
                func_code += self.compiler("", parser().parse(lexer().lexe(else_body)), variable_list)
                if(else_body):
                    func_code += f".if{self.if_cnt}:\n"
                self.if_cnt += 1
            elif statement[0] == 'while':
                condition, body = statement[1], statement[2]
                # 跳到循环体的结束标签
                func_code = self.generate_jump(func_code, f".while{self.while_cnt}")
                self.label_dict[f"while{self.while_cnt}"] = self.label_cnt # 记录label
                self.label_cnt += 1
                # 循环体的唯一标签
                func_code += f".whilebody{self.while_cnt}:\n"
                # 生成循环体的代码
                func_code += self.compiler("", parser().parse(lexer().lexe(body)), variable_list)
                # 开始while循环的唯一标签
                func_code += f".while{self.while_cnt}:\n"
                # 生成条件评估的代码
                temp_reg1, temp_reg2 = self.get_reg(2)
                expression_code, op = self.generate_expression(condition, temp_reg1, temp_reg2, variable_list) 
                func_code += expression_code
                if op == '>':
                    func_code += f"\tble\t\t{temp_reg2}, {temp_reg1}, .whilebody{self.while_cnt}\n"
                elif op == '<':
                    func_code += f"\tble\t\t{temp_reg1}, {temp_reg2}, .whilebody{self.while_cnt}\n"
                self.label_dict[f"whilebody{self.while_cnt}"] = self.label_cnt # 记录label
                self.label_cnt += 1
                self.release_reg(temp_reg1, temp_reg2)
                self.while_cnt += 1
            elif statement[0] == 'for':
                initialization, condition, update, body = statement[1], statement[2], statement[3], statement[4]
                # 生成初始化的代码
                func_code += self.compiler("", parser().parse(lexer().lexe(initialization)), variable_list)
                # 跳到循环体的结束标签
                func_code = self.generate_jump(func_code, f".for{self.for_cnt}")
                self.label_dict[f"for{self.for_cnt}"] = self.label_cnt # 记录label
                self.label_cnt += 1
                # 循环体的唯一标签
                func_code += f".forbody{self.for_cnt}:\n"
                # 生成循环体的代码
                func_code += self.compiler("", parser().parse(lexer().lexe(body)), variable_list)
                # 生成更新的代码
                func_code += self.compiler("", parser().parse(lexer().lexe(update)), variable_list)
                # 开始for循环的唯一标签
                func_code += f".for{self.for_cnt}:\n"
                # 生成条件评估的代码
                temp_reg1, temp_reg2 = self.get_reg(2)
                expression_code, op = self.generate_expression(condition, temp_reg1, temp_reg2, variable_list)
                func_code += expression_code
                if op == '>':
                    func_code += f"\tble\t\t{temp_reg2}, {temp_reg1}, .forbody{self.for_cnt}\n"
                elif op == '<':
                    func_code += f"\tble\t\t{temp_reg1}, {temp_reg2}, .forbody{self.for_cnt}\n"
                self.label_dict[f"forbody{self.for_cnt}"] = self.label_cnt # 记录label
                self.label_cnt += 1
                self.release_reg(temp_reg1, temp_reg2)
                self.for_cnt += 1
            elif statement[0] == 'function':
                function_name, parameters, body = statement[1], statement[2], statement[3]
                self.functions[function_name] = {'parameters': list(parameters), 'body': body}
                # 生成函数体的代码
                code += self.compiler(function_name, parser().parse(lexer().lexe(body)), parameters)
            elif statement[0] == 'return':
                pass
                # TODO: 函数返回值
            elif statement[0] == 'function_call':
                function_name, arguments = statement[1], statement[2]
                temp_reg1, temp_reg2 = self.get_reg(2)
                expression_code, op = self.generate_expression(arguments[0], temp_reg1, '', variable_list)
                func_code += expression_code
                expression_code, op = self.generate_expression(arguments[1], temp_reg2, '', variable_list)
                func_code += expression_code
                func_code += f"\tcall\t{function_name}\n"
                self.release_reg(temp_reg1, temp_reg2)

        variable_mem, function_mem_length = self.allocate_memory(func_name, parameter_list, variable_list)
        code += self.generate_function(func_name, function_mem_length, parameter_list, func_code)
        code = self.hide_var(code, variable_mem)

        return code

# Example usage:
if __name__ == "__main__":
    program_code = """
    def add(X, Y)
    {
        Z = X + Y;
        print Z;
    }
    a = 1;
    b = 2;
    add(a, b);
    """

    Lexer = lexer()
    tokens = Lexer.lexe(program_code)
    print(tokens)

    Parser = parser()
    statements = Parser.parse(tokens)
    print(statements)

    variable_list = []
    Compiler = compiler()
    assembly_code = Compiler.compiler("main", statements, variable_list)
    assembly_code = Compiler.hide_label(assembly_code)
    print(assembly_code.expandtabs(4))

# TODO: <的反面是>=
# TODO: 有时候会编译错误，少一行
# TODO: 添加链接功能