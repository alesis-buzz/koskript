"""Grammar conformance tests for the Koskript parser.

Every production written in ``grammar.lark`` gets an entry in
:data:`NODE_CASES`, :data:`LIST_CASES` or :data:`TERMINALS`, and the suite
fails if the grammar grows a production that no test covers, so the parser
cannot silently drift away from the specification.

Run them from the repository root with::

    PYTHONPATH=src python -m unittest discover -s tests
"""

import pathlib
import re
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from koskript.lang import emtypes
from koskript.lang.errors import Errors
from koskript.lang.lexer import Lexer
from koskript.lang.parser import parse

GRAMMAR = pathlib.Path(__file__).resolve().parent.parent \
    / "src" / "koskript" / "grammar.lark"

# ── the grammar, read from the file ──────────────────────────────────────

RULE_RE = re.compile(r"^(\??)([a-zA-Z_][a-zA-Z_0-9]*)(\.[0-9]+)?\s*:", re.M)
ALIAS_RE = re.compile(r"->\s*([a-zA-Z_][a-zA-Z_0-9]*)")


def productions():
    """Every production of the grammar: rules plus ``-> alias`` names."""
    text = GRAMMAR.read_text()
    rules = [match[1] for match in RULE_RE.findall(text)]
    aliases = ALIAS_RE.findall(text)
    return tuple(rules + [alias for alias in aliases if alias not in rules])


def node_names(value):
    """Every AST node type reachable from ``value``."""
    names = set()
    stack = [value]
    while stack:
        item = stack.pop()
        kind = type(item)
        if kind is list:
            stack.extend(item)
        elif isinstance(item, tuple):
            if hasattr(item, "_fields"):
                names.add(kind.__name__)
            stack.extend(item)
    return names


TERMINAL_RE = re.compile(r"^([A-Z_][A-Z_0-9]*)(\.[0-9]+)?\s*:\s*/(.+)/$", re.M)


def terminal_patterns():
    """The regex of every terminal of the grammar, read from the file."""
    return {name: pattern
            for name, _priority, pattern in TERMINAL_RE.findall(
                GRAMMAR.read_text())}


# ── one snippet per production ───────────────────────────────────────────

