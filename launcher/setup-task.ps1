<#
.SYNOPSIS
    Install Desktop Cat as a Windows scheduled task.
    Runs the watchdog launcher at user logon in the interactive session.
.DESCRIPTION
    Creates or updates the "DesktopCat" scheduled task.
    The task:
      - Runs at user logon (interactive session)
      - Runs with highest privileges
      - Runs even when user is logged on (interactive)
      - Auto-restarts if the process somehow dies (via watchdog)
#>

param(
    [string]$TaskName = "DesktopCat",
    [string]$CatDir = "$env:USERPROFILE\OneDrive\Desktop\desktop-cat"
)

$CatDir = [System.Environment]::ExpandEnvironmentVariables($CatDir)
$ScriptPath = Join-Path $CatDir "launcher\run-cat.ps1"
$LogDir = "$env:LOCALAPPDATA\DesktopCat"

Write-Host "=== Desktop Cat Installer ==="
Write-Host "Task name   : $TaskName"
Write-Host "Script      : $ScriptPath"
Write-Host "Working dir : $CatDir"
Write-Host "Log dir     : $LogDir"

# ── Validate ──
if (!(Test-Path $ScriptPath)) {
    Write-Error "Launcher script not found: $ScriptPath"
    exit 1
}
if (!(Test-Path (Join-Path $CatDir "main.py"))) {
    Write-Error "main.py not found in $CatDir"
    exit 1
}

# ── Delete existing task if present ──
$existing = schtasks /Query /TN $TaskName 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Removing existing task..."
    schtasks /Delete /TN $TaskName /F | Out-Null
}

# ── Create task ──
$trigger = @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Desktop Cat — Wandering overlay companion</Description>
  </RegistrationInfo>
  <Triggers>
    <LogonTrigger>
      <Enabled>true</Enabled>
      <UserId>$(whoami)</UserId>
      <Delay>PT30S</Delay>
    </LogonTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>$(whoami)</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <DisallowStartOnRemoteAppSession>false</DisallowStartOnRemoteAppSession>
    <UseUnifiedSchedulingEngine>true</UseUnifiedSchedulingEngine>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
    <RestartOnFailure>
      <Interval>PT1M</Interval>
      <Count>10</Count>
    </RestartOnFailure>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>powershell</Command>
      <Arguments>-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "$( $ScriptPath )"</Arguments>
      <WorkingDirectory>$( $CatDir )</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"@

$xmlPath = Join-Path $env:TEMP "desktop-cat-task.xml"
$trigger | Out-File -FilePath $xmlPath -Encoding utf8

Write-Host "Creating task..."
schtasks /Create /TN $TaskName /XML $xmlPath /F
$result = $LASTEXITCODE

Remove-Item $xmlPath -Force -ErrorAction SilentlyContinue

if ($result -ne 0) {
    Write-Error "Task creation failed with code $result"
    exit 1
}

Write-Host ""
Write-Host "✅ Task created successfully!"
Write-Host ""
Write-Host "Run the cat now:"
Write-Host "  schtasks /Run /TN ""$TaskName"" /I"
Write-Host ""
Write-Host "Check status:"
Write-Host "  Get-Process -Name python*,powershell* | Where-Object { `$_.SessionId -eq 1 }"
Write-Host ""
Write-Host "View logs:"
Write-Host "  Get-Content ""$LogDir\desktop-cat.log"" -Tail 20"
