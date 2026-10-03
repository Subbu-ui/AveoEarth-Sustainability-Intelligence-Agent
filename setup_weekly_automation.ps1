# ============================================================
# AVEOEARTH WEEKLY AGENT AUTOMATION SETUP
# ============================================================

$ProjectDir = "C:\Users\SUBHASHISH\OneDrive\Desktop\AveoEarth-Agent"

$RunnerFile = Join-Path $ProjectDir "weekly_agent_run.ps1"

$TaskName = "AveoEarth Weekly Intelligence Agent"

# Every Monday at 8:00 AM
$ScheduleTime = "08:00"


# ============================================================
# CHECK PROJECT
# ============================================================

Write-Host ""
Write-Host "==============================================="
Write-Host "AVEOEARTH AUTOMATION SETUP"
Write-Host "==============================================="

if (-not (Test-Path $ProjectDir)) {

    Write-Host "ERROR: Project folder not found:"
    Write-Host $ProjectDir

    exit 1
}


$PythonExe = Join-Path $ProjectDir ".venv\Scripts\python.exe"

$AgentScript = Join-Path $ProjectDir "run_agent.py"


if (-not (Test-Path $PythonExe)) {

    Write-Host "ERROR: Virtual environment Python not found:"
    Write-Host $PythonExe

    exit 1
}


if (-not (Test-Path $AgentScript)) {

    Write-Host "ERROR: run_agent.py not found."

    exit 1
}


# ============================================================
# CREATE WEEKLY RUNNER SCRIPT
# ============================================================

$RunnerContent = @'
# ============================================================
# AVEOEARTH WEEKLY INTELLIGENCE RUN
# ============================================================

$ProjectDir = "C:\Users\SUBHASHISH\OneDrive\Desktop\AveoEarth-Agent"

$PythonExe = Join-Path $ProjectDir ".venv\Scripts\python.exe"

$AgentScript = Join-Path $ProjectDir "run_agent.py"

$LogDir = Join-Path $ProjectDir "scheduled_logs"


# ------------------------------------------------------------
# CREATE LOG DIRECTORY
# ------------------------------------------------------------

if (-not (Test-Path $LogDir)) {

    New-Item `
        -ItemType Directory `
        -Path $LogDir `
        | Out-Null
}


$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

$LogFile = Join-Path `
    $LogDir `
    "weekly_agent_$Timestamp.txt"


# ------------------------------------------------------------
# FORCE UTF-8
# ------------------------------------------------------------

$env:PYTHONUTF8 = "1"

$env:PYTHONIOENCODING = "utf-8"

$env:PYTHONUNBUFFERED = "1"


# ------------------------------------------------------------
# START LOG
# ------------------------------------------------------------

"===============================================" |
    Out-File $LogFile

"AVEOEARTH WEEKLY AGENT RUN" |
    Out-File $LogFile -Append

"===============================================" |
    Out-File $LogFile -Append

"Started: $(Get-Date)" |
    Out-File $LogFile -Append

"" |
    Out-File $LogFile -Append


# ------------------------------------------------------------
# CHECK OLLAMA
# ------------------------------------------------------------

"Ollama check..." |
    Out-File $LogFile -Append


$OllamaRunning = $false


try {

    $Response = Invoke-WebRequest `
        -Uri "http://localhost:11434/api/tags" `
        -UseBasicParsing `
        -TimeoutSec 4

    if ($Response.StatusCode -eq 200) {

        $OllamaRunning = $true
    }

}
catch {

    $OllamaRunning = $false
}


# ------------------------------------------------------------
# START OLLAMA IF REQUIRED
# ------------------------------------------------------------

