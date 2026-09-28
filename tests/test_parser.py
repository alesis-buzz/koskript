"""Tests for the Koskript lexer and parser.

Run them from the repository root with::

    PYTHONPATH=src python -m unittest discover -s tests
"""

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from koskript import grammar
from koskript.lang import emtypes
from koskript.lang.lexer import Lexer
from koskript.lang.parser import parse


def types_of(*nodes):
    return [type(node).__name__ for node in nodes]


class LexerTest(unittest.TestCase):
    def tokens(self, code):
        return [(token.type, token.value) for token in Lexer(code).tokenize()]

    def test_literals(self):
        self.assertEqual(self.tokens("1 2.5")[0], ("INT", 1))
        self.assertEqual(self.tokens("1 2.5")[1], ("FLOAT", 2.5))
        self.assertEqual(self.tokens('"a"')[0], ("STRING", "a"))
        self.assertEqual(self.tokens("b'\\x41'")[0], ("BYTES", b"A"))

    def test_keywords_and_names(self):
        self.assertEqual(self.tokens("local x")[:2],
                         [("local", "local"), ("NAME", "x")])

    def test_operators_longest_first(self):
        self.assertEqual([kind for kind, _ in self.tokens("== != >= <= :: + - * / % > <")][:-1],
                         ["==", "!=", ">=", "<=", "::", "+", "-", "*", "/", "%",
                          ">", "<"])

    def test_comments_and_whitespace_are_dropped(self):
        self.assertEqual(self.tokens("  1 // note\n 2 ")[0], ("INT", 1))
        self.assertEqual(self.tokens("  1 // note\n 2 ")[1], ("INT", 2))

    def test_number_needs_a_digit_after_the_dot(self):
        self.assertEqual([kind for kind, _ in self.tokens("1.")],
                         ["INT", ".", "EOF"])

    def test_b_prefix_is_only_a_prefix_for_quotes(self):
        self.assertEqual([kind for kind, _ in self.tokens("b b1 b'x'")][:-1],
                         ["NAME", "NAME", "BYTES"])

    def test_return_void(self):
        self.assertEqual([kind for kind, _ in self.tokens("return\nreturn 1\nreturn")][:-1],
                         ["RETURN_VOID", "return", "INT", "RETURN_VOID"])

    def test_escapes(self):
        self.assertEqual(self.tokens(r'"a\nb\tc\\d\"e\'f\0g"')[0][1],
                         "a\nb\tc\\d\"e'f\0g")
        self.assertEqual(self.tokens(r'b"\xff\n"')[0][1], b"\xff\n")
        self.assertEqual(self.tokens('b"ñ"')[0][1], b"\xc3\xb1")

    def test_line_and_column(self):
        token = Lexer("a\n  b\n// c\n  @").tokenize()[-2]
        self.assertEqual((token.line, token.column), (4, 3))

    def test_unterminated_literal(self):
        from koskript.lang.lexer import ParseError

        with self.assertRaises(ParseError):
            Lexer('"abc').tokenize()

    def test_invalid_bytes_escape(self):
        from koskript.lang.lexer import ParseError

        with self.assertRaises(ParseError):
            Lexer(r'b"\xzz"').tokenize()


