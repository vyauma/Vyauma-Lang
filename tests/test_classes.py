import pytest
from src.lexer import Lexer
from src.parser.parser import Parser
from src.runtime.interpreter import Interpreter, VyaumaRuntimeError


def interpret_source(source: str, interpreter=None):
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    if interpreter is None:
        interpreter = Interpreter()
    interpreter.interpret(program)


class TestClasses:
    def test_class_declaration_and_instantiation(self, capsys):
        source = '''class Animal:
    func speak():
        print "Roar!"

let a = Animal()
a.speak()'''
        interpret_source(source)
        assert capsys.readouterr().out == "Roar!\n"
        
    def test_constructor_and_this(self, capsys):
        source = '''class Person:
    func init(name):
        this.name = name
        
    func greet():
        print "Hello, " + this.name
        
let p = Person("Vyauma")
p.greet()'''
        interpret_source(source)
        assert capsys.readouterr().out == "Hello, Vyauma\n"
        
    def test_inheritance(self, capsys):
        source = '''class Animal:
    func init(name):
        this.name = name
        
    func speak():
        print this.name + " makes a noise."
        
class Dog(Animal):
    func speak():
        print this.name + " barks."
        
class Cat(Animal):
    func purr():
        print this.name + " purrs."
        
let a = Animal("Generic")
let d = Dog("Rex")
let c = Cat("Whiskers")

a.speak()
d.speak()
c.speak()
c.purr()'''
        interpret_source(source)
        out = capsys.readouterr().out
        assert out == "Generic makes a noise.\nRex barks.\nWhiskers makes a noise.\nWhiskers purrs.\n"

    def test_invalid_property_access(self):
        source = '''class Test:
    func init():
        this.a = 1
let t = Test()
print t.b'''
        with pytest.raises(VyaumaRuntimeError, match="Undefined property 'b'."):
            interpret_source(source)

    def test_superclass_not_a_class(self):
        source = '''let NotAClass = "hello"
class Test(NotAClass):
    func foo():
        print "bar"'''
        with pytest.raises(VyaumaRuntimeError, match="Superclass must be a class."):
            interpret_source(source)
            
    def test_super_method(self, capsys):
        source = '''class A:
    func method():
        print "A method"
        
class B(A):
    func method():
        super.method()
        print "B method"
        
let b = B()
b.method()'''
        interpret_source(source)
        out = capsys.readouterr().out
        assert out == "A method\nB method\n"
        
    def test_super_init(self, capsys):
        source = '''class Animal:
    func init(name):
        this.name = name

class Dog(Animal):
    func init(name, breed):
        super.init(name)
        this.breed = breed
        
    func display():
        print this.name + " is a " + this.breed

let d = Dog("Rex", "German Shepherd")
d.display()'''
        interpret_source(source)
        out = capsys.readouterr().out
        assert out == "Rex is a German Shepherd\n"
        
    def test_super_outside_class(self):
        source = '''super.foo()'''
        with pytest.raises(VyaumaRuntimeError, match="Cannot use 'super' outside of a subclass method."):
            interpret_source(source)
