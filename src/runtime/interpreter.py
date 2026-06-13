"""
interpreter.py — The Vyauma Runtime Interpreter.

This module implements a tree-walking interpreter that executes the AST
produced by the parser.
"""

from typing import Any
import sys

from src.lexer import Token, TokenType
from src.parser import (
    ASTNode, Expr, LiteralExpr, PrintStmt, Program, Stmt,
    BinaryExpr, UnaryExpr, GroupingExpr, VariableExpr, AssignExpr, CallExpr,
    ArrayExpr, IndexExpr, IndexAssignExpr,
    ObjectExpr, PropertyAccessExpr, PropertyAssignExpr, ThisExpr, SuperExpr, ClassStmt,
    ExpressionStmt, LetStmt, BlockStmt, IfStmt, LoopStmt, FuncStmt, ReturnStmt
)


class VyaumaRuntimeError(Exception):
    """Exception raised for runtime errors during interpretation."""
    def __init__(self, token: Token, message: str) -> None:
        super().__init__(f"[line {token.line}] RuntimeError: {message}")
        self.token = token


class ReturnException(Exception):
    """Used to unwind the stack when a return statement is executed."""
    def __init__(self, value: Any) -> None:
        self.value = value


class VyaumaCallable:
    """Base interface for all callable objects (functions, methods, classes)."""
    def call(self, interpreter: "Interpreter", arguments: list[Any]) -> Any:
        raise NotImplementedError()
        
    def arity(self) -> int:
        raise NotImplementedError()


class VyaumaFunction(VyaumaCallable):
    """A user-defined function in Vyauma."""
    def __init__(self, declaration: FuncStmt, closure: "Environment") -> None:
        self.declaration = declaration
        self.closure = closure
        
    def call(self, interpreter: "Interpreter", arguments: list[Any]) -> Any:
        environment = Environment(enclosing=self.closure)
        for i, param in enumerate(self.declaration.params):
            environment.define(param.value, arguments[i])
            
        try:
            interpreter._execute_block(self.declaration.body.statements, environment)
        except ReturnException as ret:
            return ret.value
            
        return None
        
    def arity(self) -> int:
        return len(self.declaration.params)
        
    def bind(self, instance: "VyaumaInstance") -> "VyaumaFunction":
        environment = Environment(enclosing=self.closure)
        environment.define("this", instance)
        return VyaumaFunction(self.declaration, environment)
        
    def __str__(self) -> str:
        return f"<func {self.declaration.name.value}>"

class VyaumaInstance:
    def __init__(self, klass: "VyaumaClass") -> None:
        self.klass = klass
        self.fields: dict[str, Any] = {}
        
    def get(self, name: Token) -> Any:
        if name.value in self.fields:
            return self.fields[name.value]
            
        method = self.klass.find_method(name.value)
        if method is not None:
            return method.bind(self)
            
        raise VyaumaRuntimeError(name, f"Undefined property '{name.value}'.")
        
    def set(self, name: Token, value: Any) -> None:
        self.fields[name.value] = value
        
    def __str__(self) -> str:
        return f"{self.klass.name} instance"

class VyaumaClass(VyaumaCallable):
    def __init__(self, name: str, superclass: "VyaumaClass | None", methods: dict[str, VyaumaFunction]) -> None:
        self.name = name
        self.superclass = superclass
        self.methods = methods
        
    def find_method(self, name: str) -> VyaumaFunction | None:
        if name in self.methods:
            return self.methods[name]
        if self.superclass is not None:
            return self.superclass.find_method(name)
        return None
        
    def call(self, interpreter: "Interpreter", arguments: list[Any]) -> Any:
        instance = VyaumaInstance(self)
        initializer = self.find_method("init")
        if initializer is not None:
            initializer.bind(instance).call(interpreter, arguments)
        return instance
        
    def arity(self) -> int:
        initializer = self.find_method("init")
        if initializer is None:
            return 0
        return initializer.arity()
        
    def __str__(self) -> str:
        return self.name


class VyaumaBuiltin(VyaumaCallable):
    """A built-in native function in Vyauma."""
    def __str__(self) -> str:
        return "<native fn>"


