// Breakpoint Analytics - Frontend JavaScript

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
        
        // Update last updated timestamp (if element exists)
        const lastUpdatedEl = document.getElementById('last-updated');
        if (lastUpdatedEl) {
            lastUpdatedEl.textContent = 
                new Date(playersData.last_updated).toLocaleString();
        }
        
        // Populate player selectors
        populatePlayerSelectors();
        
        showLoading(false);
    } catch (error) {
        showError('Failed to load data: ' + error.message);
        showLoading(false);
    }
}

// Store sorted players list
let sortedPlayers = [];
let allPlayers = []; // Store all players for lookup

// Populate player selectors
function populatePlayerSelectors() {
    // Sort players alphabetically
    sortedPlayers = [...playersData.players].sort((a, b) => 
        a.name.localeCompare(b.name)
    );
    allPlayers = [...sortedPlayers];
    
    // Setup typeahead inputs
    setupTypeahead('player-a-input', 'player-a', 'dropdown-a', 'clear-btn-a');
    setupTypeahead('player-b-input', 'player-b', 'dropdown-b', 'clear-btn-b');
}

// Setup typeahead search component
function setupTypeahead(inputId, hiddenInputId, dropdownId, clearBtnId) {
    const input = document.getElementById(inputId);
    const hiddenInput = document.getElementById(hiddenInputId);
    const dropdown = document.getElementById(dropdownId);
    const clearBtn = document.getElementById(clearBtnId);
    
    let selectedIndex = -1;
    let filteredPlayers = [];
    let selectedPlayer = null;
    
    // Get player initials for avatar
    function getInitials(name) {
        const parts = name.split(' ');
        if (parts.length >= 2) {
            return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
        }
        return name.substring(0, 2).toUpperCase();
    }
    
    // Highlight matching text
    function highlightMatch(text, query) {
        if (!query) return text;
        const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        return text.replace(regex, '<span class="highlight">$1</span>');
    }
    
    // Filter players based on search query
    function filterPlayers(query) {
        if (!query || query.length < 1) {
            return [];
        }
        
        const lowerQuery = query.toLowerCase();
        return allPlayers
            .filter(player => 
                player.name.toLowerCase().includes(lowerQuery)
            )
            .slice(0, 10); // Show up to 10 results (5+ visible, rest scrollable)
    }
    
    // Render dropdown items
    function renderDropdown(players, query) {
        dropdown.innerHTML = '';
        selectedIndex = -1;
        
        if (players.length === 0) {
            dropdown.innerHTML = '<div class="typeahead-empty">No players found</div>';
            dropdown.classList.add('show');
            return;
        }
        
        players.forEach((player, index) => {
            const item = document.createElement('div');
            item.className = 'typeahead-item';
            item.dataset.index = index;
            item.dataset.playerId = player.id;
            
            const initials = getInitials(player.name);
            const highlightedName = highlightMatch(player.name, query);
            const rank = player.current_rank || 'N/A';
            
            item.innerHTML = `
                <div class="typeahead-avatar">${initials}</div>
                <div class="typeahead-content">
                    <div class="typeahead-name">${highlightedName}</div>
                    <div class="typeahead-meta">Rank: ${rank}</div>
                </div>
            `;
            
            item.addEventListener('click', () => selectPlayer(player, index));
            item.addEventListener('mouseenter', () => {
                setActiveIndex(index);
            });
            
            dropdown.appendChild(item);
        });
        
        dropdown.classList.add('show');
    }
    
    // Set active index (for keyboard navigation)
    function setActiveIndex(index) {
        const items = dropdown.querySelectorAll('.typeahead-item');
        items.forEach((item, i) => {
            if (i === index) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
        selectedIndex = index;
    }
    
    // Select a player
    function selectPlayer(player, index) {
        selectedPlayer = player;
        input.value = player.name;
        hiddenInput.value = player.id;
        dropdown.classList.remove('show');
        updateClearButton();
        updateCompareButton();
    }
    
    // Update clear button visibility
    function updateClearButton() {
        if (input.value.trim() !== '') {
            clearBtn.classList.remove('hidden');
        } else {
            clearBtn.classList.add('hidden');
        }
    }
    
    // Handle input typing
    input.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        filteredPlayers = filterPlayers(query);
        renderDropdown(filteredPlayers, query);
        updateClearButton();
        
        // Clear selection if input changed
        if (!query) {
            selectedPlayer = null;
            hiddenInput.value = '';
            updateCompareButton();
        }
    });
    
    // Handle keyboard navigation
    input.addEventListener('keydown', (e) => {
        if (!dropdown.classList.contains('show')) return;
        
        const items = dropdown.querySelectorAll('.typeahead-item');
        if (items.length === 0) return;
        
        switch(e.key) {
            case 'ArrowDown':
                e.preventDefault();
                selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
                setActiveIndex(selectedIndex);
                items[selectedIndex].scrollIntoView({ block: 'nearest' });
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                selectedIndex = Math.max(selectedIndex - 1, -1);
                if (selectedIndex >= 0) {
                    setActiveIndex(selectedIndex);
                    items[selectedIndex].scrollIntoView({ block: 'nearest' });
                } else {
                    items.forEach(item => item.classList.remove('active'));
                }
                break;
                
            case 'Enter':
                e.preventDefault();
                if (selectedIndex >= 0 && filteredPlayers[selectedIndex]) {
                    selectPlayer(filteredPlayers[selectedIndex], selectedIndex);
                }
                break;
                
            case 'Escape':
                dropdown.classList.remove('show');
                input.blur();
                break;
        }
    });
    
    // Handle focus
    input.addEventListener('focus', () => {
        const query = input.value.trim();
        if (query) {
            filteredPlayers = filterPlayers(query);
            renderDropdown(filteredPlayers, query);
        }
    });
    
    // Handle blur (with delay to allow clicks)
    input.addEventListener('blur', (e) => {
        setTimeout(() => {
            dropdown.classList.remove('show');
            
            // Validate selection
            const query = input.value.trim();
            if (query && !selectedPlayer) {
                // Check if exact match exists
                const exactMatch = allPlayers.find(p => 
                    p.name.toLowerCase() === query.toLowerCase()
                );
                if (exactMatch) {
                    selectPlayer(exactMatch, -1);
                } else {
                    // Clear invalid input
                    input.value = '';
                    hiddenInput.value = '';
                    selectedPlayer = null;
                    updateClearButton();
                    updateCompareButton();
                }
            }
        }, 200);
    });
    
    // Clear button handler
    clearBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        input.value = '';
        hiddenInput.value = '';
        selectedPlayer = null;
        dropdown.classList.remove('show');
        updateClearButton();
        updateCompareButton();
        input.focus();
    });
    
    // Initialize clear button state
    updateClearButton();
}

