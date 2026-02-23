# Match prediction pipeline & dashboard

## Overview

- **Model:** XGBoost classifier trained on historical match data with point-in-time features (ELO, rolling win %, surface win %, last 3 win avg, aces, minutes, BP save %, rank diff).
- **Data:** New match data is added daily (year CSVs + ongoing tourneys from TennisMyLife). The model is re-run whenever new data is available.
- **Dashboard (implemented):** User selects two players; app shows win probability and a scorecard of key stats (ELO, form, surface %, aces, minutes, BP save %). Front-end on GitHub Pages; prediction API on Render.

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
   - Save: fitted model, `feature_cols`, and latest player stats for the dashboard API.

7. **Outputs**
   - `outputs/model.pkl`: trained XGBoost model.
   - `outputs/feature_cols.json`: list of feature names in order.
   - `outputs/player_stats_latest.csv`: current ELO and rolling stats per player (for dashboard API).

### Scheduling

- GitHub Actions workflow runs daily at **8:00 JST** (see `.github/workflows/update-model.yml`): fetches data, runs full pipeline, commits updated `outputs/` to the repo.
- No incremental training: full recompute of features and retrain so point-in-time logic stays correct.

---

## 2. Dashboard (implemented)

- **Front-end (GitHub Pages):** Static site in `dashboard/`; published from `docs/` (synced via workflow or manual copy). User selects Player 1 and Player 2 via type-ahead search, then clicks "Generate Comparison".
- **Backend (Render):** FastAPI app in `api/` serves:
  - `GET /health` – readiness
  - `GET /players` – list of player names for autocomplete
  - `POST /predict` – body `{ player_a, player_b, surface }` → `{ prob_a_wins, prob_b_wins, stats_a, stats_b }`
- **Flow:** Dashboard calls `/players` on load; on "Generate Comparison" it calls `/predict` with the two selected players. API loads `outputs/` from the repo, builds the feature row (diffs A − B + surface dummies), runs `predict_proba`, and returns win probabilities plus per-player stats for the scorecard.
- **Display:** Win probability bar (green = higher, red = lower), placeholder "Last 5 Matches" icons, and a scorecard of seven metrics from the data: ELO, Form (win % last 10), Win % (last 3), Surface win %, Aces (avg per match), Minutes (avg per match), Break points saved %.

---

## 3. Code layout

| Path | Purpose |
|------|--------|
| `analytics/config.py` | Data URLs, years, dirs, model params, output filenames. |
| `pipelines/ingest.py` | Load year CSVs + optional ongoing → `historical_matches`. |
| `pipelines/features.py` | Build `player_hist`, ELO, rolling features. |
| `pipelines/train_model.py` | Build match matrix, split, train XGBoost, save model + feature_cols + player stats. |
| `api/main.py` | FastAPI app: /health, /players, /predict (reads `outputs/`). |
| `api/requirements.txt` | API dependencies for Render. |
| `dashboard/` | Front-end source: index.html, css/, js/ (theme, styles, app, config). |
| `docs/` | GitHub Pages publish root (synced from `dashboard/`). |
| `.github/workflows/update-model.yml` | Daily 8:00 JST: run pipeline, commit outputs. |
| `.github/workflows/deploy-dashboard.yml` | On push to dashboard/: sync dashboard → docs. |

---

## 4. Running the pipeline

From repo root:

```bash
uv sync
python -m pipelines.train_model
```

Outputs go to `outputs/`. The Render API and GitHub Actions use these outputs; see **README.md** for deploy and schedule details.
