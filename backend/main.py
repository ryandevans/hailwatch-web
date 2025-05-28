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
    allow_origins=["*"],  # Adjust for production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve logs.html page
@app.get("/", response_class=HTMLResponse)
async def serve_logs():
    return Path("templates/logs.html").read_text()

# SSE endpoint for real-time logs
@app.get("/stream-logs")
async def stream_logs():
    async def event_generator():
        while True:
            try:
                with open("logs.txt", "r") as f:
                    lines = f.readlines()[-20:]  # Show last 20 log lines
                for line in lines:
                    yield f"data: {line.strip()}\n\n"
                await asyncio.sleep(5)
            except Exception:
                yield f"data: (log file unavailable)\n\n"
                await asyncio.sleep(5)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Health check (optional — this route is overridden by "/" above)
@app.get("/health")
def health_check():
    return {"status": "Hailwatch API is live!"}

# Data model for incoming alerts
class Alert(BaseModel):
    lat: float
    lon: float
    city: str = None
    state: str = None
    county: str = None
    hail_size: float
    source: str
    roof_count: int = 0

# Insert alerts into Supabase
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
