"""
environment.py — Variable storage for the Vyauma Runtime.
"""

from typing import Any, Dict

from src.lexer import Token
from .interpreter import VyaumaRuntimeError


class Environment:
    """Stores bindings between variable names and their values."""
    def __init__(self, enclosing: "Environment | None" = None) -> None:
        self.values: Dict[str, Any] = {}
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