class ParserTest(unittest.TestCase):
    def test_empty_program(self):
        self.assertEqual(parse(""), [])
        self.assertEqual(parse("\n\n// only a comment\n"), [])

    def test_declarations(self):
        ast = parse("local a = 1\nconst b = 2\na = 3")
        self.assertEqual(types_of(*ast), ["LocalDecl", "ConstDecl", "DeclStmt"])
        self.assertEqual(ast[0].name, "a")
        self.assertEqual(ast[0].value, emtypes.IntLit(1))
        self.assertEqual(ast[2].name, "a")

    def test_member_assignment(self):
        ast = parse("this.x = 1")
        self.assertEqual(ast[0], emtypes.MemberAssign(
            target=emtypes.ThisRef(), attr="x", value=emtypes.IntLit(1)))
        self.assertEqual(parse("a.b.c = 1")[0], emtypes.MemberAssign(
            target=emtypes.MemberAccess(name=emtypes.NameRef("a"),
                                       attrs=[emtypes.NameRef("b")]),
            attr="c", value=emtypes.IntLit(1)))

    def test_only_names_and_members_can_be_assigned(self):
        for code in ("a[0] = 1", "1 = 2", "f() = 1", "(a) = 1"):
            with self.assertRaises(Exception, msg=code):
                parse(code)

    def test_arithmetic_precedence(self):
        ast = parse("1 + 2 * 3 - 4")
        self.assertEqual(ast[0], emtypes.SubStmt(
            left=emtypes.AddStmt(
                left=emtypes.IntLit(1),
                right=emtypes.MulStmt(left=emtypes.IntLit(2), right=emtypes.IntLit(3))),
            right=emtypes.IntLit(4)))

    def test_unary_minus(self):
        self.assertEqual(parse("-1")[0], emtypes.NegStmt(value=emtypes.IntLit(1)))
        self.assertEqual(parse("1 - -1")[0].right,
                         emtypes.NegStmt(value=emtypes.IntLit(1)))

    def test_comparison_is_not_chained(self):
        self.assertEqual(parse("a < b")[0], emtypes.LtComp(
            left=emtypes.NameRef("a"), right=emtypes.NameRef("b")))
        with self.assertRaises(Exception):
            parse("a < b < c")

    def test_logic_precedence(self):
        ast = parse("a or b and not c")
        self.assertEqual(ast[0], emtypes.OrCond(
            left=emtypes.NameRef("a"),
            right=emtypes.AndCond(
                left=emtypes.NameRef("b"),
                right=emtypes.NotCond([emtypes.NameRef("c")]))))

    def test_not_binds_looser_than_comparison(self):
        self.assertEqual(parse("not a == b")[0],
                         emtypes.NotCond([emtypes.EquComp(
                             left=emtypes.NameRef("a"), right=emtypes.NameRef("b"))]))

    def test_grouping(self):
        self.assertEqual(parse("(1 + 2) * 3")[0].left,
                         emtypes.AddStmt(left=emtypes.IntLit(1), right=emtypes.IntLit(2)))

    def test_postfix(self):
        self.assertEqual(parse("a.b[0].c(1, 2)")[0], emtypes.FnCall(
            name=emtypes.MemberAccess(
                name=emtypes.IndexAccess(
                    value=emtypes.MemberAccess(
                        name=emtypes.NameRef("a"), attrs=[emtypes.NameRef("b")]),
                    index=emtypes.IntLit(0)),
                attrs=[emtypes.NameRef("c")]),
            args=[emtypes.IntLit(1), emtypes.IntLit(2)]))

    def test_class_expressions(self):
        self.assertEqual(parse("new A()")[0],
                         emtypes.NewExpr(target=emtypes.NameRef("A"), args=[],
                                         label="A"))
        self.assertEqual(parse("new A.B(1)")[0].label, "A.B")
        self.assertEqual(parse("::run()")[0],
                         emtypes.MethodCall(name="run", args=[]))
        self.assertEqual(parse(".build()")[0],
                         emtypes.FnCall(name=emtypes.StaticRef(name="build"), args=[]))
        self.assertEqual(parse("obj::run(1)")[0],
                         emtypes.BoundMethodCall(target=emtypes.NameRef("obj"),
                                                 name="run",
                                                 args=[emtypes.IntLit(1)]))
        self.assertEqual(parse("super::run()")[0],
                         emtypes.SuperCall(name="run", args=[]))
        self.assertEqual(parse("super::constructor(name)")[0],
                         emtypes.SuperCall(name="constructor",
                                           args=[emtypes.NameRef("name")]))
        self.assertEqual(parse("this.x")[0],
                         emtypes.MemberAccess(name=emtypes.ThisRef(),
                                              attrs=[emtypes.NameRef("x")]))

    def test_lambda_versus_grouping(self):
        self.assertEqual(parse("() { }")[0],
                         emtypes.LambdaFnDef(params=[], body=[]))
        self.assertEqual(parse("(a, b) { return a }")[0],
                         emtypes.LambdaFnDef(
                             params=["a", "b"],
                             body=[emtypes.ReturnStmt(value=emtypes.NameRef("a"))]))
        self.assertEqual(parse("(a + b)")[0],
                         emtypes.AddStmt(left=emtypes.NameRef("a"),
                                         right=emtypes.NameRef("b")))
        self.assertEqual(parse("(a.b)")[0],
                         emtypes.MemberAccess(name=emtypes.NameRef("a"),
                                              attrs=[emtypes.NameRef("b")]))
        with self.assertRaises(Exception):
            parse("(a, b)")
        with self.assertRaises(Exception):
            parse("(1) { }")
        with self.assertRaises(Exception):
            parse("()")

    def test_collections(self):
        self.assertEqual(parse("[1, 2,]")[0],
                         emtypes.ArrayLit(value=[emtypes.IntLit(1), emtypes.IntLit(2)]))
        self.assertEqual(parse("[]")[0], emtypes.ArrayLit(value=[]))
        self.assertEqual(parse("{\"a\": 1,}")[0], emtypes.MapLit(value=[
            emtypes.MapValue(key=emtypes.StrLit("a"), value=emtypes.IntLit(1))]))
        self.assertEqual(parse("{}")[0], emtypes.MapLit(value=[]))

    def test_control_flow(self):
        ast = parse("""
if (a) { b() } elseif (c) { d() } else { e() }
while (f) { g() }
for (i in items) { h() }
foreach (k, v in config) { m() }
break
continue
""")
        self.assertEqual(types_of(*ast),
                         ["IfStmt", "WhileStmt", "ForStmt", "ForItemStmt",
                          "BreakStmt", "ContinueStmt"])
        self.assertEqual(types_of(*ast[0].if_tree), ["ElseIfStmt", "ElseStmt"])
        self.assertEqual(ast[0].condition, emtypes.NameRef("a"))
        self.assertEqual(ast[2].var, "i")
        self.assertEqual((ast[3].key, ast[3].var), ("k", "v"))

    def test_functions(self):
        ast = parse("""
fn add(a, b) { return a + b }
fn noop() { }
wrapper double(x) { x * 2 }
""")
        self.assertEqual(types_of(*ast), ["FnDef", "FnDef", "FnDef"])
        self.assertEqual(ast[0].params, ["a", "b"])
        self.assertEqual(ast[1].params, [])
        self.assertEqual(ast[0].implicit_return, False)
        self.assertEqual(ast[2].implicit_return, True)

    def test_decorators(self):
        ast = parse("""
@a
@b(1)
@c.ns
@d.e(1, 2)
fn f() { }
@dec
wrapper w(x) { x }
""")
        self.assertEqual(ast[0].decorators,
                         [emtypes.NameRef("a"),
                          emtypes.FnCall(name=emtypes.NameRef("b"),
                                         args=[emtypes.IntLit(1)]),
                          emtypes.MemberAccess(name=emtypes.NameRef("c"),
                                               attrs=[emtypes.NameRef("ns")]),
                          emtypes.FnCall(
                              name=emtypes.MemberAccess(
                                  name=emtypes.NameRef("d"),
                                  attrs=[emtypes.NameRef("e")]),
                              args=[emtypes.IntLit(1), emtypes.IntLit(2)])])
        self.assertTrue(ast[1].implicit_return)
        with self.assertRaises(Exception):
            parse("@a\nclass A { }")

    def test_classes(self):
        ast = parse("""
class Base {
    public a = 1
    private b = 2
    constructor(x) { this.a = x }
    public fn run() { return ::helper() }
    private fn helper() { return super::run() }
    static fn build() { return new Base(1) }
    @dec
    public fn tagged() { }
}
class Child extends Base { }
""")
        self.assertEqual(types_of(*ast), ["ClassDef", "ClassDef"])
        self.assertEqual([field.name for field in ast[0].fields], ["a", "b"])
        self.assertEqual([field.modifiers for field in ast[0].fields],
                         [["public"], ["private"]])
        self.assertEqual([method.name for method in ast[0].methods],
                         ["run", "helper", "build", "tagged"])
        self.assertEqual([method.modifiers for method in ast[0].methods],
                         [["public"], ["private"], ["static"], ["public"]])
        self.assertEqual(len(ast[0].constructors), 1)
        self.assertTrue(ast[0].constructors[0].is_constructor)
        self.assertEqual(ast[1].parent_name, "Base")
        self.assertEqual(ast[1].parent, emtypes.NameRef("Base"))

    def test_class_body_only_takes_members(self):
        with self.assertRaises(Exception):
            parse("class A { local x = 1 }")
        with self.assertRaises(Exception):
            parse("class A { class B { } }")

    def test_errors_and_throw(self):
        ast = parse("""
error MyError (err, status) { err.message = "boom" }
error Empty () { }
throw MyError(1)
try { a() } catch e { b(e) } finally { c() }
try { a() }
try { a() } finally { c() }
""")
        self.assertEqual(types_of(*ast),
                         ["ErrorDef", "ErrorDef", "ThrowStmt", "TryStmt",
                          "TryStmt", "TryStmt"])
        self.assertEqual(ast[0].params, ["err", "status"])
        self.assertEqual(ast[1].params, [])
        self.assertEqual(ast[3].catch_name, "e")
        self.assertIsNotNone(ast[3].finally_body)
        self.assertIsNone(ast[4].catch_name)
        self.assertIsNone(ast[4].finally_body)

    def test_imports(self):
        ast = parse('import "utils"\nimport "sub/math" as m')
        self.assertEqual(ast[0], emtypes.ImportStmt(path="utils", name=None))
        self.assertEqual(ast[1], emtypes.ImportStmt(path="sub/math", name="m"))

    def test_namespace(self):
        ast = parse("namespace Utils { const MAX = 3 }")
        self.assertEqual(ast[0].name, "Utils")
        self.assertEqual(ast[0].body, [emtypes.ConstDecl(name="MAX",
                                                         value=emtypes.IntLit(3))])

    def test_return(self):
        self.assertEqual(parse("fn f() { return 1 }")[0].body[0],
                         emtypes.ReturnStmt(value=emtypes.IntLit(1)))
        self.assertEqual(parse("fn f() {\n  return\n}")[0].body[0],
                         emtypes.ReturnStmt(value=None))
        self.assertEqual(parse("fn f() { return // done\n}")[0].body[0],
                         emtypes.ReturnStmt(value=None))
        self.assertEqual(parse("fn f() { return }")[0].body[0],
                         emtypes.ReturnStmt(value=None))
        # A `return` at the end of a line never swallows the next statement.
        self.assertEqual(len(parse("fn f() {\n  return\n  g()\n}")[0].body), 2)

    def test_return_takes_every_kind_of_expression(self):
        for code in ("1", "1.5", '"s"', 'b"s"', "a", "[1]", "{1: 2}",
                     "(1 + 1)", "-1", ".m()", "true", "false", "null",
                     "this.x", "new A()", "super::m()", "::m()", "not a",
                     "a.b(c)", "a[0]", "not not a"):
            body = parse(f"fn f() {{ return {code} }}")[0].body
            self.assertEqual(len(body), 1, code)
            self.assertIsNotNone(body[0].value, code)

    def test_reserved_words_are_not_identifiers(self):
        for code in ("local if = 1", "local in = 1", "obj.if", "local super = 1"):
            with self.assertRaises(Exception, msg=code):
                parse(code)

    def test_newlines_are_whitespace(self):
        self.assertEqual(parse("local a = 1\n\nlocal b = 2"),
                         parse("local a = 1 local b = 2"))

    def test_syntax_error_position_and_context(self):
        from koskript.lang.errors import Errors

        with self.assertRaises(Errors.SyntaxError) as raised:
            parse("local = 1")
        message = str(raised.exception)
        self.assertIn("Syntax error at line 1, column 7:", message)
        self.assertIn("local = 1", message)
        self.assertIn("^", message)
        self.assertIn("Unexpected token '='.", message)

        with self.assertRaises(Errors.SyntaxError) as raised:
            parse("local a = [1,\nlocal b = 2")
        self.assertIn("line 2, column 1:", str(raised.exception))

    def test_too_deep_nesting_is_a_syntax_error(self):
        from koskript.lang.errors import Errors

        with self.assertRaises(Errors.SyntaxError) as raised:
            parse("(" * 500 + "1" + ")" * 500)
        self.assertIn("nested too deeply", str(raised.exception))


