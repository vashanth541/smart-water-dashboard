import json
import os
from datetime import datetime

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# --------------------------------------------------
# Page setup
# --------------------------------------------------
st.set_page_config(
    page_title="Smart Water Pipeline Monitor",
    page_icon="💧",
    layout="wide",
)

DATA_FILE = "latest_data.json"

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    .status-normal {
        background: #e4f6e9; color: #176534;
        padding: 5px 10px; border-radius: 8px;
        font-weight: 700; display: inline-block;
    }
    .status-warning {
        background: #fff0d5; color: #875500;
        padding: 5px 10px; border-radius: 8px;
        font-weight: 700; display: inline-block;
    }
    .status-critical {
        background: #ffe4e4; color: #a11919;
        padding: 5px 10px; border-radius: 8px;
        font-weight: 700; display: inline-block;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("💧 Smart Water Pipeline Monitoring")
st.caption(
    "Real-time sensor monitoring • Safe-range analysis • "
    "Fault alerts • Troubleshooting guidance"
)

# --------------------------------------------------
# Safe ranges: configurable demonstration values
# --------------------------------------------------
DEFAULT_LIMITS = {
    "pressure_min": 1.0,
    "pressure_max": 8.0,
    "flow_min": 1.0,
    "flow_max": 20.0,
    "turbidity_max": 500.0,
    "temperature_min": 5.0,
    "temperature_max": 40.0,
    "vibration_max": 3.0,
}

SENSOR_INFO = {
    "pressure_bar": {
        "name": "Water Pressure",
        "unit": "bar",
        "icon": "🔵",
        "low": "Check for leaks, low tank level, pump failure, or a blocked intake.",
        "high": "Check for a closed valve, pressure regulator, pump overpressure, or water hammer.",
    },
    "flow_lpm": {
        "name": "Water Flow Rate",
        "unit": "L/min",
        "icon": "🌊",
        "low": "Check for a blockage, closed valve, low supply, pump issue, or flow sensor wiring.",
        "high": "Check for a leak, unexpected valve opening, sensor calibration, or excessive pump output.",
    },
    "turbidity_ntu": {
        "name": "Water Turbidity",
        "unit": "NTU",
        "icon": "💧",
        "low": "No high-turbidity alert. Low turbidity alone does not prove water is safe to drink.",
        "high": "Inspect for sediment, disturbed deposits, filter problems, or contamination; verify with a calibrated test.",
    },
    "temperature_c": {
        "name": "Water Temperature",
        "unit": "°C",
        "icon": "🌡️",
        "low": "Check the temperature sensor, water source, stagnant sections, and heating/cooling conditions.",
        "high": "Check heat exposure, the water source, process conditions, and temperature sensor calibration.",
    },
    "vibration_ms2": {
        "name": "Pipe Vibration",
        "unit": "m/s²",
        "icon": "〰️",
        "low": "No excessive-vibration alert. Confirm the sensor is mounted securely.",
        "high": "Inspect pipe supports, pump alignment, loose fittings, cavitation, and mechanical wear.",
    },
}


def load_live_data():
    if not os.path.exists(DATA_FILE):
        return None

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        required = [
            "pressure_bar",
            "flow_lpm",
            "turbidity_ntu",
            "temperature_c",
            "vibration_ms2",
        ]

        if not all(key in data for key in required):
            return None

        for key in required:
            data[key] = float(data[key])

        return data
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None


def evaluate_parameter(key, value, limits):
    if key == "pressure_bar":
        low, high = limits["pressure_min"], limits["pressure_max"]
        if value < low:
            return "LOW", "critical"
        if value > high:
            return "HIGH", "critical"

    elif key == "flow_lpm":
        low, high = limits["flow_min"], limits["flow_max"]
        if value < low:
            return "LOW", "warning"
        if value > high:
            return "HIGH", "warning"

    elif key == "turbidity_ntu":
        if value > limits["turbidity_max"]:
            return "HIGH", "critical"

    elif key == "temperature_c":
        low, high = limits["temperature_min"], limits["temperature_max"]
        if value < low:
            return "LOW", "warning"
        if value > high:
            return "HIGH", "warning"

    elif key == "vibration_ms2":
        if value > limits["vibration_max"]:
            return "HIGH", "warning"

    return "NORMAL", "normal"


def suggestion_for(key, status):
    info = SENSOR_INFO[key]
    if status == "LOW":
        return info["low"]
    if status == "HIGH":
        return info["high"]
    return info["low"]


# --------------------------------------------------
# Sidebar controls
# --------------------------------------------------
st.sidebar.header("⚙️ Dashboard Settings")

mode = st.sidebar.radio(
    "Data source",
    ["Demo Mode", "Live Data Mode"],
)

st.sidebar.subheader("Safe operating ranges")
st.sidebar.caption(
    "These are adjustable prototype defaults, not universal engineering limits."
)

with st.sidebar.expander("Pressure", expanded=True):
    limits_pressure_min = st.number_input(
        "Minimum pressure (bar)", 0.0, 100.0, 1.0, 0.5
    )
    limits_pressure_max = st.number_input(
        "Maximum pressure (bar)", 0.1, 200.0, 8.0, 0.5
    )

with st.sidebar.expander("Flow rate"):
    limits_flow_min = st.number_input(
        "Minimum flow (L/min)", 0.0, 500.0, 1.0, 0.5
    )
    limits_flow_max = st.number_input(
        "Maximum flow (L/min)", 0.1, 1000.0, 20.0, 0.5
    )

with st.sidebar.expander("Turbidity"):
    limits_turbidity_max = st.number_input(
        "Maximum turbidity (NTU)", 0.0, 10000.0, 500.0, 10.0
    )

with st.sidebar.expander("Temperature"):
    limits_temperature_min = st.number_input(
        "Minimum temperature (°C)", -20.0, 100.0, 5.0, 1.0
    )
    limits_temperature_max = st.number_input(
        "Maximum temperature (°C)", -10.0, 150.0, 40.0, 1.0
    )

with st.sidebar.expander("Vibration"):
    limits_vibration_max = st.number_input(
        "Maximum vibration deviation (m/s²)",
        0.0, 100.0, 3.0, 0.5
    )

limits = {
    "pressure_min": limits_pressure_min,
    "pressure_max": limits_pressure_max,
    "flow_min": limits_flow_min,
    "flow_max": limits_flow_max,
    "turbidity_max": limits_turbidity_max,
    "temperature_min": limits_temperature_min,
    "temperature_max": limits_temperature_max,
    "vibration_max": limits_vibration_max,
}

# --------------------------------------------------
# Demo or live sensor readings
# --------------------------------------------------
if mode == "Demo Mode":
    st.sidebar.subheader("Demo sensor controls")
    st.sidebar.caption("Change these values to test alerts.")

    pressure = st.sidebar.slider(
        "Pressure (bar)", 0.0, 10.0, 5.0, 0.1
    )
    flow = st.sidebar.slider(
        "Flow rate (L/min)", 0.0, 30.0, 5.0, 0.5
    )
    turbidity = st.sidebar.slider(
        "Turbidity (NTU)", 0.0, 1000.0, 100.0, 10.0
    )
    temperature = st.sidebar.slider(
        "Temperature (°C)", 0.0, 80.0, 25.0, 0.5
    )
    vibration = st.sidebar.slider(
        "Vibration deviation (m/s²)", 0.0, 20.0, 0.0, 0.1
    )

    data = {
        "pressure_bar": pressure,
        "flow_lpm": flow,
        "turbidity_ntu": turbidity,
        "temperature_c": temperature,
        "vibration_ms2": vibration,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

else:
    st_autorefresh(interval=2000, key="live_refresh")
    data = load_live_data()

    if data is None:
        st.warning(
            "No valid live readings found. The dashboard expects "
            "latest_data.json in the same folder as app.py. "
            "We'll connect the ESP32 data sender in the next stage."
        )
        st.stop()

# --------------------------------------------------
# Evaluate parameters
# --------------------------------------------------
parameters = [
    ("pressure_bar", data["pressure_bar"]),
    ("flow_lpm", data["flow_lpm"]),
    ("turbidity_ntu", data["turbidity_ntu"]),
    ("temperature_c", data["temperature_c"]),
    ("vibration_ms2", data["vibration_ms2"]),
]

results = {}
for key, value in parameters:
    status, severity = evaluate_parameter(key, value, limits)
    results[key] = {
        "value": value,
        "status": status,
        "severity": severity,
        "suggestion": suggestion_for(key, status),
    }

critical_count = sum(
    1 for result in results.values()
    if result["severity"] == "critical"
)
warning_count = sum(
    1 for result in results.values()
    if result["severity"] == "warning"
)

st.caption(
    f"Data source: {mode}  •  "
    f"Last update: {data.get('timestamp', 'Not provided')}"
)

if critical_count:
    st.error(
        f"🚨 {critical_count} critical parameter alert(s). "
        "Inspect the system and verify the sensor readings."
    )
elif warning_count:
    st.warning(
        f"⚠️ {warning_count} parameter warning(s). "
        "Review the suggested checks below."
    )
else:
    st.success("✅ All monitored parameters are within configured limits.")

# --------------------------------------------------
# Sensor cards
# --------------------------------------------------
st.subheader("📊 Live Parameter Values")

columns = st.columns(3)

for index, (key, value) in enumerate(parameters):
    info = SENSOR_INFO[key]
    result = results[key]

    if key == "pressure_bar":
        range_text = (
            f'{limits["pressure_min"]:.1f}–'
            f'{limits["pressure_max"]:.1f} bar'
        )
        value_text = f"{value:.2f} bar"
    elif key == "flow_lpm":
        range_text = (
            f'{limits["flow_min"]:.1f}–'
            f'{limits["flow_max"]:.1f} L/min'
        )
        value_text = f"{value:.2f} L/min"
    elif key == "turbidity_ntu":
        range_text = f'≤ {limits["turbidity_max"]:.1f} NTU'
        value_text = f"{value:.1f} NTU"
    elif key == "temperature_c":
        range_text = (
            f'{limits["temperature_min"]:.1f}–'
            f'{limits["temperature_max"]:.1f} °C'
        )
        value_text = f"{value:.2f} °C"
    else:
        range_text = f'≤ {limits["vibration_max"]:.1f} m/s²'
        value_text = f"{value:.2f} m/s²"

    with columns[index % 3]:
        st.metric(
            label=f'{info["icon"]} {info["name"]}',
            value=value_text,
            delta=f'Status: {result["status"]}',
            delta_color=(
                "normal" if result["severity"] == "normal"
                else "inverse"
            ),
        )
        st.caption(f"Configured safe range: {range_text}")

# --------------------------------------------------
# Troubleshooting alerts
# --------------------------------------------------
st.subheader("🚨 Alerts and Recommended Checks")

alerts = [
    (key, result)
    for key, result in results.items()
    if result["status"] != "NORMAL"
]

if not alerts:
    st.info("No active parameter alerts. Continue monitoring.")
else:
    for key, result in alerts:
        info = SENSOR_INFO[key]
        heading = f'{info["name"]}: {result["status"]}'

        if result["severity"] == "critical":
            with st.expander(f"🔴 {heading}", expanded=True):
                st.write(
                    f'**Measured value:** {result["value"]:.2f} '
                    f'{info["unit"]}'
                )
                st.write("**Suggested checks:**")
                st.write(result["suggestion"])
        else:
            with st.expander(f"🟠 {heading}", expanded=True):
                st.write(
                    f'**Measured value:** {result["value"]:.2f} '
                    f'{info["unit"]}'
                )
                st.write("**Suggested checks:**")
                st.write(result["suggestion"])

# --------------------------------------------------
# Current readings table
# --------------------------------------------------
st.subheader("📋 Parameter Summary")

summary_rows = []
for key, value in parameters:
    info = SENSOR_INFO[key]
    result = results[key]
    summary_rows.append({
        "Parameter": info["name"],
        "Value": round(value, 3),
        "Unit": info["unit"],
        "Status": result["status"],
        "Severity": result["severity"].upper(),
        "Suggested action": result["suggestion"],
    })

st.dataframe(
    pd.DataFrame(summary_rows),
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "Prototype guidance only. Confirm alarms with calibrated instruments "
    "and application-specific limits before making operational decisions."
)