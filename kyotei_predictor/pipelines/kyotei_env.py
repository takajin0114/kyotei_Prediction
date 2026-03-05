import gymnasium as gym
import numpy as np
import pandas as pd
import json
from itertools import permutations
from typing import Tuple, List, Dict, Any, Optional
import glob
import random
import os
import logging
from pathlib import Path

# 共通状態ベクトル（オッズは状態に含めない）
from kyotei_predictor.pipelines.state_vector import build_race_state_vector, get_state_dim

# 設定管理クラスをインポート
try:
    from ..config.improvement_config_manager import ImprovementConfigManager
    CONFIG_MANAGER = ImprovementConfigManager()
except ImportError:
    # 設定管理クラスが利用できない場合はデフォルト値を使用
    CONFIG_MANAGER = None
    logging.warning("ImprovementConfigManager not available, using default values")

# Kyotei用ロギング設定（日時は utils.logger の config に従う）
ENABLE_KYOTEI_LOGGING = True  # TrueでDEBUG/INFOも表示、FalseでWARNING以上のみ
def _kyotei_env_log_config():
    try:
        from kyotei_predictor.utils.logger import get_logging_format, get_logging_datefmt
        return get_logging_format(), get_logging_datefmt()
    except Exception:
        return "%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S"
_kyotei_fmt, _kyotei_datefmt = _kyotei_env_log_config()
if ENABLE_KYOTEI_LOGGING:
    os.makedirs('outputs/logs', exist_ok=True)
    logging.basicConfig(level=logging.DEBUG, format=_kyotei_fmt, datefmt=_kyotei_datefmt, filename='outputs/logs/kyotei_env_debug.log', filemode='w')
else:
    logging.basicConfig(level=logging.WARNING, format=_kyotei_fmt, datefmt=_kyotei_datefmt)

# config の日時フォーマットで出すため logging に統一（print は使わない）
_log = logging.getLogger(__name__)