# production -> (source, node type the production must build)
NODE_CASES = {
    # literals
    "bool_true": ('local a = true', "BoolLit"),
    "bool_false": ('local a = false', "BoolLit"),
    "null_lit": ('local a = null', "NullLit"),
    "this_ref": ('local a = this.x', "ThisRef"),

    # collections
    "array": ('local a = [1, 2, 3]', "ArrayLit"),
    "map": ('local a = {1: 2}', "MapLit"),
    "map_obj": ('local a = {1: 2}', "MapValue"),

    # operators
    "or_cond": ('local a = b or c', "OrCond"),
    "and_cond": ('local a = b and c', "AndCond"),
    "not_cond": ('local a = not b', "NotCond"),
    "equ": ('local a = b == c', "EquComp"),
    "nequ": ('local a = b != c', "NequComp"),
    "gte": ('local a = b >= c', "GteComp"),
    "lte": ('local a = b <= c', "LteComp"),
    "gt": ('local a = b > c', "GtComp"),
    "lt": ('local a = b < c', "LtComp"),
    "add_stmt": ('local a = b + c', "AddStmt"),
    "sub_stmt": ('local a = b - c', "SubStmt"),
    "mul_stmt": ('local a = b * c', "MulStmt"),
    "div_stmt": ('local a = b / c', "DivStmt"),
    "mod_stmt": ('local a = b % c', "ModStmt"),
    "neg_stmt": ('local a = -b', "NegStmt"),

    # postfix
    "member_access": ('local a = b.c', "MemberAccess"),
    "index_access": ('local a = b[0]', "IndexAccess"),
    "fn_call": ('local a = b(1)', "FnCall"),
    "bound_method_call": ('local a = b::c()', "BoundMethodCall"),
    "method_call": ('local a = ::c()', "MethodCall"),
    "super_call": ('local a = super::c()', "SuperCall"),
    "super_constructor_call": ('local a = super::constructor()', "SuperCall"),
    "static_ref": ('local a = .c()', "StaticRef"),
    "new_expr": ('local a = new B()', "NewExpr"),
    "dotted_name": ('local a = new B.C()', "MemberAccess"),
    "dotted_name": ('class A extends B.C { }', "MemberAccess"),

    # lambdas
    "lambda_fn": ('local a = () { }', "LambdaFnDef"),
    "lambda_fn_args": ('local a = (x) { }', "LambdaFnDef"),
    "lambda_fn_args": ('local a = (x, y) { }', "LambdaFnDef"),

    # declarations
    "local_decl": ('local a = 1', "LocalDecl"),
    "const_decl": ('const a = 1', "ConstDecl"),
    "decl": ('a = 1', "DeclStmt"),
    "member_assign": ('a.b = 1', "MemberAssign"),
    "import_plain": ('import "m"', "ImportStmt"),
    "import_as": ('import "m" as n', "ImportStmt"),
    "namespace_def": ('namespace N { }', "NamespaceDef"),

    # control flow
    "if_stmt": ('if (a) { }', "IfStmt"),
    "elseif_stmt": ('if (a) { } elseif (b) { }', "ElseIfStmt"),
    "elsestmt": ('if (a) { } else { }', "ElseStmt"),
    "while_stmt": ('while (a) { }', "WhileStmt"),
    "for_stmt": ('for (i in items) { }', "ForStmt"),
    "foritem_stmt": ('foreach (k, v in items) { }', "ForItemStmt"),
    "break_stmt": ('while (a) { break }', "BreakStmt"),
    "continue_stmt": ('while (a) { continue }', "ContinueStmt"),

    # errors
    "error_def": ('error E (err) { }', "ErrorDef"),
    "error_def_nargs": ('error E () { }', "ErrorDef"),
    "throw_stmt": ('throw E()', "ThrowStmt"),
    "try_stmt": ('try { }', "TryStmt"),
    "catch_clause": ('try { } catch e { }', "TryStmt"),
    "finally_clause": ('try { } finally { }', "TryStmt"),

    # functions
    "fn_def": ('fn f(a) { }', "FnDef"),
    "fn_def_nargs": ('fn f() { }', "FnDef"),
    "wrapper_def": ('wrapper w(a) { }', "FnDef"),
    "wrapper_def_nargs": ('wrapper w() { }', "FnDef"),
    "return_value": ('fn f() { return 1 }', "ReturnStmt"),
    "return_void": ('fn f() { return\n}', "ReturnStmt"),

    # decorators
    "decorator_plain": ('@d\nfn f() { }', "FnDef"),
    "decorator_call": ('@d(1)\nfn f() { }', "FnDef"),
    "decorated_fn": ('@d\nfn f() { }', "FnDef"),
    "decorated_wrapper": ('@d\nwrapper w() { }', "FnDef"),

    # classes
    "class_def_simple": ('class A { }', "ClassDef"),
    "class_def_extends": ('class A extends B { }', "ClassDef"),
    "class_def_extends": ('class A extends B.C { }', "ClassDef"),
    "class_body": ('class A { public x = 1 }', "ClassDef"),
    "field_decl": ('class A { x = 1 }', "ClassField"),
    "field_decl": ('class A { public x = 1 }', "ClassField"),
    "method_def_args": ('class A { fn m(a) { } }', "ClassMethod"),
    "method_def_nargs": ('class A { fn m() { } }', "ClassMethod"),
    "constructor_def_args": ('class A { constructor(a) { } }', "ClassMethod"),
    "constructor_def_nargs": ('class A { constructor() { } }', "ClassMethod"),
    "decorated_method": ('class A { @d\n fn m() { } }', "ClassMethod"),
}

