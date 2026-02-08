Nice — that’s a solid, realistic stack. One small heads-up first (important, but solvable):

> **GitHub Pages can’t run Python**
> It only hosts **static files (HTML/CSS/JS)**.

So the clean way to do this is:

* **Python → data + analysis (offline / scheduled)**
* **GitHub Pages → static dashboard (frontend)**

This is actually a *great* architecture for a data project 👍

Below is a **clear project layout + workflow** you can directly plan against.

---

# 🏗️ Tennis Analytics Dashboard — Project Layout

## 1️⃣ High-Level Architecture

```
Jeff Sackmann CSVs / Live API
            ↓
      Python ETL + Analytics
            ↓
   Precomputed JSON / CSV
            ↓
 Static Dashboard (GitHub Pages)
```

Python does the thinking.
GitHub Pages just **displays results**.

### 📊 Data Sources (Clarified)

**Jeff Sackmann Tennis Data:**
* **Source**: GitHub repo `JeffSackmann/tennis_atp` (https://github.com/JeffSackmann/tennis_atp)
* **Access Method**: Git submodule or direct CSV download
* **Files**: `atp_matches_YYYY.csv` (one file per year)
* **Update Frequency**: Repository updated regularly (check commit history)
* **Data Format**: CSV with columns: tourney_date, winner_name, loser_name, score, surface, etc.

**Live API (Optional - Phase 3):**
* **Options**: 
  * Tennis API (tennis-api.com) - requires API key
  * RapidAPI Tennis endpoints - rate limited
  * ATP official data (if available)
* **Use Case**: Recent matches not yet in Sackmann CSVs
* **Authentication**: Store API keys in GitHub Secrets
* **Rate Limits**: Implement retry logic with exponential backoff

---

## 2️⃣ Repo Structure (Recommended)

```
tennis-analytics-dashboard/
│
├── data/
│   ├── raw/
│   │   ├── atp_matches_2023.csv
│   │   └── atp_matches_2024.csv
│   │
│   ├── processed/
│   │   ├── players.csv
│   │   ├── matches_clean.csv
│   │   ├── h2h.csv
│   │   └── surface_stats.csv
│
├── analytics/
│   ├── elo.py
│   ├── feature_engineering.py
│   ├── win_probability.py
│   └── utils.py
│
├── pipelines/
│   ├── ingest_sackmann.py
│   ├── ingest_live_api.py
│   ├── build_features.py
│   └── export_dashboard_data.py
│
├── dashboard/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── assets/
│
├── outputs/
│   ├── player_summary.json
│   ├── matchup_stats.json
│   └── rankings.json
│
├── notebooks/
│   └── exploration.ipynb
│
├── .github/
│   └── workflows/
│       └── update-data.yml
│
├── requirements.txt
├── README.md
├── Makefile
└── .gitignore  # Exclude large data files, __pycache__, etc.
```

---

## 3️⃣ Python Side — What Each Part Does

### 🧩 Ingestion

**`pipelines/ingest_sackmann.py`**

* Pull / update Sackmann CSVs
  * Use git submodule or `wget`/`curl` to fetch latest CSVs
  * Check for new files by comparing file hashes or modification dates
* Normalize player names & IDs
  * **Name Normalization**: Handle variations like "Novak Djokovic" vs "N. Djokovic"
  * **ID System**: Use ATP player IDs from data, or create stable IDs based on normalized names
  * **Matching Strategy**: Fuzzy matching for name variations (use `fuzzywuzzy` or `rapidfuzz`)
  * **Canonical Names**: Maintain a `players.csv` lookup table with canonical name → ID mapping
* Append new matches only
  * Track last processed match date/tournament
  * Only process matches newer than last run
  * Handle duplicate detection (same match_id or tourney_date + players)

**Optional**: live API ingestion for recent matches
* **`pipelines/ingest_live_api.py`**
* Only fetch matches from last 7 days (to avoid overlap with Sackmann data)
* Merge with historical data, deduplicate
* Handle API failures gracefully (log errors, continue with historical data only)

---

### 🧠 Feature Engineering

**`analytics/feature_engineering.py`**
Compute:

* Career win %
  * Total wins / (wins + losses) across all matches
  * Handle players with < 5 matches: return None or use prior (e.g., 50%)
* Last N matches form
  * **N = 10** for recent form (configurable)
  * Weight recent matches more heavily (exponential decay)
  * Handle players with < N matches: use available matches, flag as "limited data"
* Surface-specific win %
  * Hard, Clay, Grass, Carpet (if available)
  * Minimum 3 matches per surface to report stat
* H2H stats
  * Direct head-to-head record
  * Surface-specific H2H
  * Last meeting date and result
  * Handle no H2H: return zeros, show "No previous meetings"
* Tournament performance
  * Win % by tournament level (Grand Slam, Masters, ATP 250, etc.)
  * Recent tournament results (last 3 tournaments)

---

### 📈 Strength Models

**`analytics/elo.py`**

* Global Elo
  * **Starting Elo**: 1500 (standard)
  * **K-factor**: 
    * K = 32 for regular matches
    * K = 48 for Grand Slams (more weight)
    * K = 24 for smaller tournaments
  * **Formula**: `New_Elo = Old_Elo + K * (Actual_Score - Expected_Score)`
    * Expected_Score = 1 / (1 + 10^((Opponent_Elo - Player_Elo) / 400))
* Surface-adjusted Elo
  * Maintain separate Elo ratings per surface (Hard, Clay, Grass)
  * **Surface Transfer**: When surface-specific Elo unavailable, use:
    * `Surface_Elo = Global_Elo + Surface_Adjustment`
    * Surface adjustments: Hard = 0, Clay = -50, Grass = +30 (example, tune based on data)
* Decay for recency
  * **Time Decay**: Apply exponential decay to older matches
  * Formula: `Weight = e^(-days_ago / decay_constant)`
  * **Decay Constant**: 365 days (matches older than 1 year have < 37% weight)
  * **Recency Boost**: Matches in last 30 days get 1.2x weight

**`analytics/win_probability.py`**

* **Primary Method**: Elo-based probability (simpler, interpretable)
  * Use surface-adjusted Elo when available, fallback to global Elo
  * Formula: `P(Player_A_wins) = 1 / (1 + 10^((Elo_B - Elo_A) / 400))`
* **Optional Enhancement**: Logistic regression (Phase 2+)
  * Features: Elo difference, surface-specific Elo, recent form, H2H record, age, ranking
  * Train on historical matches, validate on holdout set
  * Fallback to Elo-based if model unavailable
* Output:

  ```json
  {
    "player_a_win_prob": 0.62,
    "player_b_win_prob": 0.38,
    "confidence": "high",  // high/medium/low based on data quality
    "method": "elo_surface_adjusted"  // or "logistic_regression"
  }
  ```

---

### 📦 Export for Frontend

**`pipelines/export_dashboard_data.py`**

* Output small, fast JSON files:

  * `player_summary.json`
  * `matchup_stats.json`
  * `elo_rankings.json`

👉 These are what GitHub Pages reads.

---

## 4️⃣ Frontend Layout (GitHub Pages)

### 🖥️ Dashboard Sections

#### 1. Player Selector

* Dropdown: Player A
* Dropdown: Player B
* **Player List**: 
  * Include all players with at least 10 matches in dataset
  * Sort alphabetically or by current Elo (configurable)
  * **Search Functionality**: Type-ahead search for large lists (1000+ players)
  * **Inactive Players**: Include but mark as "Inactive" if no matches in last 12 months
  * **Scope**: ATP only for MVP (can add WTA later)

#### 2. Headline Edge Indicator

```
🏆 Predicted Edge
Player A: 62%
Player B: 38%
```

#### 3. Head-to-Head

* Total matches
* Wins / losses
* Last 5 meetings

#### 4. Form Comparison

* Win % last 10 matches
* Recent opponents strength

#### 5. Surface Breakdown

| Surface | Player A | Player B |
| ------- | -------- | -------- |
| Hard    | 68%      | 55%      |
| Clay    | 52%      | 61%      |
| Grass   | 71%      | 49%      |

#### 6. Rankings & Elo Trend

* Current rank
* Elo over time (chart)

---

### 🧠 Frontend Stack (Simple + Powerful)

* HTML + CSS
* Vanilla JS
* **Chart Library**: Chart.js (simpler, lighter) - use for Elo trends and form charts
* Fetch JSON from `/outputs/*.json`
* **Data Loading Strategy**:
  * Load all player summaries on page load (small file, < 500KB)
  * Load matchup stats on-demand when players selected
  * Cache fetched data in memory to avoid redundant requests

Example:

```js
fetch('outputs/matchup_stats.json')
  .then(res => res.json())
  .then(data => renderMatchup(data));
```

### 📋 JSON Data Schemas (Clarified)

**`outputs/player_summary.json`**
```json
{
  "players": [
    {
      "id": "djokovic-n",
      "name": "Novak Djokovic",
      "current_elo": 1850,
      "current_rank": 1,
      "career_win_pct": 0.83,
      "matches_played": 1200,
      "active": true
    }
  ],
  "last_updated": "2024-02-08T12:00:00Z"
}
```

**`outputs/matchup_stats.json`**
```json
{
  "player_a_id": "djokovic-n",
  "player_b_id": "nadal-r",
  "win_probability": {
    "player_a": 0.62,
    "player_b": 0.38,
    "confidence": "high",
    "method": "elo_surface_adjusted"
  },
  "head_to_head": {
    "total_matches": 59,
    "player_a_wins": 30,
    "player_b_wins": 29,
    "last_5": [
      {"date": "2023-06-11", "winner": "djokovic-n", "surface": "clay"},
      ...
    ]
  },
  "form": {
    "player_a": {"last_10_win_pct": 0.80, "recent_opponent_avg_elo": 1650},
    "player_b": {"last_10_win_pct": 0.70, "recent_opponent_avg_elo": 1620}
  },
  "surface_stats": {
    "hard": {"player_a": 0.68, "player_b": 0.55},
    "clay": {"player_a": 0.52, "player_b": 0.61},
    "grass": {"player_a": 0.71, "player_b": 0.49}
  },
  "elo_trends": {
    "player_a": [{"date": "2024-01-01", "elo": 1800}, ...],
    "player_b": [{"date": "2024-01-01", "elo": 1750}, ...]
  }
}
```

**`outputs/elo_rankings.json`**
```json
{
  "rankings": [
    {"rank": 1, "player_id": "djokovic-n", "name": "Novak Djokovic", "elo": 1850},
    ...
  ],
  "last_updated": "2024-02-08T12:00:00Z"
}
```

---

## 5️⃣ Automation (This is the cool part 😎)

### GitHub Actions — Auto Update Data

**`.github/workflows/update-data.yml`**

* **Schedule**: Weekly (Sunday 2 AM UTC) - adjust based on Sackmann update frequency
* **Manual Trigger**: Allow manual workflow dispatch from GitHub UI
* Steps:

  1. **Setup Python Environment**
     * Use `actions/setup-python@v4` with Python 3.10+
     * Install dependencies from `requirements.txt`
     * Cache pip dependencies for faster runs
  2. **Pull Sackmann Data**
     * If using git submodule: `git submodule update --remote`
     * If downloading: `wget` or `curl` latest CSVs
     * Handle failures: log error, use existing data, don't fail workflow
  3. **Run Python Pipeline**
     * Execute: `python pipelines/ingest_sackmann.py`
     * Then: `python pipelines/build_features.py`
     * Then: `python pipelines/export_dashboard_data.py`
     * Set timeout (e.g., 30 minutes) to prevent hanging
  4. **Commit Updated JSON**
     * Only commit if files changed (check `git diff`)
     * Commit message: "Auto-update: Data refresh [timestamp]"
     * Push to `main` branch (or `gh-pages` if using that for GitHub Pages)
  5. **GitHub Pages Auto-Refresh**
     * GitHub Pages automatically rebuilds on push to configured branch
     * **Configuration**: Settings → Pages → Source: `main` branch, `/dashboard` folder

**Error Handling**:
* If data source unavailable: log warning, use cached data, don't fail
* If pipeline fails: send notification (GitHub issue or email), keep old data
* If JSON files corrupted: rollback to previous commit

Result:
👉 **Always-fresh dashboard without a backend server**

---

## 6️⃣ Project Milestones (Very Practical)

### Phase 1 – MVP

* Historical data only
* Player comparison
* No live matches

### Phase 2 – Smart Analytics

* Elo + surface adjustment
* Edge probability
* Recent form weighting

### Phase 3 – Near-Live Feel

* Add live API for today’s matches
* “Data last updated” indicator

---

## 7️⃣ Technical Decisions & Edge Cases

### 🛠️ Python Dependencies

**Core Libraries**:
* `pandas` - Data manipulation and CSV handling
* `numpy` - Numerical computations
* `scikit-learn` - Logistic regression (optional, Phase 2+)
* `rapidfuzz` or `fuzzywuzzy` - Name matching
* `requests` - API calls (if using live API)

**Python Version**: 3.10+ (for type hints and modern features)

### 📁 Data Storage Strategy

* **Raw Data**: 
  * Store in `data/raw/` but **don't commit to git** (too large)
  * Use `.gitignore` to exclude CSV files > 10MB
  * Or use Git LFS for large files (if needed)
* **Processed Data**: 
  * Small CSVs (< 1MB) can be committed
  * JSON outputs should be committed (needed for GitHub Pages)
* **Data Size Estimates**:
  * Raw ATP matches: ~50MB per year
  * Processed JSON: ~5-10MB total (compressed if needed)

### ⚠️ Edge Cases & Error Handling

**Missing Data**:
* Player with no historical matches: Show "Insufficient data" message
* No H2H record: Display "No previous meetings", use Elo only
* Missing surface data: Use global Elo, flag as "surface data unavailable"
* Incomplete match data: Skip matches with missing critical fields (winner, loser, date)

**Data Quality**:
* Handle retirements: Count as loss for retired player
* Handle walkovers: Exclude from Elo calculations (or count as win/loss based on reason)
* Handle duplicate matches: Deduplicate by (tourney_date, winner_name, loser_name)

**Frontend Edge Cases**:
* Same player selected for A and B: Show error message
* Player with < 10 matches: Show warning "Limited data available"
* API fetch failure: Show cached data with "Last updated: [date]" warning
* Large dataset loading: Show loading spinner, implement pagination if needed

### 🔄 Update Frequency Decision

* **Recommended**: Weekly updates (Sunday)
  * Sackmann data updates irregularly
  * Weekly reduces API/workflow costs
  * Fresh enough for analytics use case
* **Alternative**: Daily if adding live API integration
* **Display**: Show "Data last updated: [timestamp]" prominently on dashboard

### 🎯 GitHub Pages Configuration

* **Branch**: `main` (or `gh-pages` if preferred)
* **Folder**: `/dashboard` (or root if you prefer)
* **Custom Domain**: Optional, can add later
* **HTTPS**: Automatically enabled by GitHub Pages

---

## 8️⃣ README Talking Points (For Portfolio 🔥)

* Data sources & update cadence
* Feature engineering rationale
* Win probability methodology
* Limitations & future improvements
* Screenshots of dashboard

---

## Final Thought

This project:

* Shows **data engineering**
* Shows **ML thinking**
* Shows **product sense**
* Runs **cheap + scalable**

If you want next, I can:

* Sketch the **JSON schema**
* Write the **Elo formula**
* Create a **basic HTML wireframe**
* Or draft the **GitHub Actions YAML**

Just tell me what you want to tackle next 🎾🚀
