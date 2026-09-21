import inspect

from .emtypes import *

class KoskriptInterpreter(object):
    def __init__(self):
        self.globals = {"_": {}}
        self.scopes = []
        self.scope_parents = {}
        self.method_frames = []
        self._scope_counter = 0
        self._handlers = {
            LocalDecl:   self._local_decl,
            ConstDecl:   self._const_decl,
            DeclStmt: self._decl,
            MemberAssign: self._member_assign,
            ClassDef:    self._class_def,
            FnDef:       self._fn_def,
            FnCall:      self._fn_call,
            ReturnStmt:  self._return_stmt,
            WhileStmt:   self._while_stmt,
            ForStmt:     self._for_stmt,
            ForItemStmt: self._foritem_stmt,
            BreakStmt:    self._break_stmt,
            ContinueStmt: self._continue_stmt,
            IfStmt: self._if_stmt,
            ElseIfStmt: self._else_if_stmt,
            ElseStmt: self._else_stmt
        }
    
    def execute(self, ast: list):
        result = None
        for node in ast:
            result = self.visit(node)
        return result

    def run(self, ast: list):
        # Entry point: a top-level `return` stops execution and yields its value.
        try:
            return self.execute(ast)
        except ReturnSignal as signal:
            return signal.value
        except (BreakSignal, ContinueSignal) as signal:
            raise Errors.RuntimeError(f"'{signal}' outside of a loop")

    def execute_block(self, body: list):
        self._push_scope("block", self._current_scope())
        try:
            self.execute(body)
        finally:
            self.scopes.pop()

    def _current_scope(self) -> str:
        return self.scopes[-1] if self.scopes else "_"

    def _push_scope(self, prefix: str, parent: str) -> str:
        self._scope_counter += 1
        scope = f"{prefix}_{self._scope_counter}"
        self.scope_parents[scope] = parent
        self.scopes.append(scope)
        return scope

    def get_global(self, name: str) -> KoskriptObject:
        scope = self._current_scope()
        while scope is not None:
            if scope in self.globals and name in self.globals[scope]:
                return self.globals[scope][name]
            scope = self.scope_parents.get(scope)
        
        if name in self.globals["_"]:
            return self.globals["_"][name]
        
        raise Errors.NameError(f"'{name}' is not defined")

    def set_global(self, name: str, value: KoskriptObject) -> None:
        if self.scopes:
            scope = self.scopes[-1]
            if scope not in self.globals:
                self.globals[scope] = {}
            self.globals[scope][name] = value
            return
        
        self.globals["_"][name] = value

    def visit(self, node):
        handler = self._handlers.get(type(node))
        if handler is None:
            # Statements can also be bare expressions (e.g. `f(x)`, `1 + 2`).
            return self.expr_eval(node)
        return handler(node)

    # EVALUATORS ####################################################################

    def expr_eval(self, expr):
        match expr:
            case IntLit(value):  return value
            case FloatLit(value): return value
            case StrLit(value):  return value
            case BoolLit(value): return value
            case NullLit(value): return value
            case NameRef(name):  return self.get_global(name).value
            case AddStmt(l, r):  return self.expr_eval(l) + self.expr_eval(r)
            case SubStmt(l, r):  return self.expr_eval(l) - self.expr_eval(r)
            case MulStmt(l, r):  return self.expr_eval(l) * self.expr_eval(r)
            case DivStmt(l, r):  return self.expr_eval(l) / self.expr_eval(r)
            case ModStmt(l, r):  return self.expr_eval(l) % self.expr_eval(r)
            case NegStmt(v):     return -self.expr_eval(v)
            case ArrayLit(array): return [self.expr_eval(i) for i in array]

            case MapValue(key, value): return key, value
            case MapLit(values):
                res = {}
                for val in values:
                    res[self.expr_eval(val.key)] = self.expr_eval(val.value)
                return res

            case MemberAccess(name, attrs):
                value = self.expr_eval(name)

                for attr in attrs:
                    value = self._member_get(value, attr.name)

                return value

            case ThisRef():
                frame = self._current_frame()

                if frame is None or frame.instance is None:
                    raise Errors.RuntimeError("'this' can only be used inside an instance method")

                return frame.instance

            case NewExpr(class_name, args):
                target = self.get_global(class_name).value

                if isinstance(target, KoskriptClass):
                    return self._instantiate(target, args)

                if inspect.isclass(target):
                    return target(*[self.expr_eval(arg) for arg in args])

                raise Errors.RuntimeError(f"'{class_name}' is not a class")

            case MethodCall(name, args):
                return self._method_call(name, args)

            case BoundMethodCall(target, name, args):
                return self._bound_method_call(target, name, args)

            case SuperCall(name, args):
                return self._super_call(name, args)

            case StaticRef(name):
                return self._static_ref(name)

            case IndexAccess(value, index):
                container = self.expr_eval(value)
                key = self.expr_eval(index)

                try:
                    return container[key]
                except (KeyError, IndexError, TypeError):
                    raise Errors.RuntimeError(
                        f"cannot index {type(container).__name__} with {key!r}")

            case FnCall(n, arg): return self.fn_eval(n, arg)
            case LambdaFnDef(p, body): return Function(
                params=p, body=body,
                closure=self._current_scope(), frame=self._current_frame())
            case EquComp() | NequComp() | LteComp() | GteComp() | GtComp() | LtComp() \
               | AndCond() | OrCond() | NotCond():
                return self.cond_eval(expr)
            case _: raise Errors.RuntimeError(f"Unknown expr: {type(expr).__name__}")

    def fn_eval(self, callee, args):
        if isinstance(callee, NameRef):
            func: KoskriptObject = self.get_global(callee.name)
            value = func.value
        else:
            value = self.expr_eval(callee)

        if isinstance(value, BoundMethod):
            return self._invoke_method(value.info, value.instance, args)

        if isinstance(value, KoskriptClass):
            raise Errors.RuntimeError(
                f"class '{value.name}' is not callable, use 'new {value.name}()'")

        if isinstance(value, KoskriptObject):
            value = value.value

        if callable(value):
            return value(*[self.expr_eval(arg) for arg in args])

        if type(value) != Function:
            raise Errors.MismatchType(f"{callee} is not callable.")
        
        func_params = value.params
        func_body = value.body
        if type(func_body) != list: func_body = [func_body]

        arg_values = [self.expr_eval(arg) for arg in args]

        self._push_scope(f"func_{callee}", value.closure)
        self.method_frames.append(
            value.frame if value.frame is not None
            else Frame(instance=None, klass=None, info=None))
        try:
            self._bind_params(func_params, arg_values)
            self.execute(func_body)
        except (BreakSignal, ContinueSignal) as signal:
            raise Errors.RuntimeError(f"'{signal}' outside of a loop")
        except ReturnSignal as signal:
            return signal.value
        finally:
            self.method_frames.pop()
            self.scopes.pop()
        return None

    # CLASSES #######################################################################

    def _current_frame(self):
        return self.method_frames[-1] if self.method_frames else None

    def _bind_params(self, params: list, values: list):
        for index_param, param in enumerate(params):
            try:
                self.set_global(
                    name=param,
                    value=KoskriptObject(
                        values[index_param],
                        read_only=True)
                )
            except IndexError:
                break

    def _invoke_method(self, info: MethodInfo, instance, args: list):
        arg_values = [self.expr_eval(arg) for arg in args]

        self._push_scope(f"method_{info.name}", info.closure)
        self.method_frames.append(
            Frame(instance=instance, klass=info.defining_class, info=info))
        try:
            self._bind_params(info.params, arg_values)
            try:
                self.execute(info.body)
            except ReturnSignal as signal:
                return signal.value
        except (BreakSignal, ContinueSignal) as signal:
            raise Errors.RuntimeError(f"'{signal}' outside of a loop")
        finally:
            self.method_frames.pop()
            self.scopes.pop()
        return None

    def _instantiate(self, klass: KoskriptClass, args: list) -> KoskriptInstance:
        instance = KoskriptInstance(klass)

        for defining_class in klass.mro():
            for name, field in defining_class.fields.items():
                self._push_scope("class_fields", defining_class.closure)
                self.method_frames.append(
                    Frame(instance=instance, klass=defining_class, info=None))
                try:
                    instance.fields[name] = self.expr_eval(field.value)
                finally:
                    self.method_frames.pop()
                    self.scopes.pop()

        constructor = klass.find_constructor()
        if constructor is not None:
            self._check_private(constructor, constructor.defining_class)
            self._invoke_method(constructor, instance, args)

        return instance

    def _method_call(self, name: str, args: list):
        frame = self._current_frame()

        if frame is None or frame.klass is None:
            raise Errors.RuntimeError("'::' can only be used inside a class method")

        if frame.instance is None:
            raise Errors.RuntimeError(f"cannot call instance method '{name}' from a static method")

        # Private methods are resolved non-virtually in their defining class;
        # public ones use dynamic dispatch on the actual instance class.
        info = None
        if frame.klass is not None:
            own = frame.klass.find_method(name)
            if own is not None and own.visibility == "private":
                info = own

        if info is None:
            start = frame.instance.klass
            info = start.find_method(name)

        if info is None:
            raise Errors.RuntimeError(f"method '{name}' is not defined in '{frame.klass.name}'")

        if info.static:
            raise Errors.RuntimeError(f"'{name}' is static, call it as .{name}()")

        self._check_private(info, info.defining_class)
        return self._invoke_method(info, frame.instance, args)

    def _bound_method_call(self, target, name: str, args: list):
        container = self.expr_eval(target)

        if isinstance(container, KoskriptInstance):
            info = container.klass.find_method(name)
            if info is None:
                raise Errors.RuntimeError(
                    f"method '{name}' is not defined on '{container.klass.name}'")

            if info.static:
                raise Errors.RuntimeError(
                    f"'{name}' is static, call it as '{container.klass.name}.{name}()'")

            self._check_private(info, info.defining_class)
            return self._invoke_method(info, container, args)

        if isinstance(container, KoskriptClass):
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

        return method(*[self.expr_eval(arg) for arg in args])

    def _super_call(self, name: str, args: list):
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
            self._invoke_method(constructor, frame.instance, args)
            return frame.instance

        info = parent.find_method(name)
        if info is None:
            raise Errors.RuntimeError(f"method '{name}' is not defined in '{parent.name}'")

        if info.static:
            raise Errors.RuntimeError(f"'{name}' is static, call it as .{name}()")

        self._check_private(info, info.defining_class)
        return self._invoke_method(info, frame.instance, args)

    def _static_ref(self, name: str):
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

    def _check_private(self, info_or_field, defining_class):
        if info_or_field.visibility != "private":
            return

        frame = self._current_frame()
        if frame is None or frame.klass is not defining_class:
            raise Errors.RuntimeError(
                f"'{info_or_field.name}' is private to '{defining_class.name}' and cannot be accessed from outside")

    def _member_get(self, container, attr: str):
        if isinstance(container, dict):
            try:
                return container[attr]
            except KeyError:
                raise Errors.RuntimeError(f"no member with the value '{attr}' is defined on {container}")

        if isinstance(container, KoskriptInstance):
            found = container.klass.find_field(attr)
            if found is not None:
                defining_class, field = found
                self._check_private(field, defining_class)
                return container.fields[attr]

            info = container.klass.find_method(attr)
            if info is not None:
                if info.static:
                    raise Errors.RuntimeError(
                        f"'{attr}' is static, call it as '{container.klass.name}.{attr}()'")
                self._check_private(info, info.defining_class)
                return BoundMethod(container, info)

            raise Errors.RuntimeError(
                f"'{attr}' is not defined on '{container.klass.name}'")

        if isinstance(container, KoskriptClass):
            info = container.find_method(attr)
            if info is None:
                raise Errors.RuntimeError(
                    f"'{container.name}' has no member '{attr}'")

            if not info.static:
                raise Errors.RuntimeError(
                    f"'{attr}' is an instance method, call it on an instance of '{container.name}'")

            self._check_private(info, info.defining_class)
            return BoundMethod(None, info)

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
        if isinstance(container, dict):
            container[attr] = value
            return

        if isinstance(container, KoskriptInstance):
            found = container.klass.find_field(attr)
            if found is None:
                raise Errors.RuntimeError(
                    f"'{attr}' is not a field of '{container.klass.name}'")

            defining_class, field = found
            self._check_private(field, defining_class)
            container.fields[attr] = value
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


    def cond_eval(self, condition):
        match condition:
            case EquComp(l, r): return self.expr_eval(l) == self.expr_eval(r)
            case NequComp(l, r): return self.expr_eval(l) != self.expr_eval(r)
            case LteComp(l, r): return self.expr_eval(l) <= self.expr_eval(r)
            case GteComp(l, r): return self.expr_eval(l) >= self.expr_eval(r)
            case GtComp(l, r): return self.expr_eval(l) > self.expr_eval(r)
            case LtComp(l, r): return self.expr_eval(l) < self.expr_eval(r)

            case AndCond(l, r): return self.cond_eval(l) and self.cond_eval(r)
            case OrCond(l, r): return self.cond_eval(l) or self.cond_eval(r)

            case NotCond(com): return not self.cond_eval(com[0])

            case _: return bool(self.expr_eval(condition))
    

    # HANDLERS ######################################################################
    
    def _local_decl(self, node: LocalDecl):
        value = self.expr_eval(node.value)
        name = node.name

        self.set_global(
            name,
            KoskriptObject(
                value=value
            )
        )

    def _const_decl(self, node: ConstDecl):
        self.set_global(
            name=node.name,
            value=KoskriptObject(
                value=self.expr_eval(node.value),
                read_only=True
            )
        )

    def _member_assign(self, node: MemberAssign):
        value = self.expr_eval(node.value)
        container = self.expr_eval(node.target)
        self._member_set(container, node.attr, value)

    def _class_def(self, node: ClassDef):
        parent = None
        if node.parent is not None:
            parent_value = self.get_global(node.parent).value
            if not isinstance(parent_value, KoskriptClass):
                raise Errors.RuntimeError(f"'{node.parent}' is not a class")
            parent = parent_value

        klass = KoskriptClass(name=node.name, parent=parent)
        klass.closure = self._current_scope()

        for field in node.fields:
            info = FieldInfo(field.name, field.value, field.modifiers)

            if info.static:
                raise Errors.RuntimeError(
                    f"field '{field.name}' cannot be static (only methods can be static)")

            if info.name in klass.fields or info.name in klass.methods:
                raise Errors.RuntimeError(
                    f"'{info.name}' is already defined in class '{node.name}'")

            if parent is not None and (
                    parent.find_field(info.name) is not None
                    or parent.find_method(info.name) is not None):
                raise Errors.RuntimeError(
                    f"field '{info.name}' shadows an inherited member of '{parent.name}'")

            info.defining_class = klass
            klass.fields[info.name] = info

        for method in node.methods:
            info = MethodInfo(
                method.name, method.params, method.body,
                method.modifiers, is_constructor=False
            )

            if info.name in klass.methods or info.name in klass.fields:
                raise Errors.RuntimeError(
                    f"'{info.name}' is already defined in class '{node.name}'")

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
            klass.methods[info.name] = info

        if len(node.constructors) > 1:
            raise Errors.RuntimeError(
                f"class '{node.name}' defines more than one constructor")

        if node.constructors:
            method = node.constructors[0]
            constructor = MethodInfo(
                method.name, method.params, method.body,
                method.modifiers, is_constructor=True
            )

            if constructor.static:
                raise Errors.RuntimeError("a constructor cannot be static")

            constructor.defining_class = klass
            constructor.closure = klass.closure
            klass.constructor = constructor

        self.set_global(node.name, KoskriptObject(value=klass))


    def _decl(self, node: DeclStmt):
        variable = self.get_global(node.name)

        if not variable:
            raise Errors.NameError(f"{node.name} is not declared.")

        variable.set_value(self.expr_eval(node.value))

    def _fn_def(self, node: FnDef):
        self.set_global(
            name=node.name,
            value=KoskriptObject(
                value=Function(
                params=node.params,
                body=node.body,
                closure=self._current_scope(),
                frame=self._current_frame()
            ))
        )

    def _fn_call(self, node: FnCall):
        #print(node)
        return self.fn_eval(node.name, args=node.args)

    def _return_stmt(self, node: ReturnStmt):
        value = self.expr_eval(node.value) if node.value is not None else None
        raise ReturnSignal(value)

    def _while_stmt(self, node: WhileStmt):
        while self.cond_eval(node.condition):
            try:
                self.execute_block(node.body)
            except ContinueSignal:
                continue
            except BreakSignal:
                break

    def _for_stmt(self, node: ForStmt):
        array_value = self.expr_eval(node.iterable)

        if type(array_value) != list and type(array_value) != dict \
                and not hasattr(array_value, "__iter__"):
            raise Errors.MismatchType(f"for statement only supports maps, arrays or iterable objects.")

        self._push_scope(f"for", self._current_scope())
        try:
            var = KoskriptObject(None)
            var.read_only = True
            self.set_global(node.var, var)

            variable = self.get_global(node.var)
            for value in array_value:
                variable.value = value
                try:
                    self.execute_block(node.body)
                except ContinueSignal:
                    continue
                except BreakSignal:
                    break
        finally:
            self.scopes.pop()
        
    def _foritem_stmt(self, node: ForItemStmt):
        map_value = self.expr_eval(node.iterable)

        if type(map_value) != dict and not hasattr(map_value, "items"):
            raise Errors.MismatchType(f"foreach statement only supports maps.")

        self._push_scope(f"foreach", self._current_scope())
        try:
            keyvalue = KoskriptObject(None)
            varvalue = KoskriptObject(None)

            keyvalue.read_only = True
            varvalue.read_only = True

            self.set_global(node.key, keyvalue)
            self.set_global(node.var, varvalue)

            kval = self.get_global(node.key)
            vval = self.get_global(node.var)
            for key, value in map_value.items():
                kval.value = key
                vval.value = value
                try:
                    self.execute_block(node.body)
                except ContinueSignal:
                    continue
                except BreakSignal:
                    break
        finally:
            self.scopes.pop()

    def _break_stmt(self, node: BreakStmt):
        raise BreakSignal()

    def _continue_stmt(self, node: ContinueStmt):
        raise ContinueSignal()
    
    def _if_stmt(self, node: IfStmt):
        condition = self.cond_eval(node.condition)

        if condition:
            self.execute_block(node.body)
            return   

        for obj in node.if_tree:
            if type(obj) == ElseIfStmt:
                res = self._else_if_stmt(obj)
                if res:
                    break
            else:
                self._else_stmt(obj)
                break

    def _else_if_stmt(self, node: ElseIfStmt):
        condition = self.cond_eval(node.condition)
        
        if not condition:
            return False
    
        self.execute_block(node.body)
        return True
    
    def _else_stmt(self, node: ElseStmt):
        self.execute_block(node.body)