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
MemberAccess = namedtuple("MemberAccess", ["name", "attrs"])
IndexAccess = namedtuple("IndexAccess", ["value", "index"])

# Control-flow signal raised by `return` so it can unwind out of
# if/while/for blocks and be caught by the enclosing function call.
class ReturnSignal(Exception):
    __slots__ = ("value",)

    def __init__(self, value=None):
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


# ── Compiled runtime model ───────────────────────────────────────────────────
#
# The interpreter compiles every scope to a static `ScopeInfo` that assigns a
# slot to each declared name. At runtime each scope instance is a `Scope` with
# a plain list of values, so variable access is a list index instead of a chain
# of string-keyed dictionary lookups.

class _Unbound:
    __slots__ = ()

    def __repr__(self):
        return "<unbound>"


UNBOUND = _Unbound()


class ScopeInfo(object):
    """Static description of a scope: name -> slot and read-only slots."""

    __slots__ = ("parent", "names", "readonly")

    def __init__(self, parent=None):
        self.parent = parent
        self.names = {}
        self.readonly = set()

    def declare(self, name: str, readonly: bool = False) -> int:
        index = self.names.get(name)
        if index is None:
            index = len(self.names)
            self.names[name] = index
        if readonly:
            self.readonly.add(index)
        else:
            self.readonly.discard(index)
        return index


class Scope(object):
    """A runtime scope instance holding the values of its `ScopeInfo` slots."""

    __slots__ = ("parent", "values", "meta")

    def __init__(self, parent, meta: ScopeInfo):
        self.parent = parent
        self.values = [UNBOUND] * len(meta.names)
        self.meta = meta


# A method/function call frame. `instance` and `klass` are None inside plain
# functions, so `this` / `::` / `.static` never leak out of a method body.
Frame = namedtuple("Frame", ["instance", "klass", "info"])
EMPTY_FRAME = Frame(None, None, None)


class Function(object):
    """A compiled Koskript function or lambda.

    ``code`` is a closure ``(interpreter, closure_scope, values, frame) -> result``.
    """

    __slots__ = ("params", "code", "closure", "frame", "name")

    def __init__(self, params, code, closure, frame=None, name="<lambda>"):
        self.params = params
        self.code = code
        self.closure = closure
        self.frame = frame
        self.name = name

    def __repr__(self):
        return f"<function {self.name}>"


class KoskriptObject(object):
    __slots__ = ("value", "read_only")

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

    __slots__ = ("name", "params", "body", "visibility", "static",
                 "is_constructor", "defining_class", "closure", "code")

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
        self.closure = None
        self.code = None

    def __repr__(self):
        kind = "constructor" if self.is_constructor else ("static method" if self.static else "method")
        return f"MethodInfo({kind} {self.name})"


class FieldInfo(object):
    """A field declared inside a class."""

    __slots__ = ("name", "value", "visibility", "static", "defining_class",
                 "code", "meta", "const", "slot")

    def __init__(self, name: str, value, modifiers: list = None):
        visibility, static = _resolve_modifiers(name, modifiers or [])
        self.name = name
        self.value = value
        self.visibility = visibility
        self.static = static
        self.defining_class = None
        # Compiled initializer: either a constant value, or `code(scope)`.
        self.code = None
        self.meta = None
        self.const = UNBOUND
        self.slot = 0

    def __repr__(self):
        return f"FieldInfo({self.visibility} field {self.name})"


class KoskriptClass(object):
    __slots__ = ("name", "parent", "fields", "methods", "constructor",
                 "closure", "_fields_cache", "_methods_cache", "_mro",
                 "_ctor_cache", "field_count")

    def __init__(self, name: str, parent=None):
        self.name = name
        self.parent = parent
        self.fields = {}
        self.methods = {}
        self.constructor = None
        self.closure = None
        self._fields_cache = None
        self._methods_cache = None
        self._mro = None
        self._ctor_cache = None
        self.field_count = parent.field_count if parent is not None else 0

    def mro(self) -> list:
        chain = self._mro
        if chain is None:
            chain = []
            klass = self
            while klass is not None:
                chain.append(klass)
                klass = klass.parent
            chain.reverse()
            self._mro = chain
        return chain

    def _build_lookup_cache(self):
        fields, methods = {}, {}
        klass = self
        while klass is not None:
            for key, value in klass.fields.items():
                if key not in fields:
                    fields[key] = (klass, value)
            for key, value in klass.methods.items():
                if key not in methods:
                    methods[key] = value
            klass = klass.parent
        self._fields_cache = fields
        self._methods_cache = methods

    def find_field(self, name: str):
        cache = self._fields_cache
        if cache is None:
            self._build_lookup_cache()
            cache = self._fields_cache
        return cache.get(name)

    def find_method(self, name: str):
        cache = self._methods_cache
        if cache is None:
            self._build_lookup_cache()
            cache = self._methods_cache
        return cache.get(name)

    def find_constructor(self):
        cached = self._ctor_cache
        if cached is None:
            klass = self
            cached = False
            while klass is not None:
                if klass.constructor is not None:
                    cached = klass.constructor
                    break
                klass = klass.parent
            self._ctor_cache = cached
        return cached if cached is not False else None

    def __repr__(self):
        return f"<class {self.name}>"


class KoskriptInstance(object):
    __slots__ = ("klass", "fields")

    def __init__(self, klass: KoskriptClass):
        self.klass = klass
        self.fields = [UNBOUND] * klass.field_count

    def __repr__(self):
        return f"<{self.klass.name} instance>"


class BoundMethod(object):
    """A method bound to an instance (or to a class, for static methods)."""

    __slots__ = ("instance", "info")

    def __init__(self, instance, info: MethodInfo):
        self.instance = instance
        self.info = info

    def __repr__(self):
        target = self.instance if self.instance is not None else self.info.defining_class
        return f"<bound {self.info.name} of {target}>"


def _resolve_modifiers(name: str, modifiers: list):
    visibility = "public"
    static = False
    for modifier in modifiers:
        if modifier == "static":
            static = True
        elif modifier in ("public", "private"):
            visibility = modifier
    return visibility, static
