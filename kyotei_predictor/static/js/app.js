/**
 * 競艇予測ツール - Phase 2 フロントエンド
 * 5つのアルゴリズム + 3連単確率計算対応
 */

// グローバル変数
let currentRaceData = null;
let currentPrediction = null;
let charts = {};

// ページ読み込み時の初期化
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚤 競艇予測ツール Phase 2 初期化開始');
    
    // レースデータの読み込み
    loadRaceData();
    
    // 予想履歴の読み込み
    loadPredictionHistory();
    
    // アルゴリズム選択の初期化
    initializeAlgorithmSelection();
    
    // タブ切り替えイベント
    initializeTabEvents();
    
    console.log('✅ 初期化完了');
});

/**
 * レースデータの読み込み
 */
async function loadRaceData() {
    try {
        console.log('📊 レースデータ読み込み開始');
        
        const response = await fetch('/api/race_data');
        const data = await response.json();
        
        if (data.success) {
            currentRaceData = data.data;
            displayRaceInfo(data.data);
            console.log('✅ レースデータ読み込み完了');
        } else {
            throw new Error(data.error || 'レースデータの取得に失敗');
        }
    } catch (error) {
        console.error('❌ レースデータ読み込みエラー:', error);
        displayError('raceInfo', 'レースデータの読み込みに失敗しました');
    }
}

/**
 * レース情報の表示
 */
function displayRaceInfo(raceData) {
    const raceInfoElement = document.getElementById('raceInfo');
    
    const raceInfo = raceData.race_info || {};
    const weatherInfo = raceData.weather_condition || {};
    const entries = raceData.race_entries || [];
    
    const html = `
        <div class="race-basic-info">
            <h6><i class="fas fa-calendar"></i> ${raceInfo.date || '2024-06-15'}</h6>
            <h6><i class="fas fa-map-marker-alt"></i> ${raceInfo.stadium || 'KIRYU'}</h6>
            <h6><i class="fas fa-flag"></i> ${raceInfo.title || '第1レース'}</h6>
            <hr>
            <p><strong>出走艇数:</strong> ${entries.length}艇</p>
        </div>
        
        ${weatherInfo.weather ? `
        <div class="weather-info">
            <h6><i class="fas fa-cloud-sun"></i> 天候情報</h6>
            <div class="row">
                <div class="col-6">
                    <small><strong>天候:</strong> ${getWeatherIcon(weatherInfo.weather)} ${weatherInfo.weather}</small>
                </div>
                <div class="col-6">
                    <small><strong>風速:</strong> ${weatherInfo.wind_velocity || 'N/A'}m/s</small>
                </div>
                <div class="col-6">
                    <small><strong>気温:</strong> ${weatherInfo.air_temperature || 'N/A'}℃</small>
                </div>
                <div class="col-6">
                    <small><strong>水温:</strong> ${weatherInfo.water_temperature || 'N/A'}℃</small>
                </div>
            </div>
        </div>
        ` : ''}
        
        <div class="entries-summary mt-3">
            <h6><i class="fas fa-users"></i> 出走選手</h6>
            ${entries.slice(0, 6).map(entry => `
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <span class="badge bg-secondary">${entry.pit_number}</span>
                    <small class="flex-grow-1 ms-2">${entry.racer.name}</small>
                    <span class="badge rating-${entry.racer.current_rating.toLowerCase()}">${entry.racer.current_rating}</span>
                </div>
            `).join('')}
        </div>
    `;
    
    raceInfoElement.innerHTML = html;
}

/**
 * 天候アイコンの取得
 */
function getWeatherIcon(weather) {
    const icons = {
        'FINE': '☀️',
        'CLOUDY': '☁️',
        'RAINY': '🌧️',
        'STORMY': '⛈️'
    };
    return icons[weather] || '🌤️';
}

/**
 * アルゴリズム選択の初期化
 */
