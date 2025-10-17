
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
    payload = await req.json()
    device_id = payload.get("device_id", "unknown")
    payload["ts"] = int(time.time())
    LAST_DATA[device_id] = payload
    return {"status": "ok"}

@app.get("/api/data")
def api_data():
    return LAST_DATA

app.mount("/", StaticFiles(directory="static", html=True), name="static")
