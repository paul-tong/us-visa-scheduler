"""PowerShell launcher integration with real Python and offline command fixtures."""
import base64
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_settings import POWERSHELLS, ROOT


RECORDER = """
import json, os, sys
from pathlib import Path
kind = Path(__file__).stem
with Path("commands.jsonl").open("a", encoding="utf-8") as stream:
    stream.write(json.dumps({
        "kind": kind, "args": sys.argv[1:],
        "sender": os.environ.get("VISA_EMAIL_SENDER"),
        "booking": os.environ.get("VISA_AUTO_BOOKING"),
    }) + "\\n")
step = sys.argv[1] if kind == "pip" else "main"
sys.exit(int(os.environ.get("TEST_FAIL_" + step.upper(), "0")))
"""


@unittest.skipUnless(os.name == "nt" and POWERSHELLS, "PowerShell launcher on Windows")
class LauncherTests(unittest.TestCase):
    def run_launcher(self, shell, choices=("1",), environment=None, existing=True,
                     invalid_root=False, broken_venv=False, fail_creation=False):
        with tempfile.TemporaryDirectory(prefix="visa launcher ") as directory:
            root = Path(directory)
            (root / "personal").mkdir()
            local = root / "personal" / "Set-VisaEnvironment.local.ps1"
            local.write_text((ROOT / "Set-VisaEnvironment.template.ps1").read_text(encoding="utf-8"),
                             encoding="utf-8")
            (root / "main.py").write_text(RECORDER, encoding="utf-8")
            (root / "pip.py").write_text(RECORDER, encoding="utf-8")
            if not invalid_root:
                (root / "requirements.txt").write_text("# offline fixture\n", encoding="utf-8")
                (root / "visa_tool").mkdir()
                (root / "visa_tool" / "app.py").touch()
            if broken_venv:
                (root / ".venv").mkdir()
            elif existing:
                subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(root / ".venv")],
                               check=True, capture_output=True, timeout=30)
                (root / ".venv" / "reuse-marker").touch()

            # The root-local pip module records arguments, never installs or downloads.
            # The main module records the selected mode, never sends email/starts a browser.
            child_environment = {
                key: value for key, value in os.environ.items()
                if not key.upper().startswith("VISA_") and key.upper() not in ("PSMODULEPATH", "PYTHONPATH")
            }
            child_environment["PATH"] = str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", "")
            child_environment.update(environment or {})
            path = str(local).replace("'", "''")
            selection_values = ",".join("'" + value.replace("'", "''") + "'" for value in choices)
            script = f"""
$global:TestSelections = [Collections.Generic.Queue[string]]::new()
foreach ($value in @({selection_values})) {{ $global:TestSelections.Enqueue($value) }}
function global:Read-Host {{
    param([string]$Prompt)
    if ($Prompt -notlike 'Select mode*') {{ throw 'Unexpected credential prompt.' }}
    if ($global:TestSelections.Count -eq 0) {{ throw 'Unexpected extra menu prompt.' }}
    $global:TestSelections.Dequeue()
}}
"""
            if fail_creation:
                script += "function global:python { $global:LASTEXITCODE = 19 }\n"
            script += f"& '{path}'\nexit $LASTEXITCODE\n"
            completed = subprocess.run(
                [shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                 "-EncodedCommand", base64.b64encode(script.encode("utf-16-le")).decode()],
                cwd=root, env=child_environment, capture_output=True, text=True, timeout=60,
            )
            trace = root / "commands.jsonl"
            records = [json.loads(line) for line in trace.read_text().splitlines()] if trace.exists() else []
            return (completed, records, (root / ".venv" / "Scripts" / "python.exe").is_file(),
                    (root / ".venv" / "reuse-marker").exists())

    def test_each_mode_inherits_settings_after_setup_in_both_shells(self):
        for shell in POWERSHELLS:
            for selection, expected in (("1", ["--check-config"]), ("2", ["--test-email"]), ("3", [])):
                with self.subTest(shell=shell, selection=selection):
                    completed, commands, _, reused = self.run_launcher(shell, (selection,))
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    self.assertTrue(reused)
                    self.assertEqual([item["kind"] for item in commands], ["pip", "pip", "main"])
                    self.assertEqual(commands[0]["args"][:2], ["install", "-r"])
                    self.assertEqual(Path(commands[0]["args"][2]).name, "requirements.txt")
                    self.assertEqual(commands[1]["args"], ["check"])
                    self.assertEqual(commands[2]["args"], expected)
                    self.assertEqual(commands[2]["sender"], "your.name@gmail.com")
                    self.assertEqual(commands[2]["booking"], "false")
                    self.assertIsNone(commands[0]["sender"])

    def test_first_run_creates_venv_and_enter_defaults_to_offline_check(self):
        for shell in POWERSHELLS:
            with self.subTest(shell=shell):
                completed, commands, created, reused = self.run_launcher(shell, ("",), existing=False)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertTrue(created)
                self.assertFalse(reused)
                self.assertEqual(commands[-1]["args"], ["--check-config"])

    def test_invalid_menu_reprompts_without_dispatching_twice(self):
        for shell in POWERSHELLS:
            with self.subTest(shell=shell):
                completed, commands, _, _ = self.run_launcher(shell, ("bad", "3"))
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn("Invalid selection", completed.stdout)
                self.assertEqual([item["kind"] for item in commands].count("main"), 1)
                self.assertEqual(commands[-1]["args"], [])

    def test_setup_errors_stop_before_menu_or_python_application(self):
        for shell in POWERSHELLS:
            for step, expected_commands in (("INSTALL", 1), ("CHECK", 2)):
                with self.subTest(shell=shell, step=step):
                    completed, commands, _, _ = self.run_launcher(
                        shell, (), environment={"TEST_FAIL_" + step: "17"})
                    self.assertEqual(completed.returncode, 1)
                    self.assertEqual(len(commands), expected_commands)
                    self.assertTrue(all(item["kind"] == "pip" for item in commands))
                    self.assertIn("exit code 17", completed.stderr)
                    self.assertNotIn("Unexpected extra menu prompt", completed.stderr)

    def test_bad_root_broken_venv_and_creation_failure_stop_without_install(self):
        for shell in POWERSHELLS:
            for case in (
                {"invalid_root": True, "existing": False},
                {"broken_venv": True},
                {"fail_creation": True, "existing": False},
            ):
                with self.subTest(shell=shell, case=case):
                    completed, commands, _, _ = self.run_launcher(shell, (), **case)
                    self.assertEqual(completed.returncode, 1)
                    self.assertEqual(commands, [])
                    self.assertNotIn("Unexpected extra menu prompt", completed.stderr)

    def test_application_exit_code_is_propagated_without_retry(self):
        for shell in POWERSHELLS:
            with self.subTest(shell=shell):
                completed, commands, _, _ = self.run_launcher(shell, ("3",), environment={"TEST_FAIL_MAIN": "2"})
                self.assertEqual(completed.returncode, 2)
                self.assertEqual([item["kind"] for item in commands].count("main"), 1)


if __name__ == "__main__":
    unittest.main()
