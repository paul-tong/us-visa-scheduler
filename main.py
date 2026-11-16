"""Configure here, then run: python main.py --check-config."""
import os
from pathlib import Path

# Environment values override the fallbacks below only when the variable exists.
# A present-but-empty/invalid value is NOT replaced by a fallback.
# Conversion is deferred to build_config(), so --help works even with bad settings.
# Use environment variables for secrets; never commit real passwords/answers.
# Example VISA_USERNAME: "your-visa-username".
USERNAME = os.environ.get("VISA_USERNAME", "")
# Example VISA_PASSWORD: "your-visa-password" (replace locally; not a Gmail app password).
PASSWORD = os.environ.get("VISA_PASSWORD", "")
# VISA_SECURITY_ANSWERS is a JSON object; it replaces, rather than merges, the map.
# Example: {"Exact question 1":"answer1","Exact question 2":"answer2","Exact question 3":"answer3"}
SECURITY_ANSWERS = os.environ.get("VISA_SECURITY_ANSWERS", {
    # Fallback map: exact displayed Chinese/English question text -> answer.
    # "Your configured question": os.environ.get("VISA_ANSWER_1", ""),
})
# Example VISA_APPLICANTS: "Exact Applicant One;Exact Applicant Two".
EXPECTED_APPLICANTS = [
    name.strip() for name in os.environ.get("VISA_APPLICANTS", "").split(";")
    if name.strip()
]
# Example VISA_VISA_CLASS: "B1/B2" or "B2", exactly as shown on the home page.
EXPECTED_VISA_CLASS = os.environ.get("VISA_VISA_CLASS", "B1/B2")
# VISA_EXISTING_APPOINTMENT: current appointment, NOT the desired target.
# Example: "2030-01-15T10:00:00", a Beijing-local ISO datetime.
EXPECTED_EXISTING_APPOINTMENT = os.environ.get("VISA_EXISTING_APPOINTMENT", "")
# VISA_PREFERRED_DATE_RANGES: JSON array of inclusive ranges, highest priority first.
# Example: [["2026-12-01","2026-12-15"],["2026-12-22","2026-12-25"]]
PREFERRED_DATE_RANGES = os.environ.get("VISA_PREFERRED_DATE_RANGES", [
    ("2026-12-01", "2026-12-15"),
    ("2026-12-22", "2026-12-25"),
])
# VISA_AUTO_BOOKING: "true"/"false" or "1"/"0" (case-insensitive).
# Example "false": no date, time-slot, or Submit clicks. Invalid strings fail closed.
AUTO_BOOKING = os.environ.get("VISA_AUTO_BOOKING", False)
# VISA_DAILY_EMAIL_TIMES: JSON array of exactly three Beijing (UTC+08:00) times.
# Example: ["08:00","12:00","17:00"]
DAILY_EMAIL_TIMES = os.environ.get("VISA_DAILY_EMAIL_TIMES", ["08:00", "12:00", "17:00"])

# Example VISA_SMTP_HOST: "smtp.gmail.com"; Gmail is the fallback provider.
SMTP_HOST = os.environ.get("VISA_SMTP_HOST", "smtp.gmail.com")
# Example VISA_SMTP_PORT: "465" (implicit TLS). STARTTLS/587 is not implemented.
SMTP_PORT = os.environ.get("VISA_SMTP_PORT", 465)
# Example VISA_EMAIL_SENDER: "your.name@gmail.com" (full Gmail login and From address).
SMTP_USERNAME = os.environ.get("VISA_EMAIL_SENDER", "")
# VISA_SMTP_PASSWORD: Google app password; format example only: "abcdefghijklmnop".
# Do not use your normal Google password or the visa-account password.
SMTP_PASSWORD = os.environ.get("VISA_SMTP_PASSWORD", "")
# Example VISA_EMAIL_TO: "notifications@example.com"; may equal the sender.
EMAIL_TO = os.environ.get("VISA_EMAIL_TO", "")

# Operational budgets: local conservative defaults, NOT published website-safe limits.
# Wait before each tool-driven UI click/selection AFTER validating the visa home page.
# Includes Reschedule, post/calendar dropdowns, a preferred date, time slot and Submit.
# Does not delay credentials, security answers, CAPTCHA interaction, or read-only checks.
# Nonnegative integer seconds; 0 disables pacing. Example active value: "3".
CLICK_WAIT_SECONDS = os.environ.get("VISA_CLICK_WAIT_SECONDS", 5)

# Inclusive random pause AFTER a completed observation, not a start-to-start period.
# Work and click waits add to the interval. Positive integers; min <= max.
# Examples: conservative "1800"/"3600"; active starting example "300"/"540".
# Equal bounds retain fixed pacing. Randomization does not guarantee no blocking.
POLL_SECONDS_MIN = os.environ.get("VISA_POLL_SECONDS_MIN", 1800)
POLL_SECONDS_MAX = os.environ.get("VISA_POLL_SECONDS_MAX", 3600)

