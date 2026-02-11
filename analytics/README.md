# Analytics Package

This package provides comprehensive tennis analytics capabilities including Elo rating calculations, feature engineering, and win probability predictions.

## 📁 Package Structure

```
analytics/
├── __init__.py              # Package exports and version
├── config.py                # Configuration constants and weights
├── elo.py                   # Elo rating system implementation
├── feature_engineering.py   # Player statistics and metrics calculation
├── win_probability.py       # Match win probability calculations
├── score_parser.py         # Tennis score string parsing utilities
├── metrics_comparator.py    # Player metrics comparison logic
└── utils.py                 # General utility functions
```

## 🎯 Core Modules

### `config.py` - Configuration
Central configuration file containing:
- **Elo Settings**: Starting ratings, K-factors, decay constants
- **Feature Engineering**: Minimum match thresholds, recent form windows
- **Metric Weights**: Weights for each metric in win probability calculation
- **Hybrid Weights**: Elo vs Metrics weighting (65% Elo, 35% Metrics)
- **Fallback Settings**: Minimum metrics required for predictions

**Key Constants:**
- `METRIC_WEIGHTS`: Dictionary mapping metric names to their weights (sums to ~1.0)
- `ELO_WEIGHT` / `METRICS_WEIGHT`: Hybrid probability weighting
- `MIN_METRICS_REQUIRED`: Minimum non-zero metrics needed (default: 3)

### `elo.py` - Elo Rating System
Implements the Elo rating algorithm for tennis players.

**Main Class: `EloRating`**

**Key Methods:**
- `get_rating(player_id, surface=None)`: Get current Elo rating
- `get_surface_adjusted_rating(player_id, surface)`: Get surface-specific rating
- `expected_score(player_a_elo, player_b_elo)`: Calculate expected win probability
- `update_rating(winner_id, loser_id, surface, tournament_level, match_date)`: Update ratings after match
- `calculate_ratings_from_matches(matches_df)`: Process historical matches chronologically

**Features:**
- Surface-specific ratings (Hard, Clay, Grass, Carpet)
- Tournament-level K-factors (Grand Slam: 48, Regular: 32, Small: 24)
- Time decay for older matches (365-day half-life)
- Automatic initialization for new players (default: 1500)

### `feature_engineering.py` - Feature Engineering
Computes comprehensive statistics and metrics for players.

**Main Class: `FeatureEngineer`**

**Key Methods:**

**Basic Statistics:**
- `get_career_stats(player_id)`: Career wins, losses, win percentage
- `get_recent_form(player_id, n_matches=10)`: Recent match performance
- `get_surface_stats(player_id)`: Surface-specific win percentages
- `get_head_to_head(player_a_id, player_b_id)`: H2H record and last 5 meetings
- `get_tournament_performance(player_id)`: Performance by tournament level

**Detailed Metrics:**
- `get_detailed_player_metrics(player_id)`: Returns 11 comprehensive metrics:
  - `avg_winning_margin`: Average game difference when winning
  - `avg_minutes_for_wins`: Average match duration for wins
  - `first_set_win_pct`: Percentage of matches where player won first set
  - `second_set_win_pct`: Percentage of matches where player won second set
  - `ace_pct`: Ace percentage (total aces / total service points)
  - `most_lost_surface`: Surface where player loses most often
  - `avg_losing_game_time`: Average match duration for losses
  - `avg_opponent_age_when_lost`: Average opponent age when player lost
  - `avg_opponent_age_when_won`: Average opponent age when player won
  - `form_last_10_wins`: Average winning margin from last 10 wins
  - `form_last_5_wins`: Average winning margin from last 5 wins

**Comparison:**
- `compare_detailed_metrics(player_a_id, player_b_id, surface)`: Compare all metrics between two players

**Helper Methods:**
- `_get_player_matches(player_id)`: Get all matches for a player
- `_calculate_wins_losses(matches, player_id)`: Calculate wins and losses
- `_calculate_avg_winning_margin(wins)`: Calculate average winning margin
- `_calculate_set_win_pct(player_matches, player_id, set_number)`: Calculate set win percentage
- `_calculate_form_metric(wins, n_wins)`: Calculate form from recent wins

