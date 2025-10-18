import RPi.GPIO as GPIO
import time
import os
import requests
import json


# === CONFIG ===
RELAIS_PIN = 27
CONTACT_PIN = 22
API_BASE = "http://192.168.28.64:8081"
API_CYCLE = f"{API_BASE}/cycle"

# === SETUP GPIO ===
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAIS_PIN, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(CONTACT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("🔄 Moteur prêt. Durées ON/OFF viennent du dashboard.")
print("Contact fermé → moteur autorisé. Contact ouvert → pause.\n")

phase = "OFF"
temps_depart = None
temps_pause = 0
temps_restant_avant_pause = 0
cycle_actif = False

def set_relais(etat: bool):
    GPIO.output(RELAIS_PIN, GPIO.LOW if etat else GPIO.HIGH)

def lire_durees():
    try:
        r = requests.get(API_CYCLE, timeout=2)
        data = r.json()
        return int(data.get("on", 15)), int(data.get("off", 15))
    except Exception as e:
        print("⚠️ Erreur lecture cycle :", e)
        return 15, 15

try:
    while True:
        DUREE_ON, DUREE_OFF = lire_durees()
        contact_ferme = GPIO.input(CONTACT_PIN) == GPIO.LOW

        # === CONTACT OUVERT ===
        if not contact_ferme:
            if cycle_actif:
                # on calcule le temps restant avant la pause
                duree_phase = DUREE_ON if phase == "ON" else DUREE_OFF
                temps_pause = time.time() - temps_depart
                temps_restant_avant_pause = max(0, duree_phase - temps_pause)
                cycle_actif = False
                set_relais(False)
                print("\n🟥 Contact ouvert → cycle figé, relais OFF")
            os.system("clear")
            print("=== CYCLE EN PAUSE ===")
            print(f"Phase : {phase}")
            print(f"Temps restant avant reprise : {int(temps_restant_avant_pause)} s")
            print("Relais = OFF (sécurité)")
            time.sleep(1)
            continue

        # === CONTACT FERMÉ ===
        if not cycle_actif:
            cycle_actif = True
            # reprise à partir du temps restant avant pause
            duree_phase = DUREE_ON if phase == "ON" else DUREE_OFF
            temps_depart = time.time() - (duree_phase - temps_restant_avant_pause)
            if phase == "ON" and temps_restant_avant_pause > 0:
                set_relais(True)
            print("\n▶️ Contact fermé → reprise du cycle")

        # === Gestion du cycle ===
        temps_ecoule = time.time() - temps_depart
        duree_phase = DUREE_ON if phase == "ON" else DUREE_OFF
        restant = duree_phase - temps_ecoule

        if restant <= 0:
            if phase == "ON":
                phase = "OFF"
                set_relais(False)
                print("⏱ Fin phase ON → relais OFF")
            else:
                phase = "ON"
                set_relais(True)
                print("⏱ Fin phase OFF → relais ON")
            temps_depart = time.time()
            restant = DUREE_ON if phase == "ON" else DUREE_OFF

        # === Affichage dynamique ===
               # === Affichage dynamique ===
        os.system("clear")
        print("=== CYCLE ACTIF ===")
        print(f"Durées : ON={DUREE_ON}s / OFF={DUREE_OFF}s")
        print(f"Phase : {phase}")
        print(f"Temps restant : {int(restant)} s")
        print("Relais :", "ON ✅" if phase == "ON" else "OFF ❌")
        print("(Ctrl+C pour arrêter)")

        # --- ENVOI ÉTAT MOTEUR AU DASHBOARD ---
        try:
            requests.post(f"{API_BASE}/update_moteur", json={
                "phase": phase,
                "temps_restant": int(restant)
            }, timeout=1)
        except:
            pass
        # === Mise à jour du fichier etat.json pour le dashboard ===
        try:
            etat_data = {"phase": phase, "temps_restant": int(restant)}
            with open("/home/pi/dashboard_pompe/etat.json", "w") as f:
                json.dump(etat_data, f)
        except Exception as e:
            print("⚠️ Erreur écriture état moteur :", e)

        time.sleep(1)

except KeyboardInterrupt:
    set_relais(False)
    GPIO.cleanup()
    print("\n🧹 GPIO nettoyés, relais OFF, programme arrêté proprement.")
# Sauvegarde état pour le dashboard
etat_data = {"phase": phase, "temps_restant": int(restant)}
with open("/home/pi/dashboard_pompe/etat.json", "w") as f:
    json.dump(etat_data, f)