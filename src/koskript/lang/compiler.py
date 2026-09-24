"""Compiles the Koskript AST into Python code.

The compiler has two levels:

* Statements are emitted as real Python source (loops, branches, assignments
  and so on) inside generated functions. Scopes become local variables that
  hold a :class:`Scope`, so name resolution is a static slot index.
* Expressions are either inlined directly into the generated statement code
  (so `a + b * 2` is a native Python expression) or compiled to a small lambda
  when a callable value is required (field initializers).

Names that cannot be resolved statically (host globals registered later,
forward declarations, missing arguments, ...) fall back to a dynamic chain
lookup, which keeps the observable semantics of the original tree walker.
"""

import os
import re

from .emtypes import *
from .errors import Errors

_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_RESERVED_NAMES = frozenset((
    "if", "elseif", "else", "while", "for", "foreach", "fn", "return",
    "local", "const", "true", "false", "null", "and", "or", "not", "in",
    "break", "continue", "class", "extends", "new", "static", "public",
    "private", "this", "super", "constructor", "import", "as",
))


def module_binding_name(path: str) -> str:
    """Default binding name for ``import "path"``: the file stem."""
    base = os.path.basename(path.replace("\\", "/"))
    if base.lower().endswith(".kos"):
        base = base[:-4]
    if not _IDENTIFIER_RE.match(base) or base in _RESERVED_NAMES:
        raise Errors.RuntimeError(
            f"cannot import '{path}': '{base}' is not a valid module name, "
            f'use import "{path}" as name')
    return base


def lookup_name(env, name):
    """Dynamic name resolution used when no static slot is known."""
    scope = env
    while scope is not None:
        index = scope.meta.names.get(name)
        if index is not None:
            value = scope.values[index]
            if value is not UNBOUND:
                return value
        scope = scope.parent
    raise Errors.NameError(f"'{name}' is not defined")


def assign_name(env, name, value):
    """Dynamic assignment used when the static slot is not bound yet."""
    scope = env
    while scope is not None:
        meta = scope.meta
        index = meta.names.get(name)
        if index is not None:
            if scope.values[index] is not UNBOUND:
                if index in meta.readonly:
                    raise Errors.ProtectedObject("cannot modify a constant value.")
                scope.values[index] = value
                return value
        scope = scope.parent
    raise Errors.NameError(f"'{name}' is not defined")


def index_get(container, key):
    try:
        return container[key]
    except (KeyError, IndexError, TypeError):
        raise Errors.RuntimeError(
            f"cannot index {type(container).__name__} with {key!r}")


_CODEGEN_COMPARISONS = {
    EquComp: "==",
    NequComp: "!=",
    LtComp: "<",
    LteComp: "<=",
    GtComp: ">",
    GteComp: ">=",
}