# Fallback pause after a detected restriction; a longer Retry-After always wins.
# Persisted across restarts. "86400" = 24 hours; "7200" = 2 hours is NOT a known reset.
BLOCK_COOLDOWN_SECONDS = os.environ.get("VISA_BLOCK_COOLDOWN_SECONDS", 86400)
# Initial failure plus at most this many recovery cycles (0-3), persisted per task.
# 0 stops at the first restriction. This never authorizes retrying a booking submit.
MAX_RECOVERY_RETRIES = os.environ.get("VISA_MAX_RECOVERY_RETRIES", 3)
# Successful observations allowed for this persistent task, despite the old name.
# Restarts do NOT reset the count. One check may issue multiple HTTP requests.
# Start with "24"; "150" is a larger exposure budget, not a verified site allowance.
MAX_CHECKS_PER_RUN = os.environ.get("VISA_MAX_CHECKS_PER_RUN", 24)
# Enables only the best-effort Cloudflare GUI helper; accepts true/false or 1/0.
# False -> email/manual fallback if a challenge persists; login/answers stay automatic.
AUTO_VERIFICATION = os.environ.get("VISA_AUTO_VERIFICATION", True)
# Maximum helper invocations in this process run, across separate challenge episodes.
# At most one invocation per episode, then manual fallback if it does not resolve.
# Calls that cannot safely click still consume budget. 0 disables automatic attempts.
# Example "10" is accepted but not recommended as a starting budget; default is 1.
MAX_AUTO_VERIFICATIONS = os.environ.get("VISA_MAX_AUTO_VERIFICATIONS", 1)
# Positive seconds for the emailed manual handoff before terminal stop.
# Example "900" = 15 minutes; the helper-result grace period is a separate 60 seconds.
MANUAL_VERIFICATION_TIMEOUT_SECONDS = os.environ.get("VISA_MANUAL_VERIFICATION_TIMEOUT_SECONDS", 900)
# Positive seconds for normal page/navigation/response waits, not a polling interval.
# The worker watchdog adds command overhead and applicable click delays.
# Example "45"; this does not change the fixed 90-second post-submit observation.
PAGE_TIMEOUT_SECONDS = os.environ.get("VISA_PAGE_TIMEOUT_SECONDS", 45)
# Positive seconds per waiting-room episode. Allow the site's automatic refresh;
# no forced queue refreshes. Example "1800" = 30 minutes, then stop and notify.
QUEUE_TIMEOUT_SECONDS = os.environ.get("VISA_QUEUE_TIMEOUT_SECONDS", 1800)


def build_config():
    from visa_tool.core import Config
    from visa_tool.settings import (
        answer_setting, boolean_setting, integer_setting, range_setting, time_setting,
    )

    return Config(
        root=Path(__file__).resolve().parent,
        username=USERNAME,
        password=PASSWORD,
        security_answers=answer_setting("VISA_SECURITY_ANSWERS", SECURITY_ANSWERS),
        applicants=tuple(EXPECTED_APPLICANTS),
        visa_class=EXPECTED_VISA_CLASS,
        existing_appointment=EXPECTED_EXISTING_APPOINTMENT,
        ranges=range_setting("VISA_PREFERRED_DATE_RANGES", PREFERRED_DATE_RANGES),
        auto_booking=boolean_setting("VISA_AUTO_BOOKING", AUTO_BOOKING),
        daily_times=time_setting("VISA_DAILY_EMAIL_TIMES", DAILY_EMAIL_TIMES),
        smtp_host=SMTP_HOST,
        smtp_port=integer_setting("VISA_SMTP_PORT", SMTP_PORT),
        smtp_username=SMTP_USERNAME,
        smtp_password=SMTP_PASSWORD,
        email_to=EMAIL_TO,
        click_wait_seconds=integer_setting("VISA_CLICK_WAIT_SECONDS", CLICK_WAIT_SECONDS),
        poll_seconds_min=integer_setting("VISA_POLL_SECONDS_MIN", POLL_SECONDS_MIN),
        poll_seconds_max=integer_setting("VISA_POLL_SECONDS_MAX", POLL_SECONDS_MAX),
        cooldown_seconds=integer_setting("VISA_BLOCK_COOLDOWN_SECONDS", BLOCK_COOLDOWN_SECONDS),
        max_retries=integer_setting("VISA_MAX_RECOVERY_RETRIES", MAX_RECOVERY_RETRIES),
        max_checks=integer_setting("VISA_MAX_CHECKS_PER_RUN", MAX_CHECKS_PER_RUN),
        auto_verification=boolean_setting("VISA_AUTO_VERIFICATION", AUTO_VERIFICATION),
        max_auto_verifications=integer_setting("VISA_MAX_AUTO_VERIFICATIONS", MAX_AUTO_VERIFICATIONS),
        manual_timeout=integer_setting("VISA_MANUAL_VERIFICATION_TIMEOUT_SECONDS", MANUAL_VERIFICATION_TIMEOUT_SECONDS),
        page_timeout=integer_setting("VISA_PAGE_TIMEOUT_SECONDS", PAGE_TIMEOUT_SECONDS),
        queue_timeout=integer_setting("VISA_QUEUE_TIMEOUT_SECONDS", QUEUE_TIMEOUT_SECONDS),
    )


if __name__ == "__main__":
    from visa_tool.app import cli

    raise SystemExit(cli(build_config))
