"""Run controlled children through the installed-harness negative assertion."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

CMAKE = shutil.which("cmake")
WRAPPER = Path(__file__).resolve().parents[1] / "cmake/ExpectToolFailure.cmake"


@unittest.skipUnless(CMAKE, "CMake required")
class FailureWrapperTests(unittest.TestCase):
    def run_child(self, body):
        with tempfile.TemporaryDirectory(prefix="tool failure with spaces ") as tmp:
            child = Path(tmp) / "controlled child.py"
            child.write_text("import os, signal, sys\n" + body)
            return subprocess.run([
                CMAKE, f"-DTOOL_EXECUTABLE={sys.executable}", f"-DTOOL_ARGUMENTS={child}",
                "-DEXPECTED_EXIT_CODE=6", "-DEXPECTED_DIAGNOSTICS=invalid processOption;THISVALUEISINVALID",
                "-P", str(WRAPPER)], capture_output=True, text=True)

    def test_accepts_expected_failure_across_output_streams(self):
        result = self.run_child("print('invalid processOption')\nsys.stderr.write('THISVALUEISINVALID')\nsys.exit(6)\n")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_wrong_status_even_with_expected_diagnostic(self):
        for code in (0, 1, 42):
            with self.subTest(code=code):
                result = self.run_child(f"print('invalid processOption THISVALUEISINVALID')\nsys.exit({code})\n")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Expected tool exit 6", result.stderr)

    def test_rejects_unrelated_failure_with_same_exit_code(self):
        result = self.run_child("print('something else failed')\nsys.exit(6)\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("wrong reason", result.stderr)

    def test_rejects_loader_diagnostic_even_with_expected_text_and_code(self):
        result = self.run_child("print('invalid processOption THISVALUEISINVALID')\nprint('dyld[1]: Library not loaded: missing')\nsys.exit(6)\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("runtime loader", result.stderr)

    @unittest.skipIf(os.name == "nt", "POSIX signal check")
    def test_rejects_signal_with_expected_diagnostic(self):
        result = self.run_child("print('invalid processOption THISVALUEISINVALID', flush=True)\nos.kill(os.getpid(), signal.SIGTERM)\n")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Expected tool exit 6", result.stderr)


if __name__ == "__main__":
    unittest.main()
