import streamlit as st
import json 
import firebase_admin
from firebase_admin import credentials, db
import time
import pandas as pd 

# --- 1. Firebase Initialization (using Streamlit Secrets) ---
# This block runs only once when the app starts
if not firebase_admin._apps:
    try:
        # 1. Load the immutable secrets dictionary
        secret_data = st.secrets["firebase_key"]
        
        # 2. CRITICAL FIX: Use dict() constructor to create a MUTABLE copy
        firebase_credentials = dict(secret_data)
        
        # 3. Handle newline conversion for private key
        if isinstance(firebase_credentials["private_key"], str):
            firebase_credentials["private_key"] = firebase_credentials["private_key"].replace('\\n', '\n')

        # 4. Initialize Firebase using the corrected credentials dictionary
        cred = credentials.Certificate(firebase_credentials)
        
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://hydrophonics-12345-default-rtdb.asia-southeast1.firebasedatabase.app/' 
        })
    except Exception as e:
        st.error(f"❌ Fatal Error: Could not initialize Firebase.")
        st.exception(e)
        st.stop() 

db_ref = db.reference('/')

# --- 2. Data Fetching ---
# Refreshes data from Firebase every 3 seconds
@st.cache_data(ttl=3) 
def fetch_data():
    try:
        data = db_ref.get()
        return data.get('sensors', {}), data.get('actuators', {})
    except Exception:
        return {}, {}

# --- 3. Actuator Control Function ---
def set_actuator(actuator, state):
    try:
        # Write command directly to Firebase (e.g., /actuators/pumpA)
        db_ref.child(f'actuators/{actuator}').set(state)
        # Clear cache to force an immediate refresh after the command is sent
        fetch_data.clear()
        st.rerun() # Forces Streamlit to rerun the app immediately
    except Exception as e:
        st.error(f"Failed to send command: {e}")

# --- 4. Main Dashboard Execution (Runs once per update/interaction) ---
st.set_page_config(layout="wide")
st.title("🧪 Automated Hydroponic System Dashboard")

# Fetch data for the current run
sensors, actuators = fetch_data() 

st.header("Live Sensor Readings")

# Display Sensor Metrics
col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("pH Level", f"{sensors.get('ph', '--'):.2f}")
col2.metric("EC (mS/cm)", f"{sensors.get('ec', '--'):.2f}")
col3.metric("Water Temp (°C)", f"{sensors.get('waterTemp', '--'):.1f}")
col4.metric("Air Temp (°C)", f"{sensors.get('airTemp', '--'):.1f}")
col5.metric("Humidity (%)", f"{sensors.get('humidity', '--'):.1f}")
col6.metric("Water Level", sensors.get('waterlevel', '--'))

st.markdown("---")
st.header("Actuator Controls")

# Pump A Controls
pumpA_status = actuators.get('pumpA_status', 'OFF')
st.subheader(f"Nutrient Pump A (Status: **{pumpA_status}**)")

col_a_on, col_a_off = st.columns(2)

# CRITICAL FIX: The logic is now outside the infinite loop.
# Clicking the button calls set_actuator, which calls st.rerun().
if col_a_on.button("Turn Pump A ON", key="A_ON"):
    set_actuator('pumpA', 'ON')
if col_a_off.button("Turn Pump A OFF", key="A_OFF"):
    set_actuator('pumpA', 'OFF')

# Pump B Controls
pumpB_status = actuators.get('pumpB_status', 'OFF')
st.subheader(f"pH Pump B (Status: **{pumpB_status}**)")

col_b_on, col_b_off = st.columns(2)
if col_b_on.button("Turn Pump B ON", key="B_ON"):
    set_actuator('pumpB', 'ON')
if col_b_off.button("Turn Pump B OFF", key="B_OFF"):
    set_actuator('pumpB', 'OFF')