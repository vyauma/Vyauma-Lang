# Vyauma Syntax Guide

This guide introduces the beginner-friendly syntax of the Vyauma language.  
Vyauma aims to be simple, readable, and easy to learn.

> **Note**: Features marked **(planned)** are not yet implemented. They describe syntax being designed for future versions.

---

## 1. Printing Output

The `print` statement writes text to the screen.

```
print "Hello, world!"
```

Use either double quotes or single quotes — both work:

```
print "Hello!"
print 'Hello!'
```

Run your first program:

```bash
python src/cli/vyauma.py run hello.vym
```

Output:

```
Hello!
```

---

## 2. Comments

Use `#` to write a comment. The interpreter ignores everything after `#` on that line.

```
# This line is a comment and does nothing
print "Vyauma"   # This prints Vyauma
```

Comments are great for explaining your code to yourself and others.

---

## 3. Variables *(planned)*

Variables store values so you can use them later.  
Use the `let` keyword to create a variable:

```
let name = "Vyauma"
let age = 3
let score = 9.5
```

Print a variable:

```
let language = "Vyauma"
print language
```

Output:

```
Vyauma
```

Variable names:
- Must start with a letter or `_`
- Can contain letters, digits, and underscores
- Are case-sensitive (`Name` and `name` are different)

---

## 4. Data Types *(planned)*

Vyauma supports four basic types:

| Type | Example | Description |
|---|---|---|
| String | `"hello"` | Text in quotes |
| Integer | `42` | Whole numbers |
| Float | `3.14` | Decimal numbers |
| Boolean | `true` / `false` | True or false values |

---

## 5. Arithmetic *(planned)*

Use standard operators to do math:

```
let a = 10
let b = 3

print a + b    # 13
print a - b    # 7
print a * b    # 30
print a / b    # 3.333...
```

| Operator | Meaning | Example |
|---|---|---|
| `+` | Add | `1 + 2` |
| `-` | Subtract | `5 - 3` |
| `*` | Multiply | `4 * 3` |
| `/` | Divide | `10 / 2` |

---

## 6. Conditions *(planned)*

Use `if` and `else` to make decisions:

```
let score = 75

if score >= 50:
    print "You passed!"
else:
    print "Try again."
```

### Comparison Operators

| Operator | Meaning |
|---|---|
| `==` | Equal to |
| `!=` | Not equal to |
| `<` | Less than |
| `>` | Greater than |
| `<=` | Less than or equal |
| `>=` | Greater than or equal |

---

## 7. Loops *(planned)*

Repeat a block of code using `loop`:

```
let i = 1

loop i <= 5:
    print i
    let i = i + 1
```

Output:

```
1
2
3
4
5
```

The loop runs as long as the condition after `loop` is `true`.

---

## 8. Functions *(planned)*

Group reusable code into a function using `func`:

```
func greet(name):
    print "Hello, " + name

greet("Vyauma")
```

Output:

```
Hello, Vyauma
```

Return a value with `return`:

```
func add(a, b):
    return a + b

let result = add(3, 7)
print result
```

Output:

```
10
```

---

## 9. Quick Reference

| Feature | Syntax | Status |
|---|---|---|
| Print | `print "text"` | ✅ Implemented |
| Comment | `# comment` | ✅ Implemented |
| Variable | `let x = value` | Planned |
| If/else | `if cond:` / `else:` | Planned |
| Loop | `loop cond:` | Planned |
| Function | `func name(params):` | Planned |

---

## 10. Running Your Code

Save your code in a file with the `.vym` extension, then run it:

```bash
python src/cli/vyauma.py run myprogram.vym
```

See the [`docs/examples/`](examples/) folder for ready-to-run programs.

For the full formal rules, refer to the [Language Specification](specification.md).
