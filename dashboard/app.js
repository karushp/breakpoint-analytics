// Tennis Analytics Dashboard - Frontend JavaScript

let playersData = null;
let rankingsData = null;
let eloChart = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadInitialData();
    setupEventListeners();
});

// Load initial data
async function loadInitialData() {
    try {
        showLoading(true);
        
        // Determine base path (works for both local and GitHub Pages)
        const basePath = window.location.pathname.includes('/dashboard/') 
            ? '../outputs/' 
            : 'outputs/';
        
        // Load player summary
        const playersResponse = await fetch(`${basePath}player_summary.json`);
        if (!playersResponse.ok) throw new Error('Failed to load player data');
        playersData = await playersResponse.json();
        
        // Load rankings
        const rankingsResponse = await fetch(`${basePath}elo_rankings.json`);
        if (rankingsResponse.ok) {
            rankingsData = await rankingsResponse.json();
        }
        
        // Update last updated timestamp
        document.getElementById('last-updated').textContent = 
            new Date(playersData.last_updated).toLocaleString();
        
        // Populate player selectors
        populatePlayerSelectors();
        
        showLoading(false);
    } catch (error) {
        showError('Failed to load data: ' + error.message);
        showLoading(false);
    }
}

// Populate player selectors
function populatePlayerSelectors() {
    const selectA = document.getElementById('player-a');
    const selectB = document.getElementById('player-b');
    
    // Sort players alphabetically
    const sortedPlayers = [...playersData.players].sort((a, b) => 
        a.name.localeCompare(b.name)
    );
    
    sortedPlayers.forEach(player => {
        const optionA = document.createElement('option');
        optionA.value = player.id;
        optionA.textContent = player.name;
        selectA.appendChild(optionA);
        
        const optionB = document.createElement('option');
        optionB.value = player.id;
        optionB.textContent = player.name;
        selectB.appendChild(optionB);
    });
}

// Setup event listeners
function setupEventListeners() {
    const selectA = document.getElementById('player-a');
    const selectB = document.getElementById('player-b');
    const compareBtn = document.getElementById('compare-btn');
    
    // Enable compare button when both players selected
    [selectA, selectB].forEach(select => {
        select.addEventListener('change', () => {
            const bothSelected = selectA.value && selectB.value && selectA.value !== selectB.value;
            compareBtn.disabled = !bothSelected;
        });
    });
    
    // Compare button click
    compareBtn.addEventListener('click', () => {
        comparePlayers(selectA.value, selectB.value);
    });
}

// Compare two players
async function comparePlayers(playerAId, playerBId) {
    if (!playerAId || !playerBId || playerAId === playerBId) {
        showError('Please select two different players');
        return;
    }
    
    try {
        showLoading(true);
        
        // For MVP, we'll generate matchup stats client-side
        // In production, this would be an API call
        const matchupStats = await generateMatchupStats(playerAId, playerBId);
        
        displayResults(matchupStats, playerAId, playerBId);
        
        showLoading(false);
    } catch (error) {
        showError('Failed to compare players: ' + error.message);
        showLoading(false);
    }
}

// Generate matchup stats (simplified - would normally come from API)
async function generateMatchupStats(playerAId, playerBId) {
    // This is a placeholder - in production, you'd call an API endpoint
    // For now, we'll use the player summary data to create basic stats
    
    const playerA = playersData.players.find(p => p.id === playerAId);
    const playerB = playersData.players.find(p => p.id === playerBId);
    
    if (!playerA || !playerB) {
        throw new Error('Player not found');
    }
    
    // Calculate win probability from Elo
    const eloDiff = playerA.current_elo - playerB.current_elo;
    const playerAProb = 1 / (1 + Math.pow(10, -eloDiff / 400));
    const playerBProb = 1 - playerAProb;
    
    // Determine confidence
    let confidence = 'low';
    if (Math.abs(eloDiff) > 200) confidence = 'high';
    else if (Math.abs(eloDiff) > 100) confidence = 'medium';
    
    return {
        player_a_id: playerAId,
        player_b_id: playerBId,
        win_probability: {
            player_a: playerAProb,
            player_b: playerBProb,
            confidence: confidence,
            method: 'elo_global'
        },
        head_to_head: {
            total_matches: 0,
            player_a_wins: 0,
            player_b_wins: 0,
            last_5: []
        },
        form: {
            player_a: {
                last_10_win_pct: null,
                recent_opponent_avg_elo: null
            },
            player_b: {
                last_10_win_pct: null,
                recent_opponent_avg_elo: null
            }
        },
        surface_stats: {
            hard: { player_a: null, player_b: null },
            clay: { player_a: null, player_b: null },
            grass: { player_a: null, player_b: null }
        },
        elo_trends: {
            player_a: [],
            player_b: []
        },
        player_a: playerA,
        player_b: playerB
    };
}

