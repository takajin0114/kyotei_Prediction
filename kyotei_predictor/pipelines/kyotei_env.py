#!/usr/bin/env python3
"""
競艇予測のための強化学習環境
"""

import os
import sys
import json
import logging
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path
import re

# プロジェクトルートを動的に取得
def get_project_root() -> Path:
    """プロジェクトルートを動的に検出"""
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent
    
    # Google Colab環境の検出
    if str(project_root).startswith('/content/'):
        return Path('/content/kyotei_Prediction')
    
    return project_root

PROJECT_ROOT = get_project_root()

# プロジェクトルートをパスに追加
sys.path.append(str(PROJECT_ROOT))

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KyoteiEnv(gym.Env):
    """
    競艇予測のための強化学習環境
    """
    
    def __init__(self, data_dir: str = None, bet_amount: int = 100, race_pairs: list = None):
        """
        初期化
        
        Args:
            data_dir: データディレクトリのパス
            bet_amount: ベット金額
            race_pairs: 事前に検索されたレースペア（KyoteiEnvManagerから渡される）
        """
        super().__init__()
        
        # データディレクトリの設定
        if data_dir is None:
            self.data_dir = PROJECT_ROOT / "kyotei_predictor" / "data" / "raw"
        else:
            self.data_dir = Path(data_dir)
        
        self.bet_amount = bet_amount
        
        # 行動空間: 6艇の3着予想 (6P3 = 120通り)
        # stable-baselines3との互換性のためDiscrete(120)を使用
        self.action_space = spaces.Discrete(120)
        
        # 観測空間: 各艇の特徴量 (6艇 × 特徴量数)
        # 特徴量: 選手名, 年齢, 出身地, 級別, 全国勝率, 当地勝率, モーター番号, ボート番号
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(6, 8), dtype=np.float32
        )
        
        # 環境状態
        self.current_race_data = None
        self.current_race_index = 0
        self.race_files = []
        
        # race_pairsが渡された場合はそれを使用、そうでなければ従来通り読み込み
        if race_pairs is not None:
            # race_pairsからレースファイルパスのみを抽出
            self.race_files = [Path(pair[0]) for pair in race_pairs]
            logger.info(f"KyoteiEnv初期化完了（事前検索）: {len(self.race_files)}レース, ベット金額: {bet_amount}円")
        else:
            self._load_race_files()
            logger.info(f"KyoteiEnv初期化完了: {len(self.race_files)}レース, ベット金額: {bet_amount}円")
    
    def _load_race_files(self):
        """レースファイルの読み込み（改善版）"""
        try:
            if not self.data_dir.exists():
                logger.warning(f"データディレクトリが存在しません: {self.data_dir}")
                self.race_files = []
                return
            
            # 月別サブディレクトリからレースファイルを検索
            race_files = []
            for month_dir in self.data_dir.iterdir():
                if month_dir.is_dir() and month_dir.name.startswith('2024-'):
                    # 月別ディレクトリ内のrace_dataファイルを検索
                    month_race_files = list(month_dir.glob("race_data_*.json"))
                    race_files.extend(month_race_files)
            

            
            self.race_files = race_files
            
            logger.info(f"レースファイル読み込み完了: {len(self.race_files)}件")
            
        except Exception as e:
            logger.error(f"レースファイル読み込みエラー: {e}")
            self.race_files = []
    
    def _load_race_data(self, file_path: Path) -> Optional[Dict]:
        """レースデータの読み込み"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error(f"レースデータ読み込みエラー {file_path}: {e}")
            return None
    
    def _extract_features(self, race_data: Dict) -> np.ndarray:
        """レースデータから特徴量を抽出"""
        try:
            features = np.zeros((6, 8), dtype=np.float32)
            
            if 'race_entries' not in race_data:
                logger.warning("race_entriesが見つかりません")
                return features
            
            entries = race_data['race_entries']
            
            for i, entry in enumerate(entries[:6]):  # 最大6艇
                if i >= 6:
                    break
                
                # 特徴量の正規化
                features[i, 0] = self._normalize_name(entry.get('racer', {}).get('name', ''))
                features[i, 1] = self._normalize_age(entry.get('racer', {}).get('age', 0))
                features[i, 2] = self._normalize_prefecture(entry.get('racer', {}).get('prefecture', ''))
                features[i, 3] = self._normalize_grade(entry.get('racer', {}).get('grade', ''))
                features[i, 4] = self._normalize_rate(entry.get('performance', {}).get('rate_in_all_stadium', 0))
                features[i, 5] = self._normalize_rate(entry.get('performance', {}).get('rate_in_event_going_stadium', 0))
                features[i, 6] = self._normalize_number(entry.get('motor', {}).get('number', 0))
                features[i, 7] = self._normalize_number(entry.get('boat', {}).get('number', 0))
            
            return features
            
        except Exception as e:
            logger.error(f"特徴量抽出エラー: {e}")
            return np.zeros((6, 8), dtype=np.float32)
    
    def _normalize_name(self, name: str) -> float:
        """選手名の正規化"""
        if not name:
            return 0.0
        # 名前の長さを正規化
        return min(len(name) / 10.0, 1.0)
    
    def _normalize_age(self, age: int) -> float:
        """年齢の正規化"""
        if age <= 0:
            return 0.0
        return min(age / 60.0, 1.0)
    
    def _normalize_prefecture(self, prefecture: str) -> float:
        """出身地の正規化"""
        if not prefecture:
            return 0.0
        # 都道府県コードを数値化
        prefecture_codes = {
            '北海道': 1, '青森県': 2, '岩手県': 3, '宮城県': 4, '秋田県': 5,
            '山形県': 6, '福島県': 7, '茨城県': 8, '栃木県': 9, '群馬県': 10,
            '埼玉県': 11, '千葉県': 12, '東京都': 13, '神奈川県': 14, '新潟県': 15,
            '富山県': 16, '石川県': 17, '福井県': 18, '山梨県': 19, '長野県': 20,
            '岐阜県': 21, '静岡県': 22, '愛知県': 23, '三重県': 24, '滋賀県': 25,
            '京都府': 26, '大阪府': 27, '兵庫県': 28, '奈良県': 29, '和歌山県': 30,
            '鳥取県': 31, '島根県': 32, '岡山県': 33, '広島県': 34, '山口県': 35,
            '徳島県': 36, '香川県': 37, '愛媛県': 38, '高知県': 39, '福岡県': 40,
            '佐賀県': 41, '長崎県': 42, '熊本県': 43, '大分県': 44, '宮崎県': 45,
            '鹿児島県': 46, '沖縄県': 47
        }
        code = prefecture_codes.get(prefecture, 0)
        return code / 47.0
    
    def _normalize_grade(self, grade: str) -> float:
        """級別の正規化"""
        grade_values = {
            'A1': 1.0, 'A2': 0.9, 'B1': 0.8, 'B2': 0.7,
            'C1': 0.6, 'C2': 0.5, 'D1': 0.4, 'D2': 0.3
        }
        return grade_values.get(grade, 0.0)
    
    def _normalize_rate(self, rate: float) -> float:
        """勝率の正規化"""
        if rate <= 0:
            return 0.0
        return min(rate / 100.0, 1.0)
    
    def _normalize_number(self, number: int) -> float:
        """番号の正規化"""
        if number <= 0:
            return 0.0
        return min(number / 100.0, 1.0)
    
    def _action_to_trifecta(self, action: int) -> Tuple[int, int, int]:
        """行動を3着予想に変換"""
        # 120通りの組み合わせを生成（全組み合わせ）
        combinations = []
        for i in range(1, 7):
            for j in range(1, 7):
                for k in range(1, 7):
                    if i != j and j != k and i != k:
                        combinations.append((i, j, k))
                        if len(combinations) >= 120:  # 全組み合わせ
                            break
            if len(combinations) >= 120:
                break
        
        if 0 <= action < len(combinations):
            return combinations[action]
        else:
            return (1, 2, 3)  # デフォルト
    
    def _get_race_result(self, race_data: Dict) -> Optional[Tuple[int, int, int]]:
        """レース結果を取得"""
        try:
            if 'race_records' not in race_data:
                return None
            
            records = race_data['race_records']
            if len(records) < 3:
                return None
            
            # 1着、2着、3着の艇番を取得
            first = records[0]['pit_number']
            second = records[1]['pit_number']
            third = records[2]['pit_number']
            
            return (first, second, third)
            
        except Exception as e:
            logger.error(f"レース結果取得エラー: {e}")
            return None
    
    def reset(self, seed: Optional[int] = None, options: Optional[Dict] = None) -> Tuple[np.ndarray, Dict]:
        """環境をリセット（改善版）"""
        super().reset(seed=seed)
        
        if not self.race_files:
            logger.warning("レースファイルがありません")
            return np.zeros((6, 8), dtype=np.float32), {}
        
        # エピソード開始：最初のレースから開始
        self.current_race_index = 0
        race_file = self.race_files[self.current_race_index]
        
        # レースデータを読み込み
        self.current_race_data = self._load_race_data(race_file)
        
        if self.current_race_data is None:
            logger.warning(f"レースデータの読み込みに失敗: {race_file}")
            return np.zeros((6, 8), dtype=np.float32), {}
        
        # 特徴量を抽出
        features = self._extract_features(self.current_race_data)
        
        logger.debug(f"環境リセット: {race_file.name} (エピソード開始)")
        return features, {'episode_start': True, 'total_races': len(self.race_files)}
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """環境を1ステップ進める（改善版）"""
        if self.current_race_data is None:
            return np.zeros((6, 8), dtype=np.float32), 0.0, True, False, {}
        
        # 行動を3着予想に変換
        predicted_trifecta = self._action_to_trifecta(action)
        
        # 実際の結果を取得
        actual_result = self._get_race_result(self.current_race_data)
        
        # 的中判定とタイプを詳細に計算
        hit_info = self._calculate_hit_info(predicted_trifecta, actual_result)
        
        # 報酬を計算
        reward = self._calculate_reward(predicted_trifecta, actual_result)
        
        # 次のレースに進む
        self.current_race_index += 1
        
        # エピソード終了条件：すべてのレースを処理した場合
        terminated = self.current_race_index >= len(self.race_files)
        truncated = False
        
        # 次のレースの観測を準備
        if not terminated:
            # 次のレースデータを読み込み
            next_race_file = self.race_files[self.current_race_index]
            self.current_race_data = self._load_race_data(next_race_file)
            next_features = self._extract_features(self.current_race_data)
        else:
            # エピソード終了時はゼロベクトル
            next_features = np.zeros((6, 8), dtype=np.float32)
        
        info = {
            'predicted': predicted_trifecta,
            'actual': actual_result,
            'hit': hit_info['hit'],
            'hit_type': hit_info['hit_type'],
            'bet': 1,  # 1レースにつき1ベット
            'reward': reward,
            'predicted_trifecta': predicted_trifecta,  # 後方互換性
            'actual_result': actual_result,  # 後方互換性
            'race_index': self.current_race_index,
            'total_races': len(self.race_files),
            'episode_ended': terminated
        }
        
        return next_features, reward, terminated, truncated, info
    
    def _calculate_hit_info(self, predicted: Tuple[int, int, int], actual: Optional[Tuple[int, int, int]]) -> Dict[str, Any]:
        """的中情報を詳細に計算"""
        if actual is None:
            return {'hit': 0, 'hit_type': 'unknown'}
        
        # 完全一致の場合
        if predicted == actual:
            return {'hit': 1, 'hit_type': 'win'}
        
        # 部分一致の場合
        correct_positions = 0
        for i in range(3):
            if predicted[i] == actual[i]:
                correct_positions += 1
        
        if correct_positions == 2:
            return {'hit': 1, 'hit_type': 'first_second'}
        elif correct_positions == 1:
            return {'hit': 1, 'hit_type': 'first_only'}
        else:
            return {'hit': 0, 'hit_type': 'miss'}
    
    def _calculate_reward(self, predicted: Tuple[int, int, int], actual: Optional[Tuple[int, int, int]]) -> float:
        """報酬を計算（改善版）"""
        if actual is None:
            return 0.0
        
        # 完全一致の場合（最高報酬）
        if predicted == actual:
            return 100.0
        
        # 部分一致の場合（段階的報酬）
        correct_positions = 0
        for i in range(3):
            if predicted[i] == actual[i]:
                correct_positions += 1
        
        # より詳細な段階的報酬
        if correct_positions == 2:
            # 2着的中の場合、位置も考慮
            if predicted[0] == actual[0] and predicted[1] == actual[1]:
                return 25.0  # 1着2着的中
            elif predicted[0] == actual[0] and predicted[2] == actual[2]:
                return 20.0  # 1着3着的中
            elif predicted[1] == actual[1] and predicted[2] == actual[2]:
                return 15.0  # 2着3着的中
            else:
                return 10.0  # その他の2着的中
        elif correct_positions == 1:
            # 1着的中の場合、位置も考慮
            if predicted[0] == actual[0]:
                return 5.0   # 1着的中
            elif predicted[1] == actual[1]:
                return 3.0   # 2着的中
            elif predicted[2] == actual[2]:
                return 1.0   # 3着的中
            else:
                return 1.0   # その他の1着的中
        else:
            # 不的中の場合、小さな負の報酬
            return -0.1

def calc_trifecta_reward(action: int, arrival_tuple: Tuple[int,int,int], odds_data: list, bet_amount: int = 100) -> float:
    """
    3連単の報酬を計算
    
    Args:
        action: 行動（0-119の整数）
        arrival_tuple: 実際の着順 (1着, 2着, 3着)
        odds_data: オッズデータ
        bet_amount: ベット金額
        
    Returns:
        報酬（利益）
    """
    # 行動を3着予想に変換
    combinations = []
    for i in range(1, 7):
        for j in range(1, 7):
            for k in range(1, 7):
                if i != j and j != k and i != k:
                    combinations.append((i, j, k))
                    if len(combinations) >= 120:  # 全組み合わせ
                        break
        if len(combinations) >= 120:
            break
    
    if 0 <= action < len(combinations):
        predicted = combinations[action]
    else:
        predicted = (1, 2, 3)
    
    # 予想が正しい場合
    if predicted == arrival_tuple:
        # オッズデータから該当するオッズを検索
        for odds in odds_data:
            if (odds.get('first') == predicted[0] and 
                odds.get('second') == predicted[1] and 
                odds.get('third') == predicted[2]):
                odds_value = odds.get('odds', 0)
                reward = (odds_value * bet_amount) - bet_amount
                return reward
        
        # オッズが見つからない場合はデフォルト報酬
        reward = 100
    else:
        reward = -100
    return reward

class KyoteiEnvManager(gym.Env):
    """
    複数レースデータを使ったエピソード切替用ラッパー。
    dataディレクトリからrace_data/odds_dataのペア一覧を作成し、resetごとにランダムなレースを選択してKyoteiEnvを初期化する。
    gym.Envを継承してstable-baselines3との互換性を確保。
    """
    metadata = {"render_modes": ["human"]}
    
    def __init__(self, data_dir: str = None, bet_amount: int = 100, pairs: list = None):
        super().__init__()
        logging.debug(f"[KyoteiEnvManager.__init__] received data_dir: {data_dir}")
        
        # データディレクトリの設定
        if data_dir is None:
            self.data_dir = PROJECT_ROOT / "kyotei_predictor" / "data" / "raw"
        else:
            self.data_dir = Path(data_dir)
        
        logging.debug(f"[KyoteiEnvManager.__init__] self.data_dir set to: {self.data_dir}")
        self.bet_amount = bet_amount
        
        # 事前にペア情報が渡された場合はそれを使用、そうでなければ検索
        if pairs is not None:
            self.pairs = pairs
            self._pairs_loaded = True
            logging.debug("Using pre-loaded pairs")
        else:
            self._pairs_loaded = False
            self.pairs = self._find_race_odds_pairs()
        
        self.env = None

    def _find_race_odds_pairs(self) -> list:
        # 既にペア情報が設定されている場合はスキップ
        if hasattr(self, '_pairs_loaded') and self._pairs_loaded:
            logging.debug("Skipping _find_race_odds_pairs - pairs already loaded")
            return self.pairs
        
        logging.debug(f"data_dir: {self.data_dir}")
        logging.debug(f"abspath(data_dir): {os.path.abspath(self.data_dir)}")
        
        # 効率的な検索のため、特定のディレクトリのみを対象
        race_pattern = re.compile(r'race_data_(\d{4}-\d{2}-\d{2})_([A-Z0-9]+)_R\d+\.json')
        odds_pattern = re.compile(r'odds_data_(\d{4}-\d{2}-\d{2})_([A-Z0-9]+)_R\d+\.json')
        
        pairs = []
        
        # 直接ファイルを検索（2024-01ディレクトリ内のファイル）
        race_files = []
        odds_files = []
        
        # デバッグ用ログ
        logging.info(f"Searching in directory: {self.data_dir}")
        
        for file in self.data_dir.iterdir():
            if file.is_file():
                filename = file.name
                if race_pattern.match(filename):
                    race_files.append(str(file))
                elif odds_pattern.match(filename):
                    odds_files.append(str(file))
        
        logging.info(f"Found race files: {len(race_files)}")
        logging.info(f"Found odds files: {len(odds_files)}")
        
        # レースファイルとオッズファイルをマッチング
        for race_file in race_files:
                race_match = race_pattern.match(os.path.basename(race_file))
                if race_match:
                    date_str, stadium = race_match.groups()
                    
                    # 対応するオッズファイルを検索
                    for odds_file in odds_files:
                        odds_match = odds_pattern.match(os.path.basename(odds_file))
                        if odds_match and odds_match.groups() == (date_str, stadium):
                            pairs.append((race_file, odds_file))
                            break
        
        # データ量制限を削除（本番環境用）
        
        logging.info(f"Found {len(pairs)} race-odds pairs")
        return pairs

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        if not self.pairs:
            logging.warning("No race-odds pairs found")
            return np.zeros((6, 8), dtype=np.float32), {}
        
        # 初回のみ環境を作成
        if self.env is None:
            self.env = KyoteiEnv(data_dir=str(self.data_dir), bet_amount=self.bet_amount, race_pairs=self.pairs)
        
        # 環境をリセット
        observation, info = self.env.reset(seed=seed)
        
        return observation, info

    def step(self, action):
        if self.env is None:
            return np.zeros((6, 8), dtype=np.float32), 0.0, True, False, {}
        
        return self.env.step(action)

    @property
    def action_space(self):
        if self.env is None:
            return spaces.Discrete(120)
        return self.env.action_space

    @property
    def observation_space(self):
        if self.env is None:
            return spaces.Box(low=0, high=1, shape=(6, 8), dtype=np.float32)
        return self.env.observation_space 