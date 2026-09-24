# SKYsense AI - Simulated IoT Client (`iot_simulator/`)

## 1. Important Scientific & Hardware Disclaimer

> **SIMULATED IoT DEVICE NOTICE**  
> This directory contains a **software simulator** designed for demonstration, validation, and academic review.
> - **NOT real IoT hardware**: No physical sensors (e.g. DHT11, BME280) or microcontrollers (ESP32, Raspberry Pi) are connected.
> - All transmitted values (`device_id`, `latitude`, `longitude`, `temperature`, `humidity`) are **simulated software values**.
> - Do not cite or present simulated numbers as physical in-situ meteorological measurements.

---

## 2. Purpose & Architecture

The simulator demonstrates how future edge devices will communicate with SKYsense AI over HTTP using `POST /api/predict/`:

```
   ┌────────────────────────────────┐
   │    Simulated IoT Client        │
   │  (simulate_device.py)          │
   └───────────────┬────────────────┘
                   │
                   │  1. Loads cloud photograph
                   │  2. Packages synthetic device telemetry
                   │  3. Transmits multipart/form-data
                   ▼
   ┌────────────────────────────────┐
   │ SKYsense Backend Ingestion API │
   │       POST /api/predict/       │
   └───────────────┬────────────────┘
                   │
                   │  4. Runs Xception deep learning inference
                   │  5. Computes confidence & probability distribution
                   │  6. Persists record in SQLite database
                   ▼
   ┌────────────────────────────────┐
   │    JSON Response (HTTP 200)    │
   │  - Dominant Rainfall Regime    │
   │  - Confidence Percentage       │
   │  - Softmax Probability Matrix  │
   │  - Echoed Sensor Metadata      │
   └────────────────────────────────┘
```

---

## 3. Quickstart & Usage

### 3.1 Basic Usage with an Image File
```bash
python iot_simulator/simulate_device.py path/to/cloud_image.jpg
```

### 3.2 Automated Test with Test Split Sample
If no image path is passed or `--sample` is provided, the simulator automatically locates a verified cloud image from the test partition:
```bash
python iot_simulator/simulate_device.py --sample
```

### 3.3 Custom Telemetry Overrides
```bash
python iot_simulator/simulate_device.py image.jpg \
  --device-id ESP32-CAM-NODE-07 \
  --lat 12.9716 \
  --lon 77.5946 \
  --temp 26.5 \
  --humidity 78.0
```

### 3.4 Custom Endpoint
```bash
python iot_simulator/simulate_device.py image.jpg --endpoint http://192.168.1.50:8000/api/predict/
```

---

## 4. Expected Output Format

The simulator prints the complete formatted JSON response followed by an ASCII confidence breakdown:

```json
{
  "success": true,
  "prediction": "Medium_to_Heavy_Rain",
  "confidence": 0.8845,
  "probabilities": {
    "Low_to_Medium_Rain": 0.0825,
    "Medium_to_Heavy_Rain": 0.8845,
    "No_to_Low_Rain": 0.0330
  },
  "timestamp": "2026-09-24T03:15:20.123456+00:00",
  "model_version": "Xception-v1.0",
  "id": "7b8d29a1-43ef-489e-991c-16b713e2f180",
  "source_type": "IOT_DEVICE",
  "device_id": "SIMULATED-ESP32-CAM-01",
  "latitude": 12.9716,
  "longitude": 77.5946,
  "temperature": 24.8,
  "humidity": 76.5
}
```

Every successful run appends to `iot_simulator/simulated_telemetry_log.json` for auditing and historical demonstration.
