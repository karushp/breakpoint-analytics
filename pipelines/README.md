# Pipelines

This directory contains the data processing pipelines for Breakpoint Analytics. These pipelines transform raw tennis match data into actionable analytics and insights.

## Overview

The pipelines follow a sequential workflow:

```
Raw Data → Ingestion → Feature Building → Export → Dashboard
                                    ↓
                              Validation (optional)
```

Each pipeline performs a specific transformation step in the analytics pipeline.

---

## Pipeline Descriptions

### 1. `ingest_sackmann.py`

**Purpose**: Downloads and normalizes tennis match data from Jeff Sackmann's tennis_atp repository.

**What it does**:
- Downloads ATP match CSV files for specified years from GitHub
- Normalizes player names and creates consistent player IDs
- Standardizes date formats and surface types
- Removes invalid or incomplete records
- Saves combined normalized data to `data/raw/matches_combined.csv`

**Key Functions**:
- `download_sackmann_csv(year)`: Downloads CSV for a specific year
- `load_sackmann_data(years)`: Loads multiple years of data
- `normalize_match_data(df)`: Normalizes and cleans the data
- `main()`: Orchestrates the ingestion process (defaults to last 5 years)

**Output**:
- `data/raw/matches_combined.csv`: Normalized match data ready for processing

**Usage**:
```bash
uv run python pipelines/ingest_sackmann.py
```

**Configuration**:
- Years to download: Configurable in `main()` function (default: last 5 years)
- Data source: `analytics.config.SACKMANN_CSV_BASE_URL`

---

### 2. `build_features.py`

**Purpose**: Calculates Elo ratings and comprehensive player statistics from match data.

**What it does**:
- Loads normalized match data from ingestion pipeline
- Calculates Elo ratings for all players (with surface adjustments and time decay)
- Computes detailed player metrics:
  - Career statistics (win percentage, total matches)
  - Recent form (last 10 matches)
  - Surface-specific statistics (Hard, Clay, Grass)
  - **11 detailed performance metrics**:
    - Average winning margin
    - Average minutes for wins
    - First/second set win percentages
    - Ace percentage
    - Most lost surface
    - Average losing game time
    - Average opponent age (wins/losses)
    - Form metrics (last 10 wins, last 5 wins)
- Saves player summaries to CSV

**Key Functions**:
- `build_all_features(matches_df)`: Main orchestration function
- `_build_player_summary()`: Creates summary for a single player
- `_create_player_name_lookup()`: Efficient player name lookup

**Output**:
- `data/processed/players.csv`: Complete player statistics and metrics

**Usage**:
```bash
uv run python pipelines/build_features.py
```

**Dependencies**:
- Requires `data/raw/matches_combined.csv` from ingestion pipeline
- Uses `analytics.elo.EloRating` for Elo calculations
- Uses `analytics.feature_engineering.FeatureEngineer` for statistics

**Configuration**:
- Elo parameters: `analytics.config.ELO_*`
- Minimum matches: `analytics.config.MIN_MATCHES_FOR_STATS`
- Surface adjustments: `analytics.config.SURFACE_ADJUSTMENTS`

---

### 3. `export_dashboard_data.py`

**Purpose**: Exports processed analytics data to JSON format for frontend dashboard consumption.

**What it does**:
- Loads match data and builds all features (reuses `build_features.py` logic)
- Filters to active players (minimum match threshold)
- Exports player summaries with rankings
- Exports Elo rankings (top N players)
- Provides on-demand matchup statistics function

**Key Functions**:
- `export_player_summary(features)`: Exports active players with rankings
- `export_elo_rankings(features, top_n=100)`: Exports top Elo rankings
- `export_matchup_stats(player_a_id, player_b_id, features, surface)`: 
  - Calculates hybrid win probability (Elo + Metrics)
  - Compares detailed metrics between players
  - Returns head-to-head, form, and surface statistics
- `_filter_active_players()`: Filters by minimum matches
- `_add_rankings()`: Adds ranking numbers to sorted lists
- `_build_surface_comparison()`: Compares surface statistics
- `main()`: Orchestrates the full export process

**Output**:
- `outputs/player_summary.json`: Player data for dashboard
- `outputs/elo_rankings.json`: Top player rankings
- `outputs/matchup_stats.json`: Generated on-demand (not in main export)

**Usage**:
```bash
uv run python pipelines/export_dashboard_data.py
```

**Dependencies**:
- Requires `data/raw/matches_combined.csv` (or will rebuild from ingestion)
- Uses `pipelines.build_features.build_all_features()` internally
- Uses `analytics.win_probability.WinProbabilityCalculator` for predictions

