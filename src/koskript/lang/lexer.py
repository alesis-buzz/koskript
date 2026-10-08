"""Tokenizer for Koskript.

The scanner turns source code into a flat list of :class:`Token` objects.
Comments and whitespace are dropped, escapes of string and bytes literals are
resolved and numeric literals are converted to ``int`` / ``float``, so the
parser never has to look at the raw text again.

Token types are:

* ``NAME`` for identifiers,
* the keyword itself for reserved words (``local``, ``if``, ``fn``, ...),
* the operator text for punctuation (``+``, ``==``, ``::``, ...),
* ``INT``, ``FLOAT``, ``STRING`` and ``BYTES`` for literals,
* ``EOF`` at the end of the source.

Newlines are plain whitespace, but not quite invisible: every token carries a
``line_start`` flag with whether a newline separates it from the previous
token, which is how a postfix operator (``.``, ``::``, ``[``, ``(``) at the
beginning of a line is kept from continuing the expression above it (see
:mod:`.parser`). The other exception is ``return``, which is lexed as the
``RETURN_VOID`` token when it is the last thing on its line, so ``return``
without a value can be told apart from ``return <expression>``.
"""

from bisect import bisect_right

# Words reserved by the language: they can never be used as identifiers.
RESERVED_WORDS = frozenset((
    "if", "elseif", "else", "while", "for", "foreach", "fn", "wrapper",
    "return", "local", "const", "true", "false", "null", "and", "or", "not",
    "in", "break", "continue", "class", "extends", "new", "static", "public",
    "private", "this", "super", "constructor", "import", "as", "error",
    "throw", "try", "catch", "finally", "namespace",
))

_ESCAPES = {
    "n": "\n",
    "t": "\t",
    "r": "\r",
    "0": "\0",
    "\\": "\\",
    '"': '"',
    "'": "'",
}

_HEX_DIGITS = "0123456789abcdefABCDEF"

# Two character operators, keyed by their first character, so they win over
# the single character operator they start with.
_DOUBLE_OPERATORS = {
    "=": "==",
    "!": "!=",
    ">": ">=",
    "<": "<=",
    ":": "::",
}

_SINGLE_OPERATORS = frozenset("+-*/%><()[]{},:.=@")

_WHITESPACE = " \t\r\n"
_DIGITS = "0123456789"
_IDENT_START = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
_IDENT_BODY = _IDENT_START + _DIGITS
_QUOTES = "\"'"


def unescape(raw: str) -> str:
    """Resolve the escape sequences of the body of a string literal."""
    if "\\" not in raw:
        return raw

    out = []
    index = 0
    length = len(raw)
    while index < length:
        char = raw[index]
        if char == "\\" and index + 1 < length:
            out.append(_ESCAPES.get(raw[index + 1], raw[index + 1]))
            index += 2
        else:
            out.append(char)
            index += 1
    return "".join(out)


def unescape_bytes(raw: str) -> bytes:
    """Resolve the escape sequences of the body of a bytes literal.

    Supports the same escapes as strings plus ``\\xNN`` for arbitrary byte
    values. Characters outside ASCII are encoded as UTF-8.
    """
    if "\\" not in raw:
        return raw.encode("utf-8")

    out = bytearray()
    index = 0
    length = len(raw)
    while index < length:
        char = raw[index]
        if char == "\\" and index + 1 < length:
            nxt = raw[index + 1]
            if nxt == "x":
                digits = raw[index + 2:index + 4]
                if len(digits) != 2 \
                        or digits[0] not in _HEX_DIGITS \
                        or digits[1] not in _HEX_DIGITS:
                    raise ValueError(
                        f"invalid bytes escape '\\x{digits}', expected \\xNN")
                out.append(int(digits, 16))
                index += 4
                continue
            out.extend(_ESCAPES.get(nxt, nxt).encode("utf-8"))
            index += 2
        else:
            out.extend(char.encode("utf-8"))
            index += 1
    return bytes(out)


