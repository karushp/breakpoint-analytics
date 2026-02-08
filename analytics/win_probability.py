"""
Win probability calculation for tennis matches.
"""
from typing import Dict, Optional
from analytics.elo import EloRating


class WinProbabilityCalculator:
    """Calculates win probabilities for matchups."""
    
    def __init__(self, elo_system: EloRating):
        """
        Initialize win probability calculator.
        
        Args:
            elo_system: EloRating instance with calculated ratings
        """
        self.elo_system = elo_system
    
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
        
        return result
