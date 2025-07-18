/**
 * 競艇予測結果表示用JavaScript
 * ES6+ モジュラー実装
 */

class PredictionsViewer {
    constructor() {
        this.data = null;
        this.filteredData = null;
        this.pastData = null;
        this.filteredPastData = null;
        this.venues = new Set();
        this.pastVenues = new Set();
        this.combinationSortStates = {}; // { '<venue>-<race_number>': { column: 'rank', order: 'asc' } }
        this.init();
    }

    /**
     * 初期化
     */
    init() {
        this.setupEventListeners();
        this.loadPredictions();
        this.setupPastDateSelector();
    }

    /**
     * イベントリスナーの設定
     */
    setupEventListeners() {
        // 本日分フィルター変更イベント
        document.getElementById('venue-filter').addEventListener('change', (e) => {
            this.filterData();
        });

        document.getElementById('risk-filter').addEventListener('change', (e) => {
            this.filterData();
        });

        // 過去分フィルター変更イベント
        document.getElementById('past-venue-filter').addEventListener('change', (e) => {
            this.filterPastData();
        });

        document.getElementById('past-risk-filter').addEventListener('change', (e) => {
            this.filterPastData();
        });

        // 過去分データ読み込みボタン
        document.getElementById('load-past-predictions').addEventListener('click', (e) => {
            this.loadPastPredictions();
        });

        // タブ切り替えイベント
        document.getElementById('past-tab').addEventListener('shown.bs.tab', (e) => {
            this.onPastTabShown();
        });

        // Phase 4.1: 検索・フィルター機能のイベントリスナー
        this.setupSearchEventListeners();
    }

