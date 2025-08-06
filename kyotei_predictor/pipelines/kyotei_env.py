import gymnasium as gym
import numpy as np
import pandas as pd
import json
from itertools import permutations
from typing import Tuple, List, Dict, Any
import glob
import random
import os
import logging
from pathlib import Path

# 設定管理クラスをインポート
try:
    from ..config.improvement_config_manager import ImprovementConfigManager
    CONFIG_MANAGER = ImprovementConfigManager()
except ImportError:
    # 設定管理クラスが利用できない場合はデフォルト値を使用
    CONFIG_MANAGER = None
    print("Warning: ImprovementConfigManager not available, using default values")

# Kyotei用ロギング設定
ENABLE_KYOTEI_LOGGING = True  # TrueでDEBUG/INFOも表示、FalseでWARNING以上のみ
if ENABLE_KYOTEI_LOGGING:
    os.makedirs('outputs/logs', exist_ok=True)
    logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s', filename='outputs/logs/kyotei_env_debug.log', filemode='w')
else:
    logging.basicConfig(level=logging.WARNING, format='[%(levelname)s] %(message)s')

class KyoteiEnv(gym.Env):
    """
    競艇レース用の強化学習環境（3連単・損益ベース）。
    resetでレースデータ・oddsデータ・正解着順をセットし、stepでactionに対しrewardを返す。
    1レース1エピソードの簡易実装。
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self, race_data_path=None, odds_data_path=None, bet_amount=100):
        super().__init__()
        self.race_data_path = race_data_path
        self.odds_data_path = odds_data_path
        self.bet_amount = bet_amount
        self.observation_space = gym.spaces.Box(low=0, high=1, shape=(192,), dtype=np.float32)
        self.action_space = gym.spaces.Discrete(120)
        self.state = None
        self.terminated = False
        self.odds_data = []  # 必ずリストで初期化
        self.arrival_tuple = (0,0,0)  # 必ずタプルで初期化

    def reset(self, *, seed=None, options=None) -> Tuple[np.ndarray | None, dict]:
        print(f"[KyoteiEnv.reset] called. race={self.race_data_path}, odds={self.odds_data_path}")
        super().reset(seed=seed)
        assert self.race_data_path and self.odds_data_path, "race_data_path, odds_data_pathを指定してください"
        with open(self.race_data_path, encoding='utf-8') as f:
            race = json.load(f)
        with open(self.odds_data_path, encoding='utf-8') as f:
            odds = json.load(f)
        self.odds_data = odds['odds_data']
        valid_records = [r for r in race['race_records'] if r.get('arrival') is not None]
        print(f"[KyoteiEnv.reset] valid_records={len(valid_records)}")
        if len(valid_records) < 3:
            print(f"[KyoteiEnv.reset] Skipping race with insufficient valid records: {len(valid_records)} < 3")
            logging.warning(f"Skipping race with insufficient valid records: {len(valid_records)} < 3")
            raise ValueError(f"Insufficient valid records: {len(valid_records)} < 3")
        records = sorted(valid_records, key=lambda x: x['arrival'])
        self.arrival_tuple = tuple(r['pit_number'] for r in records[:3])
        print(f"[KyoteiEnv.reset] arrival_tuple={self.arrival_tuple}")
        if len(self.arrival_tuple) != 3:
            print(f"[KyoteiEnv.reset] Skipping race with invalid arrival_tuple: {self.arrival_tuple}")
            logging.warning(f"Skipping race with invalid arrival_tuple: {self.arrival_tuple}")
            raise ValueError(f"Invalid arrival_tuple: {self.arrival_tuple}, length: {len(self.arrival_tuple)}")
        self.state = vectorize_race_state(self.race_data_path, self.odds_data_path)
        self.terminated = False
        info = {}
        print(f"[KyoteiEnv.reset] state shape={self.state.shape if hasattr(self.state, 'shape') else type(self.state)}")
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

# --- サンプル: 1レース分の状態ベクトル生成関数 ---
def vectorize_race_state(race_data_path: str, odds_data_path: str) -> np.ndarray:
    """
    race_data/odds_dataのjsonから状態ベクトルを生成するサンプル関数。
    特徴量・前処理はrepo.mdの方針に従う。
    """
    # 1. データ読み込み
    with open(race_data_path, encoding='utf-8') as f:
        race = json.load(f)
    with open(odds_data_path, encoding='utf-8') as f:
        odds = json.load(f)

    # 2. 各艇ごとの特徴量ベクトル
    rating_map = {'A1': [1,0,0,0], 'A2': [0,1,0,0], 'B1': [0,0,1,0], 'B2': [0,0,0,1]}
    boats = []
    
    # race_entriesがある場合はそれを使用、ない場合はrace_recordsから基本情報を構築
    if 'race_entries' in race:
        entries = race['race_entries']
    else:
        # race_recordsから基本情報を構築（エントリーデータがない場合のフォールバック）
        entries = []
        for record in race['race_records']:
            entry = {
                'pit_number': record['pit_number'],
                'racer': {'current_rating': 'B1'},  # デフォルト
                'performance': {'rate_in_all_stadium': 5.0, 'rate_in_event_going_stadium': 5.0},  # デフォルト
                'boat': {'quinella_rate': 50.0, 'trio_rate': 50.0},  # デフォルト
                'motor': {'quinella_rate': 50.0, 'trio_rate': 50.0}  # デフォルト
            }
            entries.append(entry)
    
    for entry in entries:
        pit = (entry['pit_number'] - 1) / 5  # 1-6→0-1
        rating = rating_map.get(entry['racer']['current_rating'], [0,0,0,0])
        # None/NaNチェックとfillna(0)を追加
        perf_all = entry['performance']['rate_in_all_stadium'] / 10 if entry['performance']['rate_in_all_stadium'] is not None else 0
        perf_local = entry['performance']['rate_in_event_going_stadium'] / 10 if entry['performance']['rate_in_event_going_stadium'] is not None else 0
        boat2 = entry['boat']['quinella_rate'] / 100 if entry['boat']['quinella_rate'] is not None else 0
        boat3 = entry['boat']['trio_rate'] / 100 if entry['boat']['trio_rate'] is not None else 0
        motor2 = entry['motor']['quinella_rate'] / 100 if entry['motor']['quinella_rate'] is not None else 0
        motor3 = entry['motor']['trio_rate'] / 100 if entry['motor']['trio_rate'] is not None else 0
        vec = [pit] + rating + [perf_all, perf_local, boat2, boat3, motor2, motor3]
        boats.append(vec)
    boats = np.array(boats)  # shape: (6, 特徴量数)

    # 3. レース全体特徴量
    stadiums = ['KIRYU','TODA','EDOGAWA']  # 必要に応じて拡張
    stadium_onehot = [1 if race['race_info']['stadium']==s else 0 for s in stadiums]
    race_num = (race['race_info']['race_number']-1)/11
    laps = (race['race_info']['number_of_laps']-1)/4 if 'number_of_laps' in race['race_info'] and race['race_info']['number_of_laps'] is not None else 0
    is_fixed = 1 if race['race_info'].get('is_course_fixed') else 0
    race_feat = stadium_onehot + [race_num, laps, is_fixed]

    # 4. オッズ特徴量（3連単120通り, log+minmax）
    trifecta_list = list(permutations(range(1,7), 3))  # 1-indexed
    odds_map = {tuple(o['betting_numbers']): o['ratio'] for o in odds['odds_data']}
    odds_vec = [np.log(odds_map.get(t, 1)+1) for t in trifecta_list]  # log(odds+1)
    # None/NaNチェックを追加
    odds_vec = [o if o is not None and not np.isnan(o) else 0 for o in odds_vec]
    odds_min, odds_max = min(odds_vec), max(odds_vec)
    # ゼロ除算を防ぐ
    if odds_max > odds_min:
        odds_vec = [(o-odds_min)/(odds_max-odds_min) for o in odds_vec]
    else:
        odds_vec = [0 for o in odds_vec]

    # 5. 結合
    state_vec = np.concatenate([boats.flatten(), race_feat, odds_vec])
    return state_vec 

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
        reward_params = CONFIG_MANAGER.get_reward_params("phase1")
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
        reward_params = CONFIG_MANAGER.get_reward_params("phase1")
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
    dataディレクトリからrace_data/odds_dataのペア一覧を作成し、resetごとにランダムなレースを選択してKyoteiEnvを初期化する。
    gym.Envを継承してstable-baselines3との互換性を確保。
    """
    metadata = {"render_modes": ["human"]}
    
    def __init__(self, data_dir: str = "../data", bet_amount: int = 100, year_month: str = None):
        super().__init__()
        logging.debug(f"[KyoteiEnvManager.__init__] received data_dir: {data_dir}")
        self.data_dir = data_dir
        self.year_month = year_month  # 年月フィルタ（例: "2024-01"）
        logging.debug(f"[KyoteiEnvManager.__init__] self.data_dir set to: {self.data_dir}")
        logging.debug(f"[KyoteiEnvManager.__init__] year_month filter: {self.year_month}")
        self.bet_amount = bet_amount
        self.pairs = self._find_race_odds_pairs()
        self.env = None

    def _find_race_odds_pairs(self) -> list:
        logging.debug(f"data_dir: {self.data_dir}")
        logging.debug(f"abspath(data_dir): {os.path.abspath(self.data_dir)}")
        logging.debug(f"year_month filter: {self.year_month}")
        
        # サブディレクトリも含めて再帰的に検索
        race_pattern = os.path.join(self.data_dir, "**", "race_data_*.json")
        odds_pattern = os.path.join(self.data_dir, "**", "odds_data_*.json")
        
        logging.debug(f"race_pattern: {race_pattern}")
        logging.debug(f"odds_pattern: {odds_pattern}")
        
        # キャッシュを完全に無効化して年月フィルタを確実に動作させる
        print(f"[DEBUG] Cache disabled, recalculating pairs for year_month: {self.year_month}")
        # キャッシュをクリア
        if hasattr(self, '_pairs_cache'):
            delattr(self, '_pairs_cache')
        
        # 年月フィルタのデバッグ情報を追加
        print(f"[DEBUG] Year month filter: {self.year_month}")
        print(f"[DEBUG] Data directory: {self.data_dir}")
        
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
            print(f"[DEBUG] Applying year_month filter: {self.year_month}")
            original_race_count = len(race_files)
            original_odds_count = len(odds_files)
            
            race_files = [f for f in race_files if self._matches_year_month(os.path.basename(f), self.year_month)]
            odds_files = [f for f in odds_files if self._matches_year_month(os.path.basename(f), self.year_month)]
            
            print(f"[DEBUG] After filtering - race_files: {len(race_files)} (from {original_race_count})")
            print(f"[DEBUG] After filtering - odds_files: {len(odds_files)} (from {original_odds_count})")
        else:
            print(f"[DEBUG] No year_month filter applied")
        
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
            # race_data_YYYY-MM-DD_VENUE_RN.json -> odds_data_YYYY-MM-DD_VENUE_RN.json
            odds_key = race_key.replace("race_data_", "odds_data_")
            if odds_key in odds_map:
                common_keys.add(race_key)
        
        logging.debug(f"common_keys count: {len(common_keys)}")
        
        # ペアリストを作成
        pairs = []
        for race_key in common_keys:
            odds_key = race_key.replace("race_data_", "odds_data_")
            pairs.append((race_map[race_key], odds_map[odds_key]))
        
        print(f"[DEBUG] Final pairs count: {len(pairs)}")
        if pairs:
            print(f"[DEBUG] Sample pair: {pairs[0]}")
        logging.debug(f"pairs count: {len(pairs)}")
        if pairs:
            logging.debug(f"sample pair: {pairs[0]}")
        
        # キャッシュを無効化（年月フィルタの確実な動作のため）
        print(f"[DEBUG] Cache disabled, not saving pairs to cache")
        
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
        print(f"[KyoteiEnvManager.reset] called. pairs={len(self.pairs)}")
        # 年月フィルタの確認
        if self.year_month:
            print(f"[KyoteiEnvManager.reset] year_month filter: {self.year_month}")
            # 実際のペアの年月分布を確認
            year_month_distribution = {}
            for pair in self.pairs:
                race_file = os.path.basename(pair[0])
                if race_file.startswith('race_data_'):
                    parts = race_file.split('_')
                    if len(parts) >= 3:
                        date_part = parts[2]
                        if len(date_part) >= 7:
                            year_month = date_part[:7]
                            year_month_distribution[year_month] = year_month_distribution.get(year_month, 0) + 1
            print(f"[KyoteiEnvManager.reset] actual year_month distribution: {year_month_distribution}")
        else:
            print(f"[KyoteiEnvManager.reset] no year_month filter applied")
        
        super().reset(seed=seed)
        
        # ペアが空の場合はエラー
        if not self.pairs:
            error_msg = f"No valid race-odds pairs found in {self.data_dir} with filter: {self.year_month}. Please check if data files exist."
            print(f"[KyoteiEnvManager.reset] {error_msg}")
            logging.error(error_msg)
            raise ValueError(error_msg)
        
        # 有効なレースが見つかるまで試行（無限ループ防止）
        max_attempts = 50  # 試行回数を増やす
        attempted_pairs = set()  # 既に試行したペアを記録
        
        # 年月フィルタが設定されている場合、フィルタに合致するペアのみを使用
        if self.year_month:
            filtered_pairs = []
            for pair in self.pairs:
                race_file = os.path.basename(pair[0])
                if self._matches_year_month(race_file, self.year_month):
                    filtered_pairs.append(pair)
            if filtered_pairs:
                available_pairs = filtered_pairs
                print(f"[KyoteiEnvManager.reset] Using {len(filtered_pairs)} pairs filtered by year_month: {self.year_month}")
            else:
                print(f"[KyoteiEnvManager.reset] No pairs match year_month filter: {self.year_month}, using all pairs")
                available_pairs = self.pairs
        else:
            available_pairs = self.pairs
        
        for attempt in range(max_attempts):
            try:
                # ランダムに1レース選択（未試行のペアから）
                current_available_pairs = [pair for pair in available_pairs if pair not in attempted_pairs]
                if not current_available_pairs:
                    # すべてのペアを試行した場合は最初からやり直し
                    attempted_pairs.clear()
                    current_available_pairs = available_pairs
                
                race_path, odds_path = random.choice(current_available_pairs)
                attempted_pairs.add((race_path, odds_path))
                
                print(f"[KyoteiEnvManager.reset] attempt {attempt+1}: race={race_path}, odds={odds_path}")
                logging.debug(f"Selected race: {race_path}")
                logging.debug(f"Selected odds: {odds_path}")
                
                self.env = KyoteiEnv(race_data_path=race_path, odds_data_path=odds_path, bet_amount=self.bet_amount)
                return self.env.reset()
            except ValueError as e:
                print(f"[KyoteiEnvManager.reset] attempt {attempt+1} failed: {e}")
                logging.info(f"Attempt {attempt + 1}: Skipping invalid race data: {e}")
                if attempt == max_attempts - 1:
                    # 最後の試行でも失敗した場合は、デフォルトの着順で強制実行
                    print(f"[KyoteiEnvManager.reset] All attempts failed, using fallback data")
                    logging.warning(f"All attempts failed, using fallback data")
                    self.env = KyoteiEnv(race_data_path=race_path, odds_data_path=odds_path, bet_amount=self.bet_amount)
                    # 強制的にデフォルト値を設定
                    self.env.arrival_tuple = (1, 2, 3)
                    return self.env.state, {}
        
        # 万が一の場合のフォールバック
        race_path, odds_path = random.choice(self.pairs)
        print(f"[KyoteiEnvManager.reset] fallback: race={race_path}, odds={odds_path}")
        self.env = KyoteiEnv(race_data_path=race_path, odds_data_path=odds_path, bet_amount=self.bet_amount)
        self.env.arrival_tuple = (1, 2, 3)
        return self.env.state, {}

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
        return gym.spaces.Box(low=0, high=1, shape=(192,), dtype=np.float32) 