class KyoteiEnv(gym.Env):
    """
    競艇レース用の強化学習環境（3連単・損益ベース）。
    resetでレースデータ・oddsデータ・正解着順をセットし、stepでactionに対しrewardを返す。
    1レース1エピソードの簡易実装。
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self, race_data_path=None, odds_data_path=None, race_data=None, odds_data=None, bet_amount=100):
        super().__init__()
        self.race_data_path = race_data_path
        self.odds_data_path = odds_data_path
        self._race_data_dict = race_data  # DB から渡す場合の辞書
        self._odds_data_dict = odds_data
        self.bet_amount = bet_amount
        self.observation_space = gym.spaces.Box(low=0, high=1, shape=(get_state_dim(),), dtype=np.float32)
        self.action_space = gym.spaces.Discrete(120)
        self.state = None
        self.terminated = False
        self.odds_data = []  # 必ずリストで初期化
        self.arrival_tuple = (0,0,0)  # 必ずタプルで初期化

    def reset(self, *, seed=None, options=None) -> Tuple[np.ndarray | None, dict]:
        super().reset(seed=seed)
        if self._race_data_dict is not None and self._odds_data_dict is not None:
            race = self._race_data_dict
            odds = self._odds_data_dict
        else:
            assert self.race_data_path and self.odds_data_path, "race_data_path, odds_data_path または race_data, odds_data を指定してください"
            with open(self.race_data_path, encoding='utf-8') as f:
                race = json.load(f)
            with open(self.odds_data_path, encoding='utf-8') as f:
                odds = json.load(f)
        self.odds_data = odds.get('odds_data', [])
        valid_records = [r for r in race.get('race_records', []) if r.get('arrival') is not None]
        if ENABLE_KYOTEI_LOGGING:
            _log.debug("[KyoteiEnv.reset] valid_records=%s", len(valid_records))
        if len(valid_records) < 3:
            _log.debug("[KyoteiEnv.reset] Skipping race with insufficient valid records: %s < 3", len(valid_records))
            logging.warning(f"Skipping race with insufficient valid records: {len(valid_records)} < 3")
            raise ValueError(f"Insufficient valid records: {len(valid_records)} < 3")
        records = sorted(valid_records, key=lambda x: x['arrival'])
        self.arrival_tuple = tuple(r['pit_number'] for r in records[:3])
        _log.debug("[KyoteiEnv.reset] arrival_tuple=%s", self.arrival_tuple)
        if len(self.arrival_tuple) != 3:
            _log.debug("[KyoteiEnv.reset] Skipping race with invalid arrival_tuple: %s", self.arrival_tuple)
            logging.warning(f"Skipping race with invalid arrival_tuple: {self.arrival_tuple}")
            raise ValueError(f"Invalid arrival_tuple: {self.arrival_tuple}, length: {len(self.arrival_tuple)}")
        # 状態は出走表＋レース情報のみ（オッズは含めない）。報酬計算では self.odds_data を使用
        self.state = build_race_state_vector(race, None)
        self.terminated = False
        info = {}
        _log.debug("[KyoteiEnv.reset] state shape=%s", self.state.shape if hasattr(self.state, 'shape') else type(self.state))
        return self.state, info

    def step(self, action: int) -> Tuple[np.ndarray | None, float, bool, bool, dict]:
        assert not self.terminated, "エピソードはすでに終了しています。resetしてください。"
        # 報酬計算
        reward = calc_trifecta_reward(action, self.arrival_tuple, self.odds_data, self.bet_amount)
        self.terminated = True  # 1レース1stepで終了
        truncated = False
        info = {"arrival": self.arrival_tuple}
        return self.state, reward, self.terminated, truncated, info

    def render(self, mode: str = "human") -> None:
        logging.debug(f"State: {self.state}")

    def close(self) -> None:
        pass

# --- 状態ベクトル生成（共通モジュール利用・オッズは状態に含めない） ---
def vectorize_race_state(race_data_path: str, odds_data_path: str) -> np.ndarray:
    """
    ファイルパスから状態ベクトルを生成する。状態にはオッズを含めない。
    odds_data_path は互換用に受け取るが、状態の計算では使用しない。
    """
    with open(race_data_path, encoding='utf-8') as f:
        race = json.load(f)
    return build_race_state_vector(race, None) 

# --- 3連単actionと買い目の相互変換関数 ---
TRIFECTA_LIST = list(permutations(range(1,7), 3))  # 1-indexed, 120通り
TRIFECTA_MAP = {v: i for i, v in enumerate(TRIFECTA_LIST)}

def action_to_trifecta(action: int) -> Tuple[int, int, int]:
    """action(0-119)→(1着,2着,3着)の買い目タプル"""
    return TRIFECTA_LIST[action]

def trifecta_to_action(trifecta: Tuple[int, int, int]) -> int:
    """(1着,2着,3着)の買い目タプル→action(0-119)"""
    return TRIFECTA_MAP[trifecta]

def calc_trifecta_reward(action: int, arrival_tuple: Tuple[int,int,int], odds_data: list, bet_amount: int = 100) -> float:
    """
    action（0-119）, 着順タプル, oddsデータ, 賭け金を受け取り、段階的報酬を返す。
    
    設定ファイルから報酬パラメータを取得し、動的に報酬を計算します。
    """
    # 設定ファイルから報酬パラメータを取得
    if CONFIG_MANAGER is not None:
        reward_params = CONFIG_MANAGER.get_reward_params()
        win_multiplier = reward_params.get("win_multiplier", 1.5)
        partial_second_hit_reward = reward_params.get("partial_second_hit_reward", 10)
        partial_first_hit_penalty = reward_params.get("partial_first_hit_penalty", -10)
        no_hit_penalty = reward_params.get("no_hit_penalty", -80)
    else:
        # デフォルト値（設定ファイルが利用できない場合）
        win_multiplier = 1.5
        partial_second_hit_reward = 10
        partial_first_hit_penalty = -10
        no_hit_penalty = -80
    
    # 着順タプルの妥当性チェック
    if len(arrival_tuple) != 3:
        logging.warning(f"Invalid arrival_tuple: {arrival_tuple}, length: {len(arrival_tuple)}")
        return no_hit_penalty  # 不正な着順の場合はペナルティ
    
    trifecta = action_to_trifecta(action)
    
    # 的中判定
    is_win = trifecta == arrival_tuple
    
    if is_win:
        # 的中時: 払戻金-賭け金 × win_multiplier
        odds_map = {tuple(o['betting_numbers']): o['ratio'] for o in odds_data}
        odds = odds_map.get(trifecta, 0)
        payout = odds * bet_amount
        reward = (payout - bet_amount) * win_multiplier
    else:
        # 部分的中の判定
        first_hit = trifecta[0] == arrival_tuple[0]  # 1着的中
        second_hit = trifecta[1] == arrival_tuple[1]  # 2着的中
        if first_hit and second_hit:
            reward = partial_second_hit_reward  # 2着的中の報酬
        elif first_hit:
            reward = partial_first_hit_penalty  # 1着的中のペナルティ
        else:
            reward = no_hit_penalty  # 不的中のペナルティ
    return reward

def calc_trifecta_reward_improved(action: int, arrival_tuple: Tuple[int,int,int], odds_data: list, bet_amount: int = 100) -> float:
    """
    改善された段階的報酬設計（Phase 1）のテスト用関数
    
    改善点:
    - 的中報酬の強化: 1.2 → 1.5
    - 部分的中の報酬化: 2着的中を0 → +10
    - ペナルティの緩和: 1着的中を-20 → -10, 不的中を-100 → -80
    """
    # 設定ファイルから報酬パラメータを取得
    if CONFIG_MANAGER is not None:
        reward_params = CONFIG_MANAGER.get_reward_params()
        win_multiplier = reward_params.get("win_multiplier", 1.5)
        partial_second_hit_reward = reward_params.get("partial_second_hit_reward", 10)
        partial_first_hit_penalty = reward_params.get("partial_first_hit_penalty", -10)
        no_hit_penalty = reward_params.get("no_hit_penalty", -80)
    else:
        # デフォルト値（設定ファイルが利用できない場合）
        win_multiplier = 1.5
        partial_second_hit_reward = 10
        partial_first_hit_penalty = -10
        no_hit_penalty = -80
    
    # 着順タプルの妥当性チェック
    if len(arrival_tuple) != 3:
        logging.warning(f"Invalid arrival_tuple: {arrival_tuple}, length: {len(arrival_tuple)}")
        return no_hit_penalty  # 不正な着順の場合はペナルティ
    
    trifecta = action_to_trifecta(action)
    
    # 的中判定
    is_win = trifecta == arrival_tuple
    
    if is_win:
        # 的中時: 払戻金-賭け金 × win_multiplier
        odds_map = {tuple(o['betting_numbers']): o['ratio'] for o in odds_data}
        odds = odds_map.get(trifecta, 0)
        payout = odds * bet_amount
        reward = (payout - bet_amount) * win_multiplier
    else:
        # 部分的中の判定
        first_hit = trifecta[0] == arrival_tuple[0]  # 1着的中
        second_hit = trifecta[1] == arrival_tuple[1]  # 2着的中
        if first_hit and second_hit:
            reward = partial_second_hit_reward  # 2着的中を報酬化
        elif first_hit:
            reward = partial_first_hit_penalty  # 1着的中のペナルティ
        else:
            reward = no_hit_penalty  # 不的中のペナルティ
    
    return reward

class KyoteiEnvManager(gym.Env):
    """
    複数レースデータを使ったエピソード切替用ラッパー。
    data_dir から race_data/odds_data のペア一覧を作成するか、data_source='db' の場合は DB からペアを取得する。
    gym.Envを継承してstable-baselines3との互換性を確保。
    """
    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        data_dir: str = "../data",
        bet_amount: int = 100,
        year_month: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        data_source: str = "file",
        db_path: Optional[str] = None,
    ):
        super().__init__()
        self.data_source = data_source
        self.db_path = db_path
        self._db = None
        if data_source == "db" and db_path:
            from kyotei_predictor.data.race_db import RaceDB
            self._db = RaceDB(db_path)
        logging.debug(f"[KyoteiEnvManager.__init__] data_source={data_source}, data_dir={data_dir}")
        self.data_dir = data_dir
        self.year_month = year_month  # 年月フィルタ（例: "2024-01"）
        self.date_from = date_from  # 日付範囲（例: "2025-01-01"）
        self.date_to = date_to  # 日付範囲（例: "2025-12-31"）
        self.bet_amount = bet_amount
        self.pairs = self._find_race_odds_pairs()
        self.env = None

    def _find_race_odds_pairs(self) -> list:
        if self.data_source == "db" and self._db is not None:
            pairs = self._db.get_race_odds_pairs(
                year_month=self.year_month,
                date_from=self.date_from,
                date_to=self.date_to,
            )
            return [(p[0], p[1], p[2]) for p in pairs]  # (race_date, stadium, race_number)
        logging.debug(f"data_dir: {self.data_dir}")
        logging.debug(f"abspath(data_dir): {os.path.abspath(self.data_dir)}")
        logging.debug(f"year_month filter: {self.year_month}")
        
        # サブディレクトリも含めて再帰的に検索
        race_pattern = os.path.join(self.data_dir, "**", "race_data_*.json")
        odds_pattern = os.path.join(self.data_dir, "**", "odds_data_*.json")
        
        logging.debug(f"race_pattern: {race_pattern}")
        logging.debug(f"odds_pattern: {odds_pattern}")
        
        # キャッシュを完全に無効化して年月フィルタを確実に動作させる
        _log.debug("[DEBUG] Cache disabled, recalculating pairs for year_month: %s", self.year_month)
        # キャッシュをクリア
        if hasattr(self, '_pairs_cache'):
            delattr(self, '_pairs_cache')
        
        # 年月フィルタのデバッグ情報を追加
        _log.debug("[DEBUG] Year month filter: %s", self.year_month)
        _log.debug("[DEBUG] Data directory: %s", self.data_dir)
        
        # ファイル検索を最適化
        race_files = []
        odds_files = []
        
        # ディレクトリを直接探索して高速化
        for root, dirs, files in os.walk(self.data_dir):
            for file in files:
                if file.startswith('race_data_') and file.endswith('.json'):
                    race_files.append(os.path.join(root, file))
                elif file.startswith('odds_data_') and file.endswith('.json'):
                    odds_files.append(os.path.join(root, file))
        
        # 年月フィルタリングを適用
        if self.year_month:
            _log.debug("[DEBUG] Applying year_month filter: %s", self.year_month)
            original_race_count = len(race_files)
            original_odds_count = len(odds_files)
            
            race_files = [f for f in race_files if self._matches_year_month(os.path.basename(f), self.year_month)]
            odds_files = [f for f in odds_files if self._matches_year_month(os.path.basename(f), self.year_month)]
            
            _log.debug("[DEBUG] After filtering - race_files: %s (from %s)", len(race_files), original_race_count)
            _log.debug("[DEBUG] After filtering - odds_files: %s (from %s)", len(odds_files), original_odds_count)
        else:
            _log.debug("[DEBUG] No year_month filter applied")
        
        logging.debug(f"race_files count: {len(race_files)}")
        logging.debug(f"odds_files count: {len(odds_files)}")
        
        if not race_files:
            logging.warning(f"No race files found in {self.data_dir} with filter: {self.year_month}")
            return []
        if not odds_files:
            logging.warning(f"No odds files found in {self.data_dir} with filter: {self.year_month}")
            return []
        
        # ファイル名ベースでマッピングを作成
        race_map = {}
        odds_map = {}
        
        for race_file in race_files:
            # ファイル名からキーを抽出（例: race_data_2024-03-31_OMURA_R1.json -> race_data_2024-03-31_OMURA_R1.json）
            key = os.path.basename(race_file)
            race_map[key] = race_file
            
        for odds_file in odds_files:
            # ファイル名からキーを抽出（例: odds_data_2024-03-31_OMURA_R1.json -> odds_data_2024-03-31_OMURA_R1.json）
            key = os.path.basename(odds_file)
            odds_map[key] = odds_file
        
        logging.debug(f"race_map keys count: {len(race_map)}")
        logging.debug(f"odds_map keys count: {len(odds_map)}")
        
        # 共通のキーを見つける（race_data_YYYY-MM-DD_VENUE_RN.json と odds_data_YYYY-MM-DD_VENUE_RN.json）
        common_keys = set()
        for race_key in race_map.keys():
            odds_key = race_key.replace("race_data_", "odds_data_")
            if odds_key in odds_map:
                common_keys.add(race_key)
        
        logging.debug(f"common_keys count: {len(common_keys)}")
        
        # ペアリストを作成（ファイルモードは (race_path, odds_path) の2タプル）
        pairs = []
        for race_key in common_keys:
            odds_key = race_key.replace("race_data_", "odds_data_")
            pairs.append((race_map[race_key], odds_map[odds_key]))
        
        _log.debug("[DEBUG] Final pairs count (file): %s", len(pairs))
        if pairs:
            _log.debug("[DEBUG] Sample pair: %s", pairs[0])
        logging.debug(f"pairs count: {len(pairs)}")
        if pairs:
            logging.debug(f"sample pair: {pairs[0]}")
        
        # キャッシュを無効化（年月フィルタの確実な動作のため）
        _log.debug("[DEBUG] Cache disabled, not saving pairs to cache")
        
        return pairs

    def _matches_year_month(self, filename: str, year_month: str) -> bool:
        """
        ファイル名が指定された年月に一致するかチェック
        
        Args:
            filename: ファイル名（例: race_data_2024-01-27_OMURA_R1.json）
            year_month: 年月（例: "2024-01"）
        
        Returns:
            bool: 一致する場合True
        """
        if not year_month:
            return True  # フィルタが指定されていない場合は常にTrue
        
        try:
            # ファイル名から日付部分を抽出
            # race_data_2024-01-27_OMURA_R1.json -> 2024-01-27
            if not filename.startswith(('race_data_', 'odds_data_')):
                return False
            
            # アンダースコアで分割して日付部分を取得
            parts = filename.split('_')
            if len(parts) >= 3:
                date_part = parts[2]  # 2024-01-27
                if len(date_part) >= 7:
                    file_year_month = date_part[:7]  # 2024-01
                    return file_year_month == year_month
            return False
        except Exception as e:
            return False

    def reset(self, *, seed=None, options=None) -> Tuple[np.ndarray | None, dict]:
        _log.debug("[KyoteiEnvManager.reset] called. pairs=%s", len(self.pairs))
        # 年月フィルタの確認
        if self.year_month:
            _log.debug("[KyoteiEnvManager.reset] year_month filter: %s", self.year_month)
            # 実際のペアの年月分布を確認（ファイルモード時のみ；DB は既に絞り込み済み）
            year_month_distribution = {}
            if self.pairs and len(self.pairs[0]) == 2:
                for pair in self.pairs:
                    race_file = os.path.basename(pair[0])
                    if race_file.startswith('race_data_'):
                        parts = race_file.split('_')
                        if len(parts) >= 3:
                            date_part = parts[2]
                            if len(date_part) >= 7:
                                ym = date_part[:7]
                                year_month_distribution[ym] = year_month_distribution.get(ym, 0) + 1
            elif self.pairs and len(self.pairs[0]) == 3:
                for pair in self.pairs:
                    date_s = pair[0]
                    if len(date_s) >= 7:
                        ym = date_s[:7]
                        year_month_distribution[ym] = year_month_distribution.get(ym, 0) + 1
            if year_month_distribution:
                _log.debug("[KyoteiEnvManager.reset] actual year_month distribution: %s", year_month_distribution)
        else:
            _log.debug("[KyoteiEnvManager.reset] no year_month filter applied")
        
        super().reset(seed=seed)
        
        # ペアが空の場合はエラー
        if not self.pairs:
            error_msg = f"No valid race-odds pairs found in {self.data_dir} with filter: {self.year_month}. Please check if data files exist."
            _log.debug("[KyoteiEnvManager.reset] %s", error_msg)
            logging.error(error_msg)
            raise ValueError(error_msg)
        
        # 有効なレースが見つかるまで試行（無限ループ防止）
        max_attempts = 50  # 試行回数を増やす
        attempted_pairs = set()  # 既に試行したペアを記録
        
        # 利用するペアを決定（DB の場合は既に year_month で絞り込み済み）
        if self.pairs and len(self.pairs[0]) == 3:
            available_pairs = self.pairs  # DB モード: 既に get_race_odds_pairs(year_month=...) で絞り込み済み
        elif self.year_month:
            filtered_pairs = []
            for pair in self.pairs:
                race_file = os.path.basename(pair[0])
                if self._matches_year_month(race_file, self.year_month):
                    filtered_pairs.append(pair)
            if filtered_pairs:
                available_pairs = filtered_pairs
                _log.debug("[KyoteiEnvManager.reset] Using %s pairs filtered by year_month: %s", len(filtered_pairs), self.year_month)
            else:
                _log.debug("[KyoteiEnvManager.reset] No pairs match year_month filter: %s, using all pairs", self.year_month)
                available_pairs = self.pairs
        else:
            available_pairs = self.pairs
        
        for attempt in range(max_attempts):
            try:
                current_available_pairs = [p for p in available_pairs if p not in attempted_pairs]
                if not current_available_pairs:
                    attempted_pairs.clear()
                    current_available_pairs = available_pairs

                chosen = random.choice(current_available_pairs)
                attempted_pairs.add(chosen)

                if len(chosen) == 3:
                    # DB モード: (race_date, stadium, race_number)
                    race_date, stadium, race_number = chosen
                    race_data = self._db.get_race_json(race_date, stadium, race_number)
                    odds_data = self._db.get_odds_json(race_date, stadium, race_number)
                    if not race_data or not odds_data:
                        continue
                    if ENABLE_KYOTEI_LOGGING:
                        _log.debug("[KyoteiEnvManager.reset] attempt %s: DB %s %s R%s", attempt + 1, race_date, stadium, race_number)
                    self.env = KyoteiEnv(race_data=race_data, odds_data=odds_data, bet_amount=self.bet_amount)
                else:
                    # ファイルモード: (race_path, odds_path)
                    race_path, odds_path = chosen
                    if ENABLE_KYOTEI_LOGGING:
                        _log.debug("[KyoteiEnvManager.reset] attempt %s: race=%s, odds=%s", attempt + 1, race_path, odds_path)
                    logging.debug(f"Selected race: {race_path}")
                    logging.debug(f"Selected odds: {odds_path}")
                    self.env = KyoteiEnv(race_data_path=race_path, odds_data_path=odds_path, bet_amount=self.bet_amount)
                return self.env.reset()
            except ValueError as e:
                _log.debug("[KyoteiEnvManager.reset] attempt %s failed: %s", attempt + 1, e)
                logging.info(f"Attempt {attempt + 1}: Skipping invalid race data: {e}")
                if attempt == max_attempts - 1:
                    _log.debug("[KyoteiEnvManager.reset] All attempts failed, using fallback data")
                    logging.warning(f"All attempts failed, using fallback data")
                    if len(chosen) == 3:
                        rd = self._db.get_race_json(chosen[0], chosen[1], chosen[2])
                        od = self._db.get_odds_json(chosen[0], chosen[1], chosen[2])
                        if rd and od:
                            self.env = KyoteiEnv(race_data=rd, odds_data=od, bet_amount=self.bet_amount)
                    else:
                        self.env = KyoteiEnv(race_data_path=chosen[0], odds_data_path=chosen[1], bet_amount=self.bet_amount)
                    if self.env:
                        self.env.arrival_tuple = (1, 2, 3)
                        return self.env.state, {}
        
        # 万が一の場合のフォールバック
        chosen = random.choice(self.pairs)
        if len(chosen) == 3:
            rd = self._db.get_race_json(chosen[0], chosen[1], chosen[2]) if self._db else None
            od = self._db.get_odds_json(chosen[0], chosen[1], chosen[2]) if self._db else None
            if rd and od:
                self.env = KyoteiEnv(race_data=rd, odds_data=od, bet_amount=self.bet_amount)
        else:
            _log.debug("[KyoteiEnvManager.reset] fallback: race=%s, odds=%s", chosen[0], chosen[1])
            self.env = KyoteiEnv(race_data_path=chosen[0], odds_data_path=chosen[1], bet_amount=self.bet_amount)
        if self.env:
            self.env.arrival_tuple = (1, 2, 3)
        return (self.env.state, {}) if self.env else (None, {})

    def step(self, action: int) -> Tuple[np.ndarray | None, float, bool, bool, dict]:
        if self.env is None:
            raise RuntimeError("envが初期化されていません。reset()を先に呼んでください。")
        return self.env.step(action)
    
    def render(self, mode: str = "human") -> None:
        if self.env is not None:
            return self.env.render(mode)
        return None
    
    def close(self) -> None:
        if self.env is not None:
            self.env.close()

    @property
    def action_space(self):
        if self.env is not None:
            return self.env.action_space
        # デフォルトのaction_spaceを返す（初期化前）
        return gym.spaces.Discrete(120)

    @property
    def observation_space(self):
        if self.env is not None:
            return self.env.observation_space
        # デフォルトのobservation_spaceを返す（初期化前）
        return gym.spaces.Box(low=0, high=1, shape=(get_state_dim(),), dtype=np.float32) 