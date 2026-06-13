"""
tests/test_lexer.py — Tests for the Vyauma lexer.

Coverage
--------
- String literals (double-quoted, single-quoted, empty)
- Integer and float literals
- All keywords (print, let, if, else, loop, func, return, true, false)
- Identifiers
- All arithmetic operators (+, -, *, /)
- All comparison operators (==, !=, <, >, <=, >=)
- Assignment operator (=)
- Punctuation ( (, ), ,, : )
- Comments (full-line and inline)
- Newline handling (collapsed, blank lines ignored)
- Windows line endings (\r\n)
- Multi-statement programs
- Source location (line, column) on tokens
- EOF always present at end
- LexError: unterminated string (newline before close)
- LexError: unterminated string (EOF before close)
- LexError: unrecognised character
"""

import sys
from pathlib import Path

import pytest

# Make the project root importable regardless of how pytest is invoked
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lexer import LexError, Lexer, Token, TokenType


# --------------------------------------------------------------------------- #
# Helpers                                                                       #
# --------------------------------------------------------------------------- #

def lex(source: str) -> list[Token]:
    """Tokenise *source* and return the token list (including EOF)."""
    return Lexer(source).tokenize()


def types(source: str) -> list[TokenType]:
    """Return just the TokenType sequence for *source*."""
    return [t.type for t in lex(source)]


def values(source: str) -> list:
    """Return just the .value sequence for *source*."""
    return [t.value for t in lex(source)]


# --------------------------------------------------------------------------- #
# String literals                                                               #
# --------------------------------------------------------------------------- #

class TestStringLiterals:
    def test_double_quoted(self):
        tokens = lex('"hello"')
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "hello"

    def test_single_quoted(self):
        tokens = lex("'world'")
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "world"

    def test_empty_double_quoted(self):
        tokens = lex('""')
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == ""

    def test_empty_single_quoted(self):
        tokens = lex("''")
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == ""

    def test_string_with_spaces(self):
        tokens = lex('"Hello, Vyauma!"')
        assert tokens[0].value == "Hello, Vyauma!"

    def test_string_with_digits(self):
        tokens = Lexer('"123"').tokenize()
        assert tokens[0].value == "123"

    def test_escape_sequences(self):
        tokens = Lexer('"line1\\nline2\\t\\\\\\"\\\'"').tokenize()
        assert tokens[0].value == "line1\nline2\t\\\"'"

    def test_invalid_escape_sequence(self):
        with pytest.raises(LexError) as exc:
            Lexer('"bad\\xescape"').tokenize()
        assert "Invalid escape sequence: \\x" in str(exc.value)

    def test_unterminated_string_newline(self):
        with pytest.raises(LexError, match="Unterminated"):
            lex('"hello\n"')

    def test_unterminated_string_eof(self):
        with pytest.raises(LexError, match="Unterminated"):
            lex('"hello')

    def test_unterminated_single_quote_eof(self):
        with pytest.raises(LexError, match="Unterminated"):
            lex("'oops")


# --------------------------------------------------------------------------- #
# Integer literals                                                              #
# --------------------------------------------------------------------------- #

class TestIntegerLiterals:
    def test_zero(self):
        tokens = lex("0")
        assert tokens[0].type == TokenType.INTEGER
        assert tokens[0].value == 0

    def test_positive(self):
        tokens = lex("42")
        assert tokens[0].type == TokenType.INTEGER
        assert tokens[0].value == 42

    def test_large(self):
        tokens = lex("1000000")
        assert tokens[0].value == 1_000_000

    def test_value_is_python_int(self):
        tokens = lex("7")
        assert isinstance(tokens[0].value, int)


# --------------------------------------------------------------------------- #
# Float literals                                                                #
# --------------------------------------------------------------------------- #

class TestFloatLiterals:
    def test_basic(self):
        tokens = lex("3.14")
        assert tokens[0].type == TokenType.FLOAT
        assert tokens[0].value == pytest.approx(3.14)

    def test_leading_zero(self):
        tokens = lex("0.5")
        assert tokens[0].value == pytest.approx(0.5)

    def test_value_is_python_float(self):
        tokens = lex("1.0")
        assert isinstance(tokens[0].value, float)

    def test_trailing_dot_scanned_as_integer_and_dot(self):
        # "42." should tokenise as INTEGER(42) then DOT
        tokens = lex("42.")
        assert len(tokens) == 3  # INTEGER, DOT, EOF
        assert tokens[0].type == TokenType.INTEGER
        assert tokens[0].value == 42
        assert tokens[1].type == TokenType.DOT