**Configuration**:
- Minimum matches for export: `analytics.config.MIN_MATCHES_FOR_EXPORT` (default: 10)
- Top N rankings: Configurable in `export_elo_rankings()` (default: 100)
- Metric weights: `analytics.config.METRIC_WEIGHTS`
- Hybrid model weights: `analytics.config.ELO_WEIGHT`, `METRICS_WEIGHT`

---

### 4. `validate_models.py`

**Purpose**: Validates tennis match prediction models using time-based splitting and walk-forward validation.

**What it does**:
- Loads normalized match data from ingestion pipeline
- Splits data chronologically into train/test sets (80/20 default)
- Evaluates Elo-only model performance
- Evaluates Hybrid model (Elo + Metrics) performance
- Compares both models using multiple metrics
- Saves validation results to JSON

**Key Functions**:
- `load_match_data(data_path)`: Loads match data from CSV
- `save_results(results, output_path)`: Saves validation results to JSON
- `main()`: Orchestrates the validation process

**Evaluation Metrics**:
- **Accuracy**: Percentage of correct predictions
- **Brier Score**: Probability calibration (lower is better)
- **Log Loss**: Probability quality (lower is better)
- **ROC AUC**: Discrimination ability (higher is better)
- **Calibration Error**: How well probabilities match outcomes (lower is better)

**Validation Approach**:
- **Time-based splitting**: Training data always comes before test data (no data leakage)
- **Walk-forward validation**: Elo ratings update incrementally during evaluation
- **Chronological processing**: Matches processed in date order
- **Realistic simulation**: Mimics real-world prediction scenarios

**Output**:
- `outputs/validation_results.json`: Complete validation results with metrics and comparison
  - Structure: `{elo_only: {...}, hybrid: {...}, improvement: {...}, metadata: {...}}`
  - Includes calibration curves, probability statistics, and model comparison

**Usage**:
```bash
uv run python pipelines/validate_models.py
```

**Dependencies**:
- Requires `data/raw/matches_combined.csv` from ingestion pipeline
- Uses `analytics.validation.MatchPredictorValidator` for validation
- Uses `analytics.elo.EloRating` and `analytics.feature_engineering.FeatureEngineer`
- Requires `scikit-learn` for evaluation metrics

**Configuration**:
- Train/test split: `analytics.config.VALIDATION_TRAIN_SPLIT` (default: 0.8)
- Minimum training matches: `analytics.config.VALIDATION_MIN_TRAIN_MATCHES` (default: 100)
- Minimum test matches: `analytics.config.VALIDATION_MIN_TEST_MATCHES` (default: 50)
- Can customize date ranges in `validate_models.py` if needed

**Example Output**:
```
============================================================
Model Comparison
============================================================

Metric               Elo-Only        Hybrid          Improvement
-----------------------------------------------------------------
Accuracy             58.42%          59.42%                 +1.71%
Brier Score          0.2403          0.2333                  +2.91%
Log Loss             0.7207          0.7586                  -5.26%
```

**When to Run**:
- After building features to evaluate model performance
- When tuning model weights or parameters
- Periodically to monitor model performance over time
- Before deploying model changes to production

See `VALIDATION_GUIDE.md` in project root for detailed validation documentation.

---

## Execution Order

To run the complete pipeline from scratch:

```bash
# Step 1: Download and normalize raw data
uv run python pipelines/ingest_sackmann.py

# Step 2: Calculate features and statistics
uv run python pipelines/build_features.py

# Step 3: Export data for dashboard
uv run python pipelines/export_dashboard_data.py

# Step 4: Validate models (optional but recommended)
uv run python pipelines/validate_models.py
```

**Notes**:
- `export_dashboard_data.py` will automatically rebuild features if needed, so you can skip step 2 if you only need dashboard exports
- Validation can be run anytime after ingestion to evaluate model performance
- Run validation after tuning model weights/parameters to measure improvements

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. ingest_sackmann.py                                       │
│    Downloads → Normalizes → Saves                           │
│    Output: data/raw/matches_combined.csv                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. build_features.py                                        │
│    Loads matches → Calculates Elo → Computes metrics        │
│    Output: data/processed/players.csv                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. export_dashboard_data.py                                 │
│    Loads features → Filters → Exports JSON                  │
│    Output: outputs/player_summary.json                      │
│            outputs/elo_rankings.json                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. validate_models.py (optional)                           │
│    Time-based split → Walk-forward validation → Compare     │
│    Output: outputs/validation_results.json                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Output Files

### From `ingest_sackmann.py`:
- **`data/raw/matches_combined.csv`**: Normalized match data
  - Columns: `winner_id`, `loser_id`, `tourney_date`, `surface`, `score`, etc.
  - Used by: `build_features.py`, `export_dashboard_data.py`

### From `build_features.py`:
- **`data/processed/players.csv`**: Player statistics and metrics
  - Columns: `id`, `name`, `current_elo`, `career_win_pct`, `matches_played`, `detailed_metrics`, etc.
  - Used by: Analysis, reporting, dashboard (via export)