### `win_probability.py` - Win Probability Calculator
Calculates match win probabilities using multiple approaches.

**Main Class: `WinProbabilityCalculator`**

**Key Methods:**
- `calculate_elo_based_probability(player_a_id, player_b_id, surface)`: Elo-only probability
- `calculate_metric_based_probability(player_a_id, player_b_id, surface)`: Metrics-only probability
- `calculate_hybrid_probability(player_a_id, player_b_id, surface, h2h_record)`: **Recommended** - Combines Elo + Metrics
- `calculate_with_features(player_a_id, player_b_id, surface, h2h_record, recent_form)`: Legacy method with H2H adjustments

**Hybrid Approach:**
- Combines Elo (65% weight) + Metrics (35% weight)
- Automatically falls back to Elo-only if insufficient metrics (< 3 non-zero metrics)
- Includes H2H adjustments (±3% max)
- Returns detailed breakdown including:
  - Final hybrid probability
  - Elo-only probability
  - Metric-only probability (if available)
  - Metric comparison details
  - Key advantages
  - Confidence level

### `score_parser.py` - Score Parsing
Parses tennis match score strings into structured data.

**Main Class: `ScoreParser`**

**Key Methods:**
- `ScoreParser.parse(score_str)`: Parse score string (e.g., "6-4 6-2", "7-6(3) 6-3")

**Supported Formats:**
- Two sets: `"6-4 6-2"`
- Three sets: `"6-3 4-6 6-2"`
- Tiebreaks: `"7-6(3) 6-3"`, `"6-7(4) 6-1"`
- Mixed: `"7-5 6-7(4) 6-1"`

**Returns:**
- Parsed sets with game counts
- Set winners
- Total games won/lost
- Winning margin in games

**Backward Compatibility:**
- `parse_tennis_score()`: Function wrapper for backward compatibility

### `metrics_comparator.py` - Metrics Comparison
Handles comparison of player metrics for win probability calculation.

**Main Class: `MetricsComparator`**

**Key Methods:**
- `compare_all_metrics(metrics_a, metrics_b, surface)`: Compare all 11 metrics between two players
- `compare_higher_is_better(value_a, value_b, metric_name, weight)`: Compare metrics where higher is better
- `compare_lower_is_better(value_a, value_b, metric_name, weight)`: Compare metrics where lower is better
- `safe_value(val)`: Convert None to 0.0 for missing metrics

**Comparison Logic:**
- Each metric is compared and scored based on configured weights
- Scores are summed and converted to probability using sigmoid transformation
- Returns comparison details, scores, probabilities, and key advantages

### `utils.py` - Utility Functions
General-purpose utility functions.

**Key Functions:**
- `normalize_player_name(name)`: Normalize player names (whitespace, case)
- `create_player_id(name)`: Create stable player ID from name (e.g., "djokovic-n")
- `calculate_win_percentage(wins, losses, min_matches=5)`: Calculate win % with threshold
- `get_recent_matches(df, player_id, days=30)`: Get matches within date range
- `handle_missing_data(value, default)`: Handle None/NaN values consistently
- `convert_to_native_type(val)`: Convert numpy/pandas types to native Python types

## 🔄 Data Flow

```
Match Data (CSV)
    ↓
FeatureEngineer.get_detailed_player_metrics()
    ↓
11 Detailed Metrics (per player)
    ↓
MetricsComparator.compare_all_metrics()
    ↓
Metric-based Probability
    ↓
WinProbabilityCalculator.calculate_hybrid_probability()
    ↓
Final Win Probability (Elo + Metrics)
```

## 📊 Usage Example

```python
from analytics import FeatureEngineer, EloRating, WinProbabilityCalculator
import pandas as pd

# Load match data
matches_df = pd.read_csv('matches.csv')
matches_df['tourney_date'] = pd.to_datetime(matches_df['tourney_date'])

# Initialize systems
elo_system = EloRating()
elo_system.calculate_ratings_from_matches(matches_df)

feature_engineer = FeatureEngineer(matches_df)

# Get player metrics
metrics = feature_engineer.get_detailed_player_metrics('player_id')
print(f"Average winning margin: {metrics['avg_winning_margin']}")
print(f"Form (last 10 wins): {metrics['form_last_10_wins']}")

# Calculate win probability
win_prob_calc = WinProbabilityCalculator(elo_system, feature_engineer)
result = win_prob_calc.calculate_hybrid_probability(
    'player_a_id',
    'player_b_id',
    surface='Hard',
    h2h_record=None
)

print(f"Player A win probability: {result['player_a_win_prob']}")
print(f"Method: {result['method']}")
print(f"Key advantages: {result.get('key_advantages', [])}")
```