function initializeAlgorithmSelection() {
    const algorithmOptions = document.querySelectorAll('.algorithm-option');
    
    algorithmOptions.forEach(option => {
        option.addEventListener('click', function() {
            // 全ての選択を解除
            algorithmOptions.forEach(opt => opt.classList.remove('selected'));
            
            // クリックされたオプションを選択
            this.classList.add('selected');
            
            // ラジオボタンをチェック
            const radio = this.querySelector('input[type="radio"]');
            radio.checked = true;
        });
    });
    
    // 初期選択
    document.querySelector('.algorithm-option[data-algorithm="basic"]').classList.add('selected');
}

/**
 * タブイベントの初期化
 */
function initializeTabEvents() {
    const tabs = document.querySelectorAll('[data-bs-toggle="tab"]');
    
    tabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(event) {
            const targetId = event.target.getAttribute('data-bs-target').substring(1);
            
            switch(targetId) {
                case 'history':
                    loadPredictionHistory();
                    break;
                case 'analysis':
                    initializeCharts();
                    break;
            }
        });
    });
}

/**
 * 予測実行
 */
async function executePrediction() {
    const selectedAlgorithm = document.querySelector('input[name="algorithm"]:checked').value;
    
    console.log(`🎯 予測実行開始: ${selectedAlgorithm}`);
    
    // ローディング表示
    showLoading();
    
    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                algorithm: selectedAlgorithm
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentPrediction = result.data;
            displayPredictionResults(result.data);
            console.log('✅ 予測完了');
        } else {
            throw new Error(result.error || '予測の実行に失敗');
        }
    } catch (error) {
        console.error('❌ 予測エラー:', error);
        displayError('predictionResults', '予測の実行に失敗しました');
    } finally {
        hideLoading();
    }
}

/**
 * 予測結果の表示
 */
