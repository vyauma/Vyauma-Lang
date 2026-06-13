# Contributing to Vyauma

Thank you for considering contributing to Vyauma.

This project is in early-stage development and contributions are encouraged across documentation, specification design, interpreter implementation, testing, and tooling.

---

## How to Contribute

### 1. Fork the Repository

Click **Fork** on GitHub and clone your copy locally:

```bash
git clone https://github.com/<your-username>/Vyauma-Lang.git
cd Vyauma-Lang
```

### 2. Create a Feature Branch

Use a descriptive branch name:

```bash
git checkout -b feat/add-lexer
git checkout -b fix/print-strip-bug
git checkout -b docs/complete-spec
```

### 3. Make Your Changes

Work inside the relevant directory:

| Area | Location |
|---|---|
| CLI runner | `src/cli/vyauma.py` |
| Lexer | `src/lexer/` |
| Parser | `src/parser/` |
| Runtime | `src/runtime/` |
| Tests | `tests/` |
| Documentation | `docs/` |

### 4. Write or Update Tests

All changes to the interpreter must include tests in `tests/`. Tests use [pytest](https://docs.pytest.org/).

Run the test suite locally before opening a PR:

```bash
python -m pip install pytest
python -m pytest -v
```

All tests must pass before your PR will be reviewed.

### 5. Commit Your Changes

Write clear, concise commit messages:

```bash
git add .
git commit -m "feat: implement lexer tokenisation for print statement"
```

Use the following prefixes:

| Prefix | When to use |
|---|---|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation only |
| `test:` | Adding or fixing tests |
| `refactor:` | Code change with no behaviour change |
| `chore:` | Build, CI, or tooling changes |

### 6. Push and Open a Pull Request

```bash
git push origin feat/add-lexer
```

Open a Pull Request on GitHub against the `main` branch. Include:
- A description of what you changed and why
- Any relevant issue numbers

---

## Areas Where Help Is Needed

The following areas are the highest priority for Phase 2:

- **Lexer** (`src/lexer/`) — tokenise `.vym` source into a token stream
- **Parser** (`src/parser/`) — build an AST from the token stream
- **Runtime** (`src/runtime/`) — walk the AST and execute the program
- **Tests** (`tests/`) — expand coverage as new features land
- **Documentation** (`docs/`) — improve examples and specification depth

---

## Code Style

- Use Python 3.9+ compatible syntax.
- Follow [PEP 8](https://peps.python.org/pep-0008/) conventions.
- Keep functions small and focused.
- Add a docstring to every public function or class.
- Prefer clarity over cleverness.

---

## Questions

If you have a question or want to discuss a design decision before writing code, open a [GitHub Issue](https://github.com/vyauma/Vyauma-Lang/issues) with the `question` label. This avoids duplicated effort and keeps design discussions visible to everyone.

---

*This contributing guide will be updated as the project matures.*