class _Emitter(object):
    """Emits Python source for an expression subtree.

    When attached to a `_Unit` the emitted code is inlined in place (variable
    reads become slot accesses with an unbound fallback); otherwise it is
    wrapped in a lambda by the caller.
    """

    __slots__ = ("compiler", "scope", "unit", "temp_index", "extras", "extra_index")

    def __init__(self, compiler, scope, unit=None):
        self.compiler = compiler
        self.scope = scope
        self.unit = unit
        self.temp_index = 0
        self.extras = {}
        self.extra_index = 0

    def _temp(self):
        if self.unit is not None:
            return self.unit.new_temp()
        name = f"v{self.temp_index}"
        self.temp_index += 1
        return name

    def _closure(self, node):
        closure = self.compiler._closure_expression(node, self.scope)
        if self.unit is not None:
            return self.unit.add_const(closure)
        name = f"_f{self.extra_index}"
        self.extra_index += 1
        self.extras[name] = closure
        return name

    def read(self, name, env="env"):
        resolved = self.compiler._resolve(self.scope, name)
        if resolved is None:
            return f"_g({env}, {name!r})"
        hops, index, _info = resolved
        target = env
        for _ in range(hops):
            target = f"{target}.parent"
        temp = self._temp()
        return (f"({temp} if ({temp} := {target}.values[{index}]) "
                f"is not _U else _g({env}, {name!r}))")

    def condition(self, node, env="env"):
        kind = type(node)
        if kind is AndCond:
            return (f"(({self.condition(node.left, env)}) and "
                    f"({self.condition(node.right, env)}))")
        if kind is OrCond:
            return (f"(({self.condition(node.left, env)}) or "
                    f"({self.condition(node.right, env)}))")
        if kind is NotCond:
            return f"(not ({self.condition(node.comparison[0], env)}))"
        if kind in _CODEGEN_COMPARISONS:
            return self.expr(node, env)
        return f"bool({self.expr(node, env)})"

    def _arguments(self, args, env):
        return ", ".join(f"({self.expr(arg, env)})" for arg in args)

    def _call(self, node, env="env"):
        args = self._arguments(node.args, env)
        callee_node = node.name
        if type(callee_node) is MemberAccess and len(callee_node.attrs) == 1:
            base = self.expr(callee_node.name, env)
            attr = callee_node.attrs[0].name
            return f"_i.call_member_values(({base}), {attr!r}, [{args}])"
        callee = self.expr(callee_node, env)
        return f"_i.call_value(({callee}), [{args}])"

    def expr(self, node, env="env"):
        kind = type(node)
        if kind is IntLit or kind is FloatLit or kind is StrLit or kind is BoolLit:
            return repr(node.value)
        if kind is NullLit:
            return "None"
        if kind is NameRef:
            return self.read(node.name, env)
        if kind is AddStmt:
            return f"(({self.expr(node.left, env)}) + ({self.expr(node.right, env)}))"
        if kind is SubStmt:
            return f"(({self.expr(node.left, env)}) - ({self.expr(node.right, env)}))"
        if kind is MulStmt:
            return f"(({self.expr(node.left, env)}) * ({self.expr(node.right, env)}))"
        if kind is DivStmt:
            return f"(({self.expr(node.left, env)}) / ({self.expr(node.right, env)}))"
        if kind is ModStmt:
            return f"(({self.expr(node.left, env)}) % ({self.expr(node.right, env)}))"
        if kind is NegStmt:
            return f"(-({self.expr(node.value, env)}))"
        if kind in _CODEGEN_COMPARISONS:
            operator = _CODEGEN_COMPARISONS[kind]
            return (f"(({self.expr(node.left, env)}) {operator} "
                    f"({self.expr(node.right, env)}))")
        if kind is AndCond:
            return (f"(({self.condition(node.left, env)}) and "
                    f"({self.condition(node.right, env)}))")
        if kind is OrCond:
            return (f"(({self.condition(node.left, env)}) or "
                    f"({self.condition(node.right, env)}))")
        if kind is NotCond:
            return f"(not ({self.condition(node.comparison[0], env)}))"
        if kind is ArrayLit:
            return "[" + ", ".join(self.expr(item, env) for item in node.value) + "]"
        if kind is MapLit:
            pairs = ", ".join(
                f"{self.expr(pair.key, env)}: {self.expr(pair.value, env)}"
                for pair in node.value)
            return "{" + pairs + "}"
        if kind is MemberAccess:
            base_node = node.name
            if type(base_node) is ThisRef and len(node.attrs) == 1:
                return f"_i.this_member_get({node.attrs[0].name!r})"
            value = self.expr(base_node, env)
            for attr in node.attrs:
                value = f"_i._member_get(({value}), {attr.name!r})"
            return value
        if kind is IndexAccess:
            return f"_x(({self.expr(node.value, env)}), ({self.expr(node.index, env)}))"
        if kind is FnCall:
            return self._call(node, env)
        if kind is NewExpr:
            target = self.read(node.class_name, env)
            args = self._arguments(node.args, env)
            return f"_i.new_value({node.class_name!r}, ({target}), [{args}])"
        if kind is MethodCall:
            args = self._arguments(node.args, env)
            return f"_i._method_call_values({node.name!r}, [{args}])"
        if kind is SuperCall:
            args = self._arguments(node.args, env)
            return f"_i._super_call_values({node.name!r}, [{args}])"
        if kind is StaticRef:
            return f"_i._static_ref_value({node.name!r})"
        if kind is BoundMethodCall:
            target = self.expr(node.target, env)
            args = self._arguments(node.args, env)
            return f"_i._bound_method_call_values(({target}), {node.name!r}, [{args}])"
        if kind is ThisRef:
            return "_i.current_instance()"
        fallback = self._closure(node)
        return f"{fallback}({env})"


