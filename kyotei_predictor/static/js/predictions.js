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
        this.oddsCache = {}; // オッズデータのキャッシュ
        this.currentRaceContext = null; // 現在のレースコンテキスト
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

        // オッズ取得ボタンのイベントリスナー（動的に追加される要素のため、イベント委譲を使用）
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('fetch-odds-btn')) {
                const button = e.target;
                const date = button.dataset.date;
                const venue = button.dataset.venue;
                const race = button.dataset.race;
                this.fetchOddsForRace(date, venue, race, button);
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

            // 利用可能な過去分データファイルを確認
            const availableFiles = await this.getAvailablePastPredictionFiles();
            console.log('利用可能な過去分ファイル:', availableFiles);

            // 選択された日付に対応するファイルを探す
            const targetDate = new Date(selectedDate);
            const targetDateStr = targetDate.toISOString().split('T')[0];
            const targetDateStrCompact = targetDateStr.replace(/-/g, '');
            
            let dataUrl = null;
            let foundFile = null;

            // まず完全一致を探す
            for (const file of availableFiles) {
                if (file.includes(targetDateStrCompact) || file.includes(targetDateStr)) {
                    dataUrl = `/outputs/${file}`;
                    foundFile = file;
                    break;
                }
            }

            // 完全一致が見つからない場合、最も近い日付のファイルを探す
            if (!dataUrl) {
                const closestFile = this.findClosestDateFile(availableFiles, targetDate);
                if (closestFile) {
                    dataUrl = `/outputs/${closestFile}`;
                    foundFile = closestFile;
                    console.log('最も近い日付のファイルを使用:', closestFile);
                }
            }

            if (!dataUrl) {
                throw new Error(`指定された日付（${selectedDate}）の予測データファイルが見つかりません。`);
            }

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
     * 利用可能な過去分予測データファイルの取得
     */
    async getAvailablePastPredictionFiles() {
        try {
            // 利用可能なファイルのリストを取得（実際の実装ではサーバーサイドで提供）
            // 現在は固定リストを使用
            return [
                'predictions_2024-04-30.json',
                'predictions_20250715.json',
                'predictions_2025-07-07.json',
                'predictions_2024-07-12.json'
            ];
        } catch (error) {
            console.error('利用可能なファイルリストの取得に失敗:', error);
            return [];
        }
    }

    /**
     * 最も近い日付のファイルを探す
     */
    findClosestDateFile(availableFiles, targetDate) {
        let closestFile = null;
        let minDiff = Infinity;

        for (const file of availableFiles) {
            if (!file.startsWith('predictions_')) continue;
            
            // ファイル名から日付を抽出
            const dateMatch = file.match(/predictions_(\d{4})[-_]?(\d{2})[-_]?(\d{2})\.json/);
            if (!dateMatch) continue;

            const year = parseInt(dateMatch[1]);
            const month = parseInt(dateMatch[2]);
            const day = parseInt(dateMatch[3]);
            const fileDate = new Date(year, month - 1, day);

            const diff = Math.abs(targetDate.getTime() - fileDate.getTime());
            if (diff < minDiff) {
                minDiff = diff;
                closestFile = file;
            }
        }

        return closestFile;
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
        const combos = prediction.all_combinations || prediction.top_20_combinations || [];
        if (criteria.highExpectedValue) {
            const hasHighExpectedValue = combos.some(combo => combo.expected_value >= 1.5);
            if (!hasHighExpectedValue) return false;
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
        const combosPast = prediction.all_combinations || prediction.top_20_combinations || [];
        if (criteria.boatNumber) {
            const boatPattern = criteria.boatNumber.toLowerCase().replace(/\s+/g, '');
            let found = false;
            combosPast.forEach(combo => {
                const comboStr = (combo.combination || '').toLowerCase();
                if (comboStr.includes(boatPattern)) found = true;
            });
            if (!found) return false;
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
            const hasHighExpectedValue = combosPast.some(combo => combo.expected_value >= 1.5);
            if (!hasHighExpectedValue) return false;
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
        this.setupSuggestionToggleHandlers();
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
        this.setupSuggestionToggleHandlers();
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
        
        // 非同期で組み合わせテーブルをレンダリング
        setTimeout(() => {
            sortedRaces.forEach(race => {
                this.renderCombinationsTableAsync(race);
            });
        }, 0);
        
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
        // 予測データの日付を取得
        const predictionDate = this.filteredData?.prediction_date || this.filteredPastData?.prediction_date;
        
        console.log('renderRaceDetails: レース情報:', {
            venue: race.venue,
            race_number: race.race_number,
            prediction_date: predictionDate,
            filteredData_prediction_date: this.filteredData?.prediction_date,
            filteredPastData_prediction_date: this.filteredPastData?.prediction_date
        });
        
        // レースコンテキストを設定
        this.setCurrentRaceContext(race.venue, race.race_number, predictionDate);

        return `
            <div class="race-details" id="details-${race.venue}-${race.race_number}">
                <!-- 3連単上位20組セクション -->
                <div class="race-section" id="section-${race.venue}-${race.race_number}-combinations">
                    <div class="section-header" data-section="combinations" data-race-id="${race.venue}-${race.race_number}">
                        <h5 class="mb-0">
                            <i class="fas fa-list-ol me-2"></i>3連単上位20組 予測確率・期待値
                            <i class="fas fa-chevron-down ms-2 section-toggle"></i>
                        </h5>
                    </div>
                    <div class="section-content">
                        <div class="table-responsive" id="combinations-table-${race.venue}-${race.race_number}">
                            <div class="text-center py-4">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">読み込み中...</span>
                                </div>
                                <p class="mt-2 text-muted">組み合わせテーブルを読み込み中...</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- 投資提案セクション（オッズ情報統合） -->
                <div class="race-section" id="section-${race.venue}-${race.race_number}-suggestions">
                    <div class="section-header" data-section="suggestions" data-race-id="${race.venue}-${race.race_number}">
                        <h5 class="mb-0">
                            <i class="fas fa-chart-line me-2"></i>投資提案・オッズ情報
                            <i class="fas fa-chevron-down ms-2 section-toggle"></i>
                        </h5>
                    </div>
                    <div class="section-content">
                        <!-- オッズ情報サマリー -->
                        <div class="odds-summary mb-3">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="card border-info">
                                        <div class="card-header bg-info text-white">
                                            <h6 class="mb-0">
                                                <i class="fas fa-coins me-2"></i>オッズ情報
                                            </h6>
                                        </div>
                                        <div class="card-body">
                                            <div class="row">
                                                <div class="col-6">
                                                    <div class="text-center">
                                                        <div class="h5 text-primary mb-0" id="avg-odds-${race.venue}-${race.race_number}">-</div>
                                                        <small class="text-muted">平均オッズ</small>
                                                    </div>
                                                </div>
                                                <div class="col-6">
                                                    <div class="text-center">
                                                        <div class="h5 text-success mb-0" id="max-odds-${race.venue}-${race.race_number}">-</div>
                                                        <small class="text-muted">最高オッズ</small>
                                                    </div>
                                                </div>
                                            </div>
                                            <div class="mt-2">
                                                <button class="btn btn-outline-info btn-sm w-100 fetch-odds-btn" data-date="${predictionDate}" data-venue="${race.venue}" data-race="${race.race_number}">
                                                    <i class="fas fa-sync-alt me-1"></i>オッズ更新
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="card border-warning">
                                        <div class="card-header bg-warning text-dark">
                                            <h6 class="mb-0">
                                                <i class="fas fa-chart-bar me-2"></i>投資判断サマリー
                                            </h6>
                                        </div>
                                        <div class="card-body">
                                            <div class="row">
                                                <div class="col-6">
                                                    <div class="text-center">
                                                        <div class="h5 text-success mb-0" id="best-return-${race.venue}-${race.race_number}">-</div>
                                                        <small class="text-muted">最高期待値</small>
                                                    </div>
                                                </div>
                                                <div class="col-6">
                                                    <div class="text-center">
                                                        <div class="h5 text-info mb-0" id="recommendation-${race.venue}-${race.race_number}">-</div>
                                                        <small class="text-muted">推奨レベル</small>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- 購入提案 -->
                        ${this.renderPurchaseSuggestions(race.purchase_suggestions, race)}
                        
                        <!-- オッズ詳細テーブル（非表示で初期化） -->
                        <div class="odds-detail-section mt-3 d-none" id="odds-detail-${race.venue}-${race.race_number}">
                            <div class="card">
                                <div class="card-header bg-secondary text-white">
                                    <h6 class="mb-0">
                                        <i class="fas fa-table me-2"></i>オッズ詳細
                                    </h6>
                                </div>
                                <div class="card-body p-0">
                                    <div class="odds-loading d-none text-center py-3">
                                        <div class="spinner-border text-info" role="status">
                                            <span class="visually-hidden">取得中...</span>
                                        </div>
                                        <p class="mt-2 text-muted">オッズ取得中...</p>
                                    </div>
                                    <div class="odds-error alert alert-danger d-none m-3" role="alert">
                                        <i class="fas fa-exclamation-triangle me-1"></i><span class="odds-error-text">オッズ取得に失敗しました</span>
                                    </div>
                                    <div class="odds-compare-table"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 組み合わせテーブルの描画
     */
    async renderCombinationsTable(combinations, venue, raceNumber) {
        const raceId = `${venue}-${raceNumber}`;
        // デフォルトソート状態
        if (!this.combinationSortStates[raceId]) {
            this.combinationSortStates[raceId] = { column: 'rank', order: 'asc' };
        }
        const { column, order } = this.combinationSortStates[raceId];
        
        // オッズデータを取得
        const predictionDate = this.filteredData?.prediction_date || this.filteredPastData?.prediction_date;
        const race = { venue, race_number: raceNumber, prediction_date: predictionDate };
        const oddsData = await this.getOddsDataForRace(race);
        
        // オッズマップを作成
        const oddsMap = {};
        if (oddsData && oddsData.odds_data) {
            oddsData.odds_data.forEach(row => {
                oddsMap[row.combination] = row.ratio;
            });
        } else if (oddsData && oddsData.combinations) {
            oddsData.combinations.forEach(row => {
                oddsMap[row.combination] = row.odds;
            });
        }
        
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
                case 'odds':
                    vA = oddsMap[a.combination] || 0; vB = oddsMap[b.combination] || 0; break;
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
                        <th class="sortable" data-col="odds">オッズ${icon('odds')}</th>
                    </tr>
                </thead>
                <tbody>
        `;
        sorted.forEach(combination => {
            const rankClass = this.getRankClass(combination.rank);
            const probabilityClass = this.getProbabilityClass(combination.probability);
            const expectedValueClass = this.getExpectedValueClass(combination.expected_value);
            const odds = oddsMap[combination.combination];
            const oddsClass = odds ? (odds >= 10 ? 'text-success' : odds >= 5 ? 'text-warning' : 'text-danger') : 'text-muted';
            
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
                    <td>
                        <span class="fw-bold ${oddsClass}">
                            ${odds ? `${odds.toFixed(1)}倍` : '-'}
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
     * 組み合わせテーブルを非同期でレンダリング
     */
    async renderCombinationsTableAsync(race) {
        try {
            const containerId = `combinations-table-${race.venue}-${race.race_number}`;
            const container = document.getElementById(containerId);
            
            if (!container) {
                console.error('renderCombinationsTableAsync: コンテナが見つかりません:', containerId);
                return;
            }

            console.log('renderCombinationsTableAsync: 開始', { venue: race.venue, race_number: race.race_number });
            
            // タイムアウト付きでレンダリングを実行
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('タイムアウト')), 15000); // 15秒タイムアウト
            });

            const tableCombos = (race.all_combinations || race.top_20_combinations || []).slice(0, 20);
            const renderPromise = this.renderCombinationsTable(tableCombos, race.venue, race.race_number);
            const html = await Promise.race([renderPromise, timeoutPromise]);
            
            container.innerHTML = html;
            
            console.log('renderCombinationsTableAsync: 完了', { venue: race.venue, race_number: race.race_number });
            
        } catch (error) {
            console.error('組み合わせテーブルのレンダリングに失敗:', error);
            const containerId = `combinations-table-${race.venue}-${race.race_number}`;
            const container = document.getElementById(containerId);
            if (container) {
                if (error.message === 'タイムアウト') {
                    container.innerHTML = `
                        <div class="alert alert-warning">
                            <i class="fas fa-clock me-2"></i>
                            組み合わせテーブルの読み込みがタイムアウトしました。ページを再読み込みしてください。
                        </div>
                    `;
                } else {
                    container.innerHTML = `
                        <div class="alert alert-danger">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            組み合わせテーブルの読み込みに失敗しました: ${error.message}
                        </div>
                    `;
                }
            }
        }
    }

    /**
     * レースのオッズ情報を取得して表示
     */
    async fetchOddsForRace(date, venue, race, button) {
        try {
            // ボタンを無効化してローディング表示
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>更新中...';
            
            // ローディング表示
            const sectionContent = button.closest('.section-content');
            const loadingEl = sectionContent.querySelector('.odds-loading');
            const errorEl = sectionContent.querySelector('.odds-error');
            const tableEl = sectionContent.querySelector('.odds-compare-table');
            const detailSection = document.getElementById(`odds-detail-${venue}-${race}`);
            
            loadingEl.classList.remove('d-none');
            errorEl.classList.add('d-none');
            
            // オッズデータを取得
            const raceInfo = { venue, race_number: parseInt(race), prediction_date: date };
            const oddsData = await this.getOddsDataForRace(raceInfo);
            
            if (!oddsData) {
                throw new Error('オッズデータが見つかりません');
            }
            
            // オッズサマリー情報を更新
            this.updateOddsSummary(venue, race, oddsData);
            
            // 投資判断サマリーを更新
            this.updateInvestmentSummary(venue, race);
            
            // オッズ詳細テーブルを表示
            const html = this.renderOddsCompareTable(oddsData, raceInfo);
            tableEl.innerHTML = html;
            detailSection.classList.remove('d-none');
            
            console.log('オッズ情報取得成功:', { venue, race, oddsData });
            
        } catch (error) {
            console.error('オッズ情報の取得に失敗:', error);
            
            // エラー表示
            const sectionContent = button.closest('.section-content');
            const errorEl = sectionContent.querySelector('.odds-error');
            const errorTextEl = sectionContent.querySelector('.odds-error-text');
            
            errorTextEl.textContent = error.message;
            errorEl.classList.remove('d-none');
            
        } finally {
            // ボタンを元に戻す
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-sync-alt me-1"></i>オッズ更新';
            
            // ローディング非表示
            const sectionContent = button.closest('.section-content');
            const loadingEl = sectionContent.querySelector('.odds-loading');
            loadingEl.classList.add('d-none');
        }
    }

    /**
     * オッズサマリー情報を更新
     */
    updateOddsSummary(venue, race, oddsData) {
        // オッズマップを作成
        const oddsMap = {};
        if (oddsData.odds_data) {
            oddsData.odds_data.forEach(row => {
                oddsMap[row.combination] = row.ratio;
            });
        } else if (oddsData.combinations) {
            oddsData.combinations.forEach(row => {
                oddsMap[row.combination] = row.odds;
            });
        }

        // 平均オッズと最高オッズを計算
        const oddsValues = Object.values(oddsMap);
        const averageOdds = oddsValues.length > 0 ? oddsValues.reduce((sum, odds) => sum + odds, 0) / oddsValues.length : 0;
        const maxOdds = oddsValues.length > 0 ? Math.max(...oddsValues) : 0;

        // DOM要素を更新
        const avgOddsEl = document.getElementById(`avg-odds-${venue}-${race}`);
        const maxOddsEl = document.getElementById(`max-odds-${venue}-${race}`);

        if (avgOddsEl) {
            avgOddsEl.textContent = averageOdds > 0 ? `${averageOdds.toFixed(1)}倍` : '-';
        }
        if (maxOddsEl) {
            maxOddsEl.textContent = maxOdds > 0 ? `${maxOdds.toFixed(1)}倍` : '-';
        }
    }

    /**
     * 投資判断サマリーを更新
     */
    updateInvestmentSummary(venue, raceNumber) {
        // レース情報を取得
        const raceId = `${venue}-${raceNumber}`;
        const race = this.findRaceById(raceId);
        
        if (!race || !race.purchase_suggestions || race.purchase_suggestions.length === 0) {
            return;
        }

        // 最高期待値と推奨レベルを計算
        const bestSuggestion = race.purchase_suggestions.reduce((best, current) => 
            current.expected_return > best.expected_return ? current : best
        );

        // DOM要素を更新
        const bestReturnEl = document.getElementById(`best-return-${venue}-${raceNumber}`);
        const recommendationEl = document.getElementById(`recommendation-${venue}-${raceNumber}`);

        if (bestReturnEl) {
            bestReturnEl.textContent = bestSuggestion.expected_return > 0 ? 
                `+${bestSuggestion.expected_return.toFixed(1)}` : 
                bestSuggestion.expected_return.toFixed(1);
        }

        if (recommendationEl) {
            // 簡易的な推奨レベル判定
            const returnValue = bestSuggestion.expected_return;
            let recommendation = '慎重';
            let className = 'text-warning';
            
            if (returnValue > 50) {
                recommendation = '強推奨';
                className = 'text-success';
            } else if (returnValue > 20) {
                recommendation = '推奨';
                className = 'text-info';
            } else if (returnValue > 0) {
                recommendation = '検討';
                className = 'text-primary';
            }

            recommendationEl.textContent = recommendation;
            recommendationEl.className = `h5 text-info mb-0 ${className}`;
        }
    }

    /**
     * 購入提案表示（Phase 3実装）
     */
    renderPurchaseSuggestions(suggestions, race) {
        if (!suggestions || suggestions.length === 0) {
            return '<div class="alert alert-info">購入提案はありません</div>';
        }

        // レース固有のコンテナIDを生成
        const containerId = `suggestions-container-${race.venue}-${race.race_number}`;
        
        // DOM更新後に非同期でレンダリングを実行（既に処理中の場合はスキップ）
        setTimeout(() => {
            // 既に処理済みの場合はスキップ
            const container = document.getElementById(containerId);
            if (container && !container.classList.contains('rendering')) {
                container.classList.add('rendering');
                this.renderSuggestionsAsync(suggestions, containerId, race);
            }
        }, 0);

        return `
            <div class="suggestions-comparison mb-4" id="${containerId}">
                <div class="text-center py-4">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">読み込み中...</span>
                    </div>
                    <p class="mt-2 text-muted">提案比較テーブルを読み込み中...</p>
                </div>
            </div>
        `;
    }

    /**
     * 提案比較テーブルを非同期でレンダリング
     */
    async renderSuggestionsAsync(suggestions, containerId, race) {
        console.log('renderSuggestionsAsync: 開始', { containerId, suggestionsCount: suggestions.length });
        
        try {
            const container = document.getElementById(containerId);
            if (!container) {
                console.error('renderSuggestionsAsync: コンテナが見つかりません:', containerId);
                return;
            }

            console.log('renderSuggestionsAsync: レンダリング開始');
            
            // タイムアウト付きでレンダリングを実行
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => reject(new Error('タイムアウト')), 10000); // 10秒タイムアウト
            });

            const renderPromise = this.renderSuggestionsComparisonTable(suggestions, race);
            console.log('renderSuggestionsAsync: renderSuggestionsComparisonTable呼び出し完了');
            
            const html = await Promise.race([renderPromise, timeoutPromise]);
            console.log('renderSuggestionsAsync: HTML生成完了');
            
            container.innerHTML = html;
            container.classList.remove('rendering');
            console.log('renderSuggestionsAsync: コンテナ更新完了');
            
            // イベントハンドラーを設定
            console.log('renderSuggestionsAsync: イベントハンドラー設定開始');
            this.setupSuggestionToggleHandlers();
            console.log('renderSuggestionsAsync: イベントハンドラー設定完了');
            
        } catch (error) {
            console.error('提案比較テーブルのレンダリングに失敗:', error);
            const container = document.getElementById(containerId);
            if (container) {
                container.classList.remove('rendering');
                if (error.message === 'タイムアウト') {
                    container.innerHTML = `
                        <div class="alert alert-warning">
                            <i class="fas fa-clock me-2"></i>
                            提案比較テーブルの読み込みがタイムアウトしました。ページを再読み込みしてください。
                        </div>
                    `;
                } else {
                    container.innerHTML = `
                        <div class="alert alert-danger">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            提案比較テーブルの読み込みに失敗しました: ${error.message}
                        </div>
                    `;
                }
            }
        }
    }

    /**
     * 提案比較テーブル表示
     */
    async renderSuggestionsComparisonTable(suggestions, race) {
        console.log('renderSuggestionsComparisonTable: 開始', { suggestionsCount: suggestions.length });
        
        // 期待値でソート
        const sortedSuggestions = [...suggestions].sort((a, b) => b.expected_return - a.expected_return);
        const bestSuggestion = sortedSuggestions[0];
        
        console.log('renderSuggestionsComparisonTable: ソート完了');

        let html = `
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h6 class="card-title mb-0">
                        <i class="fas fa-chart-bar me-2"></i>提案比較
                    </h6>
                </div>
                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-hover mb-0">
                            <thead class="table-light">
                                <tr>
                                    <th style="width: 30px;"></th>
                                    <th>提案タイプ</th>
                                    <th>説明</th>
                                    <th>組数</th>
                                    <th>合計確率</th>
                                    <th>購入金額</th>
                                    <th>期待リターン</th>
                                    <th>平均オッズ</th>
                                    <th>オッズ期待値</th>
                                    <th>投資判断</th>
                                    <th>リスクレベル</th>
                                    <th>評価</th>
                                </tr>
                            </thead>
                            <tbody>
        `;

        for (let index = 0; index < sortedSuggestions.length; index++) {
            console.log(`renderSuggestionsComparisonTable: 提案${index + 1}処理中`);
            
            const suggestion = sortedSuggestions[index];
            const isBest = suggestion === bestSuggestion;
            const riskLevel = this.calculateSuggestionRiskLevel(suggestion);
            const evaluation = this.evaluateSuggestion(suggestion);
            const suggestionId = `suggestion-${index}`;
            
                    // オッズ情報を取得
        console.log(`renderSuggestionsComparisonTable: 提案${index + 1}のオッズ情報を計算中...`);
        const oddsInfo = await this.calculateOddsInfo(suggestion);
        console.log(`renderSuggestionsComparisonTable: 提案${index + 1}のオッズ情報:`, oddsInfo);
            
            html += `
                <tr class="suggestion-row ${isBest ? 'table-success' : ''}" data-suggestion-id="${suggestionId}">
                    <td>
                        <button class="btn btn-sm btn-outline-primary suggestion-toggle" data-suggestion-id="${suggestionId}">
                            <i class="fas fa-chevron-down"></i>
                        </button>
                    </td>
                    <td>
                        <span class="badge ${this.getSuggestionTypeClass(suggestion.type)}">
                            ${this.getSuggestionTypeText(suggestion.type)}
                        </span>
                        ${isBest ? '<i class="fas fa-crown text-warning ms-1" title="最良提案"></i>' : ''}
                    </td>
                    <td>${suggestion.description}</td>
                    <td>
                        <span class="badge bg-secondary">${Math.round(suggestion.total_cost / 100)}組</span>
                    </td>
                    <td>
                        <div class="d-flex align-items-center">
                            <div class="progress flex-grow-1 me-2" style="height: 8px;">
                                <div class="progress-bar bg-info" 
                                     style="width: ${(suggestion.total_probability * 100).toFixed(1)}%"></div>
                            </div>
                            <small>${(suggestion.total_probability * 100).toFixed(1)}%</small>
                        </div>
                    </td>
                    <td>
                        <span class="fw-bold">¥${suggestion.total_cost.toLocaleString()}</span>
                    </td>
                    <td>
                        <span class="fw-bold ${this.getExpectedValueClass(suggestion.expected_return)}">
                            ${suggestion.expected_return > 0 ? '+' : ''}${suggestion.expected_return.toFixed(1)}
                        </span>
                    </td>
                    <td>
                        ${oddsInfo.available ? 
                            `<span class="fw-bold text-primary">${oddsInfo.averageOdds.toFixed(1)}倍</span>` : 
                            '<span class="text-muted">-</span>'
                        }
                    </td>
                    <td>
                        ${oddsInfo.available ? 
                            `<span class="fw-bold ${this.getExpectedValueClass(oddsInfo.oddsExpectedValue)}">
                                ${oddsInfo.oddsExpectedValue > 0 ? '+' : ''}${oddsInfo.oddsExpectedValue.toFixed(1)}
                            </span>` : 
                            '<span class="text-muted">-</span>'
                        }
                    </td>
                    <td>
                        ${oddsInfo.available && oddsInfo.investmentDecision ? 
                            `<span class="badge ${this.getInvestmentDecisionClass(oddsInfo.investmentDecision.recommendation)}">
                                <i class="fas ${this.getInvestmentDecisionIcon(oddsInfo.investmentDecision.recommendation)} me-1"></i>
                                ${oddsInfo.investmentDecision.recommendation}
                            </span>` : 
                            '<span class="text-muted">-</span>'
                        }
                    </td>
                    <td>
                        <span class="badge ${this.getRiskLevelClass(riskLevel)}">
                            ${this.getRiskLevelText(riskLevel)}
                        </span>
                    </td>
                    <td>
                        <span class="badge ${this.getEvaluationClass(evaluation)}">
                            ${this.getEvaluationText(evaluation)}
                        </span>
                    </td>
                </tr>
                <tr class="suggestion-detail-row" id="${suggestionId}-detail" style="display: none;">
                    <td colspan="12" class="p-0">
                        <div class="suggestion-detail-content p-3 bg-light border-top">
                            ${await this.renderSuggestionDetailContent(suggestion, race, oddsInfo)}
                        </div>
                    </td>
                </tr>
            `;
        }

        html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;

        console.log('renderSuggestionsComparisonTable: HTML生成完了');
        return html;
    }

    /**
     * 提案のオッズ情報を計算
     */
    async calculateOddsInfo(suggestion) {
        // 現在のレース情報を取得
        const currentRace = this.getCurrentRaceContext();
        console.log('calculateOddsInfo: 現在のレースコンテキスト:', currentRace);
        
        if (!currentRace) {
            console.warn('calculateOddsInfo: レースコンテキストが設定されていません');
            return { available: false, averageOdds: 0, oddsExpectedValue: 0 };
        }

        // オッズデータを取得
        const oddsData = await this.getOddsDataForRace(currentRace);
        console.log('calculateOddsInfo: オッズデータ取得結果:', oddsData ? '成功' : '失敗');
        
        if (!oddsData || !oddsData.combinations) {
            return { available: false, averageOdds: 0, oddsExpectedValue: 0 };
        }

        // オッズマップを作成
        const oddsMap = {};
        if (oddsData.odds_data) {
            // 新しい形式: odds_data配列
            oddsData.odds_data.forEach(row => {
                oddsMap[row.combination] = row.ratio;
            });
        } else if (oddsData.combinations) {
            // 古い形式: combinations配列
            oddsData.combinations.forEach(row => {
                oddsMap[row.combination] = row.odds;
            });
        }

        // 提案の組み合わせでオッズが利用可能なものを抽出
        const availableCombinations = suggestion.combinations.filter(combo => oddsMap[combo]);
        
        if (availableCombinations.length === 0) {
            return { available: false, averageOdds: 0, oddsExpectedValue: 0 };
        }

        // 平均オッズを計算
        const totalOdds = availableCombinations.reduce((sum, combo) => sum + oddsMap[combo], 0);
        const averageOdds = totalOdds / availableCombinations.length;

        // オッズ期待値を計算（確率 × オッズ）
        let oddsExpectedValue = 0;
        suggestion.combinations.forEach(combo => {
            if (oddsMap[combo]) {
                // 各組み合わせの確率を取得（簡易計算）
                const comboProbability = suggestion.total_probability / suggestion.combinations.length;
                oddsExpectedValue += comboProbability * oddsMap[combo];
            }
        });

        // 投資判断を計算
        const investmentDecision = this.calculateInvestmentDecision(suggestion, oddsExpectedValue, averageOdds);

        return {
            available: true,
            averageOdds: averageOdds,
            oddsExpectedValue: oddsExpectedValue,
            availableCount: availableCombinations.length,
            totalCount: suggestion.combinations.length,
            oddsMap: oddsMap,
            investmentDecision: investmentDecision
        };
    }

    /**
     * 現在のレースコンテキストを取得
     */
    getCurrentRaceContext() {
        return this.currentRaceContext;
    }

    /**
     * 現在のレースコンテキストを設定
     */
    setCurrentRaceContext(venue, raceNumber, predictionDate) {
        this.currentRaceContext = {
            venue: venue,
            race_number: raceNumber,
            prediction_date: predictionDate
        };
    }

    /**
     * レースのオッズデータを取得
     */
    async getOddsDataForRace(race) {
        if (!race) return null;

        const cacheKey = `${race.venue}-${race.race_number}-${race.prediction_date}`;
        console.log('getOddsDataForRace: レース情報:', race);
        console.log('getOddsDataForRace: キャッシュキー:', cacheKey);
        
        // キャッシュから取得
        if (this.oddsCache[cacheKey]) {
            console.log('getOddsDataForRace: キャッシュから取得');
            return this.oddsCache[cacheKey];
        }

        try {
            // タイムアウト付きでフェッチ
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 3000); // 3秒タイムアウト

            const url = `/kyotei_predictor/data/raw/odds_data_${race.prediction_date}_${race.venue}_R${race.race_number}.json`;
            console.log('getOddsDataForRace: フェッチURL:', url);

            const response = await fetch(url, { 
                signal: controller.signal 
            });
            clearTimeout(timeoutId);

            if (!response.ok) {
                console.log(`オッズデータが見つかりません: ${race.venue} R${race.race_number} (${response.status})`);
                return null;
            }

            const oddsData = await response.json();
            console.log('getOddsDataForRace: オッズデータ取得成功');
            
            // キャッシュに保存
            this.oddsCache[cacheKey] = oddsData;
            
            return oddsData;
        } catch (error) {
            if (error.name === 'AbortError') {
                console.warn(`オッズデータの取得がタイムアウトしました: ${race.venue} R${race.race_number}`);
            } else {
                console.error('オッズデータの取得に失敗:', error);
            }
            return null;
        }
    }

    /**
     * 提案詳細コンテンツ表示
     */
    async renderSuggestionDetailContent(suggestion, race, oddsInfo = null) {
        const riskLevel = this.calculateSuggestionRiskLevel(suggestion);
        const evaluation = this.evaluateSuggestion(suggestion);
        const expectedValueClass = this.getExpectedValueClass(suggestion.expected_return);
        const isProfitable = suggestion.expected_return > 0;

        return `
            <div class="row">
                <!-- 統計情報 -->
                <div class="col-md-4 mb-3">
                    <h6 class="mb-3">
                        <i class="fas fa-chart-pie me-2"></i>統計情報
                    </h6>
                    <div class="row">
                        <div class="col-6">
                            <div class="stat-card text-center p-2 bg-white rounded border">
                                <div class="stat-value text-primary fw-bold">${Math.round(suggestion.total_cost / 100)}</div>
                                <div class="stat-label small text-muted">購入組数</div>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="stat-card text-center p-2 bg-white rounded border">
                                <div class="stat-value text-info fw-bold">${(suggestion.total_probability * 100).toFixed(1)}%</div>
                                <div class="stat-label small text-muted">合計確率</div>
                            </div>
                        </div>
                    </div>
                    <div class="row mt-2">
                        <div class="col-6">
                            <div class="stat-card text-center p-2 bg-white rounded border">
                                <div class="stat-value text-secondary fw-bold">¥${suggestion.total_cost.toLocaleString()}</div>
                                <div class="stat-label small text-muted">購入金額</div>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="stat-card text-center p-2 bg-white rounded border">
                                <div class="stat-value ${expectedValueClass} fw-bold">
                                    ${suggestion.expected_return > 0 ? '+' : ''}${suggestion.expected_return.toFixed(1)}
                                </div>
                                <div class="stat-label small text-muted">期待リターン</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- オッズ情報 -->
                <div class="col-md-4 mb-3">
                    <h6 class="mb-3">
                        <i class="fas fa-coins me-2"></i>オッズ情報
                    </h6>
                    ${oddsInfo && oddsInfo.available ? `
                        <div class="odds-info p-3 bg-white rounded border">
                            <div class="row">
                                <div class="col-6">
                                    <div class="stat-card text-center p-2 bg-light rounded">
                                        <div class="stat-value text-primary fw-bold">${oddsInfo.averageOdds.toFixed(1)}倍</div>
                                        <div class="stat-label small text-muted">平均オッズ</div>
                                    </div>
                                </div>
                                <div class="col-6">
                                    <div class="stat-card text-center p-2 bg-light rounded">
                                        <div class="stat-value ${this.getExpectedValueClass(oddsInfo.oddsExpectedValue)} fw-bold">
                                            ${oddsInfo.oddsExpectedValue > 0 ? '+' : ''}${oddsInfo.oddsExpectedValue.toFixed(1)}
                                        </div>
                                        <div class="stat-label small text-muted">オッズ期待値</div>
                                    </div>
                                </div>
                            </div>
                            <div class="mt-2">
                                <small class="text-muted">
                                    利用可能: ${oddsInfo.availableCount}/${oddsInfo.totalCount}組
                                </small>
                            </div>
                        </div>
                    ` : `
                        <div class="odds-info p-3 bg-light rounded border">
                            <div class="text-center text-muted">
                                <i class="fas fa-exclamation-triangle me-2"></i>
                                オッズ情報が利用できません
                            </div>
                        </div>
                    `}
                </div>

                <!-- 投資判断 -->
                <div class="col-md-4 mb-3">
                    <h6 class="mb-3">
                        <i class="fas fa-lightbulb me-2"></i>投資判断
                    </h6>
                    ${oddsInfo && oddsInfo.available && oddsInfo.investmentDecision ? `
                        <div class="investment-decision p-3 bg-white rounded border">
                            <div class="d-flex align-items-center mb-2">
                                <span class="badge ${this.getInvestmentDecisionClass(oddsInfo.investmentDecision.recommendation)} me-2">
                                    <i class="fas ${this.getInvestmentDecisionIcon(oddsInfo.investmentDecision.recommendation)} me-1"></i>
                                    ${oddsInfo.investmentDecision.recommendation}
                                </span>
                            </div>
                            <div class="mb-2">
                                <small class="text-muted">
                                    <strong>判断理由:</strong>
                                </small>
                                <ul class="list-unstyled small mt-1">
                                    ${oddsInfo.investmentDecision.reasoning.map(reason => 
                                        `<li><i class="fas fa-check text-success me-1"></i>${reason}</li>`
                                    ).join('')}
                                </ul>
                            </div>
                            <div>
                                <small class="text-muted">
                                    <strong>リスクレベル:</strong> 
                                    <span class="badge ${this.getRiskLevelClass(oddsInfo.investmentDecision.riskLevel)}">
                                        ${this.getRiskLevelText(oddsInfo.investmentDecision.riskLevel)}
                                    </span>
                                </small>
                            </div>
                        </div>
                    ` : `
                        <div class="investment-advice p-3 bg-white rounded border">
                            <div class="d-flex align-items-center mb-2">
                                <i class="fas ${isProfitable ? 'fa-thumbs-up text-success' : 'fa-exclamation-triangle text-warning'} me-2"></i>
                                <span class="fw-bold">
                                    ${isProfitable ? '推奨' : '注意が必要'}
                                </span>
                            </div>
                            <small class="text-muted">
                                ${this.getInvestmentAdvice(suggestion)}
                            </small>
                        </div>
                    `}
                </div>
            </div>

            <!-- 組み合わせリスト -->
            <div class="mb-3">
                <h6 class="mb-2">
                    <i class="fas fa-list me-2"></i>組み合わせ一覧
                    <span class="badge bg-secondary ms-2">${Math.round(suggestion.total_cost / 100)}組</span>
                </h6>
                <div class="combinations-grid bg-white p-3 rounded border" style="max-height: 200px; overflow-y: auto;">
                    ${suggestion.combinations.map(combo => 
                        `<span class="combination-badge badge bg-light text-dark me-1 mb-1">${combo}</span>`
                    ).join('')}
                </div>
            </div>

            <!-- 確率バー -->
            <div class="mb-3">
                <h6 class="mb-2">
                    <i class="fas fa-percentage me-2"></i>的中確率
                </h6>
                <div class="bg-white p-3 rounded border">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <small class="text-muted">的中確率</small>
                        <small class="text-muted fw-bold">${(suggestion.total_probability * 100).toFixed(1)}%</small>
                    </div>
                    <div class="progress" style="height: 15px;">
                        <div class="progress-bar bg-info" 
                             style="width: ${(suggestion.total_probability * 100).toFixed(1)}%"
                             title="${(suggestion.total_probability * 100).toFixed(1)}%"></div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 組み合わせのオッズを取得
     */
    getOddsForCombination(combination, oddsInfo) {
        // 実際の実装では、オッズデータから該当する組み合わせのオッズを取得
        // ここでは簡易的な実装として、平均オッズを返す
        return oddsInfo.averageOdds;
    }

    /**
     * 個別提案カード表示
     */
    renderSuggestionCard(suggestion, index) {
        const riskLevel = this.calculateSuggestionRiskLevel(suggestion);
        const evaluation = this.evaluateSuggestion(suggestion);
        const expectedValueClass = this.getExpectedValueClass(suggestion.expected_return);
        const isProfitable = suggestion.expected_return > 0;

        return `
            <div class="card suggestion-card mb-3 ${isProfitable ? 'border-success' : 'border-warning'}">
                <div class="card-header d-flex justify-content-between align-items-center ${isProfitable ? 'bg-success' : 'bg-warning'} text-white">
                    <div class="d-flex align-items-center">
                        <span class="badge ${this.getSuggestionTypeClass(suggestion.type)} me-2">
                            ${this.getSuggestionTypeText(suggestion.type)}
                        </span>
                        <h6 class="card-title mb-0">${suggestion.description}</h6>
                    </div>
                    <div class="d-flex align-items-center">
                        <span class="badge ${this.getRiskLevelClass(riskLevel)} me-2">
                            ${this.getRiskLevelText(riskLevel)}
                        </span>
                        <span class="badge ${this.getEvaluationClass(evaluation)}">
                            ${this.getEvaluationText(evaluation)}
                        </span>
                    </div>
                </div>
                
                <div class="card-body">
                    <!-- 統計情報 -->
                    <div class="row mb-3">
                        <div class="col-md-3">
                            <div class="stat-card text-center p-2 bg-light rounded">
                                <div class="stat-value text-primary fw-bold">${Math.round(suggestion.total_cost / 100)}</div>
                                <div class="stat-label small text-muted">購入組数</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="stat-card text-center p-2 bg-light rounded">
                                <div class="stat-value text-info fw-bold">${(suggestion.total_probability * 100).toFixed(1)}%</div>
                                <div class="stat-label small text-muted">合計確率</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="stat-card text-center p-2 bg-light rounded">
                                <div class="stat-value text-secondary fw-bold">¥${suggestion.total_cost.toLocaleString()}</div>
                                <div class="stat-label small text-muted">購入金額</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="stat-card text-center p-2 bg-light rounded">
                                <div class="stat-value ${expectedValueClass} fw-bold">
                                    ${suggestion.expected_return > 0 ? '+' : ''}${suggestion.expected_return.toFixed(1)}
                                </div>
                                <div class="stat-label small text-muted">期待リターン</div>
                            </div>
                        </div>
                    </div>

                    <!-- 確率バー -->
                    <div class="mb-3">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <small class="text-muted">的中確率</small>
                            <small class="text-muted">${(suggestion.total_probability * 100).toFixed(1)}%</small>
                        </div>
                        <div class="progress" style="height: 12px;">
                            <div class="progress-bar bg-info" 
                                 style="width: ${(suggestion.total_probability * 100).toFixed(1)}%"
                                 title="${(suggestion.total_probability * 100).toFixed(1)}%"></div>
                        </div>
                    </div>

                    <!-- 組み合わせリスト -->
                    <div class="mb-3">
                        <h6 class="mb-2">
                            <i class="fas fa-list me-1"></i>組み合わせ一覧
                            <small class="text-muted">（全${Math.round(suggestion.total_cost / 100)}組）</small>
                        </h6>
                        <div class="combinations-grid">
                            ${suggestion.combinations.map(combo => 
                                `<span class="combination-badge">${combo}</span>`
                            ).join('')}
                        </div>
                    </div>

                    <!-- 投資判断 -->
                    <div class="investment-advice p-3 bg-light rounded">
                        <h6 class="mb-2">
                            <i class="fas fa-lightbulb me-1"></i>投資判断
                        </h6>
                        <div class="d-flex align-items-center">
                            <i class="fas ${isProfitable ? 'fa-thumbs-up text-success' : 'fa-exclamation-triangle text-warning'} me-2"></i>
                            <span class="fw-bold">
                                ${isProfitable ? '推奨' : '注意が必要'}
                            </span>
                        </div>
                        <small class="text-muted">
                            ${this.getInvestmentAdvice(suggestion)}
                        </small>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 提案のリスクレベル計算
     */
    calculateSuggestionRiskLevel(suggestion) {
        const probability = suggestion.total_probability;
        const cost = suggestion.total_cost;
        const expectedReturn = suggestion.expected_return;
        
        // 確率が低い場合は高リスク
        if (probability < 0.3) return 'HIGH';
        
        // 期待値がマイナスの場合は中リスク以上
        if (expectedReturn < 0) return 'MEDIUM';
        
        // 購入金額が高い場合はリスク上昇
        if (cost > 1000) return 'MEDIUM';
        
        return 'LOW';
    }

    /**
     * 提案の評価
     */
    evaluateSuggestion(suggestion) {
        const probability = suggestion.total_probability;
        const expectedReturn = suggestion.expected_return;
        const cost = suggestion.total_cost;
        
        // 期待値が高い場合は優秀
        if (expectedReturn > 50) return 'EXCELLENT';
        
        // 確率が高く期待値がプラス
        if (probability > 0.7 && expectedReturn > 0) return 'GOOD';
        
        // 期待値がプラス
        if (expectedReturn > 0) return 'FAIR';
        
        // 期待値がマイナス
        return 'POOR';
    }

    /**
     * 投資判断メッセージ生成
     */
    getInvestmentAdvice(suggestion) {
        const probability = suggestion.total_probability;
        const expectedReturn = suggestion.expected_return;
        const cost = suggestion.total_cost;
        
        if (expectedReturn > 50) {
            return '期待値が非常に高く、積極的な投資を推奨します。';
        } else if (expectedReturn > 0 && probability > 0.5) {
            return '期待値がプラスで確率も高く、比較的安全な投資です。';
        } else if (expectedReturn > 0) {
            return '期待値はプラスですが、確率が低いため慎重に判断してください。';
        } else {
            return '期待値がマイナスのため、投資は推奨しません。';
        }
    }

    /**
     * オッズと比較した投資判断を計算
     */
    calculateInvestmentDecision(suggestion, oddsExpectedValue, averageOdds) {
        const predictionExpectedValue = suggestion.expected_return;
        const totalCost = suggestion.total_cost;
        
        // オッズ期待値と予測期待値の比較
        const oddsVsPrediction = oddsExpectedValue - predictionExpectedValue;
        
        // 投資判断の基準
        const decision = {
            overall: 'NEUTRAL', // OVERALL, GOOD, NEUTRAL, POOR
            oddsComparison: 'NEUTRAL', // BETTER, SIMILAR, WORSE
            recommendation: '',
            reasoning: [],
            riskLevel: 'MEDIUM'
        };

        // 1. 予測期待値の評価
        if (predictionExpectedValue > totalCost * 0.15) {
            decision.overall = 'OVERALL';
            decision.reasoning.push('予測期待値が購入金額の15%を超える高収益');
        } else if (predictionExpectedValue > totalCost * 0.08) {
            decision.overall = 'GOOD';
            decision.reasoning.push('予測期待値が購入金額の8%を超える良好な収益');
        } else if (predictionExpectedValue > 0) {
            decision.overall = 'NEUTRAL';
            decision.reasoning.push('予測期待値はプラスだが低収益');
        } else {
            decision.overall = 'POOR';
            decision.reasoning.push('予測期待値がマイナス');
        }

        // 2. オッズ期待値との比較
        if (oddsExpectedValue > 0) {
            if (oddsExpectedValue > predictionExpectedValue * 1.2) {
                decision.oddsComparison = 'BETTER';
                decision.reasoning.push('オッズ期待値が予測期待値を20%上回る');
            } else if (oddsExpectedValue > predictionExpectedValue * 0.8) {
                decision.oddsComparison = 'SIMILAR';
                decision.reasoning.push('オッズ期待値と予測期待値が類似');
            } else {
                decision.oddsComparison = 'WORSE';
                decision.reasoning.push('オッズ期待値が予測期待値を20%下回る');
            }
        }

        // 3. 平均オッズの評価
        if (averageOdds > 50) {
            decision.reasoning.push('平均オッズが50倍を超える高配当');
        } else if (averageOdds > 20) {
            decision.reasoning.push('平均オッズが20倍を超える良好な配当');
        } else if (averageOdds < 5) {
            decision.reasoning.push('平均オッズが5倍未満の低配当');
        }

        // 4. 最終推奨度の決定
        if (decision.overall === 'OVERALL' && decision.oddsComparison === 'BETTER') {
            decision.recommendation = '強く推奨';
            decision.riskLevel = 'LOW';
        } else if (decision.overall === 'GOOD' && decision.oddsComparison !== 'WORSE') {
            decision.recommendation = '推奨';
            decision.riskLevel = 'LOW';
        } else if (decision.overall === 'NEUTRAL' && decision.oddsComparison === 'BETTER') {
            decision.recommendation = '検討';
            decision.riskLevel = 'MEDIUM';
        } else if (decision.overall === 'POOR' || decision.oddsComparison === 'WORSE') {
            decision.recommendation = '非推奨';
            decision.riskLevel = 'HIGH';
        } else {
            decision.recommendation = '慎重に検討';
            decision.riskLevel = 'MEDIUM';
        }

        return decision;
    }

    /**
     * 投資判断の表示クラスを取得
     */
    getInvestmentDecisionClass(decision) {
        const classMap = {
            '強く推奨': 'bg-success text-white',
            '推奨': 'bg-info text-white',
            '検討': 'bg-warning text-dark',
            '慎重に検討': 'bg-secondary text-white',
            '非推奨': 'bg-danger text-white'
        };
        return classMap[decision] || 'bg-secondary text-white';
    }

    /**
     * 投資判断のアイコンを取得
     */
    getInvestmentDecisionIcon(decision) {
        const iconMap = {
            '強く推奨': 'fa-thumbs-up',
            '推奨': 'fa-check-circle',
            '検討': 'fa-question-circle',
            '慎重に検討': 'fa-exclamation-triangle',
            '非推奨': 'fa-times-circle'
        };
        return iconMap[decision] || 'fa-info-circle';
    }

    /**
     * 順位クラスの取得
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
        if (probability >= 0.7) return 'probability-high';
        if (probability >= 0.4) return 'probability-medium';
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
            'nagashi': 'nagashi',
            'single': 'single',
            'formation': 'formation',
            'complex_wheel': 'complex-wheel',
            'advanced_formation': 'advanced-formation'
        };
        return typeMap[type] || 'secondary';
    }

    /**
     * 提案タイプテキストの取得
     */
    getSuggestionTypeText(type) {
        const typeMap = {
            'wheel': '流し',
            'box': 'ボックス',
            'nagashi': '流し',
            'single': '単勝',
            'formation': 'フォーメーション',
            'complex_wheel': '複雑流し',
            'advanced_formation': '高度フォーメーション'
        };
        return typeMap[type] || 'その他';
    }

    /**
     * リスククラスの取得（既存コード用）
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
     * リスクテキストの取得（既存コード用）
     */
    getRiskText(riskLevel) {
        const riskMap = {
            'LOW': '低リスク',
            'MEDIUM': '中リスク',
            'HIGH': '高リスク'
        };
        return riskMap[riskLevel] || '不明';
    }

    /**
     * リスクレベルクラス取得（Phase 3用）
     */
    getRiskLevelClass(riskLevel) {
        const riskMap = {
            'LOW': 'bg-success',
            'MEDIUM': 'bg-warning',
            'HIGH': 'bg-danger'
        };
        return riskMap[riskLevel] || 'bg-secondary';
    }

    /**
     * リスクレベルテキスト取得（Phase 3用）
     */
    getRiskLevelText(riskLevel) {
        const riskMap = {
            'LOW': '低リスク',
            'MEDIUM': '中リスク',
            'HIGH': '高リスク'
        };
        return riskMap[riskLevel] || '不明';
    }

    /**
     * 評価クラス取得
     */
    getEvaluationClass(evaluation) {
        const evalMap = {
            'EXCELLENT': 'bg-success',
            'GOOD': 'bg-info',
            'FAIR': 'bg-warning',
            'POOR': 'bg-danger'
        };
        return evalMap[evaluation] || 'bg-secondary';
    }

    /**
     * 評価テキスト取得
     */
    getEvaluationText(evaluation) {
        const evalMap = {
            'EXCELLENT': '優秀',
            'GOOD': '良好',
            'FAIR': '普通',
            'POOR': '不良'
        };
        return evalMap[evaluation] || '不明';
    }

    /**
     * オッズ比較テーブルの描画
     */
    renderOddsCompareTable(oddsData, race = null) {
        // race: 予測データの all_combinations または top_20_combinations を含むオブジェクト
        const raceCombos = race && (race.all_combinations || race.top_20_combinations || []).slice(0, 20);
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
        if (race && raceCombos && raceCombos.length) {
            raceCombos.forEach(row => {
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
                        const combos = (race.all_combinations || race.top_20_combinations || []).slice(0, 20);
                        tableContainer.innerHTML = this.renderCombinationsTable(combos, race.venue, race.race_number);
                    }
                }
            };
        });
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
        
        // セクションヘッダーのクリックイベント設定
        const sectionHeaders = document.querySelectorAll('#venues-section .section-header');
        console.log('setupRaceHeaders: セクションヘッダー数:', sectionHeaders.length);
        
        sectionHeaders.forEach((sectionHeader, index) => {
            console.log(`setupRaceHeaders: セクションヘッダー${index + 1}を設定:`, sectionHeader);
            sectionHeader.addEventListener('click', (e) => {
                e.stopPropagation(); // イベントの伝播を停止
                console.log('セクションヘッダーがクリックされました:', sectionHeader);
                
                const raceId = sectionHeader.dataset.raceId;
                const section = sectionHeader.dataset.section;
                const sectionContent = document.querySelector(`#section-${raceId}-${section} .section-content`);
                const toggleIcon = sectionHeader.querySelector('.section-toggle');
                
                console.log('セクション情報:', { raceId, section, sectionContent, toggleIcon });
                
                if (!sectionContent) {
                    console.error('セクションコンテンツが見つかりません:', `#section-${raceId}-${section} .section-content`);
                    return;
                }
                
                if (sectionContent.classList.contains('show')) {
                    sectionContent.classList.remove('show');
                    toggleIcon.classList.remove('fa-chevron-up');
                    toggleIcon.classList.add('fa-chevron-down');
                    console.log('セクションを折り畳みました');
                    console.log('CSSクラス確認:', sectionContent.className);
                    console.log('display スタイル確認:', window.getComputedStyle(sectionContent).display);
                } else {
                    sectionContent.classList.add('show');
                    toggleIcon.classList.remove('fa-chevron-down');
                    toggleIcon.classList.add('fa-chevron-up');
                    console.log('セクションを展開しました');
                    console.log('CSSクラス確認:', sectionContent.className);
                    console.log('display スタイル確認:', window.getComputedStyle(sectionContent).display);
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
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 取得中...';
                
                try {
                    const response = await fetch(`/kyotei_predictor/data/raw/odds_data_${date}_${venue}_R${raceNo}.json`);
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    const oddsData = await response.json();
                    
                    // テーブル更新
                    table.innerHTML = this.renderOddsCompareTable(oddsData, this.findRaceById(`${venue}-${raceNo}`));
                    table.classList.remove('d-none');
                    
                } catch (error) {
                    console.error('オッズデータの取得に失敗:', error);
                    errorText.textContent = `オッズデータの取得に失敗しました: ${error.message}`;
                    error.classList.remove('d-none');
                } finally {
                    loading.classList.add('d-none');
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fas fa-download"></i> オッズ取得';
                }
            });
        });
        
        // 組み合わせテーブルのソート機能設定
        document.querySelectorAll('#venues-section .combinations-table').forEach(table => {
            const raceId = table.getAttribute('data-race-id');
            this.setupCombinationSortHandlers(raceId);
        });
    }

    /**
     * 提案比較テーブルの展開/折りたたみ機能設定
     */
    setupSuggestionToggleHandlers() {
        const buttons = document.querySelectorAll('.suggestion-toggle');
        console.log('setupSuggestionToggleHandlers: ボタン数:', buttons.length);
        
        buttons.forEach((button, index) => {
            console.log(`setupSuggestionToggleHandlers: ボタン${index + 1}を設定:`, button);
            
            // 既存のイベントリスナーを削除
            button.removeEventListener('click', button._toggleHandler);
            
            // 新しいイベントハンドラーを作成
            button._toggleHandler = (e) => {
                e.stopPropagation(); // イベントの伝播を停止
                console.log('提案トグルボタンがクリックされました:', button);
                
                const suggestionId = button.getAttribute('data-suggestion-id');
                const detailRow = document.getElementById(`${suggestionId}-detail`);
                const icon = button.querySelector('i');
                
                console.log('提案トグル情報:', { suggestionId, detailRow, icon });
                
                if (!detailRow) {
                    console.error('提案詳細行が見つかりません:', suggestionId);
                    return;
                }
                
                const isHidden = detailRow.style.display === 'none' || detailRow.style.display === '';
                console.log('現在の表示状態:', detailRow.style.display, 'isHidden:', isHidden);
                
                if (isHidden) {
                    // 展開
                    console.log('提案詳細を展開します');
                    detailRow.style.display = 'table-row';
                    detailRow.style.visibility = 'visible';
                    detailRow.style.opacity = '1';
                    icon.classList.remove('fa-chevron-down');
                    icon.classList.add('fa-chevron-up');
                    button.classList.remove('btn-outline-primary');
                    button.classList.add('btn-primary');
                } else {
                    // 折りたたみ
                    console.log('提案詳細を折りたたみます');
                    detailRow.style.display = 'none';
                    detailRow.style.visibility = 'visible';
                    detailRow.style.opacity = '1';
                    icon.classList.remove('fa-chevron-up');
                    icon.classList.add('fa-chevron-down');
                    button.classList.remove('btn-primary');
                    button.classList.add('btn-outline-primary');
                }
                
                console.log('変更後の表示状態:', detailRow.style.display);
            };
            
            // イベントリスナーを追加
            button.addEventListener('click', button._toggleHandler);
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
        
        // 過去分セクションヘッダーのクリックイベント設定
        const pastSectionHeaders = document.querySelectorAll('#past-venues-section .section-header');
        console.log('setupPastRaceHeaders: 過去分セクションヘッダー数:', pastSectionHeaders.length);
        
        pastSectionHeaders.forEach((sectionHeader, index) => {
            console.log(`setupPastRaceHeaders: 過去分セクションヘッダー${index + 1}を設定:`, sectionHeader);
            sectionHeader.addEventListener('click', (e) => {
                e.stopPropagation(); // イベントの伝播を停止
                console.log('過去分セクションヘッダーがクリックされました:', sectionHeader);
                
                const raceId = sectionHeader.dataset.raceId;
                const section = sectionHeader.dataset.section;
                const sectionContent = document.querySelector(`#section-${raceId}-${section} .section-content`);
                const toggleIcon = sectionHeader.querySelector('.section-toggle');
                
                console.log('過去分セクション情報:', { raceId, section, sectionContent, toggleIcon });
                
                if (!sectionContent) {
                    console.error('過去分セクションコンテンツが見つかりません:', `#section-${raceId}-${section} .section-content`);
                    return;
                }
                
                if (sectionContent.classList.contains('show')) {
                    sectionContent.classList.remove('show');
                    toggleIcon.classList.remove('fa-chevron-up');
                    toggleIcon.classList.add('fa-chevron-down');
                    console.log('過去分セクションを折り畳みました');
                } else {
                    sectionContent.classList.add('show');
                    toggleIcon.classList.remove('fa-chevron-down');
                    toggleIcon.classList.add('fa-chevron-up');
                    console.log('過去分セクションを展開しました');
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
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 取得中...';
                
                try {
                    const response = await fetch(`/kyotei_predictor/data/raw/odds_data_${date}_${venue}_R${raceNo}.json`);
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    const oddsData = await response.json();
                    
                    // テーブル更新
                    table.innerHTML = this.renderOddsCompareTable(oddsData, this.pastData.predictions.find(p => p.prediction_date === date && p.venue === venue && p.race_number === parseInt(raceNo)));
                    table.classList.remove('d-none');
                    
                } catch (error) {
                    console.error('オッズデータの取得に失敗:', error);
                    errorText.textContent = `オッズデータの取得に失敗しました: ${error.message}`;
                    error.classList.remove('d-none');
                } finally {
                    loading.classList.add('d-none');
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fas fa-download"></i> オッズ取得';
                }
            });
        });
        
        // 組み合わせテーブルのソート機能設定
        document.querySelectorAll('#past-venues-section .combinations-table').forEach(table => {
            const raceId = table.getAttribute('data-race-id');
            this.setupCombinationSortHandlers(raceId);
        });
    }
} 