class Token(object):
    """A lexical token with its semantic value and its source position.

    ``text`` is the raw source of the token (used by error messages) and
    ``value`` is what the parser works with: the name of a ``NAME``, the
    resolved contents of a literal, or the text of an operator.

    ``line`` and ``column`` are computed on demand, because only the token
    reported in an error message ever needs them.

    ``line_start`` is ``True`` when a newline separates the token from the
    previous one. It is what stops a postfix operator at the beginning of a
    line from continuing the expression above it (see
    :meth:`Parser.parse_postfix <.parser.Parser.parse_postfix>`); the other
    tokens keep it as plain information.
    """

    __slots__ = ("type", "value", "text", "offset", "_lines", "_line",
                 "line_start")

    def __init__(self, type, value, text, offset, lines):
        self.type = type
        self.value = value
        self.text = text
        self.offset = offset
        self._lines = lines
        self._line = 0
        self.line_start = False

    @property
    def line(self):
        if self._line == 0:
            self._line = bisect_right(self._lines, self.offset)
        return self._line

    @property
    def column(self):
        return self.offset - self._lines[self.line - 1] + 1

    def __repr__(self):
        return f"Token({self.type!r}, {self.text!r})"


class ParseError(Exception):
    """A syntax error found while scanning or parsing, with its position."""

    __slots__ = ("offset", "line", "column", "message", "expected")

    def __init__(self, offset, line, column, message, expected=()):
        super().__init__(message)
        self.offset = offset
        self.line = line
        self.column = column
        self.message = message
        self.expected = expected


def _context(code: str, offset: int, span: int = 40) -> str:
    """The offending line of ``code`` plus a caret under ``offset``."""
    before = code[max(offset - span, 0):offset].rsplit("\n", 1)[-1]
    after = code[offset:offset + span].split("\n", 1)[0]
    return before + after + "\n" + " " * len(before.expandtabs()) + "^"


def format_syntax_error(code: str, error: ParseError, span: int = 40) -> str:
    """Build the host facing message of a :class:`ParseError`."""
    lines = [
        f"Syntax error at line {error.line}, column {error.column}:",
        _context(code, error.offset, span),
        error.message,
    ]

    expected = sorted(set(error.expected))
    if len(expected) == 1:
        lines.append("Expected " + expected[0])
    elif expected:
        lines.append("Expected one of: " + ", ".join(expected))

    return "\n".join(lines)


