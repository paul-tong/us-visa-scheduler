import base64
import contextlib
import io
import json
import os
import runpy
import shutil
import subprocess
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from visa_tool.app import cli
from visa_tool.core import SafetyError
from visa_tool.settings import answer_setting, boolean_setting, integer_setting, range_setting, time_setting

ROOT = Path(__file__).resolve().parents[1]
POWERSHELLS = tuple(path for path in (shutil.which("pwsh"), shutil.which("powershell.exe")) if path)
ENVIRONMENT = {
    "VISA_USERNAME": "synthetic-username",
    "VISA_PASSWORD": "synthetic-visa-password",
    "VISA_SECURITY_ANSWERS": json.dumps({
        "问题一？": 'answer with "quotes" and \\slashes',
        "Question two?": "two",
        "Question three?": "three",
    }, ensure_ascii=False),
    "VISA_APPLICANTS": " Applicant One ; Applicant Two ",
    "VISA_VISA_CLASS": "B2",
    "VISA_EXISTING_APPOINTMENT": "2030-01-15T10:00:00",
    "VISA_PREFERRED_DATE_RANGES": '[["2027-01-10","2027-01-12"],["2026-12-01","2026-12-15"]]',
    "VISA_AUTO_BOOKING": "false",
    "VISA_DAILY_EMAIL_TIMES": '["07:00","13:00","18:00"]',
    "VISA_POLL_SECONDS_MIN": "123",
    "VISA_POLL_SECONDS_MAX": "456",
    "VISA_CLICK_WAIT_SECONDS": "3",
    "VISA_BLOCK_COOLDOWN_SECONDS": "7200",
    "VISA_MAX_RECOVERY_RETRIES": "2",
    "VISA_MAX_CHECKS_PER_RUN": "150",
    "VISA_AUTO_VERIFICATION": "false",
    "VISA_MAX_AUTO_VERIFICATIONS": "10",
    "VISA_MANUAL_VERIFICATION_TIMEOUT_SECONDS": "901",
    "VISA_PAGE_TIMEOUT_SECONDS": "46",
    "VISA_QUEUE_TIMEOUT_SECONDS": "1801",
    "VISA_SMTP_HOST": "smtp.example.invalid",
    "VISA_SMTP_PORT": "2465",
    "VISA_EMAIL_SENDER": "sender@example.invalid",
    "VISA_SMTP_PASSWORD": "synthetic-smtp-password",
    "VISA_EMAIL_TO": "recipient@example.invalid",
}


def load_main(environment):
    with patch.dict(os.environ, environment, clear=True):
        return runpy.run_path(str(ROOT / "main.py"))


