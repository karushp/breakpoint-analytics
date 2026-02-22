"""
Load historical match data from TennisMyLife (stats.tennismylife.org).

Returns a single DataFrame of all matches, sorted by tourney_date.
"""
import pandas as pd

from analytics.config import (
    get_tennismylife_year_url,
    TENNISMYLIFE_YEARS,
    TENNISMYLIFE_CURRENT_TOURNEYS_URL,
)


def load_historical_matches(
    years: list[int] | None = None,
    include_ongoing: bool = True,
) -> pd.DataFrame:
    """
    Load and concatenate year CSVs (and optionally ongoing tourneys) into one DataFrame.

    Args:
        years: List of years to load (default: TENNISMYLIFE_YEARS from config).
        include_ongoing: If True, append ongoing_tourneys.csv (in-progress tournaments).

    Returns:
        DataFrame with columns including tourney_date, winner_name, loser_name,
        surface, winner_rank, loser_rank, minutes, w_ace, l_ace, w_bpSaved, etc.
        tourney_date is datetime. Sorted by tourney_date.
    """
    years = years or TENNISMYLIFE_YEARS
    frames = []

    for year in years:
        url = get_tennismylife_year_url(year)
        try:
            df = pd.read_csv(url)
            frames.append(df)
        except Exception as e:
            print(f"Skip {year}: {e}")

    if include_ongoing:
        try:
            ongoing = pd.read_csv(TENNISMYLIFE_CURRENT_TOURNEYS_URL)
            frames.append(ongoing)
        except Exception as e:
            print(f"Skip ongoing tourneys: {e}")

    if not frames:
        return pd.DataFrame()

    out = pd.concat(frames, ignore_index=True)
    out["tourney_date"] = pd.to_datetime(
        out["tourney_date"].astype(str), format="%Y%m%d", errors="coerce"
    )
    out = out.dropna(subset=["tourney_date"])
    out = out.sort_values("tourney_date").reset_index(drop=True)
    return out
