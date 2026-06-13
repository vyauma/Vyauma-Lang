"""
lexer.py — The Vyauma lexer.

Converts a raw source string into a flat list of Token objects.

Usage
-----
    from src.lexer.lexer import Lexer

    tokens = Lexer(source).tokenize()

The lexer raises LexError on any character it cannot recognise or on an
unterminated string literal.  All other tokens in the stream are valid.

Design notes
------------
- The lexer is a single-pass, character-at-a-time scanner.
- It tracks line and column numbers for accurate error reporting.
- Comments (#) are consumed silently — no token is emitted.
- Blank lines produce no NEWLINE token (consecutive newlines are collapsed).
- The final token in every stream is always EOF.
"""

from __future__ import annotations

from typing import List

from .token import KEYWORDS, Token, TokenType


class LexError(Exception):
    """Raised when the lexer encounters a character it cannot tokenise."""

    def __init__(self, message: str, line: int, column: int) -> None:
        super().__init__(f"[line {line}, col {column}] LexError: {message}")
        self.line = line
        self.column = column


class Lexer:
    """
    Tokenises a Vyauma source string.

    Parameters
    ----------
    source:
        The full contents of a .vym file as a UTF-8 string.
    """

    def __init__(self, source: str) -> None:
        self._source: str = source
        self._pos: int = 0          # index of current character
        self._line: int = 1         # current 1-based line number
        self._col: int = 1          # current 1-based column number
        self._tokens: List[Token] = []
        self._indent_stack: List[int] = [0]
        self._is_at_line_start: bool = True

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def tokenize(self) -> List[Token]:
        """
        Scan the entire source and return a list of tokens.

        The list always ends with a single EOF token.
        Consecutive/trailing newlines are collapsed so the parser sees at
        most one NEWLINE between statements.

        Returns
        -------
        List[Token]
            All tokens including the terminal EOF.

        Raises
        ------
        LexError
            On an unrecognised character or unterminated string literal.
        """
        while not self._at_end():
            self._scan_token()

        # Dedent any remaining blocks before EOF
        while len(self._indent_stack) > 1:
            self._indent_stack.pop()
            self._emit(TokenType.DEDENT, "", self._line, self._col)

        self._tokens.append(
            Token(TokenType.EOF, "", self._line, self._col)
        )
        return self._tokens

    # ------------------------------------------------------------------ #
    # Core scanner loop                                                    #
    # ------------------------------------------------------------------ #

    def _scan_token(self) -> None:
        """Read the next token from the current position."""
        if self._is_at_line_start:
            indent_width = 0
            while not self._at_end():
                ch = self._peek()
                if ch == " ":
                    indent_width += 1
                    self._advance()
                elif ch == "\t":
                    indent_width += 4
                    self._advance()
                else:
                    break
                    
            if self._at_end():
                return
                
            ch = self._peek()
            if ch in ("\n", "\r", "#"):
                # Blank lines and full-line comments do not affect indentation
                pass
            else:
                self._is_at_line_start = False
                current_indent = self._indent_stack[-1]
                
                if indent_width > current_indent:
                    self._indent_stack.append(indent_width)
                    self._emit(TokenType.INDENT, "", self._line, self._col)
                elif indent_width < current_indent:
                    while self._indent_stack and indent_width < self._indent_stack[-1]:
                        self._indent_stack.pop()
                        self._emit(TokenType.DEDENT, "", self._line, self._col)
                        
                    if indent_width != self._indent_stack[-1]:
                        raise LexError("Inconsistent indentation", self._line, self._col)

        if self._at_end():
            return

        ch = self._advance()

        # ---- Whitespace (spaces and tabs only — NOT newlines) ----------
        if ch in (" ", "\t"):
            return  # skip silently

        # ---- Newline ---------------------------------------------------
        if ch == "\n":
            self._is_at_line_start = True
            # Collapse consecutive newlines: only emit if last token is
            # not already a NEWLINE, INDENT, DEDENT, or EOF.
            if self._tokens and self._tokens[-1].type not in (
                TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT, TokenType.EOF
            ):
                self._emit(TokenType.NEWLINE, "\n", self._line, self._col - 1)
            return

        # Windows-style \r\n: skip the \r, the \n is handled on next call
        if ch == "\r":
            return

        # ---- Comment ---------------------------------------------------
        if ch == "#":
            self._skip_comment()
            return

        # ---- String literals -------------------------------------------
        if ch in ('"', "'"):
            self._read_string(ch)
            return

        # ---- Numeric literals ------------------------------------------
        if ch.isdigit():
            self._read_number(ch)
            return

        # ---- Identifiers and keywords ----------------------------------
        if ch.isalpha() or ch == "_":
            self._read_identifier(ch)
            return

        # ---- Two-character operators (must be checked before single) ---
        start_col = self._col - 1  # column of the first char already consumed

        if ch == "=" and self._peek() == "=":
            self._advance()
            self._emit(TokenType.EQ, "==", self._line, start_col)
            return

        if ch == "!" and self._peek() == "=":
            self._advance()
            self._emit(TokenType.NEQ, "!=", self._line, start_col)
            return

        if ch == "<" and self._peek() == "=":
            self._advance()
            self._emit(TokenType.LTE, "<=", self._line, start_col)
            return

        if ch == ">" and self._peek() == "=":
            self._advance()
            self._emit(TokenType.GTE, ">=", self._line, start_col)
            return

        # ---- Single-character operators --------------------------------
        _SINGLE: dict[str, TokenType] = {
            "+": TokenType.PLUS,
            "-": TokenType.MINUS,
            "*": TokenType.STAR,
            "/": TokenType.SLASH,
            "=": TokenType.ASSIGN,
            "<": TokenType.LT,
            ">": TokenType.GT,
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            "[": TokenType.LBRACKET,
            "]": TokenType.RBRACKET,
            "{": TokenType.LBRACE,
            "}": TokenType.RBRACE,
            ",": TokenType.COMMA,
            ":": TokenType.COLON,
            ".": TokenType.DOT,
        }
        if ch in _SINGLE:
            self._emit(_SINGLE[ch], ch, self._line, start_col)
            return

        # ---- Unrecognised character ------------------------------------
        raise LexError(
            f"Unexpected character {ch!r}",
            self._line,
            start_col,
        )

    # ------------------------------------------------------------------ #
    # Specialised readers                                                  #
    # ------------------------------------------------------------------ #

    def _skip_comment(self) -> None:
        """Consume everything up to (but not including) the next newline."""
        while not self._at_end() and self._peek() != "\n":
            self._advance()

    def _read_string(self, quote: str) -> None:
        """
        Read a string literal delimited by *quote* (either ' or ").

        The value stored in the token is the content *without* the
        surrounding quotes.  Escape sequences are not yet processed
        (planned for a later phase).

        Raises
        ------
        LexError
            If the string is not closed before a newline or EOF.
        """
        start_line = self._line
        start_col = self._col - 1  # column of the opening quote
        chars: list[str] = []

        while not self._at_end():
            ch = self._peek()
            if ch == "\n":
                raise LexError(
                    "Unterminated string literal (newline before closing quote)",
                    start_line,
                    start_col,
                )
            
            if ch == "\\":
                self._advance() # consume the backslash
                if self._at_end():
                    raise LexError(
                        "Unterminated string literal (reached end of file)",
                        start_line,
                        start_col,
                    )
                escape_char = self._advance()
                if escape_char == "n":
                    chars.append("\n")
                elif escape_char == "t":
                    chars.append("\t")
                elif escape_char == "\\":
                    chars.append("\\")
                elif escape_char == '"':
                    chars.append('"')
                elif escape_char == "'":
                    chars.append("'")
                else:
                    raise LexError(
                        f"Invalid escape sequence: \\{escape_char}",
                        self._line,
                        self._col - 2
                    )
                continue
                
            self._advance()
            if ch == quote:
                # Closing quote found — stop without adding it
                self._emit(TokenType.STRING, "".join(chars), start_line, start_col)
                return
            chars.append(ch)

        raise LexError(
            "Unterminated string literal (reached end of file)",
            start_line,
            start_col,
        )

    def _read_number(self, first_digit: str) -> None:
        """
        Read an integer or float literal.

        An integer is a sequence of digits.
        A float is digits, a single dot, then more digits.
        A trailing dot with no following digit (e.g. ``42.``) is an error.

        Raises
        ------
        LexError
            If a dot is followed by a non-digit.
        """
        start_col = self._col - 1
        digits = [first_digit]

        while not self._at_end() and self._peek().isdigit():
            digits.append(self._advance())

        # Check for a decimal point
        if not self._at_end() and self._peek() == ".":
            # Look one character ahead of the dot
            dot_pos = self._pos + 1
            if dot_pos < len(self._source) and self._source[dot_pos].isdigit():
                digits.append(self._advance())  # consume '.'
                while not self._at_end() and self._peek().isdigit():
                    digits.append(self._advance())
                raw = "".join(digits)
                self._emit(TokenType.FLOAT, float(raw), self._line, start_col)
                return
            elif dot_pos >= len(self._source) or not self._source[dot_pos].isdigit():
                # Dot with no digit after it — leave the dot for the next scan
                pass

        raw = "".join(digits)
        self._emit(TokenType.INTEGER, int(raw), self._line, start_col)

    def _read_identifier(self, first_char: str) -> None:
        """
        Read an identifier or keyword.

        After collecting all identifier characters, the lexer checks the
        result against the KEYWORDS table.  Matching keywords get their
        own TokenType; everything else becomes IDENTIFIER.

        Boolean keywords ``true`` and ``false`` have their values converted
        to Python booleans.
        """
        start_col = self._col - 1
        chars = [first_char]

        while not self._at_end() and (
            self._peek().isalnum() or self._peek() == "_"
        ):
            chars.append(self._advance())

        word = "".join(chars)
        token_type = KEYWORDS.get(word, TokenType.IDENTIFIER)

        # Convert booleans to native Python values
        if token_type == TokenType.TRUE:
            value: object = True
        elif token_type == TokenType.FALSE:
            value = False
        else:
            value = word

        self._emit(token_type, value, self._line, start_col)

    # ------------------------------------------------------------------ #
    # Low-level character helpers                                          #
    # ------------------------------------------------------------------ #

    def _advance(self) -> str:
        """
        Consume and return the current character, updating position/line/col.
        """
        ch = self._source[self._pos]
        self._pos += 1
        if ch == "\n":
            self._line += 1
            self._col = 1
        else:
            self._col += 1
        return ch

    def _peek(self) -> str:
        """Return the current character without consuming it."""
        if self._at_end():
            return "\0"
        return self._source[self._pos]

    def _at_end(self) -> bool:
        """True when all source characters have been consumed."""
        return self._pos >= len(self._source)

    def _emit(
        self, token_type: TokenType, value: object, line: int, col: int
    ) -> None:
        """Append a new Token to the internal list."""
        self._tokens.append(Token(token_type, value, line, col))
