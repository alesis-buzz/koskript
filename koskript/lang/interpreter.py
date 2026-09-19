from .emtypes import *

class KoskripInterpreter(object):
    def __init__(self):
        self.globals = {"_": {}}
        self.scopes = []
        self._scope_counter = 0
        self._handlers = {
            LocalDecl:   self._local_decl,
            DeclStmt: self._decl,
            FnDef:       self._fn_def,
            FnCall:      self._fn_call,
            ReturnStmt:  self._return_stmt,
            WhileStmt:   self._while_stmt,
            ForStmt:     self._for_stmt,
            ForItemStmt: self._foritem_stmt,
            IfStmt: self._if_stmt,
            ElseIfStmt: self._else_if_stmt,
            ElseStmt: self._else_stmt
        }
    
    def execute(self, ast: list):
        for node in ast:
            self.visit(node)

    def run(self, ast: list):
        # Entry point: a top-level `return` simply stops execution.
        try:
            self.execute(ast)
        except ReturnSignal:
            pass

    def _push_scope(self, prefix: str) -> str:
        self._scope_counter += 1
        scope = f"{prefix}_{self._scope_counter}"
        self.scopes.append(scope)
        return scope

    def get_global(self, name: str) -> KoskriptObject:
        for scope in reversed(self.scopes):
            if scope in self.globals and name in self.globals[scope]:
                return self.globals[scope][name]
        
        if name in self.globals["_"]:
            return self.globals["_"][name]
        
        raise NameError(f"'{name}' is not defined")

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
            case StrLit(value):  return value
            case BoolLit(value): return value
            case NameRef(name):  return self.get_global(name).value
            case AddStmt(l, r):  return self.expr_eval(l) + self.expr_eval(r)
            case SubStmt(l, r):  return self.expr_eval(l) - self.expr_eval(r)
            case MulStmt(l, r):  return self.expr_eval(l) * self.expr_eval(r)
            case DivStmt(l, r):  return self.expr_eval(l) / self.expr_eval(r)
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

                if not isinstance(value, dict):
                    raise Errors.MismatchType(f"member access only supported on map, got {value}")
                
                for attr in attrs:
                    try:
                        value = value[attr.name]
                    except:
                        raise Errors.RuntimeError(f"no member with the value {attr} is defined on {value}")

                return value
                
            case FnCall(n, arg): return self.fn_eval(n, arg)
            case LambdaFnDef(p, body): return Function(params=p, body=body)
            case EquComp() | NequComp() | LteComp() | GteComp() | GtComp() | LtComp() \
               | AndCond() | OrCond() | NotCond():
                return self.cond_eval(expr)
            case _: raise RuntimeError(f"Unknown expr: {type(expr).__name__}")

    def fn_eval(self, name, args):
        if type(name) != MemberAccess:
            func: KoskriptObject = self.get_global(name.name)
        else:
            func = self.expr_eval(name)
            if not isinstance(func, KoskriptObject):
                func = KoskriptObject(value=func)

        if not func:
            raise NameError(f"no define with the name {name} exists.")
        
        if callable(func.value):
            return func.value(*[self.expr_eval(arg) for arg in args])

        if type(func.value) != Function:
            raise ValueError(f"{name} is not callable.")
        
        func_params = func.value.params
        func_body = func.value.body
        if type(func_body) != list: func_body = [func_body]

        self._push_scope(f"func_{name}")
        try:
            for index_param, param in enumerate(func_params):
                try:
                    self.set_global(
                        name=param, 
                        value=KoskriptObject(
                            self.expr_eval(args[index_param]), 
                            read_only=True)
                    )
                except IndexError:
                    break
            
            self.execute(func_body)
        except ReturnSignal as signal:
            return signal.value
        finally:
            self.scopes.pop()
        return None


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


    def _decl(self, node: DeclStmt):
        variable = self.get_global(node.name)

        if not variable:
            raise NameError(f"{node.name} is not declared.")

        variable.set_value(self.expr_eval(node.value))

    def _fn_def(self, node: FnDef):
        self.set_global(
            name=node.name,
            value=KoskriptObject(
                value=Function(
                params=node.params,
                body=node.body
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
            self.execute(node.body)

    def _for_stmt(self, node: ForStmt):
        array_value = self.expr_eval(node.iterable)

        if type(array_value) != list and type(array_value) != dict:
            raise NameError(f"for statement only supports maps or arrays.")

        self._push_scope(f"for")
        var = KoskriptObject(None)
        var.read_only = True
        self.set_global(node.var, var)

        variable = self.get_global(node.var)
        for value in array_value:
            variable.value = value
            self.execute(node.body)
        
        self.scopes.pop()
        
    def _foritem_stmt(self, node: ForItemStmt):
        map_value = self.expr_eval(node.iterable)

        if type(map_value) != dict:
            raise ValueError(f"foreach statement only supports maps.")

        self._push_scope(f"foreach")
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
            self.execute(node.body)
        
        self.scopes.pop()
    
    def _if_stmt(self, node: IfStmt):
        condition = self.cond_eval(node.condition)

        if condition:
            self.execute(node.body)
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
    
        self.execute(node.body)
        return True
    
    def _else_stmt(self, node: ElseStmt):
        self.execute(node.body)