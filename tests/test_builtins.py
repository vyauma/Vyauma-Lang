import pytest
from src.lexer import Lexer
from src.parser.parser import Parser
from src.runtime.interpreter import Interpreter

def interpret_source(source: str, interpreter=None):
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    if interpreter is None:
        interpreter = Interpreter()
    interpreter.interpret(program)


class TestBuiltins:
    def test_len_builtin(self, capsys):
        interpret_source('print len("hello")')
        assert capsys.readouterr().out == "5\n"
        
        interpret_source('print len([1, 2, 3])')
        assert capsys.readouterr().out == "3\n"
        
        interpret_source('print len({a: 1})')
        assert capsys.readouterr().out == "1\n"
        
        interpret_source('print len(42)')
        assert capsys.readouterr().out == "0\n"

    def test_str_builtin(self, capsys):
        interpret_source('print str(42)')
        assert capsys.readouterr().out == "42\n"
        
        interpret_source('print str(true)')
        assert capsys.readouterr().out == "true\n"
        
        interpret_source('print str(false)')
        assert capsys.readouterr().out == "false\n"

    def test_int_builtin(self, capsys):
        interpret_source('print int("42")')
        assert capsys.readouterr().out == "42\n"
        
        interpret_source('print int(3.14)')
        assert capsys.readouterr().out == "3\n"
        
        interpret_source('print int("bad")')
        assert capsys.readouterr().out == "0\n"

    def test_float_builtin(self, capsys):
        interpret_source('print float("3.14")')
        assert capsys.readouterr().out == "3.14\n"
        
        interpret_source('print float(42)')
        assert capsys.readouterr().out == "42.0\n"
        
        interpret_source('print float("bad")')
        assert capsys.readouterr().out == "0.0\n"

    def test_type_builtin(self, capsys):
        interpret_source('print type("hello")')
        assert capsys.readouterr().out == "string\n"
        
        interpret_source('print type(42)')
        assert capsys.readouterr().out == "number\n"
        
        interpret_source('print type(true)')
        assert capsys.readouterr().out == "boolean\n"
        
        interpret_source('print type([])')
        assert capsys.readouterr().out == "array\n"
        
        interpret_source('print type({})')
        assert capsys.readouterr().out == "object\n"
        
        interpret_source('print type(len)')
        assert capsys.readouterr().out == "function\n"

    def test_input_builtin(self, capsys, monkeypatch):
        monkeypatch.setattr('builtins.input', lambda prompt: "user input")
        interpret_source('print input("> ")')
        out = capsys.readouterr().out
        # In our implementation, input() doesn't print the prompt to stdout through capsys,
        # it prints it directly to stdout inside the `input()` call. The mock avoids that.
        assert out == "user input\n"
