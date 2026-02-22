# 🎾 Breakpoint Analytics

A data-driven tennis analytics project that predicts match outcomes using Elo ratings and an XGBoost model trained on [TennisMyLife](https://stats.tennismylife.org) data.

## 🏗️ Architecture

```
TennisMyLife (stats.tennismylife.org) — year CSVs + ongoing tourneys
            ↓
      Python pipelines (ingest → features → train)
            ↓
   outputs/ (model.pkl, feature_cols.json, player_stats_latest.csv)
            ↓
 Dashboard (planned): select two players → win probability + stats
```

- **Data:** 2024–2026 year CSVs and ongoing tourneys
- **Model:** XGBoost with point-in-time features (ELO, rolling win %, surface win %, last 3 win avg, aces, minutes, BP save %, rank diff)
- **Pipeline:** Full recompute and retrain (ingest → features → train → save to `outputs/`)
- **Scheduler:** GitHub Actions runs the pipeline daily at **8:00 JST** and commits updated model and stats to the repo

## 📁 Project structure

```
breakpoint-analytics/
├── .github/workflows/
│   └── update-model.yml  # Daily 8:00 JST: fetch data, retrain, commit outputs
├── analytics/
│   └── config.py         # Data URLs, years, output dirs, model params
├── pipelines/
│   ├── ingest.py         # Load historical matches
│   ├── features.py       # Player history, ELO, rolling features
│   └── train_model.py    # Match matrix, train XGBoost, save artifacts
├── outputs/               # model.pkl, feature_cols.json, player_stats_latest.csv
├── notebooks/             # Jupyter notebooks (e.g. 220226.ipynb)
├── plan.md                # Pipeline and dashboard plan
├── pyproject.toml
└── README.md
```

## 🚀 Quick start

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (or pip) for dependencies

### Install

```bash
git clone <your-repo-url>
cd breakpoint-analytics
uv sync
# or: pip install -e .
```

### Run the pipeline

```bash
# From repo root
python pipelines/train_model.py
# or
python -m pipelines.train_model
```

Outputs are written to `outputs/`: trained model, feature column list, and latest player stats for dashboard lookups.

See **plan.md** for the full pipeline description and planned dashboard.

## ⏰ Automated updates (GitHub Actions)

A workflow runs **every morning at 8:00 JST** (23:00 UTC):

1. Fetches the latest match data from TennisMyLife (year CSVs + ongoing tourneys).
2. Rebuilds player history, ELO, and rolling features.
3. Retrains the XGBoost model and writes new artifacts to `outputs/`.
4. Commits and pushes the updated `outputs/` (model, feature_cols, player_stats) to the repo.

- **Workflow file:** `.github/workflows/update-model.yml`
- **Manual run:** In the repo, go to **Actions → Update model (daily) → Run workflow** to trigger a run on demand.

## 📊 Data source

- [TennisMyLife](https://stats.tennismylife.org/data) — year CSVs (e.g. `2024.csv`, `2025.csv`, `2026.csv`) and `ongoing_tourneys.csv`

## 📄 License

See repository for license and acknowledgments.