    /**
     * 検索・フィルター機能のイベントリスナー設定
     */
    setupSearchEventListeners() {
        // 本日分検索・フィルター
        document.getElementById('search-button').addEventListener('click', (e) => {
            this.performSearch();
        });

        document.getElementById('clear-search-button').addEventListener('click', (e) => {
            this.clearSearch();
        });

        document.getElementById('export-button').addEventListener('click', (e) => {
            this.exportData();
        });

        // 過去分検索・フィルター
        document.getElementById('past-search-button').addEventListener('click', (e) => {
            this.performPastSearch();
        });

        document.getElementById('past-clear-search-button').addEventListener('click', (e) => {
            this.clearPastSearch();
        });

        document.getElementById('past-export-button').addEventListener('click', (e) => {
            this.exportPastData();
        });

        // Enterキーでの検索実行
        const searchInputs = [
            'date-filter', 'race-number-filter', 'boat-number-filter', 'player-name-filter',
            'past-race-number-filter', 'past-boat-number-filter', 'past-player-name-filter'
        ];

        searchInputs.forEach(inputId => {
            const element = document.getElementById(inputId);
            if (element) {
                element.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        e.preventDefault();
                        if (inputId.startsWith('past-')) {
                            this.performPastSearch();
                        } else {
                            this.performSearch();
                        }
                    }
                });
            }
        });
    }

    /**
     * 過去分日付選択の設定
     */
    setupPastDateSelector() {
        const dateSelector = document.getElementById('past-date-selector');
        if (dateSelector) {
            // アクセス日の前日をデフォルトに設定
            const today = new Date();
            const yesterday = new Date(today);
            yesterday.setDate(today.getDate() - 1);
            const yesterdayStr = yesterday.toISOString().split('T')[0];
            dateSelector.value = yesterdayStr;
            
            // 日付変更時のイベントリスナー
            dateSelector.addEventListener('change', (e) => {
                const selectedDate = e.target.value;
                if (selectedDate) {
                    this.loadPastPredictions(selectedDate);
                }
            });
        }
    }

    /**
     * 過去分タブ表示時の処理
     */
    onPastTabShown() {
        console.log('過去分タブが表示されました');
        const dateSelector = document.getElementById('past-date-selector');
        if (dateSelector && dateSelector.value) {
            this.loadPastPredictions(dateSelector.value);
        } else {
            // デフォルトで前日のデータを読み込み
            const today = new Date();
            const yesterday = new Date(today);
            yesterday.setDate(today.getDate() - 1);
            const yesterdayStr = yesterday.toISOString().split('T')[0];
            this.loadPastPredictions(yesterdayStr);
        }
    }

    /**
     * 予測データの読み込み
     */
    async loadPredictions() {
        try {
            console.log('loadPredictions: 開始');
            this.showLoading(true);
            this.showError(false);

            console.log('loadPredictions: データ取得中...');
            const response = await fetch('/outputs/predictions_latest.json');
            console.log('loadPredictions: レスポンス受信', response.status, response.ok);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            console.log('loadPredictions: JSON解析中...');
            this.data = await response.json();
            console.log('loadPredictions: データ取得成功', this.data);
            
            this.filteredData = this.data;
            this.extractVenues();
            this.setupFilters();
            this.renderPredictions();
            this.updateLastUpdated();
            this.showLoading(false);
            this.showMainContent(true);
            console.log('loadPredictions: 完了');
            console.log('showMainContent: メインコンテンツを表示しました');

        } catch (error) {
            console.error('予測データの読み込みに失敗:', error);
            this.showError(true, error.message);
            this.showLoading(false);
        }
    }

    /**
     * 過去分予測データの読み込み
     */
    async loadPastPredictions(selectedDate = null) {
        try {
            if (!selectedDate) {
                const dateSelector = document.getElementById('past-date-selector');
                selectedDate = dateSelector ? dateSelector.value : null;
            }
            
            if (!selectedDate) {
                alert('日付を選択してください。');
                return;
            }

            this.showPastLoading(true);
            this.showPastError(false);
            this.showPastPredictionsContent(false);

            // 過去分データファイルのパスを構築
            const dateStr = selectedDate.replace(/-/g, '');
            const dataUrl = `/outputs/predictions_${dateStr}.json`;

            console.log('過去分データ読み込み開始:', dataUrl);

            const response = await fetch(dataUrl);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('過去分データ取得成功:', data);

            this.pastData = data;
            this.filteredPastData = { ...data };

            this.extractPastVenues();
            this.setupPastFilters();
            this.renderPastPredictions();

            this.showPastLoading(false);
            this.showPastPredictionsContent(true);

            console.log('過去分データ読み込み完了');

        } catch (error) {
            console.error('過去分データ読み込みエラー:', error);
            this.showPastLoading(false);
            this.showPastError(true, `過去分予測データの取得に失敗しました: ${error.message}`);
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
     * 過去分会場情報の抽出
     */
    extractPastVenues() {
        this.pastVenues.clear();
        this.pastData.predictions.forEach(prediction => {
            this.pastVenues.add(prediction.venue);
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
     * 過去分フィルターの設定
     */
    setupPastFilters() {
        const venueFilter = document.getElementById('past-venue-filter');
        venueFilter.innerHTML = '<option value="">全会場</option>';
        
        Array.from(this.pastVenues).sort().forEach(venue => {
            const option = document.createElement('option');
            option.value = venue;
            option.textContent = venue;
            venueFilter.appendChild(option);
        });
    }

    /**
     * データのフィルタリング（基本フィルター）
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
        this.updateSearchResultCount();
    }

    /**
     * 過去分データのフィルタリング（基本フィルター）
     */
    filterPastData() {
        const venueFilter = document.getElementById('past-venue-filter').value;
        const riskFilter = document.getElementById('past-risk-filter').value;

        this.filteredPastData = {
            ...this.pastData,
            predictions: this.pastData.predictions.filter(prediction => {
                const venueMatch = !venueFilter || prediction.venue === venueFilter;
                const riskMatch = !riskFilter || prediction.risk_level === riskFilter;
                return venueMatch && riskMatch;
            })
        };

        this.renderPastPredictions();
        this.updatePastSearchResultCount();
    }

    /**
     * 高度な検索・フィルター機能
     */
    performSearch() {
        if (!this.data) return;

        const searchCriteria = this.getSearchCriteria();
        const filteredPredictions = this.data.predictions.filter(prediction => {
            return this.matchesSearchCriteria(prediction, searchCriteria);
        });

        this.filteredData = {
            ...this.data,
            predictions: filteredPredictions
        };

        this.renderPredictions();
        this.updateSearchResultCount();
        console.log('検索実行完了:', filteredPredictions.length, '件');
    }

    /**
     * 過去分の高度な検索・フィルター機能
     */
    performPastSearch() {
        if (!this.pastData) return;

        const searchCriteria = this.getPastSearchCriteria();
        const filteredPredictions = this.pastData.predictions.filter(prediction => {
            return this.matchesPastSearchCriteria(prediction, searchCriteria);
        });

        this.filteredPastData = {
            ...this.pastData,
            predictions: filteredPredictions
        };

        this.renderPastPredictions();
        this.updatePastSearchResultCount();
        console.log('過去分検索実行完了:', filteredPredictions.length, '件');
    }

    /**
     * 検索条件の取得
     */
    getSearchCriteria() {
        return {
            venue: document.getElementById('venue-filter').value,
            riskLevel: document.getElementById('risk-filter').value,
            raceNumber: document.getElementById('race-number-filter').value,
            hitOnly: document.getElementById('hit-only-filter').checked,
            highExpectedValue: document.getElementById('high-expected-value-filter').checked,
            oddsAvailable: document.getElementById('odds-available-filter').checked
        };
    }

    /**
     * 過去分検索条件の取得
     */
    getPastSearchCriteria() {
        return {
            venue: document.getElementById('past-venue-filter').value,
            riskLevel: document.getElementById('past-risk-filter').value,
            raceNumber: document.getElementById('past-race-number-filter').value,
            boatNumber: document.getElementById('past-boat-number-filter').value,
            playerName: document.getElementById('past-player-name-filter').value,
            hitOnly: document.getElementById('past-hit-only-filter').checked,
            highExpectedValue: document.getElementById('past-high-expected-value-filter').checked,
            oddsAvailable: document.getElementById('past-odds-available-filter').checked
        };
    }

    /**
     * 検索条件とのマッチング
     */
    matchesSearchCriteria(prediction, criteria) {
        // 会場名フィルター
        if (criteria.venue && prediction.venue !== criteria.venue) {
            return false;
        }

        // リスクレベルフィルター
        if (criteria.riskLevel && prediction.risk_level !== criteria.riskLevel) {
            return false;
        }

        // レース番号フィルター
        if (criteria.raceNumber) {
            const raceNum = parseInt(criteria.raceNumber);
            if (prediction.race_number !== raceNum) {
                return false;
            }
        }

        // 的中のみフィルター
        if (criteria.hitOnly) {
            // 的中判定は現在のデータ構造では実装困難のためスキップ
            // TODO: 的中データが追加されたら実装
        }

        // 高期待値のみフィルター
        if (criteria.highExpectedValue) {
            const hasHighExpectedValue = prediction.top_20_combinations.some(combo => 
                combo.expected_value >= 1.5
            );
            if (!hasHighExpectedValue) {
                return false;
            }
        }

        // オッズ取得済みフィルター
        if (criteria.oddsAvailable) {
            // オッズデータの存在確認は現在のデータ構造では実装困難のためスキップ
            // TODO: オッズデータが追加されたら実装
        }

        return true;
    }

    /**
     * 過去分検索条件とのマッチング
     */
    matchesPastSearchCriteria(prediction, criteria) {
        // 会場名フィルター
        if (criteria.venue && prediction.venue !== criteria.venue) {
            return false;
        }

        // リスクレベルフィルター
        if (criteria.riskLevel && prediction.risk_level !== criteria.riskLevel) {
            return false;
        }

        // レース番号フィルター
        if (criteria.raceNumber) {
            const raceNum = parseInt(criteria.raceNumber);
            if (prediction.race_number !== raceNum) {
                return false;
            }
        }

        // 艇番フィルター
        if (criteria.boatNumber) {
            const boatPattern = criteria.boatNumber.toLowerCase().replace(/\s+/g, '');
            let found = false;
            
            // 各組み合わせをチェック
            prediction.top_20_combinations.forEach(combo => {
                const comboStr = combo.combination.toLowerCase();
                if (comboStr.includes(boatPattern)) {
                    found = true;
                }
            });
            
            if (!found) {
                return false;
            }
        }

        // 選手名フィルター
        if (criteria.playerName) {
            const playerPattern = criteria.playerName.toLowerCase();
            // 選手名フィルタは現在のデータ構造では実装困難のためスキップ
            // TODO: 選手名データが追加されたら実装
        }

        // 的中のみフィルター
        if (criteria.hitOnly) {
            // 的中判定は現在のデータ構造では実装困難のためスキップ
            // TODO: 的中データが追加されたら実装
        }

        // 高期待値のみフィルター
        if (criteria.highExpectedValue) {
            const hasHighExpectedValue = prediction.top_20_combinations.some(combo => 
                combo.expected_value >= 1.5
            );
            if (!hasHighExpectedValue) {
                return false;
            }
        }

        // オッズ取得済みフィルター
        if (criteria.oddsAvailable) {
            // オッズデータの存在確認は現在のデータ構造では実装困難のためスキップ
            // TODO: オッズデータが追加されたら実装
        }

        return true;
    }

    /**
     * 検索条件のクリア
     */
    clearSearch() {
        document.getElementById('venue-filter').value = '';
        document.getElementById('risk-filter').value = '';
        document.getElementById('race-number-filter').value = '';
        document.getElementById('hit-only-filter').checked = false;
        document.getElementById('high-expected-value-filter').checked = false;
        document.getElementById('odds-available-filter').checked = false;
        
        this.filteredData = this.data ? { ...this.data } : null;
        this.renderPredictions();
        this.updateSearchResultCount();
    }

    /**
     * 過去分検索条件のクリア
     */
    clearPastSearch() {
        document.getElementById('past-venue-filter').value = '';
        document.getElementById('past-risk-filter').value = '';
        document.getElementById('past-race-number-filter').value = '';
        document.getElementById('past-boat-number-filter').value = '';
        document.getElementById('past-player-name-filter').value = '';
        document.getElementById('past-hit-only-filter').checked = false;
        document.getElementById('past-high-expected-value-filter').checked = false;
        document.getElementById('past-odds-available-filter').checked = false;
        
        this.filteredPastData = this.pastData ? { ...this.pastData } : null;
        this.renderPastPredictions();
        this.updatePastSearchResultCount();
    }

    /**
     * 検索結果件数の更新
     */
    updateSearchResultCount() {
        const countElement = document.getElementById('search-result-count');
        if (countElement) {
            const count = this.filteredData ? this.filteredData.predictions.length : 0;
            countElement.textContent = `検索結果: ${count}件`;
        }
    }

    /**
     * 過去分検索結果件数の更新
     */
    updatePastSearchResultCount() {
        const countElement = document.getElementById('past-search-result-count');
        if (countElement) {
            const count = this.filteredPastData ? this.filteredPastData.predictions.length : 0;
            countElement.textContent = `検索結果: ${count}件`;
        }
    }

    /**
     * データエクスポート機能
     */
    exportData() {
        if (!this.filteredData) {
            alert('エクスポートするデータがありません。');
            return;
        }

        const exportData = this.prepareExportData(this.filteredData);
        this.downloadFile(exportData, 'predictions_export.json', 'application/json');
    }

    /**
     * 過去分データエクスポート機能
     */
    exportPastData() {
        if (!this.filteredPastData) {
            alert('エクスポートするデータがありません。');
            return;
        }

        const exportData = this.prepareExportData(this.filteredPastData);
        this.downloadFile(exportData, 'past_predictions_export.json', 'application/json');
    }

    /**
     * エクスポート用データの準備
     */
    prepareExportData(data) {
        const exportData = {
            export_info: {
                exported_at: new Date().toISOString(),
                total_predictions: data.predictions.length,
                search_criteria: this.getSearchCriteria()
            },
            data: data
        };

        return exportData;
    }

    /**
     * ファイルダウンロード機能
     */
    downloadFile(data, filename, contentType) {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: contentType });
        const url = URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        URL.revokeObjectURL(url);
        console.log('エクスポート完了:', filename);
    }

    /**
     * 予測結果の描画
     */
    renderPredictions() {
        console.log('renderPredictions: 開始');
        this.renderSummary();
        this.renderVenues();
        console.log('renderPredictions: 完了');
    }

    /**
     * 過去分予測結果の描画
     */
    renderPastPredictions() {
        console.log('renderPastPredictions: 開始');
        this.renderPastSummary();
        this.renderPastVenues();
        console.log('renderPastPredictions: 完了');
    }

    /**
     * サマリーの描画
     */
    renderSummary() {
        console.log('renderSummary: 開始', this.filteredData);
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

        console.log('renderSummary: HTML生成完了', html);
        document.getElementById('summary-section').innerHTML = html;
        console.log('renderSummary: 完了');
    }

    /**
     * 過去分サマリーの描画
     */
    renderPastSummary() {
        console.log('renderPastSummary: 開始', this.filteredPastData);
        const summary = this.filteredPastData.execution_summary;
        const model = this.filteredPastData.model_info;
        const generatedAt = new Date(this.filteredPastData.generated_at);

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
                        <strong>予測日:</strong> ${this.filteredPastData.prediction_date}
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

        console.log('renderPastSummary: HTML生成完了', html);
        document.getElementById('past-summary-section').innerHTML = html;
        console.log('renderPastSummary: 完了');
    }

    /**
     * 会場別レースの描画
     */
    renderVenues() {
        const venuesSection = document.getElementById('venues-section');
        venuesSection.innerHTML = '';

        // 会場ごとにレースをグループ化
        const venueGroups = {};
        this.filteredData.predictions.forEach(prediction => {
            if (!venueGroups[prediction.venue]) {
                venueGroups[prediction.venue] = [];
            }
            venueGroups[prediction.venue].push(prediction);
        });

        // 会場ごとにレンダリング
        let allHtml = '';
        Object.keys(venueGroups).sort().forEach(venue => {
            const venueSectionHtml = this.renderVenueSection(venue, venueGroups[venue]);
            allHtml += venueSectionHtml;
        });
        
        venuesSection.innerHTML = allHtml;
        this.setupRaceHeaders();
    }

    /**
     * 過去分会場別レースの描画
     */
    renderPastVenues() {
        const venuesSection = document.getElementById('past-venues-section');
        venuesSection.innerHTML = '';

        // 会場ごとにレースをグループ化
        const venueGroups = {};
        this.filteredPastData.predictions.forEach(prediction => {
            if (!venueGroups[prediction.venue]) {
                venueGroups[prediction.venue] = [];
            }
            venueGroups[prediction.venue].push(prediction);
        });

        // 会場ごとにレンダリング
        let allHtml = '';
        Object.keys(venueGroups).sort().forEach(venue => {
            const venueSectionHtml = this.renderVenueSection(venue, venueGroups[venue]);
            allHtml += venueSectionHtml;
        });
        
        venuesSection.innerHTML = allHtml;
        this.setupPastRaceHeaders();
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
                            ${this.renderCombinationsTable(race.top_20_combinations, race.venue, race.race_number)}
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
                <div class="row">
                    <div class="col-12">
                        <div class="odds-section mt-3">
                            <button class="btn btn-outline-info btn-sm fetch-odds-btn" data-date="${race.prediction_date}" data-venue="${race.venue}" data-race="${race.race_number}">
                                <i class="fas fa-coins me-1"></i>オッズ取得
                            </button>
                            <div class="odds-loading d-none mt-2">
                                <div class="spinner-border spinner-border-sm text-info" role="status">
                                    <span class="visually-hidden">取得中...</span>
                                </div>
                                <span class="ms-2">オッズ取得中...</span>
                            </div>
                            <div class="odds-error alert alert-danger d-none mt-2" role="alert">
                                <i class="fas fa-exclamation-triangle me-1"></i><span class="odds-error-text">オッズ取得に失敗しました</span>
                            </div>
                            <div class="odds-compare-table mt-2 d-none"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 組み合わせテーブルの描画
     */
    renderCombinationsTable(combinations, venue, raceNumber) {
        const raceId = `${venue}-${raceNumber}`;
        // デフォルトソート状態
        if (!this.combinationSortStates[raceId]) {
            this.combinationSortStates[raceId] = { column: 'rank', order: 'asc' };
        }
        const { column, order } = this.combinationSortStates[raceId];
        // ソート処理
        const sorted = [...combinations].sort((a, b) => {
            let vA, vB;
            switch (column) {
                case 'rank':
                    vA = a.rank; vB = b.rank; break;
                case 'combination':
                    vA = a.combination; vB = b.combination; break;
                case 'probability':
                    vA = a.probability; vB = b.probability; break;
                case 'expected_value':
                    vA = a.expected_value; vB = b.expected_value; break;
                default:
                    vA = a.rank; vB = b.rank;
            }
            if (typeof vA === 'string') {
                return order === 'asc' ? vA.localeCompare(vB) : vB.localeCompare(vA);
            } else {
                return order === 'asc' ? vA - vB : vB - vA;
            }
        });
        // ソートアイコン
        const icon = (col) => {
            if (column !== col) return '';
            return order === 'asc' ? '<i class="fas fa-caret-up ms-1"></i>' : '<i class="fas fa-caret-down ms-1"></i>';
        };
        // テーブルHTML
        let html = `
            <table class="table table-hover combinations-table" data-race-id="${raceId}">
                <thead>
                    <tr>
                        <th class="sortable" data-col="rank">順位${icon('rank')}</th>
                        <th class="sortable" data-col="combination">組み合わせ${icon('combination')}</th>
                        <th class="sortable" data-col="probability">確率${icon('probability')}</th>
                        <th class="sortable" data-col="expected_value">期待値${icon('expected_value')}</th>
                    </tr>
                </thead>
                <tbody>
        `;
        sorted.forEach(combination => {
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
        // ソートイベント付与は描画後にsetupCombinationSortHandlersで行う
        setTimeout(() => this.setupCombinationSortHandlers(raceId), 0);
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
        document.querySelectorAll('#venues-section .race-header').forEach(header => {
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
        
        // 最初のレースを自動で開く
        const firstHeader = document.querySelector('#venues-section .race-header');
        if (firstHeader) {
            const raceId = firstHeader.dataset.raceId;
            const details = document.getElementById(`details-${raceId}`);
            const icon = firstHeader.querySelector('.fa-chevron-down, .fa-chevron-up');
            
            if (details && !details.classList.contains('show')) {
                details.classList.add('show');
                icon.classList.remove('fa-chevron-down');
                icon.classList.add('fa-chevron-up');
            }
        }
        
        // オッズ取得ボタンのイベント設定
        document.querySelectorAll('#venues-section .fetch-odds-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const date = btn.getAttribute('data-date');
                const venue = btn.getAttribute('data-venue');
                const raceNo = btn.getAttribute('data-race');
                const oddsSection = btn.closest('.odds-section');
                const loading = oddsSection.querySelector('.odds-loading');
                const error = oddsSection.querySelector('.odds-error');
                const errorText = oddsSection.querySelector('.odds-error-text');
                const table = oddsSection.querySelector('.odds-compare-table');
                // 表示制御
                loading.classList.remove('d-none');
                error.classList.add('d-none');
                table.classList.add('d-none');
                table.innerHTML = '';
                try {
                    // ファイル名例: odds_data_2024-02-07_KIRYU_R1.json
                    const oddsFile = `/kyotei_predictor/data/raw/odds_data_${date}_${venue}_R${raceNo}.json`;
                    const resp = await fetch(oddsFile);
                    if (!resp.ok) throw new Error('オッズデータが見つかりません');
                    const oddsData = await resp.json();
                    // 予測データとオッズを比較してテーブル生成
                    table.innerHTML = this.renderOddsCompareTable(oddsData, this.data.predictions.find(p => p.prediction_date === date && p.venue === venue && p.race_number === parseInt(raceNo)));
                    table.classList.remove('d-none');
                } catch (err) {
                    errorText.textContent = err.message || 'オッズ取得に失敗しました';
                    error.classList.remove('d-none');
                } finally {
                    loading.classList.add('d-none');
                }
            });
        });
    }

    /**
     * 過去分レースヘッダーのイベント設定
     */
    setupPastRaceHeaders() {
        document.querySelectorAll('#past-venues-section .race-header').forEach(header => {
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
        
        // 最初のレースを自動で開く
        const firstHeader = document.querySelector('#past-venues-section .race-header');
        if (firstHeader) {
            const raceId = firstHeader.dataset.raceId;
            const details = document.getElementById(`details-${raceId}`);
            const icon = firstHeader.querySelector('.fa-chevron-down, .fa-chevron-up');
            
            if (details && !details.classList.contains('show')) {
                details.classList.add('show');
                icon.classList.remove('fa-chevron-down');
                icon.classList.add('fa-chevron-up');
            }
        }
        
        // オッズ取得ボタンのイベント設定
        document.querySelectorAll('#past-venues-section .fetch-odds-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const date = btn.getAttribute('data-date');
                const venue = btn.getAttribute('data-venue');
                const raceNo = btn.getAttribute('data-race');
                const oddsSection = btn.closest('.odds-section');
                const loading = oddsSection.querySelector('.odds-loading');
                const error = oddsSection.querySelector('.odds-error');
                const errorText = oddsSection.querySelector('.odds-error-text');
                const table = oddsSection.querySelector('.odds-compare-table');
                // 表示制御
                loading.classList.remove('d-none');
                error.classList.add('d-none');
                table.classList.add('d-none');
                table.innerHTML = '';
                try {
                    // ファイル名例: odds_data_2024-02-07_KIRYU_R1.json
                    const oddsFile = `/kyotei_predictor/data/raw/odds_data_${date}_${venue}_R${raceNo}.json`;
                    const resp = await fetch(oddsFile);
                    if (!resp.ok) throw new Error('オッズデータが見つかりません');
                    const oddsData = await resp.json();
                    // 予測データとオッズを比較してテーブル生成
                    table.innerHTML = this.renderOddsCompareTable(oddsData, this.pastData.predictions.find(p => p.prediction_date === date && p.venue === venue && p.race_number === parseInt(raceNo)));
                    table.classList.remove('d-none');
                } catch (err) {
                    errorText.textContent = err.message || 'オッズ取得に失敗しました';
                    error.classList.remove('d-none');
                } finally {
                    loading.classList.add('d-none');
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
     * オッズ比較テーブルの描画
     */
    renderOddsCompareTable(oddsData, race = null) {
        // race: 予測データのtop_20_combinationsを含むオブジェクト
        // oddsData.combinations: [{combination, odds, ...}]
        // 予測データとオッズデータを組み合わせて比較
        let oddsMap = {};
        (oddsData.combinations || []).forEach(row => {
            oddsMap[row.combination] = row.odds;
        });
        let html = `<table class="table table-bordered table-sm">
            <thead><tr>
                <th>組み合わせ</th>
                <th>予測確率</th>
                <th>期待値</th>
                <th>オッズ</th>
                <th>期待リターン</th>
            </tr></thead><tbody>`;
        if (race && race.top_20_combinations) {
            race.top_20_combinations.forEach(row => {
                const odds = oddsMap[row.combination];
                const expectedReturn = odds ? (row.probability * odds) : '-';
                html += `<tr>
                    <td>${row.combination}</td>
                    <td>${(row.probability * 100).toFixed(2)}%</td>
                    <td>${row.expected_value.toFixed(1)}</td>
                    <td>${odds !== undefined ? odds : '-'}</td>
                    <td>${odds !== undefined ? expectedReturn.toFixed(2) : '-'}</td>
                </tr>`;
            });
        } else {
            // fallback: オッズデータのみ
            (oddsData.combinations || []).forEach(row => {
                html += `<tr><td>${row.combination}</td><td>-</td><td>-</td><td>${row.odds}</td><td>-</td></tr>`;
            });
        }
        html += '</tbody></table>';
        return html;
    }

    /**
     * ソートイベントハンドラ
     */
    setupCombinationSortHandlers(raceId) {
        const table = document.querySelector(`.combinations-table[data-race-id="${raceId}"]`);
        if (!table) return;
        const headers = table.querySelectorAll('th.sortable');
        headers.forEach(th => {
            th.style.cursor = 'pointer';
            th.onclick = () => {
                const col = th.getAttribute('data-col');
                const state = this.combinationSortStates[raceId];
                if (state.column === col) {
                    state.order = state.order === 'asc' ? 'desc' : 'asc';
                } else {
                    state.column = col;
                    state.order = 'asc';
                }
                // テーブルのみ再描画（展開状態を保持）
                const race = this.findRaceById(raceId);
                if (race) {
                    const tableContainer = table.closest('.table-responsive');
                    if (tableContainer) {
                        tableContainer.innerHTML = this.renderCombinationsTable(race.top_20_combinations, race.venue, race.race_number);
                    }
                }
            };
        });
    }

    /**
     * レースIDからraceデータを取得
     */
    findRaceById(raceId) {
        const [venue, raceNumber] = raceId.split('-');
        const num = parseInt(raceNumber, 10);
        // 本日分・過去分両対応
        const all = (this.filteredData?.predictions || []).concat(this.filteredPastData?.predictions || []);
        return all.find(r => r.venue === venue && r.race_number === num);
    }

    /**
     * ローディング表示の制御
     */
    showLoading(show) {
        const loading = document.getElementById('loading');
        console.log('showLoading: 呼び出し', show, loading);
        if (loading) {
            loading.style.display = show ? 'block' : 'none';
            console.log('showLoading: 表示設定完了', loading.style.display);
        } else {
            console.error('showLoading: loading要素が見つかりません');
        }
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
        console.log('showMainContent: 呼び出し', show, mainContent);
        if (mainContent) {
            if (show) {
                mainContent.classList.remove('d-none');
                mainContent.style.display = 'block';
            } else {
                mainContent.classList.add('d-none');
                mainContent.style.display = 'none';
            }
            console.log('showMainContent: 表示設定完了', mainContent.style.display, 'd-none:', mainContent.classList.contains('d-none'));
        } else {
            console.error('showMainContent: main-content要素が見つかりません');
        }
    }

    /**
     * 過去分コンテンツ表示の制御
     */
    showPastPredictionsContent(show) {
        const pastPredictionsContent = document.getElementById('past-predictions-content');
        console.log('showPastPredictionsContent: 呼び出し', show, pastPredictionsContent);
        if (pastPredictionsContent) {
            if (show) {
                pastPredictionsContent.classList.remove('d-none');
                pastPredictionsContent.style.display = 'block';
            } else {
                pastPredictionsContent.classList.add('d-none');
                pastPredictionsContent.style.display = 'none';
            }
            console.log('showPastPredictionsContent: 表示設定完了', pastPredictionsContent.style.display, 'd-none:', pastPredictionsContent.classList.contains('d-none'));
        } else {
            console.error('showPastPredictionsContent: past-predictions-content要素が見つかりません');
        }
    }

    /**
     * 過去分ローディング表示の制御
     */
    showPastLoading(show) {
        const loading = document.getElementById('past-loading');
        console.log('showPastLoading: 呼び出し', show, loading);
        if (loading) {
            loading.style.display = show ? 'block' : 'none';
            console.log('showPastLoading: 表示設定完了', loading.style.display);
        } else {
            console.error('showPastLoading: past-loading要素が見つかりません');
        }
    }

    /**
     * 過去分エラー表示の制御
     */
    showPastError(show, message = '過去分予測データの取得に失敗しました') {
        const errorMessage = document.getElementById('past-error-message');
        const errorText = document.getElementById('past-error-text');
        
        if (show) {
            errorText.textContent = message;
            errorMessage.classList.remove('d-none');
        } else {
            errorMessage.classList.add('d-none');
        }
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