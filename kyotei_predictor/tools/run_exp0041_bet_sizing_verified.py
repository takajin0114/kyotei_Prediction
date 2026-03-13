"""
EXP-0041: ベットサイジング厳密検証（verify 内で stake / payout を整合）。

採用条件（skip_top20pct + 3≤EV<5 + prob≥0.05）を固定し、
各 sizing variant ごとに「selection → sizing → verify」を一体で実行する。

EXP-0040 との差分:
- EXP-0040 は verify を 1 回だけ実行し payout を固定し、stake を後段で再計算していたため
  ROI / total_profit が過大評価されている可能性がある。
- 本実験では各 bet ごとに stake と payout を対応させ、
  payout = stake × odds（hit 時）、profit = payout - stake で厳密に計算する。

payout の計算式: payout_i = stake_i * odds_i if hit_i else 0
hit 時の扱い: 組み合わせが実際の着順と一致すれば hit、odds は odds_data から取得
odds の参照元: repo.get_odds(prediction_date, venue, rno) で取得した odds_data の ratio
unit から stake への換算: unit は円単位（50〜200）。stake = unit（そのまま）
既存 verify_usecase: 本ツールでは verify は使わず、race_data / odds_data を直接読み
  bet 単位で hit / odds を取得し、各 variant の unit で stake と payout を算出する。
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

_THIS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _THIS_DIR.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

os.environ["KYOTEI_USE_MOTOR_WIN_PROXY"] = os.environ.get("KYOTEI_USE_MOTOR_WIN_PROXY", "1")
os.environ["KYOTEI_FEATURE_SET"] = os.environ.get("KYOTEI_FEATURE_SET", "extended_features")

from kyotei_predictor.tools.rolling_validation_roi import (
    build_windows,
    get_db_date_range,
    run_rolling_validation_roi,
)
from kyotei_predictor.tools.rolling_validation_windows import _date_range, _month_dir
from kyotei_predictor.domain.verification_models import (
    get_actual_trifecta_from_race_data,
    get_odds_for_combination,
)
from kyotei_predictor.infrastructure.repositories.race_data_repository_factory import (
    get_race_data_repository,
)

TRAIN_DAYS = 30
TEST_DAYS = 7
STEP_DAYS = 7
TOP_N = 3

STRATEGIES: List[Tuple] = [
    ("exp0015", "top_n_ev_gap_filter", TOP_N, 1.20, None, None, None, 0.07),
]
STRATEGY_SUFFIX = "_top3ev120_evgap0x07"

SKIP_TOP_PCT = 0.2
EV_LO, EV_HI = 3.0, 5.0
PROB_MIN = 0.05

MIN_UNIT = 50
MAX_UNIT = 200
MAX_UNIT_CAPPED = 150
BASELINE_UNIT = 100


def _ev_prob_list_for_race(race: dict) -> List[Tuple[float, float]]:
    """レースの selected_bets のうち 3≤EV<5 かつ prob≥0.05 を満たす (ev, prob) を EV 降順で返す。"""
    selected = race.get("selected_bets") or []
    all_comb = race.get("all_combinations") or []
    comb_to_ev: Dict[str, float] = {}
    comb_to_prob: Dict[str, float] = {}
    for c in all_comb:
        comb_raw = (c.get("combination") or "").strip()
        if not comb_raw:
            continue
        prob = float(c.get("probability", c.get("score", 0.0)))
        r = c.get("ratio") or c.get("odds")
        if r is None:
            continue
        try:
            ratio = float(r)
        except (TypeError, ValueError):
            continue
        if ratio <= 0:
            continue
        ev = prob * ratio
        comb_to_ev[comb_raw] = ev
        comb_to_prob[comb_raw] = prob
    out: List[Tuple[float, float]] = []
    for c in selected:
        comb_raw = (c if isinstance(c, str) else "").strip()
        ev = comb_to_ev.get(comb_raw, 0.0)
        prob = comb_to_prob.get(comb_raw, 0.0)
        if EV_LO <= ev < EV_HI and prob >= PROB_MIN:
            out.append((ev, prob))
    out.sort(key=lambda x: -x[0])
    return out


def _max_ev_for_race(race: dict) -> float:
    """レースの selected_bets の EV 最大値（skip_top20pct 用）。"""
    selected = race.get("selected_bets") or []
    all_comb = race.get("all_combinations") or []
    comb_to_ev: Dict[str, float] = {}
    for c in all_comb:
        comb_raw = (c.get("combination") or "").strip()
        if not comb_raw:
            continue
        prob = float(c.get("probability", c.get("score", 0.0)))
        r = c.get("ratio") or c.get("odds")
        if r is None:
            continue
        try:
            ratio = float(r)
        except (TypeError, ValueError):
            continue
        if ratio <= 0:
            continue
        comb_to_ev[comb_raw] = prob * ratio
    if not selected:
        return 0.0
    evs = [comb_to_ev.get((c if isinstance(c, str) else "").strip(), 0.0) for c in selected]
    return max(evs) if evs else 0.0


def _clip_round(x: float, lo: int, hi: int) -> int:
    return max(lo, min(hi, round(x)))


# Sizing: list of (ev, prob) -> list of int (unit per bet, in yen)
def _fixed(bets: List[Tuple[float, float]]) -> List[int]:
    return [BASELINE_UNIT] * len(bets)


def _by_ev_linear(bets: List[Tuple[float, float]]) -> List[int]:
    return [_clip_round(25.0 * ev, MIN_UNIT, MAX_UNIT) for ev, _ in bets]


def _by_prob_linear(bets: List[Tuple[float, float]]) -> List[int]:
    return [_clip_round(200.0 * prob, MIN_UNIT, MAX_UNIT) for _, prob in bets]


def _by_ev_prob(bets: List[Tuple[float, float]]) -> List[int]:
    return [_clip_round(40.0 * ev * prob, MIN_UNIT, MAX_UNIT) for ev, prob in bets]


def _by_ev_capped(bets: List[Tuple[float, float]]) -> List[int]:
    return [_clip_round(25.0 * ev, MIN_UNIT, MAX_UNIT_CAPPED) for ev, _ in bets]


def _by_ev_prob_capped(bets: List[Tuple[float, float]]) -> List[int]:
    return [_clip_round(40.0 * ev * prob, MIN_UNIT, MAX_UNIT_CAPPED) for ev, prob in bets]


VARIANTS: List[Tuple[str, Callable[[List[Tuple[float, float]]], List[int]]]] = [
    ("baseline_fixed", _fixed),
    ("size_by_ev_linear", _by_ev_linear),
    ("size_by_prob_linear", _by_prob_linear),
    ("size_by_ev_prob", _by_ev_prob),
    ("size_by_ev_capped", _by_ev_capped),
    ("size_by_ev_prob_capped", _by_ev_prob_capped),
]


def _norm(s: str) -> str:
    return (s or "").replace(" ", "")


# 1 race 分の bet 情報: (ev, prob, odds, hit). odds は None の場合はその bet は対象外とする。
def _bets_for_race(
    race: dict,
    prediction_date: str,
    repo,
) -> Optional[List[Tuple[float, float, float, bool]]]:
    """
    レースについて 3≤EV<5 & prob≥0.05 の bet ごとに (ev, prob, odds, hit) を返す。
    race_data または odds_data が無い場合は None（レース全体をスキップ）。
    各 bet で odds が取れない場合はその bet をリストから除外する（stake/payout を計算できないため）。
    """
    ev_prob_list = _ev_prob_list_for_race(race)
    if not ev_prob_list:
        return None
    venue = race.get("venue") or ""
    rno = int(race.get("race_number") or 0)
    if not venue or rno <= 0:
        return None
    race_data = repo.load_race(prediction_date, venue, rno)
    if race_data is None:
        return None
    actual = get_actual_trifecta_from_race_data(race_data)
    if actual is None:
        return None
    odds_data = repo.get_odds(prediction_date, venue, rno) if hasattr(repo, "get_odds") else None
    if odds_data is None:
        return None
    actual_norm = _norm(actual)
    # selected_bets の順序と ev_prob_list の順序は、_ev_prob_list_for_race が selected を走り
    # 3≤EV<5 & prob≥0.05 でフィルタし EV 降順でソートしているので、combination の対応を取る必要がある。
    # _ev_prob_list_for_race は (ev, prob) のみ返しており combination 文字列を返していない。
    # そこで all_combinations から再度 (comb, ev, prob) のリストを 3≤EV<5 & prob≥0.05 で作り、
    # 各 comb に対して odds と hit を付与する。
    selected = race.get("selected_bets") or []
    all_comb = race.get("all_combinations") or []
    comb_to_ev: Dict[str, float] = {}
    comb_to_prob: Dict[str, float] = {}
    for c in all_comb:
        comb_raw = (c.get("combination") or "").strip()
        if not comb_raw:
            continue
        prob = float(c.get("probability", c.get("score", 0.0)))
        r = c.get("ratio") or c.get("odds")
        if r is None:
            continue
        try:
            ratio = float(r)
        except (TypeError, ValueError):
            continue
        if ratio <= 0:
            continue
        ev = prob * ratio
        comb_to_ev[comb_raw] = ev
        comb_to_prob[comb_raw] = prob
    triples: List[Tuple[str, float, float]] = []
    for c in selected:
        comb_raw = (c if isinstance(c, str) else "").strip()
        ev = comb_to_ev.get(comb_raw, 0.0)
        prob = comb_to_prob.get(comb_raw, 0.0)
        if EV_LO <= ev < EV_HI and prob >= PROB_MIN:
            triples.append((comb_raw, ev, prob))
    triples.sort(key=lambda x: -x[1])
    out: List[Tuple[float, float, float, bool]] = []
    for comb_raw, ev, prob in triples:
        od = get_odds_for_combination(odds_data, comb_raw)
        if od is None or float(od) <= 0:
            continue
        odds = float(od)
        hit = _norm(comb_raw) == actual_norm
        out.append((ev, prob, odds, hit))
    return out if out else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True, help="SQLite DB path")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--predictions-dir", type=Path, default=None)
    parser.add_argument("--n-windows", type=int, default=18)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    raw_dir = _REPO_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")

    output_dir = args.output_dir or _REPO_ROOT / "outputs" / "bet_sizing_optimization"
    output_dir.mkdir(parents=True, exist_ok=True)

    pred_parent = args.predictions_dir or _REPO_ROOT / "outputs" / "ev_cap_experiments"
    out_pred_dir = pred_parent / "rolling_roi_predictions"

    min_date, max_date = get_db_date_range(args.db_path)
    window_list = build_windows(
        min_date, max_date, TRAIN_DAYS, TEST_DAYS, STEP_DAYS, args.n_windows
    )
    need_days = set()
    for _ts, _te, tst, tend in window_list:
        for d in _date_range(tst, tend):
            need_days.add(d)
    existing = set()
    if out_pred_dir.exists():
        for p in out_pred_dir.glob("predictions_baseline_*" + STRATEGY_SUFFIX + ".json"):
            stem = p.stem
            date_part = stem.replace("predictions_baseline_", "").replace(STRATEGY_SUFFIX, "")
            if len(date_part) == 10 and date_part[4] == "-" and date_part[7] == "-":
                existing.add(date_part)
    if need_days and need_days.issubset(existing):
        print(f"EXP-0041: Using existing predictions in {out_pred_dir} ({len(existing)} files).")
    else:
        print(f"EXP-0041: Running rolling validation (n_windows={args.n_windows})...")
        run_rolling_validation_roi(
            db_path=args.db_path,
            output_dir=pred_parent,
            data_dir_raw=raw_dir,
            train_days=TRAIN_DAYS,
            test_days=TEST_DAYS,
            step_days=STEP_DAYS,
            n_windows=args.n_windows,
            strategies=STRATEGIES,
            model_type="xgboost",
            calibration="sigmoid",
            feature_set="extended_features",
            seed=args.seed,
        )

    repo = get_race_data_repository(
        "db",
        data_dir=raw_dir,
        db_path=args.db_path,
    )

    # (day, max_ev, list of (ev, prob, odds, hit))
    races_per_date: Dict[str, List[Tuple[float, List[Tuple[float, float, float, bool]]]]] = {}

    for wi, (ts, te, tst, tend) in enumerate(window_list):
        test_dates = _date_range(tst, tend)
        for day in test_dates:
            path = out_pred_dir / f"predictions_baseline_{day}{STRATEGY_SUFFIX}.json"
            if not path.exists():
                continue
            try:
                with open(path, encoding="utf-8") as f:
                    pred = json.load(f)
            except Exception:
                continue
            prediction_date = pred.get("prediction_date") or day
            predictions_list = pred.get("predictions") or []
            day_races: List[Tuple[float, List[Tuple[float, float, float, bool]]]] = []
            for race in predictions_list:
                max_ev = _max_ev_for_race(race)
                bets = _bets_for_race(race, prediction_date, repo)
                if not bets:
                    continue
                day_races.append((max_ev, bets))
            if day_races:
                races_per_date[day] = day_races

    # skip_top20pct 適用後、各 variant で bet 単位に stake / payout を整合して集計
    results: Dict[str, Dict] = {}
    for name, _ in VARIANTS:
        results[name] = {
            "total_stake": 0.0,
            "total_payout": 0.0,
            "bet_count": 0,
            "hit_count": 0,
            "race_count": 0,
            "window_profits": [0.0] * len(window_list),
        }

    for day, day_races in races_per_date.items():
        day_races_sorted = sorted(day_races, key=lambda x: -x[0])
        n = len(day_races_sorted)
        k_skip = int(n * SKIP_TOP_PCT)
        idx_start = min(k_skip, n)
        races_after_skip = day_races_sorted[idx_start:]

        wi = next((i for i, (_, _, tst, tend) in enumerate(window_list) if tst <= day <= tend), 0)
        for max_ev, bets in races_after_skip:
            # bets: list of (ev, prob, odds, hit)
            for name, sizing_fn in VARIANTS:
                ev_prob_list = [(b[0], b[1]) for b in bets]
                units = sizing_fn(ev_prob_list)
                if len(units) != len(bets):
                    continue
                race_stake = 0.0
                race_payout = 0.0
                for i, (ev, prob, odds, hit) in enumerate(bets):
                    if i >= len(units):
                        break
                    stake = float(units[i])
                    payout = stake * odds if hit else 0.0
                    race_stake += stake
                    race_payout += payout
                    if hit:
                        results[name]["hit_count"] += 1
                results[name]["total_stake"] += race_stake
                results[name]["total_payout"] += race_payout
                results[name]["bet_count"] += len(units)
                results[name]["race_count"] += 1
                results[name]["window_profits"][wi] += race_payout - race_stake

    results_list: List[Dict] = []
    for name, _ in VARIANTS:
        r = results[name]
        ts = r["total_stake"]
        tp = r["total_payout"]
        cnt = r["bet_count"]
        rc = r["race_count"]
        hit_count = r["hit_count"]
        total_profit = round(tp - ts, 2)
        roi = round((tp / ts - 1) * 100, 2) if ts else None
        profit_per_1000 = round(1000.0 * (tp - ts) / cnt, 2) if cnt else 0.0
        cum = 0.0
        peak = 0.0
        dd = 0.0
        for wprof in r["window_profits"]:
            cum += wprof
            if cum > peak:
                peak = cum
            if peak - cum > dd:
                dd = peak - cum
        avg_bet = round(ts / cnt, 2) if cnt else 0.0
        avg_stake_per_race = round(ts / rc, 2) if rc else 0.0
        hit_rate = round(100.0 * hit_count / cnt, 2) if cnt else 0.0
        # average_payout_when_hit: hit 時のみの平均払戻（stake*odds の平均）
        hit_payouts = []  # 本ループでは持っていないので、別途集計しないと出せない。簡易で hit_count と total_payout からは導出困難なのでスキップ or 近似
        avg_payout_when_hit = round(tp / hit_count, 2) if hit_count else None
        out = {
            "variant": name,
            "ROI": roi,
            "total_profit": total_profit,
            "max_drawdown": round(dd, 2),
            "profit_per_1000_bets": profit_per_1000,
            "bet_count": cnt,
            "total_stake": round(ts, 2),
            "total_payout": round(tp, 2),
            "average_bet_size": avg_bet,
            "average_stake_per_race": avg_stake_per_race,
            "hit_count": hit_count,
            "hit_rate": hit_rate,
            "average_payout_when_hit": avg_payout_when_hit,
        }
        r.update(out)
        results_list.append(out)

    out_path = output_dir / "exp0041_bet_sizing_verified_results.json"
    payload = {
        "experiment_id": "EXP-0041",
        "base_conditions": "skip_top20pct, 3<=EV<5, prob>=0.05",
        "n_windows": args.n_windows,
        "seed": args.seed,
        "min_unit": MIN_UNIT,
        "max_unit": MAX_UNIT,
        "max_unit_capped": MAX_UNIT_CAPPED,
        "baseline_unit": BASELINE_UNIT,
        "payout_calculation": "payout_i = stake_i * odds_i if hit_i else 0; stake_i = unit_i (yen); odds from repo.get_odds",
        "exp0040_difference": "EXP-0040 used single verify payout then rescaled stake per variant; EXP-0041 computes stake and payout per bet consistently per variant.",
        "sizing_formulas": {
            "baseline_fixed": "unit = 100 (all bets)",
            "size_by_ev_linear": "unit = clip(round(25*EV), 50, 200)",
            "size_by_prob_linear": "unit = clip(round(200*prob), 50, 200)",
            "size_by_ev_prob": "unit = clip(round(40*EV*prob), 50, 200)",
            "size_by_ev_capped": "unit = clip(round(25*EV), 50, 150)",
            "size_by_ev_prob_capped": "unit = clip(round(40*EV*prob), 50, 150)",
        },
        "results": results_list,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")

    print("\n--- EXP-0041 Bet sizing VERIFIED (skip_top20pct, 3<=EV<5, prob>=0.05, n_windows={}) ---".format(args.n_windows))
    print("  payout = stake * odds per bet (hit only); stake = unit per variant. No reuse of baseline payout.")
    print("variant                  | ROI     | total_profit | max_drawdown | profit/1k  | bet_count | hit_count | hit_rate | total_stake | avg_bet | avg_stake/race")
    print("-" * 160)
    for name, _ in VARIANTS:
        r = results[name]
        print(
            f"  {name:22} | {r['ROI']:6}% | {r['total_profit']:12} | {r['max_drawdown']:12} | {r['profit_per_1000_bets']:9} | {r['bet_count']:9} | {r['hit_count']:9} | {r['hit_rate']:6}% | {r['total_stake']:11} | {r['average_bet_size']:7} | {r['average_stake_per_race']}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
