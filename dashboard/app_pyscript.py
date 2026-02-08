"""
Tennis Analytics Dashboard - PyScript Version
This runs Python directly in the browser!
"""
from pyscript import document, window
import json
from datetime import datetime

# Global state
players_data = None
rankings_data = None

def load_initial_data():
    """Load player data from JSON files."""
    global players_data, rankings_data
    
    try:
        show_loading(True)
        
        # Determine base path
        base_path = "../outputs/" if "/dashboard/" in window.location.pathname else "outputs/"
        
        # Load player summary
        # Note: In PyScript, we'd use fetch API through js module
        # For now, this is a template showing the Python approach
        
        show_loading(False)
    except Exception as e:
        show_error(f"Failed to load data: {e}")
        show_loading(False)

def populate_player_selectors():
    """Populate dropdown menus with players."""
    if not players_data:
        return
    
    select_a = document.querySelector("#player-a")
    select_b = document.querySelector("#player-b")
    
    # Sort players alphabetically
    sorted_players = sorted(players_data["players"], key=lambda p: p["name"])
    
    for player in sorted_players:
        # Create option elements
        option_a = document.createElement("option")
        option_a.value = player["id"]
        option_a.textContent = player["name"]
        select_a.appendChild(option_a)
        
        option_b = document.createElement("option")
        option_b.value = player["id"]
        option_b.textContent = player["name"]
        select_b.appendChild(option_b)

def compare_players(player_a_id, player_b_id):
    """Compare two players and display results."""
    if not player_a_id or not player_b_id or player_a_id == player_b_id:
        show_error("Please select two different players")
        return
    
    # Generate matchup stats (would call Python functions here)
    matchup_stats = generate_matchup_stats(player_a_id, player_b_id)
    display_results(matchup_stats, player_a_id, player_b_id)

def generate_matchup_stats(player_a_id, player_b_id):
    """Generate matchup statistics using Python."""
    player_a = next(p for p in players_data["players"] if p["id"] == player_a_id)
    player_b = next(p for p in players_data["players"] if p["id"] == player_b_id)
    
    # Calculate win probability from Elo (Python math!)
    elo_diff = player_a["current_elo"] - player_b["current_elo"]
    player_a_prob = 1 / (1 + 10 ** (-elo_diff / 400))
    player_b_prob = 1 - player_a_prob
    
    # Determine confidence
    confidence = "low"
    if abs(elo_diff) > 200:
        confidence = "high"
    elif abs(elo_diff) > 100:
        confidence = "medium"
    
    return {
        "player_a_id": player_a_id,
        "player_b_id": player_b_id,
        "win_probability": {
            "player_a": player_a_prob,
            "player_b": player_b_prob,
            "confidence": confidence
        },
        "player_a": player_a,
        "player_b": player_b
    }

def display_results(stats, player_a_id, player_b_id):
    """Display comparison results."""
    results_section = document.querySelector("#results-section")
    results_section.classList.remove("hidden")
    
    player_a = stats["player_a"]
    player_b = stats["player_b"]
    
    # Update win probability display
    document.querySelector("#name-player-a").textContent = player_a["name"]
    document.querySelector("#name-player-b").textContent = player_b["name"]
    document.querySelector("#prob-value-a").textContent = f"{stats['win_probability']['player_a'] * 100:.1f}%"
    document.querySelector("#prob-value-b").textContent = f"{stats['win_probability']['player_b'] * 100:.1f}%"
    
    # Scroll to results
    results_section.scrollIntoView({"behavior": "smooth"})

def show_loading(show):
    """Show/hide loading indicator."""
    loading = document.querySelector("#loading")
    if show:
        loading.classList.remove("hidden")
    else:
        loading.classList.add("hidden")

def show_error(message):
    """Display error message."""
    error_div = document.querySelector("#error")
    error_div.textContent = message
    error_div.classList.remove("hidden")
    window.setTimeout(lambda: error_div.classList.add("hidden"), 5000)

# Initialize on page load
if __name__ == "__main__":
    load_initial_data()