class RuntimeTest(unittest.TestCase):
    def test_executes(self):
        from koskript import KoskriptRuntime

        runtime = KoskriptRuntime()
        self.assertEqual(runtime.execute("local x = 10\nx + 26"), 36)
        self.assertEqual(runtime.execute("return 1 + 2"), 3)
        self.assertEqual(
            runtime.execute("""
class Counter {
    private count = 0
    constructor() { this.count = 1 }
    public fn bump() { this.count = this.count + 1 return this.count }
}
const c = new Counter()
c.bump() + c.bump()
"""), 5)
        self.assertEqual(
            runtime.execute("""
wrapper loud(target) { (name) { return target(name) + "!" } }
@loud
fn greet(name) { return "hola " + name }
greet("Ana")
"""), "hola Ana!")

    def test_error_handling(self):
        from koskript import Errors, KoskriptRuntime

        runtime = KoskriptRuntime()
        self.assertEqual(runtime.execute("""
error MyError (err) { err.message = "boom" }
try {
    throw MyError()
} catch e {
    return e.name + ": " + e.message
}
"""), "MyError: boom")

        with self.assertRaises(Errors.KoskriptError):
            runtime.execute("error E (err) { err.message = \"x\" }\nthrow E()")

    def test_syntax_error_reaches_the_host(self):
        from koskript import Errors, KoskriptRuntime

        with self.assertRaises(Errors.SyntaxError):
            KoskriptRuntime().execute("local = 1")

    def test_modules(self):
        import tempfile
        from koskript import KoskriptRuntime

        with tempfile.TemporaryDirectory() as folder:
            with open(f"{folder}/helpers.kos", "w") as handle:
                handle.write("fn double(x) { return x * 2 }")
            runtime = KoskriptRuntime()
            runtime.add_import_path(folder)
            script = 'import "helpers"\nhelpers.double(21)'
            self.assertEqual(runtime.execute(script), 42)
            # ... and with the experimental parser
            native = KoskriptRuntime(native_parser_experiment=True)
            native.add_import_path(folder)
            self.assertEqual(native.execute(script), 42)


