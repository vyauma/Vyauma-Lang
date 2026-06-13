import sys
from typing import Any
from dataclasses import dataclass
from .chunk import Chunk, VMFunction, VMClosure, Upvalue, VMClass, VMInstance, VMBoundMethod, VMNativeFunction
from .opcode import OpCode

class VMError(Exception):
    """Exception raised for runtime errors during VM execution."""
    def __init__(self, message: str, line: int = 1, col: int = 1) -> None:
        super().__init__(f"VMError: {message}")
        self.line = line
        self.col = col

@dataclass
class CallFrame:
    closure: VMClosure
    ip: int
    slot_offset: int

class VM:
    """
    The stack-based Virtual Machine that executes bytecode.
    """
    def __init__(self) -> None:
        self.frames: list[CallFrame] = []
        self.stack: list[Any] = []
        self.globals: dict[str, Any] = {}
        self.open_upvalues: list[Upvalue] = []
        self._define_natives()
        
    def _define_natives(self) -> None:
        def native_len(obj):
            if isinstance(obj, (str, list, dict)):
                return float(len(obj))
            raise VMError("Type error: 'len' requires a string, array, or dictionary.")
            
        def native_str(obj):
            if isinstance(obj, bool):
                return "true" if obj else "false"
            if obj is None:
                return "null"
            return str(obj)
            
        def native_int(obj):
            try:
                return float(int(obj))
            except (ValueError, TypeError):
                raise VMError(f"Cannot convert '{obj}' to int.")
                
        def native_float(obj):
            try:
                return float(obj)
            except (ValueError, TypeError):
                raise VMError(f"Cannot convert '{obj}' to float.")
                
        def native_type(obj):
            if isinstance(obj, str): return "string"
            if isinstance(obj, bool): return "boolean"
            if isinstance(obj, (int, float)): return "number"
            if isinstance(obj, list): return "array"
            if isinstance(obj, dict): return "dictionary"
            if isinstance(obj, VMInstance): return obj.klass.name
            if obj is None: return "null"
            return "function"
            
        def native_input(prompt=""):
            return input(prompt)
            
        self.globals["len"] = VMNativeFunction("len", 1, native_len)
        self.globals["str"] = VMNativeFunction("str", 1, native_str)
        self.globals["int"] = VMNativeFunction("int", 1, native_int)
        self.globals["float"] = VMNativeFunction("float", 1, native_float)
        self.globals["type"] = VMNativeFunction("type", 1, native_type)
        self.globals["input"] = VMNativeFunction("input", 1, native_input)
        
    def interpret(self, function: VMFunction) -> None:
        closure = VMClosure(function)
        self.frames = [CallFrame(closure=closure, ip=0, slot_offset=0)]
        self.stack = [closure]
        self.open_upvalues = []
        self._run()
        
    def capture_upvalue(self, location: int) -> Upvalue:
        for upvalue in self.open_upvalues:
            if upvalue.location == location:
                return upvalue
        created_upvalue = Upvalue(location)
        self.open_upvalues.append(created_upvalue)
        return created_upvalue

    def close_upvalues(self, last: int) -> None:
        to_keep = []
        for uv in self.open_upvalues:
            if uv.location >= last:
                uv.closed = self.stack[uv.location]
                uv.is_closed = True
            else:
                to_keep.append(uv)
        self.open_upvalues = to_keep

    def _run(self) -> None:
        try:
            while True:
                frame = self.frames[-1]
                instruction = frame.closure.function.chunk.code[frame.ip]
                frame.ip += 1
                
                if instruction == OpCode.RETURN:
                    result = self.stack.pop()
                    self.close_upvalues(frame.slot_offset)
                    
                    # pop the current frame
                    frame = self.frames.pop()
                    if len(self.frames) == 0:
                        # we finished the top-level script
                        self.stack.pop() # pop top level function
                        return
                    
                    # shrink the stack down to where the arguments were
                    self.stack = self.stack[:frame.slot_offset]
                    self.stack.append(result)
                
                elif instruction == OpCode.CONSTANT:
                    constant_idx = frame.closure.function.chunk.code[frame.ip]
                    frame.ip += 1
                    value = frame.closure.function.chunk.constants[constant_idx]
                    self.stack.append(value)
                    
                elif instruction == OpCode.TRUE:
                    self.stack.append(True)
                    
                elif instruction == OpCode.FALSE:
                    self.stack.append(False)
                    
                elif instruction == OpCode.NULL:
                    self.stack.append(None)
                    
                elif instruction == OpCode.ADD:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    if isinstance(a, str) and isinstance(b, str):
                        self.stack.append(a + b)
                    elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
                        self.stack.append(a + b)
                    else:
                        raise VMError("Operands must be two numbers or two strings.")
                        
                elif instruction == OpCode.SUBTRACT:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self.stack.append(a - b)
                    
                elif instruction == OpCode.MULTIPLY:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self.stack.append(a * b)
                    
                elif instruction == OpCode.DIVIDE:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    if b == 0:
                        raise VMError("Division by zero.")
                    self.stack.append(a / b)
                    
                elif instruction == OpCode.NEGATE:
                    a = self.stack.pop()
                    self.stack.append(-a)
                    
                elif instruction == OpCode.EQUAL:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self.stack.append(a == b)
                    
                elif instruction == OpCode.GREATER:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self.stack.append(a > b)
                    
                elif instruction == OpCode.LESS:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self.stack.append(a < b)
                    
                elif instruction == OpCode.NOT:
                    a = self.stack.pop()
                    self.stack.append(not self._is_truthy(a))
                    
                elif instruction == OpCode.PRINT:
                    value = self.stack.pop()
                    if isinstance(value, bool):
                        print("true" if value else "false")
                    elif value is None:
                        print("null")
                    else:
                        print(value)
                        
                elif instruction == OpCode.POP:
                    self.stack.pop()
                    
                elif instruction == OpCode.DEFINE_GLOBAL:
                    name_idx = frame.closure.function.chunk.code[frame.ip]
                    frame.ip += 1
                    name = frame.closure.function.chunk.constants[name_idx]
                    self.globals[name] = self.stack.pop()
                    
                elif instruction == OpCode.GET_GLOBAL:
                    name_idx = frame.closure.function.chunk.code[frame.ip]
                    frame.ip += 1
                    name = frame.closure.function.chunk.constants[name_idx]
                    if name not in self.globals:
                        raise VMError(f"Undefined variable '{name}'.")
                    self.stack.append(self.globals[name])
                    
                elif instruction == OpCode.SET_GLOBAL:
                    name_idx = frame.closure.function.chunk.code[frame.ip]
                    frame.ip += 1
                    name = frame.closure.function.chunk.constants[name_idx]
                    if name not in self.globals:
                        raise VMError(f"Undefined variable '{name}'.")
                    self.globals[name] = self.stack[-1]
                    
                elif instruction == OpCode.GET_LOCAL:
                    slot = frame.closure.function.chunk.code[frame.ip]
                    frame.ip += 1
                    self.stack.append(self.stack[frame.slot_offset + slot])
                    
                elif instruction == OpCode.SET_LOCAL:
                    slot = frame.closure.function.chunk.code[frame.ip]
                    frame.ip += 1
                    self.stack[frame.slot_offset + slot] = self.stack[-1]
                    
                elif instruction == OpCode.JUMP:
                    offset = frame.closure.function.chunk.code[frame.ip]
                    frame.ip += 1
                    frame.ip += offset
                    
                elif instruction == OpCode.JUMP_IF_FALSE:
                    offset = frame.closure.function.chunk.code[frame.ip]
                    frame.ip += 1
                    if not self._is_truthy(self.stack[-1]):
                        frame.ip += offset
                        
                elif instruction == OpCode.LOOP:
                    offset = frame.closure.function.chunk.code[frame.ip]
                    frame.ip += 1
                    frame.ip -= offset
                    
                elif instruction == OpCode.CALL:
                    arg_count = frame.closure.function.chunk.code[frame.ip]
                    frame.ip += 1
                    callee = self.stack[-1 - arg_count]
                    
                    if isinstance(callee, VMClass):
                        instance = VMInstance(callee)
                        self.stack[-1 - arg_count] = instance
                        if arg_count != 0:
                            raise VMError(f"Expected 0 arguments but got {arg_count}.")
                            
                    elif isinstance(callee, VMBoundMethod):
                        self.stack[-1 - arg_count] = callee.receiver
                        if arg_count != callee.method.function.arity:
                            raise VMError(f"Expected {callee.method.function.arity} arguments but got {arg_count}.")
                        new_frame = CallFrame(
                            closure=callee.method,
                            ip=0,
                            slot_offset=len(self.stack) - arg_count - 1
                        )
                        self.frames.append(new_frame)
                        
                    elif isinstance(callee, VMClosure):
                        if arg_count != callee.function.arity:
                            raise VMError(f"Expected {callee.function.arity} arguments but got {arg_count}.")
                        new_frame = CallFrame(
                            closure=callee,
                            ip=0,
                            slot_offset=len(self.stack) - arg_count - 1
                        )
                        self.frames.append(new_frame)
                        
                    elif isinstance(callee, VMNativeFunction):
                        if arg_count != callee.arity and callee.arity != -1:
                            raise VMError(f"Expected {callee.arity} arguments but got {arg_count}.")
                        
                        args = self.stack[-arg_count:] if arg_count > 0 else []
                        try:
                            result = callee.function(*args)
                        except Exception as e:
                            if isinstance(e, VMError):
                                raise
                            raise VMError(str(e))
                            
                        self.stack = self.stack[:len(self.stack) - arg_count - 1]
                        self.stack.append(result)
                        
                    else:
                        raise VMError("Can only call functions and classes.")
                    
                elif instruction == OpCode.CLOSURE:
                    constant_idx = frame.closure.function.chunk.code[frame.ip]
                    frame.ip += 1
                    function = frame.closure.function.chunk.constants[constant_idx]
                    
                    upvalues = []
                    for _ in range(function.upvalue_count):
                        is_local = frame.closure.function.chunk.code[frame.ip]
                        frame.ip += 1
                        index = frame.closure.function.chunk.code[frame.ip]
                        frame.ip += 1
                        
                        if is_local == 1:
                            upvalues.append(self.capture_upvalue(frame.slot_offset + index))
                        else:
                            upvalues.append(frame.closure.upvalues[index])
                            
                    closure = VMClosure(function, upvalues)
                    self.stack.append(closure)
                    
                elif instruction == OpCode.GET_UPVALUE:
                    index = frame.closure.function.chunk.code[frame.ip]
                    frame.ip += 1
                    uv = frame.closure.upvalues[index]
                    if uv.is_closed:
                        self.stack.append(uv.closed)
                    else:
                        self.stack.append(self.stack[uv.location])
                        
                elif instruction == OpCode.SET_UPVALUE:
                    index = frame.closure.function.chunk.code[frame.ip]
                    frame.ip += 1
                    uv = frame.closure.upvalues[index]
                    if uv.is_closed:
                        uv.closed = self.stack[-1]
                    else:
                        self.stack[uv.location] = self.stack[-1]
                        
                elif instruction == OpCode.CLOSE_UPVALUE:
                    self.close_upvalues(len(self.stack) - 1)
                    self.stack.pop()
                    
                elif instruction == OpCode.CLASS:
                    constant_idx = frame.closure.function.chunk.code[frame.ip]
                    frame.ip += 1
                    name = frame.closure.function.chunk.constants[constant_idx]
                    self.stack.append(VMClass(name))
                    
                elif instruction == OpCode.METHOD:
                    constant_idx = frame.closure.function.chunk.code[frame.ip]
                    frame.ip += 1
                    name = frame.closure.function.chunk.constants[constant_idx]
                    method = self.stack.pop()
                    klass = self.stack[-1]
                    klass.methods[name] = method
                    
                elif instruction == OpCode.GET_PROPERTY:
                    constant_idx = frame.closure.function.chunk.code[frame.ip]
                    frame.ip += 1
                    name = frame.closure.function.chunk.constants[constant_idx]
                    
                    instance = self.stack[-1]
                    if isinstance(instance, VMInstance):
                        if name in instance.fields:
                            self.stack.pop() # pop instance
                            self.stack.append(instance.fields[name])
                        elif name in instance.klass.methods:
                            self.stack.pop() # pop instance
                            bound = VMBoundMethod(instance, instance.klass.methods[name])
                            self.stack.append(bound)
                        else:
                            raise VMError(f"Undefined property '{name}'.")
                    else:
                        raise VMError("Only instances have properties.")
                        
                elif instruction == OpCode.SET_PROPERTY:
                    constant_idx = frame.closure.function.chunk.code[frame.ip]
                    frame.ip += 1
                    name = frame.closure.function.chunk.constants[constant_idx]
                    
                    value = self.stack.pop()
                    instance = self.stack[-1]
                    
                    if isinstance(instance, VMInstance):
                        instance.fields[name] = value
                        self.stack.pop() # pop instance
                        self.stack.append(value)
                    else:
                        raise VMError("Only instances have fields.")
                        
                elif instruction == OpCode.INHERIT:
                    superclass = self.stack[-2]
                    subclass = self.stack[-1]
                    if not isinstance(superclass, VMClass):
                        raise VMError("Superclass must be a class.")
                    subclass.methods.update(superclass.methods)
                    
                elif instruction == OpCode.GET_SUPER:
                    constant_idx = frame.closure.function.chunk.code[frame.ip]
                    frame.ip += 1
                    name = frame.closure.function.chunk.constants[constant_idx]
                    
                    superclass = self.stack.pop()
                    instance = self.stack.pop()
                    
                    if not isinstance(superclass, VMClass):
                        raise VMError("Superclass must be a class.")
                        
                    if name not in superclass.methods:
                        raise VMError(f"Undefined property '{name}'.")
                        
                    bound = VMBoundMethod(instance, superclass.methods[name])
                    self.stack.append(bound)
                    
                elif instruction == OpCode.BUILD_ARRAY:
                    length = frame.closure.function.chunk.code[frame.ip]
                    frame.ip += 1
                    
                    arr = []
                    for _ in range(length):
                        arr.insert(0, self.stack.pop())
                    
                    self.stack.append(arr)
                    
                elif instruction == OpCode.BUILD_OBJECT:
                    length = frame.closure.function.chunk.code[frame.ip]
                    frame.ip += 1
                    
                    obj = {}
                    items = []
                    for _ in range(length):
                        val = self.stack.pop()
                        key = self.stack.pop()
                        items.insert(0, (key, val))
                        
                    for key, val in items:
                        obj[key] = val
                        
                    self.stack.append(obj)
                    
                elif instruction == OpCode.INDEX_GET:
                    index = self.stack.pop()
                    target = self.stack.pop()
                    
                    if isinstance(target, list):
                        if not isinstance(index, (int, float)):
                            raise VMError("Array index must be a number.")
                        index = int(index)
                        if index < 0 or index >= len(target):
                            raise VMError("Array index out of bounds.")
                        self.stack.append(target[index])
                    elif isinstance(target, dict):
                        if index not in target:
                            raise VMError(f"Key '{index}' not found in dictionary.")
                        self.stack.append(target[index])
                    else:
                        raise VMError("Can only index into arrays and dictionaries.")
                        
                elif instruction == OpCode.INDEX_SET:
                    value = self.stack.pop()
                    index = self.stack.pop()
                    target = self.stack.pop()
                    
                    if isinstance(target, list):
                        if not isinstance(index, (int, float)):
                            raise VMError("Array index must be a number.")
                        index = int(index)
                        if index < 0 or index >= len(target):
                            raise VMError("Array index out of bounds.")
                        target[index] = value
                        self.stack.append(value)
                    elif isinstance(target, dict):
                        target[index] = value
                        self.stack.append(value)
                    else:
                        raise VMError("Can only set items in arrays and dictionaries.")
                        
                else:
                    raise VMError(f"Unknown instruction: {instruction}")
        except VMError as e:
            if getattr(e, 'line', 1) == 1:
                frame = self.frames[-1]
                ip = frame.ip - 1
                if 0 <= ip < len(frame.closure.function.chunk.lines):
                    e.line = frame.closure.function.chunk.lines[ip]
                    e.col = frame.closure.function.chunk.cols[ip]
            raise
                

    def _is_truthy(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        return True