# productions that build a list of nodes instead of a single one
LIST_CASES = {
    "start": "local a = 1",
    "statement": "local a = 1",
    "expr_stmt": "f()",
    "expr": "1",
    "atom": "1",
    "postfix": "a.b",
    "block": "fn f() { local a = 1 }",
    "class_member": "class A { x = 1 }",
    "param_list": "fn f(a, b) { }",
    "arg_list": "f(1, 2)",
    "modifier": "class A { static fn m() { } }",
    "or_expr": "a or b",
    "and_expr": "a and b",
    "not_expr": "not a",
    "comparison": "a == b",
    "sum": "a + b",
    "term": "a * b",
    "unary": "-a",
    "decorator": "@d\nfn f() { }",
    "class_def": "class A { }",
    "fn_def": "fn f() { }",
    "wrapper_def": "wrapper w() { }",
    "method_def": "class A { fn m() { } }",
    "constructor_def": "class A { constructor() { } }",
    "return_stmt": "fn f() { return }",
    "if_stmt": "if (a) { }",
    "import_stmt": 'import "m"',
    "bool": "local a = true",
    "lambda_fn": "local a = () { }",
    "map": "local a = {1: 2}",
    "array": "local a = [1]",
    "error_def": "error E (e) { }",
    "try_stmt": "try { }",
    "while_stmt": "while (a) { }",
    "for_stmt": "for (i in x) { }",
    "foritem_stmt": "foreach (k, v in x) { }",
    "local_decl": "local a = 1",
    "const_decl": "const a = 1",
    "decl": "a = 1",
    "member_assign": "a.b = 1",
    "namespace_def": "namespace N { }",
    "throw_stmt": "throw E()",
    "field_decl": "class A { x = 1 }",
    "decorated_fn": "@d\nfn f() { }",
    "decorated_wrapper": "@d\nwrapper w() { }",
    "decorated_method": "class A { @d\n fn m() { } }",
    "class_def_simple": "class A { }",
    "class_def_extends": "class A extends B { }",
}

# terminals are produced by the scanner, not by the parser
TERMINALS = {
    "NAME": "local a = 1",
    "NUMBER": "local a = 1",
    "STRING": 'local a = "s"',
    "BYTES": 'local a = b"s"',
    "COMMENT": "// a comment\nlocal a = 1",
    "RETURN_VOID": "fn f() { return\n}",
}

# the scanner names numeric tokens after their type, not after the terminal
TOKEN_TYPES = {"NUMBER": ("INT", "FLOAT")}

# productions that build the string modifiers of a class member
MODIFIER_CASES = {
    "mod_static": ('class A { static fn m() { } }', "static"),
    "mod_public": ('class A { public fn m() { } }', "public"),
    "mod_private": ('class A { private x = 1 }', "private"),
}

# ── sources the grammar rejects ───────────────────────────────────────────

