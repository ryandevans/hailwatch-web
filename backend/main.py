from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime

from backend.supabase_client import supabase

app = FastAPI()

# Allow frontend apps to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this if you want to restrict it
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/")
def home():
    return {"status": "Hailwatch API is live!"}

# Data model for incoming alerts
class Alert(BaseModel):
    lat: float
    lon: float
    city: str = None
    state: str = None
    county: str = None
    hail_size: float
    source: str  # 'noaa' or 'hailstrike'
    roof_count: int = 0

# Endpoint to insert a new alert into Supabase
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
