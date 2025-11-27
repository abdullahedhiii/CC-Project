from typing import Dict, List
from src import ast as _ast


class SemanticError(Exception):
    pass


class SemanticAnalyzer:
    def __init__(self, program: _ast.Program):
        self.program = program
        self.errors: List[str] = []
        # map name -> (type, is_const)
        self.global_scope: Dict[str, tuple] = {}
        self.functions: Dict[str, _ast.FuncDecl] = {}

    def analyze(self):
        # collect globals and functions
        for decl in self.program.declarations:
            if isinstance(decl, _ast.VarDecl):
                if decl.name in self.global_scope:
                    self.errors.append(f'Redeclaration of global {decl.name}')
                else:
                    self.global_scope[decl.name] = (decl.var_type, decl.is_const)
            elif isinstance(decl, _ast.FuncDecl):
                if decl.name in self.functions:
                    self.errors.append(f'Redeclaration of function {decl.name}')
                else:
                    self.functions[decl.name] = decl
        # analyze functions
        for fname, fdecl in self.functions.items():
            self.check_function(fdecl)

    def check_function(self, f: _ast.FuncDecl):
        # simple local scope: map name -> (type, is_const)
        scope = { name: (typ, False) for typ, name in f.params }

        def infer_type(node):
            if node is None:
                return None
            t = type(node)
            if t is _ast.Literal:
                return node.typ
            if t is _ast.UnaryOp:
                op = node.op
                if op in ('!') or op == 'pre!' or op == 'post!':
                    return 'bool'
                if op in ('pre++','pre--','post++','post--'):
                    # result type is the operand type if numeric
                    return infer_type(node.expr)
                if op in ('+','-'):
                    return infer_type(node.expr)
            if t is _ast.VarRef:
                if node.name in scope:
                    return scope[node.name][0]
                if node.name in self.global_scope:
                    return self.global_scope[node.name][0]
                if node.name in self.functions:
                    # function name used as value is not allowed
                    self.errors.append(f'Function {node.name} used as value in function {f.name}')
                    return None
                self.errors.append(f'Use of undeclared identifier {node.name} in function {f.name}')
                return None
            if t is _ast.FuncCall:
                if node.name not in self.functions:
                    self.errors.append(f'Call to undeclared function {node.name} in function {f.name}')
                    return None
                callee = self.functions[node.name]
                if len(node.args) != len(callee.params):
                    self.errors.append(f'Wrong number of arguments in call to {node.name} in function {f.name}')
                # check arg types
                for i, a in enumerate(node.args):
                    at = infer_type(a)
                    if i < len(callee.params):
                        expected = callee.params[i][0]
                        if at and expected and at != expected:
                            # allow int->float
                            if not (at == 'int' and expected == 'float'):
                                self.errors.append(f'Type mismatch for argument {i+1} in call to {node.name}: expected {expected}, got {at}')
                return callee.ret_type
            if t is _ast.UnaryOp:
                return infer_type(node.expr)
            if t is _ast.BinaryOp:
                op = node.op
                ltype = infer_type(node.left)
                rtype = infer_type(node.right)
                if op in ('+', '-', '*', '/', '%'):
                    if ltype == 'float' or rtype == 'float':
                        return 'float'
                    return 'int'
                if op in ('==','!=','<','>','<=','>='):
                    return 'bool'
                if op in ('&&','||'):
                    return 'bool'
                if op in ('=','+=','-=','*=','/=','%='):
                    # assignment: type of lhs
                    if isinstance(node.left, _ast.VarRef):
                        lname = node.left.name
                        if lname in scope:
                            return scope[lname][0]
                        if lname in self.global_scope:
                            return self.global_scope[lname][0]
                    return None
            return None

        def visit(node):
            if node is None:
                return None
            t = type(node)
            if t is _ast.Compound:
                for s in node.statements:
                    visit(s)
            elif t is _ast.VarDecl:
                if node.name in scope:
                    self.errors.append(f'Redeclaration of {node.name} in function {f.name}')
                scope[node.name] = (node.var_type, node.is_const)
                if node.init:
                    it = infer_type(node.init)
                    if it and it != node.var_type:
                        if not (it == 'int' and node.var_type == 'float'):
                            self.errors.append(f'Type mismatch in initializer for {node.name}: {it} -> {node.var_type} in function {f.name}')
                    visit(node.init)
            elif t is _ast.If:
                visit(node.cond)
                visit(node.then_branch)
                if node.else_branch:
                    visit(node.else_branch)
            elif t is _ast.While:
                visit(node.cond)
                visit(node.body)
            elif t is _ast.Return:
                if node.expr:
                    rtype = infer_type(node.expr)
                    if f.ret_type != 'void':
                        if rtype and rtype != f.ret_type:
                            if not (rtype == 'int' and f.ret_type == 'float'):
                                self.errors.append(f'Return type mismatch in function {f.name}: expected {f.ret_type}, got {rtype}')
                    visit(node.expr)
            elif t is _ast.ExprStmt:
                visit(node.expr)
            elif t is _ast.BinaryOp:
                # check assignment to const
                if node.op in ('=','+=','-=','*=','/=','%='):
                    if isinstance(node.left, _ast.VarRef):
                        lname = node.left.name
                        if lname in scope and scope[lname][1]:
                            self.errors.append(f'Assignment to const variable {lname} in function {f.name}')
                        if lname in self.global_scope and self.global_scope[lname][1]:
                            self.errors.append(f'Assignment to const global {lname} in function {f.name}')
                visit(node.left)
                visit(node.right)
            elif t is _ast.UnaryOp:
                visit(node.expr)
            elif t is _ast.VarRef:
                if node.name not in scope and node.name not in self.global_scope and node.name not in self.functions:
                    self.errors.append(f'Use of undeclared identifier {node.name} in function {f.name}')
            elif t is _ast.FuncCall:
                if node.name not in self.functions:
                    self.errors.append(f'Call to undeclared function {node.name} in function {f.name}')
                for a in node.args:
                    visit(a)
            elif t is _ast.Literal:
                pass
            else:
                # unknown node types
                pass

        visit(f.body)