function displayPredictionResults(prediction) {
    const resultsElement = document.getElementById('predictionResults');
    
    const summary = prediction.summary;
    const predictions = prediction.predictions;
    const algorithm = prediction.algorithm;
    
    const html = `
        <div class="prediction-result">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h4><i class="fas fa-trophy"></i> 予測結果</h4>
                <span class="badge bg-primary fs-6">${getAlgorithmName(algorithm)}</span>
            </div>
            
            <!-- サマリー情報 -->
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="text-center p-3 bg-light rounded">
                        <h5 class="text-primary">本命</h5>
                        <h3>${summary.favorite.pit_number}号艇</h3>
                        <p class="mb-0">${summary.favorite.racer_name}</p>
                        <small class="text-muted">${summary.favorite.rating}</small>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="text-center p-3 bg-light rounded">
                        <h5 class="text-success">勝率</h5>
                        <h3>${summary.favorite.win_probability}%</h3>
                        <p class="mb-0">予測勝率</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="text-center p-3 bg-light rounded">
                        <h5 class="confidence-${summary.confidence_level}">信頼度</h5>
                        <h3>${getConfidenceIcon(summary.confidence_level)}</h3>
                        <p class="mb-0">${summary.confidence_level.toUpperCase()}</p>
                    </div>
                </div>
            </div>
            
            <!-- 穴馬情報 -->
            ${summary.dark_horse ? `
            <div class="alert alert-warning">
                <h6><i class="fas fa-star"></i> 注目の穴馬</h6>
                <strong>${summary.dark_horse.pit_number}号艇 ${summary.dark_horse.racer_name}</strong> 
                (${summary.dark_horse.rating}) - 予測${summary.dark_horse.predicted_rank}位
            </div>
            ` : ''}
            
            <!-- 詳細予測結果 -->
            <h5><i class="fas fa-list-ol"></i> 詳細予測</h5>
            <div class="prediction-details">
                ${predictions.map((pred, index) => `
                    <div class="racer-row ${index < 3 ? `rank-${index + 1}` : ''} d-flex align-items-center">
                        <div class="rank-badge me-3">
                            <span class="badge ${index < 3 ? 'bg-warning' : 'bg-secondary'} fs-6">
                                ${pred.rank}位
                            </span>
                        </div>
                        <div class="racer-info flex-grow-1">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>${pred.pit_number}号艇 ${pred.racer_name}</strong>
                                    <span class="badge rating-${pred.rating.toLowerCase()} ms-2">${pred.rating}</span>
                                </div>
                                <div class="text-end">
                                    <div class="fw-bold text-primary">${pred.win_probability}%</div>
                                    <small class="text-muted">スコア: ${pred.prediction_score.toFixed(3)}</small>
                                </div>
                            </div>
                            <div class="mt-1">
                                <small class="text-muted">
                                    信頼度: <span class="confidence-${pred.confidence}">${pred.confidence}</span>
                                    ${pred.details.algorithm ? `| アルゴリズム: ${pred.details.algorithm}` : ''}
                                </small>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
            
            <!-- 推奨買い目 -->
            <div class="mt-4 p-3 bg-info bg-opacity-10 rounded">
                <h6><i class="fas fa-lightbulb"></i> 推奨買い目</h6>
                <div class="row">
                    <div class="col-md-4">
                        <strong>3連単:</strong> ${predictions.slice(0, 3).map(p => p.pit_number).join('-')}
                    </div>
                    <div class="col-md-4">
                        <strong>3連複:</strong> ${predictions.slice(0, 3).map(p => p.pit_number).sort().join('-')}
                    </div>
                    <div class="col-md-4">
                        <strong>2連単:</strong> ${predictions.slice(0, 2).map(p => p.pit_number).join('-')}
                    </div>
                </div>
            </div>
            
            <!-- 保存ボタン -->
            <div class="text-center mt-4">
                <button class="btn btn-success" onclick="savePrediction()">
                    <i class="fas fa-save"></i> 予想を保存
                </button>
                <button class="btn btn-outline-primary ms-2" onclick="showTrifectaTab()">
                    <i class="fas fa-calculator"></i> 3連単確率計算
                </button>
            </div>
        </div>
    `;
    
    resultsElement.innerHTML = html;
    resultsElement.style.display = 'block';
}

/**
 * 3連単確率計算
 */
async function calculateTrifecta() {
    const algorithm = document.getElementById('trifectaAlgorithm').value;
    const topN = parseInt(document.getElementById('topN').value);
    
    console.log(`🎯 3連単確率計算開始: ${algorithm}, 上位${topN}位`);
    
    try {
        // まず予測を実行
        const predictionResponse = await fetch('/api/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                algorithm: algorithm
            })
        });
        
        const predictionResult = await predictionResponse.json();
        
        if (!predictionResult.success) {
            throw new Error('予測の実行に失敗');
        }
        
        // 3連単確率を計算（フロントエンドで実装）
        const trifectaData = calculateTrifectaProbabilities(predictionResult.data.predictions, topN);
        
        displayTrifectaResults(trifectaData, algorithm);
        
        console.log('✅ 3連単確率計算完了');
    } catch (error) {
        console.error('❌ 3連単確率計算エラー:', error);
        displayError('trifectaResults', '3連単確率計算に失敗しました');
    }
}

/**
 * 3連単確率の計算（フロントエンド実装）
 */
function calculateTrifectaProbabilities(predictions, topN) {
    const combinations = [];
    
    // 全ての3連単組み合わせを生成
    for (let i = 0; i < predictions.length; i++) {
        for (let j = 0; j < predictions.length; j++) {
            for (let k = 0; k < predictions.length; k++) {
                if (i !== j && j !== k && i !== k) {
                    const first = predictions[i];
                    const second = predictions[j];
                    const third = predictions[k];
                    
                    // 簡易確率計算
                    const firstProb = first.win_probability / 100;
                    const secondProb = second.win_probability / 100 * 0.8;
                    const thirdProb = third.win_probability / 100 * 0.6;
                    
                    const combinationProb = firstProb * secondProb * thirdProb;
                    
                    combinations.push({
                        combination: `${first.pit_number}-${second.pit_number}-${third.pit_number}`,
                        pit_numbers: [first.pit_number, second.pit_number, third.pit_number],
                        probability: combinationProb,
                        percentage: (combinationProb * 100).toFixed(2),
                        expected_odds: combinationProb > 0 ? (1 / combinationProb).toFixed(1) : '999.9'
                    });
                }
            }
        }
    }
    
    // 確率順でソート
    combinations.sort((a, b) => b.probability - a.probability);
    
    return {
        top_combinations: combinations.slice(0, topN),
        total_combinations: combinations.length,
        summary: {
            most_likely: combinations[0],
            total_probability: combinations.slice(0, topN).reduce((sum, combo) => sum + combo.probability, 0),
            average_odds: combinations.slice(0, topN).reduce((sum, combo) => sum + parseFloat(combo.expected_odds), 0) / topN
        }
    };
}

/**
 * 3連単結果の表示
 */
function displayTrifectaResults(trifectaData, algorithm) {
    const resultsElement = document.getElementById('trifectaResults');
    
    const html = `
        <div class="trifecta-results">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h5><i class="fas fa-trophy"></i> 3連単確率計算結果</h5>
                <span class="badge bg-warning fs-6">${getAlgorithmName(algorithm)}</span>
            </div>
            
            <!-- サマリー -->
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="text-center p-3 bg-light rounded">
                        <h6 class="text-primary">最有力</h6>
                        <h4>${trifectaData.summary.most_likely.combination}</h4>
                        <small>${trifectaData.summary.most_likely.percentage}%</small>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="text-center p-3 bg-light rounded">
                        <h6 class="text-success">期待オッズ</h6>
                        <h4>${trifectaData.summary.most_likely.expected_odds}倍</h4>
                        <small>最有力組み合わせ</small>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="text-center p-3 bg-light rounded">
                        <h6 class="text-info">合計確率</h6>
                        <h4>${(trifectaData.summary.total_probability * 100).toFixed(1)}%</h4>
                        <small>上位組み合わせ</small>
                    </div>
                </div>
            </div>
            
            <!-- 上位組み合わせ一覧 -->
            <h6><i class="fas fa-list-ol"></i> 上位組み合わせ</h6>
            <div class="trifecta-list">
                ${trifectaData.top_combinations.map((combo, index) => `
                    <div class="combination-item">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <span class="badge bg-primary me-2">${index + 1}位</span>
                                <strong class="fs-5">${combo.combination}</strong>
                            </div>
                            <div class="text-end">
                                <div class="fw-bold text-success">${combo.percentage}%</div>
                                <small class="text-muted">${combo.expected_odds}倍</small>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
            
            <!-- 投資戦略 -->
            <div class="mt-4 p-3 bg-warning bg-opacity-10 rounded">
                <h6><i class="fas fa-chart-line"></i> 投資戦略</h6>
                <div class="row">
                    <div class="col-md-6">
                        <strong>本命狙い:</strong> ${trifectaData.top_combinations.slice(0, 3).map(c => c.combination).join(', ')}
                    </div>
                    <div class="col-md-6">
                        <strong>平均オッズ:</strong> ${trifectaData.summary.average_odds.toFixed(1)}倍
                    </div>
                </div>
            </div>
        </div>
    `;
    
    resultsElement.innerHTML = html;
    resultsElement.style.display = 'block';
}

/**
 * 予想履歴の読み込み
 */
async function loadPredictionHistory() {
    try {
        const response = await fetch('/api/predictions_history');
        const data = await response.json();
        
        if (data.success) {
            displayPredictionHistory(data.data);
        } else {
            throw new Error(data.error || '履歴の取得に失敗');
        }
    } catch (error) {
        console.error('❌ 履歴読み込みエラー:', error);
        displayError('historyResults', '予想履歴の読み込みに失敗しました');
    }
}

/**
 * 予想履歴の表示
 */
function displayPredictionHistory(history) {
    const historyElement = document.getElementById('historyResults');
    
    if (!history || history.length === 0) {
        historyElement.innerHTML = `
            <div class="text-center p-4">
                <i class="fas fa-inbox fa-3x text-muted mb-3"></i>
                <h5 class="text-muted">予想履歴がありません</h5>
                <p class="text-muted">予測を実行して保存すると、ここに履歴が表示されます。</p>
            </div>
        `;
        return;
    }
    
    const html = `
        <div class="history-list">
            ${history.map((item, index) => `
                <div class="card mb-3">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">
                            <i class="fas fa-calendar"></i> ${new Date(item.timestamp).toLocaleString('ja-JP')}
                        </h6>
                        <span class="badge bg-primary">${getAlgorithmName(item.algorithm)}</span>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <strong>予測結果:</strong> ${item.prediction.slice(0, 3).map(p => `${p.pit_number}号艇`).join(' → ')}
                            </div>
                            <div class="col-md-6">
                                <strong>本命:</strong> ${item.prediction[0].pit_number}号艇 ${item.prediction[0].racer_name} (${item.prediction[0].win_probability}%)
                            </div>
                        </div>
                        ${item.memo ? `<div class="mt-2"><strong>メモ:</strong> ${item.memo}</div>` : ''}
                    </div>
                </div>
            `).join('')}
        </div>
    `;
    
    historyElement.innerHTML = html;
}

/**
 * 予想の保存
 */
async function savePrediction() {
    if (!currentPrediction) {
        alert('保存する予想がありません');
        return;
    }
    
    const memo = prompt('メモを入力してください（任意）:');
    
    try {
        const response = await fetch('/api/save_prediction', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prediction: currentPrediction,
                memo: memo || ''
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('予想を保存しました');
            loadPredictionHistory(); // 履歴を更新
        } else {
            throw new Error(result.error || '保存に失敗');
        }
    } catch (error) {
        console.error('❌ 保存エラー:', error);
        alert('予想の保存に失敗しました');
    }
}

/**
 * チャートの初期化
 */
function initializeCharts() {
    if (!currentRaceData) return;
    
    // 勝率チャート
    initializeWinRateChart();
    
    // アルゴリズム比較チャート
    initializeAlgorithmChart();
}

/**
 * 勝率チャートの初期化
 */
function initializeWinRateChart() {
    const ctx = document.getElementById('winRateChart');
    if (!ctx || charts.winRate) return;
    
    const entries = currentRaceData.race_entries || [];
    
    charts.winRate = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: entries.map(entry => `${entry.pit_number}号艇`),
            datasets: [{
                label: '全国勝率',
                data: entries.map(entry => entry.performance.rate_in_all_stadium),
                backgroundColor: 'rgba(54, 162, 235, 0.8)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }, {
                label: '当地勝率',
                data: entries.map(entry => entry.performance.rate_in_event_going_stadium),
                backgroundColor: 'rgba(255, 99, 132, 0.8)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: '選手勝率比較'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 10
                }
            }
        }
    });
}

