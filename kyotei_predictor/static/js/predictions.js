/**
 * 競艇予測結果表示用JavaScript
 * ES6+ モジュラー実装
 */

class PredictionsViewer {
    constructor() {
        this.data = null;
        this.filteredData = null;
        this.venues = new Set();
        this.init();
    }

    /**
     * 初期化
     */
    init() {
        this.setupEventListeners();
        this.loadPredictions();
    }

    /**
     * イベントリスナーの設定
     */
    setupEventListeners() {
        // フィルター変更イベント
        document.getElementById('venue-filter').addEventListener('change', (e) => {
            this.filterData();
        });

        document.getElementById('risk-filter').addEventListener('change', (e) => {
            this.filterData();
        });
    }

    /**
     * 予測データの読み込み
     */
    async loadPredictions() {
        try {
            this.showLoading(true);
            this.showError(false);

            const response = await fetch('/outputs/predictions_latest.json');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            this.data = await response.json();
            this.filteredData = this.data;
            this.extractVenues();
            this.setupFilters();
            this.renderPredictions();
            this.updateLastUpdated();
            this.showLoading(false);
            this.showMainContent(true);

        } catch (error) {
            console.error('予測データの読み込みに失敗:', error);
            this.showError(true, error.message);
            this.showLoading(false);
        }
    }

    /**
     * 会場情報の抽出
     */
    extractVenues() {
        this.venues.clear();
        this.data.predictions.forEach(prediction => {
            this.venues.add(prediction.venue);
        });
    }

    /**
     * フィルターの設定
     */
    setupFilters() {
        const venueFilter = document.getElementById('venue-filter');
        venueFilter.innerHTML = '<option value="">全会場</option>';
        
        Array.from(this.venues).sort().forEach(venue => {
            const option = document.createElement('option');
            option.value = venue;
            option.textContent = venue;
            venueFilter.appendChild(option);
        });
    }

    /**
     * データのフィルタリング
     */
    filterData() {
        const venueFilter = document.getElementById('venue-filter').value;
        const riskFilter = document.getElementById('risk-filter').value;

        this.filteredData = {
            ...this.data,
            predictions: this.data.predictions.filter(prediction => {
                const venueMatch = !venueFilter || prediction.venue === venueFilter;
                const riskMatch = !riskFilter || prediction.risk_level === riskFilter;
                return venueMatch && riskMatch;
            })
        };

        this.renderPredictions();
    }

    /**
     * 予測結果の描画
     */
    renderPredictions() {
        this.renderSummary();
        this.renderVenues();
    }

    /**
     * サマリーの描画
     */
    renderSummary() {
        const summary = this.filteredData.execution_summary;
        const model = this.filteredData.model_info;
        const generatedAt = new Date(this.filteredData.generated_at);

        const html = `
            <div class="row">
                <div class="col-md-6">
                    <div class="row">
                        <div class="col-6">
                            <div class="text-center p-3 bg-light rounded">
                                <div class="h4 text-primary mb-0">${summary.total_venues}</div>
                                <div class="small text-muted">対象会場数</div>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="text-center p-3 bg-light rounded">
                                <div class="h4 text-success mb-0">${summary.total_races}</div>
                                <div class="small text-muted">予測レース数</div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="row">
                        <div class="col-6">
                            <div class="text-center p-3 bg-light rounded">
                                <div class="h4 text-info mb-0">${summary.successful_predictions}</div>
                                <div class="small text-muted">成功レース数</div>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="text-center p-3 bg-light rounded">
                                <div class="h4 text-warning mb-0">${summary.execution_time_minutes.toFixed(1)}</div>
                                <div class="small text-muted">実行時間(分)</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <hr>
            <div class="row">
                <div class="col-md-6">
                    <div class="mb-2">
                        <strong>予測日:</strong> ${this.filteredData.prediction_date}
                    </div>
                    <div class="mb-2">
                        <strong>生成日時:</strong> ${generatedAt.toLocaleString('ja-JP')}
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="mb-2">
                        <strong>モデル:</strong> ${model.model_name || 'N/A'} (${model.version || 'N/A'})
                    </div>
                    <div class="mb-2">
                        <strong>学習データ:</strong> ${model.training_data_until || 'N/A'}まで
                    </div>
                </div>
            </div>
        `;

        document.getElementById('summary-section').innerHTML = html;
    }

