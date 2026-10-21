from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)
DATA_FILE = "latest_data.json"

@app.route("/sensor-data", methods=["POST"])
def receive_sensor_data():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Expected JSON data"}), 400

    required = [
        "pressure_bar",
        "flow_lpm",
        "turbidity_ntu",
        "temperature_c",
        "vibration_ms2",
    ]

    try:
        readings = {key: float(data[key]) for key in required}
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Missing or invalid sensor readings"}), 400

    readings["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    temp_file = DATA_FILE + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(readings, file, indent=2)
    os.replace(temp_file, DATA_FILE)

    return jsonify({"status": "received", "readings": readings}), 200

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "Smart Water Pipeline receiver running"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