class LenFunction(VyaumaBuiltin):
    def arity(self) -> int:
        return 1
        
    def call(self, interpreter: "Interpreter", arguments: list[Any]) -> Any:
        obj = arguments[0]
        if isinstance(obj, (str, list, dict)):
            return len(obj)
        # For simplicity, returning 0 or raising error. We will return 0.
        return 0


class StrFunction(VyaumaBuiltin):
    def arity(self) -> int:
        return 1
        
    def call(self, interpreter: "Interpreter", arguments: list[Any]) -> Any:
        obj = arguments[0]
        if obj is True:
            return "true"
        if obj is False:
            return "false"
        if obj is None:
            return "null"
        return str(obj)


class IntFunction(VyaumaBuiltin):
    def arity(self) -> int:
        return 1
        
    def call(self, interpreter: "Interpreter", arguments: list[Any]) -> Any:
        obj = arguments[0]
        try:
            return int(obj)
        except (ValueError, TypeError):
            return 0


class FloatFunction(VyaumaBuiltin):
    def arity(self) -> int:
        return 1
        
    def call(self, interpreter: "Interpreter", arguments: list[Any]) -> Any:
        obj = arguments[0]
        try:
            return float(obj)
        except (ValueError, TypeError):
            return 0.0


class TypeFunction(VyaumaBuiltin):
    def arity(self) -> int:
        return 1
        
    def call(self, interpreter: "Interpreter", arguments: list[Any]) -> Any:
        obj = arguments[0]
        if isinstance(obj, bool):
            return "boolean"
        if isinstance(obj, (int, float)):
            return "number"
        if isinstance(obj, str):
            return "string"
        if isinstance(obj, list):
            return "array"
        if isinstance(obj, dict):
            return "object"
        if isinstance(obj, VyaumaCallable):
            return "function"
        return "unknown"


class InputFunction(VyaumaBuiltin):
    def arity(self) -> int:
        return 1
        
    def call(self, interpreter: "Interpreter", arguments: list[Any]) -> Any:
        prompt = arguments[0]
        return input(str(prompt))


class Environment:
    """Stores bindings between variable names and their values."""
    def __init__(self, enclosing: "Environment | None" = None) -> None:
        self.values: dict[str, Any] = {}
        self.enclosing = enclosing

    def define(self, name: str, value: Any) -> None:
        """Define a new variable or overwrite an existing one."""
        self.values[name] = value

    def get(self, name: Token) -> Any:
        """Retrieve a variable's value."""
        if name.value in self.values:
            return self.values[name.value]
            
        if self.enclosing is not None:
            return self.enclosing.get(name)
            
        raise VyaumaRuntimeError(name, f"Undefined variable '{name.value}'.")
        
    def get_by_name(self, name_str: str, token: Token) -> Any:
        if name_str in self.values:
            return self.values[name_str]
        if self.enclosing is not None:
            return self.enclosing.get_by_name(name_str, token)
        raise VyaumaRuntimeError(token, f"Undefined variable '{name_str}'.")

    def assign(self, name: Token, value: Any) -> None:
        """Assign a new value to an existing variable."""
        if name.value in self.values:
            self.values[name.value] = value
            return
            
        if self.enclosing is not None:
            self.enclosing.assign(name, value)
            return
            
        raise VyaumaRuntimeError(name, f"Undefined variable '{name.value}'.")