def _uses_frame(nodes):
    """True when any node (transitively) needs the method frame stack.

    Plain functions that never use `this`, `::`, `super`, `.static`, private
    members and never create nested functions can skip pushing an (empty)
    frame entirely.
    """
    stack = list(nodes) if type(nodes) is list else [nodes]
    while stack:
        current = stack.pop()
        kind = type(current)
        if kind is ThisRef or kind is MethodCall or kind is SuperCall \
                or kind is StaticRef or kind is FnDef or kind is LambdaFnDef \
                or kind is MemberAccess or kind is MemberAssign \
                or kind is BoundMethodCall:
            return True
        if isinstance(current, tuple):
            stack.extend(current)
        elif type(current) is list:
            stack.extend(current)
    return False


class _Unit(object):
    """Builds the Python source of a chunk or a function body."""

    __slots__ = ("compiler", "scope", "params", "use_frame", "ns",
                 "lines", "indent", "const_index", "temp_index", "env_index",
                 "body_start", "create_scope")

    def __init__(self, compiler, scope, params=(), use_frame=False,
                 create_scope=True):
        self.compiler = compiler
        self.scope = scope
        self.params = params
        self.use_frame = use_frame
        self.create_scope = create_scope
        self.ns = {
            "__builtins__": {},
            "Scope": Scope,
            "Function": Function,
            "Errors": Errors,
            "ReturnSignal": ReturnSignal,
            "BreakSignal": BreakSignal,
            "ContinueSignal": ContinueSignal,
            "lookup_name": lookup_name,
            "assign_name": assign_name,
            "index_get": index_get,
            "UNBOUND": UNBOUND,
            "len": len,
            "range": range,
            "type": type,
            "hasattr": hasattr,
            "list": list,
            "dict": dict,
            "bool": bool,
        }
        self.lines = []
        self.indent = 1
        self.const_index = 0
        self.temp_index = 0
        self.env_index = 0

    # LOW LEVEL #################################################################

    def line(self, text=""):
        self.lines.append(("    " * self.indent + text) if text else "")

    def new_temp(self):
        name = f"__v{self.temp_index}"
        self.temp_index += 1
        return name

    def add_const(self, value):
        name = f"_C{self.const_index}"
        self.const_index += 1
        self.ns[name] = value
        return name

    def new_env(self, scope_info, parent_env):
        name = f"__b{self.env_index}"
        self.env_index += 1
        constant = self.add_const(scope_info)
        self.line(f"{name} = Scope({parent_env}, {constant})")
        return name

    def inline(self, node, scope, env):
        return _Emitter(self.compiler, scope, unit=self).expr(node, env)

    def inline_condition(self, node, scope, env):
        return _Emitter(self.compiler, scope, unit=self).condition(node, env)

    # FUNCTION FRAMES ###########################################################

    def open_chunk(self):
        self.line("__r = None")

    def close_chunk(self):
        self.line("return __r")
        return self._finish(
            "__chunk",
            "def __chunk(_i, env, _g=lookup_name, _U=UNBOUND, _x=index_get):")

    def open_function(self):
        if self.create_scope:
            constant = self.add_const(self.scope)
            self.line(f"env = Scope(closure, {constant})")
        else:
            self.line("env = closure")
        self._bind_params()
        if self.use_frame:
            self.line("__frames = _i.method_frames")
            self.line("__frames.append(frame)")
        self.line("try:")
        self.indent += 1
        self.body_start = len(self.lines)

    def close_function(self):
        if len(self.lines) == self.body_start:
            self.line("pass")
        self.indent -= 1
        self.line("except ReturnSignal as __s:")
        self.indent += 1
        self.line("return __s.value")
        self.indent -= 1
        self.line("except (BreakSignal, ContinueSignal) as __s:")
        self.indent += 1
        self.line("raise Errors.RuntimeError(f\"'{__s}' outside of a loop\")")
        self.indent -= 1
        if self.use_frame:
            self.line("finally:")
            self.indent += 1
            self.line("__frames.pop()")
            self.indent -= 1
        self.line("return None")
        return self._finish(
            "__fn",
            "def __fn(_i, closure, values, frame, _g=lookup_name, "
            "_U=UNBOUND, _x=index_get):")

    def _bind_params(self):
        arity = len(self.params)
        if arity == 0:
            return
        if arity == 1:
            self.line("if values:")
            self.indent += 1
            self.line("env.values[0] = values[0]")
            self.indent -= 1
        elif arity == 2:
            count = self.new_temp()
            self.line(f"{count} = len(values)")
            for index in range(arity):
                self.line(f"if {count} > {index}:")
                self.indent += 1
                self.line(f"env.values[{index}] = values[{index}]")
                self.indent -= 1
        elif arity == 3:
            count = self.new_temp()
            self.line(f"{count} = len(values)")
            for index in range(arity):
                self.line(f"if {count} > {index}:")
                self.indent += 1
                self.line(f"env.values[{index}] = values[{index}]")
                self.indent -= 1
        else:
            count = self.new_temp()
            key = self.new_temp()
            self.line(f"{count} = len(values)")
            self.line(f"if {count} > {arity}: {count} = {arity}")
            self.line(f"for {key} in range({count}):")
            self.indent += 1
            self.line(f"env.values[{key}] = values[{key}]")
            self.indent -= 1

    def _finish(self, name, header):
        source = header + "\n" + "\n".join(self.lines) + "\n"
        namespace = self.ns
        exec(compile(source, "<koskript>", "exec"), namespace)
        return namespace[name]

    # STATEMENTS ################################################################

    def emit_statements(self, statements, scope, env, track_result=False):
        count = len(statements)
        for position, statement in enumerate(statements):
            self.emit_statement(
                statement, scope, env,
                result=track_result and position == count - 1)

    def emit_statement(self, node, scope, env, result=False):
        kind = type(node)
        if kind is LocalDecl or kind is ConstDecl:
            index = scope.names[node.name]
            source = self.inline(node.value, scope, env)
            self.line(f"{env}.values[{index}] = {source}")
        elif kind is DeclStmt:
            self._emit_assign(node, scope, env)
        elif kind is MemberAssign:
            if type(node.target) is ThisRef:
                value = self.inline(node.value, scope, env)
                self.line(f"_i.this_member_set({node.attr!r}, {value})")
            else:
                value = self.inline(node.value, scope, env)
                target = self.inline(node.target, scope, env)
                value_temp = self.new_temp()
                container_temp = self.new_temp()
                self.line(f"{value_temp} = {value}")
                self.line(f"{container_temp} = {target}")
                self.line(f"_i._member_set({container_temp}, {node.attr!r}, {value_temp})")
        elif kind is FnDef:
            self._emit_fn_def(node, scope, env)
        elif kind is ClassDef:
            self._emit_class_def(node, scope, env)
        elif kind is ImportStmt:
            self._emit_import(node, scope, env)
        elif kind is ReturnStmt:
            value = "None" if node.value is None else self.inline(node.value, scope, env)
            self.line(f"raise ReturnSignal({value})")
        elif kind is WhileStmt:
            self._emit_while(node, scope, env)
        elif kind is ForStmt:
            self._emit_for(node, scope, env)
        elif kind is ForItemStmt:
            self._emit_foreach(node, scope, env)
        elif kind is BreakStmt:
            self.line("raise BreakSignal()")
        elif kind is ContinueStmt:
            self.line("raise ContinueSignal()")
        elif kind is IfStmt:
            self._emit_if(node, scope, env)
        else:
            source = self.inline(node, scope, env)
            self.line(("__r = " + source) if result else source)

    def _emit_assign(self, node, scope, env):
        source = self.inline(node.value, scope, env)
        resolved = self.compiler._resolve(scope, node.name)
        if resolved is None:
            self.line(f"assign_name({env}, {node.name!r}, {source})")
            return
        hops, index, info = resolved
        target = env
        for _ in range(hops):
            target = f"{target}.parent"
        value_temp = self.new_temp()
        self.line(f"{value_temp} = {source}")
        self.line(f"if {target}.values[{index}] is UNBOUND:")
        self.indent += 1
        self.line(f"assign_name({env}, {node.name!r}, {value_temp})")
        self.indent -= 1
        self.line("else:")
        self.indent += 1
        if index in info.readonly:
            self.line('raise Errors.ProtectedObject("cannot modify a constant value.")')
        else:
            self.line(f"{target}.values[{index}] = {value_temp}")
        self.indent -= 1

    def _emit_import(self, node, scope, env):
        name = node.name or module_binding_name(node.path)
        index = scope.names[name]
        base = self.compiler.base_dir
        self.line(
            f"{env}.values[{index}] = _i.import_module({node.path!r}, {base!r})")

    def _emit_fn_def(self, node, scope, env):
        index = scope.names[node.name]
        code, _body_scope = self.compiler._compile_function(
            node.params, self.compiler._as_statements(node.body), scope)
        code_const = self.add_const(code)
        params_const = self.add_const(tuple(node.params))
        self.line(
            f"{env}.values[{index}] = Function({params_const}, {code_const}, "
            f"{env}, _i._current_frame(), {node.name!r})")

    def _emit_class_def(self, node, scope, env):
        index = scope.names[node.name]

        field_specs = []
        for field in node.fields:
            field_scope = ScopeInfo(scope)
            value_node = field.value
            kind = type(value_node)
            if kind is IntLit or kind is FloatLit or kind is StrLit \
                    or kind is BoolLit or kind is NullLit:
                field_specs.append((field, None, None, value_node.value))
            else:
                value = self.compiler._compile_expression(value_node, field_scope)
                field_specs.append((field, value, field_scope, UNBOUND))

        method_specs = []
        for method in node.methods:
            body = self.compiler._as_statements(method.body)
            code, _body_scope = self.compiler._compile_function(
                method.params, body, scope)
            method_specs.append((method, code))

        constructor_spec = None
        if node.constructors:
            method = node.constructors[0]
            body = self.compiler._as_statements(method.body)
            code, _body_scope = self.compiler._compile_function(
                method.params, body, scope)
            constructor_spec = (method, code)

        fields_const = self.add_const(field_specs)
        methods_const = self.add_const(method_specs)
        constructor_const = "None" if constructor_spec is None \
            else self.add_const(constructor_spec)
        parent_source = "None" if node.parent is None \
            else _Emitter(self.compiler, scope, unit=self).read(node.parent, env)

        self.line(
            f"{env}.values[{index}] = _i.define_class({node.name!r}, "
            f"{node.parent!r}, {parent_source}, {env}, {fields_const}, "
            f"{methods_const}, {constructor_const}, {len(node.constructors)})")

    def _emit_while(self, node, scope, env):
        condition = self.inline_condition(node.condition, scope, env)
        body_scope = ScopeInfo(scope)
        self.compiler._predeclare(node.body, body_scope)
        self.line(f"while {condition}:")
        self.indent += 1
        self._emit_loop_body(node.body, body_scope, scope, env)
        self.indent -= 1

    def _emit_for(self, node, scope, env):
        iterable = self.new_temp()
        self.line(f"{iterable} = {self.inline(node.iterable, scope, env)}")
        self.line(
            f'if not (type({iterable}) is list or type({iterable}) is dict '
            f'or hasattr({iterable}, "__iter__")):')
        self.indent += 1
        self.line('raise Errors.MismatchType('
                  '"for statement only supports maps, arrays or iterable objects.")')
        self.indent -= 1

        loop_scope = ScopeInfo(scope)
        var_index = loop_scope.declare(node.var, readonly=True)
        loop_env = self.new_env(loop_scope, env)
        item = self.new_temp()
        body_scope = ScopeInfo(loop_scope)
        self.compiler._predeclare(node.body, body_scope)
        self.line(f"for {item} in {iterable}:")
        self.indent += 1
        self.line(f"{loop_env}.values[{var_index}] = {item}")
        self._emit_loop_body(node.body, body_scope, loop_scope, loop_env)
        self.indent -= 1

    def _emit_foreach(self, node, scope, env):
        mapping = self.new_temp()
        self.line(f"{mapping} = {self.inline(node.iterable, scope, env)}")
        self.line(f'if type({mapping}) is not dict and not hasattr({mapping}, "items"):')
        self.indent += 1
        self.line('raise Errors.MismatchType("foreach statement only supports maps.")')
        self.indent -= 1

        loop_scope = ScopeInfo(scope)
        key_index = loop_scope.declare(node.key, readonly=True)
        value_index = loop_scope.declare(node.var, readonly=True)
        loop_env = self.new_env(loop_scope, env)
        key = self.new_temp()
        value = self.new_temp()
        body_scope = ScopeInfo(loop_scope)
        self.compiler._predeclare(node.body, body_scope)
        self.line(f"for {key}, {value} in {mapping}.items():")
        self.indent += 1
        self.line(f"{loop_env}.values[{key_index}] = {key}")
        self.line(f"{loop_env}.values[{value_index}] = {value}")
        self._emit_loop_body(node.body, body_scope, loop_scope, loop_env)
        self.indent -= 1

    def _emit_loop_body(self, statements, body_scope, parent_scope, parent_env):
        self.line("try:")
        self.indent += 1
        start = len(self.lines)
        if body_scope.names:
            body_env = self.new_env(body_scope, parent_env)
            self.emit_statements(statements, body_scope, body_env)
        else:
            self.emit_statements(statements, parent_scope, parent_env)
        if len(self.lines) == start:
            self.line("pass")
        self.indent -= 1
        self.line("except ContinueSignal:")
        self.indent += 1
        self.line("continue")
        self.indent -= 1
        self.line("except BreakSignal:")
        self.indent += 1
        self.line("break")
        self.indent -= 1

    def _emit_if(self, node, scope, env):
        branches = []
        body_scope = ScopeInfo(scope)
        self.compiler._predeclare(node.body, body_scope)
        branches.append((
            self.inline_condition(node.condition, scope, env),
            node.body, body_scope))
        for branch in node.if_tree:
            if type(branch) is ElseIfStmt:
                branch_scope = ScopeInfo(scope)
                self.compiler._predeclare(branch.body, branch_scope)
                branches.append((
                    self.inline_condition(branch.condition, scope, env),
                    branch.body, branch_scope))
            else:
                branch_scope = ScopeInfo(scope)
                self.compiler._predeclare(branch.body, branch_scope)
                branches.append((None, branch.body, branch_scope))

        for position, (condition, statements, branch_scope) in enumerate(branches):
            if position == 0:
                self.line(f"if {condition}:")
            elif condition is None:
                self.line("else:")
            else:
                self.line(f"elif {condition}:")
            self.indent += 1
            start = len(self.lines)
            if branch_scope.names:
                branch_env = self.new_env(branch_scope, env)
                self.emit_statements(statements, branch_scope, branch_env)
            else:
                self.emit_statements(statements, scope, env)
            if len(self.lines) == start:
                self.line("pass")
            self.indent -= 1


