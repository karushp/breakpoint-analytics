# 🎾 Breakpoint Analytics (Sackmann)

**This directory is the Sackmann-based codebase.** All existing files except notebooks live here. The repo root is used for TennisMyLife.

A data-driven tennis analytics dashboard that compares players and predicts match outcomes using Elo ratings, head-to-head statistics, and surface-specific performance metrics.

## 🏗️ Architecture

```
Jeff Sackmann CSVs / Live API
            ↓
      Python ETL + Analytics
            ↓
   Precomputed JSON / CSV
            ↓
 Static Dashboard (GitHub Pages)
```

- **Python**: Handles data ingestion, feature engineering, and Elo rating calculations
- **GitHub Pages**: Hosts a static frontend that displays precomputed analytics
- **GitHub Actions**: Automatically updates data weekly

## ✨ Features

- **Player Comparison**: Compare any two ATP players
- **Win Probability**: Elo-based match prediction with confidence levels
- **Head-to-Head**: Historical matchup statistics
- **Surface Analysis**: Performance breakdown by surface (Hard, Clay, Grass)
- **Recent Form**: Last 10 matches win percentage
- **Elo Rankings**: Current Elo ratings and rankings

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer

### Installing uv

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew (macOS)
brew install uv

# Or with pip
pip install uv
```

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd breakpoint-analytics

# Install dependencies with uv
make install
# or
uv sync
```

### Running the Pipeline

```bash
# Run full pipeline (ingest -> build -> export)
make all

# Or run steps individually:
make ingest    # Download data from Sackmann repo
make build     # Build features and calculate Elo ratings
make export    # Export JSON files for dashboard
```

**Note**: All Python scripts run via `uv run python` which automatically uses the project's virtual environment.

### Viewing the Dashboard

```bash
# Start local web server
make run-dashboard

# Open http://localhost:8000/dashboard/ in your browser
```

## 📁 Project Structure

```
breakpoint-analytics/
├── data/
│   ├── raw/              # Raw CSV files (gitignored)
│   └── processed/        # Processed data files
├── analytics/
│   ├── elo.py            # Elo rating system
│   ├── feature_engineering.py
│   ├── win_probability.py
│   ├── utils.py
│   └── config.py
├── pipelines/
│   ├── ingest_sackmann.py
│   ├── build_features.py
│   └── export_dashboard_data.py
├── dashboard/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── outputs/              # JSON files for frontend
├── .github/workflows/
│   └── update-data.yml   # Automated data updates
├── pyproject.toml      # Project dependencies (uv)
├── requirements.txt     # Legacy (for compatibility)
├── Makefile
└── README.md
```

## 📊 Data Sources

- **Primary**: [Jeff Sackmann's Tennis Data](https://github.com/JeffSackmann/tennis_atp)
  - Historical ATP match data
  - Updated regularly
  - Free and open source

- **Future**: Live API integration for recent matches (Phase 3)

## 🧮 Methodology

### Elo Rating System

- **Starting Rating**: 1500
- **K-Factor**: 
  - 48 for Grand Slams
  - 32 for regular tournaments
  - 24 for smaller tournaments
- **Surface Adjustment**: Separate Elo ratings per surface with transfer learning
- **Time Decay**: Exponential decay for older matches (365-day half-life)

### Win Probability

Calculated using Elo-based expected score formula:
```
P(Player A wins) = 1 / (1 + 10^((Elo_B - Elo_A) / 400))
```

### Feature Engineering

- Career win percentage (minimum 5 matches)
- Recent form (last 10 matches)
- Surface-specific statistics (minimum 3 matches per surface)
- Head-to-head records
- Tournament-level performance

## 🔄 Automated Updates

GitHub Actions workflow runs weekly (Sunday 2 AM UTC) to:
1. Download latest data from Sackmann repo
2. Recalculate Elo ratings and features
3. Export updated JSON files
4. Commit and push changes
5. GitHub Pages automatically refreshes

## 🛠️ Development

### Running Tests

```bash
# Add tests as needed
pytest tests/
```

### Adding New Features

1. Update analytics modules (`analytics/`)
2. Modify export pipeline (`pipelines/export_dashboard_data.py`)
3. Update frontend (`dashboard/`)
4. Test locally with `make run-dashboard`

## 📝 Limitations & Future Improvements

### Current Limitations

- Historical data only (no live match updates in MVP)
- Simplified matchup stats (no detailed H2H in MVP)
- Basic Elo implementation (no advanced ML models)
- ATP only (no WTA data)

### Planned Enhancements

- [ ] Logistic regression model for win probability
- [ ] Live API integration for recent matches
- [ ] Detailed match history and score breakdowns
- [ ] Elo trend charts over time
- [ ] Tournament-specific predictions
- [ ] WTA data support
- [ ] Player search and autocomplete
- [ ] Mobile-responsive improvements

## 📄 License

This project uses data from [Jeff Sackmann's Tennis Data](https://github.com/JeffSackmann/tennis_atp), which is licensed under CC BY-NC-SA 4.0.

## 🙏 Acknowledgments

- [Jeff Sackmann](https://github.com/JeffSackmann) for providing excellent tennis data
- ATP for match data

## 📧 Contact

For questions or contributions, please open an issue on GitHub.

---

Built with ❤️ for tennis analytics enthusiasts