    /**
     * 会場別レースの描画
     */
    renderVenues() {
        // 会場ごとにグループ化
        const venues = {};
        this.filteredData.predictions.forEach(prediction => {
            if (!venues[prediction.venue]) {
                venues[prediction.venue] = [];
            }
            venues[prediction.venue].push(prediction);
        });

        let html = '';
        Object.keys(venues).sort().forEach(venue => {
            html += this.renderVenueSection(venue, venues[venue]);
        });

        document.getElementById('venues-section').innerHTML = html;
        this.setupRaceHeaders();
    }

    /**
     * 会場セクションの描画
     */
    renderVenueSection(venue, races) {
        const sortedRaces = races.sort((a, b) => a.race_number - b.race_number);
        
        let html = `
            <div class="venue-section fade-in">
                <div class="venue-header">
                    <h3><i class="fas fa-map-marker-alt me-2"></i>${venue}</h3>
                </div>
        `;

        sortedRaces.forEach(race => {
            html += this.renderRaceHeader(race);
            html += this.renderRaceDetails(race);
        });

        html += '</div>';
        return html;
    }

    /**
     * レースヘッダーの描画
     */
    renderRaceHeader(race) {
        const riskClass = this.getRiskClass(race.risk_level);
        const riskText = this.getRiskText(race.risk_level);

        return `
            <div class="race-header" data-race-id="${race.venue}-${race.race_number}">
                <div class="race-info">
                    <span class="race-number">R${race.race_number}</span>
                    <span class="race-time">
                        <i class="fas fa-clock me-1"></i>${race.race_time}
                    </span>
                </div>
                <div class="race-meta">
                    <span class="risk-badge ${riskClass}">${riskText}</span>
                    <i class="fas fa-chevron-down ms-2"></i>
                </div>
            </div>
        `;
    }

    /**
     * レース詳細の描画
     */
    renderRaceDetails(race) {
        return `
            <div class="race-details" id="details-${race.venue}-${race.race_number}">
                <div class="row">
                    <div class="col-12">
                        <h5 class="mb-3">
                            <i class="fas fa-list-ol me-2"></i>3連単上位20組 予測確率・期待値
                        </h5>
                        <div class="table-responsive">
                            ${this.renderCombinationsTable(race.top_20_combinations)}
                        </div>
                    </div>
                </div>
                <div class="row">
                    <div class="col-12">
                        <h5 class="mb-3">
                            <i class="fas fa-shopping-cart me-2"></i>購入方法提案
                        </h5>
                        ${this.renderPurchaseSuggestions(race.purchase_suggestions)}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 組み合わせテーブルの描画
     */
    renderCombinationsTable(combinations) {
        let html = `
            <table class="table table-hover">
                <thead>
                    <tr>
                        <th>順位</th>
                        <th>組み合わせ</th>
                        <th>確率</th>
                        <th>期待値</th>
                    </tr>
                </thead>
                <tbody>
        `;

        combinations.forEach(combination => {
            const rankClass = this.getRankClass(combination.rank);
            const probabilityClass = this.getProbabilityClass(combination.probability);
            const expectedValueClass = this.getExpectedValueClass(combination.expected_value);

            html += `
                <tr class="${rankClass}">
                    <td>
                        <span class="badge bg-primary">${combination.rank}</span>
                    </td>
                    <td>
                        <strong>${combination.combination}</strong>
                    </td>
                    <td>
                        <div class="${probabilityClass}">
                            ${(combination.probability * 100).toFixed(2)}%
                        </div>
                        <div class="probability-bar">
                            <div class="probability-fill" style="width: ${combination.probability * 100}%"></div>
                        </div>
                    </td>
                    <td>
                        <span class="expected-value ${expectedValueClass}">
                            ${combination.expected_value.toFixed(1)}
                        </span>
                    </td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        return html;
    }