# --------------------------------------------------------------------------- #
# Keywords                                                                      #
# --------------------------------------------------------------------------- #

class TestKeywords:
    @pytest.mark.parametrize("keyword, expected_type", [
        ("print",  TokenType.PRINT),
        ("let",    TokenType.LET),
        ("if",     TokenType.IF),
        ("else",   TokenType.ELSE),
        ("loop",   TokenType.LOOP),
        ("func",   TokenType.FUNC),
        ("return", TokenType.RETURN),
    ])
    def test_keyword_types(self, keyword, expected_type):
        tokens = lex(keyword)
        assert tokens[0].type == expected_type

    def test_true_type(self):
        tokens = lex("true")
        assert tokens[0].type == TokenType.TRUE

    def test_true_value_is_python_bool(self):
        tokens = lex("true")
        assert tokens[0].value is True

    def test_false_type(self):
        tokens = lex("false")
        assert tokens[0].type == TokenType.FALSE

    def test_false_value_is_python_bool(self):
        tokens = lex("false")
        assert tokens[0].value is False


# --------------------------------------------------------------------------- #
# Identifiers                                                                   #
# --------------------------------------------------------------------------- #

class TestIdentifiers:
    def test_simple(self):
        tokens = lex("x")
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "x"

    def test_underscore_start(self):
        tokens = lex("_count")
        assert tokens[0].type == TokenType.IDENTIFIER

    def test_mixed(self):
        tokens = lex("myVar123")
        assert tokens[0].value == "myVar123"

    def test_not_keyword(self):
        # "printing" starts with "print" but is longer — must be IDENTIFIER
        tokens = lex("printing")
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "printing"

    def test_case_sensitive(self):
        tokens_lower = lex("myvar")
        tokens_upper = lex("myVar")
        assert tokens_lower[0].value != tokens_upper[0].value


# --------------------------------------------------------------------------- #
# Arithmetic operators                                                          #
# --------------------------------------------------------------------------- #

class TestArithmeticOperators:
    @pytest.mark.parametrize("src, expected_type", [
        ("+", TokenType.PLUS),
        ("-", TokenType.MINUS),
        ("*", TokenType.STAR),
        ("/", TokenType.SLASH),
    ])
    def test_single_char_operators(self, src, expected_type):
        tokens = lex(src)
        assert tokens[0].type == expected_type


# --------------------------------------------------------------------------- #
# Comparison and assignment operators                                           #
# --------------------------------------------------------------------------- #

class TestComparisonOperators:
    @pytest.mark.parametrize("src, expected_type", [
        ("==", TokenType.EQ),
        ("!=", TokenType.NEQ),
        ("<",  TokenType.LT),
        (">",  TokenType.GT),
        ("<=", TokenType.LTE),
        (">=", TokenType.GTE),
        ("=",  TokenType.ASSIGN),
    ])
    def test_operator_types(self, src, expected_type):
        tokens = lex(src)
        assert tokens[0].type == expected_type

    def test_eq_not_confused_with_assign(self):
        toks = lex("==")
        assert toks[0].type == TokenType.EQ
        assert len(toks) == 2  # EQ + EOF

    def test_assign_not_confused_with_eq(self):
        toks = lex("=")
        assert toks[0].type == TokenType.ASSIGN


# --------------------------------------------------------------------------- #
# Punctuation                                                                   #
# --------------------------------------------------------------------------- #

class TestPunctuation:
    @pytest.mark.parametrize("src, expected_type", [
        ("(", TokenType.LPAREN),
        (")", TokenType.RPAREN),
        ("[", TokenType.LBRACKET),
        ("]", TokenType.RBRACKET),
        ("{", TokenType.LBRACE),
        ("}", TokenType.RBRACE),
        (",", TokenType.COMMA),
        (":", TokenType.COLON),
        (".", TokenType.DOT),
    ])
    def test_punctuation_types(self, src, expected_type):
        tokens = lex(src)
        assert tokens[0].type == expected_type


