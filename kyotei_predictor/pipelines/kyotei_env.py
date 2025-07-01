import gymnasium as gym
import numpy as np
import json
from itertools import permutations
from typing import Tuple

class KyoteiEnv(gym.Env):
    """
    競艇レース用の強化学習環境（雛形）。
    状態・行動・報酬設計は今後拡張予定。
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self, config=None):
        super().__init__()
        self.config = config or {}
        # 状態空間: 仮に6艇の簡易数値ベクトル
        self.observation_space = gym.spaces.Box(low=0, high=1, shape=(6,), dtype=np.float32)
        # 行動空間: 仮に6艇のうち1つを選ぶ（単勝予想の例）
        self.action_space = gym.spaces.Discrete(6)
        self.state = None
        self.current_step = 0
        self.max_steps = self.config.get('max_steps', 10)

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.current_step = 0
        # 状態をランダム初期化（今後: レースデータから生成）
        self.state = np.random.rand(6).astype(np.float32)
        info = {}
        return self.state, info

    def step(self, action):
        # ダミー報酬: actionが0なら+1, それ以外は0
        reward = 1.0 if action == 0 else 0.0
        self.current_step += 1
        terminated = self.current_step >= self.max_steps
        truncated = False
        info = {}
        # 状態遷移（今後: レース進行に応じて更新）
        self.state = np.random.rand(6).astype(np.float32)
        return self.state, reward, terminated, truncated, info

    def render(self, mode="human"):
        print(f"Step: {self.current_step}, State: {self.state}")

    def close(self):
        pass

# --- サンプル: 1レース分の状態ベクトル生成関数 ---
def vectorize_race_state(race_data_path, odds_data_path):
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
    for entry in race['race_entries']:
        pit = (entry['pit_number'] - 1) / 5  # 1-6→0-1
        rating = rating_map.get(entry['racer']['current_rating'], [0,0,0,0])
        perf_all = entry['performance']['rate_in_all_stadium'] / 10 if entry['performance']['rate_in_all_stadium'] else 0
        perf_local = entry['performance']['rate_in_event_going_stadium'] / 10 if entry['performance']['rate_in_event_going_stadium'] else 0
        boat2 = entry['boat']['quinella_rate'] / 100 if entry['boat']['quinella_rate'] else 0
        boat3 = entry['boat']['trio_rate'] / 100 if entry['boat']['trio_rate'] else 0
        motor2 = entry['motor']['quinella_rate'] / 100 if entry['motor']['quinella_rate'] else 0
        motor3 = entry['motor']['trio_rate'] / 100 if entry['motor']['trio_rate'] else 0
        vec = [pit] + rating + [perf_all, perf_local, boat2, boat3, motor2, motor3]
        boats.append(vec)
    boats = np.array(boats)  # shape: (6, 特徴量数)

    # 3. レース全体特徴量
    stadiums = ['KIRYU','TODA','EDOGAWA']  # 必要に応じて拡張
    stadium_onehot = [1 if race['race_info']['stadium']==s else 0 for s in stadiums]
    race_num = (race['race_info']['race_number']-1)/11
    laps = (race['race_info']['number_of_laps']-1)/4 if 'number_of_laps' in race['race_info'] else 0
    is_fixed = 1 if race['race_info'].get('is_course_fixed') else 0
    race_feat = stadium_onehot + [race_num, laps, is_fixed]

    # 4. オッズ特徴量（3連単120通り, log+minmax）
    trifecta_list = list(permutations(range(1,7), 3))  # 1-indexed
    odds_map = {tuple(o['betting_numbers']): o['ratio'] for o in odds['odds_data']}
    odds_vec = [np.log(odds_map.get(t, 1)+1) for t in trifecta_list]  # log(odds+1)
    odds_min, odds_max = min(odds_vec), max(odds_vec)
    odds_vec = [(o-odds_min)/(odds_max-odds_min) if odds_max>odds_min else 0 for o in odds_vec]

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