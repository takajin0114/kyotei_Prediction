#!/usr/bin/env python3
"""
予想ツール - 3連単予測・購入方法提案機能

機能:
1. レース前データ取得
2. 3連単予測実行（上位20組）
3. 購入方法の提案生成
4. JSON形式での結果保存
5. Web表示用データ生成

使用方法:
    python -m kyotei_predictor.tools.prediction_tool --predict-date 2024-07-12
    python -m kyotei_predictor.tools.prediction_tool --predict-date 2024-07-12 --venues KIRYU,TODA
"""

import os
import sys
import json
import argparse
import logging
import numpy as np
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from itertools import permutations
import torch
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import cast

from kyotei_predictor.utils.common import KyoteiUtils

# Windows: UTF-8 環境変数のみ設定（stdout の detach は logging と競合するため行わない）
if sys.platform.startswith('win'):
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    os.environ.setdefault('PYTHONLEGACYWINDOWSSTDIO', 'utf-8')

# 可視化結果の表示を無効化
import matplotlib
matplotlib.use('Agg')  # 非表示バックエンドを使用
import matplotlib.pyplot as plt
plt.ioff()  # インタラクティブモードを無効化

# プロット表示を完全に無効化
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')
warnings.filterwarnings('ignore', category=RuntimeWarning, module='matplotlib')

# プロジェクトルートの設定
from kyotei_predictor.config.settings import Settings

PROJECT_ROOT = Settings.PROJECT_ROOT
sys.path.append(str(PROJECT_ROOT))

from stable_baselines3 import PPO
from kyotei_predictor.pipelines.kyotei_env import action_to_trifecta, vectorize_race_state
from kyotei_predictor.pipelines.state_vector import build_race_state_vector, get_state_dim
from kyotei_predictor.data.race_db import RaceDB
from metaboatrace.models.stadium import StadiumTelCode
from kyotei_predictor.tools.fetch.race_data_fetcher import fetch_race_entry_data, fetch_pre_race_data
from kyotei_predictor.tools.fetch.odds_fetcher import fetch_trifecta_odds
from metaboatrace.scrapers.official.website.v1707.pages.monthly_schedule_page.location import create_monthly_schedule_page_url
from metaboatrace.scrapers.official.website.v1707.pages.monthly_schedule_page.scraping import extract_events
import requests
from io import StringIO

try:
    from kyotei_predictor.utils.betting_selector import select_bets
    from kyotei_predictor.config.improvement_config_manager import ImprovementConfigManager
    _BETTING_AVAILABLE = True
except ImportError:
    _BETTING_AVAILABLE = False

