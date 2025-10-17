from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import time

app = FastAPI()
LAST_DATA = {}

@app.get("/health")
def health():
    return {"ok": True, "ts": int(time.time())}

@app.post("/api/update")
async def api_update(req: Request):
    """Reçoit les données envoyées depuis le Raspberry"""
    payload = await req.json()
    device_id = payload.get("device_id", "unknown")
    payload["ts"] = int(time.time())
    LAST_DATA[device_id] = payload
    print(f"📥 Données reçues : {payload}")
    return {"status": "ok"}

@app.get("/api/data")
def api_data():
    """Permet au site web ou dashboard de lire les dernières données"""
    return LAST_DATA

# Servir les fichiers HTML/JS du dashboard
app.mount("/", StaticFiles(directory="static", html=True), name="static")
