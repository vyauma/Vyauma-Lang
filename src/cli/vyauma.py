#!/usr/bin/env python3
import sys
from pathlib import Path

def run_file(path):
    p = Path(path)
    if not p.exists():
        print(f"Error: File not found → {path}")
        return 1

    print(f"Running Vyauma file: {p}")
    code = p.read_text()

    # Placeholder interpreter (for now)
    # Later this will call lexer → parser → runtime
    for line in code.splitlines():
        line = line.strip()
        if line.startswith("print "):
            content = line.replace("print ", "", 1)
            content = content.strip().strip('"').strip("'")
            print(content)

    return 0

def main():
    if len(sys.argv) < 3:
        print("Usage: vyauma.py run <file.vym>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "run":
        file_path = sys.argv[2]
        sys.exit(run_file(file_path))
    else:
        print(f"Unknown command: {command}")
        print("Usage: vyauma.py run <file.vym>")
        sys.exit(1)


if __name__ == "__main__":
    main()
