"""
Win probability calculation for tennis matches.

This module provides the WinProbabilityCalculator class for calculating
match win probabilities using Elo ratings, detailed metrics, and hybrid approaches.
"""
from typing import Dict, Optional
from analytics.elo import EloRating
from analytics.feature_engineering import FeatureEngineer
from analytics.config import (
    ELO_WEIGHT,
    METRICS_WEIGHT,
    USE_METRICS_FALLBACK,
    MIN_METRICS_REQUIRED,
    USE_LATEST_GAME_RECENT_WIN_BONUS,
    LATEST_GAME_RECENT_DAYS,
    LATEST_GAME_RECENT_WIN_BOOST,
)


class WinProbabilityCalculator:
    """Calculates win probabilities for matchups."""
    
    def __init__(self, elo_system: EloRating, feature_engineer: Optional[FeatureEngineer] = None):
        """
        Initialize win probability calculator.
        
        Args:
            elo_system: EloRating instance with calculated ratings
            feature_engineer: Optional FeatureEngineer instance for metric-based calculations
                            
        Raises:
            TypeError: If elo_system is not an EloRating instance
        """
        if not isinstance(elo_system, EloRating):
            raise TypeError("elo_system must be an EloRating instance")
        
        self.elo_system = elo_system
        self.feature_engineer = feature_engineer
    
    def calculate_elo_based_probability(
        self,
        player_a_id: str,
        player_b_id: str,
        surface: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Calculate win probability using Elo ratings.
        
        Args:
            player_a_id: First player identifier
            player_b_id: Second player identifier
            surface: Optional surface for surface-adjusted ratings
            
        Returns:
            Dictionary with win probabilities and metadata
        """
        # Get Elo ratings
        if surface:
            player_a_elo = self.elo_system.get_surface_adjusted_rating(player_a_id, surface)
            player_b_elo = self.elo_system.get_surface_adjusted_rating(player_b_id, surface)
            method = "elo_surface_adjusted"
        else:
            player_a_elo = self.elo_system.get_rating(player_a_id)
            player_b_elo = self.elo_system.get_rating(player_b_id)
            method = "elo_global"
        
        # Calculate expected score (win probability)
        player_a_prob = self.elo_system.expected_score(player_a_elo, player_b_elo)
        player_b_prob = 1 - player_a_prob
        
        # Determine confidence level
        confidence = self._determine_confidence(player_a_elo, player_b_elo)
        
        return {
            "player_a_win_prob": round(player_a_prob, 3),
            "player_b_win_prob": round(player_b_prob, 3),
            "player_a_elo": round(player_a_elo, 1),
            "player_b_elo": round(player_b_elo, 1),
            "confidence": confidence,
            "method": method
        }
    
    def _determine_confidence(
        self,
        player_a_elo: float,
        player_b_elo: float
    ) -> str:
        """
        Determine confidence level based on Elo difference and data quality.
        
        Args:
            player_a_elo: Player A's Elo
            player_b_elo: Player B's Elo
            
        Returns:
            Confidence level: "high", "medium", or "low"
        """
        elo_diff = abs(player_a_elo - player_b_elo)
        
        # High confidence: large Elo difference
        if elo_diff > 200:
            return "high"
        # Medium confidence: moderate difference
        elif elo_diff > 100:
            return "medium"
        # Low confidence: close ratings
        else:
            return "low"
    
    def calculate_with_features(
        self,
        player_a_id: str,
        player_b_id: str,
        surface: Optional[str] = None,
        h2h_record: Optional[Dict] = None,
        recent_form: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        Calculate win probability using Elo + additional features.
        
        This is a placeholder for future logistic regression implementation.
        For now, uses Elo with minor adjustments based on H2H and form.
        
        Args:
            player_a_id: First player identifier
            player_b_id: Second player identifier
            surface: Optional surface
            h2h_record: Optional H2H record dictionary
            recent_form: Optional recent form dictionary
            
        Returns:
            Dictionary with win probabilities
        """
        # Start with Elo-based probability
        result = self.calculate_elo_based_probability(player_a_id, player_b_id, surface)
        
        # Apply H2H adjustment (small boost if significant H2H advantage)
        if h2h_record and h2h_record.get('total_matches', 0) >= 3:
            player_a_h2h_wins = h2h_record.get('player_a_wins', 0)
            total_h2h = h2h_record.get('total_matches', 1)
            h2h_advantage = (player_a_h2h_wins / total_h2h) - 0.5
            
            # Small adjustment: ±5% max based on H2H
            h2h_adjustment = h2h_advantage * 0.05
            result['player_a_win_prob'] = max(0.05, min(0.95, 
                result['player_a_win_prob'] + h2h_adjustment))
            result['player_b_win_prob'] = 1 - result['player_a_win_prob']
        
        # Apply recent form adjustment
        if recent_form:
            # This would use recent form data to adjust probabilities
            # Placeholder for now
            pass
        
        # Apply latest-game recency bonus if enabled
        if (
            USE_LATEST_GAME_RECENT_WIN_BONUS
            and self.feature_engineer
        ):
            ref_date = self.feature_engineer.matches_df['tourney_date'].max()
            if hasattr(ref_date, 'to_pydatetime'):
                ref_date = ref_date.to_pydatetime()
            info_a = self.feature_engineer.get_latest_game_info(player_a_id, ref_date)
            info_b = self.feature_engineer.get_latest_game_info(player_b_id, ref_date)
            prob_a = result['player_a_win_prob']
            if info_a.get('days_ago') is not None and info_a['days_ago'] <= LATEST_GAME_RECENT_DAYS and info_a.get('is_win'):
                prob_a = prob_a + LATEST_GAME_RECENT_WIN_BOOST
            if info_b.get('days_ago') is not None and info_b['days_ago'] <= LATEST_GAME_RECENT_DAYS and info_b.get('is_win'):
                prob_a = prob_a - LATEST_GAME_RECENT_WIN_BOOST
            prob_a = max(0.05, min(0.95, prob_a))
            result['player_a_win_prob'] = round(prob_a, 3)
            result['player_b_win_prob'] = round(1 - prob_a, 3)
        
        return result
    
    def calculate_metric_based_probability(
        self,
        player_a_id: str,
        player_b_id: str,
        surface: Optional[str] = None
    ) -> Dict:
        """
        Calculate win probability based on detailed metrics comparison.
        
        Args:
            player_a_id: First player identifier
            player_b_id: Second player identifier
            surface: Optional surface for surface-specific comparison
            
        Returns:
            Dictionary with metric-based probabilities and comparison data
        """
        if not self.feature_engineer:
            raise ValueError("FeatureEngineer instance required for metric-based probability")
        
        metric_comparison = self.feature_engineer.compare_detailed_metrics(
            player_a_id, player_b_id, surface
        )
        
        return {
            "player_a_win_prob": metric_comparison['metric_probability']['player_a'],
            "player_b_win_prob": metric_comparison['metric_probability']['player_b'],
            "method": "metrics_only",
            "metric_comparison": metric_comparison['metric_comparison'],
            "key_advantages": metric_comparison['key_advantages'],
            "metrics_available": metric_comparison['metrics_available'],
            "total_metrics": metric_comparison['total_metrics']
        }
    
    def calculate_hybrid_probability(
        self,
        player_a_id: str,
        player_b_id: str,
        surface: Optional[str] = None,
        h2h_record: Optional[Dict] = None
    ) -> Dict:
        """
        Calculate win probability using hybrid approach: Elo + Metrics.
        
        Uses fallback to Elo-only if insufficient metrics are available.
        
        Args:
            player_a_id: First player identifier
            player_b_id: Second player identifier
            surface: Optional surface for surface-adjusted ratings
            h2h_record: Optional H2H record dictionary
            
        Returns:
            Dictionary with hybrid win probabilities and metadata
        """
        # Start with Elo-based probability
        elo_result = self.calculate_elo_based_probability(player_a_id, player_b_id, surface)
        elo_prob_a = elo_result['player_a_win_prob']
        
        # Try to get metric-based probability
        use_metrics = False
        metric_prob_a = None
        metric_comparison_data = None
        
        if self.feature_engineer:
            try:
                metric_result = self.calculate_metric_based_probability(
                    player_a_id, player_b_id, surface
                )
                metrics_available = metric_result.get('metrics_available', 0)
                
                # Check if we have enough metrics
                if metrics_available >= MIN_METRICS_REQUIRED or not USE_METRICS_FALLBACK:
                    metric_prob_a = metric_result['player_a_win_prob']
                    metric_comparison_data = {
                        'comparison': metric_result['metric_comparison'],
                        'key_advantages': metric_result['key_advantages'],
                        'metrics_available': metrics_available
                    }
                    use_metrics = True
            except Exception as e:
                # If metric calculation fails, fall back to Elo
                # In production, you might want to log this error
                use_metrics = False
        
        # Calculate final probability
        if use_metrics and metric_prob_a is not None:
            # Hybrid: weighted combination of Elo and Metrics
            final_prob_a = (ELO_WEIGHT * elo_prob_a) + (METRICS_WEIGHT * metric_prob_a)
            final_prob_a = max(0.05, min(0.95, final_prob_a))  # Clamp between 5% and 95%
            method = "hybrid_elo_metrics"
        else:
            # Fallback: Elo only
            final_prob_a = elo_prob_a
            method = elo_result['method']
            if not use_metrics:
                method += "_fallback"
        
        final_prob_b = 1 - final_prob_a
        
        # Apply H2H adjustment if available
        if h2h_record and h2h_record.get('total_matches', 0) >= 3:
            player_a_h2h_wins = h2h_record.get('player_a_wins', 0)
            total_h2h = h2h_record.get('total_matches', 1)
            h2h_advantage = (player_a_h2h_wins / total_h2h) - 0.5
            
            # Small adjustment: ±3% max based on H2H (reduced since we have metrics now)
            h2h_adjustment = h2h_advantage * 0.03
            final_prob_a = max(0.05, min(0.95, final_prob_a + h2h_adjustment))
            final_prob_b = 1 - final_prob_a
        
        # Apply latest-game recency bonus: if latest match was a win within last N days, small boost
        if (
            USE_LATEST_GAME_RECENT_WIN_BONUS
            and self.feature_engineer
        ):
            ref_date = self.feature_engineer.matches_df['tourney_date'].max()
            if hasattr(ref_date, 'to_pydatetime'):
                ref_date = ref_date.to_pydatetime()
            info_a = self.feature_engineer.get_latest_game_info(player_a_id, ref_date)
            info_b = self.feature_engineer.get_latest_game_info(player_b_id, ref_date)
            if info_a.get('days_ago') is not None and info_a['days_ago'] <= LATEST_GAME_RECENT_DAYS and info_a.get('is_win'):
                final_prob_a = final_prob_a + LATEST_GAME_RECENT_WIN_BOOST
            if info_b.get('days_ago') is not None and info_b['days_ago'] <= LATEST_GAME_RECENT_DAYS and info_b.get('is_win'):
                final_prob_a = final_prob_a - LATEST_GAME_RECENT_WIN_BOOST
            final_prob_a = max(0.05, min(0.95, final_prob_a))
            final_prob_b = 1 - final_prob_a
        
        result = {
            "player_a_win_prob": round(final_prob_a, 3),
            "player_b_win_prob": round(final_prob_b, 3),
            "player_a_elo": elo_result['player_a_elo'],
            "player_b_elo": elo_result['player_b_elo'],
            "confidence": elo_result['confidence'],
            "method": method,
            "elo_probability": {
                "player_a": round(elo_prob_a, 3),
                "player_b": round(1 - elo_prob_a, 3)
            }
        }
        
        if use_metrics and metric_comparison_data:
            result["metric_probability"] = {
                "player_a": round(metric_prob_a, 3),
                "player_b": round(1 - metric_prob_a, 3)
            }
            result["metric_comparison"] = metric_comparison_data['comparison']
            result["key_advantages"] = metric_comparison_data['key_advantages']
            result["metrics_available"] = metric_comparison_data['metrics_available']
        else:
            result["metric_probability"] = None
            result["fallback_reason"] = "Insufficient metrics available" if self.feature_engineer else "FeatureEngineer not provided"
        
        return result
