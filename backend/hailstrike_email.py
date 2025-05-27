import imaplib
import email
from datetime import datetime, timedelta
from backend.supabase_client import supabase
from backend.worker import get_roof_count
from supabase_client import supabase
from backend.utils import get_roof_count
from hailstrike_email import fetch_hailstrike_alerts, push_to_supabase as push_hail


# NOTE: For deployment to Render, replace these with environment variables later
EMAIL = "hailstrike@unitedpowersolutions.com"
APP_PASSWORD = "eibz cigt aqlt xncx"

def fetch_hailstrike_alerts():
    print("📬 Checking Gmail for HailStrike alerts...")

    try:
        # Connect to Gmail
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL, APP_PASSWORD)
        mail.select("inbox")

        # Look for HailStrike messages from last 1 day
        since = (datetime.utcnow() - timedelta(days=1)).strftime("%d-%b-%Y")
        result, data = mail.search(None, f'(SINCE "{since}" SUBJECT "Hail Notification")')

        alert_ids = data[0].split()
        new_alerts = []

        for num in alert_ids:
            result, msg_data = mail.fetch(num, "(RFC822)")
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Get email body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors="ignore")

            # Very basic parsing – adjust this to match your actual email format
            try:
                lat = float(body.split("Latitude: ")[1].split()[0])
                lon = float(body.split("Longitude: ")[1].split()[0])
                hail_size = float(body.split("Hail Size: ")[1].split()[0].replace('"', ''))

                alert_id = f"hailstrike-{num.decode()}"
                exists = supabase.table("alerts").select("id").eq("alert_id", alert_id).execute()
                if exists.data:
                    print(f"⏭️ Skipping duplicate email alert: {alert_id}")
                    continue

                alert = {
                    "alert_id": alert_id,
                    "lat": lat,
                    "lon": lon,
                    "hail_size": hail_size,
                    "source": "hailstrike",
                    "roof_count": get_roof_count(lat, lon),
                    "city": None,
                    "state": None,
                    "county": None,
                    "timestamp": datetime.utcnow().isoformat()
                }
                new_alerts.append(alert)

            except Exception as e:
                print("❌ Failed to parse email alert:", e)

        return new_alerts

    except Exception as e:
        print("❌ Gmail connection error:", e)
        return []

def push_to_supabase(alerts):
    for alert in alerts:
        print(f"📤 Uploading HailStrike alert: {alert['alert_id']}")
        supabase.table("alerts").insert(alert).execute()

if __name__ == "__main__":
    alerts = fetch_hailstrike_alerts()
    if alerts:
        push_to_supabase(alerts)
    else:
        print("📭 No new HailStrike alerts found.")
