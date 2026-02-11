"""
Validation pipeline for tennis match prediction models.

This script:
1. Loads match data
2. Splits into train/test sets (time-based)
3. Evaluates Elo-only and Hybrid models
4. Compares performance and outputs results
"""
import pandas as pd
import os
import json
from datetime import datetime
from analytics.config import DATA_RAW_DIR, OUTPUTS_DIR
from analytics.validation import (
    MatchPredictorValidator,
    print_evaluation_results,
    print_comparison
)


def load_match_data(data_path: str) -> pd.DataFrame:
    """
    Load match data from CSV file.
    
    Args:
        data_path: Path to matches CSV file
        
    Returns:
        DataFrame with match data
        
    Raises:
        FileNotFoundError: If data file doesn't exist
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(
            f"Match data file not found: {data_path}\n"
            "Please run ingest_sackmann.py first to download and normalize data."
        )
    
    matches_df = pd.read_csv(data_path)
    
    # Ensure date column is datetime
    if 'tourney_date' in matches_df.columns:
        matches_df['tourney_date'] = pd.to_datetime(
            matches_df['tourney_date'], errors='coerce'
        )
    
    return matches_df


def save_results(results: dict, output_path: str) -> None:
    """
    Save validation results to JSON file.
    
    Args:
        results: Dictionary with validation results
        output_path: Path to save JSON file
    """
    import numpy as np
    
    # Convert numpy types to native Python types for JSON serialization
    def convert_to_serializable(obj):
        if isinstance(obj, dict):
            return {k: convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_serializable(item) for item in obj]
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj) if isinstance(obj, np.floating) else int(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        return obj
    
    serializable_results = convert_to_serializable(results)
    
    with open(output_path, 'w') as f:
        json.dump(serializable_results, f, indent=2, default=str)


def main():
    """Main validation function."""
    print("=" * 60)
    print("Tennis Match Prediction Model Validation")
    print("=" * 60)
    
    # Load match data
    data_path = os.path.join(DATA_RAW_DIR, "matches_combined.csv")
    print(f"\nLoading match data from {data_path}...")
    
    try:
        matches_df = load_match_data(data_path)
        print(f"✓ Loaded {len(matches_df):,} matches")
    except FileNotFoundError as e:
        print(f"✗ Error: {e}")
        return
    
    # Initialize validator with time-based split
    print("\nSplitting data into train/test sets...")
    try:
        validator = MatchPredictorValidator(
            matches_df=matches_df,
            # Use 80% for training, 20% for testing (default)
            # Can customize dates if needed
        )
    except ValueError as e:
        print(f"✗ Error: {e}")
        return
    
    # Compare models
    print("\nRunning model evaluation...")
    comparison = validator.compare_models()
    
    # Print results
    print_evaluation_results(comparison['elo_only'])
    print_evaluation_results(comparison['hybrid'])
    print_comparison(comparison)
    
    # Save results
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    results_path = os.path.join(OUTPUTS_DIR, 'validation_results.json')
    
    # Add metadata
    comparison['metadata'] = {
        'validation_date': datetime.now().isoformat(),
        'train_start': validator.train_start_date.isoformat(),
        'train_end': validator.train_end_date.isoformat(),
        'test_start': validator.test_start_date.isoformat(),
        'test_end': validator.test_end_date.isoformat(),
        'n_train_matches': len(validator.train_matches),
        'n_test_matches': len(validator.test_matches)
    }
    
    save_results(comparison, results_path)
    print(f"\n✓ Results saved to {results_path}")
    
    print("\n" + "=" * 60)
    print("Validation Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
