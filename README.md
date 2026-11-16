# Wuhan visitor visa appointment assistant

[简体中文](README.zh-CN.md)

A local Windows application that monitors the U.S. visa scheduling website for
Wuhan B1/B2 or B2 interview dates. It can optionally make **one guarded rescheduling
submission** for an existing appointment. Monitoring is enabled by default;
automatic rescheduling must be explicitly enabled.

Use automation only where the service provider permits it. The tool does not
guarantee access, CAPTCHA completion, avoidance of account restrictions, or a
successful booking. It is not a general-purpose booking service.

## Features

- Automatic credential entry and matching of the two displayed security questions
  against a locally configured question/answer map.
- Bounded, best-effort GUI verification with email-notified manual fallback.
- Availability monitoring through the normal website UI, including all dates
  returned by the observed response rather than only visible calendar months.
- Ordered, inclusive date preferences. Unpreferred dates are logged, never selected.
- Monitor-only mode that never selects a date, time slot or Submit.
- Existing-appointment, applicant, visa-class and Wuhan-post checks; only the
  verified reschedule link is used on the home page.
- Post-login click pacing, randomized observation pauses and bounded recovery.
- A persistent one-submission guard, a 90-second result-observation window,
  local daily logs and SMTP notifications.

New appointments, other consulates, OFC/biometrics scheduling, cancellation and
application replacement are not supported. The client never invokes cancellation;
server-side preservation of the old appointment and rescheduling quota accounting
cannot be guaranteed.

## Requirements

- Windows with an interactive desktop and Google Chrome installed.
- PowerShell 7 or Windows PowerShell 5.1.
- Python on `PATH`, with `venv` and `pip`, compatible with `requirements.txt`.
  The pinned dependencies were originally exercised on Python 3.9.13; not every
  newer Python/Chrome combination has been tested.
- An existing Wuhan visitor-visa appointment and an SMTP account.
- Network access for package installation, initial ChromeDriver provisioning,
  email delivery and website access.

The launcher does not install Python or Chrome, change execution policy, or request
administrator access. Follow the local execution policy when running scripts.
Dependencies are pinned in `requirements.txt`; the launcher does not use `--upgrade`.

## Quick start

### 1. Create a private launcher

Open PowerShell in the cloned project root. Replace the example path below:

```powershell
Set-Location 'C:\path\to\us-visa-scheduler'
New-Item -ItemType Directory -Force .\personal | Out-Null
if (-not (Test-Path .\personal\Set-VisaEnvironment.local.ps1)) {
    Copy-Item .\Set-VisaEnvironment.template.ps1 .\personal\Set-VisaEnvironment.local.ps1
}
notepad .\personal\Set-VisaEnvironment.local.ps1
```

Edit the **CUSTOMIZATION** section: credentials, exact security questions/answers,
applicant names, current appointment, preferred ranges and notification settings.
Replace every placeholder and expired example date. Keep `VISA_AUTO_BOOKING`
set to `'false'` initially.

Credentials are literal strings; no password or security-answer prompts appear.
Inside single-quoted PowerShell strings, escape an apostrophe by doubling it:
`'example''s answer'`. Question text and answers can contain Chinese characters.
Save the script in an encoding supported by the selected PowerShell host; use
UTF-8 with BOM for non-ASCII text when also using Windows PowerShell 5.1.

The private file contains plaintext secrets. `personal/` and
`Set-VisaEnvironment.local.ps1` are git-ignored, not encrypted. Protect local access
and never commit real credentials into the tracked template.

### 2. Run the launcher

From the **project root**, not the `personal` directory:

```powershell
pwsh -File .\personal\Set-VisaEnvironment.local.ps1
```

Windows PowerShell users can run:

```powershell
powershell.exe -File .\personal\Set-VisaEnvironment.local.ps1
```

The launcher:

1. Displays a project-root reminder and validates the current working directory.
2. Creates `.venv` if absent, or reuses its existing Python executable.
3. Runs `pip install -r requirements.txt` and `pip check` using that executable.
4. Loads the customization into its process environment without printing secrets.
5. Displays the menu and runs exactly one selected mode.

| Selection | Python command | Effect |
|---|---|---|
| `1` or Enter | `main.py --check-config` | Validate settings without SMTP, browser access or application-state creation. |
| `2` | `main.py --test-email` | Send one explicit test email; no visa-site access. |
| `3` | `main.py` | Start monitoring, or guarded rescheduling if enabled. |

