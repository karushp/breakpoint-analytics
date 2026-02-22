# Model Validation Guide

This guide explains the validation approach for tennis match prediction models in Breakpoint Analytics.

## Overview

We use **time-based train/test splitting** with **walk-forward validation** to ensure realistic evaluation of our prediction models. This approach simulates real-world usage where:
1. Models are trained on historical data
2. Predictions are made on future matches
3. Models are updated incrementally as new matches occur

## Why Time-Based Splitting?

Tennis match prediction is a **time-series problem**:
- Player performance changes over time
- Elo ratings evolve based on match results
- Using future data to predict past matches would be **data leakage**
- Standard random splitting would give unrealistic performance estimates

## Validation Approach

### 1. Time-Based Split

```
Training Set (80%)          Test Set (20%)
[==========]                [====]
2000-01-01  to  2020-12-31  2021-01-01  to  2024-12-31
```

- **Training**: Historical matches used to build Elo ratings and calculate metrics
- **Test**: Future matches used to evaluate predictions
- **No overlap**: Test set always comes after training set chronologically

### 2. Walk-Forward Validation

For each match in the test set:
1. **Before match**: Make prediction using current Elo/metrics
2. **Record prediction**: Store predicted probability and outcome
3. **After match**: Update Elo ratings (simulating real-world usage)
4. **Move to next match**: Repeat with updated ratings

This ensures that:
- Predictions use only information available at match time
- Elo ratings evolve naturally over the test period
- Evaluation reflects real-world model performance

## Evaluation Metrics

We use multiple metrics to comprehensively assess model performance:

### 1. **Accuracy**
- Percentage of correct predictions (winner predicted correctly)
- Simple but can be misleading if probabilities are well-calibrated

### 2. **Brier Score**
- Measures probability calibration: `BS = mean((predicted_prob - actual_outcome)²)`
- **Lower is better** (perfect = 0.0, worst = 1.0)
- Penalizes confident wrong predictions more than uncertain ones

### 3. **Log Loss (Cross-Entropy)**
- Measures probability quality: `LL = -mean(y*log(p) + (1-y)*log(1-p))`
- **Lower is better** (perfect = 0.0)
- Heavily penalizes confident wrong predictions

### 4. **ROC AUC**
- Area under the Receiver Operating Characteristic curve
- Measures ability to distinguish winners from losers
- **Higher is better** (perfect = 1.0, random = 0.5)

### 5. **Calibration Error**
- Measures how well predicted probabilities match actual outcomes
- **Lower is better** (perfect = 0.0)
- A well-calibrated model: if it predicts 70% win probability, ~70% should actually win

## Models Evaluated

### 1. Elo-Only Model
- Uses only Elo ratings (with surface adjustments)
- Baseline model for comparison
- Fast and interpretable

### 2. Hybrid Model
- Combines Elo ratings with detailed player metrics
- Uses configurable weights (`ELO_WEIGHT` vs `METRICS_WEIGHT`)
- More complex but potentially more accurate

## Usage

### Running Validation

```bash
# Ensure you have match data
uv run python pipelines/ingest_sackmann.py

# Run validation
uv run python pipelines/validate_models.py
```

### Customizing Validation

You can customize the validation in `pipelines/validate_models.py`:

```python
validator = MatchPredictorValidator(
    matches_df=matches_df,
    train_start_date=datetime(2000, 1, 1),  # Custom start
    train_end_date=datetime(2020, 12, 31),   # Custom end
    test_start_date=datetime(2021, 1, 1),    # Custom test start
    test_end_date=datetime(2024, 12, 31),    # Custom test end
    min_train_matches=200,                   # Minimum training matches
    min_test_matches=100                     # Minimum test matches
)
```

### Programmatic Usage

```python
from analytics.validation import MatchPredictorValidator
from analytics.validation import print_evaluation_results, print_comparison

# Load your data
matches_df = pd.read_csv('data/raw/matches_combined.csv')

# Create validator
validator = MatchPredictorValidator(matches_df)

# Evaluate individual models
elo_results = validator.evaluate_elo_only()
hybrid_results = validator.evaluate_hybrid_model()

# Compare models
comparison = validator.compare_models()
print_comparison(comparison)
```

