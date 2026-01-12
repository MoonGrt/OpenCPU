# 语法分析器
class parser:
    def __init__(self):
        self.index = 0
        self.tokens = []
        self.statements = []
        self.function_list = []

    # 解析表达式
    def parse_expression(self):
        expression = ''
        while self.index < len(self.tokens) and self.tokens[self.index] not in (';', ')'):
            expression += self.tokens[self.index]
            self.index += 1
        return expression, self.index + 1  # 跳过 ';'

    # 解析代码块
    def parse_block(self):
        block = ''
        bracket_cnt = 0
        self.index += 1
        if self.tokens[self.index] == '{':
            self.index += 1  # 跳过'{'
        while self.index < len(self.tokens):
            if self.tokens[self.index] == '{':
                bracket_cnt += 1
            elif self.tokens[self.index] == '}':
                if not bracket_cnt:
                    break
                else:
                    bracket_cnt -= 1
            block += self.tokens[self.index] + ' '
            self.index += 1
        return block, self.index + 1  # 跳过'}'

    # 解析函数定义
    def parse_function(self):
        start = self.index
        self.index += 3  # 跳过'def'、函数名和'('
        parameters = []
        while self.tokens[self.index] != ')':
            if self.tokens[self.index] != ',':
                parameters.append(self.tokens[self.index])
            self.index += 1
        self.index += 1  # 跳过')'
        body, _ = self.parse_block()
        return ('function', self.tokens[start + 1], parameters, body.strip()), self.index + 1

    # 解析语句
    def parse_statement(self):
        if self.tokens[self.index] == '#':
            abandon, self.index = self.parse_expression()  # 跳过语句
            return ('comment', abandon), self.index
        elif self.tokens[self.index] == '/' and self.tokens[self.index + 1] == '/':
            abandon, self.index = self.parse_expression()  # 跳过语句
            return ('comment', abandon), self.index
        elif self.tokens[self.index] == 'print':
            self.index += 1
            expression, self.index = self.parse_expression()
            return ('print', expression), self.index
        elif self.tokens[self.index] == 'if':
            self.index += 2  # 跳过'if'、'('
            condition, self.index = self.parse_expression()
            if_body, self.index = self.parse_block()
            else_body, self.index = self.parse_block() if self.index < len(self.tokens) and self.tokens[self.index] == 'else' else ('', self.index)
            return ('if', condition, if_body, else_body), self.index
        elif self.tokens[self.index] == 'while':
            self.index += 2  # 跳过'while'、'('
            condition, self.index = self.parse_expression()
            while_body, self.index = self.parse_block()
            return ('while', condition, while_body), self.index
        elif self.tokens[self.index] == 'for':
            self.index += 2  # 跳过'for'、'('
            init, self.index = self.parse_expression()
            condition, self.index = self.parse_expression()
            update, self.index = self.parse_expression()
            body, self.index = self.parse_block()
            return ('for', init, condition, update, body), self.index
        elif self.tokens[self.index] == 'return':
            pass
            # TODO: 函数返回值
        elif self.tokens[self.index] == 'def':
            return self.parse_function()
        elif self.tokens[self.index] in self.function_list and self.tokens[self.index + 1] == '(':
            function_name = self.tokens[self.index]
            self.index += 2  # 跳过函数名、'('
            arguments = []
            while self.tokens[self.index] != ')':
                if self.tokens[self.index] != ',':
                    arguments.append(self.tokens[self.index])
                self.index += 1
            self.index += 2  # 跳过')'、';'
            return ('function_call', function_name, arguments), self.index
        else:
            # 默认为赋值语句
            variable = self.tokens[self.index]
            self.index += 2  # 跳过变量、等号
            value = ''
            while self.index < len(self.tokens) and self.tokens[self.index] != ';':
                value += self.tokens[self.index]
                self.index += 1
            return ('assign', variable, value), self.index + 1  # 跳过分号
    
    # 解析器
    def parse(self, tokens):
        self.tokens = tokens
        while self.index < len(tokens):
            statement, self.index = self.parse_statement()
            self.statements.append(statement)
            if statement[0] == 'function':
                self.function_list.append(statement[1])
        return self.statements

if __name__ == "__main__":
    tokens = ['def', 'add', '(', 'X', ',', 'Y', ')', '{', 'Z', '=', 'X', '+', 'Y', ';', 'print', 'Z', ';', '}', 'a', '=', '1', ';', 'b', '=', '2', ';', 'add', '(', 'a', ',', 'b', ')', ';']
    Parser = parser()
    statements = Parser.parse(tokens)
    print(statements)
