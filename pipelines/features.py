"""
Build player-level history and point-in-time features (ELO, rolling stats).

Used by the train pipeline; outputs can also feed the dashboard (latest stats per player).
"""
import numpy as np
import pandas as pd

from analytics.config import ROLL_WINDOW, LAST_N_WIN_AVG, ELO_K, ELO_INIT, ELO_SCALE


def build_player_history(matches: pd.DataFrame) -> pd.DataFrame:
    """
    One row per player per match: date, player, opponent, surface, rank, won, ace, minutes, bpSaved, bpFaced.
    Sorted by (player, date).
    """
    rows = []
    for _, row in matches.iterrows():
        rows.append({
            "date": row["tourney_date"],
            "player": row["winner_name"],
            "opponent": row["loser_name"],
            "surface": row["surface"],
            "rank": row["winner_rank"],
            "won": 1,
            "ace": row["w_ace"],
            "minutes": row["minutes"],
            "bpSaved": row["w_bpSaved"],
            "bpFaced": row["w_bpFaced"],
        })
        rows.append({
            "date": row["tourney_date"],
            "player": row["loser_name"],
            "opponent": row["winner_name"],
            "surface": row["surface"],
            "rank": row["loser_rank"],
            "won": 0,
            "ace": row["l_ace"],
            "minutes": row["minutes"],
            "bpSaved": row["l_bpSaved"],
            "bpFaced": row["l_bpFaced"],
        })
    df = pd.DataFrame(rows)
    return df.sort_values(["player", "date"]).reset_index(drop=True)


def add_elo(
    player_hist: pd.DataFrame,
    matches: pd.DataFrame,
    return_final_elo: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, dict[str, float]]:
    """
    Compute point-in-time ELO; merge elo_before into player_hist.
    Expects matches sorted by tourney_date.

    If return_final_elo is True, returns (player_hist, current_elo_dict).
    """
    elo: dict[str, float] = {}
    elo_rows = []

    for _, row in matches.iterrows():
        date = row["tourney_date"]
        w, l = row["winner_name"], row["loser_name"]
        r_w = elo.get(w, ELO_INIT)
        r_l = elo.get(l, ELO_INIT)
        elo_rows.append({"date": date, "player": w, "elo_before": r_w})
        elo_rows.append({"date": date, "player": l, "elo_before": r_l})
        e_w = 1.0 / (1.0 + 10.0 ** ((r_l - r_w) / ELO_SCALE))
        elo[w] = r_w + ELO_K * (1.0 - e_w)
        elo[l] = r_l + ELO_K * (0.0 - (1.0 - e_w))

    elo_df = pd.DataFrame(elo_rows).drop_duplicates(subset=["date", "player"])
    out = player_hist.merge(elo_df, on=["date", "player"], how="left")
    out["elo_before"] = out["elo_before"].fillna(ELO_INIT)
    if return_final_elo:
        return out, elo
    return out


def _surface_win_pct_rolling(g: pd.DataFrame) -> pd.Series:
    return g.groupby("surface")["won"].transform(
        lambda x: x.shift().rolling(ROLL_WINDOW, min_periods=1).mean()
    )


def add_rolling_features(player_hist: pd.DataFrame) -> pd.DataFrame:
    """
    Add rolling_win_pct, last3_win_avg, surface_win_pct, rolling_ace_avg,
    rolling_minutes_avg, bp_save_pct, rolling_bp_save. All point-in-time (shift).
    """
    out = player_hist.copy()

    out["rolling_win_pct"] = (
        out.groupby("player")["won"]
        .transform(lambda x: x.shift().rolling(ROLL_WINDOW, min_periods=1).mean())
    )
    out["last3_win_avg"] = (
        out.groupby("player")["won"]
        .transform(lambda x: x.shift().rolling(LAST_N_WIN_AVG, min_periods=1).mean())
    )
    out["surface_win_pct"] = (
        out.groupby("player", group_keys=False)
        .apply(_surface_win_pct_rolling)
        .values
    )
    out["rolling_ace_avg"] = (
        out.groupby("player")["ace"]
        .transform(lambda x: x.shift().rolling(ROLL_WINDOW, min_periods=1).mean())
    )
    out["rolling_minutes_avg"] = (
        out.groupby("player")["minutes"]
        .transform(lambda x: x.shift().rolling(ROLL_WINDOW, min_periods=1).mean())
    )
    out["bp_save_pct"] = np.where(
        out["bpFaced"] > 0,
        out["bpSaved"] / out["bpFaced"],
        np.nan,
    )
    out["rolling_bp_save"] = (
        out.groupby("player")["bp_save_pct"]
        .transform(lambda x: x.shift().rolling(ROLL_WINDOW, min_periods=1).mean())
    )
    return out


def build_player_hist_with_features(matches: pd.DataFrame) -> pd.DataFrame:
    """
    Full pipeline: player history -> ELO -> rolling features.
    """
    player_hist = build_player_history(matches)
    player_hist = add_elo(player_hist, matches)
    player_hist = add_rolling_features(player_hist)
    return player_hist
