import time
import requests
from datetime import datetime
from backend.supabase_client import supabase

def fetch_noaa_alerts():
    print("📡 Fetching NOAA alerts...")
    # Example endpoint (replace with real filter later)
    url = "https://api.weather.gov/alerts/active?event=Severe%20Thunderstorm%20Warning"
    response = requests.get(url)
    if response.status_code != 200:
        print("⚠️ NOAA API error")
        return []

    data = response.json()
    alerts = []
    for feature in data.get("features", []):
        try:
            coords = feature["geometry"]["coordinates"][0][0]  # [lon, lat]
            alert = {
                "lat": coords[1],
                "lon": coords[0],
                "hail_size": 1.0,  # Placeholder
                "source": "noaa",
                "roof_count": get_roof_count(coords[1], coords[0]),
                "city": None,
                "state": None,
                "county": None,
                "timestamp": datetime.utcnow().isoformat()
            }
            alerts.append(alert)
        except Exception as e:
            print("🚫 Skipped malformed NOAA alert:", e)

    return alerts

def get_roof_count(lat, lon, radius_meters=1609):  # ~1 mile
    print(f"🔎 Estimating roof count near {lat}, {lon}")
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
        print(f"📤 Uploading alert at {alert['lat']}, {alert['lon']}")
        alert["id"] = str(datetime.utcnow().timestamp()) + alert["source"]
        supabase.table("alerts").insert(alert).execute()

if __name__ == "__main__":
    print("🚀 HailWatch worker started...")
    noaa_alerts = fetch_noaa_alerts()

    if noaa_alerts:
        push_to_supabase(noaa_alerts)

    print("✅ Done")
