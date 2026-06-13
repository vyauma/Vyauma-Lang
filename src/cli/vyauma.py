#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project root to sys.path so we can import src modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.lexer import Lexer, LexError
from src.parser import Parser, ParseError, ExpressionStmt
from src.runtime import Interpreter, VyaumaRuntimeError
from src.vm.compiler import Compiler
from src.vm.vm import VM, VMError

def report_error(e: Exception, source_code: str):
    if isinstance(e, LexError):
        line, col = e.line, e.column
        msg = str(e).split("LexError: ")[-1] if "LexError: " in str(e) else str(e)
        err_type = "LexError"
    elif isinstance(e, ParseError):
        line, col = e.token.line, e.token.column
        msg = str(e).split("ParseError: ")[-1] if "ParseError: " in str(e) else str(e)
        err_type = "ParseError"
    elif isinstance(e, VyaumaRuntimeError):
        line, col = e.token.line, e.token.column
        msg = str(e).split("RuntimeError: ")[-1] if "RuntimeError: " in str(e) else str(e)
        err_type = "RuntimeError"
    elif isinstance(e, VMError):
        line, col = getattr(e, 'line', 1), getattr(e, 'col', 1)
        msg = str(e).split("VMError: ")[-1] if "VMError: " in str(e) else str(e)
        err_type = "VMError"
    else:
        print(e, file=sys.stderr)
        return

    lines = source_code.splitlines()
    if 1 <= line <= len(lines):
        source_line = lines[line - 1]
        print(f"[line {line}, col {col}] {err_type}: {msg}", file=sys.stderr)
        print(source_line, file=sys.stderr)
        
        # Handle tab characters for column alignment
        caret_line = ""
        for i in range(col - 1):
            if i < len(source_line) and source_line[i] == "\t":
                caret_line += "\t"
            else:
                caret_line += " "
        caret_line += "^"
        print(caret_line, file=sys.stderr)
    else:
        print(e, file=sys.stderr)

def run_file(path, use_vm=False):
    p = Path(path)
    if not p.exists():
        print(f"Error: File not found -> {path}", file=sys.stderr)
        return 1

    print(f"Running Vyauma file: {p}" + (" (VM Mode)" if use_vm else ""), file=sys.stderr)
    code = p.read_text(encoding="utf-8")

    try:
        # Lexical analysis
        lexer = Lexer(code)
        tokens = lexer.tokenize()

        # Parsing
        parser = Parser(tokens)
        program = parser.parse()

        if use_vm:
            compiler = Compiler()
            chunk = compiler.compile(program)
            vm = VM()
            vm.interpret(chunk)
        else:
            # Interpretation
            interpreter = Interpreter()
            interpreter.interpret(program)

        return 0

    except (LexError, ParseError, VyaumaRuntimeError, VMError) as e:
        report_error(e, code)
        return 1

def run_prompt():
    print("Vyauma REPL (Phase 1)")
    print("Type 'exit' or press Ctrl+C to quit.")
    interpreter = Interpreter()

    while True:
        try:
            line = input(">>> ")
            if line.strip() == "exit":
                break
            if not line.strip():
                continue

            # Read block if the line ends with a colon
            if line.rstrip().endswith(":"):
                lines = [line]
                while True:
                    sub_line = input("... ")
                    if not sub_line:
                        break
                    lines.append(sub_line)
                code = "\n".join(lines) + "\n"
            else:
                code = line + "\n"

            try:
                tokens = Lexer(code).tokenize()
                program = Parser(tokens).parse()

                if len(program.statements) == 1 and isinstance(program.statements[0], ExpressionStmt):
                    # Auto-print single expressions
                    result = interpreter._evaluate(program.statements[0].expression)
                    if result is not None:
                        if isinstance(result, bool):
                            print("true" if result else "false")
                        else:
                            print(result)
                else:
                    for stmt in program.statements:
                        interpreter._execute(stmt)

            except (LexError, ParseError, VyaumaRuntimeError) as e:
                report_error(e, code)

        except (KeyboardInterrupt, EOFError):
            print()
            break


def main():
    args = sys.argv[1:]
    use_vm = False
    
    if "--vm" in args:
        use_vm = True
        args.remove("--vm")
        
    if len(args) == 0:
        # Run REPL
        sys.exit(run_prompt())
    elif len(args) >= 2 and args[0] == "run":
        file_path = args[1]
        sys.exit(run_file(file_path, use_vm))
    else:
        print(f"Unknown command or arguments: {' '.join(args)}")
        print("Usage:")
        print("  vyauma.py                 # Start REPL")
        print("  vyauma.py run <file.vym>  # Run script")
        print("  Options:")
        print("    --vm                    # Run using the new Bytecode VM")
        sys.exit(1)


if __name__ == "__main__":
    main()