/**
 * アルゴリズム比較チャートの初期化
 */
function initializeAlgorithmChart() {
    const ctx = document.getElementById('algorithmChart');
    if (!ctx || charts.algorithm) return;
    
    // サンプルデータ（実際の予測結果があれば使用）
    const algorithmData = {
        'Basic': 85,
        'Rating Weighted': 88,
        'Equipment Focused': 82,
        'Comprehensive': 90,
        'Relative Strength': 87
    };
    
    charts.algorithm = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: Object.keys(algorithmData),
            datasets: [{
                label: '予測精度',
                data: Object.values(algorithmData),
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(75, 192, 192, 1)'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'アルゴリズム性能比較'
                }
            },
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

/**
 * ユーティリティ関数
 */

function showLoading() {
    document.getElementById('loadingSpinner').style.display = 'block';
    document.getElementById('predictionResults').style.display = 'none';
}

function hideLoading() {
    document.getElementById('loadingSpinner').style.display = 'none';
}

function displayError(elementId, message) {
    const element = document.getElementById(elementId);
    element.innerHTML = `
        <div class="alert alert-danger">
            <i class="fas fa-exclamation-triangle"></i> ${message}
        </div>
    `;
    element.style.display = 'block';
}

function getAlgorithmName(algorithm) {
    const names = {
        'basic': 'Basic',
        'rating_weighted': 'Rating Weighted',
        'equipment_focused': 'Equipment Focused',
        'comprehensive': 'Comprehensive',
        'relative_strength': 'Relative Strength'
    };
    return names[algorithm] || algorithm;
}

function getConfidenceIcon(confidence) {
    const icons = {
        'high': '🔥',
        'medium': '👍',
        'low': '⚠️'
    };
    return icons[confidence] || '❓';
}

function showTrifectaTab() {
    const trifectaTab = new bootstrap.Tab(document.getElementById('trifecta-tab'));
    trifectaTab.show();
}