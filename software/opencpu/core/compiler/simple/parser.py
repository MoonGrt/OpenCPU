"""Parse source once into structured statements and Python expression ASTs."""
import ast
from dataclasses import dataclass
import keyword

from .lexer import LanguageError, Lexer, Token


@dataclass(frozen=True, slots=True)
class Assign:
    name: str
    value: ast.expr


@dataclass(frozen=True, slots=True)
class Call:
    value: ast.Call


@dataclass(frozen=True, slots=True)
class Return:
    value: ast.expr


@dataclass(frozen=True, slots=True)
class Print:
    value: ast.expr


@dataclass(frozen=True, slots=True)
class If:
    condition: ast.expr
    body: list
    otherwise: list


@dataclass(frozen=True, slots=True)
class While:
    condition: ast.expr
    body: list


@dataclass(frozen=True, slots=True)
class For:
    initial: Assign | Call | None
    condition: ast.expr
    update: Assign | Call | None
    body: list


@dataclass(frozen=True, slots=True)
class Function:
    name: str
    parameters: tuple[str, ...]
    body: list


class Parser:
    _reserved = frozenset(("def", "if", "else", "while", "for", "return", "print"))

    def __init__(self):
        self._tokens: list[Token] = []
        self._position = 0

    def _peek(self) -> str | None:
        return self._tokens[self._position].text if self._position < len(self._tokens) else None

    def _error(self, message: str) -> LanguageError:
        if self._position < len(self._tokens):
            token = self._tokens[self._position]
            return LanguageError(f"line {token.line}, column {token.column}: {message}")
        return LanguageError("end of source: " + message)

    def _take(self, expected: str | None = None) -> Token:
        value = self._peek()
        if value is None or (expected is not None and value != expected):
            raise self._error(f"expected {expected or 'token'}, got {value!r}")
        token = self._tokens[self._position]
        self._position += 1
        return token

    def _identifier(self) -> str:
        token = self._take()
        if (not token.text.isidentifier() or token.text in self._reserved
                or keyword.iskeyword(token.text)):
            raise LanguageError(f"line {token.line}, column {token.column}: expected an identifier")
        return token.text

    def _until(self, delimiter: str) -> list[Token]:
        result = []
        depth = 0
        while self._peek() is not None:
            token = self._peek()
            if token == delimiter and depth == 0:
                self._take(delimiter)
                return result
            item = self._take()
            if item.text == "(":
                depth += 1
            elif item.text == ")":
                depth -= 1
                if depth < 0:
                    raise self._error(f"missing {delimiter!r}")
            result.append(item)
        raise self._error(f"missing {delimiter!r}")

    @staticmethod
    def _expression(tokens: list[Token], default: int | None = None) -> ast.expr:
        if not tokens and default is not None:
            return ast.Constant(default)
        # Spaces preserve token boundaries: '1 2' must never silently become 12.
        text = " ".join(token.text for token in tokens)
        try:
            node = ast.parse(text, mode="eval").body
        except SyntaxError as error:
            line = tokens[0].line if tokens else 1
            raise LanguageError(f"line {line}: invalid expression {text!r}") from error
        if tokens:
            ast.increment_lineno(node, tokens[0].line - 1)
        return node

    def _block(self) -> list:
        self._take("{")
        result = []
        while self._peek() != "}":
            if self._peek() is None:
                raise self._error("missing '}'")
            if self._peek() == ";":
                self._take(";")
            else:
                result.append(self._statement())
        self._take("}")
        return result

    def _simple(self, delimiter: str = ";") -> Assign | Call:
        name = self._identifier()
        if self._peek() == "=":
            self._take("=")
            return Assign(name, self._expression(self._until(delimiter)))
        if self._peek() == "(":
            first = self._tokens[self._position - 1]
            expression = self._expression([first, *self._until(delimiter)])
            if isinstance(expression, ast.Call):
                return Call(expression)
        raise self._error("expected assignment or function call")

    def _statement(self):
        kind = self._peek()
        if kind == "def":
            self._take("def")
            name = self._identifier()
            self._take("(")
            parameters = []
            if self._peek() != ")":
                while True:
                    parameters.append(self._identifier())
                    if self._peek() != ",":
                        break
                    self._take(",")
            self._take(")")
            if len(parameters) > 4 or len(set(parameters)) != len(parameters):
                raise self._error("functions require unique parameters (at most four)")
            return Function(name, tuple(parameters), self._block())
        if kind in ("if", "while"):
            self._take(kind)
            self._take("(")
            condition = self._expression(self._until(")"))
            body = self._block()
            if kind == "while":
                return While(condition, body)
            otherwise = []
            if self._peek() == "else":
                self._take("else")
                otherwise = self._block()
            return If(condition, body, otherwise)
        if kind == "for":
            self._take("for")
            self._take("(")
            if self._peek() == ";":
                self._take(";")
                initial = None
            else:
                initial = self._simple(";")
            condition = self._expression(self._until(";"), default=1)
            if self._peek() == ")":
                self._take(")")
                update = None
            else:
                update = self._simple(")")
            return For(initial, condition, update, self._block())
        if kind in ("return", "print"):
            self._take(kind)
            value = self._expression(self._until(";"), default=0 if kind == "return" else None)
            return Return(value) if kind == "return" else Print(value)
        return self._simple()

    def parse(self, source: str) -> list:
        self._tokens = Lexer().tokenize(source)
        self._position = 0
        statements = []
        while self._peek() is not None:
            if self._peek() == ";":
                self._take(";")
            else:
                statements.append(self._statement())
        return statements