class ParserSelectionTest(unittest.TestCase):
    """`native_parser_experiment` picks the front end, and both agree."""

    SCRIPTS = [
        "local x = 10\nx + 26",
        "return 1 + 2",
        'local m = { "a": 1, "b": [1, 2, 3] }\nreturn m.b[1]',
        "fn fact(n) {\n if (n < 2) { return 1 }\n return n * fact(n - 1)\n}\n"
        "return fact(6)",
        "class Counter {\n private n = 0\n constructor(v) { this.n = v }\n"
        " public fn bump() { this.n = this.n + 1 return this.n }\n"
        " public fn value() { return this.n }\n"
        " static fn make() { return new Counter(0) }\n}\n"
        "const c = new Counter(1)\nc.bump() + c.bump() + Counter.make().value()",
        "class Animal { public fn speak() { return \"woof\" } }\n"
        "class Dog extends Animal { public fn speak() { return super::speak() + \"!\" } }\n"
        "return new Dog().speak()",
        "namespace U { const MAX = 3\n fn twice(x) { return x * 2 } }\n"
        "return U.MAX + U.twice(2)",
        "error MyError (err) { err.message = \"boom\" }\n"
        "try { throw MyError() } catch e { return e.message }",
        "wrapper loud(t) { (n) { return t(n) + \"!\" } }\n@loud\n"
        "fn hi(n) { return \"hi \" + n }\nreturn hi(\"ana\")",
        "const add = (a, b) { return a + b }\nreturn add(1, 2)",
        "local out = []\nfor (i in range(5)) {\n if (i == 2) { continue }\n"
        " if (i == 4) { break }\n out = array.insert(out, 0, i)\n}\nreturn out",
        'foreach (k, v in { "a": "x", "b": "y" }) { return k + v }',
        "local b = b\"\\x01\\x02\"\nreturn len(b) + b[1]",
        "local i = 0\nwhile (i < 3) { i = i + 1 }\nreturn i",
    ]

    def test_default_uses_lark_and_the_flag_uses_the_native_parser(self):
        import koskript

        self.assertFalse(koskript.KoskriptRuntime().native_parser_experiment)
        self.assertTrue(
            koskript.KoskriptRuntime(native_parser_experiment=True)
            .native_parser_experiment)
        self.assertFalse(
            koskript.KoskriptRuntime(native_parser_experiment=False)
            .native_parser_experiment)

    def test_both_parsers_execute_the_same(self):
        from koskript import KoskriptRuntime

        default = KoskriptRuntime()
        native = KoskriptRuntime(native_parser_experiment=True)
        for script in self.SCRIPTS:
            with self.subTest(script=script):
                self.assertEqual(default.execute(script), native.execute(script))

    def test_both_parsers_build_the_same_ast(self):
        from koskript import KoskriptRuntime
        from koskript.lang.astgen import KoskriptTransformer
        from koskript.lang.parser import parse

        transformer = KoskriptTransformer()
        for script in self.SCRIPTS:
            with self.subTest(script=script):
                tree_ast = transformer.transform(grammar.parse(script))
                if not isinstance(tree_ast, list):
                    tree_ast = [tree_ast]
                self.assertEqual(parse(script), tree_ast)

    def test_both_parsers_reject_the_same_sources(self):
        from koskript import KoskriptRuntime, Errors

        broken = ["local = 1", "fn f( {", "a[0] = 1", "class A { local x = 1 }",
                  "return not", "a < b < c", "(a) = 1", "local in = 1"]
        default = KoskriptRuntime()
        native = KoskriptRuntime(native_parser_experiment=True)
        for script in broken:
            with self.subTest(script=script):
                with self.assertRaises(Errors.SyntaxError):
                    default.execute(script)
                with self.assertRaises(Errors.SyntaxError):
                    native.execute(script)

    def run_python(self, script):
        """Run ``script`` in a clean process that imports this checkout."""
        import os
        import subprocess
        import sys

        source = str(pathlib.Path(__file__).resolve().parent.parent / "src")
        env = dict(os.environ)
        env["PYTHONPATH"] = (source + os.pathsep + env["PYTHONPATH"]
                             if env.get("PYTHONPATH") else source)
        return subprocess.run([sys.executable, "-c", script],
                              capture_output=True, text=True, env=env)

    def test_native_parser_never_imports_lark(self):
        result = self.run_python(
            "import sys\n"
            "import koskript\n"
            "assert koskript.grammar.parser is None\n"
            "koskript.KoskriptRuntime(native_parser_experiment=True)"
            ".execute('return 1 + 2')\n"
            "loaded = [m for m in sys.modules if m.split('.')[0] == 'lark']\n"
            "assert not loaded, loaded\n"
            "print('ok')\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ok", result.stdout)

    def test_default_parser_without_lark_explains_the_flag(self):
        result = self.run_python(
            "import sys\n"
            "sys.modules['lark'] = None\n"
            "from koskript import KoskriptRuntime, Errors\n"
            "try:\n"
            "    KoskriptRuntime()\n"
            "except Errors.RuntimeError as error:\n"
            "    assert 'native_parser_experiment' in str(error), error\n"
            "    print('ok')\n"
            "else:\n"
            "    raise AssertionError('expected a RuntimeError')\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ok", result.stdout)

    def test_grammar_tables_are_built_on_first_use(self):
        result = self.run_python(
            "import koskript\n"
            "assert koskript.grammar.parser is None\n"
            "koskript.grammar.parse('1 + 2')\n"
            "assert koskript.grammar.parser is not None\n"
            "print('ok')\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ok", result.stdout)

    def test_grammar_object_is_usable(self):
        import koskript

        self.assertEqual(koskript.grammar.parse("1 + 2").data, "add_stmt")

    def test_benchmark_script_runs_on_both_parsers(self):
        import contextlib
        import io
        import koskript

        script = pathlib.Path(__file__).resolve().parent.parent \
            / "examples" / "benchmark.kos"
        if not script.is_file():
            self.skipTest("examples/benchmark.kos is not present")

        code = script.read_text()
        reports = []
        for flag in (False, True):
            runtime = koskript.KoskriptRuntime(native_parser_experiment=flag)
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                runtime.execute(code)
            reports.append(stream.getvalue())

        self.assertEqual(len(reports[0].splitlines()), 102)
        self.assertEqual(reports[0], reports[1])


