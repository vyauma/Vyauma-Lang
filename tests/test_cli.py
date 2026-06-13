"""
Minimal tests for the Vyauma CLI runner.
Covers the current placeholder interpreter behaviour.
"""

import subprocess
import sys
import tempfile
import os
from pathlib import Path

# Path to the CLI entry point
CLI = Path(__file__).parent.parent / "src" / "cli" / "vyauma.py"


def run_cli(*args, input_file=None):
    """Helper: invoke the CLI and return (returncode, stdout, stderr)."""
    cmd = [sys.executable, str(CLI)] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_vym(content: str) -> str:
    """Write content to a temporary .vym file and return its path."""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".vym", delete=False, encoding="utf-8"
    )
    tmp.write(content)
    tmp.close()
    return tmp.name


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPrintStatement:
    def test_print_double_quoted_string(self):
        """print "Hello, Vyauma!" should output the string."""
        path = make_vym('print "Hello, Vyauma!"\n')
        try:
            code, out, _ = run_cli("run", path)
            assert code == 0
            assert "Hello, Vyauma!" in out
        finally:
            os.unlink(path)

    def test_print_single_quoted_string(self):
        """print 'hello' should also strip single quotes."""
        path = make_vym("print 'hello'\n")
        try:
            code, out, _ = run_cli("run", path)
            assert code == 0
            assert "hello" in out
        finally:
            os.unlink(path)

    def test_multiple_print_lines(self):
        """Multiple print statements should each produce a line."""
        path = make_vym('print "line one"\nprint "line two"\n')
        try:
            code, out, _ = run_cli("run", path)
            assert code == 0
            assert "line one" in out
            assert "line two" in out
        finally:
            os.unlink(path)

    def test_empty_file_runs_cleanly(self):
        """An empty .vym file should exit 0 with no stdout output.
        The status banner goes to stderr, not stdout.
        """
        path = make_vym("")
        try:
            code, out, err = run_cli("run", path)
            assert code == 0
            assert out.strip() == ""   # program stdout is silent
            assert "running" in err.lower()  # banner goes to stderr
        finally:
            os.unlink(path)


class TestErrorHandling:
    def test_missing_file_returns_nonzero(self):
        """Running a non-existent file should return exit code 1
        and print an error message to stderr.
        """
        code, out, err = run_cli("run", "nonexistent_file.vym")
        assert code == 1
        assert "not found" in err.lower() or "error" in err.lower()

    def test_unknown_command_returns_nonzero(self):
        """An unrecognised command should return exit code 1."""
        code, out, _ = run_cli("explode")
        assert code == 1

    def test_no_args_starts_repl(self):
        """Invoking with no arguments should start REPL and exit zero on EOF."""
        code, out, _ = run_cli()
        assert code == 0
        assert "Vyauma REPL" in out
        assert "usage" in out.lower() or "vyauma" in out.lower()
