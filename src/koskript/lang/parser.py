"""Recursive descent parser for Koskript.

:func:`parse` turns source code into the list of statements described by the
AST nodes of :mod:`.emtypes`, which is what the compiler consumes.

The grammar implemented here is the one written in ``grammar.lark``: same
statements, same expressions and same precedence. The rules that a
context free parser cannot express directly are resolved the same way the LALR
table used to resolve them:

* a parenthesized expression followed by ``{`` is a lambda, otherwise it is a
  grouping,
* a statement that starts with an expression is a declaration when the
  expression is a plain name followed by ``=``, a member assignment when it is
  a single member access, and a plain expression statement otherwise,
* ``return`` without a value is the ``RETURN_VOID`` token (see
  :mod:`.lexer`), so ``return`` at the end of a line never swallows the next
  statement as its value,
* a postfix operator (``.``, ``::``, ``[``, ``(``) that starts a new line
  ends the statement instead of chaining, matching the ``_LINE_*`` terminals
  of the Lark grammar. A token carries that position in its ``line_start``
  flag (see :mod:`.lexer`).
"""

from .emtypes import *
from .errors import Errors
from .lexer import Lexer, ParseError, format_syntax_error

# Comparison operators are not chained: `a < b < c` is not valid.
_COMPARISONS = {
    "==": EquComp,
    "!=": NequComp,
    ">=": GteComp,
    "<=": LteComp,
    ">": GtComp,
    "<": LtComp,
}

_ARITHMETIC = {
    "+": AddStmt,
    "-": SubStmt,
}

_TERMS = {
    "*": MulStmt,
    "/": DivStmt,
    "%": ModStmt,
}

# Tokens that can start an expression, used by `return <expression>?`.
_EXPRESSION_START = frozenset((
    "INT", "FLOAT", "STRING", "BYTES", "NAME", "[", "{", "(", "-", ".",
    "true", "false", "null", "this", "new", "super", "::", "not",
))

# The postfix operators, the only tokens that extend an expression to the
# right. One of them at the beginning of a line ends the statement instead
# of chaining, like the `_LINE_*` terminals of the Lark grammar.
_CHAINED = frozenset((".", "::", "[", "("))

_NAMES = ("a name",)


def _qualified_name(node) -> str:
    """Display name of a simple or dotted reference node."""
    if type(node) is NameRef:
        return node.name
    if type(node) is MemberAccess:
        return _qualified_name(node.name) + "." + node.attrs[-1].name
    return str(node)


def _describe(token) -> str:
    """The `"Unexpected token 'x'"` part of an error message."""
    if token.type == "EOF":
        return "Unexpected end of input."
    return f"Unexpected token '{token.text}'."


def _display(kind) -> str:
    """How a token type is named in the `Expected one of` list."""
    if kind == "NAME":
        return "a name"
    if kind in ("INT", "FLOAT"):
        return "a number"
    if kind == "STRING":
        return "a string"
    if kind == "BYTES":
        return "a bytes literal"
    return f"'{kind}'"


