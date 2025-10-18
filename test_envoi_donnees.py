import requests
import time

# Remplace cette URL par ton futur lien Render (on la mettra après le déploiement)
URL = "http://192.168.28.64:8081/api/update"  # pour tester en local d’abord

while True:
    data = {
        "device_id": "RPI_001",
        "pression": 123.4,   # valeur simulée
        "etat": "ON"
    }

    try:
        r = requests.post(URL, json=data)
        print("Envoyé :", r.json())
    except Exception as e:
        print("Erreur :", e)

    time.sleep(5)  # envoie toutes les 5 secondes
