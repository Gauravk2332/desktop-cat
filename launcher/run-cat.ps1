<#
.SYNOPSIS
    Desktop Cat Watchdog Launcher
.DESCRIPTION
    Launches the cat overlay and auto-restarts on crash.
    Runs in a loop until the script itself is killed.
    Logs all crashes and restarts to a log file.

    Designed to be launched via Task Scheduler at user logon.
#>

param(
    [string]$CatDir = "$env:USERPROFILE\OneDrive\Desktop\desktop-cat",
    [string]$LogDir = "$env:LOCALAPPDATA\DesktopCat",
    [int]$MaxRestartDelaySec = 30,
    [int]$MinRunSec = 15,
    [int]$PollIntervalSec = 10
)

# Resolve paths
$LogDir = [System.Environment]::ExpandEnvironmentVariables($LogDir)
$CatDir = [System.Environment]::ExpandEnvironmentVariables($CatDir)
$LogPath = Join-Path $LogDir "desktop-cat.log"
$PidFile = Join-Path $LogDir "desktop-cat.pid"

# Ensure log directory exists
New-Item -ItemType Directory -Path $LogDir -Force -ErrorAction SilentlyContinue | Out-Null

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp $Message" | Out-File -FilePath $LogPath -Append -Encoding ascii
}

function Cleanup-Process {
    param($Proc)
    if ($Proc -and !$Proc.HasExited) {
        try { $Proc.Kill() } catch {}
        try { $Proc.Dispose() } catch {}
    }
}

function Start-CatProcess {
    $env:QT_QPA_PLATFORM = "windows"
    $env:PYTHONUNBUFFERED = "1"

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "python"
    $psi.Arguments = "main.py"
    $psi.WorkingDirectory = $CatDir
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true

    # Environment
    $psi.Environment["QT_QPA_PLATFORM"] = "windows"
    $psi.Environment["PYTHONUNBUFFERED"] = "1"

    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    $proc.Start() | Out-Null

    # Read stdout/stderr asynchronously
    $outTask = $proc.StandardOutput.ReadToEndAsync()
    $errTask = $proc.StandardError.ReadToEndAsync()

    return @{
        Process = $proc
        OutTask = $outTask
        ErrTask = $errTask
        Started = (Get-Date)
    }
}

# Main Watchdog Loop
Write-Log "=== Desktop Cat Watchdog STARTED ==="
Write-Log "CatDir: $CatDir"
Write-Log "LogDir: $LogDir"

# Save PID for external monitoring
$currentPid = [System.Diagnostics.Process]::GetCurrentProcess().Id
$currentPid | Out-File $PidFile -Force

# ── Guard: kill any other watchdog that was running ──
# Prevents duplicate instances when scheduled task is re-run
$existingPid = $null
if (Test-Path $PidFile) {
    try {
        $existingPid = Get-Content $PidFile -Raw -ErrorAction Stop | ForEach-Object { $_.Trim() }
    } catch {}
}
if ($existingPid -and $existingPid -ne $currentPid) {
    Write-Log "Found stale watchdog PID=$existingPid — killing..."
    try {
        $oldProc = Get-Process -Id $existingPid -ErrorAction Stop
        # Kill children first (python processes)
        Get-CimInstance Win32_Process | Where-Object {
            $_.ParentProcessId -eq $existingPid
        } | ForEach-Object {
            try { Stop-Process -Id $_.ProcessId -Force } catch {}
        }
        $oldProc.Kill()
        Write-Log "Killed old watchdog (PID=$existingPid)"
    } catch {
        Write-Log "Could not kill old watchdog (PID=$existingPid): $_"
    }
}
# Rewrite PID file now that we own the slot
$currentPid | Out-File $PidFile -Force

$consecutiveCrashes = 0
$restartDelay = 0

while ($true) {
    # Launch cat
    Write-Log "Starting Desktop Cat..."
    $ctx = Start-CatProcess
    $proc = $ctx.Process
    $consecutiveCrashes = 0

    # Monitor loop
    while (!$proc.HasExited) {
        Start-Sleep -Seconds $PollIntervalSec
        if ($proc.HasExited) {
            break
        }
    }

    # Process exited
    $exitCode = $proc.ExitCode
    $runtimeSec = [math]::Round(((Get-Date) - $ctx.Started).TotalSeconds)

    try { $stdout = $ctx.OutTask.Result } catch { $stdout = "" }
    try { $stderr = $ctx.ErrTask.Result } catch { $stderr = "" }

    if ($stdout) { Write-Log "STDOUT: $stdout" }
    if ($stderr) { Write-Log "STDERR: $stderr" }

    Write-Log "Cat exited. Code=$exitCode Runtime=${runtimeSec}s"

    # Check if it ran long enough (not a crash-on-startup)
    if ($runtimeSec -ge $MinRunSec) {
        $consecutiveCrashes = 0
        $restartDelay = 2
        Write-Log "Ran > ${MinRunSec}s -- clean restart."
    } else {
        $consecutiveCrashes++
        $restartDelay = [math]::Min(2 * $consecutiveCrashes, $MaxRestartDelaySec)
        Write-Log "CRASH #$consecutiveCrashes -- waiting ${restartDelay}s before restart"
    }

    # Wait before restart
    Start-Sleep -Seconds $restartDelay

    # Clean up
    Cleanup-Process $proc
}