REJECTED = [
    # literals
    ("array: unclosed", "[1, 2"),
    ("array: unclosed empty", "["),
    ("array: missing comma", "[1 2]"),
    ("array: double comma", "[1,,2]"),
    ("map: unclosed", "{1: 2"),
    ("map: unclosed empty", "{"),
    ("map: missing value", "{1: }"),
    ("map: missing key", "{: 2}"),
    ("map: missing colon", "{1 2}"),
    ("number: trailing dot", "1."),
    ("string: unterminated", '"abc'),
    ("string: unterminated escape", '"abc\\'),
    ("bytes: unterminated", 'b"abc'),
    ("bytes: invalid escape", 'b"\\xzz"'),
    ("char: not in the language", "local a = 1 $ 2"),
    ("char: unicode digits", "local a = ٣"),
    ("comment: block comments do not exist", "/* hi */ local a = 1"),

    # reserved words
    ("NAME: reserved as declaration", "local if = 1"),
    ("NAME: reserved as member", "obj.if"),
    ("NAME: reserved in", "local in = 1"),
    ("NAME: reserved constructor", "local constructor = 1"),
    ("NAME: reserved after dot", "a.super"),
    ("NAME: cannot start with a digit", "local 1a = 1"),

    # declarations
    ("local_decl: no name", "local = 1"),
    ("local_decl: no value", "local a"),
    ("local_decl: no equals", "local a 1"),
    ("const_decl: no name", "const = 1"),
    ("decl: no name", "= 1"),
    ("member_assign: no value", "a.b ="),
    ("member_assign: no attribute", "a. = 1"),
    ("member_assign: index is not assignable", "a[0] = 1"),
    ("member_assign: literal is not assignable", "1 = 2"),
    ("member_assign: parenthesized name is not assignable", "(a) = 1"),
    ("member_assign: call is not assignable", "f() = 1"),
    ("decl: semicolons do not exist", "local a = 1; local b = 2"),

    # operators
    ("sum: missing operand", "1 +"),
    ("sum: double operator", "1 + * 2"),
    ("term: missing operand", "1 *"),
    ("unary: dangling minus", "local a = -"),
    ("comparison: not chained", "a < b < c"),
    ("comparison: missing operand", "a == "),
    ("and_cond: missing operand", "a and"),
    ("or_cond: missing operand", "or a"),
    ("not_cond: missing operand", "local a = not"),
    ("expr: stray closing paren", "a)"),
    ("expr: stray closing bracket", "a]"),
    ("expr: stray closing brace", "}"),
    ("expr: opening paren never closed", "f(1"),

    # statements
    ("block: never closed", "fn f() {"),
    ("block: statement missing", "fn f() { local = 1 }"),
    ("if_stmt: no condition", "if { }"),
    ("if_stmt: condition not closed", "if (a { }"),
    ("if_stmt: no body", "if (a)"),
    ("elseif_stmt: no condition", "if (a) { } elseif { }"),
    ("elsestmt: no body", "if (a) { } else"),
    ("while_stmt: no condition", "while { }"),
    ("for_stmt: no in", "for (i items) { }"),
    ("for_stmt: no name", "for (in items) { }"),
    ("for_stmt: missing comma", "foreach (k v in m) { }"),
    ("throw_stmt: no value", "throw"),
    ("try_stmt: no body", "try"),
    ("catch_clause: no name", "try { } catch { }"),
    ("finally_clause: no body", "try { } finally"),
    ("import_stmt: no path", "import"),
    ("import_stmt: path is not a string", "import 1"),
    ("import_stmt: no name after as", 'import "m" as'),

    # functions
    ("fn_def: no name", "fn () { }"),
    ("fn_def: params are not closed", "fn f(a { }"),
    ("fn_def: param is not a name", "fn f(1) { }"),
    ("fn_def: trailing comma in params", "fn f(a,) { }"),
    ("wrapper_def: no name", "wrapper () { }"),
    ("return_stmt: value missing", "fn f() { return + }"),

    # decorators
    ("decorator: no name", "@"),
    ("decorator: no function after it", "@d"),
    ("decorated_fn: decorator on a class", "@d\nclass A { }"),
    ("decorated_fn: decorator on a const", "@d\nconst a = 1"),

    # classes
    ("class_def: no name", "class { }"),
    ("class_def: no body", "class A"),
    ("class_def: body never closed", "class A {"),
    ("class_def: parent is not a name", "class A extends 1 { }"),
    ("class_member: statements are not members", "class A { local x = 1 }"),
    ("class_member: nested classes are not members", "class A { class B { } }"),
    ("field_decl: no value", "class A { x }"),
    ("field_decl: no name", "class A { = 1 }"),
    ("method_def: no name", "class A { fn () { } }"),
    ("constructor_def: no params", "class A { constructor { } }"),
    ("class_body: modifier without a member", "class A { static }"),

    # expressions
    ("atom: nothing to read", "local a ="),
    ("atom: lone dot", "local a = ."),
    ("new_expr: no parens", "new A"),
    ("new_expr: no name", "new (A)()"),
    ("method_call: no name", "::()"),
    ("method_call: no parens", "::m"),
    ("super_call: no parent", "super"),
    ("super_call: no parens", "super::m"),
    ("static_ref: no name", "local a = .()"),
    ("fn_call: args need a value", "f(,)"),
    ("fn_call: trailing comma in args", "f(1,)"),
    ("lambda: params are not names", "(1) { }"),
    ("lambda: two names and no block", "(a, b)"),
    ("lambda: empty parens and no block", "()"),
    ("dotted_name: nothing after the dot", "new A.()"),
    ("index_access: index is never closed", "a[0"),
]


class ProductionCoverageTest(unittest.TestCase):
    """The suite must know about every production of the grammar."""

    def test_grammar_file_is_found(self):
        self.assertTrue(GRAMMAR.is_file(), GRAMMAR)

    def test_every_production_is_covered(self):
        covered = set(NODE_CASES) | set(LIST_CASES) | set(TERMINALS) \
            | set(MODIFIER_CASES)
        declared = set(productions())
        self.assertEqual(declared - covered, set(),
                         "productions of grammar.lark without a test case")
        self.assertEqual(covered - declared, set(),
                         "test cases for productions that grammar.lark "
                         "does not declare")

    def test_productions_are_parsed_from_the_grammar(self):
        self.assertIn("add_stmt", productions())
        self.assertIn("start", productions())
        self.assertIn("RETURN_VOID", productions())