class Parser(object):
    """Builds the AST of a token stream.

    Every ``parse_*`` method consumes the tokens of one grammar rule and
    returns the node of :mod:`.emtypes` it produces.
    """

    __slots__ = ("tokens", "pos")

    def __init__(self, code: str):
        self.tokens = Lexer(code).tokenize()
        self.pos = 0

    # TOKENS ###################################################################

    def _current(self):
        return self.tokens[self.pos]

    def _check(self, *kinds):
        return self.tokens[self.pos].type in kinds

    def _accept(self, kind):
        """Consume the current token when it matches, otherwise ignore it."""
        token = self.tokens[self.pos]
        if token.type == kind:
            self.pos += 1
            return token
        return None

    def _expect(self, kind, expected=()):
        """Consume the current token, which must be of type ``kind``."""
        token = self.tokens[self.pos]
        if token.type != kind:
            self._error(token, expected=expected or (_display(kind),))
        self.pos += 1
        return token

    def _error(self, token, message=None, expected=()):
        raise ParseError(token.offset, token.line, token.column,
                         message or _describe(token), expected)

    # PROGRAM ##################################################################

    def parse(self) -> list:
        """Every statement of the source, in order."""
        statements = []
        while not self._check("EOF"):
            statements.append(self.parse_statement())
        return statements

    def _statements(self, closing):
        statements = []
        while not self._check(closing, "EOF"):
            statements.append(self.parse_statement())
        return statements

    # STATEMENTS ###############################################################

    def parse_statement(self):
        kind = self._current().type

        if kind == "local" or kind == "const":
            return self.parse_declaration()
        if kind == "fn" or kind == "wrapper":
            return self.parse_function(implicit_return=kind == "wrapper")
        if kind == "@":
            return self.parse_decorated()
        if kind == "class":
            return self.parse_class()
        if kind == "namespace":
            return self.parse_namespace()
        if kind == "error":
            return self.parse_error_def()
        if kind == "import":
            return self.parse_import()
        if kind == "return" or kind == "RETURN_VOID":
            return self.parse_return()
        if kind == "if":
            return self.parse_if()
        if kind == "while":
            return self.parse_while()
        if kind == "for":
            return self.parse_for()
        if kind == "foreach":
            return self.parse_foreach()
        if kind == "break":
            self.pos += 1
            return BreakStmt()
        if kind == "continue":
            self.pos += 1
            return ContinueStmt()
        if kind == "throw":
            self.pos += 1
            return ThrowStmt(value=self.parse_expression())
        if kind == "try":
            return self.parse_try()

        return self.parse_expression_statement()

    def parse_declaration(self):
        """`local name = expr` and `const name = expr`."""
        keyword = self._current().type
        self.pos += 1
        name = self._expect("NAME", _NAMES).value
        self._expect("=", ("'='",))
        value = self.parse_expression()
        if keyword == "local":
            return LocalDecl(name=name, value=value)
        return ConstDecl(name=name, value=value)

    def parse_expression_statement(self):
        """An expression, a `name = value` declaration or `target.name = value`."""
        start = self.pos
        target = self.parse_expression()
        end = self.pos

        if not self._accept("="):
            return target

        value = self.parse_expression()
        # `name = value` is a declaration and `target.name = value` is a member
        # assignment. A parenthesized target is neither: `decl` starts with a
        # NAME token, so `(a) = 1` is a syntax error.
        if type(target) is NameRef and end == start + 1:
            return DeclStmt(name=target.name, value=value)
        if type(target) is MemberAccess and len(target.attrs) == 1:
            return MemberAssign(target=target.name,
                                attr=target.attrs[0].name, value=value)

        self._error(self.tokens[start],
                    "Only a name or a single member can be assigned.")

    def parse_return(self):
        token = self._current()
        self.pos += 1
        if token.type == "RETURN_VOID" \
                or self._current().type not in _EXPRESSION_START:
            return ReturnStmt(value=None)
        return ReturnStmt(value=self.parse_expression())

    def parse_block(self) -> list:
        self._expect("{", ("'{'",))
        statements = self._statements("}")
        self._expect("}", ("'}'",))
        return statements

    def parse_condition(self):
        """The `( expr )` of a loop or branch."""
        self._expect("(", ("'('",))
        condition = self.parse_expression()
        self._expect(")", ("')'",))
        return condition

    def parse_if(self):
        self.pos += 1
        condition = self.parse_condition()
        body = self.parse_block()

        branches = []
        while self._check("elseif"):
            self.pos += 1
            branch_condition = self.parse_condition()
            branches.append(
                ElseIfStmt(condition=branch_condition, body=self.parse_block()))
        if self._accept("else"):
            branches.append(ElseStmt(body=self.parse_block()))

        return IfStmt(condition=condition, body=body, if_tree=branches)

    def parse_while(self):
        self.pos += 1
        condition = self.parse_condition()
        return WhileStmt(condition=condition, body=self.parse_block())

    def parse_for(self):
        self.pos += 1
        self._expect("(", ("'('",))
        name = self._expect("NAME", _NAMES).value
        self._expect("in", ("'in'",))
        iterable = self.parse_expression()
        self._expect(")", ("')'",))
        return ForStmt(var=name, iterable=iterable, body=self.parse_block())

    def parse_foreach(self):
        self.pos += 1
        self._expect("(", ("'('",))
        key = self._expect("NAME", _NAMES).value
        self._expect(",", ("','",))
        name = self._expect("NAME", _NAMES).value
        self._expect("in", ("'in'",))
        iterable = self.parse_expression()
        self._expect(")", ("')'",))
        return ForItemStmt(key=key, var=name, iterable=iterable,
                           body=self.parse_block())

    def parse_try(self):
        self.pos += 1
        body = self.parse_block()

        catch_name = None
        catch_body = None
        finally_body = None
        if self._accept("catch"):
            catch_name = self._expect("NAME", _NAMES).value
            catch_body = self.parse_block()
        if self._accept("finally"):
            finally_body = self.parse_block()

        return TryStmt(body=body, catch_name=catch_name, catch_body=catch_body,
                       finally_body=finally_body)

    # FUNCTIONS ################################################################

    def parse_function(self, implicit_return=False, decorators=None):
        """`fn name(params) { }` and its `wrapper` counterpart."""
        self.pos += 1
        name = self._expect("NAME", _NAMES).value
        params = self.parse_parameters()
        body = self.parse_block()
        if decorators:
            return FnDef(name=name, params=params, body=body,
                         decorators=decorators, implicit_return=implicit_return)
        return FnDef(name=name, params=params, body=body,
                     implicit_return=implicit_return)

    def parse_parameters(self) -> list:
        self._expect("(", ("'('",))
        params = []
        if not self._check(")"):
            params.append(self._expect("NAME", _NAMES).value)
            while self._accept(","):
                params.append(self._expect("NAME", _NAMES).value)
        self._expect(")", ("',' or ')'",))
        return params

    def parse_decorated(self):
        """A `fn` or `wrapper` preceded by one or more decorators."""
        decorators = self.parse_decorators()
        if self._check("fn"):
            return self.parse_function(decorators=decorators)
        if self._check("wrapper"):
            return self.parse_function(implicit_return=True, decorators=decorators)
        self._error(self._current(),
                    "A decorator must be followed by 'fn' or 'wrapper'.",
                    ("'fn'", "'wrapper'"))

    def parse_decorators(self) -> list:
        decorators = []
        while self._accept("@"):
            decorators.append(self.parse_decorator())
        return decorators

    def parse_decorator(self):
        target = self.parse_dotted_name()
        if not self._accept("("):
            return target
        return FnCall(name=target, args=self.parse_arguments())

    def parse_error_def(self):
        self.pos += 1
        name = self._expect("NAME", _NAMES).value
        params = self.parse_parameters()
        return ErrorDef(name=name, params=params, body=self.parse_block())

    def parse_import(self):
        self.pos += 1
        path = self._expect("STRING", ("a module path",)).value
        name = self._expect("NAME", _NAMES).value if self._accept("as") else None
        return ImportStmt(path=path, name=name)

    # CLASSES ##################################################################

    def parse_namespace(self):
        self.pos += 1
        name = self._expect("NAME", _NAMES).value
        return NamespaceDef(name=name, body=self.parse_block())

    def parse_class(self):
        self.pos += 1
        name = self._expect("NAME", ("a class name",)).value

        parent = None
        parent_name = None
        if self._accept("extends"):
            parent = self.parse_dotted_name()
            parent_name = _qualified_name(parent)

        fields, methods, constructors = self.parse_class_body()
        return ClassDef(name=name, parent=parent, parent_name=parent_name,
                        fields=fields, methods=methods, constructors=constructors)

    def parse_class_body(self):
        self._expect("{", ("'{'",))
        fields, methods, constructors = [], [], []

        while not self._accept("}"):
            if self._check("@"):
                decorators = self.parse_decorators()
                methods.append(self.parse_method(self.parse_modifiers(), decorators))
                continue

            modifiers = self.parse_modifiers()
            if self._check("fn"):
                methods.append(self.parse_method(modifiers))
            elif self._check("constructor"):
                constructors.append(self.parse_constructor(modifiers))
            else:
                fields.append(self.parse_field(modifiers))

        return fields, methods, constructors

    def parse_modifiers(self) -> list:
        modifiers = []
        while self._check("static", "public", "private"):
            modifiers.append(self._current().type)
            self.pos += 1
        return modifiers

    def parse_field(self, modifiers):
        if not self._check("NAME"):
            self._error(self._current(),
                        "A class can only contain fields, methods and "
                        "constructors.", ("a name", "'fn'", "'constructor'"))
        name = self._current().value
        self.pos += 1
        self._expect("=", ("'='",))
        return ClassField(name=name, value=self.parse_expression(),
                          modifiers=modifiers)

    def parse_method(self, modifiers, decorators=None):
        self._expect("fn", ("'fn'",))
        name = self._expect("NAME", ("a method name",)).value
        params = self.parse_parameters()
        body = self.parse_block()
        if decorators:
            return ClassMethod(name=name, params=params, body=body,
                               modifiers=modifiers, is_constructor=False,
                               decorators=decorators)
        return ClassMethod(name=name, params=params, body=body,
                           modifiers=modifiers, is_constructor=False)

    def parse_constructor(self, modifiers):
        self.pos += 1
        params = self.parse_parameters()
        return ClassMethod(name="constructor", params=params,
                           body=self.parse_block(), modifiers=modifiers,
                           is_constructor=True)

    # EXPRESSIONS ##############################################################

    def parse_expression(self):
        return self.parse_or()

    def parse_or(self):
        node = self.parse_and()
        while self._check("or"):
            self.pos += 1
            node = OrCond(left=node, right=self.parse_and())
        return node

    def parse_and(self):
        node = self.parse_not()
        while self._check("and"):
            self.pos += 1
            node = AndCond(left=node, right=self.parse_not())
        return node

    def parse_not(self):
        if self._accept("not"):
            # The operand is wrapped in a list: `NotCond.comparison` mirrors
            # the children of the grammar rule, like every other node.
            return NotCond([self.parse_not()])
        return self.parse_comparison()

    def parse_comparison(self):
        left = self.parse_sum()
        node_type = _COMPARISONS.get(self._current().type)
        if node_type is None:
            return left
        self.pos += 1
        return node_type(left=left, right=self.parse_sum())

    def parse_sum(self):
        node = self.parse_term()
        while True:
            node_type = _ARITHMETIC.get(self._current().type)
            if node_type is None:
                return node
            self.pos += 1
            node = node_type(left=node, right=self.parse_term())

    def parse_term(self):
        node = self.parse_unary()
        while True:
            node_type = _TERMS.get(self._current().type)
            if node_type is None:
                return node
            self.pos += 1
            node = node_type(left=node, right=self.parse_unary())

    def parse_unary(self):
        if self._accept("-"):
            return NegStmt(value=self.parse_unary())
        return self.parse_postfix()

    def parse_postfix(self):
        node = self.parse_atom()
        while True:
            token = self._current()
            kind = token.type

            # A postfix operator that starts a new line ends the statement
            # instead of chaining: `foo()\n(1)` is two statements, not the
            # call `foo()(1)`.
            if kind in _CHAINED and token.line_start:
                return node

            if kind == ".":
                self.pos += 1
                node = MemberAccess(name=node, attrs=[NameRef(self._member_name())])
            elif kind == "[":
                self.pos += 1
                index = self.parse_expression()
                self._expect("]", ("']'",))
                node = IndexAccess(value=node, index=index)
            elif kind == "(":
                self.pos += 1
                node = FnCall(name=node, args=self.parse_arguments())
            elif kind == "::":
                self.pos += 1
                name = self._member_name()
                self._expect("(", ("'('",))
                node = BoundMethodCall(target=node, name=name,
                                       args=self.parse_arguments())
            else:
                return node

    def parse_atom(self):
        token = self._current()
        kind = token.type

        if kind == "INT":
            self.pos += 1
            return IntLit(value=token.value)
        if kind == "FLOAT":
            self.pos += 1
            return FloatLit(value=token.value)
        if kind == "STRING":
            self.pos += 1
            return StrLit(value=token.value)
        if kind == "BYTES":
            self.pos += 1
            return BytesLit(value=token.value)
        if kind == "NAME":
            self.pos += 1
            return NameRef(name=token.value)
        if kind == "[":
            return self.parse_array()
        if kind == "{":
            return self.parse_map()
        if kind == "(":
            return self.parse_group()
        if kind == "true" or kind == "false":
            self.pos += 1
            return BoolLit(value=kind == "true")
        if kind == "null":
            self.pos += 1
            return NullLit(value=None)
        if kind == "this":
            self.pos += 1
            return ThisRef()
        if kind == "new":
            return self.parse_new()
        if kind == "::":
            return self.parse_method_call()
        if kind == "super":
            return self.parse_super_call()
        if kind == ".":
            self.pos += 1
            return StaticRef(name=self._member_name())

        self._error(token, expected=(
            "a literal", "a name", "an array", "a map", "a lambda",
            "a function call", "'new'", "'this'", "'null'", "'::'",
        ))

    def parse_array(self):
        self.pos += 1
        items = []
        if not self._check("]"):
            items.append(self.parse_expression())
            while self._accept(","):
                if self._check("]"):
                    break
                items.append(self.parse_expression())
        self._expect("]", ("',' or ']'",))
        return ArrayLit(value=items)

    def parse_map(self):
        self.pos += 1
        entries = []
        if not self._check("}"):
            entries.append(self.parse_map_entry())
            while self._accept(","):
                if self._check("}"):
                    break
                entries.append(self.parse_map_entry())
        self._expect("}", ("',' or '}'",))
        return MapLit(value=entries)

    def parse_map_entry(self):
        key = self.parse_expression()
        self._expect(":", ("':'",))
        return MapValue(key=key, value=self.parse_expression())

    def parse_group(self):
        """`(...)` is a lambda when it is followed by a block, else a grouping."""
        self.pos += 1
        if self._accept(")"):
            return LambdaFnDef(params=[], body=self.parse_block())

        items = [self.parse_expression()]
        while self._accept(","):
            items.append(self.parse_expression())
        self._expect(")", ("',' or ')'",))

        if self._check("{"):
            params = []
            for item in items:
                if type(item) is not NameRef:
                    self._error(self._current(),
                                "Lambda parameters must be plain names.",
                                _NAMES)
                params.append(item.name)
            return LambdaFnDef(params=params, body=self.parse_block())
        if len(items) > 1:
            self._error(self._current(),
                        "A parenthesized expression can only hold one value.",
                        ("'{'",))
        return items[0]

    def parse_new(self):
        self.pos += 1
        target = self.parse_dotted_name()
        self._expect("(", ("'('",))
        return NewExpr(target=target, args=self.parse_arguments(),
                       label=_qualified_name(target))

    def parse_method_call(self):
        """`::name(args)`: calls an instance method with the current `this`."""
        self.pos += 1
        name = self._member_name()
        self._expect("(", ("'('",))
        return MethodCall(name=name, args=self.parse_arguments())

    def parse_super_call(self):
        """`super::name(args)` and `super::constructor(args)`."""
        self.pos += 1
        self._expect("::", ("'::'",))
        if self._accept("constructor"):
            name = "constructor"
        else:
            name = self._member_name()
        self._expect("(", ("'('",))
        return SuperCall(name=name, args=self.parse_arguments())

    def parse_dotted_name(self):
        """`Name` or `Name.Member.Other` as a reference node."""
        node = NameRef(name=self._expect("NAME", _NAMES).value)
        while self._accept("."):
            node = MemberAccess(name=node, attrs=[NameRef(self._member_name())])
        return node

    def _member_name(self) -> str:
        return self._expect("NAME", ("a member name",)).value

    def parse_arguments(self) -> list:
        """The arguments of a call, with the opening `(` already consumed."""
        args = []
        if not self._check(")"):
            args.append(self.parse_expression())
            while self._accept(","):
                args.append(self.parse_expression())
        self._expect(")", ("',' or ')'",))
        return args


def parse(code: str) -> list:
    """Parse ``code`` into a list of statements.

    Raises ``Errors.SyntaxError`` with the offending line, column and context
    when the source cannot be parsed.
    """
    try:
        return Parser(code).parse()
    except ParseError as error:
        raise Errors.SyntaxError(format_syntax_error(code, error)) from None
    except RecursionError:
        raise Errors.SyntaxError(
            "Syntax error: the source is nested too deeply to parse.") from None
