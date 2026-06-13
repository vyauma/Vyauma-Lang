from enum import IntEnum, auto

class OpCode(IntEnum):
    """
    Instructions for the Vyauma Virtual Machine.
    """
    CONSTANT = auto()    # Load a constant from the constant pool
    TRUE = auto()        # Load boolean True
    FALSE = auto()       # Load boolean False
    NULL = auto()        # Load None (null)
    
    ADD = auto()         # Pop two values, push their sum
    SUBTRACT = auto()    # Pop two values, push their difference
    MULTIPLY = auto()    # Pop two values, push their product
    DIVIDE = auto()      # Pop two values, push their quotient
    NEGATE = auto()      # Pop one value, push its negation
    
    EQUAL = auto()       # Pop two values, push if they are equal
    GREATER = auto()     # Pop two values, push if a > b
    LESS = auto()        # Pop two values, push if a < b
    NOT = auto()         # Pop one value, push its boolean negation
    
    PRINT = auto()       # Pop one value and print it
    POP = auto()         # Pop one value and discard it
    
    DEFINE_GLOBAL = auto() # Pop a value and bind it to a global variable
    GET_GLOBAL = auto()    # Push the value of a global variable
    SET_GLOBAL = auto()    # Set the value of a global variable (leaves value on stack)
    
    GET_LOCAL = auto()     # Push the value of a local variable from the stack
    SET_LOCAL = auto()     # Set the value of a local variable on the stack
    
    JUMP = auto()          # Unconditional forward jump
    JUMP_IF_FALSE = auto() # Jump forward if top of stack is false
    LOOP = auto()          # Unconditional backward jump
    
    CALL = auto()          # Call a function
    CLOSURE = auto()       # Create a closure
    
    GET_UPVALUE = auto()   # Push value of upvalue
    SET_UPVALUE = auto()   # Set value of upvalue
    CLOSE_UPVALUE = auto() # Close an upvalue
    
    CLASS = auto()         # Create a class
    METHOD = auto()        # Define a method
    GET_PROPERTY = auto()  # Get object property
    SET_PROPERTY = auto()  # Set object property
    INHERIT = auto()       # Inherit methods from superclass
    GET_SUPER = auto()     # Get superclass method
    
    BUILD_ARRAY = auto()   # Build an array
    BUILD_OBJECT = auto()  # Build an object/dictionary
    INDEX_GET = auto()     # Get item at index/key
    INDEX_SET = auto()     # Set item at index/key
    
    RETURN = auto()      # Return from the current frame