Type the number and press Enter. Invalid choices are requested again; the default
is offline validation, never booking. **Installation precedes the menu and can use
the network even when selecting option 1.** Setup failures stop before the menu or
scheduler. A broken existing `.venv` is reported rather than silently replaced.
The selected application's exit code is returned; failed runs are not retried.

Python is launched by the configured PowerShell process, so `pwsh -File ...` works
without copying variables back into the parent terminal. No separate activation,
installation commands or Python command is required for this workflow.

Existing private copies are not automatically updated. When upgrading, merge their
customization into a fresh copy of the current template; do not overwrite secrets
or assume an old setup-only script contains the new launcher.

## Configuration reference

The launcher explicitly sets all 25 variables from its customization section,
overriding inherited values for those names in its own process. Python reads
environment values first; an absent variable uses the corresponding fallback at
the top of `main.py`. Present-but-empty or malformed structured values fail rather
than falling back silently. Settings are loaded when Python starts.

### Account, appointment and email

| Property | Environment variable | Format / fallback |
|---|---|---|
| `USERNAME` | `VISA_USERNAME` | Visa username; empty Python fallback. |
| `PASSWORD` | `VISA_PASSWORD` | Visa password; empty fallback. |
| `SECURITY_ANSWERS` | `VISA_SECURITY_ANSWERS` | JSON question-to-answer object; fallback map initially empty. The template converts its PowerShell map to JSON. |
| `EXPECTED_APPLICANTS` | `VISA_APPLICANTS` | Exact applicant names separated by `;`; empty fallback. |
| `EXPECTED_VISA_CLASS` | `VISA_VISA_CLASS` | Exact displayed `B1/B2` or `B2`; fallback `B1/B2`. |
| `EXPECTED_EXISTING_APPOINTMENT` | `VISA_EXISTING_APPOINTMENT` | Current appointment's Beijing-local ISO datetime, e.g. `2030-01-15T10:00:00`; empty fallback. |
| `PREFERRED_DATE_RANGES` | `VISA_PREFERRED_DATE_RANGES` | JSON array of `[start, end]` date pairs, most preferred first; replace example ranges. |
| `AUTO_BOOKING` | `VISA_AUTO_BOOKING` | `true`/`false` or `1`/`0`, case-insensitive; fallback `False`. |
| `DAILY_EMAIL_TIMES` | `VISA_DAILY_EMAIL_TIMES` | Exactly three distinct Beijing HH:MM times; fallback `["08:00","12:00","17:00"]`. |
| `SMTP_HOST` | `VISA_SMTP_HOST` | SMTP hostname; fallback `smtp.gmail.com`. |
| `SMTP_PORT` | `VISA_SMTP_PORT` | Implicit TLS port; fallback `465`. |
| `SMTP_USERNAME` | `VISA_EMAIL_SENDER` | Full sending address; empty fallback. |
| `SMTP_PASSWORD` | `VISA_SMTP_PASSWORD` | SMTP app password; empty fallback. |
| `EMAIL_TO` | `VISA_EMAIL_TO` | Recipient address; empty fallback. |

Use exact displayed security-question text. The JSON map replaces the fallback map,
not merges with it; duplicate keys, unknown questions and invalid shapes fail closed.
For preferred dates, the first range with availability wins, then its earliest date.
Range endpoints are inclusive; gaps remain excluded. The existing-appointment
timestamp is a safety check, not a desired target.

For Gmail, use `smtp.gmail.com:465`, a full Gmail sender address and a Google app
password, not the normal account password. App-password availability depends on
Google account policy and two-step verification. This implementation uses implicit
TLS and password-based SMTP, not STARTTLS/587 or OAuth. SMTP acceptance does not
guarantee inbox delivery.

Official references:
`https://developers.google.com/workspace/gmail/imap/imap-smtp`
and `https://support.google.com/accounts/answer/185833`.

### Operational budgets

These are local limits, not published website quotas or guaranteed safe rates.
All numeric values are integers; timeouts, cooldown, observation count and polling
bounds must be positive. Click delay and helper cap may be zero; retries are 0-3.

