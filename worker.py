import requests
from datetime import datetime
from backend.supabase_client import supabase
from backend.hailstrike_email import fetch_hailstrike_alerts, push_to_supabase as push_hail
import time

LOG_FILE = "logs.txt"

def log(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    entry = f"{timestamp} {message}"
    print(entry)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")

def get_roof_count(lat, lon, radius_meters=1609):
    log(f"🔍 Counting roofs near {lat}, {lon}")
    query = f"""
    [out:json][timeout:25];
    (
      way["building"](around:{radius_meters},{lat},{lon});
    );
    out count;
    """
    try:
        r = requests.post("https://overpass-api.de/api/interpreter", data=query)
        count = r.json()["elements"][0]["tags"]["total"]
        log(f"🔍 Counting roofs near {lat}, {lon}: {count}")
        return int(count)
    except Exception as e:
        log(f"⚠️ OSM roof count failed: {e}")
        return 0

def fetch_noaa_alerts():
    log("📡 Fetching NOAA alerts...")
    url = "https://api.weather.gov/alerts/active?event=Severe%20Thunderstorm%20Warning"
    response = requests.get(url)
    if response.status_code != 200:
        log("⚠️ NOAA API error")
        return []

    data = response.json()
    alerts = []

    for feature in data.get("features", []):
        try:
            alert_id = feature.get("id")
            sent_time = feature["properties"].get("sent")
            geometry = feature.get("geometry")

            if not alert_id or not geometry or not geometry["coordinates"]:
                continue

            coords = geometry["coordinates"][0][0]
            lon, lat = coords[0], coords[1]

            exists = supabase.table("alerts").select("id").eq("alert_id", alert_id).execute()
            if exists.data:
                log(f"⏭️ Skipping duplicate NOAA alert: {alert_id}")
                continue

            alert = {
                "alert_id": alert_id,
                "lat": lat,
                "lon": lon,
                "hail_size": 1.0,
                "source": "noaa",
                "roof_count": get_roof_count(lat, lon),
                "city": None,
                "state": None,
                "county": None,
                "timestamp": sent_time or datetime.utcnow().isoformat()
            }
            log(f"📦 Inserting alert: {alert}")
            supabase.table("alerts").insert(alert).execute()
            log(f"📤 Uploading NOAA alert at {lat}, {lon}")
        except Exception as e:
            log(f"🚫 Error processing NOAA alert: {e}")
    return alerts

if __name__ == "__main__":
    log("🚀 HailWatch worker started")
    fetch_noaa_alerts()
    log("📬 Checking Gmail for HailStrike alerts...")
    try:
        hailstrike_alerts = fetch_hailstrike_alerts()
        if hailstrike_alerts:
            push_hail(hailstrike_alerts)
        else:
            log("📭 No new HailStrike alerts")
    except Exception as e:
        log(f"❌ HailStrike fetch failed: {e}")
    log("✅ Worker finished.")
