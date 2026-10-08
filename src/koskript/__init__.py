import pathlib

from .lang.emtypes import (KoskriptObject, Module, Namespace, Scope, ScopeInfo,
                           ThrownSignal)
from .lang.interpreter import KoskriptInterpreter
from .lang.parser import parse
from .lang.errors import Errors
from .stdlib import build_globals
import os

_grammar_path = os.path.join(pathlib.Path(__file__).resolve().parent,
                             "grammar.lark")


def _wrap(value):
    return value if isinstance(value, KoskriptObject) else KoskriptObject(value=value)


def _require_lark():
    """Import Lark, with a message that points at the experimental parser."""
    try:
        from lark import Lark
    except ImportError:
        raise Errors.RuntimeError(
            "the default parser needs the 'lark' package: install it, or pass "
            "native_parser_experiment=True to use the native parser") from None
    return Lark


class _Grammar(object):
    """The Lark grammar, with the LALR tables built on first use.

    Building them takes about 200 ms, so it is deferred until a script is
    actually parsed: runtimes created with ``native_parser_experiment=True``
    never pay for them.
    """

    __slots__ = ("path", "parser")

    def __init__(self, path):
        self.path = path
        self.parser = None

    def parse(self, code: str):
        """Parse ``code`` into a Lark tree."""
        if self.parser is None:
            with open(self.path, "r") as grammar_file:
                from .lang.larklex import LineStartRetag
                self.parser = _require_lark()(
                    grammar_file.read(), parser="lalr",
                    maybe_placeholders=False, postlex=LineStartRetag())
        return self.parser.parse(code)


grammar = _Grammar(_grammar_path)

# How many compiled sources a runtime keeps. Running the same script again is
# then free of parsing and compiling; the oldest entry is dropped past this.
_CHUNK_CACHE = 32

# Internal grammar terminals shown as the punctuation they stand for, so the
# "Expected one of" line of a Lark error does not leak the `_LINE_*` names.
_DISPLAY_NAMES = {"_LINE_LPAR": "'('", "_LINE_LSQB": "'['",
                  "_LINE_DOT": "'.'", "_LINE_DCOLON": "'::'"}


def _format_syntax_error(code: str, error) -> str:
    from lark.exceptions import UnexpectedInput

    if not isinstance(error, UnexpectedInput) or error.line is None:
        return str(error)

    lines = [f"Syntax error at line {error.line}, column {error.column}:", error.get_context(code).rstrip()]

    token = getattr(error, "token", None)
    if token is not None and token.type != "$END":
        lines.append(f"Unexpected token '{token}'.")

    expected = getattr(error, "expected", None)
    if expected:
        lines.append("Expected one of: " + ", ".join(sorted(
            _DISPLAY_NAMES.get(name, name) for name in expected)))

    return "\n".join(lines)


class KoskriptRuntime(object):
    """Embeddable Koskript runtime.

    The standard library is registered by default. Host globals are registered
    after it, so any of them can override a standard library name. Pass
    ``stdlib=False`` to skip the standard library entirely.

    Any Python value or callable exposed to scripts is wrapped automatically,
    so you can pass plain functions without building ``KoskriptObject`` by hand.

    Scripts are parsed with Lark, the default and stable front end, which
    needs the ``lark`` package. ``native_parser_experiment=True`` switches to
    the experimental pure Python scanner and parser instead: it needs no
    dependency, starts faster and parses about 6x quicker, and it is what
    will become the default once it has been validated in production.

    >>> rt = KoskriptRuntime({"print": print})
    >>> rt.execute("local x = 10\\nx + 26")
    36
    """

    def __init__(self, globals_map=None, _globals_=None, stdlib=True,
                 native_parser_experiment=False):
        if _globals_ is not None:
            globals_map = {**(globals_map or {}), **_globals_}

        self.globals = {}
        self.native_parser_experiment = bool(native_parser_experiment)
        self.__interpreter__ = KoskriptInterpreter()
        self._ast = None
        self.__interpreter__.module_loader = self._load_module
        self._modules = {}
        self._loading = []
        self._import_paths = []
        self._chunks = {}

        if not self.native_parser_experiment:
            # fail here instead of on the first script
            _require_lark()

        if stdlib:
            self.register_many(build_globals(self.__interpreter__.call_value))

        if globals_map:
            self.register_many(globals_map)

    @property
    def __ast__(self):
        """The Lark AST transformer, created the first time it is needed.

        It lives in :mod:`koskript.lang.astgen`, which imports Lark, so
        runtimes using the native parser never load it.
        """
        transformer = self._ast
        if transformer is None:
            from .lang.astgen import KoskriptTransformer
            transformer = self._ast = KoskriptTransformer()
        return transformer

    @__ast__.setter
    def __ast__(self, transformer):
        self._ast = transformer

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

        The compiled form of a source is cached, so running the same source
        again skips parsing and compiling it.

        Raises ``Errors.SyntaxError`` if the code cannot be parsed.
        """
        try:
            return self.__interpreter__.run_chunk(self._chunk(code))
        except ThrownSignal as signal:
            raise self.__interpreter__._uncaught(signal) from None

    def _chunk(self, code: str):
        """The compiled chunk of ``code``, compiled once per source."""
        chunk = self._chunks.get(code)
        if chunk is not None:
            return chunk

        chunk = self.__interpreter__.compiler.compile_chunk(self._compile(code))
        if len(self._chunks) >= _CHUNK_CACHE:
            # bounded, so a host that runs many different scripts does not
            # grow the cache without limit
            del self._chunks[next(iter(self._chunks))]
        self._chunks[code] = chunk
        return chunk

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

    def _transform(self, tree):
        """Run the AST transformer, unwrapping clean syntax errors."""
        from lark.exceptions import VisitError

        transformer = self.__ast__
        try:
            return transformer.transform(tree)
        except VisitError as e:
            if isinstance(e.orig_exc, Errors.SyntaxError):
                raise e.orig_exc from None
            raise

    def _compile(self, code: str):
        """Parse ``code`` into the list of statements the compiler consumes."""
        if self.native_parser_experiment:
            return parse(code)

        from lark.exceptions import LarkError

        try:
            tree = grammar.parse(code)
        except LarkError as e:
            raise Errors.SyntaxError(_format_syntax_error(code, e)) from e
        ast = self._transform(tree)

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
            ast = self._compile(code)
        except Errors.SyntaxError as e:
            raise Errors.SyntaxError(f"module '{path}':\n{e}") from None

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
