"""Execute candidate code against appended assertions in a subprocess.

Safety: the candidate runs in a scratch temp directory with a hard timeout.
No network access is granted by this module; runs that try to hang are killed
by the timeout and reported as such. (A sandboxed runner can replace this in
the SAB execution environment.)
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, Optional


class UnitTestChecker:
    def __init__(self, name: str = "unit_test", test_code: str = "", timeout_s: float = 10.0):
        if not test_code.strip():
            raise ValueError("test_code must not be empty")
        self.name = name
        self.test_code = test_code
        self.timeout_s = timeout_s

    def check(self, output: Any, context: Optional[Dict] = None):
        from .base import CheckerResult

        code = output if isinstance(output, str) else (output or {}).get("code", "")
        if not code.strip():
            return CheckerResult(self.name, passed=False, details={"problems": ["no code in output"]})

        t0 = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="verifront_ut_") as td:
            path = pathlib.Path(td) / "candidate.py"
            path.write_text(code + "\n\n" + self.test_code, encoding="utf-8")
            try:
                proc = subprocess.run(
                    [sys.executable, str(path)],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_s,
                    cwd=td,
                )
                passed = proc.returncode == 0
                status = "passed" if passed else f"exit={proc.returncode}"
                stderr_tail = (proc.stderr or "")[-500:]
            except subprocess.TimeoutExpired:
                passed = False
                status = "timeout"
                stderr_tail = ""
        return CheckerResult(
            self.name,
            passed=passed,
            details={"status": status, "stderr_tail": stderr_tail},
            cost_seconds=time.monotonic() - t0,
        )
