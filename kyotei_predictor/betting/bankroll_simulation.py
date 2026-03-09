"""
資金シミュレーション。

賭けの並びから資金曲線・最大ドローダウン・Sharpe・profit factor を計算する。
fixed / kelly_half は賭け時点の資金と確率・オッズから stake を計算可能。
"""

import math
from typing import Any, Dict, List, Optional, Tuple

from kyotei_predictor.betting.bet_sizing import kelly_fraction, BET_SIZING_KELLY_HALF, BET_SIZING_KELLY_CAPPED
from kyotei_predictor.betting.kelly import kelly_capped


def simulate_bankroll(
    bets: List[Dict[str, Any]],
    initial_bankroll: float = 100_000.0,
    bet_sizing: str = "fixed",
    unit_stake: float = 100.0,
) -> Dict[str, Any]:
    """
    賭けの並びから資金推移とリスク指標を計算する。

    各 bet は "stake", "odds", "hit" (bool) を持つ。bet_sizing が kelly_half のときは
    "probability" と "odds", "hit" から賭け時点の資金で stake を計算する（stake は無視）。

    Args:
        bets: [{"stake": 100, "odds": 12.5, "hit": True}, ...] または kelly 時は {"probability", "odds", "hit"}
        initial_bankroll: 初期資金（円）
        bet_sizing: "fixed" | "kelly_half"。kelly_half のとき確率とオッズから Kelly 半額で stake 計算。
        unit_stake: fixed 時の 1 点あたり金額（円）

    Returns:
        {
            "bankroll_curve": [initial, after_bet_1, after_bet_2, ...],
            "max_drawdown": 最大ドローダウン（正の値＝下がった幅）,
            "sharpe_ratio": 1賭けあたりリターンの Sharpe（簡易）,
            "profit_factor": 総利益 / 総損失（損失 0 のときは None または inf）,
            "bet_count": len(bets),
            "total_stake": 総賭け金,
            "total_payout": 総払戻,
            "final_bankroll": 最終資金,
        }
    """
    curve: List[float] = [initial_bankroll]
    total_stake = 0.0
    total_payout = 0.0
    returns: List[float] = []

    bankroll = initial_bankroll

    for b in bets:
        odds = float(b.get("odds") or 0)
        hit = bool(b.get("hit"))
        if bet_sizing == BET_SIZING_KELLY_HALF or bet_sizing == "half_kelly":
            prob = float(b.get("probability") or 0)
            kf = kelly_fraction(prob, odds) * 0.5
            stake = min(bankroll, max(0, bankroll * kf))
            stake = round(stake, 2)
        elif bet_sizing in ("kelly_capped_0.02", "capped_kelly_0.02"):
            prob = float(b.get("probability") or 0)
            kf = kelly_capped(prob, odds, cap=0.02)
            stake = min(bankroll, max(0, bankroll * kf))
            stake = round(stake, 2)
        elif bet_sizing in ("kelly_capped_0.05", "capped_kelly_0.05", BET_SIZING_KELLY_CAPPED):
            prob = float(b.get("probability") or 0)
            kf = kelly_capped(prob, odds, cap=0.05)
            stake = min(bankroll, max(0, bankroll * kf))
            stake = round(stake, 2)
        else:
            stake = float(b.get("stake") or unit_stake)
        if stake <= 0:
            curve.append(bankroll)
            continue
        total_stake += stake
        payout = stake * odds if hit else 0.0
        total_payout += payout
        bankroll = bankroll - stake + payout
        curve.append(bankroll)
        # 1賭けあたりのリターン率（stake に対する）
        ret = (payout - stake) / stake if stake else 0.0
        returns.append(ret)

    # 最大ドローダウン
    peak = curve[0]
    max_dd = 0.0
    for v in curve:
        if v > peak:
            peak = v
        dd = peak - v
        if dd > max_dd:
            max_dd = dd

    # Sharpe（簡易: リターン率の平均/標準偏差、賭け数でスケール）
    if len(returns) >= 2:
        mean_r = sum(returns) / len(returns)
        var_r = sum((x - mean_r) ** 2 for x in returns) / (len(returns) - 1)
        std_r = math.sqrt(var_r) if var_r > 0 else 0.0
        sharpe = (mean_r / std_r * math.sqrt(len(returns))) if std_r > 0 else 0.0
    else:
        sharpe = 0.0

    # profit factor: 総利益 / 総損失
    gross_profit = sum(stake * (float(b.get("odds") or 0) - 1) for b in bets if b.get("hit") and b.get("stake"))
    gross_loss = sum(float(b.get("stake") or 0) for b in bets if not b.get("hit") and b.get("stake"))
    profit_factor: Optional[float] = None
    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss
    elif gross_profit > 0:
        profit_factor = float("inf")

    return {
        "bankroll_curve": curve,
        "max_drawdown": round(max_dd, 2),
        "sharpe_ratio": round(sharpe, 4),
        "profit_factor": profit_factor if profit_factor is not None else None,
        "bet_count": len(bets),
        "total_stake": round(total_stake, 2),
        "total_payout": round(total_payout, 2),
        "final_bankroll": round(bankroll, 2),
        "roi_pct": round((total_payout / total_stake - 1) * 100, 2) if total_stake else 0.0,
    }


def build_bet_list_from_verify(
    predictions: List[Dict[str, Any]],
    details: List[Dict[str, Any]],
    fixed_stake: float = 100.0,
) -> List[Dict[str, Any]]:
    """
    予測（selected_bets, all_combinations）と検証詳細（actual）から、
    1賭けずつのリストを組み立てる。stake は固定。

    Args:
        predictions: 予測の predictions リスト（各要素に venue, race_number, selected_bets, all_combinations）
        details: run_verify の details（venue, race_number, actual, odds 等）
        fixed_stake: 1点あたり金額

    Returns:
        [{"stake": 100, "odds": 12.5, "hit": True, "probability": 0.08}, ...]
    """
    key_to_actual: Dict[Tuple[str, int], str] = {}
    for d in details:
        venue = d.get("venue") or ""
        rno = int(d.get("race_number") or 0)
        actual = (d.get("actual") or "").strip().replace(" ", "")
        if venue and rno:
            key_to_actual[(venue, rno)] = actual

    out: List[Dict[str, Any]] = []
    for race in predictions:
        venue = (race.get("venue") or "").strip()
        rno = int(race.get("race_number") or 0)
        key = (venue, rno)
        actual = key_to_actual.get(key)
        if actual is None:
            continue
        selected = race.get("selected_bets") or []
        combs = {str((c.get("combination") or "").strip().replace(" ", "")): c for c in (race.get("all_combinations") or [])}
        for comb in selected:
            c = (comb if isinstance(comb, str) else "").strip().replace(" ", "")
            if not c:
                continue
            cand = combs.get(c)
            odds = float(cand.get("ratio") or cand.get("odds") or 0) if cand else 0
            prob = float(cand.get("probability") or cand.get("score") or 0) if cand else 0
            hit = c == actual
            out.append({
                "stake": fixed_stake,
                "odds": odds,
                "hit": hit,
                "probability": prob,
            })
    return out