class Lexer(object):
    """Scans Koskript source code into a list of tokens.

    >>> Lexer("local x = 1").tokenize()[0]
    Token('local', 'local')
    """

    __slots__ = ("code", "length", "pos", "line_starts")

    def __init__(self, code: str):
        self.code = code
        self.length = length = len(code)
        self.pos = 0
        # Offsets of the first character of every line, used to turn a
        # position in the source into a (line, column) pair.
        line_starts = [0]
        index = code.find("\n")
        while index >= 0:
            line_starts.append(index + 1)
            index = code.find("\n", index + 1)
        self.line_starts = line_starts

    def tokenize(self) -> list:
        """Return every token of the source, ending with the ``EOF`` one.

        Every token gets its ``line_start`` flag: whether a newline
        separates it from the previous one.
        """
        tokens = []
        append = tokens.append
        while self.pos < self.length:
            char = self.code[self.pos]

            if char in _WHITESPACE:
                self.pos += 1
            elif char == "/":
                if self.code.startswith("//", self.pos):
                    end = self.code.find("\n", self.pos)
                    self.pos = self.length if end < 0 else end
                elif self.code.startswith("/*", self.pos):
                    self._error(self.pos, "Block comments are not supported, "
                                         "use // for a line comment.")
                else:
                    append(self._operator())
            elif char in _DIGITS:
                append(self._number())
            elif char in _QUOTES:
                append(self._string())
            elif char in "bB" and self._opens_quote(self.pos + 1):
                append(self._bytes())
            elif char in _IDENT_START:
                append(self._word())
            else:
                append(self._operator())

        append(self._make_token("EOF", None, "", self.length))

        # A token starts a line when a newline separates it from the
        # previous one; a newline inside a string literal belongs to the
        # literal, not to what follows it, which this gets right by
        # measuring the raw text between both tokens.
        previous_end = 0
        for token in tokens:
            token.line_start = "\n" in self.code[previous_end:token.offset]
            previous_end = token.offset + len(token.text)
        return tokens

    # SCANNERS ##################################################################

    def _number(self):
        start = self.pos
        code = self.code
        pos = self.pos
        while pos < self.length and code[pos] in _DIGITS:
            pos += 1

        is_float = False
        if pos + 1 < self.length and code[pos] == "." and code[pos + 1] in _DIGITS:
            is_float = True
            pos += 1
            while pos < self.length and code[pos] in _DIGITS:
                pos += 1

        self.pos = pos
        text = code[start:pos]
        value = float(text) if is_float else int(text)
        return self._make_token("FLOAT" if is_float else "INT", value, text, start)

    def _string(self):
        start = self.pos
        raw = self._literal_body(0, "string")
        return self._make_token("STRING", unescape(raw),
                                self.code[start:self.pos], start)

    def _bytes(self):
        start = self.pos
        raw = self._literal_body(1, "bytes")
        try:
            value = unescape_bytes(raw)
        except ValueError as error:
            self._error(start, str(error))
        return self._make_token("BYTES", value, self.code[start:self.pos], start)

    def _word(self):
        start = self.pos
        code = self.code
        pos = self.pos
        while pos < self.length and code[pos] in _IDENT_BODY:
            pos += 1
        self.pos = pos

        text = code[start:pos]
        if text not in RESERVED_WORDS:
            return self._make_token("NAME", text, text, start)

        if text == "return" and self._return_is_void(pos):
            return self._make_token("RETURN_VOID", None, text, start)
        return self._make_token(text, text, text, start)

    def _operator(self):
        start = self.pos
        code = self.code
        char = code[start]

        double = _DOUBLE_OPERATORS.get(char)
        if double is not None and code.startswith(double, start):
            self.pos = start + 2
            return self._make_token(double, double, double, start)

        if char not in _SINGLE_OPERATORS:
            self._error(start, f"Unexpected character {char!r}.")
        self.pos = start + 1
        return self._make_token(char, char, char, start)

    # HELPERS ###################################################################

    def _opens_quote(self, offset):
        return offset < self.length and self.code[offset] in _QUOTES

    def _literal_body(self, prefix, kind):
        """Consume a quoted literal and return its raw body.

        ``prefix`` is the length of the text before the opening quote (the
        ``b`` of a bytes literal) and ``kind`` names the literal in errors.
        """
        code = self.code
        quote = code[self.pos + prefix]
        index = self.pos + prefix + 1
        while index < self.length and code[index] != quote:
            index += 2 if code[index] == "\\" else 1

        if index >= self.length:
            self._error(self.pos, f"Unterminated {kind} literal.")

        body = code[self.pos + prefix + 1:index]
        self.pos = index + 1
        return body

    def _return_is_void(self, offset):
        """True when ``return`` is followed by a comment, a newline or EOF."""
        code = self.code
        index = offset
        while index < self.length and code[index] in " \t":
            index += 1
        if index >= self.length or code[index] == "\n":
            return True
        return code[index] == "/" and code.startswith("//", index)

    def _make_token(self, type, value, text, offset):
        return Token(type, value, text, offset, self.line_starts)

    def _error(self, offset, message, expected=()):
        """Raise a :class:`ParseError` at ``offset``; never returns."""
        line = bisect_right(self.line_starts, offset)
        column = offset - self.line_starts[line - 1] + 1
        raise ParseError(offset, line, column, message, expected)
