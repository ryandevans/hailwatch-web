from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime
import asyncio

from backend.supabase_client import supabase

app = FastAPI()

# Allow frontend apps to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the logs page
@app.get("/", response_class=HTMLResponse)
async def serve_logs():
    return Path("templates/logs.html").read_text()


# SSE streaming endpoint
@app.get("/stream")
async def stream_logs():
    async def event_generator():
        with open("logs.txt", "r") as f:
            f.seek(0, 2)  # go to end of file
            while True:
                line = f.readline()
                if line:
                    yield f"data: {line.strip()}\n\n"
                else:
                    await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# Data model for alerts
class Alert(BaseModel):
    lat: float
    lon: float
    city: str = None
    state: str = None
    county: str = None
    hail_size: float
    source: str
    roof_count: int = 0

# Insert new alert
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
