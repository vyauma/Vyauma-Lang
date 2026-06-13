"""
src/lexer — Vyauma lexer package.

Public API
----------
    from src.lexer import Lexer, Token, TokenType, LexError
"""

from .lexer import LexError, Lexer
from .token import KEYWORDS, Token, TokenType

__all__ = [
    "Lexer",
    "LexError",
    "Token",
    "TokenType",
    "KEYWORDS",
]
