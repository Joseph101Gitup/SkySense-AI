# =====================================================================
#  SKYsense AI - PowerShell Automation Workflow Script
#  Automates the complete workflow:
#  VERIFY -> TRAIN -> EVALUATE -> EXPORT -> MIGRATE -> SERVER -> TEST
# =====================================================================

[CmdletBinding()]
param (
    [switch]$SkipTrain,
    [switch]$TrainDryRun,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
Set-Location $RepoRoot

# Detect Python interpreter
$VenvPython = Join-Path $RepoRoot "03_AI_Model\.venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $PythonExe = $VenvPython
} else {
    $PythonExe = "python"
}

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "         SKYSENSE AI - POWERSHELL AUTOMATED WORKFLOW" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "Using Python : $PythonExe"
Write-Host "Repo Root    : $RepoRoot"
Write-Host "====================================================================="

$WorkflowScript = Join-Path $ScriptDir "run_workflow.py"
$ArgsList = @()

if ($SkipTrain) { $ArgsList += "--skip-train" }
if ($TrainDryRun) { $ArgsList += "--train-dry-run" }
if ($SkipTests) { $ArgsList += "--skip-tests" }

& $PythonExe $WorkflowScript @ArgsList
if ($LASTEXITCODE -ne 0) {
    Write-Error "Pipeline execution failed with exit code $LASTEXITCODE."
    exit $LASTEXITCODE
}

Write-Host "`n[OK] PowerShell workflow finished successfully." -ForegroundColor Green
exit 0
