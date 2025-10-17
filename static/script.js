// ==== Identifiants simples (temporaire)
const VALID_USERNAME = "0";
const VALID_PASSWORD = "0";

// ==== Références globales
let tempChart = null;
let cycleChart = null;

// ==== Helpers
function hhmm(date = new Date()) {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatTime(sec) {
  sec = Math.max(0, Math.floor(sec));
  const m = String(Math.floor((sec % 3600) / 60)).padStart(2, "0");
  const s = String(sec % 60).padStart(2, "0");
  return `${m}:${s}`;
}

// ==== Connexion utilisateur
function loginUser(e) {
  e.preventDefault();
  const u = document.getElementById("username").value.trim();
  const p = document.getElementById("password").value.trim();
  const err = document.getElementById("error-msg");

  if (u === VALID_USERNAME && p === VALID_PASSWORD) {
    document.getElementById("loginBox").style.display = "none";
    const main = document.getElementById("dashboard");
    main.style.display = "flex";
    main.classList.remove("hidden");
    err.textContent = "";
    initCharts();
    startDashboard();
  } else {
    err.textContent = "Nom d’utilisateur ou mot de passe incorrect.";
    err.style.color = "red";
  }
  return false;
}

// ====================== INITIALISATION DES GRAPHIQUES ======================
function initCharts() {
  const ctx = document.getElementById("tempChart").getContext("2d");
  tempChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Température (°C)",
          data: [],
          borderColor: "#ffcc00",
          backgroundColor: "rgba(255,204,0,0.15)",
          borderWidth: 2,
          fill: true,
          tension: 0.4,
        },
      ],
    },
    options: {
      plugins: { legend: { display: true } },
      maintainAspectRatio: false,
      scales: {
        x: { ticks: { color: "#e4efff" } },
        y: {
          min: 0,
          suggestedMax: 70,
          ticks: { stepSize: 5, color: "#e4efff" },
        },
      },
    },
  });

  const ctx2 = document.getElementById("cycleChart").getContext("2d");
  cycleChart = new Chart(ctx2, {
    type: "doughnut",
    data: {
      labels: ["Progression", "Reste"],
      datasets: [
        { data: [0, 100], backgroundColor: ["#00ff00", "#1b355e"], borderWidth: 2 },
      ],
    },
    options: {
      animation: { duration: 800, easing: "easeInOutCubic" },
      cutout: "70%",
      plugins: { legend: { display: false } },
    },
  });
}

// ====================== MISE À JOUR DES DONNÉES ======================
function startDashboard() {
  updateData();
  setInterval(updateData, 2000); // actualisation toutes les 2 secondes
}

async function updateData() {
  const label = hhmm();
  try {
    const response = await fetch("/api/data");
    const json = await response.json();
    const d = json.RPI_001 || {};

    console.log("🌐 Données reçues du cloud:", d); // Debug

    const temperature = parseFloat(d.temperature || 0);
    const niveau = d.niveau || "normal";
    const etat = d.etat || "OFF";
    const restant = d.temps_restant || 0;
    const on = d.on || 0;
    const off = d.off || 0;

    // ===== Température =====
    if (tempChart) {
      tempChart.data.labels.push(label);
      tempChart.data.datasets[0].data.push(temperature);
      if (tempChart.data.labels.length > 20) {
        tempChart.data.labels.shift();
        tempChart.data.datasets[0].data.shift();
      }
      tempChart.update("none");
    }

    // ===== Niveau =====
    const niveauEl = document.getElementById("niveauText");
    const badge = document.getElementById("niveauBadge");
    const tankFill = document.getElementById("tankFill");

    if (niveauEl) {
      niveauEl.textContent = "Niveau : " + niveau.toUpperCase();
      if (niveau === "bas") {
        niveauEl.style.color = "red";
        badge.textContent = "BAS";
        badge.classList.remove("green");
        badge.classList.add("red");
        tankFill.style.height = "25%";
      } else {
        niveauEl.style.color = "limegreen";
        badge.textContent = "NORMAL";
        badge.classList.remove("red");
        badge.classList.add("green");
        tankFill.style.height = "90%";
      }
    }

    // ===== Cycle moteur =====
    document.getElementById("cycleState").textContent = etat;
    document.getElementById("cycleRemaining").textContent = formatTime(restant);
    document.getElementById("onValue").textContent = formatTime(on);
    document.getElementById("offValue").textContent = formatTime(off);
    console.log("Durées actuelles :", { on, off, restant, etat });

    const ledEl = document.getElementById("led");
    if (etat === "ON") ledEl.className = "led on";
    else if (etat === "OFF") ledEl.className = "led off";
    else ledEl.className = "led pause";

    // ===== Donut =====
    if (cycleChart) {
      let progress = 0;
      if (etat === "ON" && on > 0) progress = ((on - restant) / on) * 100;
      else if (etat === "OFF" && off > 0) progress = ((off - restant) / off) * 100;

      progress = Math.max(0, Math.min(100, progress));
      const color =
        etat === "ON" ? "#00ff00" :
        etat === "OFF" ? "#ff0000" : "#888888";

      cycleChart.data.datasets[0].data = [progress, 100 - progress];
      cycleChart.data.datasets[0].backgroundColor = [color, "#1b355e"];
      cycleChart.update("none");
    }

  } catch (error) {
    console.error("Erreur récupération données Render :", error);
  }
}

// ====================== CONTRÔLE DES DURÉES (boutons +/-) ======================
async function changerCycle(type, delta) {
  try {
    const res = await fetch("/api/data");
    const json = await res.json();
    const d = json.RPI_001 || {};

    let currentOn = d.on || 0;
    let currentOff = d.off || 0;

    if (type === "on") currentOn = Math.max(2, currentOn + delta);
    else if (type === "off") currentOff = Math.max(2, currentOff + delta);

    // Envoi vers Render
    await fetch("/api/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        device_id: "RPI_001",
        on: currentOn,
        off: currentOff,
        etat: d.etat,
        niveau: d.niveau,
        temperature: d.temperature,
        temps_restant: d.temps_restant,
        contact_ferme: d.contact_ferme,
      }),
    });

    console.log("✅ Cycle mis à jour :", { on: currentOn, off: currentOff });
    await updateData();

  } catch (err) {
    console.warn("⚠️ Erreur changement cycle:", err);
  }
}