class SettingsTests(unittest.TestCase):
    def test_all_requested_properties_override_fallbacks(self):
        config = load_main(ENVIRONMENT)["build_config"]()
        config.validate(today=date(2026, 11, 15))
        self.assertEqual(config.username, ENVIRONMENT["VISA_USERNAME"])
        self.assertEqual(config.password, ENVIRONMENT["VISA_PASSWORD"])
        self.assertEqual(config.security_answers, json.loads(ENVIRONMENT["VISA_SECURITY_ANSWERS"]))
        self.assertEqual(config.applicants, ("Applicant One", "Applicant Two"))
        self.assertEqual(config.visa_class, "B2")
        self.assertEqual(config.existing_appointment, "2030-01-15T10:00:00")
        self.assertEqual(config.ranges, (("2027-01-10", "2027-01-12"), ("2026-12-01", "2026-12-15")))
        self.assertFalse(config.auto_booking)
        self.assertEqual(config.daily_times, ("07:00", "13:00", "18:00"))
        self.assertEqual(config.poll_seconds_min, 123)
        self.assertEqual(config.poll_seconds_max, 456)
        self.assertEqual(config.click_wait_seconds, 3)
        self.assertEqual(config.cooldown_seconds, 7200)
        self.assertEqual(config.max_retries, 2)
        self.assertEqual(config.max_checks, 150)
        self.assertIs(config.auto_verification, False)
        self.assertEqual(config.max_auto_verifications, 10)
        self.assertEqual(config.manual_timeout, 901)
        self.assertEqual(config.page_timeout, 46)
        self.assertEqual(config.queue_timeout, 1801)
        self.assertEqual(config.smtp_host, "smtp.example.invalid")
        self.assertEqual(config.smtp_port, 2465)
        self.assertEqual(config.smtp_username, ENVIRONMENT["VISA_EMAIL_SENDER"])
        self.assertEqual(config.smtp_password, ENVIRONMENT["VISA_SMTP_PASSWORD"])
        self.assertEqual(config.email_to, ENVIRONMENT["VISA_EMAIL_TO"])

    def test_absent_environment_uses_main_fallbacks(self):
        config = load_main({})["build_config"]()
        self.assertEqual(config.username, "")
        self.assertEqual(config.password, "")
        self.assertEqual(config.security_answers, {})
        self.assertEqual(config.applicants, ())
        self.assertEqual(config.visa_class, "B1/B2")
        self.assertEqual(config.existing_appointment, "")
        self.assertEqual(config.ranges, (("2026-12-01", "2026-12-15"), ("2026-12-22", "2026-12-25")))
        self.assertFalse(config.auto_booking)
        self.assertEqual(config.daily_times, ("08:00", "12:00", "17:00"))
        self.assertEqual(config.poll_seconds_min, 1800)
        self.assertEqual(config.poll_seconds_max, 3600)
        self.assertEqual(config.click_wait_seconds, 5)
        self.assertEqual(config.cooldown_seconds, 86400)
        self.assertEqual(config.max_retries, 3)
        self.assertEqual(config.max_checks, 24)
        self.assertIs(config.auto_verification, True)
        self.assertEqual(config.max_auto_verifications, 1)
        self.assertEqual(config.manual_timeout, 900)
        self.assertEqual(config.page_timeout, 45)
        self.assertEqual(config.queue_timeout, 1800)
        self.assertEqual(config.smtp_host, "smtp.gmail.com")
        self.assertEqual(config.smtp_port, 465)
        self.assertEqual((config.smtp_username, config.smtp_password, config.email_to), ("", "", ""))

    def test_boolean_conversion_never_uses_string_truthiness(self):
        for value in (False, "false", "FALSE", " False ", "0"):
            self.assertIs(boolean_setting("FLAG", value), False)
        for value in (True, "true", "TRUE", " 1 "):
            self.assertIs(boolean_setting("FLAG", value), True)
        for value in ("", "offf", "yes", "null", 0, 1, None):
            with self.subTest(value=value), self.assertRaises(SafetyError):
                boolean_setting("FLAG", value)

    def test_port_integer_type_and_bounds(self):
        self.assertEqual(integer_setting("PORT", "465"), 465)
        self.assertEqual(integer_setting("PORT", 465), 465)
        for value in ("", "465.0", "4e2", True, None):
            with self.subTest(value=value), self.assertRaises(SafetyError):
                integer_setting("PORT", value)
        for port in ("0", "65536"):
            config = load_main({**ENVIRONMENT, "VISA_SMTP_PORT": port})["build_config"]()
            with self.assertRaises(SafetyError):
                config.validate(browser=False)

    def test_bad_json_shapes_duplicates_and_empty_values_fail_closed(self):
        cases = [
            (answer_setting, '{"question":"secret-a","question":"secret-b"}'),
            (answer_setting, '{"question":123}'),
            (answer_setting, '["question","answer"]'),
            (range_setting, '["2026-12-01","2026-12-15"]'),
            (range_setting, '[["2026-12-01"]]'),
            (range_setting, '[[1,2]]'),
            (time_setting, '["08:00",null,"17:00"]'),
            (time_setting, '{"time":"08:00"}'),
        ]
        for function, value in cases:
            with self.subTest(function=function.__name__, value=value):
                with self.assertRaises(SafetyError):
                    function("SETTING", value)
        for function in (answer_setting, range_setting, time_setting):
            with self.assertRaises(SafetyError):
                function("SETTING", "")

    def test_present_empty_variable_does_not_restore_default(self):
        config = load_main({**ENVIRONMENT, "VISA_SMTP_HOST": ""})["build_config"]()
        self.assertEqual(config.smtp_host, "")
        with self.assertRaises(SafetyError):
            config.validate(browser=False)
        with self.assertRaises(SafetyError):
            load_main({**ENVIRONMENT, "VISA_AUTO_BOOKING": ""})["build_config"]()

    def test_smtp_diagnostic_names_fields_without_echoing_values(self):
        config = load_main({
            **ENVIRONMENT, "VISA_EMAIL_SENDER": "",
            "VISA_EMAIL_TO": "   ", "VISA_SMTP_PASSWORD": "NEVER_PRINT_THIS\n",
        })["build_config"]()
        with self.assertRaises(SafetyError) as caught:
            config.validate(browser=False)
        message = str(caught.exception)
        for name in ("VISA_EMAIL_SENDER", "VISA_EMAIL_TO", "VISA_SMTP_PASSWORD"):
            self.assertIn(name, message)
        self.assertIn("SAME PowerShell process", message)
        self.assertNotIn("NEVER_PRINT_THIS", message)
        self.assertNotIn("smtp.example.invalid", message)

    def test_invalid_poll_environment_stops_cli_before_side_effects(self):
        cases = [
            {"VISA_POLL_SECONDS_MIN": ""},
            {"VISA_POLL_SECONDS_MAX": "2.5"},
            {"VISA_POLL_SECONDS_MIN": "true"},
            {"VISA_POLL_SECONDS_MIN": "0"},
            {"VISA_POLL_SECONDS_MAX": "-1"},
            {"VISA_POLL_SECONDS_MIN": "457", "VISA_POLL_SECONDS_MAX": "456"},
        ]
        for overrides in cases:
            with self.subTest(overrides=overrides):
                config_factory = load_main({**ENVIRONMENT, **overrides})["build_config"]
                output = io.StringIO()
                with patch.object(sys, "argv", ["main.py", "--check-config"]), contextlib.redirect_stdout(output):
                    with patch("visa_tool.app.smtp_send") as send, patch("visa_tool.app.Store") as store:
                        self.assertEqual(cli(config_factory), 2)
                        send.assert_not_called()
                        store.assert_not_called()
                self.assertIn("POLL_SECONDS", output.getvalue())

    def test_one_poll_override_uses_other_bound_fallback(self):
        minimum = load_main({"VISA_POLL_SECONDS_MIN": "2000"})["build_config"]()
        self.assertEqual((minimum.poll_seconds_min, minimum.poll_seconds_max), (2000, 3600))
        maximum = load_main({"VISA_POLL_SECONDS_MAX": "2400"})["build_config"]()
        self.assertEqual((maximum.poll_seconds_min, maximum.poll_seconds_max), (1800, 2400))

    def test_invalid_configuration_reports_safe_error_before_side_effects(self):
        config_factory = load_main({
            **ENVIRONMENT, "VISA_SECURITY_ANSWERS": '{"secret":"NEVER_PRINT_THIS"',
        })["build_config"]
        output = io.StringIO()
        with patch.object(sys, "argv", ["main.py", "--check-config"]), contextlib.redirect_stdout(output):
            with patch("visa_tool.app.smtp_send") as send, patch("visa_tool.app.Store") as store:
                self.assertEqual(cli(config_factory), 2)
                send.assert_not_called()
                store.assert_not_called()
        self.assertIn("VISA_SECURITY_ANSWERS", output.getvalue())
        self.assertNotIn("NEVER_PRINT_THIS", output.getvalue())
        self.assertNotIn("Traceback", output.getvalue())

    def test_requested_active_budget_profile_is_accepted(self):
        environment = {
            **ENVIRONMENT, "VISA_CLICK_WAIT_SECONDS": "3", "VISA_POLL_SECONDS_MIN": "300",
            "VISA_POLL_SECONDS_MAX": "600", "VISA_BLOCK_COOLDOWN_SECONDS": "7200",
            "VISA_MAX_RECOVERY_RETRIES": "3", "VISA_MAX_CHECKS_PER_RUN": "150",
            "VISA_AUTO_VERIFICATION": "true", "VISA_MAX_AUTO_VERIFICATIONS": "10",
            "VISA_MANUAL_VERIFICATION_TIMEOUT_SECONDS": "900",
            "VISA_PAGE_TIMEOUT_SECONDS": "45", "VISA_QUEUE_TIMEOUT_SECONDS": "1800",
        }
        config = load_main(environment)["build_config"]()
        config.validate(today=date(2026, 11, 15))
        self.assertEqual(config.max_auto_verifications, 10)
        self.assertIs(config.auto_verification, True)
        self.assertEqual((config.poll_seconds_min, config.poll_seconds_max), (300, 600))

    def test_bad_operational_environment_fails_before_network(self):
        overrides = (
            {"VISA_CLICK_WAIT_SECONDS": "-1"},
            {"VISA_BLOCK_COOLDOWN_SECONDS": "0"},
            {"VISA_MAX_RECOVERY_RETRIES": "4"},
            {"VISA_MAX_CHECKS_PER_RUN": "1.5"},
            {"VISA_AUTO_VERIFICATION": "maybe"},
            {"VISA_MAX_AUTO_VERIFICATIONS": "-1"},
            {"VISA_MANUAL_VERIFICATION_TIMEOUT_SECONDS": ""},
            {"VISA_PAGE_TIMEOUT_SECONDS": "0"},
            {"VISA_QUEUE_TIMEOUT_SECONDS": "-1"},
        )
        for values in overrides:
            with self.subTest(values=values):
                config_factory = load_main({**ENVIRONMENT, **values})["build_config"]
                with patch.object(sys, "argv", ["main.py", "--check-config"]), contextlib.redirect_stdout(io.StringIO()):
                    with patch("visa_tool.app.smtp_send") as send, patch("visa_tool.app.Store") as store:
                        self.assertEqual(cli(config_factory), 2)
                        send.assert_not_called()
                        store.assert_not_called()

    def test_help_does_not_parse_invalid_environment_values(self):
        config_factory = load_main({"VISA_AUTO_BOOKING": "invalid"})["build_config"]
        with patch.object(sys, "argv", ["main.py", "--help"]), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                cli(config_factory)
        self.assertEqual(caught.exception.code, 0)

    def test_fallback_python_collections_preserve_order_and_types(self):
        self.assertEqual(range_setting("DATES", [("2026-12-01", "2026-12-15")]),
                         (("2026-12-01", "2026-12-15"),))
        self.assertEqual(time_setting("TIMES", ["08:00", "12:00", "17:00"]),
                         ("08:00", "12:00", "17:00"))
        self.assertEqual(answer_setting("ANSWERS", {"Question": "Answer"}), {"Question": "Answer"})


