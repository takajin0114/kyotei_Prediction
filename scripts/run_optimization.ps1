# ============================================================================
# Kyotei Prediction Optimization (PowerShell)
# ============================================================================
# optimization_config.ini を読み、最適化実行後に verify_predictions を
# --evaluation-mode で実行し、比較条件（evaluation_mode）を統一する。
# ============================================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

$ConfigPath = Join-Path $ProjectRoot "optimization_config.ini"

# デフォルト値
$MODE = "fast"
$TRIALS = "20"
$YEAR_MONTH = ""
$EVALUATION_MODE = "first_only"
$VENV_PATH = "venv"
$LOG_DIR = "logs"
$DATA_DIR = "kyotei_predictor/data/test_raw"
$PREDICTION_DEFAULT = "outputs/predictions_latest.json"

if (Test-Path $ConfigPath) {
    Get-Content $ConfigPath | ForEach-Object {
        if ($_ -match "^\s*MODE\s*=\s*(.+)$") { $MODE = $Matches[1].Trim() }
        if ($_ -match "^\s*TRIALS\s*=\s*(.+)$") { $TRIALS = $Matches[1].Trim() }
        if ($_ -match "^\s*YEAR_MONTH\s*=\s*(.+)$") { $YEAR_MONTH = $Matches[1].Trim() }
        if ($_ -match "^\s*EVALUATION_MODE\s*=\s*(.+)$") { $EVALUATION_MODE = $Matches[1].Trim() }
        if ($_ -match "^\s*VENV_PATH\s*=\s*(.+)$") { $VENV_PATH = $Matches[1].Trim() }
        if ($_ -match "^\s*LOG_DIR\s*=\s*(.+)$") { $LOG_DIR = $Matches[1].Trim() }
    }
} else {
    Write-Warning "Config not found: $ConfigPath (using defaults)"
}

# 許可値に揃える（CLI 優先は verify_predictions 側で保証）
if ($EVALUATION_MODE -notin @("first_only", "selected_bets")) {
    $EVALUATION_MODE = "first_only"
}

Write-Host "========================================"
Write-Host "Kyotei Prediction Optimization"
Write-Host "========================================"
Write-Host "Mode: $MODE  Trials: $TRIALS  YearMonth: $YEAR_MONTH"
Write-Host "EvaluationMode (for verification): $EVALUATION_MODE"
Write-Host ""

# 仮想環境の activate（Windows: venv\Scripts\Activate.ps1）
$ActivatePath = Join-Path $ProjectRoot $VENV_PATH
$ActivateScript = Join-Path $ActivatePath "Scripts\Activate.ps1"
if (-not (Test-Path $ActivateScript)) {
    $ActivateScript = Join-Path $ActivatePath "bin\Activate.ps1"
}
if (Test-Path $ActivateScript) {
    & $ActivateScript
} else {
    Write-Warning "venv not found at $ActivatePath, using system python"
}

# 最適化実行（OS非依存: Python CLI に config を渡すだけ）
$LogDirPath = Join-Path $ProjectRoot $LOG_DIR
if (-not (Test-Path $LogDirPath)) { New-Item -ItemType Directory -Path $LogDirPath | Out-Null }
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogFile = Join-Path $LogDirPath "optimization_$Timestamp.log"

Write-Host "Starting optimization... Log: $LogFile"
& python -m kyotei_predictor.cli.optimize --config $ConfigPath 2>&1 | Tee-Object -FilePath $LogFile
$OptExit = $LASTEXITCODE

# 検証: evaluation_mode を optimization_config.ini の値で統一して実行
$PredPath = Join-Path $ProjectRoot $PREDICTION_DEFAULT
$DataDirPath = Join-Path $ProjectRoot $DATA_DIR
if ((Test-Path $PredPath) -and (Test-Path $DataDirPath)) {
    Write-Host ""
    Write-Host "Running verify_predictions with --evaluation-mode $EVALUATION_MODE"
    & python -m kyotei_predictor.tools.verify_predictions `
        --prediction $PredPath `
        --data-dir $DataDirPath `
        --evaluation-mode $EVALUATION_MODE `
        --save
    $VerifyExit = $LASTEXITCODE
} else {
    Write-Host ""
    Write-Host "Skipping verification (prediction or data-dir not found). To run manually:"
    Write-Host "  python -m kyotei_predictor.tools.verify_predictions --evaluation-mode $EVALUATION_MODE --prediction $PREDICTION_DEFAULT --data-dir $DATA_DIR"
    $VerifyExit = 0
}

Write-Host ""
Write-Host "Optimization exit code: $OptExit  Verification exit code: $VerifyExit"
if ($OptExit -ne 0) { exit $OptExit }
exit $VerifyExit
