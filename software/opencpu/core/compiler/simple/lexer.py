"""Positioned tokens for the IDE's small integer language."""
from dataclasses import dataclass
import re


class LanguageError(ValueError):
    """A source syntax error with its position."""


@dataclass(frozen=True, slots=True)
class Token:
    text: str
    line: int
    column: int


class Lexer:
    _pattern = re.compile(
        r'(?P<string>"(?:\\.|[^"\\])*")|'
        r'(?P<comment>\#[^\n]*|//[^\n]*)|'
        r'(?P<space>\s+)|'
        r'(?P<token>0[xX][0-9a-fA-F]+|0[bB][01]+|\d+|'
        r'[A-Za-z_][A-Za-z_0-9]*|==|!=|<=|>=|<<|>>|[-+*/<>=;(){}%,&|^~])'
    )

    def tokenize(self, source: str) -> list[Token]:
        result = []
        position, line, column = 0, 1, 1
        while position < len(source):
            match = self._pattern.match(source, position)
            if match is None:
                raise LanguageError(f"line {line}, column {column}: unexpected character {source[position]!r}")
            text = match.group()
            if match.lastgroup in ("string", "token"):
                result.append(Token(text, line, column))
            if "\n" in text:
                line += text.count("\n")
                column = len(text.rsplit("\n", 1)[-1]) + 1
            else:
                column += len(text)
            position = match.end()
        return result