## Output

The validation pipeline outputs:

1. **Console Output**: 
   - Data split information
   - Evaluation results for each model
   - Model comparison table

2. **JSON File** (`outputs/validation_results.json`):
   - Complete results with all metrics
   - Calibration curves
   - Metadata (dates, match counts)

### Example Output

```
============================================================
Model Comparison
============================================================

Metric               Elo-Only        Hybrid           Improvement
-----------------------------------------------------------------
Accuracy             0.65            0.68             +4.62%
Brier Score          0.2150          0.1980          +7.91%
Log Loss             0.6234          0.5891          +5.50%
ROC AUC              0.7123          0.7456          +4.68%
```

## Interpreting Results

### Good Performance Indicators

- **Accuracy > 65%**: Better than random (50%)
- **Brier Score < 0.20**: Well-calibrated probabilities
- **Log Loss < 0.60**: Good probability estimates
- **ROC AUC > 0.70**: Good discrimination ability

### Model Comparison

- **Positive improvement %**: Hybrid model performs better
- **Negative improvement %**: Elo-only model performs better
- **Small differences (< 2%)**: Models are similar, choose simpler one

### Calibration

A well-calibrated model should have:
- Low calibration error (< 0.05)
- Calibration curve close to diagonal (y = x)
- Predicted probabilities match actual win rates

## Best Practices

### 1. Use Sufficient Data
- **Minimum 100 training matches**: For stable Elo ratings
- **Minimum 50 test matches**: For reliable evaluation
- **More is better**: Larger test sets give more confidence

### 2. Avoid Data Leakage
- Never use future data to predict past matches
- Always sort matches by date before processing
- Update models incrementally in chronological order

### 3. Multiple Evaluation Metrics
- Don't rely on accuracy alone
- Check calibration (Brier Score, Log Loss)
- Consider discrimination (ROC AUC)

### 4. Regular Re-validation
- Re-run validation as new data arrives
- Monitor performance over time
- Adjust model weights if performance degrades

## Advanced: Walk-Forward Cross-Validation

For more robust evaluation, you can implement walk-forward cross-validation:

```python
# Split into multiple time windows
for test_window in time_windows:
    train_data = matches_before(test_window)
    test_data = matches_in(test_window)
    
    # Train and evaluate
    validator = MatchPredictorValidator(train_data, test_data)
    results = validator.compare_models()
    
    # Aggregate results across windows
```

This provides:
- Multiple evaluation periods
- More robust performance estimates
- Better understanding of model stability

## Troubleshooting

### "Insufficient training data"
- **Solution**: Use more years of data or reduce `min_train_matches`

### "Insufficient test data"
- **Solution**: Adjust date ranges or reduce `min_test_matches`

### "All predictions are 50%"
- **Solution**: Check if Elo ratings are being calculated correctly
- Verify that players have sufficient match history

### "Calibration error is high"
- **Solution**: Adjust probability calculation weights
- Consider recalibrating probabilities using Platt scaling

## Configuration

Validation parameters can be adjusted in `analytics/config.py`:

```python
VALIDATION_TRAIN_SPLIT = 0.8  # 80% training, 20% testing
VALIDATION_MIN_TRAIN_MATCHES = 100
VALIDATION_MIN_TEST_MATCHES = 50
```

## Next Steps

1. **Run initial validation**: Establish baseline performance
2. **Compare models**: Determine if hybrid model improves predictions
3. **Tune weights**: Adjust `ELO_WEIGHT` and `METRICS_WEIGHT` based on results
4. **Iterate**: Refine metrics and weights to improve performance
5. **Monitor**: Re-run validation periodically as new data arrives

## References

- [Brier Score](https://en.wikipedia.org/wiki/Brier_score)
- [Log Loss](https://en.wikipedia.org/wiki/Cross_entropy)
- [ROC AUC](https://en.wikipedia.org/wiki/Receiver_operating_characteristic)
- [Calibration](https://scikit-learn.org/stable/modules/calibration.html)
