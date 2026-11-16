#requires -Version 5.1
<#
Copy to personal\Set-VisaEnvironment.local.ps1 and edit the customization below.
Open PowerShell in the project root (not personal), then run:
    pwsh -File .\personal\Set-VisaEnvironment.local.ps1

The launcher creates/reuses .venv, installs requirements, checks dependencies,
loads configuration and offers three modes. Python runs inside this configured
process, so a separate pwsh invocation works without exporting to its parent.
PowerShell 7 and Windows PowerShell 5.1 are supported. No administrator access
or User/Machine environment changes are needed.

For environment setup ONLY (no installation/menu), dot-source with -ConfigureOnly:
    . .\personal\Set-VisaEnvironment.local.ps1 -ConfigureOnly
Credentials are literal strings, not prompts. Protect the plaintext private copy;
personal/ and .local.ps1 copies are ignored by git.
Do not put real secrets in this tracked template. In single-quoted PowerShell
strings, escape an apostrophe by doubling it, for example 'example''s answer'.
#>
param([switch]$ConfigureOnly)

$dotSourced = $MyInvocation.InvocationName -eq '.'

& {
    $ErrorActionPreference = 'Stop'
    $PSNativeCommandUseErrorActionPreference = $false

    function Invoke-VisaSetupCommand {
        param([string]$Executable, [string[]]$Arguments, [string]$Step)
        & $Executable @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "$Step failed (exit code $LASTEXITCODE). No scheduler was started."
        }
    }

    try {
        # 1. Requirements and installation. Use the shell location, not the script's
        # directory: private copies can live in personal/ under the project root.
        if (-not $ConfigureOnly) {
            Write-Host 'Ensure this PowerShell session is open in the us-visa-scheduler project root.'
            $location = Get-Location
            if ($location.Provider.Name -ne 'FileSystem') {
                throw 'Open a FileSystem location containing the project before running this launcher.'
            }
            $projectRoot = $location.Path
            foreach ($required in @('main.py', 'requirements.txt', 'visa_tool\app.py')) {
                if (-not (Test-Path -LiteralPath (Join-Path $projectRoot $required) -PathType Leaf)) {
                    throw "Not the project root: missing $required. Use Set-Location <project-root> and retry."
                }
            }
            Write-Host "Project root: $projectRoot"
            $venvDirectory = Join-Path $projectRoot '.venv'
            $venvPython = Join-Path $venvDirectory 'Scripts\python.exe'
            if (-not (Test-Path -LiteralPath $venvDirectory)) {
                Write-Host 'Creating .venv using python on PATH...'
                Invoke-VisaSetupCommand -Executable 'python' -Arguments @('-m', 'venv', $venvDirectory) -Step 'Virtual environment creation'
            }
            if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
                throw 'The .venv Python executable is missing. Repair the existing environment before retrying.'
            }
            Write-Host 'Installing requirements into .venv...'
            Invoke-VisaSetupCommand -Executable $venvPython -Arguments @(
                '-m', 'pip', 'install', '-r', (Join-Path $projectRoot 'requirements.txt')
            ) -Step 'Requirements installation'
            Invoke-VisaSetupCommand -Executable $venvPython -Arguments @('-m', 'pip', 'check') -Step 'Dependency check'
        }

        # 2. CUSTOMIZATION: edit placeholders here in your private copy.
        # Credentials are never requested interactively.
        $settings = [ordered]@{
            # USERNAME; example: the username used on the visa authentication page.
            VISA_USERNAME = 'your-visa-username'

            # PASSWORD; example: your visa-account password, NOT your Gmail password.
            VISA_PASSWORD = 'your-visa-password'

            # SECURITY_ANSWERS; JSON question -> answer map. Replace these three question
            # texts with the EXACT displayed Chinese/English questions. Answers stay local.
            # Example JSON: {"Exact question 1":"answer1","Exact question 2":"answer2","Exact question 3":"answer3"}
            VISA_SECURITY_ANSWERS = ([ordered]@{
                'Exact question text 1' = 'answer1'
                'Exact question text 2' = 'answer2'
                'Exact question text 3' = 'answer3'
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
            VISA_SMTP_PASSWORD = 'abcdefghijklmnop' # Example only; replace in private copy.

            # EMAIL_TO; example recipient; can be the same Gmail address as the sender.
            VISA_EMAIL_TO = 'notifications@example.com'
        }

        foreach ($entry in $settings.GetEnumerator()) {
            [System.Environment]::SetEnvironmentVariable(
                $entry.Key, [string]$entry.Value, [System.EnvironmentVariableTarget]::Process
            )
        }
        Write-Host "Set $($settings.Count) VisaTool variables in this PowerShell process only."
        if ($ConfigureOnly) {
            Write-Host 'Configuration loaded only. Run Python in this same process; values were not printed.'
            $global:LASTEXITCODE = 0
            return
        }

        # 3. Run exactly one selected mode. Enter defaults to offline validation.
        Write-Host ''
        Write-Host '1. Check configuration (offline; no email or browser)'
        Write-Host '2. Send test email (one email; no visa-site access)'
        Write-Host '3. Start scheduler (monitoring or one-shot rescheduling per AUTO_BOOKING)'
        do {
            $selection = (Read-Host 'Select mode 1, 2 or 3, then press Enter [default: 1]').Trim()
            if ($selection -eq '') { $selection = '1' }
            if ($selection -notin @('1', '2', '3')) {
                Write-Host 'Invalid selection. Enter 1, 2 or 3.'
            }
        } while ($selection -notin @('1', '2', '3'))

        $runArguments = @((Join-Path $projectRoot 'main.py'))
        switch ($selection) {
            '1' { $runArguments += '--check-config' }
            '2' { $runArguments += '--test-email' }
            '3' { Write-Host "Starting scheduler. VISA_AUTO_BOOKING=$($settings.VISA_AUTO_BOOKING)" }
        }
        & $venvPython @runArguments
        $runExitCode = $LASTEXITCODE
        if ($runExitCode -ne 0) {
            Write-Host "VisaTool exited with code $runExitCode. Review the error above before retrying."
        }
        $global:LASTEXITCODE = $runExitCode
    }
    catch {
        Write-Error -Message $_.Exception.Message -ErrorAction Continue
        $global:LASTEXITCODE = 1
    }
}

if (-not $dotSourced) { exit $LASTEXITCODE }
