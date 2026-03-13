"""
EXP-0042: selection 条件の厳密再検証（stake 固定・bet 単位で payout 整合）。

EXP-0041 で bet 単位の厳密評価により全 sizing variant が赤字であることが判明した。
本実験では bet sizing を baseline_fixed（stake=100）に固定し、
selection 条件のみを変えて、どの条件が厳密評価で最もマシかを比較する。

評価ロジックは EXP-0041 と同一:
- stake = 100（全 bet 同額）
- hit のとき payout = stake × odds、外れのとき payout = 0
- profit = payout - stake
- odds / hit は repo から race_data・odds_data を取得して bet 単位で算出
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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
FIXED_STAKE = 100

# Selection variant: (name, ev_lo, ev_hi, prob_min). prob_min None = 制約なし
SELECTION_VARIANTS: List[Tuple[str, float, float, Optional[float]]] = [
    ("baseline_a", 3.0, 5.0, None),   # skip_top20pct + 3≤EV<5
    ("baseline_b", 3.0, 5.0, 0.05),   # skip_top20pct + 3≤EV<5 + prob≥0.05 (EXP-0038)
    ("baseline_c", 4.0, 5.0, None),   # skip_top20pct + 4≤EV<5
    ("baseline_d", 3.0, 6.0, None),   # skip_top20pct + 3≤EV<6
    ("baseline_e", 3.0, 5.0, 0.08),   # skip_top20pct + 3≤EV<5 + prob≥0.08
    ("baseline_f", 3.0, 8.0, None),   # skip_top20pct + 3≤EV<8
]


def _resolve_db_path(args_db_path: Optional[str]) -> Path:
    """DB パスを解決する。未指定時は repo root 基準のデフォルトを使い、存在確認する。"""
    if args_db_path and args_db_path.strip():
        p = Path(args_db_path)
        if not p.is_absolute():
            p = _REPO_ROOT / args_db_path
        return p
    default = _REPO_ROOT / "kyotei_predictor" / "data" / "kyotei_races.sqlite"
    return default


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


def _norm(s: str) -> str:
    return (s or "").replace(" ", "")


def _all_bets_for_race(
    race: dict,
    prediction_date: str,
    repo,
) -> Optional[List[Tuple[float, float, float, bool]]]:
    """
    レースの selected_bets のうち、odds が取得できるものについて
    (ev, prob, odds, hit) のリストを返す。selection フィルタはかけない。
    race_data / odds_data が無い場合は None。
    """
    selected = race.get("selected_bets") or []
    all_comb = race.get("all_combinations") or []
    if not selected or not all_comb:
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
    out: List[Tuple[float, float, float, bool]] = []
    for c in selected:
        comb_raw = (c if isinstance(c, str) else "").strip()
        ev = comb_to_ev.get(comb_raw, 0.0)
        prob = comb_to_prob.get(comb_raw, 0.0)
        od = get_odds_for_combination(odds_data, comb_raw)
        if od is None or float(od) <= 0:
            continue
        odds = float(od)
        hit = _norm(comb_raw) == actual_norm
        out.append((ev, prob, odds, hit))
    return out if out else None


def _filter_bets_by_selection(
    bets: List[Tuple[float, float, float, bool]],
    ev_lo: float,
    ev_hi: float,
    prob_min: Optional[float],
) -> List[Tuple[float, float, float, bool]]:
    """bets を selection 条件でフィルタする。"""
    out: List[Tuple[float, float, float, bool]] = []
    for ev, prob, odds, hit in bets:
        if not (ev_lo <= ev < ev_hi):
            continue
        if prob_min is not None and prob < prob_min:
            continue
        out.append((ev, prob, odds, hit))
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="SQLite DB path. Default: kyotei_predictor/data/kyotei_races.sqlite (repo root relative)",
    )
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--predictions-dir", type=Path, default=None)
    parser.add_argument("--n-windows", type=int, default=18)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    db_path_resolved = _resolve_db_path(args.db_path)
    if not db_path_resolved.exists():
        print(f"[ERROR] DB not found: {db_path_resolved}", file=sys.stderr)
        print("  Resolved from: --db-path={}".format(args.db_path or "(default)"), file=sys.stderr)
        print("  REPO_ROOT: {}".format(_REPO_ROOT), file=sys.stderr)
        return 1
    db_path_str = str(db_path_resolved)
    print(f"[EXP-0042] DB found: {db_path_str}")

    raw_dir = _REPO_ROOT / "kyotei_predictor" / "data" / "raw"
    if not raw_dir.is_dir():
        raw_dir = Path("kyotei_predictor/data/raw")

    output_dir = args.output_dir or _REPO_ROOT / "outputs" / "selection_verified"
    output_dir.mkdir(parents=True, exist_ok=True)

    pred_parent = args.predictions_dir or _REPO_ROOT / "outputs" / "ev_cap_experiments"
    out_pred_dir = pred_parent / "rolling_roi_predictions"

    min_date, max_date = get_db_date_range(db_path_str)
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
        print(f"EXP-0042: Using existing predictions in {out_pred_dir} ({len(existing)} files).")
    else:
        print(f"EXP-0042: Running rolling validation (n_windows={args.n_windows})...")
        run_rolling_validation_roi(
            db_path=db_path_str,
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
        db_path=db_path_str,
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
                bets = _all_bets_for_race(race, prediction_date, repo)
                if not bets:
                    continue
                day_races.append((max_ev, bets))
            if day_races:
                races_per_date[day] = day_races

    results: Dict[str, Dict] = {}
    for name, ev_lo, ev_hi, prob_min in SELECTION_VARIANTS:
        results[name] = {
            "total_stake": 0.0,
            "total_payout": 0.0,
            "bet_count": 0,
            "hit_count": 0,
            "race_count": 0,
            "window_profits": [0.0] * len(window_list),
            "sum_odds": 0.0,
            "sum_ev": 0.0,
            "sum_prob": 0.0,
        }

    for day, day_races in races_per_date.items():
        day_races_sorted = sorted(day_races, key=lambda x: -x[0])
        n = len(day_races_sorted)
        k_skip = int(n * SKIP_TOP_PCT)
        idx_start = min(k_skip, n)
        races_after_skip = day_races_sorted[idx_start:]

        wi = next((i for i, (_, _, tst, tend) in enumerate(window_list) if tst <= day <= tend), 0)
        for max_ev, bets in races_after_skip:
            for name, ev_lo, ev_hi, prob_min in SELECTION_VARIANTS:
                filtered = _filter_bets_by_selection(bets, ev_lo, ev_hi, prob_min)
                if not filtered:
                    continue
                race_stake = FIXED_STAKE * len(filtered)
                race_payout = 0.0
                hit_count = 0
                so = 0.0
                se = 0.0
                sp = 0.0
                for ev, prob, odds, hit in filtered:
                    payout = FIXED_STAKE * odds if hit else 0.0
                    race_payout += payout
                    if hit:
                        hit_count += 1
                    so += odds
                    se += ev
                    sp += prob
                results[name]["total_stake"] += race_stake
                results[name]["total_payout"] += race_payout
                results[name]["bet_count"] += len(filtered)
                results[name]["hit_count"] += hit_count
                results[name]["race_count"] += 1
                results[name]["window_profits"][wi] += race_payout - race_stake
                results[name]["sum_odds"] += so
                results[name]["sum_ev"] += se
                results[name]["sum_prob"] += sp

    results_list: List[Dict] = []
    for name, ev_lo, ev_hi, prob_min in SELECTION_VARIANTS:
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
        avg_odds = round(r["sum_odds"] / cnt, 2) if cnt else None
        avg_ev = round(r["sum_ev"] / cnt, 4) if cnt else None
        avg_prob = round(r["sum_prob"] / cnt, 4) if cnt else None
        out = {
            "variant": name,
            "ROI": roi,
            "total_profit": total_profit,
            "max_drawdown": round(dd, 2),
            "profit_per_1000_bets": profit_per_1000,
            "bet_count": cnt,
            "race_count": rc,
            "hit_count": hit_count,
            "hit_rate": hit_rate,
            "total_stake": round(ts, 2),
            "average_bet_size": avg_bet,
            "average_stake_per_race": avg_stake_per_race,
            "average_odds": avg_odds,
            "average_ev": avg_ev,
            "average_prob": avg_prob,
        }
        r.update(out)
        results_list.append(out)

    out_path = output_dir / "exp0042_selection_verified_results.json"
    payload = {
        "experiment_id": "EXP-0042",
        "db_path_used": db_path_str,
        "stake_fixed": FIXED_STAKE,
        "selection_variants": [
            {"name": n, "ev_lo": e0, "ev_hi": e1, "prob_min": p}
            for n, e0, e1, p in SELECTION_VARIANTS
        ],
        "exp0041_relation": "Same strict per-bet evaluation (stake=100, payout=stake*odds if hit). Only selection filter differs.",
        "results": results_list,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")

    print("\n--- EXP-0042 Selection verified (stake=100 fixed, n_windows={}) ---".format(args.n_windows))
    print("variant     | ROI     | total_profit | max_drawdown | profit/1k  | bet_count | race_count | hit_count | hit_rate | total_stake | avg_odds | avg_ev  | avg_prob")
    print("-" * 160)
    for name, _, _, _ in SELECTION_VARIANTS:
        r = results[name]
        print(
            f"  {name:10} | {r['ROI']:6}% | {r['total_profit']:12} | {r['max_drawdown']:12} | {r['profit_per_1000_bets']:9} | {r['bet_count']:9} | {r['race_count']:10} | {r['hit_count']:9} | {r['hit_rate']:6}% | {r['total_stake']:11} | {r.get('average_odds') or 0:8} | {r.get('average_ev') or 0:6} | {r.get('average_prob') or 0:6}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