class Interpreter:
    """
    A tree-walking interpreter that executes Vyauma AST nodes.
    """
    def __init__(self) -> None:
        self.environment = Environment()
        self.environment.define("len", LenFunction())
        self.environment.define("str", StrFunction())
        self.environment.define("int", IntFunction())
        self.environment.define("float", FloatFunction())
        self.environment.define("type", TypeFunction())
        self.environment.define("input", InputFunction())

    def interpret(self, program: Program) -> None:
        """
        Execute an entire Program AST.
        """
        for statement in program.statements:
            self._execute(statement)

    def _execute_block(self, statements: list[Stmt], environment: Environment) -> None:
        """Execute a block of statements within a given environment."""
        previous_env = self.environment
        try:
            self.environment = environment
            for statement in statements:
                self._execute(statement)
        finally:
            self.environment = previous_env

    # ------------------------------------------------------------------ #
    # Statements                                                           #
    # ------------------------------------------------------------------ #

    def _execute(self, stmt: Stmt) -> None:
        """Dispatch statement execution to the correct method."""
        if isinstance(stmt, PrintStmt):
            self._visit_print_stmt(stmt)
        elif isinstance(stmt, ExpressionStmt):
            self._visit_expression_stmt(stmt)
        elif isinstance(stmt, LetStmt):
            self._visit_let_stmt(stmt)
        elif isinstance(stmt, BlockStmt):
            self._visit_block_stmt(stmt)
        elif isinstance(stmt, IfStmt):
            self._visit_if_stmt(stmt)
        elif isinstance(stmt, LoopStmt):
            self._visit_loop_stmt(stmt)
        elif isinstance(stmt, FuncStmt):
            self._visit_func_stmt(stmt)
        elif isinstance(stmt, ReturnStmt):
            self._visit_return_stmt(stmt)
        elif isinstance(stmt, ClassStmt):
            self._visit_class_stmt(stmt)
        else:
            raise NotImplementedError(f"Execution for {type(stmt).__name__} is not implemented.")

    def _visit_print_stmt(self, stmt: PrintStmt) -> None:
        """Execute a print statement."""
        value = self._evaluate(stmt.expression)
        
        # Convert python True/False to lowercase true/false to match Vyauma spec
        if value is True:
            print("true")
        elif value is False:
            print("false")
        else:
            print(value)

    def _visit_expression_stmt(self, stmt: ExpressionStmt) -> None:
        """Execute an expression statement (evaluate and discard)."""
        self._evaluate(stmt.expression)

    def _visit_let_stmt(self, stmt: LetStmt) -> None:
        """Execute a let statement."""
        value = None
        if stmt.initializer is not None:
            value = self._evaluate(stmt.initializer)
            
        self.environment.define(stmt.name.value, value)

    def _visit_block_stmt(self, stmt: BlockStmt) -> None:
        self._execute_block(stmt.statements, Environment(enclosing=self.environment))

    def _visit_if_stmt(self, stmt: IfStmt) -> None:
        if self._is_truthy(self._evaluate(stmt.condition)):
            self._visit_block_stmt(stmt.then_branch)
        elif stmt.else_branch is not None:
            if isinstance(stmt.else_branch, IfStmt):
                self._visit_if_stmt(stmt.else_branch)
            else:
                self._visit_block_stmt(stmt.else_branch)

    def _visit_loop_stmt(self, stmt: LoopStmt) -> None:
        while self._is_truthy(self._evaluate(stmt.condition)):
            self._visit_block_stmt(stmt.body)

    def _visit_func_stmt(self, stmt: FuncStmt) -> None:
        function = VyaumaFunction(declaration=stmt, closure=self.environment)
        self.environment.define(stmt.name.value, function)
        
    def _visit_class_stmt(self, stmt: ClassStmt) -> None:
        superclass = None
        if stmt.superclass is not None:
            superclass = self._evaluate(stmt.superclass)
            if not isinstance(superclass, VyaumaClass):
                raise VyaumaRuntimeError(stmt.superclass.name, "Superclass must be a class.")

        self.environment.define(stmt.name.value, None)
        
        method_env = self.environment
        if superclass is not None:
            method_env = Environment(enclosing=self.environment)
            method_env.define("super", superclass)
        
        methods = {}
        for method in stmt.methods:
            function = VyaumaFunction(method, method_env)
            methods[method.name.value] = function
            
        klass = VyaumaClass(stmt.name.value, superclass, methods)
        self.environment.assign(stmt.name, klass)
        
    def _visit_return_stmt(self, stmt: ReturnStmt) -> None:
        value = None
        if stmt.value is not None:
            value = self._evaluate(stmt.value)
            
        raise ReturnException(value)

    # ------------------------------------------------------------------ #
    # Expressions                                                          #
    # ------------------------------------------------------------------ #

    def _evaluate(self, expr: Expr) -> Any:
        """Dispatch expression evaluation to the correct method."""
        if isinstance(expr, LiteralExpr):
            return self._visit_literal_expr(expr)
        elif isinstance(expr, BinaryExpr):
            return self._visit_binary_expr(expr)
        elif isinstance(expr, UnaryExpr):
            return self._visit_unary_expr(expr)
        elif isinstance(expr, GroupingExpr):
            return self._visit_grouping_expr(expr)
        elif isinstance(expr, VariableExpr):
            return self._visit_variable_expr(expr)
        elif isinstance(expr, AssignExpr):
            return self._visit_assign_expr(expr)
        elif isinstance(expr, CallExpr):
            return self._visit_call_expr(expr)
        elif isinstance(expr, ArrayExpr):
            return self._visit_array_expr(expr)
        elif isinstance(expr, IndexExpr):
            return self._visit_index_expr(expr)
        elif isinstance(expr, IndexAssignExpr):
            return self._visit_index_assign_expr(expr)
        elif isinstance(expr, ObjectExpr):
            return self._visit_object_expr(expr)
        elif isinstance(expr, PropertyAccessExpr):
            return self._visit_property_access_expr(expr)
        elif isinstance(expr, PropertyAssignExpr):
            return self._visit_property_assign_expr(expr)
        elif isinstance(expr, ThisExpr):
            return self._visit_this_expr(expr)
        elif isinstance(expr, SuperExpr):
            return self._visit_super_expr(expr)
        else:
            raise NotImplementedError(f"Evaluation for {type(expr).__name__} is not implemented.")

    def _visit_literal_expr(self, expr: LiteralExpr) -> Any:
        """Evaluate a literal expression."""
        return expr.value

    def _visit_binary_expr(self, expr: BinaryExpr) -> Any:
        left = self._evaluate(expr.left)
        right = self._evaluate(expr.right)
        
        op_type = expr.operator.type
        
        if op_type == TokenType.PLUS:
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left + right
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            raise VyaumaRuntimeError(expr.operator, "Operands must be two numbers or two strings.")
            
        if op_type == TokenType.MINUS:
            self._check_number_operands(expr.operator, left, right)
            return left - right
            
        if op_type == TokenType.STAR:
            self._check_number_operands(expr.operator, left, right)
            return left * right
            
        if op_type == TokenType.SLASH:
            self._check_number_operands(expr.operator, left, right)
            if right == 0:
                raise VyaumaRuntimeError(expr.operator, "Division by zero.")
            return left / right

        if op_type == TokenType.EQ:
            return left == right
            
        if op_type == TokenType.NEQ:
            return left != right
            
        if op_type == TokenType.LT:
            self._check_number_operands(expr.operator, left, right)
            return left < right
            
        if op_type == TokenType.GT:
            self._check_number_operands(expr.operator, left, right)
            return left > right
            
        if op_type == TokenType.LTE:
            self._check_number_operands(expr.operator, left, right)
            return left <= right
            
        if op_type == TokenType.GTE:
            self._check_number_operands(expr.operator, left, right)
            return left >= right

    def _visit_unary_expr(self, expr: UnaryExpr) -> Any:
        right = self._evaluate(expr.right)
        
        if expr.operator.type == TokenType.MINUS:
            self._check_number_operand(expr.operator, right)
            return -right
            
        raise VyaumaRuntimeError(expr.operator, "Unknown unary operator.")
        
    def _visit_grouping_expr(self, expr: GroupingExpr) -> Any:
        return self._evaluate(expr.expression)
        
    def _visit_variable_expr(self, expr: VariableExpr) -> Any:
        return self.environment.get(expr.name)

    def _visit_assign_expr(self, expr: AssignExpr) -> Any:
        value = self._evaluate(expr.value)
        self.environment.assign(expr.name, value)
        return value

    def _visit_call_expr(self, expr: CallExpr) -> Any:
        callee = self._evaluate(expr.callee)
        
        arguments = []
        for arg in expr.arguments:
            arguments.append(self._evaluate(arg))
            
        if not isinstance(callee, VyaumaCallable):
            raise VyaumaRuntimeError(expr.paren, "Can only call functions and classes.")
            
        if len(arguments) != callee.arity():
            raise VyaumaRuntimeError(expr.paren, f"Expected {callee.arity()} arguments but got {len(arguments)}.")
            
        return callee.call(self, arguments)

    def _visit_array_expr(self, expr: ArrayExpr) -> Any:
        return [self._evaluate(element) for element in expr.elements]

    def _visit_index_expr(self, expr: IndexExpr) -> Any:
        callee = self._evaluate(expr.callee)
        index = self._evaluate(expr.index)
        if not isinstance(callee, list):
            raise VyaumaRuntimeError(expr.bracket, "Can only index into arrays.")
        if not isinstance(index, int) or isinstance(index, bool):
            raise VyaumaRuntimeError(expr.bracket, "Array index must be an integer.")
        if index < 0 or index >= len(callee):
            raise VyaumaRuntimeError(expr.bracket, "Array index out of bounds.")
        return callee[index]

    def _visit_index_assign_expr(self, expr: IndexAssignExpr) -> Any:
        callee = self._evaluate(expr.callee)
        index = self._evaluate(expr.index)
        value = self._evaluate(expr.value)
        if not isinstance(callee, list):
            raise VyaumaRuntimeError(expr.bracket, "Can only index into arrays.")
        if not isinstance(index, int) or isinstance(index, bool):
            raise VyaumaRuntimeError(expr.bracket, "Array index must be an integer.")
        if index < 0 or index >= len(callee):
            raise VyaumaRuntimeError(expr.bracket, "Array index out of bounds.")
        callee[index] = value
        return value

    def _visit_object_expr(self, expr: ObjectExpr) -> Any:
        obj = {}
        for name, value_expr in expr.properties.items():
            obj[name.value] = self._evaluate(value_expr)
        return obj

    def _visit_property_access_expr(self, expr: PropertyAccessExpr) -> Any:
        callee = self._evaluate(expr.callee)
        
        if isinstance(callee, VyaumaInstance):
            return callee.get(expr.name)
            
        if not isinstance(callee, dict):
            raise VyaumaRuntimeError(expr.dot, "Only instances and objects have properties.")
        
        name = expr.name.value
        if name in callee:
            return callee[name]
        raise VyaumaRuntimeError(expr.name, f"Undefined property '{name}'.")

    def _visit_property_assign_expr(self, expr: PropertyAssignExpr) -> Any:
        callee = self._evaluate(expr.callee)
        value = self._evaluate(expr.value)
        
        if isinstance(callee, VyaumaInstance):
            callee.set(expr.name, value)
            return value
            
        if not isinstance(callee, dict):
            raise VyaumaRuntimeError(expr.dot, "Only instances and objects have properties.")
        
        callee[expr.name.value] = value
        return value

    def _visit_this_expr(self, expr: ThisExpr) -> Any:
        return self.environment.get(expr.keyword)
        
    def _visit_super_expr(self, expr: SuperExpr) -> Any:
        try:
            superclass = self.environment.get_by_name("super", expr.keyword)
            instance = self.environment.get_by_name("this", expr.keyword)
        except VyaumaRuntimeError:
            raise VyaumaRuntimeError(expr.keyword, "Cannot use 'super' outside of a subclass method.")
            
        method = superclass.find_method(expr.method.value)
        if method is None:
            raise VyaumaRuntimeError(expr.method, f"Undefined property '{expr.method.value}'.")
            
        return method.bind(instance)

    # ------------------------------------------------------------------ #
    # Helper Methods                                                       #
    # ------------------------------------------------------------------ #
    
    def _check_number_operand(self, operator: Token, operand: Any) -> None:
        if isinstance(operand, (int, float)) and not isinstance(operand, bool):
            return
        raise VyaumaRuntimeError(operator, "Operand must be a number.")

    def _check_number_operands(self, operator: Token, left: Any, right: Any) -> None:
        if isinstance(left, (int, float)) and not isinstance(left, bool):
            if isinstance(right, (int, float)) and not isinstance(right, bool):
                return
        raise VyaumaRuntimeError(operator, "Operands must be numbers.")

    def _is_truthy(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        return True
