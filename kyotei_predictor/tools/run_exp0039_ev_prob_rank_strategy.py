"""
EXP-0039: EV band + probability + race内EV順位フィルタの検証。

EXP-0038 で skip_top20pct + 3≤EV<5 + prob≥0.05（ev3_5_prob005）が adopt。
race 内の EV 1位は市場歪み・過大評価の影響を受けやすい可能性があるため、
EV band + probability に race 内 EV 順位条件を追加し、
ROI・利益効率・ドローダウンの改善を検証する。

ベース条件: skip_top20pct, 3≤EV<5, prob≥0.05（EXP-0038 と同一）。
rank フィルタ: 各レース内で「3≤EV<5 かつ prob≥0.05」を満たす bet を EV 降順に並べ、
  1位＝EV最大、2位＝2番目… として順位を付与。variant ごとに順位条件で抽出。

順位付け対象の定義:
  - 対象は「そのレースの selected_bets のうち、3≤EV<5 かつ prob≥0.05 を満たす組み合わせ」のみ。
  - skip_top20pct は「日付内でレースを max_ev 降順に並べ、上位20%のレースを除外」するため、
    順位付けは skip 後に残ったレースに対して行う。ただし EV/prob/順位は
    もともとそのレースの selected_bets に基づく（日付内並び順には依存しない）。
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Callable, Dict, List, Tuple

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
from kyotei_predictor.application.verify_usecase import run_verify

TRAIN_DAYS = 30
TEST_DAYS = 7
STEP_DAYS = 7
TOP_N = 3

STRATEGIES: List[Tuple] = [
    ("exp0015", "top_n_ev_gap_filter", TOP_N, 1.20, None, None, None, 0.07),
]
STRATEGY_SUFFIX = "_top3ev120_evgap0x07"

CONFIDENCE_WEIGHTED_CONFIG = {"ev_gap_high": 0.11, "normal_unit": 0.5}

SKIP_TOP_PCT = 0.2
EV_LO, EV_HI = 3.0, 5.0
PROB_MIN = 0.05


def _ev_prob_list_for_race(race: dict) -> List[Tuple[float, float]]:
    """
    レースの selected_bets のうち、3≤EV<5 かつ prob≥0.05 を満たす (ev, prob) のリストを
    EV 降順で返す。順位は 1-indexed で、戻り値の先頭が rank 1。
    """
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
    """レースの selected_bets に対応する EV の最大値（skip_top20pct 用、EXP-0038 と同一定義）。"""
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


# (variant_name, predicate: rank_1based -> bool). rank は 1-indexed。
def _rank_all(_r: int) -> bool:
    return True


def _rank_le_3(r: int) -> bool:
    return 1 <= r <= 3


def _rank_le_5(r: int) -> bool:
    return 1 <= r <= 5


def _rank_2_5(r: int) -> bool:
    return 2 <= r <= 5


def _rank_2_7(r: int) -> bool:
    return 2 <= r <= 7


VARIANTS: List[Tuple[str, Callable[[int], bool]]] = [
    ("ev3_5_prob005", _rank_all),
    ("ev3_5_prob005_rank_le_3", _rank_le_3),
    ("ev3_5_prob005_rank_le_5", _rank_le_5),
    ("ev3_5_prob005_rank_2_5", _rank_2_5),
    ("ev3_5_prob005_rank_2_7", _rank_2_7),
]

# 1レース分: (max_ev, ev_prob_list, stake, payout, race_profit, total_bet_count_in_race)
# ev_prob_list は 3≤EV<5 & prob≥0.05 を満たす (ev,prob) の EV 降順リスト（rank 1 = [0]）
RaceRow = Tuple[float, List[Tuple[float, float]], float, float, float, int]


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

    output_dir = args.output_dir or _REPO_ROOT / "outputs" / "ev_prob_rank_strategy"
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
        print(f"EXP-0039: Using existing predictions in {out_pred_dir} ({len(existing)} files).")
    else:
        print(f"EXP-0039: Running rolling validation (n_windows={args.n_windows})...")
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

    races_per_date: Dict[str, List[RaceRow]] = {}

    for wi, (ts, te, tst, tend) in enumerate(window_list):
        test_dates = _date_range(tst, tend)
        for day in test_dates:
            month = _month_dir(day)
            data_dir_month = raw_dir / month
            path = out_pred_dir / f"predictions_baseline_{day}{STRATEGY_SUFFIX}.json"
            if not path.exists() or not data_dir_month.exists():
                continue
            try:
                with open(path, encoding="utf-8") as f:
                    pred = json.load(f)
            except Exception:
                continue
            try:
                summary, details = run_verify(
                    path,
                    data_dir_month,
                    evaluation_mode="selected_bets",
                    data_source="db",
                    db_path=args.db_path,
                    bet_sizing_mode="confidence_weighted_ev_gap_v1",
                    bet_sizing_config=CONFIDENCE_WEIGHTED_CONFIG,
                )
            except Exception:
                continue
            predictions_list = pred.get("predictions") or []
            detail_by_key: Dict[Tuple[str, int], dict] = {}
            for d in details:
                v = d.get("venue") or ""
                rno = int(d.get("race_number") or 0)
                detail_by_key[(v, rno)] = d

            day_races: List[RaceRow] = []
            for race in predictions_list:
                venue = race.get("venue") or ""
                rno = int(race.get("race_number") or 0)
                selected = race.get("selected_bets") or []
                if not selected:
                    continue
                ev_prob_list = _ev_prob_list_for_race(race)
                max_ev = _max_ev_for_race(race)
                d = detail_by_key.get((venue, rno))
                if not d:
                    continue
                payout = float(d.get("payout") or 0)
                race_profit = float(d.get("race_profit") or 0)
                stake = payout - race_profit
                bet_count = int(d.get("purchased_bets") or 0)
                if bet_count <= 0:
                    continue
                day_races.append((max_ev, ev_prob_list, stake, payout, race_profit, bet_count))

            if day_races:
                races_per_date[day] = day_races

    results: Dict[str, Dict] = {}
    for name, _ in VARIANTS:
        results[name] = {
            "total_bet_selected": 0.0,
            "total_payout_selected": 0.0,
            "selected_bets_total_count": 0,
            "window_profits": [0.0] * len(window_list),
            "race_count": 0,
            "total_race_days": 0,
        }

    total_race_days = len(races_per_date)
    for day, day_races in races_per_date.items():
        day_races_sorted = sorted(day_races, key=lambda x: -x[0])
        n = len(day_races_sorted)
        k_skip = int(n * SKIP_TOP_PCT)
        idx_start = min(k_skip, n)
        races_after_skip = day_races_sorted[idx_start:]

        wi = next(i for i, (_, _, tst, tend) in enumerate(window_list) if tst <= day <= tend)
        for race_row in races_after_skip:
            max_ev, ev_prob_list, stake, payout, race_profit, _ = race_row
            M = len(ev_prob_list)
            if M == 0:
                continue
            total_profit_race = payout - stake
            for name, rank_fn in VARIANTS:
                K = sum(1 for i in range(M) if rank_fn(i + 1))
                if K == 0:
                    continue
                ratio = K / M
                rstats = results[name]
                rstats["total_bet_selected"] += stake * ratio
                rstats["total_payout_selected"] += payout * ratio
                rstats["selected_bets_total_count"] += K
                rstats["race_count"] += 1
                rstats["window_profits"][wi] += total_profit_race * ratio

    for name in results:
        results[name]["total_race_days"] = total_race_days

    results_list: List[Dict] = []
    for name, _ in VARIANTS:
        rstats = results[name]
        tb = rstats["total_bet_selected"]
        tp = rstats["total_payout_selected"]
        cnt = rstats["selected_bets_total_count"]
        total_profit = round(tp - tb, 2)
        roi = round((tp / tb - 1) * 100, 2) if tb else None
        profit_per_1000 = round(1000.0 * (tp - tb) / cnt, 2) if cnt else 0.0
        cum = 0.0
        peak = 0.0
        dd = 0.0
        for wprof in rstats["window_profits"]:
            cum += wprof
            if cum > peak:
                peak = cum
            if peak - cum > dd:
                dd = peak - cum
        out = {
            "variant": name,
            "ROI": roi,
            "total_profit": total_profit,
            "max_drawdown": round(dd, 2),
            "profit_per_1000_bets": profit_per_1000,
            "bet_count": cnt,
            "total_bet_selected": round(tb, 2),
            "total_payout_selected": round(tp, 2),
            "race_count": rstats["race_count"],
            "total_race_days": rstats["total_race_days"],
        }
        rstats.update(out)
        results_list.append(out)

    out_path = output_dir / "exp0039_ev_prob_rank_strategy_results.json"
    payload = {
        "experiment_id": "EXP-0039",
        "baseline": "ev3_5_prob005 (EXP-0038 adopt, no rank filter)",
        "n_windows": args.n_windows,
        "seed": args.seed,
        "skip_top_pct": SKIP_TOP_PCT,
        "ev_band": [EV_LO, EV_HI],
        "prob_min": PROB_MIN,
        "rank_definition": "Within each race, bets satisfying 3<=EV<5 and prob>=0.05 are sorted by EV descending; rank 1 = highest EV.",
        "variants": [
            "ev3_5_prob005 (baseline, no rank filter)",
            "ev3_5_prob005_rank_le_3 (rank ≤ 3)",
            "ev3_5_prob005_rank_le_5 (rank ≤ 5)",
            "ev3_5_prob005_rank_2_5 (2 ≤ rank ≤ 5)",
            "ev3_5_prob005_rank_2_7 (2 ≤ rank ≤ 7)",
        ],
        "results": results_list,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Saved {out_path}")

    print("\n--- EXP-0039 EV band + prob + rank (skip_top20pct, n_windows={}) ---".format(args.n_windows))
    print("variant                      | ROI     | total_profit | max_drawdown | profit_per_1000_bets | bet_count | race_count")
    print("-" * 130)
    for name, _ in VARIANTS:
        r = results[name]
        print(
            f"  {name:26} | {r.get('ROI'):6}% | {r.get('total_profit'):12} | {r.get('max_drawdown'):12} | "
            f"{r.get('profit_per_1000_bets'):20} | {r.get('bet_count'):9} | {r.get('race_count')}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
