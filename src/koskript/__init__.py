from lark import Lark
from lark.exceptions import LarkError, UnexpectedInput
from .lang.emtypes import (KoskriptObject, Module, Namespace, Scope, ScopeInfo,
                           ThrownSignal)
from .lang.interpreter import KoskriptInterpreter
from .lang.astgen import KoskriptTransformer
from .lang.errors import Errors
from .stdlib import build_globals
import pathlib, os

_grammar_path = os.path.join(pathlib.Path(__file__).resolve().parent, "grammar.lark")
with open(_grammar_path, "r") as _grammar_file:
    grammar = Lark(_grammar_file, parser="lalr", maybe_placeholders=False)


def _wrap(value):
    return value if isinstance(value, KoskriptObject) else KoskriptObject(value=value)


def _format_syntax_error(code: str, error: LarkError) -> str:
    if not isinstance(error, UnexpectedInput) or error.line is None:
        return str(error)

    lines = [f"Syntax error at line {error.line}, column {error.column}:", error.get_context(code).rstrip()]

    token = getattr(error, "token", None)
    if token is not None and token.type != "$END":
        lines.append(f"Unexpected token '{token}'.")

    expected = getattr(error, "expected", None)
    if expected:
        lines.append("Expected one of: " + ", ".join(sorted(expected)))

    return "\n".join(lines)


class KoskriptRuntime(object):
    """Embeddable Koskript runtime.

    The standard library is registered by default. Host globals are registered
    after it, so any of them can override a standard library name. Pass
    ``stdlib=False`` to skip the standard library entirely.

    Any Python value or callable exposed to scripts is wrapped automatically,
    so you can pass plain functions without building ``KoskriptObject`` by hand.

    >>> rt = KoskriptRuntime({"print": print})
    >>> rt.execute("local x = 10\\nx + 26")
    36
    """

    def __init__(self, globals_map=None, _globals_=None, stdlib=True):
        if _globals_ is not None:
            globals_map = {**(globals_map or {}), **_globals_}

        self.globals = {}
        self.__interpreter__ = KoskriptInterpreter()
        self.__ast__ = KoskriptTransformer()
        self.__interpreter__.module_loader = self._load_module
        self._modules = {}
        self._loading = []
        self._import_paths = []

        if stdlib:
            self.register_many(build_globals(self.__interpreter__.call_value))

        if globals_map:
            self.register_many(globals_map)

    def register(self, name: str, value):
        """Expose a Python value or callable to scripts.

        Returns the runtime so calls can be chained.
        """
        obj = _wrap(value)
        self.globals[name] = obj
        self.__interpreter__.set_global(name, obj)
        return self

    def register_many(self, mapping: dict):
        for name, value in mapping.items():
            self.register(name, value)
        return self

    def __setitem__(self, name: str, value):
        self.register(name, value)

    def __getitem__(self, name: str):
        return self.__interpreter__.get_global(name).value

    def add_import_path(self, path: str):
        """Add a directory that ``import`` searches after the base directory.

        The base directory is the one of the file that contains the ``import``
        (or the current working directory for ``execute``). Added paths are
        searched in the order they were registered, so a module next to the
        importer always wins. Returns the runtime so calls can be chained.
        """
        real = os.path.realpath(path)
        if not os.path.isdir(real):
            raise Errors.RuntimeError(
                f"import path '{path}' is not a directory")
        if real not in self._import_paths:
            self._import_paths.append(real)
        return self

    def execute(self, code: str):
        """Parse and run ``code``.

        Returns the value of the last evaluated expression, or the value of a
        top-level ``return`` if the script uses one.

        ``import "name"`` inside the script resolves against the current
        working directory of the Python process, then against the directories
        added with :meth:`add_import_path`.

        Raises ``Errors.SyntaxError`` if the code cannot be parsed.
        """
        return self.__interpreter__.run(self._compile(code))

    def execute_module(self, path: str):
        """Execute ``path`` as a Koskript module and return the module.

        The file is resolved against the current working directory, and the
        imports inside it resolve against the directory of the module file.
        Modules are loaded once per runtime and cached; circular imports raise
        ``Errors.RuntimeError``.
        """
        base_dir = os.path.dirname(self._loading[-1]) if self._loading else None
        try:
            return self._load_module(path, base_dir)
        except ThrownSignal as signal:
            raise self.__interpreter__._uncaught(signal) from None

    def _compile(self, code: str):
        try:
            tree = grammar.parse(code)
        except LarkError as e:
            raise Errors.SyntaxError(_format_syntax_error(code, e)) from e
        ast = self.__ast__.transform(tree)

        if not isinstance(ast, list):
            ast = [ast]
        return ast

    def _module_candidates(self, path: str, base_dir: str) -> list:
        """Absolute paths tried for ``import "path"``, in search order."""
        bases = [None] if os.path.isabs(path) else [base_dir, *self._import_paths]
        candidates = []
        for base in bases:
            candidate = path if base is None else os.path.join(base, path)
            if not candidate.lower().endswith(".kos") \
                    and not os.path.isfile(candidate):
                candidate += ".kos"
            candidates.append(os.path.realpath(candidate))
        return candidates

    def _load_module(self, path: str, base_dir: str = None):
        if base_dir is None:
            base_dir = os.getcwd()

        candidates = self._module_candidates(path, base_dir)
        real = next((item for item in candidates if os.path.isfile(item)), None)
        if real is None:
            looked = ", ".join(f"'{item}'" for item in candidates)
            raise Errors.RuntimeError(
                f"module '{path}' not found (looked for {looked})")

        cached = self._modules.get(real)
        if cached is not None:
            return cached

        if real in self._loading:
            raise Errors.RuntimeError(
                f"circular import of module '{path}'")

        try:
            with open(real, "r", encoding="utf-8-sig") as handle:
                code = handle.read()
        except OSError as e:
            raise Errors.RuntimeError(
                f"cannot read module '{path}': {e}") from e

        try:
            tree = grammar.parse(code)
        except LarkError as e:
            raise Errors.SyntaxError(
                f"module '{path}':\n{_format_syntax_error(code, e)}") from e

        ast = self.__ast__.transform(tree)
        if not isinstance(ast, list):
            ast = [ast]

        interpreter = self.__interpreter__
        info = ScopeInfo(interpreter.root_info)
        scope = Scope(interpreter.root, info)
        name = os.path.splitext(os.path.basename(real))[0]

        self._loading.append(real)
        try:
            interpreter.run_in(ast, scope, info,
                               base_dir=os.path.dirname(real))
        finally:
            self._loading.pop()

        module = Module(name, scope)
        self._modules[real] = module
        return module


def run(code: str, globals_map: dict = None, stdlib: bool = True, **kwargs):
    """One-shot convenience helper.

    >>> run("return 1 + 2")
    3
    """
    merged = dict(globals_map or {})
    merged.update(kwargs)
    return KoskriptRuntime(merged, stdlib=stdlib).execute(code)


__all__ = ["KoskriptRuntime", "KoskriptObject", "Module", "Namespace",
           "Errors", "run", "build_globals"]
