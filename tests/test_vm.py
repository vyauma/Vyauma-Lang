import pytest
from src.lexer import Lexer
from src.parser import Parser
from src.vm.compiler import Compiler
from src.vm.vm import VM, VMError
import textwrap

def interpret_vm(source: str):
    source = textwrap.dedent(source).strip() + "\n"
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    compiler = Compiler()
    chunk = compiler.compile(program)
    vm = VM()
    vm.interpret(chunk)


class TestVM:
    def test_arithmetic(self, capsys):
        interpret_vm("print 1 + 2 * 3")
        assert capsys.readouterr().out == "7\n"
        
        interpret_vm("print (1 + 2) * 3")
        assert capsys.readouterr().out == "9\n"
        
        interpret_vm("print 10 / 2 - 1")
        assert capsys.readouterr().out == "4.0\n"

    def test_comparisons(self, capsys):
        interpret_vm("print 5 > 3")
        assert capsys.readouterr().out == "true\n"
        
        interpret_vm("print 5 < 3")
        assert capsys.readouterr().out == "false\n"
        
        interpret_vm("print 5 == 5")
        assert capsys.readouterr().out == "true\n"
        
        interpret_vm("print 5 != 3")
        assert capsys.readouterr().out == "true\n"

    def test_types(self, capsys):
        interpret_vm("print true")
        assert capsys.readouterr().out == "true\n"
        
        interpret_vm("print false")
        assert capsys.readouterr().out == "false\n"
        
        interpret_vm("print -10")
        assert capsys.readouterr().out == "-10\n"

    def test_string_concat(self, capsys):
        interpret_vm('print "hello" + " world"')
        assert capsys.readouterr().out == "hello world\n"
        
    def test_type_error(self, capsys):
        with pytest.raises(VMError):
            interpret_vm('print 5 + "hello"')

    def test_global_variables(self, capsys):
        interpret_vm('''
        let a = "global"
        print a
        a = "changed"
        print a
        ''')
        out = capsys.readouterr().out
        assert out == "global\nchanged\n"
        
    def test_local_variables_and_scopes(self, capsys):
        interpret_vm('''
        let a = "global"
        if true:
            let a = "outer"
            let b = "local"
            if true:
                let a = "inner"
                print a
                print b
            print a
        print a
        ''')
        out = capsys.readouterr().out
        assert out == "inner\nlocal\nouter\nglobal\n"

    def test_if_else(self, capsys):
        interpret_vm('''
        if true:
            print "yes"
        else:
            print "no"
            
        if false:
            print "yes"
        else:
            print "no"
        ''')
        out = capsys.readouterr().out
        assert out == "yes\nno\n"
        
    def test_loop(self, capsys):
        interpret_vm('''
        let i = 0
        loop i < 3:
            print i
            i = i + 1
        ''')
        out = capsys.readouterr().out
        assert out == "0\n1\n2\n"

    def test_functions(self, capsys):
        interpret_vm('''
        func add(a, b):
            return a + b
            
        print add(5, 3)
        ''')
        out = capsys.readouterr().out
        assert out == "8\n"
        
    def test_recursion(self, capsys):
        interpret_vm('''
        func fib(n):
            if n < 2:
                return n
            return fib(n - 1) + fib(n - 2)
            
        print fib(5)
        ''')
        out = capsys.readouterr().out
        assert out == "5\n"
        
    def test_lexical_scoping(self, capsys):
        interpret_vm('''
        let x = "global"
        func outer():
            let x = "outer"
            func inner():
                print x
            inner()
            
        outer()
        ''')
        out = capsys.readouterr().out
        assert out == "outer\n"

    def test_closures(self, capsys):
        interpret_vm('''
        func makeClosure():
            let local = "local"
            func closure():
                print local
            return closure
            
        let closure = makeClosure()
        closure()
        ''')
        out = capsys.readouterr().out
        assert out == "local\n"

    def test_classes(self, capsys):
        interpret_vm('''
        class Person:
            func dummy():
                print 1
        let p = Person()
        print p
        ''')
        out = capsys.readouterr().out
        assert "VMInstance" in out
        
    def test_properties(self, capsys):
        interpret_vm('''
        class Person:
            func dummy():
                print 1
        let p = Person()
        p.name = "vyauma"
        p.age = 25
        print p.name
        print p.age
        ''')
        out = capsys.readouterr().out
        assert out == "vyauma\n25\n"
        
    def test_methods_and_this(self, capsys):
        interpret_vm('''
        class Person:
            func init(name, age):
                this.name = name
                this.age = age
            func introduce():
                print "Hi, I am " + this.name
        
        let p = Person()
        p.init("vyauma", 25)
        p.introduce()
        ''')
        out = capsys.readouterr().out
        assert out == "Hi, I am vyauma\n"

    def test_inheritance(self, capsys):
        interpret_vm('''
        class Animal:
            func speak():
                print "Roar!"
        
        class Dog(Animal):
            func dummy():
                print 1
            
        let d = Dog()
        d.speak()
        ''')
        out = capsys.readouterr().out
        assert out == "Roar!\n"
        
    def test_super(self, capsys):
        interpret_vm('''
        class A:
            func method():
                print "A method"
                
        class B(A):
            func method():
                print "B method"
                super.method()
                
        class C(B):
            func method():
                print "C method"
                super.method()
                
        let c = C()
        c.method()
        ''')
        out = capsys.readouterr().out
        assert out == "C method\nB method\nA method\n"

    def test_arrays(self, capsys):
        interpret_vm('''
        let arr = [1, 2, 3]
        print arr[0]
        print arr[2]
        arr[1] = 42
        print arr[1]
        ''')
        out = capsys.readouterr().out
        assert out == "1\n3\n42\n"
        
    def test_dictionaries(self, capsys):
        interpret_vm('''
        let obj = { name: "vyauma", age: 25 }
        print obj["name"]
        obj["age"] = 26
        print obj["age"]
        ''')
        out = capsys.readouterr().out
        assert out == "vyauma\n26\n"
        
    def test_stdlib(self, capsys):
        interpret_vm('''
        let s = "hello"
        let arr = [1, 2, 3]
        let obj = {a: 1}
        print len(s)
        print len(arr)
        print len(obj)
        print str(true)
        print int("42")
        print float("3.14")
        print type(s)
        print type(arr)
        print type(true)
        ''')
        out = capsys.readouterr().out
        assert out == "5.0\n3.0\n1.0\ntrue\n42.0\n3.14\nstring\narray\nboolean\n"
        

