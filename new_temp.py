import time, json, glob, os, requests
import RPi.GPIO as GPIO

# ===============================
# CONFIGURATION GÉNÉRALE
# ===============================
FICHIER_JSON = "/home/pi/dashbord complet/etat.json"
CLOUD_URL = "https://tribologie-cloud.onrender.com/api/update"  # 🌐 URL Render
DATA_URL = "https://tribologie-cloud.onrender.com/api/data"     # 🌐 Pour récupérer les valeurs actuelles

# ===============================
# CONFIGURATION DES PINS
# ===============================
PIN_NIVEAU = 17       # Capteur de niveau
RELAIS_PIN = 27       # Relais moteur
CONTACT_PIN = 22      # Interrupteur de sécurité

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_NIVEAU, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(RELAIS_PIN, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(CONTACT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# ===============================
# VARIABLES DU CYCLE MOTEUR
# ===============================
state = {
    "etat": "OFF",
    "on": 30,               # durée phase ON (secondes)
    "off": 22,              # durée phase OFF (secondes)
    "temps_restant": 22     # compteur avant changement
}

# ===============================
# DÉTECTION CAPTEUR TEMPÉRATURE DS18B20
# ===============================
def get_sensor_file():
    base = "/sys/bus/w1/devices/"
    dossiers = glob.glob(base + "28-*")
    if not dossiers:
        print("⚠️ Aucun capteur DS18B20 détecté")
        return None
    return os.path.join(dossiers[0], "w1_slave")

sensor_file = get_sensor_file()

def read_temp():
    """Lecture de la température en °C"""
    if not sensor_file or not os.path.exists(sensor_file):
        return None
    try:
        with open(sensor_file, "r") as f:
            lines = f.readlines()
        if "YES" not in lines[0]:
            return None
        pos = lines[1].find("t=")
        if pos == -1:
            return None
        temp_c = float(lines[1][pos + 2:]) / 1000.0
        return round(temp_c, 1)
    except:
        return None

# ===============================
# LOGIQUE MOTEUR
# ===============================
def lire_contact():
    """Retourne True si contact fermé (autorisation moteur)"""
    return GPIO.input(CONTACT_PIN) == GPIO.LOW

def set_relais(on: bool):
    """Active ou désactive le relais moteur"""
    GPIO.output(RELAIS_PIN, GPIO.LOW if on else GPIO.HIGH)

# ===============================
# ENVOI VERS CLOUD
# ===============================
def envoyer_vers_cloud(data):
    try:
        r = requests.post(CLOUD_URL, json=data, timeout=5)
        print("🌐 Cloud:", r.status_code, r.text)
    except Exception as e:
        print("⚠️ Erreur cloud:", e)

# ===============================
# SYNCHRONISATION CLOUD (ON/OFF)
# ===============================
def sync_on_off_depuis_cloud():
    """Vérifie si le cloud a modifié les temps ON/OFF"""
    global state
    try:
        r = requests.get(DATA_URL, timeout=3)
        cloud_data = r.json().get("RPI_001", {})
        new_on = cloud_data.get("on", state["on"])
        new_off = cloud_data.get("off", state["off"])
        if new_on != state["on"] or new_off != state["off"]:
            print(f"🔄 Synchronisation Render → Raspberry : ON={new_on}s | OFF={new_off}s")
            state["on"], state["off"] = new_on, new_off
    except Exception as e:
        print("⚠️ Erreur synchro cloud:", e)

# ===============================
# BOUCLE PRINCIPALE
# ===============================
print("🚀 Système Tribologie démarré : capteurs + moteur + cloud")

try:
    en_pause = False

    while True:
        # 🔁 Synchronisation avec le dashboard
        sync_on_off_depuis_cloud()

        # 1️⃣ Lecture des capteurs
        temp = read_temp()
        niveau_gpio = GPIO.input(PIN_NIVEAU)
        etat_niveau = "bas" if niveau_gpio == 0 else "normal"
        contact_ferme = lire_contact()

        # 2️⃣ Gestion de la sécurité (contacteur)
        if not contact_ferme:
            if not en_pause:
                en_pause = True
                state["etat_avant_pause"] = state["etat"]
                state["etat"] = "PAUSE"
                set_relais(False)
            # ⚠️ Continue à lire et envoyer les données même en pause

        else:
            # Si on revient de pause
            if en_pause:
                en_pause = False
                state["etat"] = state.get("etat_avant_pause", "OFF")
                if state["etat"] == "ON":
                    set_relais(True)

                # 🔹 Envoi immédiat après reprise
                etat = {
                    "device_id": "RPI_001",
                    "temperature": temp if temp is not None else "N/A",
                    "niveau": etat_niveau,
                    "etat": state["etat"],
                    "on": state["on"],
                    "off": state["off"],
                    "temps_restant": state["temps_restant"],
                    "contact_ferme": contact_ferme
                }
                with open(FICHIER_JSON, "w") as f:
                    json.dump(etat, f)
                envoyer_vers_cloud(etat)
                print("✅ Reprise du cycle après contact fermé")

            # 3️⃣ Gestion du cycle ON/OFF (uniquement si contact fermé)
            state["temps_restant"] -= 2  # décrémente toutes les 2s
            if state["temps_restant"] <= 0:
                if state["etat"] == "ON":
                    state["etat"] = "OFF"
                    state["temps_restant"] = state["off"]
                    set_relais(False)
                else:
                    state["etat"] = "ON"
                    state["temps_restant"] = state["on"]
                    set_relais(True)

        # 4️⃣ Données envoyées (cloud + fichier local)
        etat = {
            "device_id": "RPI_001",
            "temperature": temp if temp is not None else "N/A",
            "niveau": etat_niveau,
            "etat": state["etat"],
            "on": state["on"],
            "off": state["off"],
            "temps_restant": state["temps_restant"],
            "contact_ferme": contact_ferme
        }

        with open(FICHIER_JSON, "w") as f:
            json.dump(etat, f)

        envoyer_vers_cloud(etat)

        print(f"🌡️ Temp: {temp}°C | Niveau: {etat_niveau} | État moteur: {state['etat']} | Restant: {state['temps_restant']}s | ON={state['on']}s | OFF={state['off']}s")
        time.sleep(2)

except KeyboardInterrupt:
    GPIO.cleanup()
    print("🧹 GPIO nettoyés proprement")