## 🎛️ Configuration

All weights and thresholds are configurable in `config.py`:

```python
# Adjust metric weights
METRIC_WEIGHTS = {
    'first_set_win_pct': 0.20,  # Increase weight for first set
    'form_last_10_wins': 0.12,   # Adjust form importance
    # ... etc
}

# Adjust hybrid weighting
ELO_WEIGHT = 0.65      # Elo contribution
METRICS_WEIGHT = 0.35  # Metrics contribution

# Adjust fallback threshold
MIN_METRICS_REQUIRED = 3  # Minimum metrics needed
```

## 🔍 Key Features

### 1. **Comprehensive Metrics**
- 11 detailed metrics per player
- Career, recent form, and surface-specific stats
- Form indicators from recent wins

### 2. **Hybrid Prediction**
- Combines proven Elo system with detailed metrics
- Automatic fallback to Elo-only when data is insufficient
- Configurable weights for fine-tuning

### 3. **Robust Score Parsing**
- Handles various score formats
- Supports tiebreaks and multiple sets
- Graceful error handling for invalid scores

### 4. **Surface Awareness**
- Surface-specific Elo ratings
- Surface-specific win percentages
- Surface advantage/disadvantage in comparisons

### 5. **Missing Data Handling**
- Missing metrics default to 0 (as configured)
- Fallback mechanisms when data is insufficient
- Graceful degradation

## 📈 Metric Weights Summary

Current weights (sum to 1.0):
- **First Set Win %**: 15% (strong predictor)
- **Form (Last 10 Wins)**: 12% (recent form)
- **Avg Winning Margin**: 12% (dominance)
- **Second Set Win %**: 12%
- **Form (Last 5 Wins)**: 9% (hot form)
- **Ace %**: 8% (serve strength)
- **Opponent Age Metrics**: 8% each (context)
- **Surface Match**: 8% (surface advantage)
- **Efficiency Metrics**: 4% each (minutes)

## 🚀 Performance Considerations

- **Caching**: Consider caching player metrics for frequently accessed players
- **Batch Processing**: `calculate_ratings_from_matches()` processes matches chronologically
- **Memory**: Large DataFrames are copied - consider views for memory-constrained environments
- **Score Parsing**: Regex-based parsing is efficient for typical score formats

## 🔧 Extending the Package

### Adding New Metrics

1. Add calculation in `FeatureEngineer.get_detailed_player_metrics()`
2. Add weight in `config.py` METRIC_WEIGHTS
3. Add comparison logic in `MetricsComparator.compare_all_metrics()`
4. Update this README

### Adding New Prediction Methods

1. Add method to `WinProbabilityCalculator`
2. Integrate with existing Elo/Metrics systems
3. Update `calculate_hybrid_probability()` if needed

## 📝 Notes

- All probabilities are clamped between 5% and 95% to avoid extreme predictions
- Missing metrics are treated as 0.0 in comparisons (as configured)
- Surface adjustments are additive to base Elo ratings
- Time decay uses exponential decay with 365-day half-life
- Tournament levels: G (Grand Slam), M (Masters), 500, 250, A (ATP Cup/Other)

## 🐛 Troubleshooting

**Issue**: "Insufficient metrics available" fallback
- **Solution**: Check that players have enough matches with score data
- Minimum 3 non-zero metrics required (configurable)

**Issue**: Score parsing returns None
- **Solution**: Verify score format matches supported patterns
- Check for missing/NaN scores in data

**Issue**: Elo ratings seem incorrect
- **Solution**: Ensure matches are processed chronologically
- Check that match dates are properly formatted

## 📚 Related Documentation

- See main project README for overall architecture
- See `config.py` for all configuration options
- See individual module docstrings for detailed API documentation
