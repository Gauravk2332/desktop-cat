$ErrorActionPreference = "Stop"
$LogDir = "$env:LOCALAPPDATA\DesktopCat"
$null = New-Item -ItemType Directory -Force -Path $LogDir -ErrorAction SilentlyContinue
$LogFile = Join-Path $LogDir "desktop-cat.log"
$CatDir = "$env:USERPROFILE\OneDrive\Desktop\desktop-cat"

function Write-Log {
    param([string]$Message)
    "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $Message" | Out-File -FilePath $LogFile -Append
}

Write-Log "=== Desktop Cat Watchdog STARTED ==="
$startTime = Get-Date

while ($true) {
    Write-Log "Starting Desktop Cat..."
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "python"
    $psi.Arguments = "main.py"
    $psi.WorkingDirectory = $CatDir
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    $psi.UseShellExecute = $false
    $psi.Environment["QT_QPA_PLATFORM"] = "windows"
    $psi.Environment["PYTHONUNBUFFERED"] = "1"

    $proc = New-Object System.Diagnostics.Process
    $proc.StartInfo = $psi
    $proc.Start() | Out-Null
    $procStart = Get-Date

    $outTask = $proc.StandardOutput.ReadToEndAsync()
    $errTask = $proc.StandardError.ReadToEndAsync()

    while (!$proc.HasExited) {
        Start-Sleep -Seconds 5
    }

    $exitCode = $proc.ExitCode
    $runtimeSec = [math]::Round(((Get-Date) - $procStart).TotalSeconds)

    try { $stderr = $errTask.Result } catch { $stderr = "" }
    try { $stdout = $outTask.Result } catch { $stdout = "" }
    if ($stdout) { Write-Log "STDOUT: $stdout" }
    if ($stderr) { Write-Log "STDERR: $stderr" }

    Write-Log "Cat exited. Code=$exitCode Runtime=${runtimeSec}s"

    $delay = 2
    if ($runtimeSec -lt 15) { $delay = 10 }
    Start-Sleep -Seconds $delay
}
