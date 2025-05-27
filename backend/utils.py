import requests

def get_roof_count(lat, lon, radius_meters=1609):  # ~1 mile
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
