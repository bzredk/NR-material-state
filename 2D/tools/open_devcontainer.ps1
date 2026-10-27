# Launch an independent VS Code process; do not tie the project to a Codex terminal.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$codeExe = Join-Path $env:LOCALAPPDATA 'Programs\Microsoft VS Code\Code.exe'
$userData = Join-Path $projectRoot '.runtime\vscode-container'
if (-not (Test-Path -LiteralPath $codeExe)) { throw 'VS Code executable not found.' }
New-Item -ItemType Directory -Force -Path $userData | Out-Null
$command = '"{0}" --user-data-dir "{1}" --new-window "{2}"' -f $codeExe, $userData, $projectRoot
# CREATE_BREAKAWAY_FROM_JOB. The WMI service, not this shell, creates the process.
$startup = New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ CreateFlags=[uint32]0x01000000 }
$result = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
    CommandLine=$command; ProcessStartupInformation=$startup
}
if ($result.ReturnValue -ne 0) { throw "Independent VS Code launch failed: $($result.ReturnValue)" }
Write-Output "VS Code process: $($result.ProcessId). Use Dev Containers: Reopen in Container."
