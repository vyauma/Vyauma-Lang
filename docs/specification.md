# Vyauma Language Specification (Draft)

This document defines the core rules, grammar, and execution model of the Vyauma programming language.

Vyauma is designed for universal compatibility across devices and architectures, prioritizing readability, minimalism, and deterministic execution.

> **Status**: This is a living draft. Sections marked **(planned)** describe features not yet implemented.

---

## Table of Contents

1. [Lexical Structure](#1-lexical-structure)
2. [Data Types](#2-data-types)
3. [Statements](#3-statements)
4. [Variables (planned)](#4-variables-planned)
5. [Expressions (planned)](#5-expressions-planned)
6. [Control Flow (planned)](#6-control-flow-planned)
7. [Functions (planned)](#7-functions-planned)
8. [Comments](#8-comments)
9. [File Format](#9-file-format)
10. [Execution Model](#10-execution-model)
11. [Error Handling](#11-error-handling)

---

## 1. Lexical Structure

### 1.1 Identifiers

- Must start with a letter (`a–z`, `A–Z`) or an underscore (`_`).
- May contain letters, digits (`0–9`), and underscores.
- Case-sensitive: `myVar` and `myvar` are different identifiers.
- Must not be a reserved keyword (see §1.4).

**Valid identifiers:**

```
x
_count
myVariable
total_score2
```

**Invalid identifiers:**

```
2fast       # starts with a digit
my-var      # hyphens are not allowed
```

### 1.2 Literals

#### String literals

Enclosed in matching double quotes (`"`) or single quotes (`'`).

```
"Hello, world!"
'Vyauma'
```

Escape sequences **(planned)**:

| Sequence | Meaning |
|---|---|
| `\n` | Newline |
| `\t` | Tab |
| `\\` | Literal backslash |
| `\"` | Literal double-quote |
| `\'` | Literal single-quote |

#### Integer literals **(planned)**

Sequences of decimal digits:

```
0
42
1000
```

#### Float literals **(planned)**

Decimal number with a fractional part:

```
3.14
0.5
```

#### Boolean literals **(planned)**

```
true
false
```

### 1.3 Whitespace and Line Endings

- Whitespace (spaces and tabs) is ignored except where it separates tokens.
- Statements are terminated by a newline.
- Blank lines are ignored.
- Both Unix (`\n`) and Windows (`\r\n`) line endings are accepted.

### 1.4 Reserved Keywords

The following words are reserved and cannot be used as identifiers:

| Keyword | Purpose |
|---|---|
| `print` | Output statement |
| `let` | Variable declaration *(planned)* |
| `if` | Conditional branch *(planned)* |
| `else` | Alternative branch *(planned)* |
| `loop` | Loop construct *(planned)* |
| `func` | Function definition *(planned)* |
| `return` | Return from function *(planned)* |
| `true` | Boolean true *(planned)* |
| `false` | Boolean false *(planned)* |

### 1.5 Comments

Single-line comments begin with `#`. Everything after `#` on that line is ignored.

```
# This is a comment
print "hello"  # inline comment
```

---

## 2. Data Types

| Type | Description | Status |
|---|---|---|
| `String` | A sequence of characters | ✅ Implemented |
| `Integer` | Whole numbers | Planned |
| `Float` | Decimal numbers | Planned |
| `Boolean` | `true` or `false` | Planned |

---

## 3. Statements

### 3.1 `print` Statement

Outputs a value to standard output followed by a newline.

**Syntax:**

```
print <expression>
```

**Current behaviour (Phase 1):**

The `print` statement accepts a single string literal enclosed in `"` or `'`.

```
print "Hello, Vyauma!"
print 'Welcome'
```

**Planned behaviour (Phase 2+):**

`print` will accept any expression — variables, arithmetic, or function calls:

```
print x
print 1 + 2
print greet("world")
```

---

## 4. Variables *(planned)*

Variables are declared with the `let` keyword.

**Syntax:**

```
let <identifier> = <expression>
```

**Examples:**

```
let name = "Vyauma"
let count = 10
let score = 98.5
```

- Variables are immutable by default (re-assignment planned in a later phase).
- Type is inferred from the assigned value.

---

## 5. Expressions *(planned)*

### 5.1 Arithmetic

| Operator | Operation | Example |
|---|---|---|
| `+` | Addition | `1 + 2` |
| `-` | Subtraction | `5 - 3` |
| `*` | Multiplication | `4 * 3` |
| `/` | Division | `10 / 2` |

### 5.2 Comparison

| Operator | Meaning | Example |
|---|---|---|
| `==` | Equal | `x == 5` |
| `!=` | Not equal | `x != 0` |
| `<` | Less than | `a < b` |
| `>` | Greater than | `a > b` |
| `<=` | Less than or equal | `a <= b` |
| `>=` | Greater than or equal | `a >= b` |

### 5.3 String Concatenation

```
let greeting = "Hello, " + name
```

---

## 6. Control Flow *(planned)*

### 6.1 `if` / `else`

```
if <condition>:
    <body>
else:
    <body>
```

Example:

```
if score >= 50:
    print "Pass"
else:
    print "Fail"
```

### 6.2 `loop`

Repeats a block while a condition is true:

```
loop <condition>:
    <body>
```

Example:

```
let i = 0
loop i < 5:
    print i
    let i = i + 1
```

---

## 7. Functions *(planned)*

```
func <name>(<params>):
    <body>
    return <expression>
```

Example:

```
func add(a, b):
    return a + b

print add(3, 4)
```

---

## 8. Comments

Single-line comments use `#`:

```
# Full-line comment
print "hi"   # End-of-line comment
```

Multi-line comments are not yet defined and may be added in a later phase.

---

## 9. File Format

- Source files use the `.vym` extension.
- Files must be UTF-8 encoded.
- The interpreter reads files line-by-line (Phase 1). A full parse-tree model is introduced in Phase 2.

---

## 10. Execution Model

### Phase 1 (current)

The CLI reads `.vym` files line by line. Each line is matched against known statement patterns. No lexer or AST is used.

```
.vym file -> line-by-line scanner -> output
```

### Phase 2+ (planned)

A proper pipeline will replace the line scanner:

```
.vym file -> Lexer -> Token stream -> Parser -> AST -> Runtime -> output
```

### Entry Point

The CLI is invoked as:

```bash
python src/cli/vyauma.py run <file.vym>
```

The `run` command is the only supported command in Phase 1.

---

## 11. Error Handling

### Phase 1

Errors are printed to `stderr` and the process exits with code `1`.

| Situation | Message |
|---|---|
| File not found | `Error: File not found -> <path>` |
| Unknown CLI command | `Unknown command: <cmd>` |
| Insufficient CLI arguments | Usage hint printed to stdout |

### Phase 2+ *(planned)*

Structured error reporting with:
- Line number and column
- Error category (syntax error, runtime error, type error)
- Suggested fix where possible

---

*This specification is updated alongside each release. For the current development status, see the [Roadmap](roadmap.md).*
