"""
parser.py — The Vyauma parser.

Converts a flat list of Tokens into an Abstract Syntax Tree (AST).
The parser uses a recursive descent approach.
"""

from __future__ import annotations

from typing import List

from src.lexer import Token, TokenType
from .ast import (
    Expr, LiteralExpr, PrintStmt, Program, Stmt, LetStmt, 
    VariableExpr, BinaryExpr, UnaryExpr, GroupingExpr,
    BlockStmt, IfStmt, ExpressionStmt, LoopStmt, AssignExpr, CallExpr, FuncStmt, ReturnStmt,
    ArrayExpr, IndexExpr, IndexAssignExpr,
    ObjectExpr, PropertyAccessExpr, PropertyAssignExpr, ThisExpr, SuperExpr, ClassStmt
)


class ParseError(Exception):
    """Raised when the parser encounters invalid syntax."""
    
    def __init__(self, message: str, token: Token) -> None:
        super().__init__(f"[line {token.line}, col {token.column}] ParseError: {message}")
        self.token = token


class Parser:
    """
    Parses a sequence of Vyauma tokens into an AST.
    """

    def __init__(self, tokens: List[Token]) -> None:
        self._tokens = tokens
        self._pos = 0

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def parse(self) -> Program:
        """
        Parse the token stream into a Program AST.
        """
        statements: List[Stmt] = []
        
        while not self._is_at_end():
            # Skip any stray newlines between statements
            if self._match(TokenType.NEWLINE):
                continue
            
            stmt = self._declaration()
            if stmt:
                statements.append(stmt)
                
        return Program(statements=statements)

    # ------------------------------------------------------------------ #
    # Statements                                                           #
    # ------------------------------------------------------------------ #

    def _declaration(self) -> Stmt | None:
        """Parse a declaration or statement."""
        if self._match(TokenType.LET):
            return self._let_declaration()
        if self._match(TokenType.FUNC):
            return self._function_declaration()
        if self._match(TokenType.CLASS):
            return self._class_declaration()
        return self._statement()

    def _function_declaration(self) -> Stmt:
        if not self._match(TokenType.IDENTIFIER):
            raise self._error(self._peek(), "Expected function name.")
        name = self._previous()
        
        if not self._match(TokenType.LPAREN):
            raise self._error(self._peek(), "Expected '(' after function name.")
            
        parameters = []
        if not self._check(TokenType.RPAREN):
            while True:
                if not self._match(TokenType.IDENTIFIER):
                    raise self._error(self._peek(), "Expected parameter name.")
                parameters.append(self._previous())
                if not self._match(TokenType.COMMA):
                    break
                    
        if not self._match(TokenType.RPAREN):
            raise self._error(self._peek(), "Expected ')' after parameters.")
            
        if not self._match(TokenType.COLON):
            raise self._error(self._peek(), "Expected ':' before function body.")
            
        if not self._match(TokenType.NEWLINE):
            raise self._error(self._peek(), "Expected newline before function body.")
            
        body = self._block()
        return FuncStmt(name=name, params=parameters, body=body)

    def _class_declaration(self) -> Stmt:
        if not self._match(TokenType.IDENTIFIER):
            raise self._error(self._peek(), "Expected class name.")
        name = self._previous()
        
        superclass = None
        if self._match(TokenType.LPAREN):
            if not self._match(TokenType.IDENTIFIER):
                raise self._error(self._peek(), "Expected superclass name.")
            superclass = VariableExpr(name=self._previous())
            if not self._match(TokenType.RPAREN):
                raise self._error(self._peek(), "Expected ')' after superclass name.")
                
        if not self._match(TokenType.COLON):
            raise self._error(self._peek(), "Expected ':' after class declaration.")
            
        if not self._match(TokenType.NEWLINE):
            raise self._error(self._peek(), "Expected newline after ':'.")
            
        if not self._match(TokenType.INDENT):
            raise self._error(self._peek(), "Expected indentation for class body.")
            
        methods = []
        while not self._check(TokenType.DEDENT) and not self._is_at_end():
            if not self._match(TokenType.FUNC):
                raise self._error(self._peek(), "Expected method declaration in class body.")
            methods.append(self._function_declaration())
            
        if not self._match(TokenType.DEDENT) and not self._is_at_end():
            raise self._error(self._peek(), "Expected dedent after class body.")
            
        return ClassStmt(name=name, superclass=superclass, methods=methods)

    def _let_declaration(self) -> Stmt:
        """Parse a variable declaration: let <name> = <expr>"""
        if not self._match(TokenType.IDENTIFIER):
            raise self._error(self._peek(), "Expected variable name.")
            
        name = self._previous()
        
        initializer = None
        if self._match(TokenType.ASSIGN):
            initializer = self._expression()
            
        if not self._is_at_end() and not self._check(TokenType.NEWLINE) and not self._check(TokenType.DEDENT):
            raise self._error(self._peek(), "Expected newline after variable declaration.")
            
        self._match(TokenType.NEWLINE)
        return LetStmt(name=name, initializer=initializer)

    def _statement(self) -> Stmt:
        """Parse a single statement."""
        if self._match(TokenType.PRINT):
            return self._print_statement()
            
        if self._match(TokenType.IF):
            return self._if_statement()
            
        if self._match(TokenType.LOOP):
            return self._loop_statement()
            
        if self._match(TokenType.RETURN):
            return self._return_statement()
            
        return self._expression_statement()

    def _return_statement(self) -> Stmt:
        keyword = self._previous()
        value = None
        if not self._check(TokenType.NEWLINE) and not self._check(TokenType.DEDENT) and not self._is_at_end():
            value = self._expression()
            
        if not self._is_at_end() and not self._check(TokenType.NEWLINE) and not self._check(TokenType.DEDENT):
            raise self._error(self._peek(), "Expected newline after return value.")
            
        self._match(TokenType.NEWLINE)
        return ReturnStmt(keyword=keyword, value=value)

    def _expression_statement(self) -> Stmt:
        """Parse an expression statement."""
        expr = self._expression()
        if not self._is_at_end() and not self._check(TokenType.NEWLINE) and not self._check(TokenType.DEDENT):
            raise self._error(self._peek(), "Expected newline after expression.")
            
        self._match(TokenType.NEWLINE)
        return ExpressionStmt(expression=expr)

    def _loop_statement(self) -> Stmt:
        """Parse a loop statement: loop <expr>: <block>"""
        keyword = self._previous()
        condition = self._expression()
        
        if not self._match(TokenType.COLON):
            raise self._error(self._peek(), "Expected ':' after loop condition.")
            
        if not self._match(TokenType.NEWLINE):
            raise self._error(self._peek(), "Expected newline after loop condition.")
            
        body = self._block()
        return LoopStmt(keyword=keyword, condition=condition, body=body)

    def _if_statement(self) -> Stmt:
        """Parse an if/else statement: if <expr>: <block> [else: <block>]"""
        keyword = self._previous()
        condition = self._expression()
        
        if not self._match(TokenType.COLON):
            raise self._error(self._peek(), "Expected ':' after if condition.")
            
        if not self._match(TokenType.NEWLINE):
            raise self._error(self._peek(), "Expected newline after if condition.")
            
        then_branch = self._block()
        else_branch = None
        
        if self._match(TokenType.ELSE):
            if self._match(TokenType.IF):
                else_branch = self._if_statement()
            else:
                if not self._match(TokenType.COLON):
                    raise self._error(self._peek(), "Expected ':' after 'else'.")
                if not self._match(TokenType.NEWLINE):
                    raise self._error(self._peek(), "Expected newline after 'else:'.")
                    
                else_branch = self._block()
            
        return IfStmt(keyword=keyword, condition=condition, then_branch=then_branch, else_branch=else_branch)

    def _block(self) -> BlockStmt:
        """Parse a block of statements."""
        if not self._match(TokenType.INDENT):
            raise self._error(self._peek(), "Expected indentation for block.")
            
        statements = []
        while not self._check(TokenType.DEDENT) and not self._is_at_end():
            decl = self._declaration()
            if decl is not None:
                statements.append(decl)
                
        if not self._match(TokenType.DEDENT) and not self._is_at_end():
            raise self._error(self._peek(), "Expected dedent after block.")
            
        return BlockStmt(statements=statements)

    def _print_statement(self) -> Stmt:
        """Parse a print statement: print <expr> [NEWLINE|EOF]"""
        keyword = self._previous()
        expr = self._expression()
        
        # A print statement must be followed by a newline, dedent, or EOF
        if not self._is_at_end() and not self._check(TokenType.NEWLINE) and not self._check(TokenType.DEDENT):
            raise self._error(self._peek(), "Expected newline after print statement.")
            
        self._match(TokenType.NEWLINE)
        
        return PrintStmt(expression=expr, keyword=keyword)

    # ------------------------------------------------------------------ #
    # Expressions                                                          #
    # ------------------------------------------------------------------ #

    def _expression(self) -> Expr:
        """Parse an expression."""
        return self._assignment()

    def _assignment(self) -> Expr:
        """Parse an assignment or fallback to equality."""
        expr = self._equality()
        
        if self._match(TokenType.ASSIGN):
            equals = self._previous()
            value = self._assignment()
            
            if isinstance(expr, VariableExpr):
                name = expr.name
                return AssignExpr(name=name, value=value)
            elif isinstance(expr, IndexExpr):
                return IndexAssignExpr(bracket=expr.bracket, callee=expr.callee, index=expr.index, value=value)
            elif isinstance(expr, PropertyAccessExpr):
                return PropertyAssignExpr(callee=expr.callee, dot=expr.dot, name=expr.name, value=value)
                
            self._error(equals, "Invalid assignment target.")
            
        return expr

    def _equality(self) -> Expr:
        """Parse equality operators (==, !=)."""
        expr = self._comparison()
        
        while self._match(TokenType.EQ, TokenType.NEQ):
            operator = self._previous()
            right = self._comparison()
            expr = BinaryExpr(left=expr, operator=operator, right=right)
            
        return expr

    def _comparison(self) -> Expr:
        """Parse comparison operators (<, >, <=, >=)."""
        expr = self._term()
        
        while self._match(TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE):
            operator = self._previous()
            right = self._term()
            expr = BinaryExpr(left=expr, operator=operator, right=right)
            
        return expr

    def _term(self) -> Expr:
        """Parse addition and subtraction."""
        expr = self._factor()
        
        while self._match(TokenType.PLUS, TokenType.MINUS):
            operator = self._previous()
            right = self._factor()
            expr = BinaryExpr(left=expr, operator=operator, right=right)
            
        return expr

    def _factor(self) -> Expr:
        """Parse multiplication and division."""
        expr = self._unary()
        
        while self._match(TokenType.STAR, TokenType.SLASH):
            operator = self._previous()
            right = self._unary()
            expr = BinaryExpr(left=expr, operator=operator, right=right)
            
        return expr

    def _unary(self) -> Expr:
        """Parse unary operators."""
        if self._match(TokenType.MINUS):
            operator = self._previous()
            right = self._unary()
            return UnaryExpr(operator=operator, right=right)
            
        return self._call()

    def _call(self) -> Expr:
        expr = self._primary()
        
        while True:
            if self._match(TokenType.LPAREN):
                expr = self._finish_call(expr)
            elif self._match(TokenType.LBRACKET):
                bracket = self._previous()
                index = self._expression()
                if not self._match(TokenType.RBRACKET):
                    raise self._error(self._peek(), "Expected ']' after index.")
                expr = IndexExpr(bracket=bracket, callee=expr, index=index)
            elif self._match(TokenType.DOT):
                dot = self._previous()
                if not self._match(TokenType.IDENTIFIER):
                    raise self._error(self._peek(), "Expected property name after '.'.")
                name = self._previous()
                expr = PropertyAccessExpr(callee=expr, dot=dot, name=name)
            else:
                break
                
        return expr

    def _finish_call(self, callee: Expr) -> Expr:
        arguments = []
        if not self._check(TokenType.RPAREN):
            while True:
                arguments.append(self._expression())
                if not self._match(TokenType.COMMA):
                    break
                    
        if not self._match(TokenType.RPAREN):
            raise self._error(self._peek(), "Expected ')' after arguments.")
            
        paren = self._previous()
        return CallExpr(callee=callee, paren=paren, arguments=arguments)

    def _primary(self) -> Expr:
        """Parse a primary expression (literals, grouping, identifiers)."""
        if self._match(TokenType.STRING, TokenType.INTEGER, TokenType.FLOAT, TokenType.TRUE, TokenType.FALSE):
            token = self._previous()
            return LiteralExpr(value=token.value, token=token)
            
        if self._match(TokenType.IDENTIFIER):
            return VariableExpr(name=self._previous())
            
        if self._match(TokenType.THIS):
            return ThisExpr(keyword=self._previous())
            
        if self._match(TokenType.SUPER):
            keyword = self._previous()
            if not self._match(TokenType.DOT):
                raise self._error(self._peek(), "Expected '.' after 'super'.")
            dot = self._previous()
            if not self._match(TokenType.IDENTIFIER):
                raise self._error(self._peek(), "Expected superclass method name.")
            method = self._previous()
            return SuperExpr(keyword=keyword, method=method, dot=dot)
            
        if self._match(TokenType.LBRACKET):
            bracket = self._previous()
            elements = []
            if not self._check(TokenType.RBRACKET):
                while True:
                    elements.append(self._expression())
                    if not self._match(TokenType.COMMA):
                        break
            if not self._match(TokenType.RBRACKET):
                raise self._error(self._peek(), "Expected ']' after array elements.")
            return ArrayExpr(bracket=bracket, elements=elements)

        if self._match(TokenType.LBRACE):
            brace = self._previous()
            properties = {}
            if not self._check(TokenType.RBRACE):
                while True:
                    if not self._match(TokenType.IDENTIFIER):
                        raise self._error(self._peek(), "Expected property name.")
                    name = self._previous()
                    if not self._match(TokenType.COLON):
                        raise self._error(self._peek(), "Expected ':' after property name.")
                    value = self._expression()
                    properties[name] = value
                    
                    if not self._match(TokenType.COMMA):
                        break
            if not self._match(TokenType.RBRACE):
                raise self._error(self._peek(), "Expected '}' after object properties.")
            return ObjectExpr(brace=brace, properties=properties)

        if self._match(TokenType.LPAREN):
            expr = self._expression()
            if not self._match(TokenType.RPAREN):
                raise self._error(self._peek(), "Expected ')' after expression.")
            return GroupingExpr(expression=expr)
            
        raise self._error(self._peek(), "Expected expression.")

    # ------------------------------------------------------------------ #
    # Low-level token helpers                                              #
    # ------------------------------------------------------------------ #

    def _match(self, *types: TokenType) -> bool:
        """
        If the current token matches any of the given types, consume it and return True.
        """
        for t in types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _check(self, token_type: TokenType) -> bool:
        """Return True if the current token is of the given type (without consuming)."""
        if self._is_at_end():
            return False
        return self._peek().type == token_type

    def _advance(self) -> Token:
        """Consume the current token and return it."""
        if not self._is_at_end():
            self._pos += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        """Return True if we've reached the EOF token."""
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        """Return the current token."""
        return self._tokens[self._pos]

    def _previous(self) -> Token:
        """Return the most recently consumed token."""
        return self._tokens[self._pos - 1]

    def _error(self, token: Token, message: str) -> ParseError:
        """Create a ParseError at the given token."""
        return ParseError(message, token)
