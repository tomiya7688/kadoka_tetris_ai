from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tools import audit_python_trust as audit


class WindowsJobAssignmentTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "nt", "Windows Job Object path")
    def test_failed_assignment_never_releases_worker(self) -> None:
        import time
        from tools import windows_job

        with TemporaryDirectory() as root:
            script = Path(root) / "worker.py"
            marker = Path(root) / "started"
            script.write_text(
                "import pathlib, sys\n"
                "pathlib.Path(sys.argv[2]).write_text('started')\n",
                encoding="utf-8",
            )
            at_gate = Path(root) / "at_gate"
            original_popen = windows_job.subprocess.Popen

            def instrumented_popen(command, **kwargs):
                command = list(command)
                command[4] = (
                    f"from pathlib import Path\nPath({str(at_gate)!r}).write_text('ready')\n"
                    + command[4]
                )
                return original_popen(command, **kwargs)

            def reject_assignment(*_args):
                deadline = time.monotonic() + 60
                while not at_gate.exists() and time.monotonic() < deadline:
                    time.sleep(0.1)
                self.assertTrue(at_gate.exists(), "worker did not reach the gate")
                return 0

            with (
                patch.object(audit, "__file__", str(script)),
                patch.object(
                    windows_job.subprocess, "Popen", side_effect=instrumented_popen
                ),
                patch.object(
                    windows_job.kernel32,
                    "AssignProcessToJobObject",
                    side_effect=reject_assignment,
                ),
                self.assertRaises(OSError),
            ):
                audit.read_hashed_ca_file(marker)
            self.assertFalse(marker.exists(), "worker ran before job assignment")


if __name__ == "__main__":
    unittest.main()