class CompiledCacheTest(unittest.TestCase):
    """A source is parsed and compiled once per runtime."""

    def test_same_source_runs_twice(self):
        import koskript

        runtime = koskript.KoskriptRuntime()
        for _ in range(3):
            self.assertEqual(runtime.execute("local a = 2\nreturn a * 21"), 42)

    def test_top_level_declarations_persist(self):
        import koskript

        runtime = koskript.KoskriptRuntime()
        runtime.execute("local n = 0")
        self.assertEqual(runtime.execute("n = n + 1\nreturn n"), 1)
        self.assertEqual(runtime.execute("n = n + 1\nreturn n"), 2)

    def test_globals_are_read_at_every_run(self):
        import koskript

        runtime = koskript.KoskriptRuntime({"counter": 0})
        self.assertEqual(runtime.execute("return counter"), 0)
        runtime.register("counter", 7)
        self.assertEqual(runtime.execute("return counter"), 7)

    def test_source_is_compiled_only_once(self):
        import koskript
        from koskript.lang import compiler

        calls = []
        original = compiler.Compiler.compile_chunk

        def counting(self_, *args, **kwargs):
            calls.append(1)
            return original(self_, *args, **kwargs)

        runtime = koskript.KoskriptRuntime(native_parser_experiment=True)
        compiler.Compiler.compile_chunk = counting
        try:
            runtime.execute("return 1")
            first = len(calls)
            runtime.execute("return 1")
            second = len(calls) - first
        finally:
            compiler.Compiler.compile_chunk = original

        self.assertEqual(first, 1)
        self.assertEqual(second, 0)

    def test_the_cache_is_bounded(self):
        import koskript

        runtime = koskript.KoskriptRuntime(native_parser_experiment=True)
        for index in range(80):
            runtime.execute(f"return {index}")
        self.assertLessEqual(len(runtime._chunks), 32)
        # the most recent source is still cached
        self.assertEqual(runtime.execute("return 80"), 80)

    def test_a_broken_source_is_not_cached(self):
        import koskript

        runtime = koskript.KoskriptRuntime()
        with self.assertRaises(koskript.Errors.SyntaxError):
            runtime.execute("local = 1")
        with self.assertRaises(koskript.Errors.SyntaxError):
            runtime.execute("local = 1")
        self.assertEqual(runtime.execute("return 5"), 5)


if __name__ == "__main__":
    unittest.main()