| Property | Environment variable | Default | Meaning |
|---|---|---:|---|
| `CLICK_WAIT_SECONDS` | `VISA_CLICK_WAIT_SECONDS` | 5 | Wait before each covered post-login UI action; zero disables pacing. |
| `POLL_SECONDS_MIN` | `VISA_POLL_SECONDS_MIN` | 1800 | Inclusive minimum random pause after a completed observation. |
| `POLL_SECONDS_MAX` | `VISA_POLL_SECONDS_MAX` | 3600 | Inclusive maximum pause, at least the minimum. Equal bounds produce a fixed pause. |
| `BLOCK_COOLDOWN_SECONDS` | `VISA_BLOCK_COOLDOWN_SECONDS` | 86400 | Restriction fallback wait; a longer observed `Retry-After` wins. Persisted across restarts. |
| `MAX_RECOVERY_RETRIES` | `VISA_MAX_RECOVERY_RETRIES` | 3 | Additional recovery cycles after the initial restriction; persisted per task. Never retries Submit. |
| `MAX_CHECKS_PER_RUN` | `VISA_MAX_CHECKS_PER_RUN` | 24 | Successful observations for the persistent task; despite the name, restarts do not reset it. |
| `AUTO_VERIFICATION` | `VISA_AUTO_VERIFICATION` | `True` | Enables the GUI verification helper only. False leaves credentials/answers automated but uses manual challenge fallback. |
| `MAX_AUTO_VERIFICATIONS` | `VISA_MAX_AUTO_VERIFICATIONS` | 1 | Helper calls across challenge episodes in one process. Zero disables attempts; at most one call per episode before fallback. |
| `MANUAL_VERIFICATION_TIMEOUT_SECONDS` | `VISA_MANUAL_VERIFICATION_TIMEOUT_SECONDS` | 900 | Manual-handoff deadline, starting before notification delivery. |
| `PAGE_TIMEOUT_SECONDS` | `VISA_PAGE_TIMEOUT_SECONDS` | 45 | Normal page/response wait; worker timeouts additionally allow click delays and command overhead. |
| `QUEUE_TIMEOUT_SECONDS` | `VISA_QUEUE_TIMEOUT_SECONDS` | 1800 | Wait per website waiting-room episode; no forced refresh. |

Pacing starts only after validating the authenticated home page. It covers
Reschedule, post/calendar dropdown selections, preferred date, time slot and
Submit. Targets/context are rechecked after each pause. Authentication, CAPTCHA
interaction and read-only result checks are not delayed by this setting.

Each continuing observation samples a fresh integer pause. Processing time adds
to the interval: `300-600` seconds does not guarantee observations within ten minutes.
Faster polling, larger check budgets or more helper calls increase activity and
are not a way to bypass restrictions. Cooldowns, verification deadlines and the
90-second result window are not randomized.

The helper cap counts invocations, including refused/unsafe calls, not internal
clicks or requests. A cap of 10 does not retry the same checkbox ten times.
Unresolved challenges use the emailed manual handoff; automatic interaction has
an independent up-to-60-second result observation. Verification is forbidden after
a possible booking submission. There is also a persisted local cap of two
credential submissions per Beijing day, independent of website limits.

## Workflow and safety

```text
Launcher: verify root -> create/reuse venv -> install/check -> configure -> select mode
Scheduler: validate -> instance lock and durable state -> email preflight -> sign in
  -> verification / manual fallback -> answer questions -> validate home
  -> Reschedule only -> validate applicants and existing appointment -> observe dates
  -> no match / monitor-only: log, notify, wait and repeat within budgets
  -> preferred day: first usable time slot -> revalidate -> persist submission latch
  -> Submit once -> observe for 90 seconds -> report outcome -> close browser -> stop
```

The first usable time row must have sufficient capacity for all expected applicants.
If none remains, no submission is made. SUCCESS requires the site's `AllScheduled`
response correlated with the requested date/entry; explicit rejection is FAILURE;
missing or conflicting evidence is UNKNOWN. A redirect or title alone is not proof.

The full result window begins after the Submit command returns or raises, so its
pre-click delay cannot shorten observation. After dispatch may have begun, there
is no automatic verification, refresh, reauthentication or resubmission. Interruptions
can cut observation short, but the persistent latch still prevents another attempt.

Chrome uses Beijing time and must remain visible for GUI verification. If manual
verification is requested, complete only the challenge in that browser; do not
select dates or click Submit yourself. Expected next-page detection resumes the
flow. A hung/lost worker stops the run instead. Owned worker/Chrome processes are
isolated; unrelated browser windows are not targeted.

## Logs, notifications and recovery

Paths are relative to the project root:

