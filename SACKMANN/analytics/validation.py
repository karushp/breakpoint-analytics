"""
Validation module for tennis match prediction models.

This module provides functions for:
- Time-based train/test splitting (critical for time-series data)
- Walk-forward validation (simulates real-world prediction scenarios)
- Evaluation metrics (accuracy, Brier score, log loss, calibration)
- Model comparison (Elo-only vs Hybrid model)
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    log_loss,
    roc_auc_score
)
from sklearn.calibration import calibration_curve
import warnings
warnings.filterwarnings('ignore')  # Suppress sklearn warnings

from analytics.elo import EloRating
from analytics.feature_engineering import FeatureEngineer
from analytics.win_probability import WinProbabilityCalculator
from analytics.config import (
    ELO_STARTING_RATING,
    MIN_MATCHES_FOR_STATS
)


class MatchPredictorValidator:
    """
    Validates tennis match prediction models using time-based splitting.
    
    This validator ensures that:
    1. Training data always comes before test data (no data leakage)
    2. Elo ratings are updated incrementally (simulating real-world usage)
    3. Multiple evaluation metrics are computed for comprehensive assessment
    """
    
    def __init__(
        self,
        matches_df: pd.DataFrame,
        train_start_date: Optional[datetime] = None,
        train_end_date: Optional[datetime] = None,
        test_start_date: Optional[datetime] = None,
        test_end_date: Optional[datetime] = None,
        min_train_matches: int = 100,
        min_test_matches: int = 50
    ):
        """
        Initialize validator with match data and split configuration.
        
        Args:
            matches_df: DataFrame with match data (must have 'tourney_date', 
                       'winner_id', 'loser_id' columns)
            train_start_date: Start date for training set (default: earliest date)
            train_end_date: End date for training set (default: 80% of data)
            test_start_date: Start date for test set (default: train_end_date + 1 day)
            test_end_date: End date for test set (default: latest date)
            min_train_matches: Minimum matches required in training set
            min_test_matches: Minimum matches required in test set
            
        Raises:
            ValueError: If date ranges are invalid or insufficient data
        """
        self.matches_df = matches_df.copy()
        
        # Ensure date column is datetime
        if 'tourney_date' in self.matches_df.columns:
            self.matches_df['tourney_date'] = pd.to_datetime(
                self.matches_df['tourney_date'], errors='coerce'
            )
        
        # Sort by date
        self.matches_df = self.matches_df.sort_values('tourney_date').reset_index(drop=True)
        
        # Validate required columns
        required_cols = ['tourney_date', 'winner_id', 'loser_id']
        missing_cols = [col for col in required_cols if col not in self.matches_df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Set default date ranges
        all_dates = self.matches_df['tourney_date'].dropna()
        if len(all_dates) == 0:
            raise ValueError("No valid dates found in match data")
        
        earliest_date = all_dates.min()
        latest_date = all_dates.max()
        total_days = (latest_date - earliest_date).days
        
        if train_start_date is None:
            train_start_date = earliest_date
        if train_end_date is None:
            # Default: use 80% of data for training
            train_end_date = earliest_date + timedelta(days=int(total_days * 0.8))
        if test_start_date is None:
            test_start_date = train_end_date + timedelta(days=1)
        if test_end_date is None:
            test_end_date = latest_date
        
        # Validate date ranges
        if train_end_date >= test_start_date:
            raise ValueError(
                "Training end date must be before test start date. "
                f"Got train_end={train_end_date}, test_start={test_start_date}"
            )
        
        self.train_start_date = train_start_date
        self.train_end_date = train_end_date
        self.test_start_date = test_start_date
        self.test_end_date = test_end_date
        
        # Split data
        self.train_matches = self.matches_df[
            (self.matches_df['tourney_date'] >= train_start_date) &
            (self.matches_df['tourney_date'] <= train_end_date)
        ].copy()
        
        self.test_matches = self.matches_df[
            (self.matches_df['tourney_date'] >= test_start_date) &
            (self.matches_df['tourney_date'] <= test_end_date)
        ].copy()
        
        # Validate split sizes
        if len(self.train_matches) < min_train_matches:
            raise ValueError(
                f"Insufficient training data: {len(self.train_matches)} matches "
                f"(minimum: {min_train_matches})"
            )
        
        if len(self.test_matches) < min_test_matches:
            raise ValueError(
                f"Insufficient test data: {len(self.test_matches)} matches "
                f"(minimum: {min_test_matches})"
            )
        
        print(f"✓ Data split complete:")
        print(f"  Training: {len(self.train_matches)} matches "
              f"({train_start_date.date()} to {train_end_date.date()})")
        print(f"  Test: {len(self.test_matches)} matches "
              f"({test_start_date.date()} to {test_end_date.date()})")
    
    def evaluate_elo_only(
        self,
        use_surface_adjustment: bool = True
    ) -> Dict:
        """
        Evaluate Elo-only prediction model.
        
        Args:
            use_surface_adjustment: Whether to use surface-adjusted Elo ratings
            
        Returns:
            Dictionary with evaluation metrics
        """
        # Build Elo system from training data
        elo_system = EloRating()
        elo_system.calculate_ratings_from_matches(self.train_matches)
        
        # Make predictions on test set
        predictions = []
        actuals = []
        probabilities = []
        
        # Process test matches chronologically to update Elo incrementally
        test_sorted = self.test_matches.sort_values('tourney_date').copy()
        
        for _, match in test_sorted.iterrows():
            winner_id = match['winner_id']
            loser_id = match['loser_id']
            surface = match.get('surface')
            
            # Get Elo ratings (before match)
            if use_surface_adjustment and surface:
                winner_elo = elo_system.get_surface_adjusted_rating(winner_id, surface)
                loser_elo = elo_system.get_surface_adjusted_rating(loser_id, surface)
            else:
                winner_elo = elo_system.get_rating(winner_id)
                loser_elo = elo_system.get_rating(loser_id)
            
            # Calculate win probability
            winner_prob = elo_system.expected_score(winner_elo, loser_elo)
            
            # Store prediction: predict winner if prob > 0.5
            predictions.append(1 if winner_prob > 0.5 else 0)
            actuals.append(1)  # Actual: winner won
            probabilities.append(winner_prob)
            
            # Update Elo ratings (simulating real-world usage)
            elo_system.update_rating(
                winner_id=winner_id,
                loser_id=loser_id,
                surface=surface,
                tournament_level=match.get('tourney_level', 'M'),
                match_date=match['tourney_date']
            )
        
        return self._calculate_metrics(actuals, predictions, probabilities, "Elo-Only")
    
    def evaluate_hybrid_model(
        self,
        use_surface_adjustment: bool = True
    ) -> Dict:
        """
        Evaluate hybrid model (Elo + Metrics).
        
        Args:
            use_surface_adjustment: Whether to use surface-adjusted Elo ratings
            
        Returns:
            Dictionary with evaluation metrics
        """
        # Build systems from training data
        elo_system = EloRating()
        elo_system.calculate_ratings_from_matches(self.train_matches)
        
        feature_engineer = FeatureEngineer(self.train_matches)
        win_prob_calc = WinProbabilityCalculator(elo_system, feature_engineer)
        
        # Make predictions on test set
        predictions = []
        actuals = []
        probabilities = []
        
        # Process test matches chronologically
        test_sorted = self.test_matches.sort_values('tourney_date').copy()
        
        for _, match in test_sorted.iterrows():
            winner_id = match['winner_id']
            loser_id = match['loser_id']
            surface = match.get('surface', 'Hard')
            
            # Get H2H (from training data only)
            h2h = feature_engineer.get_head_to_head(winner_id, loser_id)
            
            # Calculate hybrid probability
            win_prob = win_prob_calc.calculate_hybrid_probability(
                winner_id, loser_id, surface, h2h
            )
            
            winner_prob = win_prob['player_a_win_prob']
            
            # Store prediction: predict winner if prob > 0.5
            predictions.append(1 if winner_prob > 0.5 else 0)
            actuals.append(1)  # Actual: winner won
            probabilities.append(winner_prob)
            
            # Update systems (simulating real-world usage)
            elo_system.update_rating(
                winner_id=winner_id,
                loser_id=loser_id,
                surface=surface,
                tournament_level=match.get('tourney_level', 'M'),
                match_date=match['tourney_date']
            )
            
            # Note: FeatureEngineer would need to be updated with new match
            # For simplicity, we'll use training data features only
            # In production, you'd update feature_engineer incrementally
        
        return self._calculate_metrics(actuals, predictions, probabilities, "Hybrid")
    
    def _calculate_metrics(
        self,
        actuals: List[int],
        predictions: List[int],
        probabilities: List[float],
        model_name: str
    ) -> Dict:
        """
        Calculate comprehensive evaluation metrics.
        
        Args:
            actuals: Actual outcomes (1 = predicted player won, 0 = lost)
            predictions: Predicted outcomes (1 = win, 0 = loss)
            probabilities: Predicted win probabilities
            model_name: Name of the model being evaluated
            
        Returns:
            Dictionary with evaluation metrics
        """
        actuals = np.array(actuals)
        predictions = np.array(predictions)
        probabilities = np.array(probabilities)
        
        # Basic metrics
        accuracy = accuracy_score(actuals, predictions)
        
        # Probability calibration metrics
        brier_score = brier_score_loss(actuals, probabilities)
        
        # Log loss (requires probabilities for both classes)
        # Convert to [prob_win, prob_loss] format
        prob_both = np.column_stack([probabilities, 1 - probabilities])
        # Explicitly provide labels to handle binary case
        log_loss_score = log_loss(actuals, prob_both, labels=[0, 1])
        
        # ROC AUC
        try:
            roc_auc = roc_auc_score(actuals, probabilities)
        except ValueError:
            # Can happen if all predictions are the same class
            roc_auc = np.nan
        
        # Calibration curve data
        try:
            fraction_of_positives, mean_predicted_value = calibration_curve(
                actuals, probabilities, n_bins=10, strategy='uniform'
            )
            calibration_error = np.mean(np.abs(fraction_of_positives - mean_predicted_value))
        except (ValueError, ZeroDivisionError):
            calibration_error = np.nan
            fraction_of_positives = np.array([])
            mean_predicted_value = np.array([])
        
        # Additional statistics
        mean_probability = np.mean(probabilities)
        std_probability = np.std(probabilities)
        
        # Count predictions by confidence level
        high_confidence = np.sum((probabilities > 0.7) | (probabilities < 0.3))
        medium_confidence = np.sum((probabilities >= 0.3) & (probabilities <= 0.7))
        
        return {
            'model_name': model_name,
            'n_matches': len(actuals),
            'accuracy': round(accuracy, 4),
            'brier_score': round(brier_score, 4),
            'log_loss': round(log_loss_score, 4),
            'roc_auc': round(roc_auc, 4) if not np.isnan(roc_auc) else None,
            'calibration_error': round(calibration_error, 4) if not np.isnan(calibration_error) else None,
            'mean_probability': round(mean_probability, 4),
            'std_probability': round(std_probability, 4),
            'high_confidence_predictions': int(high_confidence),
            'medium_confidence_predictions': int(medium_confidence),
            'calibration_curve': {
                'fraction_of_positives': fraction_of_positives.tolist(),
                'mean_predicted_value': mean_predicted_value.tolist()
            }
        }
    
    def compare_models(self) -> Dict:
        """
        Compare Elo-only vs Hybrid model performance.
        
        Returns:
            Dictionary with comparison results
        """
        print("\n" + "=" * 60)
        print("Evaluating Models...")
        print("=" * 60)
        
        elo_results = self.evaluate_elo_only()
        hybrid_results = self.evaluate_hybrid_model()
        
        comparison = {
            'elo_only': elo_results,
            'hybrid': hybrid_results,
            'improvement': {}
        }
        
        # Calculate improvements
        for metric in ['accuracy', 'brier_score', 'log_loss', 'roc_auc']:
            elo_val = elo_results.get(metric)
            hybrid_val = hybrid_results.get(metric)
            
            if elo_val is not None and hybrid_val is not None:
                if metric in ['brier_score', 'log_loss']:
                    # Lower is better
                    improvement = ((elo_val - hybrid_val) / elo_val) * 100
                else:
                    # Higher is better
                    improvement = ((hybrid_val - elo_val) / elo_val) * 100
                
                comparison['improvement'][metric] = round(improvement, 2)
        
        return comparison


def print_evaluation_results(results: Dict) -> None:
    """
    Print evaluation results in a readable format.
    
    Args:
        results: Dictionary with evaluation metrics
    """
    print("\n" + "=" * 60)
    print(f"Evaluation Results: {results['model_name']}")
    print("=" * 60)
    print(f"Matches evaluated: {results['n_matches']:,}")
    print(f"\nPerformance Metrics:")
    print(f"  Accuracy:           {results['accuracy']:.2%}")
    print(f"  Brier Score:        {results['brier_score']:.4f} (lower is better)")
    print(f"  Log Loss:           {results['log_loss']:.4f} (lower is better)")
    if results.get('roc_auc') is not None:
        print(f"  ROC AUC:            {results['roc_auc']:.4f} (higher is better)")
    if results.get('calibration_error') is not None:
        print(f"  Calibration Error:  {results['calibration_error']:.4f} (lower is better)")
    print(f"\nProbability Statistics:")
    print(f"  Mean Probability:   {results['mean_probability']:.2%}")
    print(f"  Std Probability:    {results['std_probability']:.4f}")
    print(f"  High Confidence:    {results['high_confidence_predictions']:,} matches")
    print(f"  Medium Confidence:  {results['medium_confidence_predictions']:,} matches")


def print_comparison(comparison: Dict) -> None:
    """
    Print model comparison results.
    
    Args:
        comparison: Dictionary with comparison results
    """
    print("\n" + "=" * 60)
    print("Model Comparison")
    print("=" * 60)
    
    elo = comparison['elo_only']
    hybrid = comparison['hybrid']
    
    print(f"\n{'Metric':<20} {'Elo-Only':<15} {'Hybrid':<15} {'Improvement':<15}")
    print("-" * 65)
    print(f"{'Accuracy':<20} {elo['accuracy']:<15.2%} {hybrid['accuracy']:<15.2%} "
          f"{comparison['improvement'].get('accuracy', 0):>+13.2f}%")
    print(f"{'Brier Score':<20} {elo['brier_score']:<15.4f} {hybrid['brier_score']:<15.4f} "
          f"{comparison['improvement'].get('brier_score', 0):>+13.2f}%")
    print(f"{'Log Loss':<20} {elo['log_loss']:<15.4f} {hybrid['log_loss']:<15.4f} "
          f"{comparison['improvement'].get('log_loss', 0):>+13.2f}%")
    
    if elo.get('roc_auc') and hybrid.get('roc_auc'):
        print(f"{'ROC AUC':<20} {elo['roc_auc']:<15.4f} {hybrid['roc_auc']:<15.4f} "
              f"{comparison['improvement'].get('roc_auc', 0):>+13.2f}%")
    
    print("\n" + "=" * 60)
