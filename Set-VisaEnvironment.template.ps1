#requires -Version 5.1
<#
Copy to Set-VisaEnvironment.local.ps1, edit the examples, then run in the SAME
PowerShell session as Python:
    . .\Set-VisaEnvironment.local.ps1
    .\.venv\Scripts\python.exe main.py --check-config

Scope is Process only: no User/Machine registry values, no administrator access.
Closing PowerShell discards these values. A separate powershell.exe process
cannot set its parent's environment. Secrets are prompted, not written to disk.
The .local.ps1 copy is ignored by git; do not put real secrets in this template.
#>

& {
    $ErrorActionPreference = 'Stop'

    function Read-VisaSecret {
        param([string]$Prompt)
        $secure = Read-Host $Prompt -AsSecureString
        return [System.Net.NetworkCredential]::new('', $secure).Password
    }

    # All prompts complete before any environment variable is changed.
    $settings = [ordered]@{
        # USERNAME; example: the username used on the visa authentication page.
        VISA_USERNAME = 'your-visa-username'

        # PASSWORD; example: your visa-account password, NOT your Gmail password.
        VISA_PASSWORD = Read-VisaSecret 'Visa-account password'

        # SECURITY_ANSWERS; JSON question -> answer map. Replace these three question
        # texts with the EXACT displayed Chinese/English questions. Answers stay local.
        # Example JSON: {"Exact question 1":"answer1","Exact question 2":"answer2","Exact question 3":"answer3"}
        VISA_SECURITY_ANSWERS = ([ordered]@{
            'Exact question text 1' = Read-VisaSecret 'Answer to question 1'
            'Exact question text 2' = Read-VisaSecret 'Answer to question 2'
            'Exact question text 3' = Read-VisaSecret 'Answer to question 3'
        } | ConvertTo-Json -Compress)

        # EXPECTED_APPLICANTS; semicolon-separated exact names.
        # Example for a group: 'Exact Applicant One;Exact Applicant Two'.
        VISA_APPLICANTS = 'Exact displayed applicant name'

        # EXPECTED_VISA_CLASS; example: 'B1/B2' or 'B2', matching the home page.
        VISA_VISA_CLASS = 'B1/B2'

        # EXPECTED_EXISTING_APPOINTMENT; your CURRENT appointment in Beijing time.
        # Example only: replace this with the real old appointment, not a target.
        VISA_EXISTING_APPOINTMENT = '2030-01-15T10:00:00'

        # PREFERRED_DATE_RANGES; JSON nested arrays, inclusive, in priority order.
        # Update example dates when necessary; gaps remain excluded.
        VISA_PREFERRED_DATE_RANGES = '[["2026-12-01","2026-12-15"],["2026-12-22","2026-12-25"]]'

        # AUTO_BOOKING; 'false' means monitor only. Examples: 'false'/'true', '0'/'1'.
        # Do not enable until all identity, date, and safety settings are reviewed.
        VISA_AUTO_BOOKING = 'false'

        # DAILY_EMAIL_TIMES; JSON array of exactly three distinct Beijing HH:MM times.
        VISA_DAILY_EMAIL_TIMES = '["08:00","12:00","17:00"]'

        # Operational budgets below are conservative local choices, not site allowances.
        # CLICK_WAIT_SECONDS; nonnegative seconds before EACH post-login UI action.
        # Armed only after validating the visa home page: Reschedule, dropdowns,
        # preferred date, time slot and Submit. No delay for login/questions/CAPTCHA.
        # Example active value: '3'; '0' disables it. Revalidate after the pause.
        VISA_CLICK_WAIT_SECONDS = '5'

        # POLL_SECONDS_MIN; inclusive lower bound in positive integer seconds.
        # Example: 1800 = 30 minutes; active example '300' = 5 minutes.
        # This is a pause AFTER cycle work, not the complete observation interval.
        VISA_POLL_SECONDS_MIN = '1800'

        # POLL_SECONDS_MAX; inclusive upper bound, at least POLL_SECONDS_MIN.
        # Example: 3600 = 60 minutes. Active starting example '540' leaves some room
        # below 10 minutes for work, but cannot guarantee a sub-10-minute interval.
        # Equal bounds retain a fixed delay; samples may repeat.
        VISA_POLL_SECONDS_MAX = '3600'

        # BLOCK_COOLDOWN_SECONDS; positive fallback after detected restrictions.
        # '86400' = 24 hours; a longer observed Retry-After always wins.
        # '7200' = 2 hours is allowed but NOT a verified account-unblock period.
        # Cooldown/recovery state persists across restarts.
        VISA_BLOCK_COOLDOWN_SECONDS = '86400'

        # MAX_RECOVERY_RETRIES; integer 0..3, AFTER the initial restriction.
        # '0' stops on the first restriction. Counts recovery cycles, not HTTP calls.
        # Never retries a booking submission. Budget is persisted for the task.
        VISA_MAX_RECOVERY_RETRIES = '3'

        # MAX_CHECKS_PER_RUN; positive successful-observation budget for this TASK.
        # Despite the name, restarts do not reset it. One observation can issue
        # multiple HTTP requests. Start at '24'; '150' increases exposure substantially.
        VISA_MAX_CHECKS_PER_RUN = '24'

        # AUTO_VERIFICATION; true/false or 1/0, only for the Cloudflare GUI helper.
        # 'false' -> email/manual handoff if a challenge persists; it does not
        # disable automated username/password or security-question entry.
        VISA_AUTO_VERIFICATION = 'true'

        # MAX_AUTO_VERIFICATIONS; nonnegative helper-call cap per process run.
        # One invocation per challenge episode, then manual fallback if unresolved.
        # A refused/unsafe invocation still counts. '0' disables automatic attempts.
        # '10' is accepted across episodes, NOT ten retries on one checkbox.
        # Conservative starting value remains '1'.
        VISA_MAX_AUTO_VERIFICATIONS = '1'

        # MANUAL_VERIFICATION_TIMEOUT_SECONDS; positive manual-handoff deadline.
        # '900' = 15 minutes starting before the notice is sent; then stop.
        VISA_MANUAL_VERIFICATION_TIMEOUT_SECONDS = '900'

        # PAGE_TIMEOUT_SECONDS; positive page/navigation/response wait.
        # '45' is not a polling interval. The worker watchdog additionally allows
        # command overhead and each operation's maximum configured click pauses.
        # The fixed post-submit 90-second observation is independent.
        VISA_PAGE_TIMEOUT_SECONDS = '45'

        # QUEUE_TIMEOUT_SECONDS; positive budget per virtual waiting-room episode.
        # '1800' = 30 minutes; let the site auto-refresh, then stop if still queued.
        VISA_QUEUE_TIMEOUT_SECONDS = '1800'

        # SMTP_HOST; Gmail example: smtp.gmail.com.
        VISA_SMTP_HOST = 'smtp.gmail.com'

        # SMTP_PORT; Gmail implicit TLS example: 465. Not STARTTLS/587.
        VISA_SMTP_PORT = '465'

        # SMTP_USERNAME; full Gmail address, also used as the From address.
        VISA_EMAIL_SENDER = 'your.name@gmail.com'

        # SMTP_PASSWORD; Google-generated app password (16 characters).
        # Enable Google 2-Step Verification first. Do NOT enter your normal password.
        VISA_SMTP_PASSWORD = Read-VisaSecret 'Gmail app password (not your Google password)'

        # EMAIL_TO; example recipient; can be the same Gmail address as the sender.
        VISA_EMAIL_TO = 'notifications@example.com'
    }

    foreach ($entry in $settings.GetEnumerator()) {
        [System.Environment]::SetEnvironmentVariable(
            $entry.Key, [string]$entry.Value, [System.EnvironmentVariableTarget]::Process
        )
    }
    Write-Host "Set $($settings.Count) VisaTool variables in this PowerShell process only."
    Write-Host 'Run Python from this same session. Secret values were not printed.'
}
