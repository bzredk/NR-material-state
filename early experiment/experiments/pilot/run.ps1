param([string]$RunName = 'replication', [ValidateSet('all','prepare','train','evaluate')][string]$Stage = 'all')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
& '.\.venv\Scripts\python.exe' -m pytest -q test_pilot.py
if ($LASTEXITCODE -ne 0) { throw 'Physical correctness tests failed' }
& '.\.venv\Scripts\python.exe' -u experiment.py $Stage --steps 330 --output (Join-Path $PSScriptRoot "runs\$RunName")
if ($LASTEXITCODE -ne 0) { throw 'Experiment failed' }
if ($Stage -in @('all','evaluate')) {
    & '.\.venv\Scripts\python.exe' diagnostics.py --output (Join-Path $PSScriptRoot "runs\$RunName")
    if ($LASTEXITCODE -ne 0) { throw 'Mechanism diagnostics failed' }
}