// Setup event listeners
function setupEventListeners() {
    const compareBtn = document.getElementById('compare-btn');
    
    // Compare button click
    compareBtn.addEventListener('click', () => {
        const playerAId = document.getElementById('player-a').value;
        const playerBId = document.getElementById('player-b').value;
        comparePlayers(playerAId, playerBId);
    });
}

// Update compare button state
function updateCompareButton() {
    const playerAId = document.getElementById('player-a').value;
    const playerBId = document.getElementById('player-b').value;
    const compareBtn = document.getElementById('compare-btn');
    
    const bothSelected = playerAId && playerBId && playerAId !== playerBId;
    compareBtn.disabled = !bothSelected;
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

// Helper function to safely set text content
function safeSetText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

// Helper function to safely set style
function safeSetStyle(id, property, value) {
    const el = document.getElementById(id);
    if (el) el.style[property] = value;
}

// Format metric value based on type
function formatMetricValue(value, metricType) {
    if (value === null || value === undefined || value === '') {
        return 'N/A';
    }
    
    switch(metricType) {
        case 'percentage':
            return (value * 100).toFixed(1) + '%';
        case 'integer':
            return Math.round(value).toString();
        case 'decimal':
            return value.toFixed(2);
        case 'decimal_percent':
            return value.toFixed(1) + '%';  // For values already in percentage form (0-100)
        case 'surface':
            return value || 'N/A';
        case 'minutes':
            return Math.round(value).toString() + ' min';
        case 'age':
            return value.toFixed(1);
        default:
            return value.toString();
    }
}

// Compare two metric values and determine advantage
function compareMetrics(valueA, valueB, higherIsBetter = true) {
    if (valueA === null || valueA === undefined || valueA === '') {
        return { advantage: 'b', diff: null };
    }
    if (valueB === null || valueB === undefined || valueB === '') {
        return { advantage: 'a', diff: null };
    }
    
    const diff = valueA - valueB;
    if (Math.abs(diff) < 0.01) { // Essentially equal
        return { advantage: 'tie', diff: 0 };
    }
    
    if (higherIsBetter) {
        return diff > 0 ? { advantage: 'a', diff } : { advantage: 'b', diff: -diff };
    } else {
        return diff < 0 ? { advantage: 'a', diff: -diff } : { advantage: 'b', diff };
    }
}

// Display detailed metrics comparison
function displayDetailedMetrics(playerA, playerB) {
    const metricsA = playerA.detailed_metrics || {};
    const metricsB = playerB.detailed_metrics || {};
    
    // Set player names
    safeSetText('metrics-name-a', playerA.name);
    safeSetText('metrics-name-b', playerB.name);
    
    // Helper function to display a metric row
    function displayMetricRow(metricKey, labelA, labelB, labelAdvantage, 
                              valueA, valueB, formatType, higherIsBetter = true) {
        const comparison = compareMetrics(valueA, valueB, higherIsBetter);
        const formattedA = formatMetricValue(valueA, formatType);
        const formattedB = formatMetricValue(valueB, formatType);
        
        safeSetText(labelA, formattedA);
        safeSetText(labelB, formattedB);
        
        let advantageText = '--';
        let advantageClass = '';
        if (comparison.advantage === 'a') {
            advantageText = 'A';
            advantageClass = 'player-a';
        } else if (comparison.advantage === 'b') {
            advantageText = 'B';
            advantageClass = 'player-b';
        } else if (comparison.advantage === 'tie') {
            advantageText = '—';
            advantageClass = 'tie';
        }
        
        const advantageEl = document.getElementById(labelAdvantage);
        if (advantageEl) {
            advantageEl.textContent = advantageText;
            advantageEl.className = 'metric-advantage ' + advantageClass;
        }
    }
    
    // Display each metric
    displayMetricRow('avg_winning_margin', 
        'metric-avg-winning-margin-a', 'metric-avg-winning-margin-b', 'advantage-avg-winning-margin',
        metricsA.avg_winning_margin, metricsB.avg_winning_margin, 'decimal', true);
    
    displayMetricRow('first_set_win_pct',
        'metric-first-set-win-pct-a', 'metric-first-set-win-pct-b', 'advantage-first-set-win-pct',
        metricsA.first_set_win_pct, metricsB.first_set_win_pct, 'percentage', true);
    
    displayMetricRow('second_set_win_pct',
        'metric-second-set-win-pct-a', 'metric-second-set-win-pct-b', 'advantage-second-set-win-pct',
        metricsA.second_set_win_pct, metricsB.second_set_win_pct, 'percentage', true);
    
    // ace_pct is already a percentage (0-100), not a decimal (0-1)
    displayMetricRow('ace_pct',
        'metric-ace-pct-a', 'metric-ace-pct-b', 'advantage-ace-pct',
        metricsA.ace_pct, metricsB.ace_pct, 'decimal_percent', true);
    
    displayMetricRow('avg_minutes_for_wins',
        'metric-avg-minutes-wins-a', 'metric-avg-minutes-wins-b', 'advantage-avg-minutes-wins',
        metricsA.avg_minutes_for_wins, metricsB.avg_minutes_for_wins, 'minutes', false);
    
    displayMetricRow('avg_losing_game_time',
        'metric-avg-losing-game-time-a', 'metric-avg-losing-game-time-b', 'advantage-avg-losing-game-time',
        metricsA.avg_losing_game_time, metricsB.avg_losing_game_time, 'minutes', false);
    
    displayMetricRow('avg_opponent_age_when_won',
        'metric-avg-opp-age-won-a', 'metric-avg-opp-age-won-b', 'advantage-avg-opp-age-won',
        metricsA.avg_opponent_age_when_won, metricsB.avg_opponent_age_when_won, 'age', false);
    
    displayMetricRow('avg_opponent_age_when_lost',
        'metric-avg-opp-age-lost-a', 'metric-avg-opp-age-lost-b', 'advantage-avg-opp-age-lost',
        metricsA.avg_opponent_age_when_lost, metricsB.avg_opponent_age_when_lost, 'age', false);
    
    displayMetricRow('form_last_10_wins',
        'metric-form-10-a', 'metric-form-10-b', 'advantage-form-10',
        metricsA.form_last_10_wins, metricsB.form_last_10_wins, 'decimal', true);
    
    displayMetricRow('form_last_5_wins',
        'metric-form-5-a', 'metric-form-5-b', 'advantage-form-5',
        metricsA.form_last_5_wins, metricsB.form_last_5_wins, 'decimal', true);
    
    // Most lost surface - special handling (string comparison)
    const surfaceA = metricsA.most_lost_surface || 'N/A';
    const surfaceB = metricsB.most_lost_surface || 'N/A';
    safeSetText('metric-most-lost-surface-a', surfaceA);
    safeSetText('metric-most-lost-surface-b', surfaceB);
    const surfaceAdvantageEl = document.getElementById('advantage-most-lost-surface');
    if (surfaceAdvantageEl) {
        if (surfaceA === 'N/A' && surfaceB === 'N/A') {
            surfaceAdvantageEl.textContent = '—';
            surfaceAdvantageEl.className = 'metric-advantage tie';
        } else if (surfaceA === 'N/A') {
            surfaceAdvantageEl.textContent = 'B';
            surfaceAdvantageEl.className = 'metric-advantage player-b';
        } else if (surfaceB === 'N/A') {
            surfaceAdvantageEl.textContent = 'A';
            surfaceAdvantageEl.className = 'metric-advantage player-a';
        } else {
            // Lower is better (fewer losses on a surface is better)
            // This is a simplified comparison - in reality, we'd need to compare actual loss rates
            surfaceAdvantageEl.textContent = '—';
            surfaceAdvantageEl.className = 'metric-advantage tie';
        }
    }
}

// Display results
function displayResults(stats, playerAId, playerBId) {
    const resultsSection = document.getElementById('results-section');
    if (!resultsSection) {
        console.error('Results section not found');
        return;
    }
    resultsSection.classList.remove('hidden');
    
    const playerA = stats.player_a;
    const playerB = stats.player_b;
    
    // Predicted Edge
    const probA = stats.win_probability.player_a * 100;
    const probB = stats.win_probability.player_b * 100;
    
    safeSetText('prob-text-a', probA.toFixed(1) + '%');
    safeSetText('prob-text-b', probB.toFixed(1) + '%');
    
    // Update probability bar
    safeSetStyle('prob-bar-a', 'width', probA + '%');
    safeSetStyle('prob-bar-b', 'width', probB + '%');
    
    // Confidence
    const confidenceValue = stats.win_probability.confidence === 'high' ? 99 : 
                           stats.win_probability.confidence === 'medium' ? 75 : 50;
    safeSetText('confidence-value', confidenceValue);
    
    // Vital Stats
    safeSetText('vital-name-a', playerA.name);
    safeSetText('vital-name-b', playerB.name);
    safeSetText('rank-a', playerA.current_rank || '--');
    safeSetText('rank-b', playerB.current_rank || '--');
    safeSetText('elo-a', Math.round(playerA.current_elo) || '--');
    safeSetText('elo-b', Math.round(playerB.current_elo) || '--');
    
    // Surface Win Rate
    safeSetText('surface-name-a-compact', playerA.name);
    safeSetText('surface-name-b-compact', playerB.name);
    safeSetText('surface-hard-a-compact', formatSurfaceStat(stats.surface_stats.hard.player_a));
    safeSetText('surface-hard-b-compact', formatSurfaceStat(stats.surface_stats.hard.player_b));
    safeSetText('surface-clay-a-compact', formatSurfaceStat(stats.surface_stats.clay.player_a));
    safeSetText('surface-clay-b-compact', formatSurfaceStat(stats.surface_stats.clay.player_b));
    safeSetText('surface-grass-a-compact', formatSurfaceStat(stats.surface_stats.grass.player_a));
    safeSetText('surface-grass-b-compact', formatSurfaceStat(stats.surface_stats.grass.player_b));
    
    // Recent Form - Generate dots
    safeSetText('form-name-a', playerA.name);
    safeSetText('form-name-b', playerB.name);
    renderFormDots('form-dots-a', stats.form.player_a.last_10_win_pct);
    renderFormDots('form-dots-b', stats.form.player_b.last_10_win_pct);
    
    // Surface Win Rate - Show combined win rate (for now showing N/A)
    safeSetText('surface-name-a-compact', playerA.name);
    safeSetText('surface-name-b-compact', playerB.name);
    safeSetText('surface-win-rate-a-compact', 'N/A');
    safeSetText('surface-win-rate-b-compact', 'N/A');
    
    // Detailed Metrics
    displayDetailedMetrics(playerA, playerB);
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Format surface stat
function formatSurfaceStat(value) {
    if (value === null || value === undefined) return 'N/A';
    return (value * 100).toFixed(0) + '%';
}

// Render form dots (green for wins, red for losses)
function renderFormDots(containerId, winPct) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = '';
    
    // Always show exactly 10 dots
    if (winPct === null || winPct === undefined) {
        // Show placeholder dots (grey)
        for (let i = 0; i < 10; i++) {
            const dot = document.createElement('div');
            dot.className = 'form-dot placeholder';
            container.appendChild(dot);
        }
        return;
    }
    
    // Generate win/loss pattern based on win percentage
    const wins = Math.round(winPct * 10);
    const losses = 10 - wins;
    
    // Create win dots (green)
    for (let i = 0; i < wins; i++) {
        const dot = document.createElement('div');
        dot.className = 'form-dot win';
        container.appendChild(dot);
    }
    
    // Create loss dots (red)
    for (let i = 0; i < losses; i++) {
        const dot = document.createElement('div');
        dot.className = 'form-dot loss';
        container.appendChild(dot);
    }
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