# --------------------------------------------------------------------------- #
# Comments                                                                      #
# --------------------------------------------------------------------------- #

class TestComments:
    def test_full_line_comment_produces_no_token(self):
        toks = lex("# this is a comment")
        # Only EOF
        assert types("# comment") == [TokenType.EOF]

    def test_inline_comment_stripped(self):
        toks = lex('print "hi" # comment')
        tok_types = [t.type for t in toks]
        assert TokenType.PRINT in tok_types
        assert TokenType.STRING in tok_types
        # No token for the comment text
        assert all(t.type != TokenType.IDENTIFIER or t.value != "comment"
                   for t in toks)

    def test_comment_after_newline_not_in_stream(self):
        src = 'print "a"\n# comment\nprint "b"'
        toks = lex(src)
        string_values = [t.value for t in toks if t.type == TokenType.STRING]
        assert string_values == ["a", "b"]


# --------------------------------------------------------------------------- #
# Newline handling                                                              #
# --------------------------------------------------------------------------- #

class TestNewlines:
    def test_newline_emitted_between_statements(self):
        src = 'print "a"\nprint "b"'
        tok_types = types(src)
        assert TokenType.NEWLINE in tok_types

    def test_consecutive_newlines_collapsed(self):
        src = 'print "a"\n\n\nprint "b"'
        tok_types = types(src)
        newline_count = tok_types.count(TokenType.NEWLINE)
        assert newline_count == 1

    def test_trailing_newline_ignored(self):
        # A trailing newline after the last statement should not add
        # an extra NEWLINE before EOF.
        src = 'print "hi"\n'
        tok_types = types(src)
        # Last two should be NEWLINE then EOF, or just EOF — never NEWLINE,NEWLINE
        assert tok_types.count(TokenType.NEWLINE) <= 1

    def test_windows_line_endings(self):
        src = 'print "a"\r\nprint "b"'
        tok_types = types(src)
        assert TokenType.PRINT in tok_types
        assert tok_types.count(TokenType.NEWLINE) == 1


# --------------------------------------------------------------------------- #
# EOF token                                                                     #
# --------------------------------------------------------------------------- #

class TestEOF:
    def test_eof_always_last(self):
        for src in ["", "x", 'print "hi"']:
            toks = lex(src)
            assert toks[-1].type == TokenType.EOF

    def test_empty_source_only_eof(self):
        toks = lex("")
        assert len(toks) == 1
        assert toks[0].type == TokenType.EOF

    def test_whitespace_only_source(self):
        toks = lex("   \t   ")
        assert len(toks) == 1
        assert toks[0].type == TokenType.EOF


# --------------------------------------------------------------------------- #
# Source location                                                               #
# --------------------------------------------------------------------------- #

class TestSourceLocation:
    def test_first_token_line_1(self):
        toks = lex('print "hi"')
        assert toks[0].line == 1

    def test_first_token_col_1(self):
        toks = lex('print "hi"')
        assert toks[0].column == 1

    def test_second_line_token(self):
        src = 'print "a"\nprint "b"'
        toks = lex(src)
        # Find the second PRINT token
        print_toks = [t for t in toks if t.type == TokenType.PRINT]
        assert print_toks[1].line == 2

    def test_column_advances_correctly(self):
        toks = lex("let x")
        # 'let' starts at col 1, 'x' starts at col 5
        let_tok = toks[0]
        x_tok = toks[1]
        assert let_tok.column == 1
        assert x_tok.column == 5

    def test_error_reports_line_and_col(self):
        with pytest.raises(LexError) as exc_info:
            lex('"unclosed')
        err = exc_info.value
        assert err.line == 1
        assert err.column == 1


# --------------------------------------------------------------------------- #
# Unrecognised characters                                                       #
# --------------------------------------------------------------------------- #

class TestLexErrors:
    @pytest.mark.parametrize("bad_char", ["@", "$", "^", "&", "~", "`"])
    def test_unrecognised_characters(self, bad_char):
        with pytest.raises(LexError, match="Unexpected character"):
            lex(bad_char)


# --------------------------------------------------------------------------- #
# Multi-statement / integration snippets                                        #
# --------------------------------------------------------------------------- #

