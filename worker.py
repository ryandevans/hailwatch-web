import requests
from datetime import datetime
from backend.supabase_client import supabase
from backend.hailstrike_email import fetch_hailstrike_alerts, push_to_supabase as push_hail
from backend.utils import get_roof_count

LOG_FILE = "logs.txt"

def log(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    full_message = f"{timestamp} {message}"
    print(full_message)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(full_message + "\n")
    except Exception as e:
        print("⚠️ Failed to write to log file:", e)

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

            coords = geometry["coordinates"][0][0]  # [lon, lat]
            lon, lat = coords[0], coords[1]

            exists = supabase.table("alerts").select("id").eq("alert_id", alert_id).execute()
            if exists.data:
                log(f"⏭️ Skipping duplicate NOAA alert: {alert_id}")
                continue

            roof_count = get_roof_count(lat, lon)
            log(f"🔍 Counting roofs near {lat}, {lon}: {roof_count}")

            alert = {
                "alert_id": alert_id,
                "lat": lat,
                "lon": lon,
                "hail_size": 1.0,
                "source": "noaa",
                "roof_count": roof_count,
                "city": None,
                "state": None,
                "county": None,
                "timestamp": sent_time or datetime.utcnow().isoformat()
            }
            alerts.append(alert)

        except Exception as e:
            log(f"🚫 Error processing NOAA alert: {e}")

    return alerts

def push_to_supabase(alerts):
    for alert in alerts:
        log(f"📤 Uploading NOAA alert at {alert['lat']}, {alert['lon']}")
        try:
            supabase.table("alerts").insert(alert).execute()
        except Exception as e:
            log(f"❌ Failed to insert alert: {e}")
    print("📦 Inserting alert:", alert)


if __name__ == "__main__":
    log("🚀 HailWatch worker started")

    noaa_alerts = fetch_noaa_alerts()
    if noaa_alerts:
        push_to_supabase(noaa_alerts)
    else:
        log("📭 No new NOAA alerts")

    hailstrike_alerts = fetch_hailstrike_alerts()
    if hailstrike_alerts:
        push_hail(hailstrike_alerts)
    else:
        log("📭 No new HailStrike alerts")

    log("✅ Worker finished.")
