from collections import namedtuple
from .errors import Errors
from typing import Any

# Literals and references
IntLit = namedtuple("IntLit", ["value"])
FloatLit = namedtuple("FloatLit", ["value"])
StrLit = namedtuple("StrLit", ["value"])
BoolLit = namedtuple("BoolLit", ["value"])
ArrayLit = namedtuple("ArrayLit", ["value"])
MapLit = namedtuple("MapLit", ["value"])
MapValue = namedtuple("MapValue", ["key", "value"])
NameRef = namedtuple("NameRef", ["name"])
Function = namedtuple("Function", ["params", "body"])
MemberAccess = namedtuple("MemberAccess", ["name", "attrs"])
IndexAccess = namedtuple("IndexAccess", ["value", "index"])

# Control-flow signal raised by `return` so it can unwind out of
# if/while/for blocks and be caught by the enclosing function call.
class ReturnSignal(Exception):
    def __init__(self, value=None):
        super().__init__("return")
        self.value = value

# Node Objects
LocalDecl = namedtuple("LocalDecl", ["name", "value"])
DeclStmt = namedtuple("DeclStmt", ["name", "value"])
ReturnStmt = namedtuple("ReturnStmt", ["value"])
FnDef  = namedtuple("FnDef",  ["name", "params", "body"])
FnCall = namedtuple("FnCall", ["name", "args"])
LambdaFnDef = namedtuple("LambdaFnDef", ["params", "body"])
WhileStmt   = namedtuple("WhileStmt",   ["condition", "body"])
ForStmt     = namedtuple("ForStmt",     ["var", "iterable", "body"])
ForItemStmt = namedtuple("ForItemStmt", ["key", "var", "iterable", "body"])
AddStmt = namedtuple("AddStmt", ["left", "right"])
SubStmt = namedtuple("SubStmt", ["left", "right"])
MulStmt = namedtuple("MulStmt", ["left", "right"])
DivStmt = namedtuple("DivStmt", ["left", "right"])
ModStmt = namedtuple("ModStmt", ["left", "right"])
NegStmt = namedtuple("NegStmt", ["value"])
IfStmt = namedtuple("IfStmt", ["condition", "body", "if_tree"])
ElseIfStmt = namedtuple("ElseIfStmt", ["condition", "body"])
ElseStmt = namedtuple("ElseStmt", ["body"])

# Conditions
AndCond = namedtuple("AndCond", ["left", "right"])
OrCond = namedtuple("OrCond", ["left", "right"])
NotCond = namedtuple("NotCond", ["comparison"])

# Comparisons
EquComp = namedtuple("EquComp", ["left", "right"])
NequComp = namedtuple("NequComp", ["left", "right"])
LteComp = namedtuple("LteComp", ["left", "right"])
GteComp = namedtuple("GteComp", ["left", "right"])
LtComp = namedtuple("LtComp", ["left", "right"])
GtComp = namedtuple("GtComp", ["left", "right"])


class KoskriptObject(object):
    def __init__(self, value: Any, read_only: bool = False):
        self.value = value
        self.read_only = read_only

    def set_value(self, value: Any):
        if self.read_only:
            raise Errors.ProtectedObject("cannot modify a constant value.")

        self.value = value

    def __repr__(self):
        return f"KoskriptObject(value={self.value}, read_only={self.read_only})"

