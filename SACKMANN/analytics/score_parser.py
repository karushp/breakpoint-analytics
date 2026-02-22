"""
Tennis score parsing utilities.

Handles parsing of tennis match score strings into structured data.
"""
import re
from typing import Dict, Optional, List
import pandas as pd


class ScoreParser:
    """Parser for tennis match scores."""
    
    # Regex patterns for score parsing
    TIEBREAK_PATTERN = re.compile(r'(\d+)-(\d+)\((\d+)\)')
    REGULAR_SET_PATTERN = re.compile(r'(\d+)-(\d+)')
    
    @staticmethod
    def parse(score_str: str) -> Optional[Dict]:
        """
        Parse tennis score string into structured data.
        
        Handles formats like:
        - "7-6(3) 6-3" (two sets with tiebreak)
        - "6-4 6-2" (two sets)
        - "6-3 4-6 6-2" (three sets)
        - "7-5 6-7(4) 6-1" (three sets with tiebreak)
        
        Args:
            score_str: Score string from match data
            
        Returns:
            Dictionary with parsed score data or None if parsing fails
            
        Example:
            >>> parser = ScoreParser()
            >>> result = parser.parse("6-4 6-2")
            >>> result['winning_margin_games']
            6
        """
        if pd.isna(score_str) or not isinstance(score_str, str):
            return None
        
        score_str = score_str.strip()
        if not score_str:
            return None
        
        # Split by spaces to get individual sets
        sets = score_str.split()
        if not sets:
            return None
        
        parsed_sets = []
        total_games_won = 0
        total_games_lost = 0
        
        for set_score in sets:
            parsed_set = ScoreParser._parse_set(set_score)
            if parsed_set is None:
                return None  # Invalid set score
            
            parsed_sets.append(parsed_set)
            total_games_won += parsed_set['winner_games']
            total_games_lost += parsed_set['loser_games']
        
        if not parsed_sets:
            return None
        
        return ScoreParser._build_score_dict(
            parsed_sets, total_games_won, total_games_lost
        )
    
    @staticmethod
    def _parse_set(set_score: str) -> Optional[Dict]:
        """
        Parse a single set score.
        
        Args:
            set_score: Single set score string (e.g., "6-4" or "7-6(3)")
            
        Returns:
            Dictionary with set data or None if invalid
        """
        # Try tiebreak format first
        tiebreak_match = ScoreParser.TIEBREAK_PATTERN.match(set_score)
        if tiebreak_match:
            return {
                'winner_games': int(tiebreak_match.group(1)),
                'loser_games': int(tiebreak_match.group(2)),
                'tiebreak': True,
                'tiebreak_score': int(tiebreak_match.group(3))
            }
        
        # Try regular set format
        regular_match = ScoreParser.REGULAR_SET_PATTERN.match(set_score)
        if regular_match:
            return {
                'winner_games': int(regular_match.group(1)),
                'loser_games': int(regular_match.group(2)),
                'tiebreak': False
            }
        
        return None
    
    @staticmethod
    def _build_score_dict(
        parsed_sets: List[Dict],
        total_games_won: int,
        total_games_lost: int
    ) -> Dict:
        """
        Build the final score dictionary from parsed sets.
        
        Args:
            parsed_sets: List of parsed set dictionaries
            total_games_won: Total games won by winner
            total_games_lost: Total games lost by winner
            
        Returns:
            Complete score dictionary
        """
        first_set = parsed_sets[0]
        second_set = parsed_sets[1] if len(parsed_sets) > 1 else None
        
        return {
            'sets': parsed_sets,
            'num_sets': len(parsed_sets),
            'total_games_won': total_games_won,
            'total_games_lost': total_games_lost,
            'first_set_winner_games': first_set['winner_games'],
            'first_set_loser_games': first_set['loser_games'],
            'first_set_won': first_set['winner_games'] > first_set['loser_games'],
            'second_set_winner_games': second_set['winner_games'] if second_set else None,
            'second_set_loser_games': second_set['loser_games'] if second_set else None,
            'second_set_won': (
                second_set['winner_games'] > second_set['loser_games']
                if second_set else None
            ),
            'winning_margin_games': total_games_won - total_games_lost
        }


# Backward compatibility function
def parse_tennis_score(score_str: str) -> Optional[Dict]:
    """
    Parse tennis score string (backward compatibility wrapper).
    
    Args:
        score_str: Score string from match data
        
    Returns:
        Dictionary with parsed score data or None if parsing fails
    """
    return ScoreParser.parse(score_str)
