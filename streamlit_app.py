import streamlit as st
import json # Needed for handling potential string credentials
import firebase_admin
from firebase_admin import credentials, db
import time
import pandas as pd # Included as per requirements.txt

# --- 1. Firebase Initialization (CORRECTED using st.secrets) ---
if not firebase_admin._apps:
    try:
        # Load the credentials dictionary from st.secrets
        # ⚠️ CRITICAL FIX: Use .copy() to make the dictionary mutable
        firebase_credentials = st.secrets["firebase_key"].copy() 
        
        # Now we can safely modify the private_key string in the copy
        if isinstance(firebase_credentials["private_key"], str):
            firebase_credentials["private_key"] = firebase_credentials["private_key"].replace('\\n', '\n')

        # Initialize Firebase using the now-corrected credentials dictionary
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
        # Read the entire database root
        data = db_ref.get()
        return data.get('sensors', {}), data.get('actuators', {})
    except Exception:
        # Return empty dictionaries on failure
        return {}, {}

# --- 3. Actuator Control Function ---
def set_actuator(actuator, state):
    try:
        # Write command directly to Firebase (e.g., /actuators/pumpA)
        db_ref.child(f'actuators/{actuator}').set(state)
        # Clear cache to force an immediate refresh after the command is sent
        fetch_data.clear()
    except Exception as e:
        st.error(f"Failed to send command: {e}")

# --- 4. Streamlit Dashboard Layout ---
st.set_page_config(layout="wide")
st.title("🧪 Automated Hydroponic System Dashboard")
placeholder = st.empty() # Placeholder for refreshing content

while True:
    sensors, actuators = fetch_data()

    with placeholder.container():
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

    time.sleep(1) # Reruns the dashboard fetch every 1 second