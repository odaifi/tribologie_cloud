// ==== Identifiants simples (temporaire)
const VALID_USERNAME = "0";
const VALID_PASSWORD = "0";

// ==== Références globales
let tempChart = null;
let pressChart = null;
let vibChart = null;
let cycleChart = null;

// ==== Variables du cycle
let dureeOn = 0;
let dureeOff = 0;
let etatCycle = "OFF";
let tempsRestant = 0;

// ==== Helpers
function hhmm(date = new Date()) {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatTime(sec) {
  sec = Math.max(0, Math.floor(sec));
  const h = String(Math.floor(sec / 3600)).padStart(2, "0");
  const m = String(Math.floor((sec % 3600) / 60)).padStart(2, "0");
  const s = String(sec % 60).padStart(2, "0");
  return `${h}:${m}:${s}`;
}

// ==== Connexion
document.addEventListener("DOMContentLoaded", () => {
  const u = document.getElementById("username");
  if (u) u.focus();
});

function loginUser(e) {
  e.preventDefault();
  const u = document.getElementById("username").value.trim();
  const p = document.getElementById("password").value.trim();
  const err = document.getElementById("error-msg");

  if (u === VALID_USERNAME && p === VALID_PASSWORD) {
    console.log("Connexion réussie");
    document.getElementById("loginBox").style.display = "none";
    const main = document.getElementById("dashboard");
    main.style.display = "flex";
    main.classList.remove("hidden");
    err.textContent = "";
    initCharts();
    showSection("dashboard");
    startDashboard();
  } else {
    console.log("Échec connexion");
    err.textContent = "Nom d’utilisateur ou mot de passe incorrect.";
    err.style.color = "red";
  }
  return false;
}

// ==== Navigation (sidebar)
function showSection(section, el) {
  const ids = ["temp", "press", "vib", "niveau", "cycle"];
  ids.forEach((id) => {
    const card = document.getElementById(`card-${id}`);
    if (card)
      card.style.display =
        section === "dashboard" || section === id ? "block" : "none";
  });
  document.querySelectorAll(".sidebar ul li").forEach((li) =>
    li.classList.remove("active")
  );
  if (el) el.classList.add("active");
}

// ====================== INITIALISATION DES GRAPHIQUES ======================
function initCharts() {
  const commonOptions = {
    plugins: { legend: { display: true } },
    maintainAspectRatio: false,
    scales: {
      x: { ticks: { color: "#e4efff" } },
      y: { ticks: { color: "#e4efff" } },
    },
  };

  // Température
  const ctx1 = document.getElementById("tempChart").getContext("2d");
  tempChart = new Chart(ctx1, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Température (°C)",
          data: [],
          borderColor: "#ffcc00",
          backgroundColor: "rgba(255,204,0,0.18)",
          borderWidth: 2,
          fill: true,
          tension: 0.4,
        },
      ],
    },
    options: {
      ...commonOptions,
      scales: {
        ...commonOptions.scales,
        y: {
          min: 0,
          suggestedMax: 70,
          ticks: { stepSize: 5, color: "#e4efff" },
        },
      },
    },
  });

  // Pression
  const ctx2 = document.getElementById("pressChart").getContext("2d");
  pressChart = new Chart(ctx2, {
    type: "bar",
    data: {
      labels: [],
      datasets: [
        {
          label: "Pression (Bar)",
          data: [],
          backgroundColor: "#ffcc00",
        },
      ],
    },
    options: {
      ...commonOptions,
      scales: {
        ...commonOptions.scales,
        y: {
          min: 0,
          suggestedMax: 250,
          ticks: { stepSize: 20, color: "#e4efff" },
        },
      },
    },
  });

  // Vibration
  const ctx3 = document.getElementById("vibChart").getContext("2d");
  vibChart = new Chart(ctx3, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Vibration",
          data: [],
          borderColor: "#ffcc00",
          backgroundColor: "rgba(255,204,0,0.12)",
          fill: true,
          tension: 0.3,
        },
      ],
    },
    options: {
      ...commonOptions,
      scales: {
        ...commonOptions.scales,
        y: {
          min: 0,
          suggestedMax: 10,
          ticks: { stepSize: 1, color: "#e4efff" },
        },
      },
    },
  });

  // Cycle (donut)
  const ctx4 = document.getElementById("cycleChart").getContext("2d");
  cycleChart = new Chart(ctx4, {
    type: "doughnut",
    data: {
      labels: ["Progression", "Reste"],
      datasets: [
        {
          data: [0, 100],
          backgroundColor: ["#00ff00", "#1b355e"],
          borderWidth: 2,
        },
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
  setInterval(updateData, 2000);
  setInterval(lireEtatCycle, 2000);
}

async function updateData() {
  const label = hhmm();
  try {
    const response = await fetch("http://192.168.28.64:8081/etat.json");
    const data = await response.json();
    const temperature = parseFloat(data.temperature || 0);
    const pressure = parseFloat(data.pressure || 0);
    const vibration = parseFloat(data.vibration || 0);
    const niveau = data.niveau || "NORMAL";

    // Graphiques
    if (tempChart) {
      tempChart.data.labels.push(label);
      tempChart.data.datasets[0].data.push(temperature);
      if (tempChart.data.labels.length > 20) {
        tempChart.data.labels.shift();
        tempChart.data.datasets[0].data.shift();
      }
      tempChart.update("none");
    }
    if (pressChart) {
      pressChart.data.labels.push(label);
      pressChart.data.datasets[0].data.push(pressure);
      if (pressChart.data.labels.length > 20) {
        pressChart.data.labels.shift();
        pressChart.data.datasets[0].data.shift();
      }
      pressChart.update("none");
    }
    if (vibChart) {
      vibChart.data.labels.push(label);
      vibChart.data.datasets[0].data.push(vibration);
      if (vibChart.data.labels.length > 20) {
        vibChart.data.labels.shift();
        vibChart.data.datasets[0].data.shift();
      }
      vibChart.update("none");
    }

    // Niveau
    const niveauEl = document.getElementById("niveauText");
    const tankFill = document.getElementById("tankFill");
    const badge = document.getElementById("niveauBadge");

    if (niveauEl) {
      niveauEl.textContent = "Niveau : " + niveau.toUpperCase();
      if (niveau === "bas") {
        niveauEl.style.color = "red";
        badge.textContent = "BAS";
        badge.classList.remove("green");
        badge.classList.add("red");
        tankFill.style.height = "25%";
        tankFill.style.background = "linear-gradient(to top, #ff0000, #cc0000)";
      } else {
        niveauEl.style.color = "limegreen";
        badge.textContent = "NORMAL";
        badge.classList.remove("red");
        badge.classList.add("green");
        tankFill.style.height = "90%";
        tankFill.style.background = "linear-gradient(to top, #00bfff, #3399ff)";
      }
    }
  } catch (error) {
    console.error("Erreur de mise à jour :", error);
  }
}

// ====================== CYCLE SYNCHRONISÉ AVEC FASTAPI ======================
async function lireEtatCycle() {
  try {
    const res = await fetch("http://192.168.28.64:8081/cycle_state");
    const data = await res.json();

    etatCycle = data.etat || "OFF";
    dureeOn = data.on || 0;
    dureeOff = data.off || 0;
    tempsRestant = data.temps_restant || 0;

    document.getElementById("cycleState").textContent = etatCycle;
    document.getElementById("cycleRemaining").textContent = formatTime(tempsRestant);
    document.getElementById("onValue").textContent = formatTime(dureeOn);
    document.getElementById("offValue").textContent = formatTime(dureeOff);

    const ledEl = document.getElementById("led");
    if (ledEl) {
      if (etatCycle === "ON") ledEl.className = "led on";
      else if (etatCycle === "OFF") ledEl.className = "led off";
      else ledEl.className = "led pause";
    }

    // Mise à jour du donut
    if (cycleChart) {
      let progress = 0;
      if (etatCycle === "ON" && dureeOn > 0) {
        progress = ((dureeOn - tempsRestant) / dureeOn) * 100;
      } else if (etatCycle === "OFF" && dureeOff > 0) {
        progress = ((dureeOff - tempsRestant) / dureeOff) * 100;
      }

      progress = Math.max(0, Math.min(100, progress));
      const color =
        etatCycle === "ON"
          ? "#00ff00"
          : etatCycle === "OFF"
          ? "#ff0000"
          : "#888888";

      cycleChart.data.datasets[0].data = [progress, 100 - progress];
      cycleChart.data.datasets[0].backgroundColor = [color, "#1b355e"];
      cycleChart.update("none");
    }
  } catch (err) {
    console.warn("Erreur lecture cycle:", err);
  }
}
async function changerCycle(type, delta) {
  try {
    // 🔹 Lire les valeurs actuelles depuis FastAPI
    const res = await fetch("http://192.168.28.64:8081/cycle_state");
    const data = await res.json();

    let currentOn = data.on || 0;
    let currentOff = data.off || 0;

    // 🔹 Modifier selon le bouton cliqué
    if (type === "on") currentOn = Math.max(2, currentOn + delta);
    else if (type === "off") currentOff = Math.max(2, currentOff + delta);

    // 🔹 Envoyer vers FastAPI
    const update = await fetch("http://192.168.28.64:8081/cycle_update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ on: currentOn, off: currentOff }),
    });

    const result = await update.json();
    console.log("✅ Cycle mis à jour sur FastAPI :", result);

    // 🔹 Recharger les valeurs actualisées
    await lireEtatCycle();

  } catch (err) {
    console.warn("⚠️ Erreur lors du changement de cycle :", err);
  }
}
