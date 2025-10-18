import json, time, random, os

BASE_PATH = "/home/pi/dashbord complet"
ETAT_FILE = os.path.join(BASE_PATH, "etat.json")

while True:
    data = {
        "temperature": round(random.uniform(25, 35), 2),
        "niveau": round(random.uniform(60, 100), 1),
        "contact": "FERME",
        "relais": "ON"
    }
    with open(ETAT_FILE, "w") as f:
        json.dump(data, f)
    print("✅ Données capteurs simulées :", data)
    time.sleep(2)