### From `export_dashboard_data.py`:
- **`outputs/player_summary.json`**: Active players with rankings
  - Structure: `{players: [...], last_updated: "..."}`
  - Used by: Dashboard frontend
  
- **`outputs/elo_rankings.json`**: Top player rankings
  - Structure: `{rankings: [...], last_updated: "..."}`
  - Used by: Dashboard frontend

- **`outputs/matchup_stats.json`**: Generated on-demand
  - Structure: Win probabilities, metric comparisons, H2H, form, surface stats
  - Used by: Dashboard frontend (player comparison)

### From `validate_models.py`:
- **`outputs/validation_results.json`**: Model validation and comparison results
  - Structure: `{elo_only: {...}, hybrid: {...}, improvement: {...}, metadata: {...}}`
  - Includes: Accuracy, Brier Score, Log Loss, ROC AUC, Calibration Error
  - Includes: Calibration curves, probability statistics, model comparison
  - Used by: Model evaluation, performance monitoring, parameter tuning

---

## Key Features

### Elo Rating System
- Surface-adjusted ratings (Hard, Clay, Grass)
- Time decay for older matches
- Tournament-level K-factors (Grand Slam, Masters, ATP 250/500)

### Detailed Player Metrics
1. **Average Winning Margin**: Dominance indicator
2. **First/Second Set Win %**: Set performance
3. **Ace Percentage**: Serve strength
4. **Average Minutes (Wins)**: Match efficiency
5. **Average Losing Game Time**: Resilience indicator
6. **Average Opponent Age**: Competition level
7. **Most Lost Surface**: Weakness indicator
8. **Form Metrics**: Recent performance (last 10/5 wins)

### Win Probability Calculation
- **Hybrid Model**: Combines Elo ratings with detailed metrics
- **Configurable Weights**: Adjustable metric importance
- **Fallback Logic**: Uses Elo-only if insufficient metrics available
- **Head-to-Head Adjustments**: Incorporates historical matchups

---

## Error Handling

All pipelines include comprehensive error handling:
- **File Not Found**: Clear error messages with guidance
- **Data Validation**: Checks for required columns
- **Missing Data**: Graceful handling of incomplete records
- **Network Errors**: Retry logic for data downloads

---

## Performance Considerations

- **`build_features.py`**: Processes all players sequentially
  - Progress indicators for large datasets (>100 players)
  - Efficient player name lookup (O(1) instead of O(N))
  
- **`export_dashboard_data.py`**: Filters before processing
  - Only processes active players (min matches threshold)
  - Efficient sorting and ranking

---

## Configuration

All configuration is centralized in `analytics/config.py`:
- Elo parameters
- Surface adjustments
- Metric weights
- Minimum match thresholds
- Data directories

---

## Dependencies

- **pandas**: Data manipulation
- **requests**: HTTP downloads (ingestion)
- **analytics package**: Core analytics modules
  - `elo.py`: Elo rating system
  - `feature_engineering.py`: Player statistics
  - `win_probability.py`: Win prediction
  - `metrics_comparator.py`: Metric comparison
  - `score_parser.py`: Score parsing
  - `validation.py`: Model validation and evaluation
  - `utils.py`: Utility functions
- **scikit-learn**: Evaluation metrics (for validation pipeline)

---

## Troubleshooting

### "Match data file not found"
- Run `ingest_sackmann.py` first to download and normalize data

### "Missing required columns"
- Ensure data was properly normalized in ingestion step
- Check that CSV files are not corrupted

### "No players exported"
- Check `MIN_MATCHES_FOR_EXPORT` threshold in config
- Verify match data contains sufficient records

### Export files not updating
- Ensure you're running the export pipeline after feature building
- Check file permissions in `outputs/` directory

### "Insufficient training data" (validation)
- Use more years of data or reduce `VALIDATION_MIN_TRAIN_MATCHES` threshold
- Check that date ranges are valid and contain sufficient matches

### "Insufficient test data" (validation)
- Adjust date ranges or reduce `VALIDATION_MIN_TEST_MATCHES` threshold
- Ensure test period comes after training period chronologically

### Validation shows 100% accuracy
- This indicates a bug - predictions should be based on probability > 0.5
- Check that validation logic is correctly implemented

---

## Future Enhancements

Potential improvements:
- Parallel processing for large datasets
- Incremental updates (only process new matches)
- Caching of intermediate results
- API endpoint for on-demand matchup stats
- Historical Elo trend tracking
- Tournament-specific analytics
- Walk-forward cross-validation (multiple time windows)
- Automated hyperparameter tuning based on validation results
- Real-time model performance monitoring
- A/B testing framework for model variants
