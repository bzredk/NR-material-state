param([string]$RunName='replication', [ValidateSet('all','prepare','train','evaluate')][string]$Stage='all', [switch]$Resume, [string]$Python='python')
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
$taskPython=(Get-Command $Python -ErrorAction Stop).Source
& $taskPython -m pytest -q test_round2.py test_intake.py
if ($LASTEXITCODE -ne 0) { throw 'Correctness checks failed' }
$taskArgs=@('-u','experiment.py',$Stage,'--output',(Join-Path $PSScriptRoot "runs\$RunName"))
if ($Resume) { $taskArgs+='--resume' }
& $taskPython @taskArgs
if ($LASTEXITCODE -ne 0) { throw 'Experiment incomplete; inspect logs. Test evaluation requires validation convergence.' }
if ($Stage -in @('all','evaluate')) {
    & $taskPython numerical_audit.py --output (Join-Path $PSScriptRoot "runs\$RunName")
    if ($LASTEXITCODE -ne 0) { throw 'Numerical audit failed' }
}
