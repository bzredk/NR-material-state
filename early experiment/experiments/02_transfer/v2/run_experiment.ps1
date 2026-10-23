param(
    [ValidateSet('all','train','evaluate','figures')][string]$Stage = 'all',
    [string]$Python = 'python'
)
$ErrorActionPreference = 'Stop'
function Run-Python {
    param([string[]]$Arguments)
    & $Python @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Python failed: $Arguments" }
}
Push-Location $PSScriptRoot
try {
    if ($Stage -eq 'all') {
        Run-Python -Arguments @('-m','pytest','test_core.py','-q')
        Run-Python -Arguments @('experiment.py','profile')
        Run-Python -Arguments @('experiment.py','prepare')
    }
    if ($Stage -in @('all','train')) { Run-Python -Arguments @('experiment.py','train','--resume') }
    if ($Stage -in @('all','evaluate')) {
        Run-Python -Arguments @('experiment.py','evaluate')
        Run-Python -Arguments @('numerical_audit.py')
    }
    if ($Stage -in @('all','figures','evaluate')) {
        Run-Python -Arguments @('plot_results.py')
        Run-Python -Arguments @('cases.py')
        Run-Python -Arguments @('summarize_results.py')
        Run-Python -Arguments @('decision_sensitivity.py')
        Run-Python -Arguments @('audit_results.py')
        Run-Python -Arguments @('qa_exports.py')
    }
} finally { Pop-Location }
