"""
共通状態ベクトル生成モジュール

学習・予測の両方で同一の状態定義を使う。
オッズは状態に含めず、回収率計算は予測後に別途行う。
"""
from __future__ import annotations

import numpy as np
from itertools import permutations
from typing import Dict, Any, List, Optional

# 会場順序は venue_mapping の get_all_stadiums() に合わせる（実行時取得で一貫性を保つ）
_FALLBACK_STADIUM_NAMES = [
    "KIRYU", "TODA", "EDOGAWA", "HEIWAJIMA", "TAMAGAWA", "HAMANAKO",
    "GAMAGORI", "TOKONAME", "TSU", "MIKUNI", "BIWAKO", "WAKAMATSU",
    "ASHIYA", "SUMINOE", "AMAGASAKI", "NARUTO", "MARUGAME", "KOJIMA",
    "MIYAJIMA", "FUKUOKA", "KARATSU", "OMURA",
]

# 会場リストは初回取得時にキャッシュし、次元の一貫性を保つ
_stadium_names_cache: Optional[List[str]] = None


def _get_stadium_names() -> List[str]:
    """会場名リストを venue_mapping から取得（初回のみ取得してキャッシュ）。"""
    global _stadium_names_cache
    if _stadium_names_cache is not None:
        return _stadium_names_cache
    try:
        from kyotei_predictor.utils.venue_mapping import VenueMapper
        out: List[str] = []
        for _s in VenueMapper.get_all_stadiums():
            info = VenueMapper.get_stadium_info(_s)
            out.append(info["name"] if info else getattr(_s, "name", str(_s)))
        _stadium_names_cache = out if out else _FALLBACK_STADIUM_NAMES
    except Exception:
        _stadium_names_cache = _FALLBACK_STADIUM_NAMES
    return _stadium_names_cache


# 次元: 艇48 + 会場one-hot(len) + race_num(1) + laps(1) + is_fixed(1)
NUM_BOAT_FEATURES = 48   # 6艇 × 8
# NUM_RACE_FEATURES / STATE_DIM は get_state_dim() で動的に算出

# 艇1あたり8次元: pit(1) + rating(1) + perf_all, perf_local, boat2, boat3, motor2, motor3(6)
RATING_MAP = {"A1": 1.0, "A2": 0.75, "B1": 0.5, "B2": 0.25}  # 1次元に圧縮（元はone-hot 4）
TRIFECTA_ORDER = list(permutations(range(1, 7), 3))  # 1-indexed, 120通り


def build_race_state_vector(
    race_data: Dict[str, Any],
    odds_data: Optional[Dict[str, Any]] = None,
) -> np.ndarray:
    """
    レースデータから状態ベクトルを生成する（学習・予測共通）。

    オッズは状態に含めない。回収率・期待値は予測後にオッズを使って計算する。
    次元: STATE_DIM（艇48 + レース特徴 会場数+3）。

    Args:
        race_data: race_info, race_entries を持つ辞書（race_records は不要）。
        odds_data: 未使用（互換用に受け取るが無視する）。

    Returns:
        shape=(get_state_dim(),) の float32 配列。値は 0〜1 付近に正規化。
    """
    # 次元の一貫性のため、先に get_state_dim() で会場リストを確定させる
    expected_dim = get_state_dim()
    stadium_names = _get_stadium_names()
    # 1. 艇特徴 6×8 = 48
    if "race_entries" in race_data:
        entries = race_data["race_entries"]
    else:
        entries = []
        for r in race_data.get("race_records", []):
            entries.append({
                "pit_number": r.get("pit_number", 1),
                "racer": {"current_rating": "B1"},
                "performance": {"rate_in_all_stadium": 5.0, "rate_in_event_going_stadium": 5.0},
                "boat": {"quinella_rate": 50.0, "trio_rate": 50.0},
                "motor": {"quinella_rate": 50.0, "trio_rate": 50.0},
            })

    boats = []
    for entry in entries:
        pit = (entry["pit_number"] - 1) / 5.0
        rating = RATING_MAP.get(entry.get("racer", {}).get("current_rating"), 0.0)
        if not isinstance(rating, (int, float)):
            rating = 0.0
        perf_all = entry.get("performance", {}).get("rate_in_all_stadium")
        perf_local = entry.get("performance", {}).get("rate_in_event_going_stadium")
        boat2 = entry.get("boat", {}).get("quinella_rate")
        boat3 = entry.get("boat", {}).get("trio_rate")
        motor2 = entry.get("motor", {}).get("quinella_rate")
        motor3 = entry.get("motor", {}).get("trio_rate")
        perf_all = perf_all / 10.0 if perf_all is not None else 0.0
        perf_local = perf_local / 10.0 if perf_local is not None else 0.0
        boat2 = boat2 / 100.0 if boat2 is not None else 0.0
        boat3 = boat3 / 100.0 if boat3 is not None else 0.0
        motor2 = motor2 / 100.0 if motor2 is not None else 0.0
        motor3 = motor3 / 100.0 if motor3 is not None else 0.0
        vec = [pit, rating, perf_all, perf_local, boat2, boat3, motor2, motor3]  # 8次元/艇
        boats.append(vec)

    while len(boats) < 6:
        boats.append([0.0] * 8)
    boats = np.array(boats[:6], dtype=np.float32).flatten()  # 48

    # 2. レース特徴: 会場 one-hot + race_num + laps + is_fixed
    ri = race_data.get("race_info", {})
    stadium = ri.get("stadium", "")
    stadium_onehot = [1.0 if stadium == s else 0.0 for s in stadium_names]
    race_num = (ri.get("race_number", 1) - 1) / 11.0
    laps = (ri.get("number_of_laps", 3) - 1) / 4.0 if ri.get("number_of_laps") is not None else 0.0
    is_fixed = 1.0 if ri.get("is_course_fixed") else 0.0
    race_feat = np.array(stadium_onehot + [race_num, laps, is_fixed], dtype=np.float32)

    state = np.concatenate([boats, race_feat])
    assert state.shape == (expected_dim,), f"state shape {state.shape} != ({expected_dim},)"
    return state


def get_state_dim() -> int:
    """状態ベクトルの次元を返す（艇48 + 会場数 + 3）。"""
    return NUM_BOAT_FEATURES + len(_get_stadium_names()) + 3


def get_stadium_names_order() -> List[str]:
    """会場 one-hot の順序（状態ベクトル内の並び）を返す。"""
    return list(_get_stadium_names())


# 定数エイリアス（get_state_dim() と一致）
STATE_DIM = get_state_dim()
NUM_RACE_FEATURES = len(_get_stadium_names()) + 3
