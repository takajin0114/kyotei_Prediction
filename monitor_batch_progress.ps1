# バッチ処理進行状況監視スクリプト
param(
    [int]$ProcessId = 28636,
    [int]$IntervalSeconds = 30
)

Write-Host "バッチ処理監視開始 - プロセスID: $ProcessId" -ForegroundColor Green
Write-Host "監視間隔: $IntervalSeconds秒" -ForegroundColor Yellow
Write-Host "終了するには Ctrl+C を押してください" -ForegroundColor Cyan
Write-Host ""

while ($true) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    # プロセス確認
    $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($process) {
        $cpuTime = $process.CPU
        $memoryMB = [math]::Round($process.WorkingSet / 1MB, 1)
        Write-Host "[$timestamp] プロセス実行中 - CPU: $cpuTime秒, メモリ: ${memoryMB}MB" -ForegroundColor Green
    } else {
        Write-Host "[$timestamp] プロセス終了" -ForegroundColor Red
        break
    }
    
    # ロックファイル確認
    if (Test-Path "batch_fetch_all_venues.lock") {
        $lockContent = Get-Content "batch_fetch_all_venues.lock"
        Write-Host "[$timestamp] ロックファイル存在" -ForegroundColor Yellow
    } else {
        Write-Host "[$timestamp] ロックファイルなし" -ForegroundColor Red
        break
    }
    
    # データファイル数確認
    $oddsFiles = Get-ChildItem "kyotei_predictor/data/raw/odds_data_2024-05-*.json" -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count
    $raceFiles = Get-ChildItem "kyotei_predictor/data/raw/race_data_2024-05-*.json" -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count
    Write-Host "[$timestamp] データファイル数 - オッズ: $oddsFiles件, レース: $raceFiles件" -ForegroundColor Blue
    
    Write-Host ""
    Start-Sleep -Seconds $IntervalSeconds
} 