class TestIndentation:
    def test_single_indent(self):
        source = "print a\n  print b"
        tokens = [t.type for t in lex(source)]
        assert tokens == [
            TokenType.PRINT, TokenType.IDENTIFIER, TokenType.NEWLINE,
            TokenType.INDENT, TokenType.PRINT, TokenType.IDENTIFIER,
            TokenType.DEDENT, TokenType.EOF
        ]

    def test_indent_dedent_eof(self):
        source = "a\n  b"
        tokens = [t.type for t in lex(source)]
        assert tokens == [
            TokenType.IDENTIFIER, TokenType.NEWLINE, 
            TokenType.INDENT, TokenType.IDENTIFIER, 
            TokenType.DEDENT, TokenType.EOF
        ]

    def test_nested_indent(self):
        source = "a\n  b\n    c\n  d\ne"
        tokens = [t.type for t in lex(source)]
        assert tokens == [
            TokenType.IDENTIFIER, TokenType.NEWLINE,
            TokenType.INDENT, TokenType.IDENTIFIER, TokenType.NEWLINE,
            TokenType.INDENT, TokenType.IDENTIFIER, TokenType.NEWLINE,
            TokenType.DEDENT, TokenType.IDENTIFIER, TokenType.NEWLINE,
            TokenType.DEDENT, TokenType.IDENTIFIER, TokenType.EOF
        ]

    def test_inconsistent_indentation(self):
        source = "a\n    b\n  c"
        with pytest.raises(LexError, match="Inconsistent indentation"):
            lex(source)

    def test_blank_lines_ignored(self):
        source = "a\n\n  \n    b"
        tokens = [t.type for t in lex(source)]
        assert tokens == [
            TokenType.IDENTIFIER, TokenType.NEWLINE,
            TokenType.INDENT, TokenType.IDENTIFIER, TokenType.DEDENT, TokenType.EOF
        ]

class TestIntegrationSnippets:
    def test_print_string(self):
        toks = lex('print "Hello, Vyauma!"')
        assert toks[0].type == TokenType.PRINT
        assert toks[1].type == TokenType.STRING
        assert toks[1].value == "Hello, Vyauma!"
        assert toks[2].type == TokenType.EOF

    def test_let_assignment(self):
        toks = lex("let x = 42")
        tok_types = [t.type for t in toks]
        assert tok_types == [
            TokenType.LET,
            TokenType.IDENTIFIER,
            TokenType.ASSIGN,
            TokenType.INTEGER,
            TokenType.EOF,
        ]

    def test_arithmetic_expression(self):
        toks = lex("a + b * 2")
        tok_types = [t.type for t in toks]
        assert tok_types == [
            TokenType.IDENTIFIER,
            TokenType.PLUS,
            TokenType.IDENTIFIER,
            TokenType.STAR,
            TokenType.INTEGER,
            TokenType.EOF,
        ]

    def test_function_call(self):
        toks = lex("add(x, y)")
        tok_types = [t.type for t in toks]
        assert tok_types == [
            TokenType.IDENTIFIER,  # add
            TokenType.LPAREN,
            TokenType.IDENTIFIER,  # x
            TokenType.COMMA,
            TokenType.IDENTIFIER,  # y
            TokenType.RPAREN,
            TokenType.EOF,
        ]

    def test_if_else_block(self):
        src = "if score >= 50:\n    print \"Pass\"\nelse:\n    print \"Fail\""
        toks = lex(src)
        tok_types = [t.type for t in toks]
        assert TokenType.IF in tok_types
        assert TokenType.GTE in tok_types
        assert TokenType.COLON in tok_types
        assert TokenType.ELSE in tok_types

    def test_full_program(self):
        src = (
            '# Greet the user\n'
            'let name = "Vyauma"\n'
            'print name\n'
        )
        toks = lex(src)
        tok_types = [t.type for t in toks]
        assert TokenType.LET in tok_types
        assert TokenType.IDENTIFIER in tok_types
        assert TokenType.ASSIGN in tok_types
        assert TokenType.STRING in tok_types
        assert TokenType.PRINT in tok_types
        assert toks[-1].type == TokenType.EOF

    def test_boolean_in_condition(self):
        toks = lex("if true:")
        tok_types = [t.type for t in toks]
        assert tok_types == [
            TokenType.IF,
            TokenType.TRUE,
            TokenType.COLON,
            TokenType.EOF,
        ]
