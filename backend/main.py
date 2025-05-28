from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime
from backend.supabase_client import supabase
import time

app = FastAPI()

# Allow cross-origin requests (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def serve_logs():
    return Path("templates/logs.html").read_text()

@app.get("/stream")
async def stream_logs():
    def event_stream():
        last_pos = 0
        while True:
            try:
                with open("logs.txt", "r", encoding="utf-8") as f:
                    f.seek(last_pos)
                    lines = f.readlines()
                    if lines:
                        for line in lines:
                            yield f"data: {line.strip()}\n\n"
                        last_pos = f.tell()
                time.sleep(1)
            except Exception as e:
                yield f"data: ❌ Error reading logs: {e}\n\n"
                time.sleep(2)
    return StreamingResponse(event_stream(), media_type="text/event-stream")

class Alert(BaseModel):
    lat: float
    lon: float
    city: str = None
    state: str = None
    county: str = None
    hail_size: float
    source: str
    roof_count: int = 0

@app.post("/alerts")
def insert_alert(alert: Alert):
    response = supabase.table("alerts").insert({
        "id": str(uuid4()),
        "lat": alert.lat,
        "lon": alert.lon,
        "city": alert.city,
        "state": alert.state,
        "county": alert.county,
        "hail_size": alert.hail_size,
        "source": alert.source,
        "roof_count": alert.roof_count,
        "timestamp": datetime.utcnow().isoformat()
    }).execute()
    return {"status": "inserted", "data": response.data}
