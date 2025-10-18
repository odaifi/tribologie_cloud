import time, json, glob, os, requests
import RPi.GPIO as GPIO

# ===============================
# CONFIGURATION GÉNÉRALE
# ===============================
FICHIER_JSON = "/home/pi/dashbord complet/etat.json"
CLOUD_URL = "https://tribologie-cloud.onrender.com/api/update"  # 🌐 URL Render

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
# GESTION DU CYCLE MOTEUR
# ===============================
state = {
    "etat": "OFF",
    "on": 30,
    "off": 22,
    "temps_restant": 22
}

def lire_contact():
    """Retourne True si contact fermé"""
    return GPIO.input(CONTACT_PIN) == GPIO.LOW

def set_relais(on: bool):
    """Active ou désactive le relais"""
    GPIO.output(RELAIS_PIN, GPIO.LOW if on else GPIO.HIGH)

# ===============================
# ENVOI DES DONNÉES VERS LE CLOUD
# ===============================
def envoyer_vers_cloud(data):
    try:
        r = requests.post(CLOUD_URL, json=data, timeout=5)
        print("🌐 Cloud:", r.status_code, r.text)
    except Exception as e:
        print("⚠️ Erreur cloud:", e)

# ===============================
# BOUCLE PRINCIPALE
# ===============================
print("🚀 Système Tribologie démarré : capteurs + moteur + cloud")

try:
    while True:
        # Lecture capteurs
        temp = read_temp()
        niveau_gpio = GPIO.input(PIN_NIVEAU)
        etat_niveau = "bas" if niveau_gpio == 0 else "normal"
        contact_ferme = lire_contact()

        # Gestion moteur
        state["temps_restant"] -= 1
        if state["temps_restant"] <= 0:
            if state["etat"] == "ON":
                state["etat"] = "OFF"
                state["temps_restant"] = state["off"]
                set_relais(False)
            else:
                state["etat"] = "ON"
                state["temps_restant"] = state["on"]
                set_relais(True)

        # Structure complète à envoyer
        data = {
            "device_id": "RPI_001",
            "temperature": temp if temp is not None else "N/A",
            "niveau": etat_niveau,
            "etat": state["etat"],
            "on": state["on"],
            "off": state["off"],
            "temps_restant": state["temps_restant"],
            "contact_ferme": contact_ferme
        }

        # Sauvegarde locale pour dashboard
        with open(FICHIER_JSON, "w") as f:
            json.dump(data, f)

        # Envoi cloud
        envoyer_vers_cloud(data)

        print(f"🌡️ Temp: {temp}°C | Niveau: {etat_niveau} | État moteur: {state['etat']} | Restant: {state['temps_restant']}s")
        time.sleep(5)

except KeyboardInterrupt:
    GPIO.cleanup()
    print("🧹 GPIO nettoyés proprement")
