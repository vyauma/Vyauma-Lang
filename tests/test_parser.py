"""
tests/test_parser.py — Tests for the Vyauma parser.
"""

import sys
from pathlib import Path

import pytest

# Make the project root importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.lexer import Lexer, TokenType
from src.parser import ParseError, Parser
from src.parser.ast import (
    LiteralExpr, PrintStmt, BinaryExpr, GroupingExpr, UnaryExpr, IfStmt, LoopStmt, 
    AssignExpr, FuncStmt, ReturnStmt, CallExpr, VariableExpr, ArrayExpr, IndexExpr, 
    IndexAssignExpr, ObjectExpr, PropertyAccessExpr, PropertyAssignExpr, ExpressionStmt
)


def parse_source(source: str):
    tokens = Lexer(source).tokenize()
    return Parser(tokens).parse()


class TestParser:
    def test_parse_print_string(self):
        program = parse_source('print "hello"')
        
        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, PrintStmt)
        
        assert isinstance(stmt.expression, LiteralExpr)
        assert stmt.expression.value == "hello"

    def test_parse_grouping(self):
        program = parse_source('print (1 + 2)')
        stmt = program.statements[0]
        assert isinstance(stmt.expression, GroupingExpr)
        
    def test_parse_equality(self):
        program = parse_source('print 1 == 2')
        expr = program.statements[0].expression
        assert isinstance(expr, BinaryExpr)
        assert expr.operator.type == TokenType.EQ
        
    def test_parse_comparison(self):
        program = parse_source('print 1 < 2')
        expr = program.statements[0].expression
        assert isinstance(expr, BinaryExpr)
        assert expr.operator.type == TokenType.LT

    def test_parse_let_statement(self):
        program = parse_source('let x = "hello"')
        stmt = program.statements[0]
        assert stmt.name.value == "x"
        assert isinstance(stmt.initializer, LiteralExpr)
        assert stmt.initializer.value == "hello"

    def test_parse_assignment(self):
        program = parse_source('x = "hello"')
        stmt = program.statements[0]
        assert isinstance(stmt.expression, AssignExpr)
        assert stmt.expression.name.value == "x"
        assert isinstance(stmt.expression.value, LiteralExpr)
        assert stmt.expression.value.value == "hello"

    def test_parse_print_integer(self):
        program = parse_source("print 42")
        
        stmt = program.statements[0]
        assert isinstance(stmt, PrintStmt)
        assert isinstance(stmt.expression, LiteralExpr)
        assert stmt.expression.value == 42

    def test_parse_multiple_statements(self):
        program = parse_source('print "a"\nprint "b"')
        
        assert len(program.statements) == 2
        assert program.statements[0].expression.value == "a"
        assert program.statements[1].expression.value == "b"

    def test_parse_let_statement_redeclaration(self):
        program = parse_source('let x = 42\nprint x')
        
        assert len(program.statements) == 2
        let_stmt = program.statements[0]
        assert let_stmt.name.value == "x"
        assert let_stmt.initializer.value == 42
        
        print_stmt = program.statements[1]
        assert print_stmt.expression.name.value == "x"

    def test_empty_program(self):
        program = parse_source("")
        assert len(program.statements) == 0

    def test_parse_error_missing_expression(self):
        with pytest.raises(ParseError, match="Expected expression"):
            parse_source("print")

    def test_parse_error_unexpected_token(self):
        with pytest.raises(ParseError):
            parse_source('==')

    def test_parse_arithmetic(self):
        program = parse_source('print 1 + 2 * 3')
        
        # Should be parsed as: 1 + (2 * 3)
        stmt = program.statements[0]
        expr = stmt.expression
        
        assert isinstance(expr, BinaryExpr)
        assert expr.operator.type == TokenType.PLUS
        assert expr.left.value == 1
        
        right = expr.right
        assert isinstance(right, BinaryExpr)
        assert right.operator.type == TokenType.STAR
        assert right.left.value == 2
        assert right.right.value == 3

    def test_parse_grouping_precedence(self):
        program = parse_source('print (1 + 2) * 3')
        
        # Should be parsed as: (1 + 2) * 3
        stmt = program.statements[0]
        expr = stmt.expression
        
        assert isinstance(expr, BinaryExpr)
        assert expr.operator.type == TokenType.STAR
        
        left = expr.left
        assert isinstance(left, GroupingExpr)
        
        inner = left.expression
        assert isinstance(inner, BinaryExpr)
        assert inner.operator.type == TokenType.PLUS
        assert inner.left.value == 1
        assert inner.right.value == 2
        
        assert expr.right.value == 3

    def test_parse_unary(self):
        program = parse_source('print -5')
        stmt = program.statements[0]
        expr = stmt.expression
        
        assert isinstance(expr, UnaryExpr)
        assert expr.operator.type == TokenType.MINUS
        assert expr.right.value == 5

    def test_parse_if_statement(self):
        program = parse_source('if true:\n  print "yes"')
        stmt = program.statements[0]
        assert isinstance(stmt, IfStmt)
        assert stmt.condition.value is True
        assert len(stmt.then_branch.statements) == 1
        assert isinstance(stmt.then_branch.statements[0], PrintStmt)
        assert stmt.else_branch is None

    def test_parse_if_else_statement(self):
        program = parse_source('if false:\n  print "no"\nelse:\n  print "yes"')
        stmt = program.statements[0]
        assert isinstance(stmt, IfStmt)
        assert stmt.condition.value is False
        assert len(stmt.then_branch.statements) == 1
        assert stmt.else_branch is not None
        assert len(stmt.else_branch.statements) == 1

    def test_parse_loop_statement(self):
        program = parse_source('loop true:\n  print "infinite"')
        stmt = program.statements[0]
        assert isinstance(stmt, LoopStmt)
        assert stmt.condition.value is True
        assert len(stmt.body.statements) == 1

    def test_parse_func_declaration(self):
        program = parse_source('func add(a, b):\n  return a + b')
        stmt = program.statements[0]
        assert isinstance(stmt, FuncStmt)
        assert stmt.name.value == "add"
        assert len(stmt.params) == 2
        assert stmt.params[0].value == "a"
        assert stmt.params[1].value == "b"
        
        body_stmt = stmt.body.statements[0]
        assert isinstance(body_stmt, ReturnStmt)
        assert isinstance(body_stmt.value, BinaryExpr)

    def test_parse_call(self):
        program = parse_source('print add(1, 2)')
        stmt = program.statements[0]
        assert isinstance(stmt, PrintStmt)
        expr = stmt.expression
        assert isinstance(expr, CallExpr)
        assert isinstance(expr.callee, VariableExpr)
        assert expr.callee.name.value == 'add'
        assert len(expr.arguments) == 2

    def test_parse_array_literal(self):
        program = parse_source('print [1, 2, 3]')
        stmt = program.statements[0]
        expr = stmt.expression
        assert isinstance(expr, ArrayExpr)
        assert len(expr.elements) == 3
        assert isinstance(expr.elements[0], LiteralExpr)
        assert expr.elements[0].value == 1

    def test_parse_index_expr(self):
        program = parse_source('print arr[0]')
        stmt = program.statements[0]
        expr = stmt.expression
        assert isinstance(expr, IndexExpr)
        assert isinstance(expr.callee, VariableExpr)
        assert expr.callee.name.value == 'arr'
        assert isinstance(expr.index, LiteralExpr)
        assert expr.index.value == 0

    def test_parse_index_assign(self):
        program = parse_source('arr[0] = 5')
        stmt = program.statements[0]
        assert isinstance(stmt, ExpressionStmt)
        expr = stmt.expression
        assert isinstance(expr, IndexAssignExpr)
        assert isinstance(expr.callee, VariableExpr)
        assert expr.callee.name.value == 'arr'
        assert isinstance(expr.value, LiteralExpr)
        assert expr.value.value == 5

    def test_parse_object_literal(self):
        program = parse_source('print { name: "vyauma" }')
        stmt = program.statements[0]
        expr = stmt.expression
        assert isinstance(expr, ObjectExpr)
        assert len(expr.properties) == 1
        key = list(expr.properties.keys())[0]
        assert key.value == 'name'
        assert isinstance(expr.properties[key], LiteralExpr)
        assert expr.properties[key].value == "vyauma"

    def test_parse_property_access(self):
        program = parse_source('print obj.name')
        stmt = program.statements[0]
        expr = stmt.expression
        assert isinstance(expr, PropertyAccessExpr)
        assert isinstance(expr.callee, VariableExpr)
        assert expr.callee.name.value == 'obj'
        assert expr.name.value == 'name'

    def test_parse_property_assign(self):
        program = parse_source('obj.name = "vyauma2"')
        stmt = program.statements[0]
        assert isinstance(stmt, ExpressionStmt)
        expr = stmt.expression
        assert isinstance(expr, PropertyAssignExpr)
        assert isinstance(expr.callee, VariableExpr)
        assert expr.callee.name.value == 'obj'
        assert expr.name.value == 'name'
        assert isinstance(expr.value, LiteralExpr)
        assert expr.value.value == "vyauma2"
