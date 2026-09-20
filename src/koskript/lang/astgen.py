from lark import Transformer
from .emtypes import *

_ESCAPES = {
    "n": "\n",
    "t": "\t",
    "r": "\r",
    "0": "\0",
    "\\": "\\",
    '"': '"',
    "'": "'",
}


def _unescape(raw: str) -> str:
    out = []
    i = 0
    while i < len(raw):
        ch = raw[i]
        if ch == "\\" and i + 1 < len(raw):
            nxt = raw[i + 1]
            out.append(_ESCAPES.get(nxt, nxt))
            i += 2
        else:
            out.append(ch)
            i += 1
    return "".join(out)


class KoskriptTransformer(Transformer):
    def start(self, tree): return (tree)

    def NUMBER(self, token):
        text = str(token)
        if "." in text:
            return FloatLit(value=float(text))
        return IntLit(value=int(text))

    def NAME(self, token): return NameRef(name=str(token))
    def STRING(self, token): return StrLit(value=_unescape(str(token)[1:-1]))
    def bool_true(self, tree): return BoolLit(value=True)
    def bool_false(self, tree): return BoolLit(value=False)
    def null_lit(self, tree): return NullLit(value=None)

    def this_ref(self, tree): return ThisRef()

    def new_expr(self, tree):
        name = tree[0]
        args = tree[1] if len(tree) > 1 else []
        return NewExpr(class_name=name.name, args=args)

    def method_call(self, tree):
        name = tree[0]
        args = tree[1] if len(tree) > 1 else []
        return MethodCall(name=name.name, args=args)

    def super_call(self, tree):
        name = tree[0]
        args = tree[1] if len(tree) > 1 else []
        return SuperCall(name=name.name, args=args)

    def super_constructor_call(self, tree):
        args = tree[0] if tree else []
        return SuperCall(name="constructor", args=args)

    def static_ref(self, tree):
        return StaticRef(name=tree[0].name)

    def lambda_fn(self, tree):
        return LambdaFnDef(params=[], body=tree[0])

    def lambda_fn_args(self, tree):
        params = [obj.name for obj in tree[:-1]]
        body = tree[-1]
        return LambdaFnDef(params=params, body=body)

    def array(self, tree): return ArrayLit(value=tree)
    def map(self, tree): return MapLit(value=tree)
    def map_obj(self, tree): return MapValue(key=tree[0], value=tree[1])

    def arg_list(self, tree): return tree

    def add_stmt(self, tree):
        left, right = tree
        return AddStmt(left=left, right=right)
    
    def sub_stmt(self, tree):
        left, right = tree
        return SubStmt(left=left, right=right)
    
    def mul_stmt(self, tree):
        left, right = tree
        return MulStmt(left=left, right=right)
    
    def div_stmt(self, tree):
        left, right = tree
        return DivStmt(left=left, right=right)

    def mod_stmt(self, tree):
        left, right = tree
        return ModStmt(left=left, right=right)

    def neg_stmt(self, tree):
        return NegStmt(value=tree[0])

    def param_list(self, tree):
        return [obj.name for obj in tree]
    
    def block(self, tree):
        return tree
    
    # conditions and comparisons
    def and_cond(self, tree):
        left, right = tree
        return AndCond(left=left, right=right)
    
    def not_cond(self, tree):
        return NotCond(tree)
    
    def or_cond(self, tree):
        left, right = tree
        return OrCond(left=left, right=right)


    def equ(self, tree):
        left, right = tree
        return EquComp(left=left, right=right)
    def nequ(self, tree):
        left, right = tree
        return NequComp(left=left, right=right)
    def gte(self, tree):
        left, right = tree
        return GteComp(left=left, right=right)
    def lte(self, tree):
        left, right = tree
        return LteComp(left=left, right=right)
    def lt(self, tree):
        left, right = tree
        return LtComp(left=left, right=right)
    def gt(self, tree):
        left, right = tree
        return GtComp(left=left, right=right)
    
    def member_access(self, tree):
        value, attr = tree
        return MemberAccess(name=value, attrs=[attr])

    def index_access(self, tree):
        value, index = tree
        return IndexAccess(value=value, index=index)

    def if_stmt(self, tree):
        condition = tree[0]
        block = tree[1]
        anexed_ifs = tree[2:]

        return IfStmt(
            condition=condition,
            body=block,
            if_tree=anexed_ifs
        )
    
    def elseif_stmt(self, tree):
        condition, block = tree
        return ElseIfStmt(
            condition=condition,
            body=block
        )

    def elsestmt(self, tree):
        return ElseStmt(
            body=tree[0]
        )

    # declarations
    def local_decl(self, tree):
        name, expr = tree

        return LocalDecl(
            name=name.name, 
            value=expr
        )

    def decl(self, tree):
        name, expr = tree
        return DeclStmt(
            name=name.name, value=expr
        )

    def fn_def(self, tree):
        name, params, block = tree
        return FnDef(
            name=name.name,
            params=params,
            body=block
        )
    
    def fn_def_nargs(self, tree):
        name, block = tree
        return FnDef(
            name=name.name,
            params=[],
            body=block
        )

    def const_decl(self, tree):
        name, expr = tree
        return ConstDecl(name=name.name, value=expr)

    # modifiers
    def mod_static(self, tree): return "static"
    def mod_public(self, tree): return "public"
    def mod_private(self, tree): return "private"

    @staticmethod
    def _split_modifiers(tree):
        modifiers, rest = [], []
        for item in tree:
            (modifiers if isinstance(item, str) else rest).append(item)
        return modifiers, rest

    # classes
    def class_body(self, tree):
        return list(tree)

    def class_def_simple(self, tree):
        name = tree[0]
        body = tree[1] if len(tree) > 1 else []
        return self._build_class(name.name, None, body)

    def class_def_extends(self, tree):
        name, parent = tree[0], tree[1]
        body = tree[2] if len(tree) > 2 else []
        return self._build_class(name.name, parent.name, body)

    @staticmethod
    def _build_class(name, parent, members):
        fields, methods, constructors = [], [], []
        for member in members:
            if isinstance(member, ClassField):
                fields.append(member)
            elif isinstance(member, ClassMethod):
                if member.is_constructor:
                    constructors.append(member)
                else:
                    methods.append(member)
        return ClassDef(
            name=name,
            parent=parent,
            fields=fields,
            methods=methods,
            constructors=constructors
        )

    def field_decl(self, tree):
        modifiers, rest = self._split_modifiers(tree)
        name, value = rest
        return ClassField(name=name.name, value=value, modifiers=modifiers)

    def method_def_args(self, tree):
        modifiers, rest = self._split_modifiers(tree)
        name, params, block = rest
        return ClassMethod(
            name=name.name, params=params, body=block,
            modifiers=modifiers, is_constructor=False
        )

    def method_def_nargs(self, tree):
        modifiers, rest = self._split_modifiers(tree)
        name, block = rest
        return ClassMethod(
            name=name.name, params=[], body=block,
            modifiers=modifiers, is_constructor=False
        )

    def constructor_def_args(self, tree):
        modifiers, rest = self._split_modifiers(tree)
        params, block = rest
        return ClassMethod(
            name="constructor", params=params, body=block,
            modifiers=modifiers, is_constructor=True
        )

    def constructor_def_nargs(self, tree):
        modifiers, rest = self._split_modifiers(tree)
        block = rest[0]
        return ClassMethod(
            name="constructor", params=[], body=block,
            modifiers=modifiers, is_constructor=True
        )

    def member_assign(self, tree):
        target, attr, value = tree
        return MemberAssign(target=target, attr=attr.name, value=value)

    def bound_method_call(self, tree):
        target, name = tree[0], tree[1]
        args = tree[2] if len(tree) > 2 else []
        return BoundMethodCall(target=target, name=name.name, args=args)

    # flow
    def return_value(self, tree):
        if len(tree) >= 1:
            return ReturnStmt(value=tree[0])
        return ReturnStmt(value=None)

    def return_void(self, tree):
        return ReturnStmt(value=None)
    
    def while_stmt(self, tree):
        condition, block = tree
        return WhileStmt(condition=condition, body=block)
    
    def break_stmt(self, tree):
        return BreakStmt()

    def continue_stmt(self, tree):
        return ContinueStmt()
    
    def for_stmt(self, tree):
        varname, iterable, block = tree
        return ForStmt(var=varname.name, iterable=iterable, body=block)
    
    def foritem_stmt(self, tree):
        key, value, iterable, block = tree
        return ForItemStmt(key=key.name, var=value.name, iterable=iterable, body=block)
    
    # Otros
    def fn_call(self, tree):
        name = tree[0]
        args = tree[1] if len(tree) > 1 else []
        return FnCall(name=name, args=args)
