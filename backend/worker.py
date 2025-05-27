import requests
from datetime import datetime
from backend.supabase_client import supabase
from backend.hailstrike_email import fetch_hailstrike_alerts, push_to_supabase as push_hail

def fetch_noaa_alerts():
    print("📡 Fetching NOAA alerts...")
    url = "https://api.weather.gov/alerts/active?event=Severe%20Thunderstorm%20Warning"
    response = requests.get(url)

    if response.status_code != 200:
        print("⚠️ NOAA API error")
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
                print(f"⏭️ Skipping duplicate NOAA alert: {alert_id}")
                continue

            alert = {
                "alert_id": alert_id,
                "lat": lat,
                "lon": lon,
                "hail_size": 1.0,  # Default until we parse real size
                "source": "noaa",
                "roof_count": get_roof_count(lat, lon),
                "city": None,
                "state": None,
                "county": None,
                "timestamp": sent_time or datetime.utcnow().isoformat()
            }
            alerts.append(alert)

        except Exception as e:
            print("🚫 Error processing NOAA alert:", e)

    return alerts

def get_roof_count(lat, lon, radius_meters=1609):
    print(f"🔍 Counting roofs near {lat}, {lon}")
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
        return int(count)
    except Exception as e:
        print("⚠️ OSM roof count failed:", e)
        return 0

def push_to_supabase(alerts):
    for alert in alerts:
        print(f"📤 Uploading NOAA alert at {alert['lat']}, {alert['lon']}")
        supabase.table("alerts").insert(alert).execute()

if __name__ == "__main__":
    print("🚀 HailWatch worker started")

    # NOAA
    noaa_alerts = fetch_noaa_alerts()
    if noaa_alerts:
        push_to_supabase(noaa_alerts)
    else:
        print("📭 No new NOAA alerts")

    # HailStrike
    hailstrike_alerts = fetch_hailstrike_alerts()
    if hailstrike_alerts:
        push_hail(hailstrike_alerts)
    else:
        print("📭 No new HailStrike alerts")

    print("✅ Worker finished.")
