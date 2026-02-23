(function () {
  const API_BASE = window.BREAKPOINT_API_BASE.replace(/\/$/, "");
  const playerA = document.getElementById("player-a");
  const playerB = document.getElementById("player-b");
  const surface = document.getElementById("surface");
  const result = document.getElementById("result");
  const message = document.getElementById("message");
  const probBlock = document.getElementById("probabilities");

  async function loadPlayers() {
    try {
      const res = await fetch(API_BASE + "/players");
      if (!res.ok) throw new Error("Failed to load players");
      const data = await res.json();
      const options = data.players.map(function (p) {
        const o = document.createElement("option");
        o.value = p;
        o.textContent = p;
        return o;
      });
      playerA.append.apply(playerA, options);
      playerB.append.apply(playerB, options);
    } catch (e) {
      message.textContent = "Could not load player list. Check API URL in js/config.js.";
      console.error(e);
    }
  }

  async function predict() {
    const a = playerA.value;
    const b = playerB.value;
    if (!a || !b || a === b) {
      message.textContent = "Select two different players.";
      probBlock.hidden = true;
      return;
    }
    message.textContent = "Loading…";
    probBlock.hidden = true;
    try {
      const res = await fetch(API_BASE + "/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          player_a: a,
          player_b: b,
          surface: surface.value,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        message.textContent = data.detail || "Request failed.";
        return;
      }
      message.textContent = "";
      probBlock.innerHTML =
        "<p><strong>" +
        escapeHtml(a) +
        "</strong> " +
        (data.prob_a_wins * 100).toFixed(1) +
        "% — <strong>" +
        escapeHtml(b) +
        "</strong> " +
        (data.prob_b_wins * 100).toFixed(1) +
        "%</p>";
      probBlock.hidden = false;
    } catch (e) {
      message.textContent = "Request failed. Is the API running and CORS set for this origin?";
      console.error(e);
    }
  }

  function escapeHtml(s) {
    const div = document.createElement("div");
    div.textContent = s;
    return div.innerHTML;
  }

  playerA.addEventListener("change", predict);
  playerB.addEventListener("change", predict);
  surface.addEventListener("change", predict);

  loadPlayers();
})();
