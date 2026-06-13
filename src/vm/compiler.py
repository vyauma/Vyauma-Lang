from src.parser import (
    Program, Expr, Stmt, LiteralExpr, BinaryExpr, UnaryExpr, GroupingExpr,
    PrintStmt, ExpressionStmt, LetStmt, VariableExpr, AssignExpr,
    BlockStmt, IfStmt, LoopStmt, FuncStmt, ReturnStmt, CallExpr,
    ClassStmt, PropertyAccessExpr, PropertyAssignExpr, ThisExpr, SuperExpr,
    ArrayExpr, IndexExpr, IndexAssignExpr, ObjectExpr
)
from src.lexer import TokenType
from .chunk import Chunk, VMFunction
from .opcode import OpCode
from dataclasses import dataclass

@dataclass
class Local:
    name: str
    depth: int
    is_captured: bool = False

@dataclass
class Upvalue:
    index: int
    is_local: bool

class Compiler:
    """
    Compiles an AST down to Bytecode instructions.
    """
    def __init__(self, enclosing: 'Compiler' = None, name: str = "<script>") -> None:
        self.enclosing = enclosing
        self.function = VMFunction(arity=0, upvalue_count=0, chunk=Chunk(), name=name)
        self.locals: list[Local] = [Local(name, 0)]
        self.upvalues: list[Upvalue] = []
        self.scope_depth: int = 0
        
    @property
    def chunk(self) -> Chunk:
        return self.function.chunk
        
    def begin_scope(self) -> None:
        self.scope_depth += 1
        
    def end_scope(self) -> None:
        self.scope_depth -= 1
        while len(self.locals) > 0 and self.locals[-1].depth > self.scope_depth:
            if self.locals[-1].is_captured:
                self.chunk.write(OpCode.CLOSE_UPVALUE, 0)
            else:
                self.chunk.write(OpCode.POP, 0)
            self.locals.pop()
            
    def resolve_local(self, name: str) -> int:
        for i in range(len(self.locals) - 1, -1, -1):
            if self.locals[i].name == name:
                return i
        return -1
        
    def resolve_upvalue(self, name: str) -> int:
        if self.enclosing is None:
            return -1
            
        local_idx = self.enclosing.resolve_local(name)
        if local_idx != -1:
            self.enclosing.locals[local_idx].is_captured = True
            return self.add_upvalue(local_idx, True)
            
        upvalue_idx = self.enclosing.resolve_upvalue(name)
        if upvalue_idx != -1:
            return self.add_upvalue(upvalue_idx, False)
            
        return -1
        
    def add_upvalue(self, index: int, is_local: bool) -> int:
        for i, uv in enumerate(self.upvalues):
            if uv.index == index and uv.is_local == is_local:
                return i
                
        self.upvalues.append(Upvalue(index, is_local))
        return len(self.upvalues) - 1

    def emit_jump(self, instruction: OpCode, line: int) -> int:
        self.chunk.write(instruction, line)
        self.chunk.write(0, line)
        return len(self.chunk.code) - 1
        
    def patch_jump(self, offset: int) -> None:
        jump = len(self.chunk.code) - offset - 1
        self.chunk.code[offset] = jump
        
    def emit_loop(self, loop_start: int, line: int) -> None:
        self.chunk.write(OpCode.LOOP, line)
        offset = len(self.chunk.code) - loop_start + 1
        self.chunk.write(offset, line)

    def compile(self, program: Program) -> VMFunction:
        for stmt in program.statements:
            self._compile_statement(stmt)
        self.chunk.write(OpCode.NULL, 0)
        self.chunk.write(OpCode.RETURN, 0)
        return self.function
        
    def _compile_statement(self, stmt: Stmt) -> None:
        if isinstance(stmt, ExpressionStmt):
            self._compile_expression(stmt.expression)
            self.chunk.write(OpCode.POP, 0)  # Expression statements pop their result
        elif isinstance(stmt, PrintStmt):
            self._compile_expression(stmt.expression)
            self.chunk.write(OpCode.PRINT, stmt.keyword.line)
        elif isinstance(stmt, LetStmt):
            if stmt.initializer:
                self._compile_expression(stmt.initializer)
            else:
                self.chunk.write(OpCode.NULL, stmt.name.line)
                
            if self.scope_depth > 0:
                self.locals.append(Local(stmt.name.value, self.scope_depth))
            else:
                idx = self.chunk.add_constant(stmt.name.value)
                self.chunk.write(OpCode.DEFINE_GLOBAL, stmt.name.line)
                self.chunk.write(idx, stmt.name.line)
        elif isinstance(stmt, FuncStmt):
            compiler = Compiler(enclosing=self, name=stmt.name.value)
            compiler.function.arity = len(stmt.params)
            
            compiler.begin_scope()
            for param in stmt.params:
                compiler.locals.append(Local(param.value, compiler.scope_depth))
                
            for s in stmt.body.statements:
                compiler._compile_statement(s)
                
            compiler.chunk.write(OpCode.NULL, stmt.name.line)
            compiler.chunk.write(OpCode.RETURN, stmt.name.line)
            
            compiler.function.upvalue_count = len(compiler.upvalues)
            func = compiler.function
            idx = self.chunk.add_constant(func)
            self.chunk.write(OpCode.CLOSURE, stmt.name.line)
            self.chunk.write(idx, stmt.name.line)
            
            for uv in compiler.upvalues:
                self.chunk.write(1 if uv.is_local else 0, stmt.name.line)
                self.chunk.write(uv.index, stmt.name.line)
            
            if self.scope_depth > 0:
                self.locals.append(Local(stmt.name.value, self.scope_depth))
            else:
                name_idx = self.chunk.add_constant(stmt.name.value)
                self.chunk.write(OpCode.DEFINE_GLOBAL, stmt.name.line)
                self.chunk.write(name_idx, stmt.name.line)
        elif isinstance(stmt, BlockStmt):
            self.begin_scope()
            for s in stmt.statements:
                self._compile_statement(s)
            self.end_scope()
        elif isinstance(stmt, IfStmt):
            self._compile_expression(stmt.condition)
            then_jump = self.emit_jump(OpCode.JUMP_IF_FALSE, stmt.keyword.line)
            
            self.chunk.write(OpCode.POP, stmt.keyword.line) # pop condition
            self._compile_statement(stmt.then_branch)
            
            else_jump = self.emit_jump(OpCode.JUMP, stmt.keyword.line)
            self.patch_jump(then_jump)
            self.chunk.write(OpCode.POP, stmt.keyword.line) # pop condition if false
            
            if stmt.else_branch:
                self._compile_statement(stmt.else_branch)
                
            self.patch_jump(else_jump)
            
        elif isinstance(stmt, LoopStmt):
            loop_start = len(self.chunk.code)
            self._compile_expression(stmt.condition)
            
            exit_jump = self.emit_jump(OpCode.JUMP_IF_FALSE, stmt.keyword.line)
            self.chunk.write(OpCode.POP, stmt.keyword.line)
            
            self._compile_statement(stmt.body)
            self.emit_loop(loop_start, stmt.keyword.line)
            
            self.patch_jump(exit_jump)
            self.chunk.write(OpCode.POP, stmt.keyword.line)
            
        elif isinstance(stmt, ReturnStmt):
            if stmt.value:
                self._compile_expression(stmt.value)
            else:
                self.chunk.write(OpCode.NULL, stmt.keyword.line)
            self.chunk.write(OpCode.RETURN, stmt.keyword.line)
            
        elif isinstance(stmt, ClassStmt):
            name_idx = self.chunk.add_constant(stmt.name.value)
            self.chunk.write(OpCode.CLASS, stmt.name.line)
            self.chunk.write(name_idx, stmt.name.line)
            
            if self.scope_depth > 0:
                self.locals.append(Local(stmt.name.value, self.scope_depth))
            else:
                self.chunk.write(OpCode.DEFINE_GLOBAL, stmt.name.line)
                self.chunk.write(name_idx, stmt.name.line)

            if stmt.superclass:
                if stmt.superclass.name.value == stmt.name.value:
                    raise Exception("A class can't inherit from itself.")
                self._compile_expression(stmt.superclass)
                self.begin_scope()
                self.locals.append(Local("super", self.scope_depth))

            if self.scope_depth > 0:
                idx = self.resolve_local(stmt.name.value)
                if idx != -1:
                    self.chunk.write(OpCode.GET_LOCAL, stmt.name.line)
                    self.chunk.write(idx, stmt.name.line)
                else:
                    idx = self.resolve_upvalue(stmt.name.value)
                    if idx != -1:
                        self.chunk.write(OpCode.GET_UPVALUE, stmt.name.line)
                        self.chunk.write(idx, stmt.name.line)
                    else:
                        self.chunk.write(OpCode.GET_GLOBAL, stmt.name.line)
                        self.chunk.write(name_idx, stmt.name.line)
            else:
                self.chunk.write(OpCode.GET_GLOBAL, stmt.name.line)
                self.chunk.write(name_idx, stmt.name.line)
                
            if stmt.superclass:
                self.chunk.write(OpCode.INHERIT, stmt.name.line)

            for method in stmt.methods:
                method_name_idx = self.chunk.add_constant(method.name.value)
                compiler = Compiler(enclosing=self, name=method.name.value)
                compiler.locals[0].name = "this"
                compiler.begin_scope()
                
                for param in method.params:
                    compiler.locals.append(Local(param.value, compiler.scope_depth))
                    
                for body_stmt in method.body.statements:
                    compiler._compile_statement(body_stmt)
                    
                compiler.chunk.write(OpCode.NULL, method.name.line)
                compiler.chunk.write(OpCode.RETURN, method.name.line)
                
                compiler.function.arity = len(method.params)
                compiler.function.upvalue_count = len(compiler.upvalues)
                
                idx = self.chunk.add_constant(compiler.function)
                self.chunk.write(OpCode.CLOSURE, method.name.line)
                self.chunk.write(idx, method.name.line)
                for uv in compiler.upvalues:
                    self.chunk.write(1 if uv.is_local else 0, method.name.line)
                    self.chunk.write(uv.index, method.name.line)
                    
                self.chunk.write(OpCode.METHOD, method.name.line)
                self.chunk.write(method_name_idx, method.name.line)
                
            self.chunk.write(OpCode.POP, stmt.name.line) # pop the class
            if stmt.superclass:
                self.end_scope()

        else:
            raise NotImplementedError(f"Compiler does not yet support statement: {type(stmt).__name__}")
            
    def _compile_expression(self, expr: Expr) -> None:
        if isinstance(expr, LiteralExpr):
            if expr.value is True:
                self.chunk.write(OpCode.TRUE, expr.token.line)
            elif expr.value is False:
                self.chunk.write(OpCode.FALSE, expr.token.line)
            elif expr.value is None:
                self.chunk.write(OpCode.NULL, expr.token.line)
            else:
                idx = self.chunk.add_constant(expr.value)
                self.chunk.write(OpCode.CONSTANT, expr.token.line)
                self.chunk.write(idx, expr.token.line)
                
        elif isinstance(expr, UnaryExpr):
            self._compile_expression(expr.right)
            if expr.operator.type == TokenType.MINUS:
                self.chunk.write(OpCode.NEGATE, expr.operator.line, expr.operator.column)
            else:
                raise NotImplementedError(f"Unary operator not supported in VM: {expr.operator.value}")
                
        elif isinstance(expr, BinaryExpr):
            self._compile_expression(expr.left)
            self._compile_expression(expr.right)
            
            op = expr.operator.type
            line = expr.operator.line
            col = expr.operator.column
            
            if op == TokenType.PLUS:
                self.chunk.write(OpCode.ADD, line, col)
            elif op == TokenType.MINUS:
                self.chunk.write(OpCode.SUBTRACT, line, col)
            elif op == TokenType.STAR:
                self.chunk.write(OpCode.MULTIPLY, line, col)
            elif op == TokenType.SLASH:
                self.chunk.write(OpCode.DIVIDE, line, col)
            elif op == TokenType.EQ:
                self.chunk.write(OpCode.EQUAL, line, col)
            elif op == TokenType.NEQ:
                self.chunk.write(OpCode.EQUAL, line, col)
                self.chunk.write(OpCode.NOT, line, col)
            elif op == TokenType.GT:
                self.chunk.write(OpCode.GREATER, line, col)
            elif op == TokenType.LT:
                self.chunk.write(OpCode.LESS, line, col)
            elif op == TokenType.GTE:
                self.chunk.write(OpCode.LESS, line, col)
                self.chunk.write(OpCode.NOT, line, col)
            elif op == TokenType.LTE:
                self.chunk.write(OpCode.GREATER, line, col)
                self.chunk.write(OpCode.NOT, line, col)
            else:
                raise NotImplementedError(f"Binary operator not supported in VM: {expr.operator.value}")
                
        elif isinstance(expr, GroupingExpr):
            self._compile_expression(expr.expression)
            
        elif isinstance(expr, VariableExpr):
            idx = self.resolve_local(expr.name.value)
            if idx != -1:
                self.chunk.write(OpCode.GET_LOCAL, expr.name.line, expr.name.column)
                self.chunk.write(idx, expr.name.line, expr.name.column)
            else:
                idx = self.resolve_upvalue(expr.name.value)
                if idx != -1:
                    self.chunk.write(OpCode.GET_UPVALUE, expr.name.line, expr.name.column)
                    self.chunk.write(idx, expr.name.line, expr.name.column)
                else:
                    idx = self.chunk.add_constant(expr.name.value)
                    self.chunk.write(OpCode.GET_GLOBAL, expr.name.line, expr.name.column)
                    self.chunk.write(idx, expr.name.line, expr.name.column)
                
        elif isinstance(expr, AssignExpr):
            self._compile_expression(expr.value)
            idx = self.resolve_local(expr.name.value)
            if idx != -1:
                self.chunk.write(OpCode.SET_LOCAL, expr.name.line, expr.name.column)
                self.chunk.write(idx, expr.name.line, expr.name.column)
            else:
                idx = self.resolve_upvalue(expr.name.value)
                if idx != -1:
                    self.chunk.write(OpCode.SET_UPVALUE, expr.name.line, expr.name.column)
                    self.chunk.write(idx, expr.name.line, expr.name.column)
                else:
                    idx = self.chunk.add_constant(expr.name.value)
                    self.chunk.write(OpCode.SET_GLOBAL, expr.name.line, expr.name.column)
                    self.chunk.write(idx, expr.name.line, expr.name.column)
                
        elif isinstance(expr, CallExpr):
            self._compile_expression(expr.callee)
            for arg in expr.arguments:
                self._compile_expression(arg)
            self.chunk.write(OpCode.CALL, expr.paren.line, expr.paren.column)
            self.chunk.write(len(expr.arguments), expr.paren.line, expr.paren.column)
            
        elif isinstance(expr, PropertyAccessExpr):
            self._compile_expression(expr.callee)
            name_idx = self.chunk.add_constant(expr.name.value)
            self.chunk.write(OpCode.GET_PROPERTY, expr.name.line, expr.name.column)
            self.chunk.write(name_idx, expr.name.line, expr.name.column)
            
        elif isinstance(expr, PropertyAssignExpr):
            self._compile_expression(expr.callee)
            self._compile_expression(expr.value)
            name_idx = self.chunk.add_constant(expr.name.value)
            self.chunk.write(OpCode.SET_PROPERTY, expr.name.line, expr.name.column)
            self.chunk.write(name_idx, expr.name.line, expr.name.column)
            
        elif isinstance(expr, ThisExpr):
            idx = self.resolve_local("this")
            if idx != -1:
                self.chunk.write(OpCode.GET_LOCAL, expr.keyword.line)
                self.chunk.write(idx, expr.keyword.line)
            else:
                idx = self.resolve_upvalue("this")
                if idx != -1:
                    self.chunk.write(OpCode.GET_UPVALUE, expr.keyword.line)
                    self.chunk.write(idx, expr.keyword.line)
                else:
                    raise Exception("Cannot use 'this' outside of a class.")
                    
        elif isinstance(expr, SuperExpr):
            idx = self.resolve_local("this")
            if idx != -1:
                self.chunk.write(OpCode.GET_LOCAL, expr.keyword.line)
                self.chunk.write(idx, expr.keyword.line)
            else:
                idx = self.resolve_upvalue("this")
                if idx != -1:
                    self.chunk.write(OpCode.GET_UPVALUE, expr.keyword.line)
                    self.chunk.write(idx, expr.keyword.line)
                else:
                    raise Exception("Cannot use 'super' outside of a class.")
                    
            idx = self.resolve_upvalue("super")
            if idx != -1:
                self.chunk.write(OpCode.GET_UPVALUE, expr.keyword.line)
                self.chunk.write(idx, expr.keyword.line)
            else:
                idx = self.resolve_local("super")
                if idx != -1:
                    self.chunk.write(OpCode.GET_LOCAL, expr.keyword.line)
                    self.chunk.write(idx, expr.keyword.line)
                else:
                    raise Exception("Cannot use 'super' outside of a class with a superclass.")
                    
            name_idx = self.chunk.add_constant(expr.method.value)
            self.chunk.write(OpCode.GET_SUPER, expr.keyword.line)
            self.chunk.write(name_idx, expr.keyword.line)
            
        elif isinstance(expr, ArrayExpr):
            for el in expr.elements:
                self._compile_expression(el)
            self.chunk.write(OpCode.BUILD_ARRAY, expr.bracket.line)
            self.chunk.write(len(expr.elements), expr.bracket.line)
            
        elif isinstance(expr, ObjectExpr):
            for key, val in expr.properties.items():
                # Emit the key as a constant
                key_idx = self.chunk.add_constant(key.value)
                self.chunk.write(OpCode.CONSTANT, key.line)
                self.chunk.write(key_idx, key.line)
                # Compile the value
                self._compile_expression(val)
            self.chunk.write(OpCode.BUILD_OBJECT, expr.brace.line)
            self.chunk.write(len(expr.properties), expr.brace.line)
            
        elif isinstance(expr, IndexExpr):
            self._compile_expression(expr.callee)
            self._compile_expression(expr.index)
            self.chunk.write(OpCode.INDEX_GET, expr.bracket.line, expr.bracket.column)
            
        elif isinstance(expr, IndexAssignExpr):
            self._compile_expression(expr.callee)
            self._compile_expression(expr.index)
            self._compile_expression(expr.value)
            self.chunk.write(OpCode.INDEX_SET, expr.bracket.line, expr.bracket.column)
                
        else:
            raise NotImplementedError(f"Compiler does not yet support expression: {type(expr).__name__}")
