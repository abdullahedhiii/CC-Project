import re
from dataclasses import dataclass
from typing import List


@dataclass
class Token:
    type: str
    value: str
    line: int
    column: int


class LexerError(Exception):
    pass


class Lexer:
    KEYWORDS = {
        'int', 'float', 'char', 'bool', 'if', 'else', 'for', 'while', 'do', 'return', 'const', 'true', 'false', 'void'
    }

    token_specification = [
        ('COMMENT',   r'//.*'),
        ('MULTICOMMENT', r'/\*[\s\S]*?\*/'),
        ('CHAR',      r"'(?:\\.|[^\\'])'"),
        ('FLOAT',     r'\d+\.\d+'),
        ('INT',       r'\d+'),
        ('ID',        r'[A-Za-z_][A-Za-z0-9_]*'),
        ('OP',        r'==|!=|<=|>=|\|\||&&|\+\+|--|\+=|-=|\*=|/=|%='),
        ('SYMBOL',    r'[+\-*/%<>=!&|.,;:(){}\[\]]'),
        ('SKIP',      r'[ \t]+'),
        ('NEWLINE',   r'\n'),
    ]

    def __init__(self, code: str):
        self.code = code
        parts = [f'(?P<{name}>{pattern})' for name, pattern in self.token_specification]
        self.regex = re.compile('|'.join(parts))

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []
        line_num = 1
        line_start = 0
        for mo in self.regex.finditer(self.code):
            kind = mo.lastgroup
            value = mo.group()
            column = mo.start() - line_start + 1
            if kind == 'NEWLINE':
                line_num += 1
                line_start = mo.end()
                continue
            if kind == 'SKIP' or kind == 'COMMENT' or kind == 'MULTICOMMENT':
                continue
            if kind == 'ID' and value in self.KEYWORDS:
                kind = value
            tokens.append(Token(kind, value, line_num, column))
        tokens.append(Token('EOF', '', line_num, 1))
        return tokens
