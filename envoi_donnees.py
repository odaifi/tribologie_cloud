import requests, time

URL = "https://tribologie-cloud.onrender.com/api/update"  # ton API en ligne

while True:
    data = {
        "device_id": "RPI_001",
        "pression": 123.4,   # valeur simulée (remplacer plus tard par la vraie)
        "etat": "ON"
    }
    try:
        r = requests.post(URL, json=data, timeout=10)
        print("Réponse:", r.status_code, r.text)
    except Exception as e:
        print("Erreur:", e)
    time.sleep(5)  # renvoie toutes les 5 s