class ProductionTest(unittest.TestCase):
    """Each production builds the node the grammar says it builds."""

    def assert_builds(self, source, expected, production):
        ast = parse(source)
        self.assertIn(expected, node_names(ast),
                      f"{production}: {source!r} did not build a {expected}")

    def test_node_productions(self):
        for production, (source, expected) in NODE_CASES.items():
            with self.subTest(production=production, source=source):
                self.assert_builds(source, expected, production)

    def test_list_productions(self):
        for production, source in LIST_CASES.items():
            with self.subTest(production=production, source=source):
                self.assertIsInstance(parse(source), list)

    def test_terminals(self):
        for terminal, source in TERMINALS.items():
            with self.subTest(terminal=terminal, source=source):
                self.assertIsInstance(parse(source), list)
                types = {token.type for token in Lexer(source).tokenize()}
                if terminal != "COMMENT":
                    self.assertTrue(set(TOKEN_TYPES.get(terminal, (terminal,)))
                                    & types, f"{source!r} has no {terminal}")

    def test_modifier_productions(self):
        for production, (source, expected) in MODIFIER_CASES.items():
            with self.subTest(production=production, source=source):
                members = parse(source)[0]
                member = members.fields[0] if members.fields else members.methods[0]
                self.assertEqual(member.modifiers, [expected])


class RejectedTest(unittest.TestCase):
    """Everything outside the grammar is a syntax error with a position."""

    def test_rejected_sources(self):
        for label, source in REJECTED:
            with self.subTest(rule=label, source=source):
                with self.assertRaises(Errors.SyntaxError):
                    parse(source)

    def test_error_message_has_a_position_and_context(self):
        for label, source in REJECTED:
            with self.subTest(rule=label, source=source):
                try:
                    parse(source)
                except Errors.SyntaxError as error:
                    message = str(error)
                else:
                    self.fail(f"{label} was accepted")
                self.assertRegex(message, r"^Syntax error at line \d+, column \d+:")
                self.assertIn("^", message.splitlines()[2])
                self.assertTrue(message.splitlines()[3])

    def test_line_and_column_of_a_later_error(self):
        with self.assertRaises(Errors.SyntaxError) as raised:
            parse("local a = 1\nlocal b = 2\nlocal = 3")
        self.assertIn("line 3, column 7:", str(raised.exception))
        self.assertIn("local = 3", str(raised.exception))

    def test_nothing_is_accepted_after_a_complete_program(self):
        for source in ("local a = 1 local", "fn f() { } }", "1 2 +"):
            with self.subTest(source=source):
                with self.assertRaises(Errors.SyntaxError):
                    parse(source)


class PrecedenceTest(unittest.TestCase):
    """Precedence and associativity, exactly as the grammar orders it."""

    # or < and < not < comparison < +/- < * / % < unary < postfix
    def test_shape(self):
        cases = [
            ("1 + 2 * 3", lambda n: isinstance(n.right, emtypes.MulStmt)),
            ("1 * 2 + 3", lambda n: isinstance(n.left, emtypes.MulStmt)),
            ("1 - 2 - 3", lambda n: isinstance(n.left, emtypes.SubStmt)),
            ("1 / 2 / 3", lambda n: isinstance(n.left, emtypes.DivStmt)),
            ("1 % 2 * 3", lambda n: isinstance(n.left, emtypes.ModStmt)),
            ("-1 * 2", lambda n: isinstance(n.left, emtypes.NegStmt)),
            ("- -1", lambda n: isinstance(n.value, emtypes.NegStmt)),
            ("a or b and c", lambda n: isinstance(n.right, emtypes.AndCond)),
            ("a and b or c", lambda n: isinstance(n.left, emtypes.AndCond)),
            ("a and not b", lambda n: isinstance(n.right, emtypes.NotCond)),
            ("not a == b", lambda n: isinstance(n, emtypes.NotCond)),
            ("a == b and c", lambda n: isinstance(n.left, emtypes.EquComp)),
            ("a + b == c", lambda n: isinstance(n, emtypes.EquComp)),
            ("a == b + c", lambda n: isinstance(n, emtypes.EquComp)),
            ("(a + b) * c", lambda n: isinstance(n.left, emtypes.AddStmt)),
            ("a.b[0](1)", lambda n: isinstance(n, emtypes.FnCall)),
            ("-a.b", lambda n: isinstance(n.value, emtypes.MemberAccess)),
        ]
        for source, check in cases:
            with self.subTest(source=source):
                self.assertTrue(check(parse(source)[0]), source)

    def test_associativity(self):
        self.assertEqual(parse("1 - 2 - 3")[0], emtypes.SubStmt(
            left=emtypes.SubStmt(left=emtypes.IntLit(1), right=emtypes.IntLit(2)),
            right=emtypes.IntLit(3)))
        self.assertEqual(parse("a and b and c")[0], emtypes.AndCond(
            left=emtypes.AndCond(left=emtypes.NameRef("a"),
                                 right=emtypes.NameRef("b")),
            right=emtypes.NameRef("c")))

    def test_not_keeps_its_operand_in_a_list(self):
        # the compiler reads `NotCond.comparison[0]`
        self.assertEqual(parse("not a")[0],
                         emtypes.NotCond([emtypes.NameRef("a")]))
        self.assertEqual(parse("not not a")[0],
                         emtypes.NotCond([emtypes.NotCond(
                             [emtypes.NameRef("a")])]))


