from dataclasses import dataclass
from typing import List, Optional, Any


class Node:
    pass


@dataclass
class Program(Node):
    declarations: List[Node]


@dataclass
class FuncDecl(Node):
    ret_type: str
    name: str
    params: List[Any]
    body: Any


@dataclass
class VarDecl(Node):
    var_type: str
    name: str
    init: Optional[Any] = None
    is_const: bool = False


@dataclass
class Compound(Node):
    statements: List[Node]


@dataclass
class If(Node):
    cond: Any
    then_branch: Any
    else_branch: Optional[Any]


@dataclass
class While(Node):
    cond: Any
    body: Any


@dataclass
class For(Node):
    init: Optional[Any]
    cond: Optional[Any]
    post: Optional[Any]
    body: Any


@dataclass
class Return(Node):
    expr: Optional[Any]


@dataclass
class ExprStmt(Node):
    expr: Any


@dataclass
class BinaryOp(Node):
    op: str
    left: Any
    right: Any


@dataclass
class UnaryOp(Node):
    op: str
    expr: Any


@dataclass
class Literal(Node):
    value: Any
    typ: str


@dataclass
class VarRef(Node):
    name: str


@dataclass
class FuncCall(Node):
    name: str
    args: List[Any]
