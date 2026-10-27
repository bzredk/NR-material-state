param(
    [ValidateSet('figures', 'analysis', 'full')]
    [string]$Stage = 'figures',
    [string]$Python = 'python'
)
$ErrorActionPreference = 'Stop'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:NUMBA_NUM_THREADS = '4'
$resolvedPython = Get-Command $Python -ErrorAction SilentlyContinue
if ($resolvedPython) { $Python = $resolvedPython.Source }
if (-not (Test-Path -LiteralPath $Python)) {
    throw "Specify -Python with a compatible Python environment; see results/environment.json."
}
Push-Location -LiteralPath $PSScriptRoot
try {
    if ($Stage -eq 'full') {
        # Existing input snapshots are sufficient; do not reset the preregistered hashes.
        foreach ($Step in @('prepare', 'profile', 'actions', 'diagnostic')) {
            & $Python -u bridge.py $Step
            if ($LASTEXITCODE -ne 0) { throw "bridge.py $Step failed." }
        }
    }
    if ($Stage -ne 'figures') {
        & $Python -u analyze.py
        if ($LASTEXITCODE -ne 0) { throw 'analyze.py failed.' }
    }
    & $Python -u plot_results.py
    if ($LASTEXITCODE -ne 0) { throw 'plot_results.py failed.' }
    & $Python -u finalize.py
    if ($LASTEXITCODE -ne 0) { throw 'finalize.py failed.' }
}
finally {
    Pop-Location
}
