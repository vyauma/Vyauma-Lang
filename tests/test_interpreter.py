"""
tests/test_interpreter.py — Tests for the Vyauma interpreter.
"""

import sys
from pathlib import Path

import pytest

# Make the project root importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lexer import Lexer
from src.parser import Parser
from src.runtime.interpreter import Interpreter, VyaumaRuntimeError


def interpret_source(source: str):
    """Lex, parse, and interpret the source code."""
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    interpreter = Interpreter()
    interpreter.interpret(program)


class TestInterpreter:
    def test_print_string(self, capsys):
        interpret_source('print "hello world"')
        captured = capsys.readouterr()
        assert captured.out == "hello world\n"
        assert captured.err == ""

    def test_print_integer(self, capsys):
        interpret_source('print 42')
        captured = capsys.readouterr()
        assert captured.out == "42\n"

    def test_print_boolean_true(self, capsys):
        interpret_source('print true')
        captured = capsys.readouterr()
        assert captured.out == "true\n"

    def test_print_boolean_false(self, capsys):
        interpret_source('print false')
        captured = capsys.readouterr()
        assert captured.out == "false\n"

    def test_multiple_prints(self, capsys):
        interpret_source('print "one"\nprint "two"\nprint "three"')
        captured = capsys.readouterr()
        assert captured.out == "one\ntwo\nthree\n"

    def test_variables(self, capsys):
        interpret_source('let x = 5\nprint x')
        captured = capsys.readouterr()
        assert captured.out == "5\n"

    def test_string_variable(self, capsys):
        interpret_source('let name = "Vyauma"\nprint name')
        captured = capsys.readouterr()
        assert captured.out == "Vyauma\n"

    def test_undefined_variable(self, capsys):
        # We expect a VyaumaRuntimeError when the interpreter catches a runtime error
        with pytest.raises(VyaumaRuntimeError):
            interpret_source('print oops')

    def test_arithmetic_basic(self, capsys):
        interpret_source('print 10 + 5')
        assert capsys.readouterr().out == "15\n"
        
        interpret_source('print 10 - 5')
        assert capsys.readouterr().out == "5\n"
        
        interpret_source('print 10 * 5')
        assert capsys.readouterr().out == "50\n"
        
        interpret_source('print 10 / 5')
        assert capsys.readouterr().out == "2.0\n"

    def test_arithmetic_precedence(self, capsys):
        interpret_source('print 1 + 2 * 3')
        assert capsys.readouterr().out == "7\n"

    def test_comparisons(self, capsys):
        interpret_source("print 1 < 2")
        assert capsys.readouterr().out == "true\n"
        
        interpret_source("print 2 > 1")
        assert capsys.readouterr().out == "true\n"
        
        interpret_source("print 2 <= 2")
        assert capsys.readouterr().out == "true\n"
        
        interpret_source("print 2 >= 3")
        assert capsys.readouterr().out == "false\n"

    def test_equality(self, capsys):
        interpret_source("print 1 == 1")
        assert capsys.readouterr().out == "true\n"
        
        interpret_source("print 1 != 2")
        assert capsys.readouterr().out == "true\n"
        
        interpret_source('print "hello" == "hello"')
        assert capsys.readouterr().out == "true\n"
        
        interpret_source('print "hello" != "world"')
        assert capsys.readouterr().out == "true\n"

    def test_arithmetic_grouping(self, capsys):
        interpret_source('print (1 + 2) * 3')
        assert capsys.readouterr().out == "9\n"

    def test_unary(self, capsys):
        interpret_source('print -5')
        assert capsys.readouterr().out == "-5\n"

    def test_string_concatenation(self, capsys):
        interpret_source('print "hello" + " world"')
        assert capsys.readouterr().out == "hello world\n"

    def test_type_error(self, capsys):
        with pytest.raises(VyaumaRuntimeError):
            interpret_source('print "hello" - 5')

    def test_if_statement_truthy(self, capsys):
        interpret_source('if true:\n  print "yes"')
        assert capsys.readouterr().out == "yes\n"

    def test_if_statement_falsy(self, capsys):
        interpret_source('if false:\n  print "yes"')
        assert capsys.readouterr().out == ""

    def test_if_else_statement(self, capsys):
        interpret_source('if false:\n  print "no"\nelse:\n  print "yes"')
        assert capsys.readouterr().out == "yes\n"

    def test_if_else_if_statement(self, capsys):
        source = 'if false:\n  print "no"\nelse if true:\n  print "yes"\nelse:\n  print "no"'
        interpret_source(source)
        assert capsys.readouterr().out == "yes\n"

    def test_block_scope(self, capsys):
        source = 'let x = 1\nif true:\n  let x = 2\n  print x\nprint x'
        interpret_source(source)
        assert capsys.readouterr().out == "2\n1\n"

    def test_block_scope_outer_access(self, capsys):
        source = 'let x = 1\nif true:\n  print x\n'
        interpret_source(source)
        assert capsys.readouterr().out == "1\n"

    def test_loop_falsy(self, capsys):
        source = 'loop false:\n  print "nope"\nprint "done"'
        interpret_source(source)
        assert capsys.readouterr().out == "done\n"

    def test_assignment(self, capsys):
        source = 'let x = 1\nx = x + 1\nprint x'
        interpret_source(source)
        assert capsys.readouterr().out == "2\n"

    def test_functions(self, capsys):
        source = 'func add(a, b):\n    return a + b\nprint add(2, 3)'
        interpret_source(source)
        assert capsys.readouterr().out == "5\n"

    def test_array_literal(self, capsys):
        source = 'let arr = [1, 2, 3]\nprint arr'
        interpret_source(source)
        assert capsys.readouterr().out == "[1, 2, 3]\n"

    def test_array_indexing(self, capsys):
        source = 'let arr = [10, 20, 30]\nprint arr[1]'
        interpret_source(source)
        assert capsys.readouterr().out == "20\n"

    def test_array_assignment(self, capsys):
        source = 'let arr = [10, 20, 30]\narr[1] = 99\nprint arr[1]'
        interpret_source(source)
        assert capsys.readouterr().out == "99\n"

    def test_object_literal(self, capsys):
        source = 'let obj = { name: "vyauma", version: 2 }\nprint obj.name'
        interpret_source(source)
        assert capsys.readouterr().out == "vyauma\n"

    def test_object_assignment(self, capsys):
        source = 'let obj = { x: 10 }\nobj.x = 20\nprint obj.x'
        interpret_source(source)
        assert capsys.readouterr().out == "20\n"

    def test_early_return(self, capsys):
        source = 'func check(x):\n  if x < 0:\n    return "negative"\n  return "positive"\nprint check(-5)'
        interpret_source(source)
        assert capsys.readouterr().out == "negative\n"
