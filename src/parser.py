from typing import List, Optional
from src.lexer import Lexer, Token
from src import ast as _ast


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, code: str):
        self.lexer = Lexer(code)
        self.tokens: List[Token] = self.lexer.tokenize()
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def next(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, typ: str, value: Optional[str] = None) -> Token:
        tok = self.peek()
        if tok.type != typ and (value is None or tok.value != value):
            raise ParseError(f'Expected {typ} {value or ""} got {tok.type} {tok.value} at {tok.line}:{tok.column}')
        return self.next()

    def parse(self) -> _ast.Program:
        decls = []
        while self.peek().type != 'EOF':
            d = self.parse_declaration()
            # allow declaration to return a list of decls (multiple declarators)
            if isinstance(d, list):
                decls.extend(d)
            else:
                decls.append(d)
        return _ast.Program(decls)

    def parse_declaration(self):
        tok = self.peek()
        # allow optional `const` prefix
        if tok.type == 'const':
            return self.parse_typed_declaration()
        if tok.type in ('int', 'float', 'char', 'bool', 'void') or tok.type.upper() in ('INT','FLOAT','CHAR','BOOL','VOID'):
            return self.parse_typed_declaration()
        raise ParseError(f'Unexpected token {tok.type} at {tok.line}:{tok.column}')

    def parse_typed_declaration(self):
        is_const = False
        tok = self.peek()
        if tok.type == 'const':
            is_const = True
            self.next()
        typ = self.next().value
        # read the identifier (name) first to decide whether function or variables
        name_tok = self.expect('ID')
        name = name_tok.value

        # function or variable: if next is '(', it's a function
        if self.peek().value == '(':
            # function
            self.next()  # (
            params = []
            if self.peek().value != ')':
                while True:
                    ptype = self.next().value
                    pname = self.expect('ID').value
                    params.append((ptype, pname))
                    if self.peek().value == ',':
                        self.next()
                        continue
                    break
            self.expect('SYMBOL', ')')
            body = self.parse_compound()
            return _ast.FuncDecl(typ, name, params, body)
        else:
            # variable declaration(s) — support comma-separated declarators
            decls = []
            decls.append(_ast.VarDecl(typ, name, None, is_const))
            # if the first declarator has initializer, handle it
            if self.peek().value == '=' or (self.peek().type == 'OP' and self.peek().value == '='):
                self.next()
                decls[-1].init = self.parse_expression()
            while self.peek().value == ',':
                self.next()
                # parse next declarator names
                next_name = self.expect('ID').value
                init = None
                if self.peek().value == '=' or (self.peek().type == 'OP' and self.peek().value == '='):
                    self.next()
                    init = self.parse_expression()
                decls.append(_ast.VarDecl(typ, next_name, init, is_const))
            self.expect('SYMBOL',';')
            return decls

    def parse_compound(self):
        # expect '{'
        if self.peek().value != '{':
            raise ParseError('Expected { for compound')
        self.next()
        stmts = []
        while self.peek().value != '}':
            s = self.parse_statement()
            if isinstance(s, list):
                stmts.extend(s)
            else:
                stmts.append(s)
        self.next()
        return _ast.Compound(stmts)

    def parse_statement(self):
        tok = self.peek()
        if tok.type == 'return':
            self.next()
            if self.peek().value == ';':
                self.next()
                return _ast.Return(None)
            expr = self.parse_expression()
            self.expect('SYMBOL',';')
            return _ast.Return(expr)
        if tok.value == '{':
            return self.parse_compound()
        if tok.type == 'if':
            self.next()
            self.expect('SYMBOL','(')
            cond = self.parse_expression()
            self.expect('SYMBOL',')')
            thenb = self.parse_statement()
            elseb = None
            if self.peek().type == 'else':
                self.next()
                elseb = self.parse_statement()
            return _ast.If(cond, thenb, elseb)
        if tok.type == 'while':
            self.next()
            self.expect('SYMBOL','(')
            cond = self.parse_expression()
            self.expect('SYMBOL',')')
            body = self.parse_statement()
            return _ast.While(cond, body)
        if tok.type == 'for':
            self.next()
            self.expect('SYMBOL','(')
            # init: could be declaration, expression, or empty
            if self.peek().value == ';':
                init = None
                self.next()
            else:
                if self.peek().type in ('int','float','char','bool','const'):
                    init = self.parse_declaration()
                else:
                    init = self.parse_expression()
                    self.expect('SYMBOL',';')
            # cond
            if self.peek().value == ';':
                cond = None
                self.next()
            else:
                cond = self.parse_expression()
                self.expect('SYMBOL',';')
            # post
            if self.peek().value == ')':
                post = None
            else:
                post = self.parse_expression()
            self.expect('SYMBOL',')')
            body = self.parse_statement()
            return _ast.For(init, cond, post, body)
        if tok.type == 'do':
            self.next()
            body = self.parse_statement()
            if self.peek().type != 'while':
                raise ParseError('Expected while after do-block')
            self.next()
            self.expect('SYMBOL','(')
            cond = self.parse_expression()
            self.expect('SYMBOL',')')
            self.expect('SYMBOL',';')
            return _ast.While(cond, body)
        # for, do etc omitted for brevity; can extend similarly
        # expression or declaration
        if tok.type in ('int','float','char','bool','const'):
            # local var decl
            return self.parse_typed_declaration()
        # expression statement
        expr = self.parse_expression()
        self.expect('SYMBOL',';')
        return _ast.ExprStmt(expr)

    # Expression parser (precedence climbing)
    PRECEDENCE = {
        '||': 1,
        '&&': 2,
        '==': 3, '!=': 3,
        '<': 4, '>': 4, '<=': 4, '>=': 4,
        '+': 5, '-': 5,
        '*': 6, '/': 6, '%': 6,
        '=': 0,
        '+=': 0, '-=': 0, '*=': 0, '/=': 0, '%=': 0,
    }

    def parse_expression(self, min_prec=0):
        tok = self.peek()
        # handle unary prefix operators: !, +, -, ++, --
        if tok.value in ('!','+','-','++','--'):
            op = tok.value
            self.next()
            # unary has higher precedence than multiplicative
            expr = self.parse_expression(7)
            return _ast.UnaryOp(op if op not in ('++','--') else f'pre{op}', expr)

        # primary
        if tok.type == 'INT':
            self.next()
            left = _ast.Literal(int(tok.value), 'int')
        elif tok.type == 'FLOAT':
            self.next()
            left = _ast.Literal(float(tok.value), 'float')
        elif tok.type == 'CHAR':
            self.next()
            val = tok.value[1:-1]
            left = _ast.Literal(val, 'char')
        elif tok.type in ('true','false'):
            self.next()
            left = _ast.Literal(True if tok.type == 'true' else False, 'bool')
        elif tok.type == 'ID':
            idtok = self.next()
            if self.peek().value == '(':
                # function call
                self.next()
                args = []
                if self.peek().value != ')':
                    while True:
                        args.append(self.parse_expression())
                        if self.peek().value == ',':
                            self.next()
                            continue
                        break
                self.expect('SYMBOL',')')
                left = _ast.FuncCall(idtok.value, args)
            else:
                left = _ast.VarRef(idtok.value)
        elif tok.value == '(':
            self.next()
            left = self.parse_expression()
            self.expect('SYMBOL',')')
        else:
            raise ParseError(f'Unexpected expression token {tok.type} {tok.value} at {tok.line}:{tok.column}')

        # handle postfix ++/-- (higher precedence than binary ops)
        while self.peek().value in ('++','--'):
            op = self.next().value
            left = _ast.UnaryOp(f'post{op}', left)

        while True:
            op_tok = self.peek()
            op = op_tok.value
            if op_tok.type in ('OP','SYMBOL') and op in self.PRECEDENCE and self.PRECEDENCE[op] >= min_prec:
                prec = self.PRECEDENCE[op]
                self.next()
                # right-assoc for assignment and compound assignment
                if op in ('=', '+=', '-=', '*=', '/=', '%='):
                    next_min = prec
                else:
                    next_min = prec + 1
                right = self.parse_expression(next_min)
                left = _ast.BinaryOp(op, left, right)
                continue
            break
        return left
