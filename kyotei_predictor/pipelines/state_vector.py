"""
共通状態ベクトル生成モジュール

学習・予測の両方で同一の状態定義を使う。
オッズは状態に含めず、回収率計算は予測後に別途行う。

feature_set は環境変数 KYOTEI_FEATURE_SET で切り替え:
- current_features: 従来の状態ベクトルのみ（KYOTEI_USE_MOTOR_WIN_PROXY=0 相当）
- extended_features: モーター勝率代理を追加（KYOTEI_USE_MOTOR_WIN_PROXY=1 相当）
- extended_features_v2: extended + venue_course/recent_form/motor_trend/relative_race_strength 系

KYOTEI_FEATURE_SET 未設定時は KYOTEI_USE_MOTOR_WIN_PROXY で後方互換。
"""
from __future__ import annotations

import os
import numpy as np
from itertools import permutations
from typing import Dict, Any, List, Optional, Tuple

# 会場順序は venue_mapping の get_all_stadiums() に合わせる（実行時取得で一貫性を保つ）
_FALLBACK_STADIUM_NAMES = [
    "KIRYU", "TODA", "EDOGAWA", "HEIWAJIMA", "TAMAGAWA", "HAMANAKO",
    "GAMAGORI", "TOKONAME", "TSU", "MIKUNI", "BIWAKO", "SUMINOE",
    "AMAGASAKI", "NARUTO", "MARUGAME", "KOJIMA", "MIYAJIMA", "TOKUYAMA",
    "SHIMONOSEKI", "WAKAMATSU", "ASHIYA", "FUKUOKA", "KARATSU", "OMURA",
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


# 次元: 艇48 + 会場one-hot(len) + race_num(1) + laps(1) + is_fixed(1) + motor_win_proxy(1)
NUM_BOAT_FEATURES = 48   # 6艇 × 8
# レース特徴: race_num(1) + laps(1) + is_fixed(1)。モーター勝率代理は +1 でオプション。
NUM_BASE_RACE_FEATURES = 3
NUM_EXTRA_RACE_FEATURES = 4  # base(3) + motor_win_proxy(1)


def _use_motor_win_proxy_feature() -> bool:
    """追加特徴量（モーター勝率代理）を使うか。デフォルトOFF。ON にするには KYOTEI_USE_MOTOR_WIN_PROXY=1 を設定。"""
    return os.environ.get("KYOTEI_USE_MOTOR_WIN_PROXY", "0") == "1"


# extended_features_v2: 6*(recent3+venue2)=30 + motor_trend 8 + relative_race_strength 7 = 45
EXTENDED_V2_EXTRA_DIM = 45


def _get_feature_set() -> str:
    """
    使用する特徴量セットを返す。
    KYOTEI_FEATURE_SET が未設定のときは KYOTEI_USE_MOTOR_WIN_PROXY で後方互換。
    """
    fs = os.environ.get("KYOTEI_FEATURE_SET", "").strip().lower()
    if fs in ("current_features", "extended_features", "extended_features_v2"):
        return fs
    if _use_motor_win_proxy_feature():
        return "extended_features"
    return "current_features"


# NUM_RACE_FEATURES / STATE_DIM は get_state_dim() で動的に算出

# 艇1あたり8次元（詳細は docs/STATE_VECTOR_AUDIT_MOTOR_BOAT.md を参照）:
#   0: pit（枠番の正規化）
#   1: rating（レーサー級別）
#   2: perf_all（全国勝率）
#   3: perf_local（当地勝率）
#   4: boat2（ボート2連率）、5: boat3（ボート3連率）
#   6: motor2（モーター2連率）、7: motor3（モーター3連率）
RATING_MAP = {"A1": 1.0, "A2": 0.75, "B1": 0.5, "B2": 0.25}  # 1次元に圧縮（元はone-hot 4）
TRIFECTA_ORDER = list(permutations(range(1, 7), 3))  # 1-indexed, 120通り


def _rank_to_01(values: List[float]) -> np.ndarray:
    """6要素のリストを順位で 0〜1 に正規化（1位=1, 6位=0）。同点は先着優先。欠損は 0.5。"""
    arr = np.array(values, dtype=np.float32)
    n = len(arr)
    for i in range(n):
        if np.isnan(arr[i]):
            arr[i] = 0.5
    order = np.argsort(np.argsort(arr)).astype(np.float32)  # 0=最下位, n-1=最上位
    if n <= 1:
        return np.ones(n, dtype=np.float32)
    return (n - 1 - order) / (n - 1)  # 最上位=1, 最下位=0


def _build_extended_v2_extras(
    race_data: Dict[str, Any],
    entries: List[Dict[str, Any]],
    stadium_names: List[str],
    racer_history_cache: Optional[List[tuple]] = None,
    race_date: Optional[str] = None,
    stadium: Optional[str] = None,
) -> np.ndarray:
    """
    extended_features_v2 用の追加ベクトル（45次元）。
    - recent_form + venue: 6艇×5 (avg_rank_norm, rate_1st, rate_top3, venue_avg_norm, venue_rate_1st) = 30
    - motor_trend: 2 + 6 = 8
    - relative_race_strength: 6 + 1 = 7
    racer_history_cache が None のときは recent/venue を 0.5/0 で埋める。
    """
    out: List[float] = []
    use_db = (
        racer_history_cache is not None
        and race_date is not None
        and stadium is not None
    )
    if use_db:
        try:
            from kyotei_predictor.pipelines.racer_history import (
                compute_recent_form,
                compute_venue_form,
            )
            for entry in (entries[:6] if len(entries) >= 6 else entries):
                reg_no = (entry.get("racer", {}).get("registration_number") or "")
                try:
                    reg_no = str(reg_no).strip()
                except Exception:
                    reg_no = ""
                r_avg, r_1st, r_top3, _ = compute_recent_form(
                    racer_history_cache, reg_no, race_date
                )
                v_avg, v_1st, _ = compute_venue_form(
                    racer_history_cache, reg_no, race_date, stadium or ""
                )
                out.extend([r_avg, r_1st, r_top3, v_avg, v_1st])
        except Exception:
            use_db = False
    if not use_db:
        for _ in range(6):
            out.extend([0.5, 0.0, 0.0, 0.5, 0.0])
    while len(out) < 30:
        out.extend([0.5, 0.0, 0.0, 0.5, 0.0])
    # motor_trend: 6艇のモーター強さ (m2+m3)/2 の平均・標準偏差・各艇の順位
    motor_vals = []
    for entry in (entries[:6] if len(entries) >= 6 else entries):
        m2 = entry.get("motor", {}).get("quinella_rate")
        m3 = entry.get("motor", {}).get("trio_rate")
        if m2 is not None and m3 is not None:
            motor_vals.append((float(m2) + float(m3)) / 200.0)
        else:
            motor_vals.append(0.5)
    while len(motor_vals) < 6:
        motor_vals.append(0.5)
    motor_arr = np.array(motor_vals[:6], dtype=np.float32)
    out.append(float(np.mean(motor_arr)))
    out.append(float(np.std(motor_arr)) if motor_arr.size > 0 else 0.0)
    out.extend(_rank_to_01(motor_vals[:6]).tolist())
    # relative_race_strength: 同一レース内の perf_all 順位 + 標準偏差
    perf_all_vals = []
    for entry in (entries[:6] if len(entries) >= 6 else entries):
        p = entry.get("performance", {}).get("rate_in_all_stadium")
        perf_all_vals.append(p / 10.0 if p is not None else 0.0)
    while len(perf_all_vals) < 6:
        perf_all_vals.append(0.0)
    perf_arr = np.array(perf_all_vals[:6], dtype=np.float32)
    out.extend(_rank_to_01(perf_all_vals[:6]).tolist())
    out.append(float(np.std(perf_arr)) if perf_arr.size > 0 else 0.0)
    return np.array(out[:EXTENDED_V2_EXTRA_DIM], dtype=np.float32)


def _build_base_state_vector(
    race_data: Dict[str, Any],
    entries: List[Dict[str, Any]],
    stadium_names: List[str],
    use_motor_proxy: bool,
) -> np.ndarray:
    """ベース状態ベクトル（艇48 + 会場one-hot + race_num + laps + is_fixed [+ motor_win_proxy]）を返す。"""
    boats = []
    for entry in entries:
        pit = (entry.get("pit_number", 1) - 1) / 5.0
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
        vec = [pit, rating, perf_all, perf_local, boat2, boat3, motor2, motor3]
        boats.append(vec)
    while len(boats) < 6:
        boats.append([0.0] * 8)
    boats_arr = np.array(boats[:6], dtype=np.float32).flatten()

    ri = race_data.get("race_info", {})
    stadium = ri.get("stadium", "")
    stadium_onehot = [1.0 if stadium == s else 0.0 for s in stadium_names]
    race_num = (ri.get("race_number", 1) - 1) / 11.0
    laps = (ri.get("number_of_laps", 3) - 1) / 4.0 if ri.get("number_of_laps") is not None else 0.0
    is_fixed = 1.0 if ri.get("is_course_fixed") else 0.0
    race_list = stadium_onehot + [race_num, laps, is_fixed]
    if use_motor_proxy:
        motor_vals = []
        for entry in entries[:6]:
            m2 = entry.get("motor", {}).get("quinella_rate")
            m3 = entry.get("motor", {}).get("trio_rate")
            if m2 is not None and m3 is not None:
                motor_vals.append((m2 / 100.0 + m3 / 100.0) / 2.0)
            else:
                motor_vals.append(0.5)
        motor_win_proxy = float(np.mean(motor_vals)) if motor_vals else 0.5
        race_list.append(motor_win_proxy)
    race_feat = np.array(race_list, dtype=np.float32)
    return np.concatenate([boats_arr, race_feat])


def build_race_state_vector(
    race_data: Dict[str, Any],
    odds_data: Optional[Dict[str, Any]] = None,
    racer_history_cache: Optional[List[tuple]] = None,
) -> np.ndarray:
    """
    レースデータから状態ベクトルを生成する（学習・予測共通）。

    オッズは状態に含めない。回収率・期待値は予測後にオッズを使って計算する。
    次元: get_state_dim()（feature_set により current / extended / extended_v2）。

    Args:
        race_data: race_info, race_entries を持つ辞書（race_records は不要）。
        odds_data: 未使用（互換用に受け取るが無視する）。
        racer_history_cache: extended_features_v2 で DB 由来の recent_form/venue を使う場合の履歴リスト。

    Returns:
        shape=(get_state_dim(),) の float32 配列。値は 0〜1 付近に正規化。
    """
    expected_dim = get_state_dim()
    stadium_names = _get_stadium_names()
    if "race_entries" in race_data:
        entries = list(race_data["race_entries"])
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

    ri = race_data.get("race_info", {})
    race_date = ri.get("date") or ri.get("race_date")
    if isinstance(race_date, str):
        pass
    else:
        race_date = None
    stadium = ri.get("stadium", "") or ""

    fs = _get_feature_set()
    if fs == "extended_features_v2":
        use_motor = True
        base = _build_base_state_vector(race_data, entries, stadium_names, use_motor_proxy=use_motor)
        extras = _build_extended_v2_extras(
            race_data,
            entries,
            stadium_names,
            racer_history_cache=racer_history_cache,
            race_date=race_date,
            stadium=stadium,
        )
        state = np.concatenate([base, extras]).astype(np.float32)
    else:
        use_motor = fs == "extended_features"
        state = _build_base_state_vector(race_data, entries, stadium_names, use_motor_proxy=use_motor)

    assert state.shape == (expected_dim,), f"state shape {state.shape} != ({expected_dim},)"
    return state


def get_state_dim() -> int:
    """状態ベクトルの次元を返す。feature_set とモーター勝率代理で制御。"""
    fs = _get_feature_set()
    if fs == "extended_features_v2":
        base_extended = NUM_BOAT_FEATURES + len(_get_stadium_names()) + NUM_EXTRA_RACE_FEATURES
        return base_extended + EXTENDED_V2_EXTRA_DIM
    use_motor = fs == "extended_features"
    n_extra = NUM_EXTRA_RACE_FEATURES if use_motor else NUM_BASE_RACE_FEATURES
    return NUM_BOAT_FEATURES + len(_get_stadium_names()) + n_extra


def get_stadium_names_order() -> List[str]:
    """会場 one-hot の順序（状態ベクトル内の並び）を返す。"""
    return list(_get_stadium_names())


# 定数エイリアス（環境変数で次元が変わるため、動的に get_state_dim() を呼ぶこと推奨）
STATE_DIM = get_state_dim()
NUM_RACE_FEATURES = len(_get_stadium_names()) + NUM_EXTRA_RACE_FEATURES  # 最大（モーター勝率代理あり）
