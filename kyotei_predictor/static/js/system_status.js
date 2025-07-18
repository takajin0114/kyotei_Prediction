/**
 * システムステータスページ用JavaScript
 * システム状況・バッチ進捗・エラーログ・モデル情報の表示と更新
 */

class SystemStatusManager {
    constructor() {
        this.refreshInterval = null;
        this.autoRefreshEnabled = true;
        this.refreshIntervalMs = 30000; // 30秒間隔で自動更新
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadInitialData();
        this.startAutoRefresh();
    }

    bindEvents() {
        // 手動更新ボタン
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshData();
            });
        }

        // ページ表示時の初期化
        document.addEventListener('DOMContentLoaded', () => {
            this.updateLastUpdateTime();
        });
    }

    async loadInitialData() {
        try {
            this.showLoading(true);
            await this.refreshData();
        } catch (error) {
            console.error('初期データ読み込みエラー:', error);
            this.showError('初期データの読み込みに失敗しました');
        } finally {
            this.showLoading(false);
        }
    }

    async refreshData() {
        try {
            this.showLoading(true);
            
            // 各データを並列で取得
            const [
                systemStatus,
                batchProgress,
                errorLogs,
                batchHistory,
                modelInfo,
                dataQuality
            ] = await Promise.all([
                this.fetchSystemStatus(),
                this.fetchBatchProgress(),
                this.fetchErrorLogs(),
                this.fetchBatchHistory(),
                this.fetchModelInfo(),
                this.fetchDataQuality()
            ]);

            // データを表示
            this.updateSystemStatus(systemStatus);
            this.updateBatchProgress(batchProgress);
            this.updateErrorLogs(errorLogs);
            this.updateBatchHistory(batchHistory);
            this.updateModelInfo(modelInfo);
            this.updateDataQuality(dataQuality);

            this.updateLastUpdateTime();
            
        } catch (error) {
            console.error('データ更新エラー:', error);
            this.showError('データの更新に失敗しました');
        } finally {
            this.showLoading(false);
        }
    }

    // システムステータス取得
    async fetchSystemStatus() {
        try {
            // 実際のAPIエンドポイントに置き換える
            const response = await fetch('/api/system/status');
            if (!response.ok) throw new Error('システムステータス取得失敗');
            return await response.json();
        } catch (error) {
            // モックデータを返す
            return {
                status: 'online',
                uptime: '2日 15時間 30分',
                lastCheck: new Date().toISOString(),
                services: {
                    database: 'online',
                    prediction: 'online',
                    batch: 'running'
                }
            };
        }
    }

    // バッチ進捗取得
    async fetchBatchProgress() {
        try {
            const response = await fetch('/api/batch/progress');
            if (!response.ok) throw new Error('バッチ進捗取得失敗');
            return await response.json();
        } catch (error) {
            // モックデータを返す
            return {
                overall: {
                    completed: 804,
                    total: 4152,
                    percentage: 19.4
                },
                venues: [
                    { name: 'TAMAGAWA', completed: 804, total: 4152, percentage: 19.4 },
                    { name: 'EDOGAWA', completed: 720, total: 4152, percentage: 17.3 },
                    { name: 'HEIWAJIMA', completed: 650, total: 4152, percentage: 15.7 }
                ],
                dates: [
                    { date: '2024-02-19', completed: 12, total: 12, percentage: 100 },
                    { date: '2024-02-24', completed: 8, total: 12, percentage: 66.7 },
                    { date: '2024-02-25', completed: 0, total: 12, percentage: 0 }
                ]
            };
        }
    }

    // エラーログ取得
    async fetchErrorLogs() {
        try {
            const response = await fetch('/api/logs/errors?limit=10');
            if (!response.ok) throw new Error('エラーログ取得失敗');
            return await response.json();
        } catch (error) {
            // モックデータを返す
            return [
                {
                    timestamp: '2024-02-19 22:14:02',
                    level: 'ERROR',
                    message: 'データ取得タイムアウト: TAMAGAWA 2024-02-19 R5',
                    type: 'timeout'
                },
                {
                    timestamp: '2024-02-19 22:13:45',
                    level: 'WARNING',
                    message: 'オッズデータ不整合: EDOGAWA 2024-02-19 R3',
                    type: 'data_mismatch'
                }
            ];
        }
    }

    // バッチ履歴取得
    async fetchBatchHistory() {
        try {
            const response = await fetch('/api/batch/history?limit=10');
            if (!response.ok) throw new Error('バッチ履歴取得失敗');
            return await response.json();
        } catch (error) {
            // モックデータを返す
            return [
                {
                    timestamp: '2024-02-19 22:14:02',
                    venue: 'TAMAGAWA',
                    date: '2024-02-19',
                    status: 'success',
                    races: 12,
                    odds: 12,
                    duration: '45秒'
                },
                {
                    timestamp: '2024-02-19 22:13:15',
                    venue: 'EDOGAWA',
                    date: '2024-02-19',
                    status: 'success',
                    races: 12,
                    odds: 12,
                    duration: '38秒'
                }
            ];
        }
    }

    // モデル情報取得
    async fetchModelInfo() {
        try {
            const response = await fetch('/api/model/info');
            if (!response.ok) throw new Error('モデル情報取得失敗');
            return await response.json();
        } catch (error) {
            // モックデータを返す
            return {
                currentModel: 'graduated_reward_final_20250709_141914',
                accuracy: 0.724,
                lastTraining: '2024-07-09 14:19:14',
                trainingDuration: '2時間 15分',
                parameters: {
                    learningRate: 0.0003,
                    batchSize: 64,
                    epochs: 100
                }
            };
        }
    }

    // データ品質取得
    async fetchDataQuality() {
        try {
            const response = await fetch('/api/data/quality');
            if (!response.ok) throw new Error('データ品質取得失敗');
            return await response.json();
        } catch (error) {
            // モックデータを返す
            return {
                totalRaces: 4152,
                completedRaces: 804,
                missingData: 23,
                dataIntegrity: 0.997,
                lastValidation: '2024-02-19 22:14:02'
            };
        }
    }

    // システムステータス更新
    updateSystemStatus(data) {
        const statusElement = document.getElementById('systemStatus');
        const iconElement = document.getElementById('systemStatusIcon');
        
        if (statusElement && iconElement) {
            statusElement.textContent = data.status === 'online' ? '稼働中' : '停止中';
            
            if (data.status === 'online') {
                iconElement.className = 'fas fa-circle text-success fa-2x';
            } else {
                iconElement.className = 'fas fa-circle text-danger fa-2x';
            }
        }
    }

    // バッチ進捗更新
    updateBatchProgress(data) {
        // 全体進捗
        const progressElement = document.getElementById('batchProgress');
        const detailElement = document.getElementById('batchProgressDetail');
        
        if (progressElement && detailElement) {
            progressElement.textContent = `${data.overall.percentage.toFixed(1)}%`;
            detailElement.textContent = `${data.overall.completed}/${data.overall.total}`;
        }

        // プログレスチャート
        this.updateProgressChart(data);
        
        // 会場別進捗
        this.updateVenueProgress(data.venues);
        
        // 日別進捗
        this.updateDateProgress(data.dates);
    }

    // プログレスチャート更新
    updateProgressChart(data) {
        const chartElement = document.getElementById('progressChart');
        if (!chartElement) return;

        const progress = data.overall.percentage;
        const colorClass = progress >= 80 ? 'bg-success' : 
                          progress >= 50 ? 'bg-warning' : 'bg-danger';

        chartElement.innerHTML = `
            <div class="progress-label">全体進捗</div>
            <div class="progress mb-2">
                <div class="progress-bar ${colorClass}" 
                     role="progressbar" 
                     style="width: ${progress}%" 
                     aria-valuenow="${progress}" 
                     aria-valuemin="0" 
                     aria-valuemax="100">
                    ${progress.toFixed(1)}%
                </div>
            </div>
            <div class="progress-detail">
                完了: ${data.overall.completed} / 総数: ${data.overall.total}
            </div>
        `;
    }

    // 会場別進捗更新
    updateVenueProgress(venues) {
        const element = document.getElementById('venueProgress');
        if (!element) return;

        element.innerHTML = venues.map(venue => `
            <div class="d-flex justify-content-between align-items-center mb-1">
                <span class="small">${venue.name}</span>
                <span class="small text-muted">${venue.percentage.toFixed(1)}%</span>
            </div>
            <div class="progress mb-2" style="height: 0.5rem;">
                <div class="progress-bar ${venue.percentage >= 80 ? 'bg-success' : venue.percentage >= 50 ? 'bg-warning' : 'bg-danger'}" 
                     style="width: ${venue.percentage}%"></div>
            </div>
        `).join('');
    }

    // 日別進捗更新
    updateDateProgress(dates) {
        const element = document.getElementById('dateProgress');
        if (!element) return;

        element.innerHTML = dates.map(date => `
            <div class="d-flex justify-content-between align-items-center mb-1">
                <span class="small">${date.date}</span>
                <span class="small text-muted">${date.percentage.toFixed(1)}%</span>
            </div>
            <div class="progress mb-2" style="height: 0.5rem;">
                <div class="progress-bar ${date.percentage >= 80 ? 'bg-success' : date.percentage >= 50 ? 'bg-warning' : 'bg-danger'}" 
                     style="width: ${date.percentage}%"></div>
            </div>
        `).join('');
    }

    // エラーログ更新
    updateErrorLogs(logs) {
        const element = document.getElementById('errorLogs');
        if (!element) return;

        if (logs.length === 0) {
            element.innerHTML = '<p class="text-muted">エラーはありません</p>';
            return;
        }

        element.innerHTML = logs.map(log => `
            <div class="error-log-item">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <div class="error-log-message">${log.message}</div>
                        <div class="error-log-time">${log.timestamp}</div>
                    </div>
                    <span class="error-log-type">${log.level}</span>
                </div>
            </div>
        `).join('');
    }

    // バッチ履歴更新
    updateBatchHistory(history) {
        const element = document.getElementById('batchHistory');
        if (!element) return;

        if (history.length === 0) {
            element.innerHTML = '<p class="text-muted">履歴はありません</p>';
            return;
        }

        element.innerHTML = history.map(item => `
            <div class="batch-history-item">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <div class="batch-history-venue">${item.venue} ${item.date}</div>
                        <div class="batch-history-time">${item.timestamp} (${item.duration})</div>
                        <div class="small text-muted">レース: ${item.races}, オッズ: ${item.odds}</div>
                    </div>
                    <span class="batch-history-status ${item.status}">${item.status}</span>
                </div>
            </div>
        `).join('');
    }

    // モデル情報更新
    updateModelInfo(info) {
        const element = document.getElementById('modelInfo');
        if (!element) return;

        element.innerHTML = `
            <div class="model-info-item">
                <span class="model-info-label">現在のモデル</span>
                <span class="model-info-value">${info.currentModel}</span>
            </div>
            <div class="model-info-item">
                <span class="model-info-label">精度</span>
                <span class="model-info-value">${(info.accuracy * 100).toFixed(1)}%</span>
            </div>
            <div class="model-info-item">
                <span class="model-info-label">最終学習</span>
                <span class="model-info-value">${info.lastTraining}</span>
            </div>
            <div class="model-info-item">
                <span class="model-info-label">学習時間</span>
                <span class="model-info-value">${info.trainingDuration}</span>
            </div>
        `;
    }

    // データ品質更新
    updateDataQuality(quality) {
        const element = document.getElementById('dataQuality');
        if (!element) return;

        element.innerHTML = `
            <div class="col-md-3">
                <div class="data-quality-item">
                    <div class="data-quality-number">${quality.totalRaces.toLocaleString()}</div>
                    <div class="data-quality-label">総レース数</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="data-quality-item">
                    <div class="data-quality-number">${quality.completedRaces.toLocaleString()}</div>
                    <div class="data-quality-label">完了レース数</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="data-quality-item">
                    <div class="data-quality-number">${quality.missingData}</div>
                    <div class="data-quality-label">欠損データ</div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="data-quality-item">
                    <div class="data-quality-number">${(quality.dataIntegrity * 100).toFixed(1)}%</div>
                    <div class="data-quality-label">データ整合性</div>
                </div>
            </div>
        `;
    }

    // 最終更新時刻更新
    updateLastUpdateTime() {
        const element = document.getElementById('lastUpdate');
        if (element) {
            const now = new Date();
            element.textContent = `最終更新: ${now.toLocaleString('ja-JP')}`;
        }
    }

    // ローディング表示制御
    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            if (show) {
                overlay.classList.remove('d-none');
            } else {
                overlay.classList.add('d-none');
            }
        }
    }

    // エラー表示
    showError(message) {
        // Bootstrap のトーストまたはアラートで表示
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show position-fixed';
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alertDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // 5秒後に自動削除
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 5000);
    }

    // 自動更新開始
    startAutoRefresh() {
        if (this.autoRefreshEnabled) {
            this.refreshInterval = setInterval(() => {
                this.refreshData();
            }, this.refreshIntervalMs);
        }
    }

    // 自動更新停止
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    // ページ離脱時のクリーンアップ
    cleanup() {
        this.stopAutoRefresh();
    }
}

// ページ読み込み完了時に初期化
document.addEventListener('DOMContentLoaded', () => {
    window.systemStatusManager = new SystemStatusManager();
});

// ページ離脱時のクリーンアップ
window.addEventListener('beforeunload', () => {
    if (window.systemStatusManager) {
        window.systemStatusManager.cleanup();
    }
}); 