// Display results
function displayResults(stats, playerAId, playerBId) {
    const resultsSection = document.getElementById('results-section');
    resultsSection.classList.remove('hidden');
    
    const playerA = stats.player_a;
    const playerB = stats.player_b;
    
    // Win Probability
    document.getElementById('name-player-a').textContent = playerA.name;
    document.getElementById('name-player-b').textContent = playerB.name;
    document.getElementById('prob-value-a').textContent = 
        (stats.win_probability.player_a * 100).toFixed(1) + '%';
    document.getElementById('prob-value-b').textContent = 
        (stats.win_probability.player_b * 100).toFixed(1) + '%';
    document.getElementById('confidence-badge').textContent = 
        `Confidence: ${stats.win_probability.confidence}`;
    
    // Head-to-Head
    document.getElementById('h2h-total').textContent = stats.head_to_head.total_matches || '0';
    document.getElementById('h2h-wins-a').textContent = stats.head_to_head.player_a_wins || '0';
    document.getElementById('h2h-wins-b').textContent = stats.head_to_head.player_b_wins || '0';
    document.getElementById('h2h-label-a').textContent = `${playerA.name} Wins`;
    document.getElementById('h2h-label-b').textContent = `${playerB.name} Wins`;
    
    // Form
    document.getElementById('form-name-a').textContent = playerA.name;
    document.getElementById('form-name-b').textContent = playerB.name;
    document.getElementById('form-win-pct-a').textContent = 
        stats.form.player_a.last_10_win_pct ? 
        (stats.form.player_a.last_10_win_pct * 100).toFixed(1) + '%' : 'N/A';
    document.getElementById('form-win-pct-b').textContent = 
        stats.form.player_b.last_10_win_pct ? 
        (stats.form.player_b.last_10_win_pct * 100).toFixed(1) + '%' : 'N/A';
    
    // Surface Stats
    document.getElementById('surface-name-a').textContent = playerA.name;
    document.getElementById('surface-name-b').textContent = playerB.name;
    document.getElementById('surface-hard-a').textContent = 
        formatSurfaceStat(stats.surface_stats.hard.player_a);
    document.getElementById('surface-hard-b').textContent = 
        formatSurfaceStat(stats.surface_stats.hard.player_b);
    document.getElementById('surface-clay-a').textContent = 
        formatSurfaceStat(stats.surface_stats.clay.player_a);
    document.getElementById('surface-clay-b').textContent = 
        formatSurfaceStat(stats.surface_stats.clay.player_b);
    document.getElementById('surface-grass-a').textContent = 
        formatSurfaceStat(stats.surface_stats.grass.player_a);
    document.getElementById('surface-grass-b').textContent = 
        formatSurfaceStat(stats.surface_stats.grass.player_b);
    
    // Rankings & Elo
    document.getElementById('rank-a').textContent = playerA.current_rank || 'N/A';
    document.getElementById('rank-b').textContent = playerB.current_rank || 'N/A';
    document.getElementById('elo-a').textContent = Math.round(playerA.current_elo);
    document.getElementById('elo-b').textContent = Math.round(playerB.current_elo);
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Format surface stat
function formatSurfaceStat(value) {
    if (value === null || value === undefined) return 'N/A';
    return (value * 100).toFixed(1) + '%';
}

// Show/hide loading
function showLoading(show) {
    const loading = document.getElementById('loading');
    if (show) {
        loading.classList.remove('hidden');
    } else {
        loading.classList.add('hidden');
    }
}

// Show error
function showError(message) {
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = message;
    errorDiv.classList.remove('hidden');
    setTimeout(() => {
        errorDiv.classList.add('hidden');
    }, 5000);
}