if (-not $OllamaRunning) {

    "Ollama is not running. Attempting to start it..." |
        Out-File $LogFile -Append


    $OllamaExe = Join-Path `
        $env:LOCALAPPDATA `
        "Programs\Ollama\ollama.exe"


    if (Test-Path $OllamaExe) {

        Start-Process `
            -FilePath $OllamaExe `
            -ArgumentList "serve" `
            -WindowStyle Hidden


        Start-Sleep -Seconds 8


        try {

            $Response = Invoke-WebRequest `
                -Uri "http://localhost:11434/api/tags" `
                -UseBasicParsing `
                -TimeoutSec 5


            if ($Response.StatusCode -eq 200) {

                $OllamaRunning = $true

                "Ollama started successfully." |
                    Out-File $LogFile -Append
            }

        }
        catch {

            $OllamaRunning = $false
        }

    }

}


# ------------------------------------------------------------
# STOP IF OLLAMA IS UNAVAILABLE
# ------------------------------------------------------------

if (-not $OllamaRunning) {

    "ERROR: Ollama could not be started." |
        Out-File $LogFile -Append

    "Agent run cancelled." |
        Out-File $LogFile -Append

    exit 1
}


# ------------------------------------------------------------
# RUN AVEOEARTH AGENT
# ------------------------------------------------------------

"" |
    Out-File $LogFile -Append

"Starting AveoEarth intelligence pipeline..." |
    Out-File $LogFile -Append

"" |
    Out-File $LogFile -Append


Set-Location $ProjectDir


& $PythonExe `
    -u `
    $AgentScript `
    *>> $LogFile


$ExitCode = $LASTEXITCODE


# ------------------------------------------------------------
# FINAL STATUS
# ------------------------------------------------------------

"" |
    Out-File $LogFile -Append

"===============================================" |
    Out-File $LogFile -Append


if ($ExitCode -eq 0) {

    "WEEKLY AGENT RUN COMPLETED SUCCESSFULLY" |
        Out-File $LogFile -Append

}
else {

    "WEEKLY AGENT RUN FAILED" |
        Out-File $LogFile -Append

    "Exit code: $ExitCode" |
        Out-File $LogFile -Append

}


"Finished: $(Get-Date)" |
    Out-File $LogFile -Append

"===============================================" |
    Out-File $LogFile -Append


exit $ExitCode
'@


Set-Content `
    -Path $RunnerFile `
    -Value $RunnerContent `
    -Encoding UTF8


Write-Host ""
Write-Host "Runner created:"
Write-Host $RunnerFile


# ============================================================
# REMOVE OLD TASK IF IT EXISTS
# ============================================================

$ExistingTask = Get-ScheduledTask `
    -TaskName $TaskName `
    -ErrorAction SilentlyContinue


if ($ExistingTask) {

    Write-Host ""
    Write-Host "Removing existing AveoEarth task..."

    Unregister-ScheduledTask `
        -TaskName $TaskName `
        -Confirm:$false
}


# ============================================================
# CREATE TASK ACTION
# ============================================================

$ActionArguments = `
    "-NoProfile -ExecutionPolicy Bypass -File `"$RunnerFile`""


$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument $ActionArguments


# ============================================================
# WEEKLY TRIGGER
# ============================================================

$Trigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Monday `
    -At $ScheduleTime


# ============================================================
# TASK SETTINGS
# ============================================================

$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries


# ============================================================
# REGISTER TASK
# ============================================================

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Runs AveoEarth funding and sustainability intelligence workflow every Monday." `
    -Force


# ============================================================
# FINISH
# ============================================================

Write-Host ""
Write-Host "==============================================="
Write-Host "AUTOMATION CREATED SUCCESSFULLY"
Write-Host "==============================================="

Write-Host ""
Write-Host "Task:"
Write-Host $TaskName

Write-Host ""
Write-Host "Schedule:"
Write-Host "Every Monday at 08:00"

Write-Host ""
Write-Host "Runner:"
Write-Host $RunnerFile

Write-Host ""
Write-Host "Scheduled run logs will be stored in:"
Write-Host "$ProjectDir\scheduled_logs"

Write-Host ""
Write-Host "IMPORTANT:"
Write-Host "Your laptop must be turned on for the agent to run."
Write-Host ""

Write-Host "To test the task manually later, run:"
Write-Host "Start-ScheduledTask -TaskName `"$TaskName`""

Write-Host ""