from typing import Any
from dataclasses import dataclass, field
from .opcode import OpCode

@dataclass
class VMFunction:
    """A compiled function."""
    arity: int
    upvalue_count: int
    chunk: 'Chunk'
    name: str

class Upvalue:
    """A runtime upvalue tracking a local variable."""
    def __init__(self, location: int) -> None:
        self.location = location
        self.closed: Any = None
        self.is_closed = False

@dataclass
class VMClosure:
    """A runtime closure wrapping a VMFunction and its captured upvalues."""
    function: VMFunction
    upvalues: list[Upvalue] = field(default_factory=list)

class VMClass:
    """A runtime class."""
    def __init__(self, name: str) -> None:
        self.name = name
        self.methods: dict[str, VMClosure] = {}

class VMInstance:
    """A runtime instance of a class."""
    def __init__(self, klass: VMClass) -> None:
        self.klass = klass
        self.fields: dict[str, Any] = {}

class VMBoundMethod:
    """A method bound to an instance."""
    def __init__(self, receiver: Any, method: VMClosure) -> None:
        self.receiver = receiver
        self.method = method

class VMNativeFunction:
    """A native function provided by the runtime environment."""
    def __init__(self, name: str, arity: int, function: callable) -> None:
        self.name = name
        self.arity = arity
        self.function = function

class Chunk:
    """
    A chunk of bytecode instructions and their associated constants.
    """
    def __init__(self) -> None:
        self.code: list[int] = []
        self.constants: list[Any] = []
        self.lines: list[int] = []
        self.cols: list[int] = []
        
    def write(self, byte: int, line: int, col: int = 1) -> None:
        """Write a single byte (OpCode or operand) to the chunk."""
        self.code.append(byte)
        self.lines.append(line)
        self.cols.append(col)
        
    def add_constant(self, value: Any) -> int:
        """Add a constant to the constant pool and return its index."""
        self.constants.append(value)
        return len(self.constants) - 1