class StatementTest(unittest.TestCase):
    """Every statement keyword, and the ones that are not statements."""

    def test_every_statement_starts(self):
        sources = {
            "local_decl": "local a = 1",
            "const_decl": "const a = 1",
            "class_def": "class A { }",
            "namespace_def": "namespace N { }",
            "decorated_fn": "@d\nfn f() { }",
            "fn_def": "fn f() { }",
            "decorated_wrapper": "@d\nwrapper w() { }",
            "wrapper_def": "wrapper w() { }",
            "error_def": "error E (e) { }",
            "import_stmt": 'import "m"',
            "return_stmt": "return",
            "while_stmt": "while (a) { }",
            "for_stmt": "for (i in x) { }",
            "foritem_stmt": "foreach (k, v in x) { }",
            "break_stmt": "break",
            "continue_stmt": "continue",
            "throw_stmt": "throw E()",
            "try_stmt": "try { }",
            "member_assign": "a.b = 1",
            "expr_stmt": "f()",
            "decl": "a = 1",
            "if_stmt": "if (a) { }",
        }
        for statement, source in sources.items():
            with self.subTest(statement=statement):
                ast = parse(source)
                self.assertEqual(len(ast), 1, source)

    def test_reserved_words_are_never_identifiers(self):
        from koskript.lang.lexer import RESERVED_WORDS

        # the scanner and the grammar must reserve exactly the same words
        declared = re.search(r"NAME\s*:\s*/\(\?!\(\?:([^)]*)\)\\b\)",
                             GRAMMAR.read_text()).group(1).split("|")
        self.assertEqual(set(declared), set(RESERVED_WORDS))
        self.assertEqual(len(declared), len(set(declared)))

        for word in sorted(RESERVED_WORDS):
            with self.subTest(word=word):
                with self.assertRaises(Errors.SyntaxError):
                    parse(f"local {word} = 1")
                with self.assertRaises(Errors.SyntaxError):
                    parse(f"a.{word}")


class CommentTest(unittest.TestCase):
    """Comments are whitespace and can appear anywhere between tokens."""

    def test_comment_positions(self):
        expected = parse("local a = 1 + 2")
        sources = [
            "// one\nlocal a = 1 + 2",
            "local a = 1 + 2 // two",
            "local // there\na = 1 + 2",
            "local a = 1 +\n// middle\n2",
            "local a = 1 + 2\n// end",
        ]
        for source in sources:
            with self.subTest(source=source):
                self.assertEqual(parse(source), expected)

    def test_only_line_comments(self):
        self.assertEqual(parse("// nothing\n"), [])
        with self.assertRaises(Errors.SyntaxError):
            parse("/* nothing */")


