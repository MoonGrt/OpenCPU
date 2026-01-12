import re

# 词法分析器
class lexer:
    def __init__(self):
        self.pattern = r'\b(?:print|if|else|for|while|return|def)\b|\d+|\w+|"[^"]*"|[-+*/<>=;(){}#,]'
        
    def lexe(self, program):
        tokens = [match.group(0) for match in re.finditer(self.pattern, program)]
        return tokens

# 测试
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
    print("Tokens:", tokens)