class Compiler(object):
    def __init__(self, interpreter):
        self.interp = interpreter
        self.base_dir = None

    # ENTRY POINT ###############################################################

    def compile_chunk(self, statements: list, scope_info: ScopeInfo = None,
                      base_dir: str = None):
        scope = self.interp.root_info if scope_info is None else scope_info
        self.base_dir = base_dir
        self._predeclare(statements, scope)
        unit = _Unit(self, scope)
        unit.open_chunk()
        unit.emit_statements(statements, scope, "env", track_result=True)
        chunk = unit.close_chunk()
        interp = self.interp
        return lambda env, _chunk=chunk, _i=interp: _chunk(_i, env)

    def _compile_function(self, params: list, body_statements: list,
                          enclosing: ScopeInfo):
        """Compile a function body, returning its code object and scope info."""
        scope = ScopeInfo(enclosing)
        for param in params:
            scope.declare(param, readonly=True)
        self._predeclare(body_statements, scope)
        create_scope = bool(scope.names)
        compile_scope = scope if create_scope else enclosing
        unit = _Unit(self, compile_scope, params=params,
                     use_frame=_uses_frame(body_statements),
                     create_scope=create_scope)
        unit.open_function()
        unit.emit_statements(body_statements, compile_scope, "env")
        code = unit.close_function()
        return code, compile_scope

    # SCOPE HELPERS #############################################################

    def _predeclare(self, statements: list, scope: ScopeInfo):
        for stmt in statements:
            kind = type(stmt)
            if kind is LocalDecl:
                scope.declare(stmt.name)
            elif kind is ConstDecl:
                scope.declare(stmt.name, readonly=True)
            elif kind is FnDef:
                scope.declare(stmt.name)
            elif kind is ClassDef:
                scope.declare(stmt.name)
            elif kind is ImportStmt:
                scope.declare(stmt.name or module_binding_name(stmt.path))

    def _resolve(self, scope: ScopeInfo, name: str):
        """Return ``(hops, index, scope_info)`` for a statically known name."""
        hops = 0
        current = scope
        while current is not None:
            index = current.names.get(name)
            if index is not None:
                return hops, index, current
            current = current.parent
            hops += 1
        return None

    def _as_statements(self, body):
        return body if type(body) is list else [body]

    # EXPRESSION CALLABLES ######################################################

    def _compile_expression(self, node, scope: ScopeInfo):
        """Compile an expression into a callable ``(env) -> value``."""
        if type(node) is LambdaFnDef:
            return self._expr_lambda(node, scope)
        emitter = _Emitter(self, scope)
        source = emitter.expr(node)
        return self._make_lambda(source, emitter.extras)

    def _make_lambda(self, source: str, extras: dict):
        namespace = {
            "__builtins__": {},
            "bool": bool,
            "lookup_name": lookup_name,
            "index_get": index_get,
            "interp": self.interp,
            "UNBOUND": UNBOUND,
        }
        if extras:
            namespace.update(extras)
        text = ("lambda env, _g=lookup_name, _i=interp, _U=UNBOUND, _x=index_get: "
                + source)
        return eval(compile(text, "<koskript>", "eval"), namespace)

    def _closure_expression(self, node, scope: ScopeInfo):
        if type(node) is LambdaFnDef:
            return self._expr_lambda(node, scope)
        raise Errors.RuntimeError(f"Unknown expr: {type(node).__name__}")

    def _expr_lambda(self, node, scope):
        body = self._as_statements(node.body)
        code, _body_scope = self._compile_function(node.params, body, scope)
        params = node.params
        interp = self.interp

        def run(env, _code=code, _params=params, _interp=interp):
            return Function(_params, _code, env, _interp._current_frame(), "<lambda>")

        return run
