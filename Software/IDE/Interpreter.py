import re
from Lexer import lexer
from Parser import parser

class Interpreter:
    def __init__(self):
        # 存储变量和函数信息的字典
        self.variables = {}
        self.functions = {}

    def evaluate(self, expression, vars):
        # 识别表达式中的变量，并确保它们在给定的字典中
        expression_variables = set(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', expression))
        for var in expression_variables:
            if var not in vars:
                vars[var] = 0
        # 使用提供的变量评估表达式
        return eval(expression, vars)

    def execute(self, statements):
        for statement in statements:
            if statement[0] == 'assign':
                # 赋值语句：将变量赋值为评估值
                variable, value = statement[1], statement[2]
                self.variables[variable] = self.evaluate(value, self.variables)
            elif statement[0] == 'print':
                # 打印语句：打印评估的表达式
                expression = statement[1]
                print(self.evaluate(expression, self.variables))
            elif statement[0] == 'if':
                # If语句：评估条件并执行适当的代码块
                condition, if_body, else_body = statement[1], statement[2], statement[3]
                if self.evaluate(condition, self.variables):
                    self.execute(parser().parse(lexer().lexe(if_body)))
                else:
                    self.execute(parser().parse(lexer().lexe(else_body)))
            elif statement[0] == 'while':
                # While循环：评估条件并重复执行代码块
                condition, body = statement[1], statement[2]
                while self.evaluate(condition, self.variables):
                    self.execute(parser().parse(lexer().lexe(body)))
            elif statement[0] == 'for':
                # For循环：初始化，评估条件，执行代码块，更新
                initialization, condition, update, body = statement[1], statement[2], statement[3], statement[4]
                self.variables[initialization.split('=')[0]] = self.evaluate(initialization.split('=')[1], self.variables)
                while self.evaluate(condition, self.variables):
                    self.execute(parser().parse(lexer().lexe(body)))
                    self.variables[update.split('=')[0]] = self.evaluate(update.split('=')[1], self.variables)
            elif statement[0] == 'function':
                # 函数定义：存储函数信息
                function_name, parameters, body = statement[1], statement[2], statement[3]
                self.functions[function_name] = {'parameters': parameters, 'body': body}
            elif statement[0] == 'return':
                # 返回语句：返回评估的表达式
                return_value = self.evaluate(statement[1], self.variables)
                return return_value
            elif statement[0] == 'function_call':
                # 函数调用：使用提供的参数执行函数
                function_name, arguments = statement[1], statement[2]
                function = self.functions.get(function_name)
                if function:
                    function_vars = dict(zip(function['parameters'], arguments))
                    self.execute(parser().parse(lexer().lexe(function['body'])), function_vars)

# 测试部分
if __name__ == "__main__":
    program_code = """
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
    Lexer = lexer()
    tokens = Lexer.lexe(program_code)
    print(tokens)

    Parser = parser()
    statements = Parser.parse(tokens)
    print(statements)

    interpreter_instance = Interpreter()
    interpreter_instance.execute(statements)
