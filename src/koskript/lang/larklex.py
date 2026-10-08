"""Line-start retagger for the Lark front end.

Koskript newlines are plain whitespace, so without help the LALR table
would let a line that *starts* with a postfix operator continue the
expression of the previous line:

```koskript
local r = 5
(r >= 0) and (r < 1)   // the `(5)(r >= 0)` of a call chain
```

:class:`LineStartRetag` removes that ambiguity before the parser runs: a
``.``, ``::``, ``[`` or ``(`` token that begins a physical line (no token
before it on the same line) is rewritten into the ``_LINE_DOT``,
``_LINE_DCOLON``, ``_LINE_LSQB`` or ``_LINE_LPAR`` terminal declared in
``grammar.lark``. Those terminals are only accepted where a line may begin
a new expression, never in the ``?postfix`` chain, which must stay on one
line. It runs as the Lark ``postlex`` of the parser, between the scanner
and the parser, and is the exact counterpart of the ``line_start`` flag of
:mod:`.lexer` for the native parser: both mean "a newline separates this
token from the previous one".

The grammar declares the ``_LINE_*`` terminals with patterns that never
match, so the scanner itself cannot produce them and the same-line tokens
keep their ordinary type.
"""

from lark import Token

# The tokens that can continue an expression, and the line-start terminal
# each one becomes when it starts a physical line.
_LINE_STARTS = {
    ".": "_LINE_DOT",
    "::": "_LINE_DCOLON",
    "[": "_LINE_LSQB",
    "(": "_LINE_LPAR",
}


class LineStartRetag(object):
    """Lark ``postlex`` that rewrites line-starting postfix operators.

    Instances are stateless: :meth:`process` keeps its position in a local,
    so the same object can serve every parse.
    """

    # No terminal needs to stay lexable outside the parse states that
    # expect it: the parser reports the errors itself.
    always_accept = frozenset()

    def process(self, tokens):
        """Yield ``tokens`` with the line-starting postfix operators retagged."""
        previous_end = 0
        for token in tokens:
            target = _LINE_STARTS.get(token.value) \
                if isinstance(token.value, str) else None
            if target is not None and token.line > previous_end:
                token = Token(
                    type=target, value=token.value,
                    start_pos=token.start_pos, line=token.line,
                    column=token.column, end_line=token.end_line,
                    end_column=token.end_column, end_pos=token.end_pos)
            previous_end = token.end_line or token.line
            yield token
