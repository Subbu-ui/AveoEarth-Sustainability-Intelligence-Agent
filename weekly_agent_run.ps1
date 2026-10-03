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
