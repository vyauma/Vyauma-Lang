# Vyauma Language

Vyauma is a next-generation, cross-device programming language designed to run universally on any machine.  
It uses the `.vym` file extension and focuses on simplicity, consistency, and compatibility across platforms.

The language aims to unify execution models so developers can write once and run anywhere, regardless of device hardware or operating system.

---

## Key Features

- **Universal Syntax**: Simple, readable, and inspired by Pythonic clarity.
- **Cross-Device Execution**: Designed for future runtimes across mobile, embedded systems, cloud, and desktop.
- **Lightweight Runtime**: Early interpreter architecture for consistent behaviour.
- **Developer Friendly**: Clean specification, examples, and predictable behaviour.

---

## Quick Start

### Prerequisites

- Python 3.9 or later

### Run a `.vym` file

```bash
python src/cli/vyauma.py run <file.vym>
```

### Example

Create a file called `hello.vym`:

```
print "Hello, Vyauma!"
```

Run it:

```bash
python src/cli/vyauma.py run hello.vym
```

Output:

```
Hello, Vyauma!
```

A ready-made example lives in [`docs/examples/hello.vym`](docs/examples/hello.vym).

---

## Project Structure

```
Vyauma-Lang/
├── src/
│   ├── cli/        # Command-line entry point (vyauma.py)
│   ├── lexer/      # Tokeniser (Phase 2)
│   ├── parser/     # AST builder (Phase 2)
│   └── runtime/    # Interpreter / execution engine (Phase 2)
├── docs/
│   ├── examples/           # Sample .vym programs
│   ├── specification.md    # Formal language specification
│   ├── syntax-guide.md     # Beginner-friendly syntax reference
│   └── roadmap.md          # Development milestones
├── tests/          # pytest test suite
├── CONTRIBUTING.md
└── LICENSE
```

---

## Documentation

| Document | Description |
|---|---|
| [Syntax Guide](docs/syntax-guide.md) | Beginner-friendly tour of the language |
| [Specification](docs/specification.md) | Formal grammar and execution rules |
| [Roadmap](docs/roadmap.md) | Planned features and release milestones |

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

---

## Current Status

Vyauma is actively evolving with its core foundation complete. The Lexer, Parser, AST, Compiler, and Virtual Machine (VM) runtime are fully implemented and capable of executing Vyauma code. Current focus is expanding the standard library, FFI capabilities, and the developer ecosystem tooling (Package Manager, Formatter, LSP).

---

## License

Distributed under the terms of the [LICENSE](LICENSE) file included in this repository.
