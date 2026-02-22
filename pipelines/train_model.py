"""
Daily train pipeline: ingest -> player features (ELO, rolling) -> match matrix -> train XGBoost -> save artifacts.

Run from repo root:  python pipelines/train_model.py   or   python -m pipelines.train_model
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss

# Ensure project root is on path when run as script
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from analytics.config import (
    OUTPUTS_DIR,
    ELO_INIT,
    TRAIN_FRAC,
    VAL_FRAC,
    MODEL_FILENAME,
    FEATURE_COLS_FILENAME,
    PLAYER_STATS_FILENAME,
    XGB_N_ESTIMATORS,
    XGB_MAX_DEPTH,
    XGB_LEARNING_RATE,
    XGB_SUBSAMPLE,
    XGB_COLSAMPLE_BYTREE,
    XGB_EARLY_STOPPING_ROUNDS,
    XGB_RANDOM_STATE,
)
from pipelines.ingest import load_historical_matches
from pipelines.features import (
    build_player_history,
    add_elo,
    add_rolling_features,
)


def _build_match_matrix(matches: pd.DataFrame, player_hist: pd.DataFrame) -> pd.DataFrame:
    """Build match-level feature matrix (diffs) from player_hist lookups."""
    match_rows = []
    for _, row in matches.iterrows():
        date, surface = row["tourney_date"], row["surface"]
        w, l = row["winner_name"], row["loser_name"]
        w_hist = player_hist[(player_hist["player"] == w) & (player_hist["date"] == date)]
        l_hist = player_hist[(player_hist["player"] == l) & (player_hist["date"] == date)]
        if w_hist.empty or l_hist.empty:
            continue
        w_stats, l_stats = w_hist.iloc[0], l_hist.iloc[0]
        rank_diff_w = (
            (row["loser_rank"] - row["winner_rank"])
            if pd.notna(row["winner_rank"]) and pd.notna(row["loser_rank"])
            else np.nan
        )
        match_rows.append({
            "date": date,
            "surface": surface,
            "rank_diff": rank_diff_w,
            "elo_diff": w_stats["elo_before"] - l_stats["elo_before"],
            "form_diff": w_stats["rolling_win_pct"] - l_stats["rolling_win_pct"],
            "last3_win_diff": w_stats["last3_win_avg"] - l_stats["last3_win_avg"],
            "surface_win_diff": w_stats["surface_win_pct"] - l_stats["surface_win_pct"],
            "ace_diff": w_stats["rolling_ace_avg"] - l_stats["rolling_ace_avg"],
            "minutes_diff": w_stats["rolling_minutes_avg"] - l_stats["rolling_minutes_avg"],
            "bp_diff": w_stats["rolling_bp_save"] - l_stats["rolling_bp_save"],
            "target": 1,
        })
        rank_diff_l = (
            (row["winner_rank"] - row["loser_rank"])
            if pd.notna(row["winner_rank"]) and pd.notna(row["loser_rank"])
            else np.nan
        )
        match_rows.append({
            "date": date,
            "surface": surface,
            "rank_diff": rank_diff_l,
            "elo_diff": l_stats["elo_before"] - w_stats["elo_before"],
            "form_diff": l_stats["rolling_win_pct"] - w_stats["rolling_win_pct"],
            "last3_win_diff": l_stats["last3_win_avg"] - w_stats["last3_win_avg"],
            "surface_win_diff": l_stats["surface_win_pct"] - w_stats["surface_win_pct"],
            "ace_diff": l_stats["rolling_ace_avg"] - w_stats["rolling_ace_avg"],
            "minutes_diff": l_stats["rolling_minutes_avg"] - w_stats["rolling_minutes_avg"],
            "bp_diff": l_stats["rolling_bp_save"] - w_stats["rolling_bp_save"],
            "target": 0,
        })
    return pd.DataFrame(match_rows)


def run(
    years: list[int] | None = None,
    include_ongoing: bool = True,
    train_frac: float | None = None,
    val_frac: float | None = None,
    out_dir: str | Path | None = None,
):
    """
    Ingest data, build features, train XGBoost, save model + feature_cols + latest player stats.

    Args:
        years: Years to load (default: from config).
        include_ongoing: Whether to include ongoing tourneys CSV.
        train_frac: Fraction of time range for training (default: from config).
        val_frac: Fraction for validation (default: from config); test gets the rest.
        out_dir: Directory for outputs (default: OUTPUTS_DIR under project root).
    """
    train_frac = train_frac if train_frac is not None else TRAIN_FRAC
    val_frac = val_frac if val_frac is not None else VAL_FRAC
    out_dir = Path(out_dir or _ROOT / OUTPUTS_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Ingest
    matches = load_historical_matches(years=years, include_ongoing=include_ongoing)
    if matches.empty:
        raise RuntimeError("No match data loaded.")
    print(f"Loaded {len(matches)} matches.")

    # 2. Player history + ELO + rolling features
    player_hist = build_player_history(matches)
    player_hist, current_elo = add_elo(player_hist, matches, return_final_elo=True)
    player_hist = add_rolling_features(player_hist)

    # 3. Match-level matrix
    model_df = _build_match_matrix(matches, player_hist)
    model_df = pd.get_dummies(model_df, columns=["surface"], drop_first=True)
    model_df = model_df.fillna(0)
    feature_cols = [c for c in model_df.columns if c not in ("target", "date")]
    print(f"Feature matrix: {model_df.shape}, features: {feature_cols}")

    # 4. Time split (from config unless overridden)
    q_train = train_frac
    q_val = train_frac + val_frac
    train_end = model_df["date"].quantile(q_train)
    val_end = model_df["date"].quantile(q_val)
    train_df = model_df[model_df["date"] <= train_end]
    val_df = model_df[(model_df["date"] > train_end) & (model_df["date"] <= val_end)]
    test_df = model_df[model_df["date"] > val_end]

    X_train = train_df[feature_cols]
    y_train = train_df["target"]
    X_val = val_df[feature_cols]
    y_val = val_df["target"]
    X_test = test_df[feature_cols]
    y_test = test_df["target"]
    print(f"Train {len(train_df)} / Val {len(val_df)} / Test {len(test_df)}")

    # 5. Train (XGBoost params from config)
    clf = XGBClassifier(
        n_estimators=XGB_N_ESTIMATORS,
        max_depth=XGB_MAX_DEPTH,
        learning_rate=XGB_LEARNING_RATE,
        subsample=XGB_SUBSAMPLE,
        colsample_bytree=XGB_COLSAMPLE_BYTREE,
        early_stopping_rounds=XGB_EARLY_STOPPING_ROUNDS,
        random_state=XGB_RANDOM_STATE,
    )
    clf.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )

    preds = clf.predict(X_test)
    probs = clf.predict_proba(X_test)[:, 1]
    print("Test Accuracy:", accuracy_score(y_test, preds))
    print("Test ROC AUC:", roc_auc_score(y_test, probs))
    print("Test Log Loss:", log_loss(y_test, probs))

    # 6. Save artifacts (filenames from config)
    joblib.dump(clf, out_dir / MODEL_FILENAME)
    with open(out_dir / FEATURE_COLS_FILENAME, "w") as f:
        json.dump(feature_cols, f, indent=2)

    # Latest stats per player (last row per player + current ELO)
    last = player_hist.sort_values("date").groupby("player").last().reset_index()
    last = last[
        [
            "player", "date", "elo_before", "rolling_win_pct", "last3_win_avg",
            "surface_win_pct", "rolling_ace_avg", "rolling_minutes_avg", "rolling_bp_save",
        ]
    ]
    last["current_elo"] = last["player"].map(current_elo).fillna(ELO_INIT)
    last.to_csv(out_dir / PLAYER_STATS_FILENAME, index=False)
    print(f"Saved model, feature_cols, and player_stats_latest to {out_dir}")


if __name__ == "__main__":
    run()
