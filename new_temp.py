import time, json, glob, os, requests
import RPi.GPIO as GPIO

# ===============================
# CONFIGURATION GÉNÉRALE
# ===============================
FICHIER_JSON = "/home/pi/dashbord complet/etat.json"
CLOUD_URL = "https://tribologie-cloud.onrender.com/api/update"  # Envoi vers Render
DATA_URL = "https://tribologie-cloud.onrender.com/api/data"     # Lecture depuis Render

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
# TEMPÉRATURE (DS18B20)
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
# LOGIQUE GPIO
# ===============================
def lire_contact():
    """Retourne True si contact fermé (autorisation moteur)"""
    return GPIO.input(CONTACT_PIN) == GPIO.LOW

def set_relais(on: bool):
    """Active ou désactive le relais moteur"""
    GPIO.output(RELAIS_PIN, GPIO.LOW if on else GPIO.HIGH)

# ===============================
# CLOUD
# ===============================
def envoyer_vers_cloud(data):
    """Envoi des données au cloud Render"""
    try:
        r = requests.post(CLOUD_URL, json=data, timeout=5)
        print("🌐 Cloud:", r.status_code, r.text)
    except Exception as e:
        print("⚠️ Erreur cloud:", e)

def sync_on_off_depuis_cloud():
    """Récupère les nouveaux temps ON/OFF depuis Render"""
    global state
    try:
        r = requests.get(DATA_URL, timeout=3)
        cloud_data = r.json().get("RPI_001", {})
        new_on = cloud_data.get("on", state["on"])
        new_off = cloud_data.get("off", state["off"])
        if new_on != state["on"] or new_off != state["off"]:
            state["on"], state["off"] = new_on, new_off
            print(f"🔄 Synchro Render → Raspberry : ON={new_on}s | OFF={new_off}s")
    except Exception as e:
        print("⚠️ Erreur synchro cloud:", e)

# ===============================
# BOUCLE PRINCIPALE
# ===============================
print("🚀 Système Tribologie (synchronisé avec Render) démarré")

try:
    en_pause = False

    while True:
        # 🔁 Synchroniser avec Render toutes les 2s
        sync_on_off_depuis_cloud()

        # Lecture capteurs
        temp = read_temp()
        niveau_gpio = GPIO.input(PIN_NIVEAU)
        etat_niveau = "bas" if niveau_gpio == 0 else "normal"
        contact_ferme = lire_contact()

        # Sécurité contacteur
        if not contact_ferme:
            if not en_pause:
                en_pause = True
                state["etat_avant_pause"] = state["etat"]
                state["etat"] = "PAUSE"
                set_relais(False)
                print("⚠️ Contact ouvert → moteur en pause")

        else:
            if en_pause:
                en_pause = False
                state["etat"] = state.get("etat_avant_pause", "OFF")
                print("✅ Contact refermé → reprise du cycle")
                if state["etat"] == "ON":
                    set_relais(True)

            # Cycle moteur
            state["temps_restant"] -= 2
            if state["temps_restant"] <= 0:
                if state["etat"] == "ON":
                    state["etat"] = "OFF"
                    state["temps_restant"] = state["off"]
                    set_relais(False)
                else:
                    state["etat"] = "ON"
                    state["temps_restant"] = state["on"]
                    set_relais(True)

        # Données à envoyer
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

        # Sauvegarde locale + envoi cloud
        with open(FICHIER_JSON, "w") as f:
            json.dump(etat, f)

        envoyer_vers_cloud(etat)

        print(f"🌡️ Temp: {temp}°C | Niveau: {etat_niveau} | État: {state['etat']} | "
              f"Restant: {state['temps_restant']}s | ON={state['on']}s | OFF={state['off']}s | "
              f"Contact: {'fermé' if contact_ferme else 'ouvert'}")

        time.sleep(2)

except KeyboardInterrupt:
    GPIO.cleanup()
    print("🧹 GPIO nettoyés proprement")
