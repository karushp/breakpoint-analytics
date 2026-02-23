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
   API (Render): FastAPI /predict, /players, /health
            ↓
   Dashboard (GitHub Pages): select two players → win probability + stats
```

- **Data:** 2024–2026 year CSVs and ongoing tourneys
- **Model:** XGBoost with point-in-time features (ELO, rolling win %, surface win %, last 3 win avg, aces, minutes, BP save %, rank diff)
- **Pipeline:** Full recompute and retrain (ingest → features → train → save to `outputs/`)
- **Scheduler:** GitHub Actions runs the pipeline daily at **8:00 JST** and commits updated model and stats to the repo

## 📁 Project structure

```
breakpoint-analytics/
├── .github/workflows/
│   ├── update-model.yml     # Daily 8:00 JST: fetch data, retrain, commit outputs
│   └── deploy-dashboard.yml # On push to dashboard/: sync dashboard/ → docs/
├── analytics/
│   └── config.py            # Data URLs, years, output dirs, model params
├── api/                     # Render: FastAPI backend
│   ├── main.py              # /health, /players, /predict
│   └── requirements.txt    # API deps (fastapi, uvicorn, pandas, xgboost, …)
├── dashboard/               # Front-end source (GitHub Pages)
│   ├── index.html
│   ├── css/style.css
│   └── js/config.js, app.js
├── docs/                    # GitHub Pages publish root (served at /)
│   └── (synced from dashboard/ by workflow or manual copy)
├── pipelines/
│   ├── ingest.py, features.py, train_model.py
├── outputs/                 # model.pkl, feature_cols.json, player_stats_latest.csv
├── notebooks/
├── plan.md
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

Outputs are written to `outputs/`: trained model, feature column list, and latest player stats for the dashboard API.

See **plan.md** for the full pipeline description.

---

## 🌐 Dashboard (Render + GitHub Pages)

- **Backend (Render):** FastAPI serves `/health`, `/players`, `/predict`. It reads `outputs/` from the repo (Render deploys the full repo).
- **Front-end (GitHub Pages):** Static site in `dashboard/`; published from the `docs/` folder (or run the deploy workflow so `docs/` stays in sync with `dashboard/`).

### Run the API locally

```bash
cd api
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0
# API at http://127.0.0.1:8000; set dashboard/js/config.js to this URL for local dev
```

### Deploy backend to Render

1. In [Render](https://render.com), create a **Web Service**.
2. Connect this repo. Set **Root Directory** to empty (repo root) so `outputs/` and `api/` are available.
3. **Build command:** `pip install -r api/requirements.txt`
4. **Start command:** `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
5. (Optional) **Environment:** `ALLOWED_ORIGINS` = `https://YOUR_USER.github.io` to restrict CORS.
6. After deploy, set `dashboard/js/config.js` and `docs/js/config.js` to your Render URL (e.g. `https://breakpoint-analytics.onrender.com`).

### Enable GitHub Pages (front-end)

1. Repo **Settings → Pages**. Source: **Deploy from a branch**.
2. Branch: **main**, folder: **/docs**. Save.
3. Site URL: `https://YOUR_USER.github.io/breakpoint-analytics/`.
4. After the API is on Render, set the API URL in `docs/js/config.js` (and in `dashboard/js/config.js` for future syncs) and commit. Pushes that change `dashboard/` trigger the **Deploy dashboard** workflow to sync `docs/`.

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
