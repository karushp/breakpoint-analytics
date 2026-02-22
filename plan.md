# Match prediction pipeline & dashboard

## Overview

- **Model:** XGBoost classifier trained on historical match data with point-in-time features (ELO, rolling win %, surface win %, last 3 win avg, aces, minutes, BP save %, rank diff).
- **Data:** New match data is added daily (year CSVs + ongoing tourneys). The model is re-run whenever new data is available.
- **Dashboard (later):** User selects two players; app shows win probability and key stats (ELO, form, surface, etc.).

---

## 1. Daily pipeline (re-run when new data is added)

### Steps

1. **Ingest**
   - Load all historical matches from config: year CSVs (e.g. 2024, 2025, 2026) and optionally ongoing tourneys.
   - Normalize `tourney_date` to datetime, sort by date.
   - Result: single `historical_matches` DataFrame.

2. **Player-level history**
   - One row per player per match: date, player, opponent, surface, rank, won, ace, minutes, bpSaved, bpFaced.
   - Sorted by (player, date).

3. **ELO (point-in-time)**
   - Iterate matches in date order; maintain current ELO per player (default 1500, K=32).
   - For each match store pre-match ELO for winner and loser; then update both.
   - Merge `elo_before` into player history.

4. **Rolling features (point-in-time)**
   - Rolling win % (last 10), last 3 win avg, surface win %, rolling ace avg, rolling minutes avg, rolling BP save %.
   - All use `shift()` so only past matches are used.

5. **Match-level feature matrix**
   - For each match: lookup both players' stats on that date; build diffs (rank_diff, elo_diff, form_diff, last3_win_diff, surface_win_diff, ace_diff, minutes_diff, bp_diff).
   - Two rows per match (winner perspective target=1, loser perspective target=0).
   - Encode surface (get_dummies), fill NaNs, define `feature_cols`.

6. **Train / val / test**
   - Time-based split (e.g. 60% / 20% / 20% by date).
   - Train XGBoost with early stopping on validation set.
   - Save: fitted model, `feature_cols`, and (optional) latest player stats for dashboard.

7. **Outputs**
   - `outputs/model.pkl` (or equivalent): trained XGBoost model.
   - `outputs/feature_cols.json`: list of feature names in order.
   - `outputs/player_stats_latest.csv`: current ELO and rolling stats per player (for dashboard lookups).

### Scheduling

- Run once per day after new data is available (cron/scheduler).
- No incremental training: full recompute of features and retrain so point-in-time logic stays correct.

---

## 2. Dashboard (to build later)

- **Input:** User selects Player A and Player B (and optionally surface).
- **Lookup:** For both players, get current stats from latest run (ELO, last3_win_avg, rolling_win_pct, surface_win_pct, etc.).
- **Feature row:** Build one row with same `feature_cols`: diffs (A − B) and surface dummies.
- **Predict:** Load saved model, run `predict_proba` → P(A wins).
- **Display:** Win probability for A and B; optional breakdown of stats (ELO, form, last 3, surface %, etc.).

---

## 3. Code layout

| Path | Purpose |
|------|--------|
| `analytics/config.py` | Data URLs, years, dirs (DATA_RAW_DIR, OUTPUTS_DIR, etc.). |
| `pipelines/ingest.py` | Load year CSVs + optional ongoing → `historical_matches`. |
| `pipelines/features.py` | Build `player_hist`, ELO, rolling features. |
| `pipelines/train_model.py` | Build match matrix, split, train XGBoost, save model + feature_cols + player stats. |

Dashboard code will be added later (separate app or under a `dashboard/` or `app/` area).

---

## 4. Running the pipeline

From repo root:

```bash
python pipelines/train_model.py
# or
python -m pipelines.train_model
```

Outputs go to `outputs/` (create if missing). Use same outputs for the dashboard when it's built.