class PredictionTool:
    """予想ツールのメインクラス"""
    
    def __init__(
        self,
        log_level=logging.INFO,
        data_dir: Optional[Union[str, Path]] = None,
        model_path: Optional[Union[str, Path]] = None,
        data_source: str = "db",
        db_path: Optional[Union[str, Path]] = None,
    ):
        self.setup_logging(log_level)
        self.model: Optional[PPO] = None
        self.model_info = {}
        self.utils = KyoteiUtils()  # 共通ユーティリティを初期化
        self.data_dir: Optional[Path] = Path(data_dir) if data_dir else None
        self.default_model_path: Optional[Path] = Path(model_path) if model_path else None
        self.data_source = data_source
        self._db: Optional[RaceDB] = None
        if data_source == "db":
            path = db_path or (PROJECT_ROOT / "kyotei_predictor" / "data" / "kyotei_races.sqlite")
            self._db = RaceDB(str(path))
        
    def setup_logging(self, log_level):
        """ログ設定（Windows ではファイルのみ。コンソールは safe_print で出力）"""
        log_file = PROJECT_ROOT / "kyotei_predictor" / "logs" / f"prediction_tool_{datetime.now().strftime('%Y%m%d')}.log"
        log_file.parent.mkdir(exist_ok=True)
        handlers = [logging.FileHandler(str(log_file), encoding='utf-8')]
        # Windows で StreamHandler(sys.stdout) を使うと "raw stream has been detached" が出るため、ファイルのみにする
        if not sys.platform.startswith('win'):
            handlers.append(logging.StreamHandler(sys.stdout))
        from kyotei_predictor.utils.logger import get_logging_format, get_logging_datefmt
        logging.basicConfig(
            level=log_level,
            format=get_logging_format(),
            datefmt=get_logging_datefmt(),
            handlers=handlers,
        )
        self.logger = logging.getLogger(__name__)
    
    def load_model(self, model_path: Optional[Union[str, Path]] = None) -> bool:
        """学習済みモデルの読み込み（引数 > インスタンスの default_model_path > デフォルトパス）"""
        try:
            path_to_use = model_path or (str(self.default_model_path) if self.default_model_path else None)
            if not path_to_use:
                # デフォルトで最新のベストモデルを使用
                model_dir = PROJECT_ROOT / "optuna_models" / "graduated_reward_best"
                model_path_obj = model_dir / "best_model.zip"
                
                if not model_path_obj.exists():
                    # フォールバック: 最新のチェックポイント
                    checkpoint_dir = PROJECT_ROOT / "optuna_models" / "graduated_reward_checkpoints"
                    if checkpoint_dir.exists():
                        checkpoints = list(checkpoint_dir.glob("*.zip"))
                        if checkpoints:
                            model_path_obj = max(checkpoints, key=lambda x: x.stat().st_mtime)
            else:
                model_path_obj = Path(path_to_use)
            
            if not model_path_obj.exists():
                self.logger.error(f"モデルファイルが見つかりません: {model_path_obj}")
                return False
            
            self.logger.info(f"モデルを読み込み中: {model_path_obj}")
            self.model = PPO.load(str(model_path_obj))
            
            # モデル情報を記録
            self.model_info = {
                'model_path': str(model_path_obj),
                'model_name': model_path_obj.stem,
                'version': datetime.fromtimestamp(model_path_obj.stat().st_mtime).strftime('%Y-%m-%d'),
                'training_data_until': self.get_training_data_date()
            }
            
            self.logger.info("モデルの読み込みが完了しました")
            return True
            
        except Exception as e:
            self.logger.error(f"モデル読み込みエラー: {e}")
            return False
    
    def get_training_data_date(self) -> str:
        """学習データの最終日を推定"""
        # 実際の実装では、学習時に使用したデータの最終日を記録する
        # ここでは簡易的に前日を返す
        yesterday = datetime.now() - timedelta(days=1)
        return yesterday.strftime('%Y-%m-%d')
    
    def get_all_stadiums(self) -> List[StadiumTelCode]:
        """全24会場のStadiumTelCodeを返す"""
        return [
            StadiumTelCode.KIRYU,      # 01: 桐生
            StadiumTelCode.TODA,       # 02: 戸田
            StadiumTelCode.EDOGAWA,    # 03: 江戸川
            StadiumTelCode.HEIWAJIMA,  # 04: 平和島
            StadiumTelCode.TAMAGAWA,   # 05: 多摩川
            StadiumTelCode.HAMANAKO,   # 06: 浜名湖
            StadiumTelCode.GAMAGORI,   # 07: 蒲郡
            StadiumTelCode.TOKONAME,   # 08: 常滑
            StadiumTelCode.TSU,        # 09: 津
            StadiumTelCode.MIKUNI,     # 10: 三国
            StadiumTelCode.BIWAKO,     # 11: びわこ
            StadiumTelCode.SUMINOE,    # 12: 住之江
            StadiumTelCode.AMAGASAKI,  # 13: 尼崎
            StadiumTelCode.NARUTO,     # 14: 鳴門
            StadiumTelCode.MARUGAME,   # 15: 丸亀
            StadiumTelCode.KOJIMA,     # 16: 児島
            StadiumTelCode.MIYAJIMA,   # 17: 宮島
            StadiumTelCode.TOKUYAMA,   # 18: 徳山
            StadiumTelCode.SHIMONOSEKI, # 19: 下関
            StadiumTelCode.WAKAMATSU,  # 20: 若松
            StadiumTelCode.ASHIYA,     # 21: 芦屋
            StadiumTelCode.FUKUOKA,    # 22: 福岡
            StadiumTelCode.KARATSU,    # 23: 唐津
            StadiumTelCode.OMURA,      # 24: 大村
        ]
    
    def get_event_days_for_stadium(self, stadium: StadiumTelCode, target_date: date) -> List[date]:
        """指定会場の指定日の開催日を取得"""
        try:
            url = create_monthly_schedule_page_url(target_date.year, target_date.month)
            resp = requests.get(url)
            resp.raise_for_status()
            events = extract_events(StringIO(resp.text))
            
            event_days = []
            for event in events:
                if event.stadium_tel_code == stadium:
                    for d in range(event.days):
                        day = event.starts_on + timedelta(days=d)
                        if day == target_date:
                            event_days.append(day)
            
            return event_days
        except Exception as e:
            self.logger.warning(f"{stadium.name} {target_date} 開催日確認失敗: {e}")
            return []
    
    def fetch_today_race_schedule(self, target_date: Optional[str] = None, venues: Optional[List[str]] = None) -> Dict[str, List[int]]:
        """当日のレーススケジュールを取得（venues指定時はその会場のみ）"""
        if not target_date:
            target_date = datetime.now().strftime('%Y-%m-%d')
        
        target_date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
        self.logger.info(f"レーススケジュール取得開始: {target_date}")
        
        all_stadiums = self.get_all_stadiums()
        if venues:
            self.logger.info(f'venues引数: {venues}')
            stadiums = [s for s in all_stadiums if s.name in venues]
            self.logger.info(f'抽出stadiums: {[s.name for s in stadiums]}')
        else:
            stadiums = all_stadiums
        schedule = {}
        
        for stadium in stadiums:
            event_days = self.get_event_days_for_stadium(stadium, target_date_obj)
            if event_days:
                # 開催日がある場合は1-12Rを想定
                schedule[stadium.name] = list(range(1, 13))
                self.logger.info(f"{stadium.name}: 開催日あり (1-12R)")
            else:
                schedule[stadium.name] = []
                self.logger.info(f"{stadium.name}: 開催日なし")
            time.sleep(0.5)  # レート制限
        
        self.logger.info(f"レーススケジュール取得完了: {len([s for s in schedule.values() if s])}会場で開催")
        return schedule
    
    def fetch_today_race_entries(self, target_date: Optional[str] = None, venues: Optional[List[str]] = None) -> Dict[str, Dict]:
        """当日の選手情報を取得"""
        if not target_date:
            target_date = datetime.now().strftime('%Y-%m-%d')
        
        self.logger.info(f"選手情報取得開始: {target_date}")
        
        # レーススケジュールを取得
        schedule = self.fetch_today_race_schedule(target_date, venues)
        
        # 指定された会場のみフィルタ
        if venues:
            schedule = {k: v for k, v in schedule.items() if k in venues}
        
        target_date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
        entries = {}
        
        # 並列処理で選手情報を取得
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            
            for stadium_name, race_numbers in schedule.items():
                if not race_numbers:
                    continue
                
                stadium = next((s for s in self.get_all_stadiums() if s.name == stadium_name), None)
                if not stadium:
                    continue
                
                for race_no in race_numbers:
                    future = executor.submit(
                        self._fetch_single_race_entry,
                        target_date_obj, stadium, race_no
                    )
                    futures.append((f"{stadium_name}_{race_no}", future))
            
            # 結果を収集
            for race_key, future in futures:
                try:
                    result = future.result()
                    if result:
                        entries[race_key] = result
                        self.logger.info(f"選手情報取得成功: {race_key}")
                    else:
                        self.logger.warning(f"選手情報取得失敗: {race_key}")
                except Exception as e:
                    self.logger.error(f"選手情報取得エラー {race_key}: {e}")
        
        self.logger.info(f"選手情報取得完了: {len(entries)}レース")
        return entries
    
    def _fetch_single_race_entry(self, target_date: date, stadium: StadiumTelCode, race_no: int) -> Optional[Dict]:
        """単一レースのレース前データを取得（出走表＋直前情報。展示走後なら直前情報も含む）"""
        try:
            pre_race_data = fetch_pre_race_data(target_date, stadium, race_no)
            if pre_race_data:
                return pre_race_data
            else:
                self.logger.warning(f"レース前データ取得失敗: {stadium.name} R{race_no}")
                return None
        except Exception as e:
            self.logger.error(f"レース前データ取得エラー {stadium.name} R{race_no}: {e}")
            return None
    
    def fetch_today_odds(self, target_date: Optional[str] = None, venues: Optional[List[str]] = None) -> Dict[str, Dict]:
        """当日のオッズ情報を取得"""
        if not target_date:
            target_date = datetime.now().strftime('%Y-%m-%d')
        
        self.logger.info(f"オッズ情報取得開始: {target_date}")
        
        # レーススケジュールを取得
        schedule = self.fetch_today_race_schedule(target_date, venues)
        
        # 指定された会場のみフィルタ
        if venues:
            schedule = {k: v for k, v in schedule.items() if k in venues}
        
        target_date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
        odds = {}
        
        # 並列処理でオッズ情報を取得
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            
            for stadium_name, race_numbers in schedule.items():
                if not race_numbers:
                    continue
                
                stadium = next((s for s in self.get_all_stadiums() if s.name == stadium_name), None)
                if not stadium:
                    continue
                
                for race_no in race_numbers:
                    future = executor.submit(
                        self._fetch_single_race_odds,
                        target_date_obj, stadium, race_no
                    )
                    futures.append((f"{stadium_name}_{race_no}", future))
            
            # 結果を収集
            for race_key, future in futures:
                try:
                    result = future.result()
                    if result:
                        odds[race_key] = result
                        self.logger.info(f"オッズ情報取得成功: {race_key}")
                    else:
                        self.logger.warning(f"オッズ情報取得失敗: {race_key}")
                except Exception as e:
                    self.logger.error(f"オッズ情報取得エラー {race_key}: {e}")
        
        self.logger.info(f"オッズ情報取得完了: {len(odds)}レース")
        return odds
    
    def _fetch_single_race_odds(self, target_date: date, stadium: StadiumTelCode, race_no: int) -> Optional[Dict]:
        """単一レースのオッズ情報を取得"""
        try:
            odds_data = fetch_trifecta_odds(target_date, stadium, race_no)
            if odds_data:
                return odds_data
            else:
                self.logger.warning(f"オッズ情報取得失敗: {stadium.name} R{race_no}")
                return None
        except Exception as e:
            self.logger.error(f"オッズ情報取得エラー {stadium.name} R{race_no}: {e}")
            return None
    
    def get_race_data_paths(self, predict_date: str, venues: Optional[List[str]] = None) -> List[Tuple[str, str, Optional[str], Optional[str]]]:
        """予測対象のレースデータパスを取得。data_source=db のときは (venue, race_number, None, None) を返す。"""
        if self.data_source == "db" and self._db is not None:
            pairs = self._db.get_race_odds_pairs(date_from=predict_date, date_to=predict_date)
            if venues:
                venue_set = {v.upper() for v in venues}
                pairs = [p for p in pairs if p[1] in venue_set]
            race_paths = [(p[1], str(p[2]), None, None) for p in pairs]
            self.logger.info(f"予測対象レース数(DB): {len(race_paths)}")
            return race_paths

        if self.data_dir is not None:
            d = Path(self.data_dir)
            if not d.is_absolute():
                d = PROJECT_ROOT / d
            if d.exists():
                race_data_dir = d
            else:
                race_data_dir = PROJECT_ROOT / "kyotei_predictor" / "data" / "raw"
        else:
            race_data_dir = PROJECT_ROOT / "kyotei_predictor" / "data" / "raw"
        
        race_paths = []
        
        # 指定された会場または全会場
        if not venues:
            venues = ["KIRYU", "TODA", "EDOGAWA", "KORAKUEN", "HEIWAJIMA", "KAWASAKI", 
                     "FUNEBASHI", "KASAMATSU", "HAMANAKO", "MIKUNIHARA", "TOKONAME", 
                     "GAMAGORI", "TAMANO", "MIHARA", "YAMAGUCHI", "WAKAYAMA", 
                     "AMAGASAKI", "NARUTO", "MARUGAME", "KOCHI", "TOKUSHIMA", 
                     "IMABARI", "OGATA", "MIYAZAKI"]
        
        for venue in venues:
            # レースデータファイルを検索
            race_pattern = f"race_data_{predict_date}_{venue}_R*.json"
            odds_pattern = f"odds_data_{predict_date}_{venue}_R*.json"
            
            race_files = list(race_data_dir.glob(race_pattern))
            odds_files = list(race_data_dir.glob(odds_pattern))
            
            # レース番号でマッチング
            for race_file in race_files:
                # ファイル名からレース番号を抽出
                filename = race_file.name
                if "_R" in filename:
                    race_number = filename.split("_R")[-1].replace(".json", "")
                    
                    # 対応するオッズファイルを検索
                    odds_file = race_data_dir / f"odds_data_{predict_date}_{venue}_R{race_number}.json"
                    
                    if odds_file.exists():
                        race_paths.append((venue, race_number, str(race_file), str(odds_file)))
        
        self.logger.info(f"予測対象レース数: {len(race_paths)}")
        return race_paths
    
    def predict_trifecta_probabilities(self, race_data_path: str, odds_data_path: str) -> List[Dict]:
        """3連単の予測確率を計算（120通り全て）・ファイルパス版"""
        try:
            state = vectorize_race_state(race_data_path, odds_data_path)
            state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
            action_probs = self.model.policy.get_distribution(state_tensor).distribution.probs.detach().cpu().numpy()[0]
            trifecta_list = list(permutations(range(1, 7), 3))
            odds_data = None
            if odds_data_path and Path(odds_data_path).exists():
                try:
                    with open(odds_data_path, "r", encoding="utf-8") as f:
                        odds_data = json.load(f)
                except Exception:
                    odds_data = None
            probability_combinations = []
            for i, prob in enumerate(action_probs):
                trifecta = trifecta_list[i]
                combination_str = f"{trifecta[0]}-{trifecta[1]}-{trifecta[2]}"
                ratio = self._get_ratio_from_odds_data(odds_data, trifecta)
                probability_combinations.append({
                    "combination": combination_str,
                    "probability": float(prob),
                    "expected_value": self.calculate_expected_value(trifecta, odds_data_path),
                    "ratio": ratio,
                    "rank": 0,
                })
            probability_combinations.sort(key=lambda x: x["probability"], reverse=True)
            for i, item in enumerate(probability_combinations):
                item["rank"] = i + 1
            return probability_combinations
        except Exception as e:
            self.logger.error(f"予測エラー: {e}")
            return []

    def predict_trifecta_probabilities_from_data(self, race_data: Dict, odds_data: Dict) -> List[Dict]:
        """3連単の予測確率を計算（120通り全て）・辞書版（DB取得データ用）"""
        try:
            state = build_race_state_vector(race_data, None)
            state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
            action_probs = self.model.policy.get_distribution(state_tensor).distribution.probs.detach().cpu().numpy()[0]
            trifecta_list = list(permutations(range(1, 7), 3))
            probability_combinations = []
            for i, prob in enumerate(action_probs):
                trifecta = trifecta_list[i]
                combination_str = f"{trifecta[0]}-{trifecta[1]}-{trifecta[2]}"
                ratio = self._get_ratio_from_odds_data(odds_data, trifecta)
                probability_combinations.append({
                    "combination": combination_str,
                    "probability": float(prob),
                    "expected_value": self.calculate_expected_value_from_data(trifecta, odds_data),
                    "ratio": ratio,
                    "rank": 0,
                })
            probability_combinations.sort(key=lambda x: x["probability"], reverse=True)
            for i, item in enumerate(probability_combinations):
                item["rank"] = i + 1
            return probability_combinations
        except Exception as e:
            self.logger.error(f"予測エラー(辞書): {e}")
            return []
    
    def _get_ratio_from_odds_data(self, odds_data: Optional[Dict], trifecta: Tuple[int, int, int]) -> Optional[float]:
        """
        オッズ辞書から指定 3連単の倍率を取得。betting_numbers または combination に対応。
        EV 戦略（betting_selector）で使用。オッズなし時は None。
        """
        if not odds_data:
            return None
        for o in odds_data.get("odds_data") or []:
            if tuple(o.get("betting_numbers", [])) == trifecta:
                r = o.get("ratio")
                return float(r) if r is not None else None
            if o.get("combination") == f"{trifecta[0]}-{trifecta[1]}-{trifecta[2]}":
                r = o.get("ratio")
                return float(r) if r is not None else None
        return None

    def calculate_expected_value(self, trifecta: Tuple[int, int, int], odds_data_path: str) -> float:
        """期待値を計算（従来互換: 簡易式）。EV 戦略は betting_selector で確率×オッズ-1 を使用。"""
        try:
            with open(odds_data_path, 'r', encoding='utf-8') as f:
                odds_data = json.load(f)
            ratio = self._get_ratio_from_odds_data(odds_data, trifecta)
            if ratio is None:
                return 0.0
            return ratio * 0.05 - 1  # 仮の確率0.05を使用（従来互換）
        except Exception as e:
            self.logger.warning(f"期待値計算エラー: {e}")
            return 0.0
    
    def generate_formation_suggestions(self, combinations: List[Dict]) -> List[Dict]:
        """フォーメーション買いの提案（例: 1着:1,2 2着:2,3 3着:3,4,5）"""
        suggestions = []
        # 例として、1着:1,2 2着:2,3 3着:3,4,5 のパターンを作る
        first_candidates = [1, 2]
        second_candidates = [2, 3]
        third_candidates = [3, 4, 5]
        formation_combos = []
        for first in first_candidates:
            for second in second_candidates:
                if second == first:
                    continue
                for third in third_candidates:
                    if third == first or third == second:
                        continue
                    formation_combos.append(f"{first}-{second}-{third}")
        # 上位20組に含まれるものだけ抽出
        formation_prob_combinations = [c for c in combinations if c['combination'] in formation_combos]
        if len(formation_prob_combinations) >= 1:
            total_prob = sum(c['probability'] for c in formation_prob_combinations)
            total_cost = 100 * len(formation_combos)
            expected_return = total_prob * 1000  # 仮の計算
            suggestions.append({
                'type': 'formation',
                'description': '1着:1,2 2着:2,3 3着:3,4,5 フォーメーション',
                'combinations': formation_combos,  # 全組み合わせを表示
                'total_probability': total_prob,
                'total_cost': total_cost,
                'expected_return': expected_return
            })
        return suggestions

    def generate_complex_wheel_suggestions(self, combinations: List[Dict]) -> List[Dict]:
        """複雑な流しパターンの提案（1位固定-2位流し-3位固定など）"""
        suggestions = []
        
        # パターン1: 1位固定-2位流し-3位固定
        for first in range(1, 7):
            for third in range(1, 7):
                if third == first:
                    continue
                # 2位の候補（1位と3位以外）
                second_candidates = [i for i in range(1, 7) if i != first and i != third]
                if len(second_candidates) >= 2:  # 最低2つ以上の候補がある場合のみ
                    complex_wheel_combos = []
                    for second in second_candidates:
                        complex_wheel_combos.append(f"{first}-{second}-{third}")
                    
                    # 上位20組に含まれるものだけ抽出
                    complex_wheel_prob_combinations = [c for c in combinations if c['combination'] in complex_wheel_combos]
                    if len(complex_wheel_prob_combinations) >= 2:
                        total_prob = sum(c['probability'] for c in complex_wheel_prob_combinations)
                        total_cost = 100 * len(complex_wheel_combos)
                        expected_return = total_prob * 1000
                        suggestions.append({
                            'type': 'complex_wheel',
                            'description': f"{first}-流し-{third}",
                            'combinations': complex_wheel_combos,  # 全組み合わせを表示
                            'total_probability': total_prob,
                            'total_cost': total_cost,
                            'expected_return': expected_return
                        })
        
        # パターン2: 1位流し-2位固定-3位流し
        for second in range(1, 7):
            # 1位の候補（2位以外）
            first_candidates = [i for i in range(1, 7) if i != second]
            # 3位の候補（1位と2位以外）
            third_candidates = [i for i in range(1, 7) if i != second]
            
            if len(first_candidates) >= 2 and len(third_candidates) >= 2:
                complex_wheel_combos = []
                for first in first_candidates:
                    for third in third_candidates:
                        if third != first:
                            complex_wheel_combos.append(f"{first}-{second}-{third}")
                
                # 上位20組に含まれるものだけ抽出
                complex_wheel_prob_combinations = [c for c in combinations if c['combination'] in complex_wheel_combos]
                if len(complex_wheel_prob_combinations) >= 3:
                    total_prob = sum(c['probability'] for c in complex_wheel_prob_combinations)
                    total_cost = 100 * len(complex_wheel_combos)
                    expected_return = total_prob * 1000
                    suggestions.append({
                        'type': 'complex_wheel',
                        'description': f"流し-{second}-流し",
                        'combinations': complex_wheel_combos,  # 全組み合わせを表示
                        'total_probability': total_prob,
                        'total_cost': total_cost,
                        'expected_return': expected_return
                    })
        
        return suggestions

    def generate_advanced_formation_suggestions(self, combinations: List[Dict]) -> List[Dict]:
        """高度なフォーメーション買いの提案"""
        suggestions = []
        
        # パターン1: 1着:1,2,3 2着:2,3,4 3着:4,5,6
        formation_patterns = [
            {
                'name': '1着:1,2,3 2着:2,3,4 3着:4,5,6 フォーメーション',
                'first': [1, 2, 3],
                'second': [2, 3, 4],
                'third': [4, 5, 6]
            },
            {
                'name': '1着:1,2 2着:3,4 3着:5,6 フォーメーション',
                'first': [1, 2],
                'second': [3, 4],
                'third': [5, 6]
            },
            {
                'name': '1着:1 2着:2,3,4 3着:5,6 フォーメーション',
                'first': [1],
                'second': [2, 3, 4],
                'third': [5, 6]
            }
        ]
        
        for pattern in formation_patterns:
            formation_combos = []
            for first in pattern['first']:
                for second in pattern['second']:
                    if second == first:
                        continue
                    for third in pattern['third']:
                        if third == first or third == second:
                            continue
                        formation_combos.append(f"{first}-{second}-{third}")
            
            # 上位20組に含まれるものだけ抽出
            formation_prob_combinations = [c for c in combinations if c['combination'] in formation_combos]
            if len(formation_prob_combinations) >= 2:
                total_prob = sum(c['probability'] for c in formation_prob_combinations)
                total_cost = 100 * len(formation_combos)
                expected_return = total_prob * 1000
                suggestions.append({
                    'type': 'advanced_formation',
                    'description': pattern['name'],
                    'combinations': formation_combos,  # 全組み合わせを表示
                    'total_probability': total_prob,
                    'total_cost': total_cost,
                    'expected_return': expected_return
                })
        
        return suggestions

    def generate_purchase_suggestions(self, top_20_combinations: List[Dict]) -> List[Dict]:
        """購入方法の提案を生成（フォーメーションも含む）"""
        suggestions = []
        # 1. 流し買い（Nagashi）の提案
        nagashi_suggestions = self.generate_nagashi_suggestions(top_20_combinations)
        suggestions.extend(nagashi_suggestions)
        # 2. 流し買い（Wheel）の提案
        wheel_suggestions = self.generate_wheel_suggestions(top_20_combinations)
        suggestions.extend(wheel_suggestions)
        # 3. ボックス買いの提案
        box_suggestions = self.generate_box_suggestions(top_20_combinations)
        suggestions.extend(box_suggestions)
        # 4. フォーメーションの提案
        formation_suggestions = self.generate_formation_suggestions(top_20_combinations)
        suggestions.extend(formation_suggestions)
        # 5. 複雑な流しパターンの提案
        complex_wheel_suggestions = self.generate_complex_wheel_suggestions(top_20_combinations)
        suggestions.extend(complex_wheel_suggestions)
        # 6. 高度なフォーメーションの提案
        advanced_formation_suggestions = self.generate_advanced_formation_suggestions(top_20_combinations)
        suggestions.extend(advanced_formation_suggestions)
        # 期待値でソート
        suggestions.sort(key=lambda x: x['expected_return'], reverse=True)
        return suggestions[:8]  # 上位8件を返す（パターンが増えたため）
    
    def generate_box_suggestions(self, combinations: List[Dict]) -> List[Dict]:
        """ボックス買いの提案（3艇ボックスを重複なく一意に）"""
        suggestions = []
        seen_boxes = set()
        # 上位20組から3艇ボックス候補を抽出
        for combo in combinations:
            first, second, third = map(int, combo['combination'].split('-'))
            box = tuple(sorted([first, second, third]))
            if box in seen_boxes:
                continue
            seen_boxes.add(box)
            # 3艇ボックスの全順列
            box_combinations = [f"{a}-{b}-{c}" for a, b, c in permutations(box, 3)]
            # 上位20組に含まれるものだけ抽出
            box_prob_combinations = [c for c in combinations if c['combination'] in box_combinations]
            if len(box_prob_combinations) >= 3:
                total_prob = sum(c['probability'] for c in box_prob_combinations)
                total_cost = 100 * len(box_combinations)  # 6通り=600円
                expected_return = total_prob * 1000  # 仮の計算
                suggestions.append({
                    'type': 'box',
                    'description': f"{'-'.join(map(str, box))} ボックス",
                    'combinations': box_combinations,  # 全組み合わせを表示
                    'total_probability': total_prob,
                    'total_cost': total_cost,
                    'expected_return': expected_return
                })
        return suggestions

    def generate_wheel_suggestions(self, combinations: List[Dict]) -> List[Dict]:
        """1着固定で2,3着流し（全120通りから正しい組数を抽出）"""
        suggestions = []
        for first in range(1, 7):
            wheel_combos = []
            for second in range(1, 7):
                if second == first:
                    continue
                for third in range(1, 7):
                    if third == first or third == second:
                        continue
                    wheel_combos.append(f"{first}-{second}-{third}")
            # 上位20組に含まれるものだけ抽出
            wheel_prob_combinations = [c for c in combinations if c['combination'] in wheel_combos]
            if len(wheel_prob_combinations) >= 3:
                total_prob = sum(c['probability'] for c in wheel_prob_combinations)
                total_cost = 100 * len(wheel_combos)  # 20通り=2000円
                expected_return = total_prob * 1000  # 仮の計算
                suggestions.append({
                    'type': 'wheel',
                    'description': f"{first}-流し",
                    'combinations': wheel_combos,  # 全組み合わせを表示
                    'total_probability': total_prob,
                    'total_cost': total_cost,
                    'expected_return': expected_return
                })
        return suggestions

    def generate_nagashi_suggestions(self, combinations: List[Dict]) -> List[Dict]:
        """1-2着固定で3着流し（全120通りから正しい組数を抽出）"""
        suggestions = []
        for first in range(1, 7):
            for second in range(1, 7):
                if second == first:
                    continue
                nagashi_combos = []
                for third in range(1, 7):
                    if third == first or third == second:
                        continue
                    nagashi_combos.append(f"{first}-{second}-{third}")
                # 上位20組に含まれるものだけ抽出
                nagashi_prob_combinations = [c for c in combinations if c['combination'] in nagashi_combos]
                if len(nagashi_prob_combinations) >= 3:
                    total_prob = sum(c['probability'] for c in nagashi_prob_combinations)
                    total_cost = 100 * len(nagashi_combos)  # 4通り=400円
                    expected_return = total_prob * 1000  # 仮の計算
                    suggestions.append({
                        'type': 'nagashi',
                        'description': f"{first}-{second}-流し",
                        'combinations': nagashi_combos,  # 全組み合わせを表示
                        'total_probability': total_prob,
                        'total_cost': total_cost,
                        'expected_return': expected_return
                    })
        return suggestions
    
    def predict_races(
        self,
        predict_date: str,
        venues: Optional[List[str]] = None,
        include_selected_bets: bool = False,
    ) -> Optional[Dict]:
        """全会場・全レースの予測を実行。include_selected_bets=True で設定に基づく買い目選定を追加。"""
        try:
            self.logger.info(f"予測開始: {predict_date}")
            start_time = datetime.now()
            
            # モデル読み込み
            if not self.load_model():
                return None
            
            # レースデータパスを取得
            race_paths = self.get_race_data_paths(predict_date, venues)
            
            if not race_paths:
                self.logger.warning(f"予測対象のレースデータが見つかりません: {predict_date}")
                return None
            
            # 各レースの予測を実行
            predictions = []
            successful_predictions = 0
            
            for venue, race_number, race_path, odds_path in race_paths:
                try:
                    self.logger.info(f"予測中: {venue} {race_number}")

                    if race_path is None and odds_path is None and self._db is not None:
                        # DB から取得
                        race_data = self._db.get_race_json(predict_date, venue, int(race_number))
                        odds_data = self._db.get_odds_json(predict_date, venue, int(race_number))
                        if not race_data or not odds_data:
                            self.logger.warning(f"DB にレースデータなし: {predict_date} {venue} R{race_number}")
                            continue
                        all_combinations = self.predict_trifecta_probabilities_from_data(race_data, odds_data)
                        race_info = race_data.get("race_info", {})
                    else:
                        all_combinations = self.predict_trifecta_probabilities(race_path, odds_path)
                        with open(race_path, "r", encoding="utf-8") as f:
                            race_data = json.load(f)
                        race_info = race_data.get("race_info", {})

                    if all_combinations:
                        race_time = race_info.get("race_time", "09:00")
                        prediction = {
                            "venue": venue,
                            "venue_code": self.get_venue_code(venue),
                            "race_number": int(race_number),
                            "race_time": race_time,
                            "all_combinations": all_combinations,
                        }
                        if include_selected_bets and _BETTING_AVAILABLE:
                            try:
                                cfg = ImprovementConfigManager()
                                prediction["selected_bets"] = select_bets(
                                    all_combinations,
                                    strategy=cfg.get_betting_strategy(),
                                    top_n=cfg.get_betting_top_n(),
                                    score_threshold=cfg.get_betting_score_threshold(),
                                    ev_threshold=cfg.get_betting_ev_threshold(),
                                )
                            except Exception as e:
                                self.logger.debug("selected_bets skipped: %s", e)
                        predictions.append(prediction)
                        successful_predictions += 1

                except Exception as e:
                    self.logger.error(f"レース予測エラー {venue} {race_number}: {e}")
            
            # 会場別サマリー
            venue_summaries = self.generate_venue_summaries(predictions)
            
            # 実行結果
            execution_time = (datetime.now() - start_time).total_seconds() / 60
            
            result = {
                'prediction_date': predict_date,
                'generated_at': datetime.now().isoformat(),
                'model_info': self.model_info,
                'execution_summary': {
                    'total_venues': len(set(p['venue'] for p in predictions)),
                    'total_races': len(predictions),
                    'successful_predictions': successful_predictions,
                    'execution_time_minutes': execution_time
                },
                'predictions': predictions,
                'venue_summaries': venue_summaries
            }
            
            self.logger.info(f"予測完了: {successful_predictions}レース, {execution_time:.1f}分")
            return result
            
        except Exception as e:
            self.logger.error(f"予測実行エラー: {e}")
            return None
    
    def get_venue_code(self, venue: str) -> str:
        """会場コードを取得"""
        venue_codes = {
            'KIRYU': '01', 'TODA': '02', 'EDOGAWA': '03', 'KORAKUEN': '04',
            'HEIWAJIMA': '05', 'KAWASAKI': '06', 'FUNEBASHI': '07', 'KASAMATSU': '08',
            'HAMANAKO': '09', 'MIKUNIHARA': '10', 'TOKONAME': '11', 'GAMAGORI': '12',
            'TAMANO': '13', 'MIHARA': '14', 'YAMAGUCHI': '15', 'WAKAYAMA': '16',
            'AMAGASAKI': '17', 'NARUTO': '18', 'MARUGAME': '19', 'KOCHI': '20',
            'TOKUSHIMA': '21', 'IMABARI': '22', 'OGATA': '23', 'MIYAZAKI': '24'
        }
        return venue_codes.get(venue, '00')
    
    def calculate_risk_level(self, total_probability: float) -> str:
        """リスクレベルを計算"""
        if total_probability >= 0.8:
            return 'low'
        elif total_probability >= 0.6:
            return 'medium'
        else:
            return 'high'
    
    def generate_venue_summaries(self, predictions: List[Dict]) -> List[Dict]:
        """会場別サマリーを生成"""
        venue_stats = {}
        
        for pred in predictions:
            venue = pred['venue']
            if venue not in venue_stats:
                venue_stats[venue] = {
                    'total_races': 0,
                    'high_confidence_races': 0,
                    'total_probability': 0,
                    'total_expected_value': 0
                }
            
            ac = pred.get("all_combinations") or []
            venue_stats[venue]["total_races"] += 1
            sum_top20 = sum(c["probability"] for c in ac[:20]) if ac else 0
            venue_stats[venue]["total_probability"] += sum_top20
            top_prob = ac[0]["probability"] if ac else 0
            if top_prob >= 0.08:
                venue_stats[venue]["high_confidence_races"] += 1
            avg_expected_value = sum(c["expected_value"] for c in ac[:5]) / 5 if len(ac) >= 5 else (sum(c["expected_value"] for c in ac) / len(ac) if ac else 0)
            venue_stats[venue]["total_expected_value"] += avg_expected_value
        
        # サマリーを生成
        summaries = []
        for venue, stats in venue_stats.items():
            summaries.append({
                'venue': venue,
                'total_races': stats['total_races'],
                'high_confidence_races': stats['high_confidence_races'],
                'average_top_probability': stats['total_probability'] / stats['total_races'],
                'average_expected_value': stats['total_expected_value'] / stats['total_races']
            })
        
        return summaries
    
    def save_prediction_result(self, result: Dict, output_dir: Optional[Union[str, Path]] = None) -> Optional[str]:
        """予測結果をJSONファイルに保存"""
        try:
            if output_dir is None:
                output_dir = PROJECT_ROOT / "outputs"
            else:
                output_dir = Path(output_dir)
            output_dir.mkdir(exist_ok=True)
            
            # 日付別ファイル
            date_str = result['prediction_date'].replace('-', '')
            filename = f"predictions_{result['prediction_date']}.json"
            filepath = output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            # 最新ファイルへのシンボリックリンク（Windowsではコピー）
            latest_file = output_dir / "predictions_latest.json"
            if latest_file.exists():
                latest_file.unlink()
            
            # Windowsではシンボリックリンクの代わりにコピー
            import shutil
            shutil.copy2(filepath, latest_file)
            
            self.logger.info(f"予測結果を保存しました: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"予測結果保存エラー: {e}")
            return None

    def run_complete_prediction(
        self,
        target_date: Optional[str] = None,
        venues: Optional[List[str]] = None,
        fetch_data: bool = True,
        prediction_only: bool = False,
        include_selected_bets: bool = False,
    ) -> Optional[Dict]:
        """完全統合予測フロー。include_selected_bets=True で設定に基づく買い目選定を追加。"""
        start_time = datetime.now()
        
        # target_dateの処理を統一
        if not target_date:
            target_date = datetime.now().strftime('%Y-%m-%d')
        
        self.logger.info(f"完全統合予測フロー開始: {target_date}")
        self.logger.info(f"指定会場: {venues}")
        
        try:
            # 1. 当日レーススケジュール取得
            if fetch_data:
                self.logger.info("=== ステップ1: レーススケジュール取得 ===")
                schedule = self.fetch_today_race_schedule(target_date, venues)
                if not any(schedule.values()):
                    self.logger.warning("開催予定の会場がありません")
                    return None
            else:
                self.logger.info("データ取得をスキップします")
                schedule = {}
            
            # 2. 当日選手情報取得
            if fetch_data:
                self.logger.info("=== ステップ2: 選手情報取得 ===")
                entries = self.fetch_today_race_entries(target_date, venues)
                if not entries:
                    self.logger.warning("選手情報が取得できませんでした")
                    return None
            else:
                entries = {}
            
            # 3. 当日オッズ情報取得
            if fetch_data:
                self.logger.info("=== ステップ3: オッズ情報取得 ===")
                odds = self.fetch_today_odds(target_date, venues)
                if not odds:
                    self.logger.warning("オッズ情報が取得できませんでした。オッズなしで予測を継続します")
                    odds = {}
            else:
                odds = {}
            
            # 4. 3連単予測実行
            self.logger.info("=== ステップ4: 3連単予測実行 ===")
            if not self.load_model():
                self.logger.error("モデルの読み込みに失敗しました")
                return None
            
            predictions = []
            successful_predictions = 0
            odds_available_predictions = 0
            
            # 予測対象のレースを決定
            if prediction_only:
                # 予測のみの場合は既存データを使用（DB または data_dir）
                race_paths = self.get_race_data_paths(target_date, venues)
                for venue, race_number, race_path, odds_path in race_paths:
                    try:
                        self.logger.info(f"予測中: {venue} {race_number}")
                        if race_path is None and odds_path is None and self._db is not None:
                            race_data = self._db.get_race_json(target_date, venue, int(race_number))
                            odds_data = self._db.get_odds_json(target_date, venue, int(race_number))
                            if not race_data or not odds_data:
                                continue
                            all_combinations = self.predict_trifecta_probabilities_from_data(race_data, odds_data)
                            race_info = race_data.get("race_info", {})
                        else:
                            all_combinations = self.predict_trifecta_probabilities(race_path, odds_path)
                            with open(race_path, "r", encoding="utf-8") as f:
                                race_data = json.load(f)
                            race_info = race_data.get("race_info", {})
                        if all_combinations:
                            race_time = race_info.get("race_time", "09:00")
                            prediction = {
                                "venue": venue,
                                "venue_code": self.get_venue_code(venue),
                                "race_number": int(race_number),
                                "race_time": race_time,
                                "all_combinations": all_combinations,
                            }
                            if include_selected_bets and _BETTING_AVAILABLE:
                                try:
                                    cfg = ImprovementConfigManager()
                                    prediction["selected_bets"] = select_bets(
                                        all_combinations,
                                        strategy=cfg.get_betting_strategy(),
                                        top_n=cfg.get_betting_top_n(),
                                        score_threshold=cfg.get_betting_score_threshold(),
                                        ev_threshold=cfg.get_betting_ev_threshold(),
                                    )
                                except Exception as e:
                                    self.logger.debug("selected_bets skipped: %s", e)
                            predictions.append(prediction)
                            successful_predictions += 1
                    except Exception as e:
                        self.logger.error(f"レース予測エラー {venue} {race_number}: {e}")
            else:
                # 新規データでの予測
                for race_key, entry_data in entries.items():
                    try:
                        venue, race_number = race_key.split('_')
                        race_number = int(race_number)
                        
                        self.logger.info(f"予測中: {venue} {race_number}")
                        
                        # オッズデータを取得
                        odds_data = odds.get(race_key)
                        odds_available = bool(odds_data and odds_data.get('odds_data'))
                        if not odds_available:
                            self.logger.warning(f"オッズデータがありません（期待値は暫定値になります）: {race_key}")
                            odds_data = {'odds_data': []}
                        
                        # 3連単予測（新規データ用）
                        all_combinations = self.predict_trifecta_probabilities_from_data(entry_data, odds_data)

                        if all_combinations:
                            race_info = entry_data.get("race_info", {})
                            race_time = race_info.get("race_time", "09:00")
                            prediction = {
                                "venue": venue,
                                "venue_code": self.get_venue_code(venue),
                                "race_number": race_number,
                                "race_time": race_time,
                                "all_combinations": all_combinations,
                                "odds_available": odds_available,
                            }
                            if include_selected_bets and _BETTING_AVAILABLE:
                                try:
                                    cfg = ImprovementConfigManager()
                                    prediction["selected_bets"] = select_bets(
                                        all_combinations,
                                        strategy=cfg.get_betting_strategy(),
                                        top_n=cfg.get_betting_top_n(),
                                        score_threshold=cfg.get_betting_score_threshold(),
                                        ev_threshold=cfg.get_betting_ev_threshold(),
                                    )
                                except Exception as e:
                                    self.logger.debug("selected_bets skipped: %s", e)
                            predictions.append(prediction)
                            successful_predictions += 1
                            if odds_available:
                                odds_available_predictions += 1
                        
                    except Exception as e:
                        self.logger.error(f"レース予測エラー {race_key}: {e}")
            
            # 5. 会場別サマリー
            venue_summaries = self.generate_venue_summaries(predictions)
            
            # 6. 実行結果
            execution_time = (datetime.now() - start_time).total_seconds() / 60
            
            result = {
                'prediction_date': target_date,
                'generated_at': datetime.now().isoformat(),
                'model_info': self.model_info,
                'execution_summary': {
                    'total_venues': len(set(p['venue'] for p in predictions)),
                    'total_races': len(predictions),
                    'successful_predictions': successful_predictions,
                    'odds_available_predictions': odds_available_predictions,
                    'odds_missing_predictions': max(successful_predictions - odds_available_predictions, 0),
                    'execution_time_minutes': execution_time,
                    'data_fetched': fetch_data,
                    'prediction_only': prediction_only
                },
                'predictions': predictions,
                'venue_summaries': venue_summaries
            }
            
            self.logger.info(f"完全統合予測フロー完了: {successful_predictions}レース, {execution_time:.1f}分")
            return result
            
        except Exception as e:
            self.logger.error(f"完全統合予測フローエラー: {e}")
            return None
    
    def _get_ratio_from_odds_data(self, odds_data: Optional[Dict], trifecta: Tuple[int, int, int]) -> Optional[float]:
        """オッズ辞書から指定3連単の倍率を取得。EV戦略用。"""
        if not odds_data:
            return None
        for o in odds_data.get("odds_data") or []:
            if tuple(o.get("betting_numbers", [])) == trifecta:
                r = o.get("ratio")
                return float(r) if r is not None else None
            if o.get("combination") == f"{trifecta[0]}-{trifecta[1]}-{trifecta[2]}":
                r = o.get("ratio")
                return float(r) if r is not None else None
        return None

    def predict_trifecta_probabilities_from_data(self, race_data: Dict, odds_data: Dict) -> List[Dict]:
        """新規データから3連単の予測確率を計算（120通り全て）"""
        try:
            state = self.vectorize_race_state_from_data(race_data, odds_data)
            state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
            if self.model is None or not hasattr(self.model, 'policy'):
                self.logger.error("モデルがロードされていないか、policy属性がありません")
                return []
            policy = self.model.policy
            get_dist = getattr(policy, 'get_distribution', None)
            if get_dist is None:
                self.logger.error("policyにget_distributionメソッドがありません")
                return []
            dist = get_dist(state_tensor)
            distribution = getattr(dist, 'distribution', None)
            if distribution is None or not hasattr(distribution, 'probs'):
                self.logger.error("distributionにprobs属性がありません")
                return []
            action_probs = distribution.probs.detach().cpu().numpy()[0]
            trifecta_list = list(permutations(range(1, 7), 3))
            probability_combinations = []
            for i, prob in enumerate(action_probs):
                trifecta = trifecta_list[i]
                combination_str = f"{trifecta[0]}-{trifecta[1]}-{trifecta[2]}"
                ratio = self._get_ratio_from_odds_data(odds_data, trifecta)
                probability_combinations.append({
                    "combination": combination_str,
                    "probability": float(prob),
                    "expected_value": self.calculate_expected_value_from_data(trifecta, odds_data),
                    "ratio": ratio,
                    "rank": 0,
                })
            probability_combinations.sort(key=lambda x: x["probability"], reverse=True)
            for i, item in enumerate(probability_combinations):
                item["rank"] = i + 1
            return probability_combinations
        except Exception as e:
            self.logger.error(f"新規データ予測エラー: {e}")
            return []
    
    def vectorize_race_state_from_data(self, race_data: Dict, odds_data: Dict) -> List[float]:
        """新規データから状態ベクトルを生成（共通モジュール・オッズは状態に含めない）"""
        try:
            state = build_race_state_vector(race_data, None)
            self.logger.debug(f"状態ベクトル次元: {len(state)}")
            return state.tolist()
        except Exception as e:
            self.logger.error(f"状態ベクトル生成エラー: {e}")
            return [0.0] * get_state_dim()
    
    def calculate_expected_value_from_data(self, trifecta: Tuple[int, int, int], odds_data: Dict) -> float:
        """辞書オッズデータから期待値を計算（DB/API 用。betting_numbers または combination に対応）"""
        try:
            odds_list = odds_data.get("odds_data", [])
            odds = 0
            for o in odds_list:
                if tuple(o.get("betting_numbers", [])) == trifecta:
                    odds = o.get("ratio", 0)
                    break
                if o.get("combination") == f"{trifecta[0]}-{trifecta[1]}-{trifecta[2]}":
                    odds = o.get("ratio", 0)
                    break
            return odds * 0.05 - 1
        except Exception as e:
            self.logger.warning(f"期待値計算エラー: {e}")
            return 0.0

def main():
    parser = argparse.ArgumentParser(description='予想ツール - 3連単予測・購入方法提案')
    parser.add_argument('--predict-date', type=str, help='予測対象日 (YYYY-MM-DD)')
    parser.add_argument('--venues', type=str, help='対象会場 (カンマ区切り)')
    parser.add_argument('--model-path', type=str, help='モデルファイルパス')
    parser.add_argument('--output-dir', type=str, help='出力ディレクトリ')
    parser.add_argument('--data-dir', type=str, help='レースデータのディレクトリ（data-source=file のとき）')
    parser.add_argument('--data-source', type=str, choices=['file', 'db'], default='db', help='データソース: file=JSON, db=SQLite（デフォルト: db）')
    parser.add_argument('--db-path', type=str, default=None, help='data-source=db のときの SQLite パス（未指定時は kyotei_predictor/data/kyotei_races.sqlite）')
    parser.add_argument('--verbose', action='store_true', help='詳細ログ出力')
    
    # 新規引数の追加
    parser.add_argument('--fetch-data', action='store_true', help='当日データ取得を実行')
    parser.add_argument('--prediction-only', action='store_true', help='予測のみ実行（既存データ使用）')
    parser.add_argument('--risk-level', choices=['low', 'medium', 'high'], default='medium', help='リスクレベル')
    parser.add_argument('--complete-flow', action='store_true', help='完全統合フローを実行')
    parser.add_argument('--include-selected-bets', action='store_true',
                        help='設定に基づく買い目選定（selected_bets）を予測結果に含める')
    
    args = parser.parse_args()
    
    # ログレベル設定
    log_level = logging.DEBUG if args.verbose else logging.INFO
    
    # 予想ツール初期化（デフォルトは DB からレースデータ取得）
    tool = PredictionTool(
        log_level,
        data_dir=args.data_dir,
        model_path=args.model_path,
        data_source=args.data_source,
        db_path=args.db_path,
    )
    
    # 会場リスト（正規化）
    venues = None
    if args.venues:
        venues = [v.strip().upper() for v in args.venues.split(',')]
        tool.utils.safe_print(f'DEBUG: venues = {venues}')
        tool.logger.info(f'指定会場: {venues}')
    
    # 実行モードの決定
    if args.complete_flow:
        # 完全統合フロー実行
        tool.utils.safe_print(f'DEBUG: calling run_complete_prediction with venues = {venues}')
        result = tool.run_complete_prediction(
            target_date=args.predict_date,
            venues=venues,
            fetch_data=args.fetch_data,
            prediction_only=args.prediction_only,
            include_selected_bets=args.include_selected_bets,
        )
    else:
        # 従来の予測実行（--predict-dateが必須）
        if not args.predict_date:
            tool.utils.safe_print("エラー: --predict-date が必要です")
            return
        
        result = tool.predict_races(args.predict_date, venues, include_selected_bets=args.include_selected_bets)
    
    if result:
        # 結果保存
        output_path = tool.save_prediction_result(result, args.output_dir)
        
        if output_path:
            tool.utils.safe_print(f"\n=== 予測完了 ===")
            tool.utils.safe_print(f"予測日: {result['prediction_date']}")
            tool.utils.safe_print(f"対象レース数: {result['execution_summary']['total_races']}")
            tool.utils.safe_print(f"成功レース数: {result['execution_summary']['successful_predictions']}")
            tool.utils.safe_print(f"実行時間: {result['execution_summary']['execution_time_minutes']:.1f}分")
            if 'data_fetched' in result['execution_summary']:
                tool.utils.safe_print(f"データ取得: {'あり' if result['execution_summary']['data_fetched'] else 'なし'}")
                tool.utils.safe_print(f"予測のみ: {'あり' if result['execution_summary']['prediction_only'] else 'なし'}")
            tool.utils.safe_print(f"結果ファイル: {output_path}")
        else:
            tool.utils.safe_print("予測結果の保存に失敗しました")
    else:
        tool.utils.safe_print("予測の実行に失敗しました")

if __name__ == "__main__":
    main() 