| Path | Contents |
|---|---|
| `logs\EventLog_YYYY_MM_DD.jsonl` | Actions, errors, retries, `POLL_WAIT` and `CLICK_WAIT`. |
| `logs\AvailabilityLog_YYYY_MM_DD.jsonl` | All returned dates, preference flags and priority ranks. |
| `logs\BookingLog_YYYY_MM_DD.jsonl` | Attempted Beijing date/time and outcome. |
| `.state\state.json` | Stop/retry/check counts, cooldown, cached dates and email outbox. |
| `.state\submission.json` | Permanent, exclusively created submission guard. |

Logs include fixed PST (UTC-08:00), UTC and Beijing timestamps. Files rotate on the
Beijing date boundary via heartbeat; same-day restarts use new suffixes without
truncation. Protect logs, state and browser profiles as personal information.

Notifications cover preferred availability, booking outcomes, manual verification,
restrictions, errors and three daily Beijing-time summaries. Preferred-availability
emails can repeat on each matching observation. Daily summaries use cached results
and their age, not a forced query. Notifications stop with the task.

Email delivery has bounded attempts and a persistent outbox. For mail-only recovery,
load settings with `-ConfigureOnly`, then run:

```powershell
.\.venv\Scripts\python.exe main.py --send-pending
```

This resets only unsent mail attempts; it does not open a browser or clear the booking
guard. A crash between SMTP acceptance and local acknowledgement can duplicate email.

**Do not delete `.state` just to restart a stopped task.** Reconcile the actual
appointment and remaining allowance before deliberately archiving/resetting a task.
There is no automatic reset. The local lock cannot coordinate separate project
copies or machines; use one active copy per account.

## Manual commands and troubleshooting

To load configuration without installation or a menu, use the same PowerShell
process as the subsequent Python command:

```powershell
. .\personal\Set-VisaEnvironment.local.ps1 -ConfigureOnly
.\.venv\Scripts\python.exe main.py --check-config
```

For manual installation, the equivalent commands are:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

| Problem | Action |
|---|---|
| Project-root warning/error | Change to the directory containing `main.py`, `requirements.txt` and `visa_tool`, not the private script's directory. |
| Python or `.venv` error | Check the Python installation and environment. The launcher will not delete/replace a damaged environment. |
| Package install or `pip check` failure | Resolve the reported dependency/network problem before starting monitoring. |
| Missing SMTP variables | Use the launcher, or dot-source with `-ConfigureOnly` before manual Python. A separate setup-only child cannot change its parent's environment. |
| Menu missing | Upgrade an older private setup copy to the current launcher while preserving customization. |
| Verification timeout or page mismatch | Inspect the stopped run; unknown layouts fail closed rather than inventing availability or success. |
| UNKNOWN booking result / restart refused | Check the official account manually; do not bypass the submission guard. |

Application exit codes: `0` normal completion/budget stop; `1` operational error,
failed/unknown booking or unsent notifications; `2` configuration/startup/refused
restart. Launcher setup errors return `1`. A zero code is not booking confirmation.

## Development and validation

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
# Optional Chrome fixtures, using synthetic loopback pages:
$env:VISA_LOCAL_BROWSER_TESTS = '1'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
Remove-Item Env:\VISA_LOCAL_BROWSER_TESTS
```

Launcher tests use temporary projects and recording `pip`/application fixtures,
not real package downloads, email or visa actions. They cover both available
PowerShell hosts, environment inheritance, first-run setup, menu routing and failure
handling. Other tests cover preference selection, no-click mode, authentication
mapping, pacing, durable submission limits, outcomes, recovery, logs and email.
Optional browser tests use local pages; a worker smoke test opens only a blank page.

| Component | Responsibility |
|---|---|
| `Set-VisaEnvironment.template.ps1` | Bootstrap, private configuration template and launch menu. |
| `main.py`, `visa_tool\settings.py` | Environment/fallback configuration and strict conversion. |
| `visa_tool\app.py` | Scheduler state machine and CLI modes. |
| `visa_tool\browser.py` | Guarded UI adapter and isolated browser worker. |
| `visa_tool\core.py` | Validation, persistence, locking, logs, mail and clocks. |
| `tests` | Unit and opt-in browser/PowerShell integration coverage. |

Live CAPTCHA acceptance, site quotas and server-side booking semantics are not
established by these tests. Changes to live markup may require adapter updates.

Original project acknowledgement: `SYuan03/VisaAppointmentWatcher` and
`CChen19/us-visa-scheduler`.
