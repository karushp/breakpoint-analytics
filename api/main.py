"""
FastAPI app for match prediction. Deploy to Render; front-end on GitHub Pages.

Endpoints:
  GET  /health  - readiness
  POST /predict - body: { "player_a", "player_b", "surface" } -> { "prob_a_wins" }
  GET  /players - list player names for dropdowns
"""
import json
import os
from pathlib import Path

import pandas as pd
import joblib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Outputs live in repo root outputs/ (Render clones full repo)
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = REPO_ROOT / "outputs"
MODEL_PATH = OUTPUTS / "model.pkl"
FEATURE_COLS_PATH = OUTPUTS / "feature_cols.json"
PLAYER_STATS_PATH = OUTPUTS / "player_stats_latest.csv"

app = FastAPI(title="Breakpoint Analytics API", version="0.1.0")

# Allow GitHub Pages and localhost. Set ALLOWED_ORIGINS env on Render to restrict.
_allowed = os.environ.get("ALLOWED_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed.split(",") if _allowed != "*" else ["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Lazy-loaded so Render can start even before outputs/ is in the repo
_model = None
_feature_cols = None
_player_stats = None
_load_error = None


def _load_artifacts():
    global _model, _feature_cols, _player_stats, _load_error
    if _model is not None:
        return
    if _load_error is not None:
        raise _load_error
    if not MODEL_PATH.exists():
        _load_error = FileNotFoundError(
            f"Model not found: {MODEL_PATH}. Run the pipeline and commit outputs/."
        )
        raise _load_error
    try:
        _model = joblib.load(MODEL_PATH)
        with open(FEATURE_COLS_PATH) as f:
            _feature_cols = json.load(f)
        _player_stats = pd.read_csv(PLAYER_STATS_PATH)
        _player_stats["date"] = pd.to_datetime(_player_stats["date"])
        _player_stats = (
            _player_stats.sort_values("date")
            .groupby("player", as_index=False)
            .last()
        )
    except Exception as e:
        _load_error = e
        raise


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/players")
def players():
    try:
        _load_artifacts()
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail="Model not ready. Run the pipeline and commit outputs/ to the repo, then redeploy.",
        ) from e
    names = sorted(_player_stats["player"].astype(str).tolist())
    return {"players": names}


class PredictRequest(BaseModel):
    player_a: str
    player_b: str
    surface: str = "Hard"  # Hard | Clay | Grass


@app.post("/predict")
def predict(req: PredictRequest):
    try:
        _load_artifacts()
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail="Model not ready. Run the pipeline and commit outputs/ to the repo, then redeploy.",
        ) from e
    a = req.player_a.strip()
    b = req.player_b.strip()
    if a == b:
        raise HTTPException(status_code=400, detail="Choose two different players")
    surface = req.surface.strip().capitalize()
    if surface not in ("Hard", "Clay", "Grass"):
        raise HTTPException(status_code=400, detail="surface must be Hard, Clay, or Grass")

    stats = _player_stats
    row_a = stats[stats["player"] == a]
    row_b = stats[stats["player"] == b]
    if row_a.empty:
        raise HTTPException(status_code=404, detail=f"Player not found: {a}")
    if row_b.empty:
        raise HTTPException(status_code=404, detail=f"Player not found: {b}")
    sa = row_a.iloc[0]
    sb = row_b.iloc[0]

    def _f(s, key, default=0.0):
        v = s.get(key)
        return float(v) if pd.notna(v) and v != "" else default

    # Diffs: A - B (positive => A stronger on that feature)
    rank_diff = 0.0  # not in player_stats; use 0
    elo_diff = _f(sa, "elo_before") - _f(sb, "elo_before")
    form_diff = _f(sa, "rolling_win_pct") - _f(sb, "rolling_win_pct")
    last3_win_diff = _f(sa, "last3_win_avg") - _f(sb, "last3_win_avg")
    surface_win_diff = _f(sa, "surface_win_pct") - _f(sb, "surface_win_pct")
    ace_diff = _f(sa, "rolling_ace_avg") - _f(sb, "rolling_ace_avg")
    minutes_diff = _f(sa, "rolling_minutes_avg") - _f(sb, "rolling_minutes_avg")
    bp_diff = _f(sa, "rolling_bp_save") - _f(sb, "rolling_bp_save")

    # Surface dummies (train used drop_first => Clay is reference)
    surface_Grass = 1.0 if surface == "Grass" else 0.0
    surface_Hard = 1.0 if surface == "Hard" else 0.0

    row = {
        "rank_diff": rank_diff,
        "elo_diff": elo_diff,
        "form_diff": form_diff,
        "last3_win_diff": last3_win_diff,
        "surface_win_diff": surface_win_diff,
        "ace_diff": ace_diff,
        "minutes_diff": minutes_diff,
        "bp_diff": bp_diff,
        "surface_Grass": surface_Grass,
        "surface_Hard": surface_Hard,
    }
    X = pd.DataFrame([row])[_feature_cols]
    prob_a_wins = float(_model.predict_proba(X)[0, 1])

    def _stat(s, key):
        v = s.get(key)
        if pd.isna(v) or v == "":
            return None
        try:
            return round(float(v), 4)
        except (TypeError, ValueError):
            return None

    stats_a = {
        "elo": _stat(sa, "current_elo") or _stat(sa, "elo_before"),
        "rolling_win_pct": _stat(sa, "rolling_win_pct"),
        "last3_win_avg": _stat(sa, "last3_win_avg"),
        "surface_win_pct": _stat(sa, "surface_win_pct"),
        "rolling_ace_avg": _stat(sa, "rolling_ace_avg"),
        "rolling_minutes_avg": _stat(sa, "rolling_minutes_avg"),
        "rolling_bp_save": _stat(sa, "rolling_bp_save"),
    }
    stats_b = {
        "elo": _stat(sb, "current_elo") or _stat(sb, "elo_before"),
        "rolling_win_pct": _stat(sb, "rolling_win_pct"),
        "last3_win_avg": _stat(sb, "last3_win_avg"),
        "surface_win_pct": _stat(sb, "surface_win_pct"),
        "rolling_ace_avg": _stat(sb, "rolling_ace_avg"),
        "rolling_minutes_avg": _stat(sb, "rolling_minutes_avg"),
        "rolling_bp_save": _stat(sb, "rolling_bp_save"),
    }

    def _last5(s):
        out = []
        for i in range(1, 6):
            v = s.get(f"last5_{i}")
            if pd.isna(v) or v == "":
                out.append(None)
            else:
                try:
                    out.append(int(v))
                except (TypeError, ValueError):
                    out.append(None)
        return out

    last5_a = _last5(sa)
    last5_b = _last5(sb)

    return {
        "prob_a_wins": round(prob_a_wins, 4),
        "prob_b_wins": round(1 - prob_a_wins, 4),
        "stats_a": stats_a,
        "stats_b": stats_b,
        "last5_a": last5_a,
        "last5_b": last5_b,
    }
