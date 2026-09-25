import inspect

from .emtypes import *
from .errors import Errors
from .compiler import Compiler


class KoskriptInterpreter(object):
    """Runs Koskript programs.

    The AST is compiled to Python closures by :class:`~.compiler.Compiler`;
    each scope keeps its values in a flat list of slots, so variable access is
    a list index instead of a chain of string-keyed dictionaries.
    """

    def __init__(self):
        self.globals = {}
        self.method_frames = []
        self._native_errors = {}
        self.root_info = ScopeInfo(None)
        self.root = Scope(None, self.root_info)
        self.compiler = Compiler(self)
        # Set by KoskriptRuntime; loads and caches .kos modules.
        self.module_loader = None

    # ENTRY POINTS ##############################################################

    def execute(self, ast: list):
        if type(ast) is not list:
            ast = [ast]
        chunk = self.compiler.compile_chunk(ast)
        self._sync_scope(self.root)
        try:
            return chunk(self.root)
        except ThrownSignal as signal:
            raise self._uncaught(signal) from None

    def run(self, ast: list):
        # Entry point: a top-level `return` stops execution and yields its value.
        try:
            return self.run_in(ast, self.root, self.root_info)
        except ThrownSignal as signal:
            raise self._uncaught(signal) from None

    @staticmethod
    def _uncaught(signal: ThrownSignal) -> Errors.KoskriptError:
        """Convert an uncaught `throw` into a host-facing exception."""
        return Errors.KoskriptError(str(signal.instance), signal.instance)

    def run_in(self, ast: list, scope: Scope, scope_info: ScopeInfo,
               base_dir: str = None):
        """Compile and run ``ast`` in its own root scope (used by modules)."""
        if type(ast) is not list:
            ast = [ast]
        chunk = self.compiler.compile_chunk(ast, scope_info, base_dir)
        self._sync_scope(scope)
        try:
            return chunk(scope)
        except ReturnSignal as signal:
            return signal.value
        except (BreakSignal, ContinueSignal) as signal:
            raise Errors.RuntimeError(f"'{signal}' outside of a loop")

    def _sync_scope(self, scope: Scope):
        values = scope.values
        missing = len(scope.meta.names) - len(values)
        if missing > 0:
            values.extend([UNBOUND] * missing)

    def import_module(self, path: str, base_dir: str = None):
        """Resolve ``import "path"``; the loader is provided by the runtime."""
        loader = self.module_loader
        if loader is None:
            raise Errors.RuntimeError(
                "module imports need a KoskriptRuntime")
        return loader(path, base_dir)

    # VARIABLES #################################################################

    def get_global(self, name: str) -> KoskriptObject:
        info = self.root_info
        index = info.names.get(name)
        if index is None or self.root.values[index] is UNBOUND:
            raise Errors.NameError(f"'{name}' is not defined")
        return KoskriptObject(
            self.root.values[index], index in info.readonly)

    def set_global(self, name: str, value) -> None:
        read_only = False
        if type(value) is KoskriptObject:
            read_only = value.read_only
            value = value.value

        info = self.root_info
        index = info.declare(name, read_only)
        values = self.root.values
        if index >= len(values):
            values.extend([UNBOUND] * (index + 1 - len(values)))
        values[index] = value
        self.globals[name] = KoskriptObject(value, read_only)

    # CALLS #####################################################################

    def call_value(self, value, values: list):
        """Invoke a Koskript or Python callable with already evaluated values."""
        kind = type(value)

        if kind is Function:
            frame = value.frame
            if frame is None:
                frame = EMPTY_FRAME
            return value.code(self, value.closure, values, frame)

        if kind is BoundMethod:
            return self._invoke_method_values(value.info, value.instance, values)

        if kind is KoskriptObject:
            return self.call_value(value.value, values)

        if kind is KoskriptClass:
            raise Errors.RuntimeError(
                f"class '{value.name}' is not callable, use 'new {value.name}()'")

        if kind is ErrorType:
            return self.instantiate_error(value, values)

        if kind is ErrorInstance:
            raise Errors.RuntimeError(
                f"error '{value.type.name}' is not callable")

        if callable(value):
            return value(*values)

        raise Errors.MismatchType(f"{type(value).__name__} is not callable")

    # ERRORS ####################################################################

    def instantiate_error(self, error_type: ErrorType, values: list) -> ErrorInstance:
        """Run an error body and return the configured error value."""
        instance = ErrorInstance(error_type)
        code = error_type.code
        if code is not None:
            code(self, error_type.closure, [instance, *values], EMPTY_FRAME)
        return instance

    def throw_value(self, value):
        """Raise ``value`` as the nearest `try` block's caught error."""
        if type(value) is not ErrorInstance:
            raise Errors.MismatchType(
                f"only errors can be thrown, got {type(value).__name__}")
        raise ThrownSignal(value)

    def wrap_exception(self, exc: Exception) -> ErrorInstance:
        """Wrap a host exception so `catch` can inspect it like an error."""
        kind = type(exc)
        error_type = self._native_errors.get(kind)
        if error_type is None:
            error_type = ErrorType(kind.__name__)
            self._native_errors[kind] = error_type
        return ErrorInstance(error_type, {"message": str(exc)}, exc)

    def _call_function(self, func: Function, values: list):
        frame = func.frame
        if frame is None:
            frame = EMPTY_FRAME
        return func.code(self, func.closure, values, frame)

    def call_member_values(self, container, name: str, values: list):
        """Call ``container.name(values)`` without materializing a bound method."""
        if type(container) is KoskriptInstance:
            info = container.klass.find_method(name)
            if info is not None:
                if info.static:
                    raise Errors.RuntimeError(
                        f"'{name}' is static, call it as '{container.klass.name}.{name}()'")
                self._check_private(info, info.defining_class)
                return info.code(
                    self, info.closure, values,
                    Frame(instance=container, klass=info.defining_class, info=info))

            found = container.klass.find_field(name)
            if found is None:
                raise Errors.RuntimeError(
                    f"'{name}' is not defined on '{container.klass.name}'")

            defining_class, field = found
            if field.visibility == "private":
                self._check_private(field, defining_class)
            return self.call_value(container.fields[field.slot], values)

        return self.call_value(self._member_get(container, name), values)

    def this_member_get(self, attr: str):
        """Fast path for ``this.attr`` inside a method."""
        frames = self.method_frames
        if frames:
            instance = frames[-1].instance
            if instance is not None:
                return self._member_get(instance, attr)
        raise Errors.RuntimeError("'this' can only be used inside an instance method")

    def this_member_set(self, attr: str, value):
        """Fast path for ``this.attr = value`` inside a method."""
        frames = self.method_frames
        if frames:
            instance = frames[-1].instance
            if instance is not None:
                self._member_set(instance, attr, value)
                return
        raise Errors.RuntimeError("'this' can only be used inside an instance method")

    def _invoke_method_values(self, info: MethodInfo, instance, values: list):
        return info.code(
            self, info.closure, values,
            Frame(instance=instance, klass=info.defining_class, info=info))

    def _current_frame(self):
        return self.method_frames[-1] if self.method_frames else None

    def current_instance(self):
        frames = self.method_frames
        if frames:
            frame = frames[-1]
            if frame.instance is not None:
                return frame.instance
        raise Errors.RuntimeError("'this' can only be used inside an instance method")

    def new_value(self, name, target, values: list):
        if type(target) is KoskriptClass:
            return self._instantiate(target, values)
        if inspect.isclass(target):
            return target(*values)
        raise Errors.RuntimeError(f"'{name}' is not a class")

    # CLASS EXPRESSIONS #########################################################

    def define_class(self, name, parent_name, parent, closure, field_specs,
                     method_specs, constructor_spec, constructor_count):
        if parent is not None and not isinstance(parent, KoskriptClass):
            raise Errors.RuntimeError(f"'{parent_name}' is not a class")

        klass = KoskriptClass(name=name, parent=parent)
        klass.closure = closure

        for field, value_code, value_scope, const in field_specs:
            info = FieldInfo(field.name, field.value, field.modifiers)

            if info.static:
                raise Errors.RuntimeError(
                    f"field '{field.name}' cannot be static (only methods can be static)")

            if info.name in klass.fields or info.name in klass.methods:
                raise Errors.RuntimeError(
                    f"'{info.name}' is already defined in class '{name}'")

            if parent is not None and (
                    parent.find_field(info.name) is not None
                    or parent.find_method(info.name) is not None):
                raise Errors.RuntimeError(
                    f"field '{info.name}' shadows an inherited member of '{parent.name}'")

            info.defining_class = klass
            info.code = value_code
            info.meta = value_scope
            info.const = const
            info.slot = klass.field_count
            klass.field_count += 1
            klass.fields[info.name] = info

        for method, code in method_specs:
            info = MethodInfo(
                method.name, method.params, method.body,
                method.modifiers, is_constructor=False
            )

            if info.name in klass.methods or info.name in klass.fields:
                raise Errors.RuntimeError(
                    f"'{info.name}' is already defined in class '{name}'")

            if parent is not None:
                if parent.find_field(info.name) is not None:
                    raise Errors.RuntimeError(
                        f"method '{info.name}' shadows an inherited field of '{parent.name}'")

                inherited = parent.find_method(info.name)
                if inherited is not None and inherited.static != info.static:
                    kind = "static" if inherited.static else "instance"
                    raise Errors.RuntimeError(
                        f"cannot override {kind} method '{info.name}' of '{parent.name}' "
                        f"with a {'static' if info.static else 'instance'} method")

            info.defining_class = klass
            info.closure = klass.closure
            info.code = code
            klass.methods[info.name] = info

        if constructor_count > 1:
            raise Errors.RuntimeError(
                f"class '{name}' defines more than one constructor")

        if constructor_spec is not None:
            method, code = constructor_spec
            constructor = MethodInfo(
                method.name, method.params, method.body,
                method.modifiers, is_constructor=True
            )

            if constructor.static:
                raise Errors.RuntimeError("a constructor cannot be static")

            constructor.defining_class = klass
            constructor.closure = klass.closure
            constructor.code = code
            klass.constructor = constructor

        return klass

    def _instantiate(self, klass: KoskriptClass, values: list) -> KoskriptInstance:
        instance = KoskriptInstance(klass)
        frames = self.method_frames

        for defining_class in klass.mro():
            closure = defining_class.closure
            for name, info in defining_class.fields.items():
                const = info.const
                if const is not UNBOUND:
                    instance.fields[info.slot] = const
                    continue
                env = Scope(closure, info.meta)
                frames.append(Frame(instance=instance, klass=defining_class, info=None))
                try:
                    instance.fields[info.slot] = info.code(env)
                finally:
                    frames.pop()

        constructor = klass.find_constructor()
        if constructor is not None:
            self._check_private(constructor, constructor.defining_class)
            self._invoke_method_values(constructor, instance, values)

        return instance

    def _method_call_values(self, name: str, values: list):
        frame = self._current_frame()

        if frame is None or frame.klass is None:
            raise Errors.RuntimeError("'::' can only be used inside a class method")

        if frame.instance is None:
            raise Errors.RuntimeError(f"cannot call instance method '{name}' from a static method")

        # Private methods are resolved non-virtually in their defining class;
        # public ones use dynamic dispatch on the actual instance class.
        info = None
        own = frame.klass.find_method(name)
        if own is not None and own.visibility == "private":
            info = own

        if info is None:
            info = frame.instance.klass.find_method(name)

        if info is None:
            raise Errors.RuntimeError(f"method '{name}' is not defined in '{frame.klass.name}'")

        if info.static:
            raise Errors.RuntimeError(f"'{name}' is static, call it as .{name}()")

        self._check_private(info, info.defining_class)
        return self._invoke_method_values(info, frame.instance, values)

    def _bound_method_call_values(self, container, name: str, values: list):
        if type(container) is KoskriptInstance:
            info = container.klass.find_method(name)
            if info is None:
                raise Errors.RuntimeError(
                    f"method '{name}' is not defined on '{container.klass.name}'")

            if info.static:
                raise Errors.RuntimeError(
                    f"'{name}' is static, call it as '{container.klass.name}.{name}()'")

            self._check_private(info, info.defining_class)
            return self._invoke_method_values(info, container, values)

        if type(container) is KoskriptClass:
            info = container.find_method(name)
            if info is None:
                raise Errors.RuntimeError(
                    f"method '{name}' is not defined on '{container.name}'")

            if info.static:
                raise Errors.RuntimeError(
                    f"'{name}' is static, call it as '{container.name}.{name}()'")

            raise Errors.RuntimeError(
                f"'{name}' is an instance method, call it on an instance of '{container.name}'")

        method = self._python_getattr(container, name)

        if not callable(method):
            raise Errors.RuntimeError(
                f"'{name}' is not a method of {type(container).__name__}")

        return method(*values)

    def _super_call_values(self, name: str, values: list):
        frame = self._current_frame()

        if frame is None or frame.instance is None:
            raise Errors.RuntimeError("'super::' can only be used inside an instance method")

        parent = frame.klass.parent if frame.klass else None
        if parent is None:
            raise Errors.RuntimeError(f"class '{frame.klass.name}' has no parent class")

        if name == "constructor":
            if frame.info is None or not frame.info.is_constructor:
                raise Errors.RuntimeError(
                    "'super::constructor()' can only be called from a constructor")

            constructor = parent.find_constructor()
            if constructor is None:
                raise Errors.RuntimeError(f"class '{parent.name}' has no constructor")

            self._check_private(constructor, constructor.defining_class)
            self._invoke_method_values(constructor, frame.instance, values)
            return frame.instance

        info = parent.find_method(name)
        if info is None:
            raise Errors.RuntimeError(f"method '{name}' is not defined in '{parent.name}'")

        if info.static:
            raise Errors.RuntimeError(f"'{name}' is static, call it as .{name}()")

        self._check_private(info, info.defining_class)
        return self._invoke_method_values(info, frame.instance, values)

    def _static_ref_value(self, name: str):
        frame = self._current_frame()

        if frame is None or frame.klass is None:
            raise Errors.RuntimeError("'.' static calls can only be used inside a class method")

        info = frame.klass.find_method(name)
        if info is None:
            raise Errors.RuntimeError(f"static method '{name}' is not defined in '{frame.klass.name}'")

        if not info.static:
            raise Errors.RuntimeError(f"'{name}' is not static, call it as ::{name}()")

        self._check_private(info, info.defining_class)
        return BoundMethod(None, info)

    # MEMBERS ###################################################################

    def _check_private(self, info_or_field, defining_class):
        if info_or_field.visibility != "private":
            return

        frame = self._current_frame()
        if frame is None or frame.klass is not defining_class:
            raise Errors.RuntimeError(
                f"'{info_or_field.name}' is private to '{defining_class.name}' and cannot be accessed from outside")

    def _member_get(self, container, attr: str):
        kind = type(container)

        if kind is dict:
            try:
                return container[attr]
            except KeyError:
                raise Errors.RuntimeError(
                    f"no member with the value '{attr}' is defined on {container}")

        if kind is KoskriptInstance:
            found = container.klass.find_field(attr)
            if found is not None:
                defining_class, field = found
                if field.visibility == "private":
                    self._check_private(field, defining_class)
                return container.fields[field.slot]

            info = container.klass.find_method(attr)
            if info is not None:
                if info.static:
                    raise Errors.RuntimeError(
                        f"'{attr}' is static, call it as '{container.klass.name}.{attr}()'")
                self._check_private(info, info.defining_class)
                return BoundMethod(container, info)

            raise Errors.RuntimeError(
                f"'{attr}' is not defined on '{container.klass.name}'")

        if kind is ErrorInstance:
            fields = container.fields
            if attr in fields:
                return fields[attr]
            if attr == "name":
                return container.type.name
            if attr == "native":
                return container.native
            if attr == "message":
                return None
            raise Errors.RuntimeError(
                f"error '{container.type.name}' has no member '{attr}'")

        if kind is KoskriptClass:
            info = container.find_method(attr)
            if info is None:
                raise Errors.RuntimeError(
                    f"'{container.name}' has no member '{attr}'")

            if not info.static:
                raise Errors.RuntimeError(
                    f"'{attr}' is an instance method, call it on an instance of '{container.name}'")

            self._check_private(info, info.defining_class)
            return BoundMethod(None, info)

        if kind is Module:
            scope = container.scope
            index = scope.meta.names.get(attr)
            if index is None or scope.values[index] is UNBOUND:
                raise Errors.RuntimeError(
                    f"module '{container.name}' has no member '{attr}'")
            return scope.values[index]

        if container is None:
            raise Errors.MismatchType("cannot access members on null")

        return self._python_getattr(container, attr)

    def _python_getattr(self, container, attr: str):
        if attr.startswith("__") and attr.endswith("__"):
            raise Errors.RuntimeError(
                f"access to dunder attribute '{attr}' is not allowed")

        try:
            return getattr(container, attr)
        except AttributeError:
            raise Errors.RuntimeError(
                f"'{attr}' is not defined on {type(container).__name__}")

    def _member_set(self, container, attr: str, value):
        kind = type(container)

        if kind is dict:
            container[attr] = value
            return

        if kind is KoskriptInstance:
            found = container.klass.find_field(attr)
            if found is None:
                raise Errors.RuntimeError(
                    f"'{attr}' is not a field of '{container.klass.name}'")

            defining_class, field = found
            if field.visibility == "private":
                self._check_private(field, defining_class)
            container.fields[field.slot] = value
            return

        if kind is ErrorInstance:
            if attr == "name":
                raise Errors.RuntimeError(
                    "the name of an error cannot be modified")
            container.fields[attr] = value
            return

        if kind is Module:
            scope = container.scope
            meta = scope.meta
            index = meta.names.get(attr)
            if index is None or scope.values[index] is UNBOUND:
                raise Errors.RuntimeError(
                    f"module '{container.name}' has no member '{attr}'")
            if index in meta.readonly:
                raise Errors.ProtectedObject("cannot modify a constant value.")
            scope.values[index] = value
            return

        if container is None:
            raise Errors.MismatchType("cannot assign members on null")

        if attr.startswith("__") and attr.endswith("__"):
            raise Errors.RuntimeError(
                f"access to dunder attribute '{attr}' is not allowed")

        try:
            setattr(container, attr, value)
        except AttributeError:
            raise Errors.MismatchType(
                f"cannot assign member on {type(container).__name__}")
