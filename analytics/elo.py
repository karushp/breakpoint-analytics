"""
Elo rating system implementation for tennis players.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional
from analytics.config import (
    ELO_STARTING_RATING,
    ELO_K_FACTOR_REGULAR,
    ELO_K_FACTOR_GRAND_SLAM,
    ELO_K_FACTOR_SMALL,
    ELO_DECAY_CONSTANT_DAYS,
    SURFACE_ADJUSTMENTS
)


class EloRating:
    """Manages Elo ratings for tennis players."""
    
    def __init__(self, starting_rating: int = ELO_STARTING_RATING):
        """
        Initialize Elo rating system.
        
        Args:
            starting_rating: Starting Elo rating for new players
        """
        self.starting_rating = starting_rating
        self.ratings: Dict[str, float] = {}  # player_id -> Elo
        self.surface_ratings: Dict[str, Dict[str, float]] = {}  # player_id -> {surface -> Elo}
        
    def get_rating(self, player_id: str, surface: Optional[str] = None) -> float:
        """
        Get current Elo rating for a player.
        
        Args:
            player_id: Player identifier
            surface: Optional surface for surface-specific rating
            
        Returns:
            Elo rating
        """
        if surface and player_id in self.surface_ratings and surface in self.surface_ratings[player_id]:
            return self.surface_ratings[player_id][surface]
        
        return self.ratings.get(player_id, self.starting_rating)
    
    def get_surface_adjusted_rating(self, player_id: str, surface: str) -> float:
        """
        Get surface-adjusted Elo rating.
        
        Args:
            player_id: Player identifier
            surface: Surface type
            
        Returns:
            Surface-adjusted Elo rating
        """
        base_elo = self.get_rating(player_id)
        adjustment = SURFACE_ADJUSTMENTS.get(surface, 0)
        
        # If we have surface-specific rating, use it
        if player_id in self.surface_ratings and surface in self.surface_ratings[player_id]:
            return self.surface_ratings[player_id][surface]
        
        return base_elo + adjustment
    
    def expected_score(self, player_a_elo: float, player_b_elo: float) -> float:
        """
        Calculate expected score for player A against player B.
        
        Args:
            player_a_elo: Player A's Elo rating
            player_b_elo: Player B's Elo rating
            
        Returns:
            Expected score (0-1) for player A
        """
        return 1 / (1 + 10 ** ((player_b_elo - player_a_elo) / 400))
    
    def get_k_factor(self, tournament_level: str) -> int:
        """
        Get K-factor based on tournament level.
        
        Args:
            tournament_level: Tournament level code
            
        Returns:
            K-factor value
        """
        if tournament_level in ['G']:  # Grand Slam
            return ELO_K_FACTOR_GRAND_SLAM
        elif tournament_level in ['250', '500']:  # Smaller tournaments
            return ELO_K_FACTOR_SMALL
        else:
            return ELO_K_FACTOR_REGULAR
    
    def update_rating(
        self,
        winner_id: str,
        loser_id: str,
        surface: Optional[str] = None,
        tournament_level: str = "M",
        match_date: Optional[datetime] = None
    ):
        """
        Update Elo ratings after a match.
        
        Args:
            winner_id: Winner's player ID
            loser_id: Loser's player ID
            surface: Surface type
            tournament_level: Tournament level code
            match_date: Date of the match (for decay calculation)
        """
        # Initialize ratings if needed
        if winner_id not in self.ratings:
            self.ratings[winner_id] = self.starting_rating
        if loser_id not in self.ratings:
            self.ratings[loser_id] = self.starting_rating
        
        # Get current ratings
        winner_elo = self.get_surface_adjusted_rating(winner_id, surface) if surface else self.get_rating(winner_id)
        loser_elo = self.get_surface_adjusted_rating(loser_id, surface) if surface else self.get_rating(loser_id)
        
        # Calculate expected scores
        winner_expected = self.expected_score(winner_elo, loser_elo)
        loser_expected = 1 - winner_expected
        
        # Get K-factor
        k_factor = self.get_k_factor(tournament_level)
        
        # Apply time decay if match_date provided
        decay_weight = 1.0
        if match_date:
            days_ago = (datetime.now() - match_date).days
            if days_ago > 0:
                decay_weight = np.exp(-days_ago / ELO_DECAY_CONSTANT_DAYS)
        
        # Update ratings
        winner_change = k_factor * decay_weight * (1 - winner_expected)
        loser_change = k_factor * decay_weight * (0 - loser_expected)
        
        # Update base ratings
        self.ratings[winner_id] += winner_change
        self.ratings[loser_id] += loser_change
        
        # Update surface-specific ratings if surface provided
        if surface:
            if winner_id not in self.surface_ratings:
                self.surface_ratings[winner_id] = {}
            if loser_id not in self.surface_ratings:
                self.surface_ratings[loser_id] = {}
            
            if surface not in self.surface_ratings[winner_id]:
                self.surface_ratings[winner_id][surface] = self.starting_rating
            if surface not in self.surface_ratings[loser_id]:
                self.surface_ratings[loser_id][surface] = self.starting_rating
            
            self.surface_ratings[winner_id][surface] += winner_change
            self.surface_ratings[loser_id][surface] += loser_change
    
    def calculate_ratings_from_matches(self, matches_df: pd.DataFrame):
        """
        Calculate Elo ratings from historical matches.
        
        Args:
            matches_df: DataFrame with columns: winner_id, loser_id, surface, 
                       tourney_level, tourney_date
        """
        # Sort by date to process chronologically
        matches_df = matches_df.sort_values('tourney_date')
        
        for _, match in matches_df.iterrows():
            self.update_rating(
                winner_id=match['winner_id'],
                loser_id=match['loser_id'],
                surface=match.get('surface'),
                tournament_level=match.get('tourney_level', 'M'),
                match_date=pd.to_datetime(match['tourney_date']) if 'tourney_date' in match else None
            )
