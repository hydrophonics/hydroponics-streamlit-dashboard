import firebase_admin
from firebase_admin import credentials, db
import threading, time
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Firebase Initialization (FOR LOGGING) ---
# NOTE: Uses the serviceAccountKey.json file
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://hydrophonics-12345-default-rtdb.asia-southeast1.firebasedatabase.app/' 
})

# --- Google Sheets Setup ---
SHEET_NAME = "My_Hydroponics_Log" 
GOOGLE_KEY_FILE = "hydroponics-logging-key.json" 

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

try:
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_KEY_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME).sheet1
    print("✅ Connected to Google Sheet successfully!")
except Exception as e:
    print("❌ Error connecting to Google Sheets:", e)
    sheet = None

# ==================================
# Background Logging Function
# ==================================
def log_to_google_sheet():
    while True:
        try:
            sensors = db.reference('sensors').get() or {}
            actuators = db.reference('actuators').get() or {}

            if sheet and sensors:
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                ph = sensors.get("ph", "--")
                ec = sensors.get("ec", "--")
                waterTemp = sensors.get("waterTemp", "--")
                airTemp = sensors.get("airTemp", "--")
                humidity = sensors.get("humidity", "--")
                waterLevel = sensors.get("waterlevel", "--")

                pumpA = actuators.get("pumpA_status", "--")
                pumpB = actuators.get("pumpB_status", "--")

                row = [now, ph, ec, waterTemp, airTemp, humidity, waterLevel, pumpA, pumpB]
                sheet.append_row(row)
                print(f"📝 Logged data at {now}")
            else:
                print("⚠️ Skipping log (Sheet not connected or no data)")

        except Exception as e:
            print("❌ Logging error:", e)

        time.sleep(300) # 5 minutes

# --- Start Background Logger Thread ---
threading.Thread(target=log_to_google_sheet, daemon=True).start()

if __name__ == '__main__':
    print("✅ Background logging script is running. Data will be logged every 5 minutes.")
    while True:
        time.sleep(60)