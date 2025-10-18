// === CONFIG ===
const VALID_USERNAME = "0";
const VALID_PASSWORD = "0";
const API_URL = "https://tribologie-cloud.onrender.com/api/data"; // 🔗 Render API

// === Variables globales ===
let tempChart = null;
let cycleChart = null;

// === Connexion utilisateur ===
function loginUser(e) {
  e.preventDefault();
  const u = document.getElementById("username").value.trim();
  const p = document.getElementById("password").value.trim();
  const err = document.getElementById("error-msg");

  if (u === VALID_USERNAME && p === VALID_PASSWORD) {
    document.getElementById("loginBox").style.display = "none";
    const main = document.getElementById("dashboard");
    main.style.display = "flex";
    initCharts();
    startDashboard();
  } else {
    err.textContent = "Nom d’utilisateur ou mot de passe incorrect.";
    err.style.color = "red";
  }
  return false;
}

// === Initialisation graphiques ===
function initCharts() {
  const ctx1 = document.getElementById("tempChart").getContext("2d");
  tempChart = new Chart(ctx1, {
    type: "line",
    data: {
      labels: [],
      datasets: [{
        label: "Température (°C)",
        data: [],
        borderColor: "#ffcc00",
        backgroundColor: "rgba(255,204,0,0.18)",
        fill: true,
        tension: 0.4,
      }],
    },
    options: { responsive: true, scales: { y: { suggestedMax: 60 } } },
  });

  const ctx2 = document.getElementById("cycleChart").getContext("2d");
  cycleChart = new Chart(ctx2, {
    type: "doughnut",
    data: {
      labels: ["ON", "OFF"],
      datasets: [{ data: [0, 100], backgroundColor: ["#00ff00", "#333"] }],
    },
    options: { cutout: "70%", plugins: { legend: { display: false } } },
  });
}

// === Lecture et mise à jour ===
function startDashboard() {
  updateData();
  setInterval(updateData, 3000);
}
async function updateData() {
  const label = hhmm();
  try {
    const response = await fetch("/api/data");
    const json = await response.json();
    const d = json.RPI_001 || {};

    // 🔹 Lecture propre des valeurs
    const temperature = Number(d.temperature) || 0;
    const niveau = d.niveau || "normal";
    const etat = d.etat || "OFF";
    const on = Number(d.on) || 0;
    const off = Number(d.off) || 0;
    const restant = Number(d.temps_restant) || 0;

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
      } else {
        niveauEl.style.color = "limegreen";
        badge.textContent = "NORMAL";
        badge.classList.remove("red");
        badge.classList.add("green");
        tankFill.style.height = "90%";
      }
    }

    // ===== Cycle moteur =====
    const cycleStateEl = document.getElementById("cycleState");
    const ledEl = document.getElementById("led");
    const cycleRemaining = document.getElementById("cycleRemaining");
    const onValueEl = document.getElementById("onValue");
    const offValueEl = document.getElementById("offValue");

    // affichage texte
    if (cycleStateEl) cycleStateEl.textContent = etat;
    if (cycleRemaining) cycleRemaining.textContent = formatTime(restant);
    if (onValueEl) onValueEl.textContent = formatTime(on);
    if (offValueEl) offValueEl.textContent = formatTime(off);

    // LED
    if (ledEl) {
      if (etat === "ON") ledEl.className = "led on";
      else if (etat === "OFF") ledEl.className = "led off";
      else ledEl.className = "led pause";
    }

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
    console.error("Erreur récupération données depuis Render :", error);
  }
}