class TerminalPatternTest(unittest.TestCase):
    """The scanner must tokenize exactly what the terminal regexes match.

    Every sample below is checked twice: once against the regex written in
    ``grammar.lark`` and once against the token the scanner really produces.
    """

    # terminal -> (samples the regex accepts, samples it rejects)
    SAMPLES = {
        "NAME": (["a", "b", "_x", "x9", "Abc_1", "a" * 64],
                 ["1a", "a-b", "a b", "", "ñ", "a.b"]),
        "NUMBER": (["0", "7", "42", "3.5", "0.0", "10.25"],
                   ["1.", ".5", "1.2.3", "-1", "1e5", "0x10"]),
        "STRING": (['""', '"a"', "'a'", '"a\\"b"', '"a\\\\b"', '"a\\nb"',
                    "'it\\'s'", '"two\nlines"'],
                   ['"a', "a'", '"a\\"', '"']),
        "BYTES": (['b""', 'b"a"', "B'a'", "b'\\x00'", 'b"a\\"b"'],
                  ['b"', "b'a", "b", '"b"']),
        "COMMENT": (["//", "// a", "//\t"], ["/", "/ a", "# a", "a // b"]),
        "RETURN_VOID": (["return", "return ", "return\t", "return// c",
                         "return\n", "return  \t\n"],
                        ["return 1", "returnx", "returns", "return\r"]),
    }

    def first_token(self, text):
        """``(type, text)`` of the first token, or ``(None, "")`` on error."""
        from koskript.lang.lexer import ParseError

        try:
            token = Lexer(text).tokenize()[0]
        except ParseError:
            return None, ""
        return token.type, token.text

    def matches(self, pattern, text):
        """``re.fullmatch`` for every terminal but RETURN_VOID.

        ``RETURN_VOID`` ends in a lookahead, so it stops right before the
        newline or the comment that makes it a void return.
        """
        if pattern.pattern.startswith("return"):
            return pattern.match(text)
        return pattern.fullmatch(text)

    def test_terminal_patterns_are_found(self):
        patterns = terminal_patterns()
        self.assertEqual(set(patterns), set(self.SAMPLES))
        for name in self.SAMPLES:
            self.assertTrue(patterns[name], name)

    # a comment is dropped and a void `return` stops before its tail
    TRAILING = {"COMMENT", "RETURN_VOID"}

    def test_regexes_and_scanner_agree(self):
        patterns = terminal_patterns()
        types = {"NAME": ("NAME",), "NUMBER": ("INT", "FLOAT"),
                 "STRING": ("STRING",), "BYTES": ("BYTES",),
                 "COMMENT": ("EOF",),          # comments are %ignore'd
                 "RETURN_VOID": ("RETURN_VOID",)}

        for name, (accepted, rejected) in self.SAMPLES.items():
            pattern = re.compile(patterns[name])
            for text in accepted:
                with self.subTest(terminal=name, text=text, accepted=True):
                    self.assertIsNotNone(self.matches(pattern, text))
                    kind, consumed = self.first_token(text)
                    self.assertIn(kind, types[name])
                    if name in self.TRAILING:
                        self.assertTrue(text.startswith(consumed), consumed)
                    else:
                        self.assertEqual(consumed, text)
            for text in rejected:
                with self.subTest(terminal=name, text=text, accepted=False):
                    self.assertIsNone(self.matches(pattern, text))
                    # the scanner must not read the whole text as this token
                    self.assertNotEqual(self.first_token(text),
                                        (types[name][0], text))

    def test_name_excludes_every_reserved_word(self):
        pattern = re.compile(terminal_patterns()["NAME"])
        from koskript.lang.lexer import RESERVED_WORDS

        for word in RESERVED_WORDS:
            with self.subTest(word=word):
                self.assertIsNone(pattern.fullmatch(word))
                # ... but it is a valid name as part of a longer one
                self.assertIsNotNone(pattern.fullmatch(word + "_x"))
                self.assertIsNotNone(pattern.fullmatch("a" + word))

    def test_return_void_does_not_swallow_the_next_line(self):
        # `return` alone is a void return, `return <expr>` is a value
        self.assertEqual(parse("fn f() {\n  return\n  g()\n}")[0].body[0].value,
                         None)
        self.assertIsNotNone(
            parse("fn f() {\n  return 1\n  g()\n}")[0].body[0].value)


class WhitespaceTest(unittest.TestCase):
    """Newlines are plain whitespace, like in the grammar."""

    def test_newlines_do_not_end_a_statement(self):
        self.assertEqual(parse("local a = 1\nlocal b = 2"),
                         parse("local a = 1 local b = 2"))

    def test_an_expression_can_span_lines(self):
        self.assertEqual(parse("local a = 1 +\n2"), parse("local a = 1 + 2"))

    def test_indentation_is_not_significant(self):
        self.assertEqual(parse("if (a) {\n  b()\n}"),
                         parse("if (a) { b() }"))

    def test_crlf_line_endings(self):
        self.assertEqual(parse("local a = 1\r\nlocal b = 2"),
                         parse("local a = 1 local b = 2"))
        self.assertEqual(parse("fn f() {\r\n  return\r\n}")[0].body,
                         [emtypes.ReturnStmt(value=None)])


if __name__ == "__main__":
    unittest.main()