@unittest.skipUnless(os.name == "nt" and POWERSHELLS, "PowerShell integration on Windows")
class PowerShellTemplateTests(unittest.TestCase):
    def test_process_only_template_round_trips_into_child_python(self):
        for shell in POWERSHELLS:
            with self.subTest(shell=shell):
                self._assert_template_roundtrip(shell)

    def _assert_template_roundtrip(self, shell):
        # Everything runs in a disposable child shell with synthetic template values.
        # Existing User/Machine values are compared internally, never returned.
        code = (
            "import json, main; c=main.build_config(); "
            "print(json.dumps(dict(username=c.username,password=c.password,"
            "security_answers=c.security_answers,applicants=c.applicants,visa_class=c.visa_class,"
            "existing_appointment=c.existing_appointment,ranges=c.ranges,auto_booking=c.auto_booking,"
            "daily_times=c.daily_times,smtp_host=c.smtp_host,smtp_port=c.smtp_port,"
            "poll_seconds_min=c.poll_seconds_min,poll_seconds_max=c.poll_seconds_max,"
            "click_wait_seconds=c.click_wait_seconds,cooldown_seconds=c.cooldown_seconds,"
            "max_retries=c.max_retries,max_checks=c.max_checks,auto_verification=c.auto_verification,"
            "max_auto_verifications=c.max_auto_verifications,manual_timeout=c.manual_timeout,"
            "page_timeout=c.page_timeout,queue_timeout=c.queue_timeout,"
            "smtp_username=c.smtp_username,smtp_password=c.smtp_password,email_to=c.email_to)))"
        )
        encoded_python = base64.b64encode(code.encode()).decode()
        script_path = str(ROOT / "Set-VisaEnvironment.template.ps1").replace("'", "''")
        python_path = sys.executable.replace("'", "''")
        names = ",".join("'" + name + "'" for name in ENVIRONMENT)
        script = f"""
$ErrorActionPreference = 'Stop'
function Read-Host {{
    throw 'The setup template must never prompt.'
}}
$names = @({names})
$before = @{{}}
foreach ($name in $names) {{
    foreach ($scope in @('User', 'Machine')) {{
        $before["$scope/$name"] = [Environment]::GetEnvironmentVariable($name, $scope)
    }}
}}
. '{script_path}' -ConfigureOnly 6>$null
foreach ($name in $names) {{
    foreach ($scope in @('User', 'Machine')) {{
        if ($before["$scope/$name"] -cne [Environment]::GetEnvironmentVariable($name, $scope)) {{
            throw 'Template unexpectedly changed persistent environment.'
        }}
    }}
}}
& '{python_path}' -c "import base64;exec(base64.b64decode('{encoded_python}'))"
exit $LASTEXITCODE
"""
        # A PowerShell 7 host can export its incompatible module path to Windows
        # PowerShell 5.1. Let this isolated child construct its native defaults.
        environment = {
            key: value for key, value in os.environ.items()
            if not key.upper().startswith("VISA_") and key.upper() != "PSMODULEPATH"
        }
        completed = subprocess.run(
            [shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
             "-EncodedCommand", base64.b64encode(script.encode("utf-16-le")).decode()],
            cwd=ROOT, env=environment, capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout.strip())
        self.assertEqual(result["username"], "your-visa-username")
        self.assertEqual(result["password"], "your-visa-password")
        self.assertEqual(len(result["security_answers"]), 3)
        self.assertEqual(set(result["security_answers"].values()), {"answer1", "answer2", "answer3"})
        self.assertEqual(result["applicants"], ["Exact displayed applicant name"])
        self.assertEqual(result["visa_class"], "B1/B2")
        self.assertEqual(result["existing_appointment"], "2030-01-15T10:00:00")
        self.assertEqual(result["ranges"], [["2026-12-01", "2026-12-15"], ["2026-12-22", "2026-12-25"]])
        self.assertIs(result["auto_booking"], False)
        self.assertEqual(result["daily_times"], ["08:00", "12:00", "17:00"])
        self.assertEqual(result["poll_seconds_min"], 1800)
        self.assertEqual(result["poll_seconds_max"], 3600)
        self.assertEqual(result["click_wait_seconds"], 5)
        self.assertEqual(result["cooldown_seconds"], 86400)
        self.assertEqual(result["max_retries"], 3)
        self.assertEqual(result["max_checks"], 24)
        self.assertIs(result["auto_verification"], True)
        self.assertEqual(result["max_auto_verifications"], 1)
        self.assertEqual(result["manual_timeout"], 900)
        self.assertEqual(result["page_timeout"], 45)
        self.assertEqual(result["queue_timeout"], 1800)
        self.assertEqual(result["smtp_host"], "smtp.gmail.com")
        self.assertEqual(result["smtp_port"], 465)
        self.assertEqual(result["smtp_username"], "your.name@gmail.com")
        self.assertEqual(result["smtp_password"], "abcdefghijklmnop")
        self.assertEqual(result["email_to"], "notifications@example.com")

    def test_child_setup_does_not_configure_parent_but_dot_sourcing_does(self):
        for shell in POWERSHELLS:
            with self.subTest(shell=shell):
                script_path = str(ROOT / "Set-VisaEnvironment.template.ps1").replace("'", "''")
                shell_path = shell.replace("'", "''")
                python_path = sys.executable.replace("'", "''")
                script = f"""
$ErrorActionPreference = 'Stop'
& '{shell_path}' -NoProfile -NonInteractive -ExecutionPolicy Bypass -File '{script_path}' -ConfigureOnly *> $null
if ($LASTEXITCODE -ne 0) {{ throw 'Child setup failed.' }}
$diagnostic = & '{python_path}' main.py --check-config
if ($LASTEXITCODE -ne 2 -or "$diagnostic" -notlike '*VISA_EMAIL_SENDER*') {{
    throw 'Child setup unexpectedly configured its parent.'
}}
. '{script_path}' -ConfigureOnly 6>$null
& '{python_path}' -c "import main; main.build_config().validate(browser=False)"
if ($LASTEXITCODE -ne 0) {{ throw 'Same-process SMTP configuration validation failed.' }}
Write-Output 'scope-regression-passed'
"""
                environment = {
                    key: value for key, value in os.environ.items()
                    if not key.upper().startswith("VISA_") and key.upper() != "PSMODULEPATH"
                }
                completed = subprocess.run(
                    [shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                     "-EncodedCommand", base64.b64encode(script.encode("utf-16-le")).decode()],
                    cwd=ROOT, env=environment, capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertEqual(completed.stdout.strip(), "scope-regression-passed")


if __name__ == "__main__":
    unittest.main()
