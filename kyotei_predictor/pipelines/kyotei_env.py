import gymnasium as gym
import numpy as np
import json
from itertools import permutations
from typing import Tuple
import glob
import random
import os

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
        super().reset(seed=seed)
        # レースデータ・oddsデータ読み込み
        assert self.race_data_path and self.odds_data_path, "race_data_path, odds_data_pathを指定してください"
        with open(self.race_data_path, encoding='utf-8') as f:
            race = json.load(f)
        with open(self.odds_data_path, encoding='utf-8') as f:
            odds = json.load(f)
        self.odds_data = odds['odds_data']
        
        # 正解着順（1-3着）の品質チェック
        valid_records = [r for r in race['race_records'] if r.get('arrival') is not None]
        if len(valid_records) < 3:
            print(f"[WARNING] Skipping race with insufficient valid records: {len(valid_records)} < 3")
            # 不完全なデータの場合は例外を発生させてスキップ
            raise ValueError(f"Insufficient valid records: {len(valid_records)} < 3")
        
        records = sorted(valid_records, key=lambda x: x['arrival'])
        self.arrival_tuple = tuple(r['pit_number'] for r in records[:3])
        
        # 着順タプルの妥当性チェック
        if len(self.arrival_tuple) != 3:
            print(f"[WARNING] Skipping race with invalid arrival_tuple: {self.arrival_tuple}")
            raise ValueError(f"Invalid arrival_tuple: {self.arrival_tuple}, length: {len(self.arrival_tuple)}")
        
        # 状態ベクトル生成
        self.state = vectorize_race_state(self.race_data_path, self.odds_data_path)
        self.terminated = False
        info = {}
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
        print(f"State: {self.state}")

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
    
    段階的報酬設計:
    - 的中時: 払戻金-賭け金
    - 2着的中時: -10（1着、2着が正解）
    - 1着的中時: -50（1着のみ正解）
    - 不的中時: -100（全く的中なし）
    """
    # 着順タプルの妥当性チェック
    if len(arrival_tuple) != 3:
        print(f"[WARNING] Invalid arrival_tuple: {arrival_tuple}, length: {len(arrival_tuple)}")
        return -100  # 不正な着順の場合は最大ペナルティ
    
    trifecta = action_to_trifecta(action)
    
    # 的中判定
    is_win = trifecta == arrival_tuple
    
    if is_win:
        # 的中時: 払戻金-賭け金
        odds_map = {tuple(o['betting_numbers']): o['ratio'] for o in odds_data}
        odds = odds_map.get(trifecta, 0)
        payout = odds * bet_amount
        reward = payout - bet_amount
    else:
        # 部分的中の判定
        first_hit = trifecta[0] == arrival_tuple[0]  # 1着的中
        second_hit = trifecta[1] == arrival_tuple[1]  # 2着的中
        
        if first_hit and second_hit:
            # 2着的中: 1着、2着が正解
            reward = -10
        elif first_hit:
            # 1着的中: 1着のみ正解
            reward = -50
        else:
            # 不的中: 全く的中なし
            reward = -100
    
    return reward

class KyoteiEnvManager(gym.Env):
    """
    複数レースデータを使ったエピソード切替用ラッパー。
    dataディレクトリからrace_data/odds_dataのペア一覧を作成し、resetごとにランダムなレースを選択してKyoteiEnvを初期化する。
    gym.Envを継承してstable-baselines3との互換性を確保。
    """
    metadata = {"render_modes": ["human"]}
    
    def __init__(self, data_dir: str = "../data", bet_amount: int = 100):
        super().__init__()
        self.data_dir = data_dir
        self.bet_amount = bet_amount
        self.pairs = self._find_race_odds_pairs()
        self.env = None

    def _find_race_odds_pairs(self) -> list:
        print("[DEBUG] data_dir:", self.data_dir)
        print("[DEBUG] abspath(data_dir):", os.path.abspath(self.data_dir))
        race_files = glob.glob(os.path.join(self.data_dir, "race_data_*.json"))
        odds_files = glob.glob(os.path.join(self.data_dir, "odds_data_*.json"))
        print("[DEBUG] race_files:", race_files)
        print("[DEBUG] odds_files:", odds_files)
        
        # キー: (date, stadium, race_number)
        def parse_key(path, prefix):
            fname = os.path.basename(path)
            parts = fname.replace(prefix, "").replace(".json", "").split("_")
            
            # 日付部分を統合（例: 2024-06-15 → 20240615）
            if len(parts) >= 3:
                # 日付部分を統合
                date_parts = parts[0:3]  # 年-月-日
                date = "".join(date_parts).replace("-", "")
                
                # スタジアムとレース番号
                if len(parts) >= 5:
                    stadium = parts[3]
                    rno = parts[4]
                elif len(parts) >= 4:
                    stadium = parts[3]
                    rno = "1"
                else:
                    stadium = "UNKNOWN"
                    rno = "1"
            else:
                date = parts[0] if parts else "UNKNOWN"
                stadium = parts[1] if len(parts) > 1 else "UNKNOWN"
                rno = parts[2] if len(parts) > 2 else "1"
            
            rno = rno.replace('R', '')  # 'R2'→'2' のようにRを除去
            try:
                rno_int = int(rno)
            except ValueError:
                rno_int = 1  # デフォルト値
            
            return (date, stadium, rno_int)
        
        race_map = {parse_key(f, "race_data_"): f for f in race_files}
        odds_map = {parse_key(f, "odds_data_"): f for f in odds_files}
        
        # デバッグ出力
        print("[DEBUG] race_map.keys():", list(race_map.keys()))
        print("[DEBUG] odds_map.keys():", list(odds_map.keys()))
        # ペアが揃っているものだけ
        keys = set(race_map.keys()) & set(odds_map.keys())
        print("[DEBUG] ペアが揃ったkeys:", list(keys))
        pairs = [(race_map[k], odds_map[k]) for k in sorted(keys)]
        print("[DEBUG] ペアリスト:", pairs)
        return pairs

    def reset(self, *, seed=None, options=None) -> Tuple[np.ndarray | None, dict]:
        super().reset(seed=seed)
        # 有効なレースが見つかるまで試行
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                # ランダムに1レース選択
                race_path, odds_path = random.choice(self.pairs)
                self.env = KyoteiEnv(race_data_path=race_path, odds_data_path=odds_path, bet_amount=self.bet_amount)
                return self.env.reset()
            except ValueError as e:
                print(f"[INFO] Attempt {attempt + 1}: Skipping invalid race data: {e}")
                if attempt == max_attempts - 1:
                    # 最後の試行でも失敗した場合は、デフォルトの着順で強制実行
                    print("[WARNING] All attempts failed, using fallback data")
                    self.env = KyoteiEnv(race_data_path=race_path, odds_data_path=odds_path, bet_amount=self.bet_amount)
                    # 強制的にデフォルト値を設定
                    self.env.arrival_tuple = (1, 2, 3)
                    return self.env.state, {}
        
        # 万が一の場合のフォールバック
        race_path, odds_path = random.choice(self.pairs)
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