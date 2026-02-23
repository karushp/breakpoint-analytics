/**
 * Breakpoint Analytics – Dashboard
 * Single-page app: player autocomplete, compare two players, show win probability and scorecard.
 * Depends on: config.js (window.BREAKPOINT_API_BASE)
 */
(function () {
  "use strict";

  // ---------------------------------------------------------------------------
  // Constants
  // ---------------------------------------------------------------------------
  const API_BASE = (window.BREAKPOINT_API_BASE || "").replace(/\/$/, "");
  const SUGGESTIONS_MAX = 50;
  const SUGGESTIONS_BLUR_MS = 150;
  const SCORECARD_DEFINITIONS = [
    { key: "elo", metric: "ELO", format: "elo", higherIsBetter: true },
    { key: "rolling_win_pct", metric: "Form (win % last 10)", format: "pct", higherIsBetter: true },
    { key: "last3_win_avg", metric: "Win % (last 3)", format: "pct", higherIsBetter: true },
    { key: "surface_win_pct", metric: "Surface win %", format: "pct", higherIsBetter: true },
    { key: "rolling_ace_avg", metric: "Aces (avg per match)", format: "one", higherIsBetter: true },
    { key: "rolling_minutes_avg", metric: "Minutes (avg per match)", format: "one", higherIsBetter: true },
    { key: "rolling_bp_save", metric: "Break points saved %", format: "pct", higherIsBetter: true },
  ];

  // ---------------------------------------------------------------------------
  // DOM references (single place for maintainability)
  // ---------------------------------------------------------------------------
  const dom = {
    player1Input: document.getElementById("player-1"),
    player2Input: document.getElementById("player-2"),
    suggestions1: document.getElementById("suggestions-1"),
    suggestions2: document.getElementById("suggestions-2"),
    generateBtn: document.getElementById("generate-btn"),
    resultSection: document.getElementById("result"),
    message: document.getElementById("message"),
    comparisonView: document.getElementById("comparison-view"),
    last5Name1: document.getElementById("last5-name-1"),
    last5Name2: document.getElementById("last5-name-2"),
    last5Icons1: document.getElementById("last5-icons-1"),
    last5Icons2: document.getElementById("last5-icons-2"),
    barLeft: document.getElementById("bar-left"),
    barRight: document.getElementById("bar-right"),
    barPct1: document.getElementById("bar-pct-1"),
    barPct2: document.getElementById("bar-pct-2"),
    scorecardTable: document.getElementById("scorecard-table"),
  };

  // ---------------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------------
  let playersList = [];

  // ---------------------------------------------------------------------------
  // Utils
  // ---------------------------------------------------------------------------
  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  const formatters = {
    elo: (v) => (v == null ? "—" : String(Math.round(v))),
    pct: (v) => (v == null ? "—" : Math.round(v * 100) + "%"),
    one: (v) => (v == null ? "—" : Number(v).toFixed(1)),
  };

  // ---------------------------------------------------------------------------
  // Autocomplete
  // ---------------------------------------------------------------------------
  function filterPlayers(query) {
    const lower = query.trim().toLowerCase();
    if (!lower) return playersList.slice(0, SUGGESTIONS_MAX);
    return playersList
      .filter((p) => p.toLowerCase().includes(lower))
      .slice(0, SUGGESTIONS_MAX);
  }

  function showSuggestions(input, listEl) {
    const matches = filterPlayers(input.value.trim());
    listEl.innerHTML = "";
    listEl.setAttribute("aria-hidden", "false");
    matches.forEach((name) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = name;
      btn.role = "option";
      btn.addEventListener("click", () => {
        input.value = name;
        listEl.innerHTML = "";
        listEl.setAttribute("aria-hidden", "true");
        input.focus();
      });
      listEl.appendChild(btn);
    });
    if (matches.length === 0) listEl.setAttribute("aria-hidden", "true");
  }

  function hideSuggestions(listEl) {
    listEl.innerHTML = "";
    listEl.setAttribute("aria-hidden", "true");
  }

  function setupPlayerSearch(input, listEl) {
    input.addEventListener("input", () => showSuggestions(input, listEl));
    input.addEventListener("focus", () => showSuggestions(input, listEl));
    input.addEventListener("blur", () => {
      setTimeout(() => hideSuggestions(listEl), SUGGESTIONS_BLUR_MS);
    });
  }

  // ---------------------------------------------------------------------------
  // Comparison view: probability bar
  // ---------------------------------------------------------------------------
  function renderProbabilityBar(probA, probB) {
    dom.barLeft.style.flex = `${probA} 1 0`;
    dom.barRight.style.flex = `${probB} 1 0`;
    dom.barPct1.textContent = Math.round(probA * 100) + "%";
    dom.barPct2.textContent = Math.round(probB * 100) + "%";
    dom.barLeft.classList.remove("prob-higher", "prob-lower");
    dom.barRight.classList.remove("prob-higher", "prob-lower");
    if (probA >= probB) {
      dom.barLeft.classList.add("prob-higher");
      dom.barRight.classList.add("prob-lower");
    } else {
      dom.barLeft.classList.add("prob-lower");
      dom.barRight.classList.add("prob-higher");
    }
  }

  // ---------------------------------------------------------------------------
  // Comparison view: last 5 match results (array of 1=win, 0=loss, null=no data; index 0 = most recent)
  // ---------------------------------------------------------------------------
  function renderLast5Icons(container, resultsArray) {
    container.innerHTML = "";
    container.setAttribute("aria-hidden", "false");
    const arr = Array.isArray(resultsArray) ? resultsArray.slice(0, 5) : [];
    while (arr.length < 5) arr.push(null);
    arr.forEach((result, i) => {
      const el = document.createElement("span");
      if (result === 1) {
        el.className = "icon win";
        el.setAttribute("aria-label", "Win");
      } else if (result === 0) {
        el.className = "icon loss";
        el.setAttribute("aria-label", "Loss");
      } else {
        el.className = "icon last5-unknown";
        el.setAttribute("aria-label", "No data");
      }
      container.appendChild(el);
    });
  }

  // ---------------------------------------------------------------------------
  // Comparison view: scorecard
  // ---------------------------------------------------------------------------
  function buildScorecardRows(statsA, statsB) {
    const stats1 = statsA || {};
    const stats2 = statsB || {};
    return SCORECARD_DEFINITIONS.map((def) => {
      const leftVal = stats1[def.key];
      const rightVal = stats2[def.key];
      const leftNum = leftVal != null ? Number(leftVal) : null;
      const rightNum = rightVal != null ? Number(rightVal) : null;
      const leftDisplay = formatters[def.format](leftVal);
      const rightDisplay = formatters[def.format](rightVal);
      const sum = (leftNum != null ? leftNum : 0) + (rightNum != null ? rightNum : 0);
      const leftPct = sum === 0 ? 50 : ((leftNum != null ? leftNum : 0) / sum) * 100;
      const rightPct = sum === 0 ? 50 : ((rightNum != null ? rightNum : 0) / sum) * 100;
      const tied = leftNum === rightNum;
      const leftBetter =
        leftNum != null && rightNum != null && !tied && (def.higherIsBetter ? leftNum >= rightNum : leftNum <= rightNum);
      const rightBetter =
        leftNum != null && rightNum != null && !tied && (def.higherIsBetter ? rightNum >= leftNum : rightNum <= leftNum);
      return {
        metric: def.metric,
        leftDisplay,
        rightDisplay,
        leftPct,
        rightPct,
        leftBetter,
        rightBetter,
      };
    });
  }

  function renderScorecard(rows, statsA, statsB) {
    const hasStats =
      statsA && statsB &&
      (statsA.elo != null || statsB.elo != null || statsA.rolling_win_pct != null || statsB.rolling_win_pct != null);
    dom.scorecardTable.innerHTML = "";
    if (!hasStats && rows.length > 0) {
      const hint = document.createElement("p");
      hint.className = "scorecard-hint";
      hint.textContent = "Scorecard metrics will appear after the API is updated. Redeploy the backend on Render to get the latest /predict response.";
      dom.scorecardTable.appendChild(hint);
    }
    rows.forEach((row) => {
      const tr = document.createElement("div");
      tr.className = "scorecard-row";
      tr.innerHTML = `
        <div class="metric-name">${escapeHtml(row.metric)}</div>
        <div class="scorecard-bar-row">
          <span class="value-left">${escapeHtml(row.leftDisplay)}</span>
          <div class="metric-bar">
            <span class="segment ${row.leftBetter ? "better" : "neutral"}" style="flex: 0 0 ${row.leftPct}%"></span>
            <span class="segment ${row.rightBetter ? "better" : "neutral"}" style="flex: 0 0 ${row.rightPct}%"></span>
          </div>
          <span class="value-right">${escapeHtml(row.rightDisplay)}</span>
        </div>
      `;
      dom.scorecardTable.appendChild(tr);
    });
  }

  function renderComparisonView(playerA, playerB, data) {
    const { prob_a_wins: probA, prob_b_wins: probB, stats_a: statsA, stats_b: statsB, last5_a: last5A, last5_b: last5B } = data;

    dom.last5Name1.textContent = playerA;
    dom.last5Name2.textContent = playerB;
    renderLast5Icons(dom.last5Icons1, last5A);
    renderLast5Icons(dom.last5Icons2, last5B);

    renderProbabilityBar(probA, probB);
    const scorecardRows = buildScorecardRows(statsA, statsB);
    renderScorecard(scorecardRows, statsA, statsB);
  }

  // ---------------------------------------------------------------------------
  // UI helpers
  // ---------------------------------------------------------------------------
  function showMessage(text, showComparisonPanel = false) {
    dom.message.textContent = text;
    dom.resultSection.hidden = false;
    dom.comparisonView.hidden = !showComparisonPanel;
  }

  function showComparison(data) {
    dom.message.textContent = "";
    dom.comparisonView.hidden = false;
    renderComparisonView(
      dom.player1Input.value.trim(),
      dom.player2Input.value.trim(),
      data
    );
  }

  // ---------------------------------------------------------------------------
  // API
  // ---------------------------------------------------------------------------
  async function loadPlayers() {
    try {
      const res = await fetch(`${API_BASE}/players`);
      if (!res.ok) throw new Error("Failed to load players");
      const data = await res.json();
      playersList = (data.players || []).slice().sort();
      setupPlayerSearch(dom.player1Input, dom.suggestions1);
      setupPlayerSearch(dom.player2Input, dom.suggestions2);
    } catch (e) {
      showMessage("Could not load player list. Check API URL in js/config.js.");
      console.error("loadPlayers", e);
    }
  }

  async function generateComparison() {
    const a = dom.player1Input.value.trim();
    const b = dom.player2Input.value.trim();

    if (!a || !b) {
      showMessage("Please select both players.");
      return;
    }
    if (a === b) {
      showMessage("Please select two different players.");
      return;
    }

    dom.generateBtn.disabled = true;
    showMessage("Loading…", false);
    dom.resultSection.hidden = false;
    dom.comparisonView.hidden = true;

    try {
      const res = await fetch(`${API_BASE}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ player_a: a, player_b: b, surface: "Hard" }),
      });
      const data = await res.json();

      if (!res.ok) {
        showMessage(data.detail || "Request failed.");
        return;
      }
      showComparison(data);
    } catch (e) {
      showMessage("Request failed. Is the API running and CORS set for this origin?");
      console.error("generateComparison", e);
    } finally {
      dom.generateBtn.disabled = false;
    }
  }

  // ---------------------------------------------------------------------------
  // Init
  // ---------------------------------------------------------------------------
  dom.generateBtn.addEventListener("click", generateComparison);
  loadPlayers();
})();
