"""
ast.py — Abstract Syntax Tree nodes for Vyauma.

The AST represents the grammatical structure of a Vyauma program.
Nodes are split into Expressions (which evaluate to a value)
and Statements (which perform an action).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.lexer import Token


class ASTNode:
    """Base class for all AST nodes."""
    pass


# --------------------------------------------------------------------------- #
# Expressions                                                                   #
# --------------------------------------------------------------------------- #

class Expr(ASTNode):
    """Base class for all expression nodes (evaluate to a value)."""
    pass


@dataclass(frozen=True)
class LiteralExpr(Expr):
    """
    A literal value like a string, integer, float, or boolean.
    
    Attributes:
        value: The native Python value of the literal.
        token: The original token (useful for line numbers in errors).
    """
    value: Any
    token: Token


@dataclass(frozen=True)
class BinaryExpr(Expr):
    """
    A binary expression: <left> <operator> <right>
    """
    left: Expr
    operator: Token
    right: Expr


@dataclass(frozen=True)
class UnaryExpr(Expr):
    """
    A unary expression: <operator> <right>
    """
    operator: Token
    right: Expr


@dataclass(frozen=True)
class GroupingExpr(Expr):
    """
    A grouped expression in parentheses: ( <expression> )
    """
    expression: Expr


@dataclass(frozen=True)
class VariableExpr(Expr):
    """
    A variable reference: x
    """
    name: Token


@dataclass(frozen=True)
class AssignExpr(Expr):
    """
    A variable assignment: x = 5
    """
    name: Token
    value: Expr


@dataclass(frozen=True)
class CallExpr(Expr):
    """
    A function call: greet("world")
    """
    callee: Expr
    paren: Token
    arguments: list[Expr]


@dataclass(frozen=True)
class ArrayExpr(Expr):
    """
    An array literal: [1, 2, 3]
    """
    bracket: Token
    elements: list[Expr]


@dataclass(frozen=True)
class IndexExpr(Expr):
    """
    An array access: arr[0]
    """
    bracket: Token
    callee: Expr
    index: Expr


@dataclass(frozen=True)
class IndexAssignExpr(Expr):
    """
    An array assignment: arr[0] = 5
    """
    bracket: Token
    callee: Expr
    index: Expr
    value: Expr


@dataclass(frozen=True)
class ObjectExpr(Expr):
    """
    An object literal: { name: "vyauma" }
    """
    brace: Token
    properties: dict[Token, Expr]


@dataclass(frozen=True)
class PropertyAccessExpr(Expr):
    """
    A property access: obj.name
    """
    callee: Expr
    dot: Token
    name: Token


@dataclass(frozen=True)
class PropertyAssignExpr(Expr):
    """
    A property assignment: obj.name = "vyauma2"
    """
    callee: Expr
    dot: Token
    name: Token
    value: Expr


@dataclass(frozen=True)
class ThisExpr(Expr):
    """
    A reference to the current instance: this
    """
    keyword: Token


@dataclass(frozen=True)
class SuperExpr(Expr):
    """
    A reference to a superclass method: super.init()
    """
    keyword: Token
    method: Token
    dot: Token


# --------------------------------------------------------------------------- #
# Statements                                                                    #
# --------------------------------------------------------------------------- #

class Stmt(ASTNode):
    """Base class for all statement nodes (perform actions)."""
    pass


@dataclass(frozen=True)
class PrintStmt(Stmt):
    """
    A print statement: print <expr>
    
    Attributes:
        expression: The expression to evaluate and print.
        keyword: The 'print' token.
    """
    expression: Expr
    keyword: Token


@dataclass(frozen=True)
class ExpressionStmt(Stmt):
    """
    A statement that evaluates an expression and discards the result.
    """
    expression: Expr


@dataclass(frozen=True)
class LetStmt(Stmt):
    """
    A variable declaration: let <name> = <initializer>
    """
    name: Token
    initializer: Expr | None


@dataclass(frozen=True)
class BlockStmt(Stmt):
    """
    A block of statements grouped together by indentation.
    """
    statements: list[Stmt]


@dataclass(frozen=True)
class IfStmt(Stmt):
    """
    An if statement: if <condition>: <block> [else: <block>]
    """
    keyword: Token
    condition: Expr
    then_branch: BlockStmt
    else_branch: BlockStmt | None


@dataclass(frozen=True)
class LoopStmt(Stmt):
    """
    A loop statement: loop <condition>: <block>
    """
    keyword: Token
    condition: Expr
    body: BlockStmt


@dataclass(frozen=True)
class FuncStmt(Stmt):
    """
    A function declaration: func <name>(<params>): <block>
    """
    name: Token
    params: list[Token]
    body: BlockStmt


@dataclass(frozen=True)
class ReturnStmt(Stmt):
    """
    A return statement: return a + b
    """
    keyword: Token
    value: Expr | None


@dataclass(frozen=True)
class ClassStmt(Stmt):
    """
    A class declaration: class Dog(Animal): ...
    """
    name: Token
    superclass: VariableExpr | None
    methods: list[FuncStmt]


@dataclass(frozen=True)
class Program(ASTNode):
    """
    The root of the AST, containing a list of statements.
    """
    statements: list[Stmt]
