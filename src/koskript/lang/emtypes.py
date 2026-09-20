from collections import namedtuple
from .errors import Errors
from typing import Any

# Literals and references
IntLit = namedtuple("IntLit", ["value"])
FloatLit = namedtuple("FloatLit", ["value"])
StrLit = namedtuple("StrLit", ["value"])
BoolLit = namedtuple("BoolLit", ["value"])
NullLit = namedtuple("NullLit", ["value"])
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

# Signals raised by `break` / `continue`, caught by the nearest loop.
class BreakSignal(Exception):
    def __init__(self):
        super().__init__("break")

class ContinueSignal(Exception):
    def __init__(self):
        super().__init__("continue")

# Node Objects
LocalDecl = namedtuple("LocalDecl", ["name", "value"])
ConstDecl = namedtuple("ConstDecl", ["name", "value"])
DeclStmt = namedtuple("DeclStmt", ["name", "value"])
MemberAssign = namedtuple("MemberAssign", ["target", "attr", "value"])
ReturnStmt = namedtuple("ReturnStmt", ["value"])
FnDef  = namedtuple("FnDef",  ["name", "params", "body"])
FnCall = namedtuple("FnCall", ["name", "args"])
LambdaFnDef = namedtuple("LambdaFnDef", ["params", "body"])

# Class objects
ClassDef = namedtuple("ClassDef", ["name", "parent", "fields", "methods", "constructors"])
ClassField = namedtuple("ClassField", ["name", "value", "modifiers"])
ClassMethod = namedtuple("ClassMethod", ["name", "params", "body", "modifiers", "is_constructor"])

# Class expressions
NewExpr = namedtuple("NewExpr", ["class_name", "args"])
ThisRef = namedtuple("ThisRef", [])
MethodCall = namedtuple("MethodCall", ["name", "args"])
BoundMethodCall = namedtuple("BoundMethodCall", ["target", "name", "args"])
SuperCall = namedtuple("SuperCall", ["name", "args"])
StaticRef = namedtuple("StaticRef", ["name"])
WhileStmt   = namedtuple("WhileStmt",   ["condition", "body"])
ForStmt     = namedtuple("ForStmt",     ["var", "iterable", "body"])
ForItemStmt = namedtuple("ForItemStmt", ["key", "var", "iterable", "body"])
BreakStmt    = namedtuple("BreakStmt", [])
ContinueStmt = namedtuple("ContinueStmt", [])
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


class MethodInfo(object):
    """A method declared inside a class."""

    def __init__(self, name: str, params: list, body: list, modifiers: list = None,
                 is_constructor: bool = False):
        visibility, static = _resolve_modifiers(name, modifiers or [])
        self.name = name
        self.params = params
        self.body = body
        self.visibility = visibility
        self.static = static
        self.is_constructor = is_constructor
        self.defining_class = None

    def __repr__(self):
        kind = "constructor" if self.is_constructor else ("static method" if self.static else "method")
        return f"MethodInfo({kind} {self.name})"


class FieldInfo(object):
    """A field declared inside a class."""

    def __init__(self, name: str, value, modifiers: list = None):
        visibility, static = _resolve_modifiers(name, modifiers or [])
        self.name = name
        self.value = value
        self.visibility = visibility
        self.static = static
        self.defining_class = None

    def __repr__(self):
        return f"FieldInfo({self.visibility} field {self.name})"


class KoskriptClass(object):
    def __init__(self, name: str, parent=None):
        self.name = name
        self.parent = parent
        self.fields = {}
        self.methods = {}
        self.constructor: MethodInfo | None = None

    def mro(self) -> list:
        chain, klass = [], self
        while klass is not None:
            chain.append(klass)
            klass = klass.parent
        return list(reversed(chain))

    def find_field(self, name: str):
        klass = self
        while klass is not None:
            if name in klass.fields:
                return klass, klass.fields[name]
            klass = klass.parent
        return None

    def find_method(self, name: str):
        klass = self
        while klass is not None:
            if name in klass.methods:
                return klass.methods[name]
            klass = klass.parent
        return None

    def find_constructor(self):
        klass = self
        while klass is not None:
            if klass.constructor is not None:
                return klass.constructor
            klass = klass.parent
        return None

    def __repr__(self):
        return f"<class {self.name}>"


class KoskriptInstance(object):
    def __init__(self, klass: KoskriptClass):
        self.klass = klass
        self.fields = {}

    def __repr__(self):
        return f"<{self.klass.name} instance>"


class BoundMethod(object):
    """A method bound to an instance (or to a class, for static methods)."""

    def __init__(self, instance, info: MethodInfo):
        self.instance = instance
        self.info = info

    def __repr__(self):
        target = self.instance if self.instance is not None else self.info.defining_class
        return f"<bound {self.info.name} of {target}>"


# A method/function call frame. `instance` and `klass` are None inside plain
# functions, so `this` / `::` / `.static` never leak out of a method body.
Frame = namedtuple("Frame", ["instance", "klass", "info"])


def _resolve_modifiers(name: str, modifiers: list):
    visibility = "public"
    static = False
    for modifier in modifiers:
        if modifier == "static":
            static = True
        elif modifier in ("public", "private"):
            visibility = modifier
    return visibility, static

