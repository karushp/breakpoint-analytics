"""
Ingest data from Jeff Sackmann's tennis_atp repository.
"""
import pandas as pd
import os
import requests
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from analytics.config import DATA_RAW_DIR, SACKMANN_CSV_BASE_URL
from analytics.utils import normalize_player_name, create_player_id


def download_sackmann_csv(year: int, save_path: Optional[str] = None) -> pd.DataFrame:
    """
    Download ATP matches CSV for a given year from Sackmann repo.
    
    Args:
        year: Year to download
        save_path: Optional path to save CSV file
        
    Returns:
        DataFrame with match data
    """
    url = f"{SACKMANN_CSV_BASE_URL}/atp_matches_{year}.csv"
    
    print(f"Downloading {url}...")
    try:
        df = pd.read_csv(url)
        
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            df.to_csv(save_path, index=False)
            print(f"Saved to {save_path}")
        
        return df
    except Exception as e:
        print(f"Error downloading {year}: {e}")
        return pd.DataFrame()


def load_sackmann_data(years: List[int], data_dir: str = DATA_RAW_DIR) -> pd.DataFrame:
    """
    Load multiple years of Sackmann data.
    
    Args:
        years: List of years to load
        data_dir: Directory to save/load CSV files
        
    Returns:
        Combined DataFrame
    """
    all_data = []
    failed_years = []
    
    for year in years:
        csv_path = os.path.join(data_dir, f"atp_matches_{year}.csv")
        
        # Try to load from local file first
        if os.path.exists(csv_path):
            print(f"Loading {csv_path} from local...")
            df = pd.read_csv(csv_path)
        else:
            # Download if not available locally
            df = download_sackmann_csv(year, csv_path)
        
        if not df.empty:
            df['year'] = year
            all_data.append(df)
        else:
            failed_years.append(year)
    
    if failed_years:
        print(f"\n⚠️  Warning: Could not load data for years: {failed_years}")
        print("   These years may not be available yet in the repository.")
        if all_data:
            print(f"   Continuing with {len(all_data)} year(s) of available data.\n")
        else:
            print("   No data available! Please check the repository or your connection.\n")
    
    if not all_data:
        return pd.DataFrame()
    
    combined = pd.concat(all_data, ignore_index=True)
    return combined


def normalize_match_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize and clean match data.
    
    Args:
        df: Raw match DataFrame
        
    Returns:
        Normalized DataFrame
    """
    df = df.copy()
    
    # Normalize player names and create IDs
    if 'winner_name' in df.columns:
        df['winner_name_normalized'] = df['winner_name'].apply(normalize_player_name)
        df['winner_id'] = df['winner_name_normalized'].apply(create_player_id)
    
    if 'loser_name' in df.columns:
        df['loser_name_normalized'] = df['loser_name'].apply(normalize_player_name)
        df['loser_id'] = df['loser_name_normalized'].apply(create_player_id)
    
    # Normalize date column
    if 'tourney_date' in df.columns:
        df['tourney_date'] = pd.to_datetime(df['tourney_date'], format='%Y%m%d', errors='coerce')
    
    # Normalize surface
    if 'surface' in df.columns:
        df['surface'] = df['surface'].str.capitalize()
        df['surface'] = df['surface'].replace({'Hard': 'Hard', 'Clay': 'Clay', 'Grass': 'Grass'})
    
    # Remove rows with missing critical data
    critical_cols = ['winner_id', 'loser_id', 'tourney_date']
    df = df.dropna(subset=[col for col in critical_cols if col in df.columns])
    
    return df


def get_available_years() -> List[int]:
    """
    Get list of available years from Sackmann repo.
    For now, return a hardcoded list. Could be improved to scrape the repo.
    
    Returns:
        List of available years
    """
    # Common years available (adjust based on actual repo)
    current_year = datetime.now().year
    return list(range(2000, current_year + 1))


def main():
    """Main ingestion function."""
    print("Starting data ingestion from Sackmann repository...")
    
    # Get recent years: 2022-2025
    # Note: 2025 data may not be available yet in the repository
    # The code will continue with available years if some are missing
    current_year = datetime.now().year
    years = list(range(2022, min(current_year + 1, 2026)))  # 2022-2025, or up to current year
    
    # Load data
    df = load_sackmann_data(years, DATA_RAW_DIR)
    
    if df.empty:
        print("No data loaded. Check your internet connection and data source.")
        return
    
    print(f"Loaded {len(df)} matches")
    
    # Normalize data
    df_normalized = normalize_match_data(df)
    print(f"Normalized data: {len(df_normalized)} matches")
    
    # Save processed data
    output_path = os.path.join(DATA_RAW_DIR, "matches_combined.csv")
    df_normalized.to_csv(output_path, index=False)
    print(f"Saved normalized data to {output_path}")
    
    return df_normalized


if __name__ == "__main__":
    main()