    /**
     * 購入提案の描画
     */
    renderPurchaseSuggestions(suggestions) {
        let html = '<div class="purchase-suggestions">';

        suggestions.forEach(suggestion => {
            const typeClass = this.getSuggestionTypeClass(suggestion.type);
            const expectedValueClass = this.getExpectedValueClass(suggestion.expected_return);

            html += `
                <div class="suggestion-card">
                    <span class="suggestion-type ${typeClass}">${this.getSuggestionTypeText(suggestion.type)}</span>
                    <div class="suggestion-title">${suggestion.description}</div>
                    <div class="suggestion-stats">
                        <div class="stat-item">
                            <div class="stat-label">組数</div>
                            <div class="stat-value">${suggestion.combinations.length}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">合計確率</div>
                            <div class="stat-value">${(suggestion.total_probability * 100).toFixed(2)}%</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">購入金額</div>
                            <div class="stat-value">¥${suggestion.total_cost.toLocaleString()}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">期待リターン</div>
                            <div class="stat-value ${expectedValueClass}">${suggestion.expected_return.toFixed(1)}</div>
                        </div>
                    </div>
                    <div class="combinations-list">
                        ${suggestion.combinations.map(combo => 
                            `<span class="combination-tag">${combo}</span>`
                        ).join('')}
                    </div>
                </div>
            `;
        });

        html += '</div>';
        return html;
    }

    /**
     * レースヘッダーのイベント設定
     */
    setupRaceHeaders() {
        document.querySelectorAll('.race-header').forEach(header => {
            header.addEventListener('click', () => {
                const raceId = header.dataset.raceId;
                const details = document.getElementById(`details-${raceId}`);
                const icon = header.querySelector('.fa-chevron-down, .fa-chevron-up');
                
                if (details.classList.contains('show')) {
                    details.classList.remove('show');
                    icon.classList.remove('fa-chevron-up');
                    icon.classList.add('fa-chevron-down');
                } else {
                    details.classList.add('show');
                    icon.classList.remove('fa-chevron-down');
                    icon.classList.add('fa-chevron-up');
                }
            });
        });
    }

    /**
     * リスククラスの取得
     */
    getRiskClass(riskLevel) {
        const riskMap = {
            'LOW': 'risk-low',
            'MEDIUM': 'risk-medium',
            'HIGH': 'risk-high'
        };
        return riskMap[riskLevel] || 'risk-medium';
    }

    /**
     * リスクテキストの取得
     */
    getRiskText(riskLevel) {
        const riskMap = {
            'LOW': '低リスク',
            'MEDIUM': '中リスク',
            'HIGH': '高リスク'
        };
        return riskMap[riskLevel] || '中リスク';
    }

    /**
     * ランククラスの取得
     */
    getRankClass(rank) {
        if (rank === 1) return 'rank-1';
        if (rank === 2) return 'rank-2';
        if (rank === 3) return 'rank-3';
        return '';
    }

    /**
     * 確率クラスの取得
     */
    getProbabilityClass(probability) {
        if (probability >= 0.1) return 'probability-high';
        if (probability >= 0.01) return 'probability-medium';
        return 'probability-low';
    }

    /**
     * 期待値クラスの取得
     */
    getExpectedValueClass(expectedValue) {
        if (expectedValue > 0) return 'positive';
        if (expectedValue < 0) return 'negative';
        return 'neutral';
    }

    /**
     * 提案タイプクラスの取得
     */
    getSuggestionTypeClass(type) {
        const typeMap = {
            'wheel': 'wheel',
            'box': 'box',
            'nagashi': 'nagashi'
        };
        return typeMap[type] || 'wheel';
    }

    /**
     * 提案タイプテキストの取得
     */
    getSuggestionTypeText(type) {
        const typeMap = {
            'wheel': '流し',
            'box': 'ボックス',
            'nagashi': '流し'
        };
        return typeMap[type] || 'その他';
    }

    /**
     * ローディング表示の制御
     */
    showLoading(show) {
        const loading = document.getElementById('loading');
        loading.style.display = show ? 'block' : 'none';
    }

    /**
     * エラー表示の制御
     */
    showError(show, message = '予測データの取得に失敗しました') {
        const errorMessage = document.getElementById('error-message');
        const errorText = document.getElementById('error-text');
        
        if (show) {
            errorText.textContent = message;
            errorMessage.classList.remove('d-none');
        } else {
            errorMessage.classList.add('d-none');
        }
    }

    /**
     * メインコンテンツ表示の制御
     */
    showMainContent(show) {
        const mainContent = document.getElementById('main-content');
        mainContent.style.display = show ? 'block' : 'none';
    }

    /**
     * 最終更新時刻の更新
     */
    updateLastUpdated() {
        const lastUpdated = document.getElementById('last-updated');
        const now = new Date();
        lastUpdated.innerHTML = `
            <i class="fas fa-clock me-1"></i>更新時刻: ${now.toLocaleString('ja-JP')}
        `;
    }
}

// DOM読み込み完了後に初期化
document.addEventListener('DOMContentLoaded', () => {
    new PredictionsViewer();
}); 