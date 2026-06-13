"""
token.py — Token types and the Token data class for the Vyauma lexer.

Every piece of source text the lexer recognises is represented as a Token.
Each token carries:
  - its type (a TokenType enum member)
  - its literal value (the raw text, or a converted Python value)
  - its source location (1-based line and column numbers)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class TokenType(Enum):
    """All token categories recognised by the Vyauma lexer."""

    # ------------------------------------------------------------------ #
    # Literals                                                             #
    # ------------------------------------------------------------------ #
    STRING  = auto()   # "hello" or 'hello'
    INTEGER = auto()   # 42
    FLOAT   = auto()   # 3.14

    # ------------------------------------------------------------------ #
    # Keywords                                                             #
    # ------------------------------------------------------------------ #
    PRINT   = auto()   # print
    LET     = auto()   # let
    IF      = auto()   # if
    ELSE    = auto()   # else
    LOOP    = auto()   # loop
    FUNC    = auto()   # func
    RETURN  = auto()   # return
    CLASS   = auto()   # class
    THIS    = auto()   # this
    SUPER   = auto()   # super
    TRUE    = auto()   # true
    FALSE   = auto()   # false

    # ------------------------------------------------------------------ #
    # Identifier (any non-keyword name)                                    #
    # ------------------------------------------------------------------ #
    IDENTIFIER = auto()

    # ------------------------------------------------------------------ #
    # Operators                                                            #
    # ------------------------------------------------------------------ #
    PLUS    = auto()   # +
    MINUS   = auto()   # -
    STAR    = auto()   # *
    SLASH   = auto()   # /
    ASSIGN  = auto()   # =
    EQ      = auto()   # ==
    NEQ     = auto()   # !=
    LT      = auto()   # <
    GT      = auto()   # >
    LTE     = auto()   # <=
    GTE     = auto()   # >=

    # ------------------------------------------------------------------ #
    # Punctuation                                                          #
    # ------------------------------------------------------------------ #
    LPAREN   = auto()   # (
    RPAREN   = auto()   # )
    LBRACKET = auto()   # [
    RBRACKET = auto()   # ]
    LBRACE   = auto()   # {
    RBRACE   = auto()   # }
    COMMA    = auto()   # ,
    COLON    = auto()   # :
    DOT      = auto()   # .

    # ------------------------------------------------------------------ #
    # Structure                                                            #
    # ------------------------------------------------------------------ #
    NEWLINE = auto()   # \n  (statement terminator)
    INDENT  = auto()   # increase in indentation
    DEDENT  = auto()   # decrease in indentation
    EOF     = auto()   # end of source


# Maps keyword strings to their TokenType.
# Checked after reading any identifier-shaped token.
KEYWORDS: dict[str, TokenType] = {
    "print":  TokenType.PRINT,
    "let":    TokenType.LET,
    "if":     TokenType.IF,
    "else":   TokenType.ELSE,
    "loop":   TokenType.LOOP,
    "func":   TokenType.FUNC,
    "return": TokenType.RETURN,
    "class":  TokenType.CLASS,
    "this":   TokenType.THIS,
    "super":  TokenType.SUPER,
    "true":   TokenType.TRUE,
    "false":  TokenType.FALSE,
}


@dataclass(frozen=True)
class Token:
    """
    A single lexical unit produced by the Vyauma lexer.

    Attributes
    ----------
    type:
        The category of this token (e.g. TokenType.STRING).
    value:
        The semantic value.
        - STRING  -> str  (content without surrounding quotes)
        - INTEGER -> int
        - FLOAT   -> float
        - TRUE    -> True (bool)
        - FALSE   -> False (bool)
        - All others -> str (the raw lexeme)
    line:
        1-based line number in the source file.
    column:
        1-based column number of the *first* character of this token.
    """

    type:   TokenType
    value:  Any
    line:   int
    column: int

    def __repr__(self) -> str:
        return (
            f"Token({self.type.name}, {self.value!r}, "
            f"line={self.line}, col={self.column})"
        )
