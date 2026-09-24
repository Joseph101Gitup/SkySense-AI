#!/usr/bin/env python3
"""
SKYsense AI - Simulated IoT Edge Client
=======================================
DISCLAIMER:
This script is a SIMULATED IoT CLIENT for software demonstration and validation.
It does NOT connect to physical IoT hardware or real atmospheric sensors.
All sensor measurements (device_id, latitude, longitude, temperature, humidity)
are synthetic and intended solely to demonstrate how future ESP32, Raspberry Pi,
or edge camera stations will communicate with the SKYsense AI REST API endpoint.

Usage:
    python simulate_device.py <path_to_cloud_image>
    python simulate_device.py image.jpg
    python simulate_device.py --sample
    python simulate_device.py image.jpg --endpoint http://localhost:8000/api/predict/
"""

import sys
import os
import time
import json
import random
import argparse
from pathlib import Path
from datetime import datetime

try:
    import requests
except ImportError:
    print("[ERROR] Missing required library 'requests'. Install with: pip install requests")
    sys.exit(1)

# Ensure UTF-8 output on Windows consoles if supported
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


DEFAULT_ENDPOINT = "http://127.0.0.1:8000/api/predict/"

# Pre-configured simulated IoT edge nodes
SIMULATED_DEVICES = [
    {
        "device_id": "SIMULATED-ESP32-CAM-01",
        "station_name": "SkyCam Edge Node Alpha (Simulated)",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "location_name": "Bangalore Urban (Simulated)",
        "base_temp": 24.5,
        "base_humidity": 76.0,
    },
    {
        "device_id": "SIMULATED-RPI4-STATION-02",
        "station_name": "Meteorological Micro-Node Beta (Simulated)",
        "latitude": 13.0827,
        "longitude": 80.2707,
        "location_name": "Coastal Station East (Simulated)",
        "base_temp": 28.2,
        "base_humidity": 84.5,
    },
    {
        "device_id": "SIMULATED-JETSON-NANO-03",
        "station_name": "High-Altitude Cloud Sensor Gamma (Simulated)",
        "latitude": 15.3173,
        "longitude": 75.7139,
        "location_name": "Deccan Plateau Plateau (Simulated)",
        "base_temp": 21.0,
        "base_humidity": 62.0,
    }
]


def print_banner():
    banner = """
================================================================================
              SKYsense AI - SIMULATED IoT DEVICE CLIENT
                    (Edge Hardware Demonstration)
--------------------------------------------------------------------------------
 [!] NOTICE: SIMULATED IoT DEVICE
     This software simulates an edge camera node (ESP32-CAM / Raspberry Pi).
     Sensor readings are SYNTHETIC and do NOT represent physical measurements.
================================================================================
"""
    print(banner)


def find_sample_image() -> Path:
    """Finds a verified sample image from the test split for quick demonstration."""
    base_dir = Path(__file__).resolve().parent.parent
    test_splits = base_dir / "03_AI_Model" / "datasets" / "splits" / "test"
    
    if test_splits.exists():
        for category in ["Medium_to_Heavy_Rain", "Low_to_Medium_Rain", "No_to_Low_Rain"]:
            cat_dir = test_splits / category
            if cat_dir.exists():
                images = list(cat_dir.glob("*.jpg"))
                if images:
                    return images[0]
                    
    # Fallback to local directory
    local_images = list(Path(__file__).parent.glob("*.jpg")) + list(Path(__file__).parent.glob("*.png"))
    if local_images:
        return local_images[0]

    return None


def generate_simulated_telemetry(device_profile: dict, temp_override=None, hum_override=None) -> dict:
    """Generates realistic synthetic environmental telemetry for testing."""
    # Add minor realistic fluctuations (&plusmn;0.5°C, &plusmn;1.5% RH)
    temp = temp_override if temp_override is not None else round(device_profile["base_temp"] + random.uniform(-0.8, 0.8), 1)
    humidity = hum_override if hum_override is not None else round(device_profile["base_humidity"] + random.uniform(-2.0, 2.0), 1)
    
    return {
        "device_id": device_profile["device_id"],
        "latitude": str(device_profile["latitude"]),
        "longitude": str(device_profile["longitude"]),
        "temperature": str(temp),
        "humidity": str(humidity),
        "notes": f"[SIMULATED IoT DEVICE] Automated edge telemetry from {device_profile['station_name']} at {datetime.now().strftime('%H:%M:%S')}",
    }


def send_iot_prediction(image_path: Path, endpoint: str, metadata: dict, log_file: Path = None):
    """Packages image and simulated telemetry, posts to API, and parses response."""
    if not image_path.exists() or not image_path.is_file():
        print(f"[ERROR] Image file does not exist: {image_path}")
        sys.exit(1)

    file_size_kb = round(image_path.stat().st_size / 1024, 1)

    print(f"[*] Target API Endpoint:  {endpoint}")
    print(f"[*] Ingesting Image File: {image_path.name} ({file_size_kb} KB)")
    print(f"[*] Device Profile:       {metadata['device_id']}")
    print(f"[*] Simulated Location:   Lat {metadata['latitude']}, Lon {metadata['longitude']}")
    print(f"[*] Simulated Telemetry:  Temperature = {metadata['temperature']} °C | Relative Humidity = {metadata['humidity']} %")
    print(f"[*] Transmission Status:  Transmitting multipart/form-data payload...")

    start_time = time.perf_counter()

    try:
        with open(image_path, "rb") as f:
            files = {
                "image": (image_path.name, f, "image/jpeg")
            }
            # Telemetry parameters sent alongside image
            response = requests.post(endpoint, files=files, data=metadata, timeout=120)
            
        rtt_ms = round((time.perf_counter() - start_time) * 1000.0, 1)

    except requests.exceptions.ConnectionError:
        print("\n[FAILED] Could not connect to the SKYsense AI backend server.")
        print(f"         Please verify the Django server is running at: {endpoint}")
        print("         Tip: Run 'python manage.py runserver' inside '05_Backend/'")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("\n[FAILED] Request timed out while waiting for inference response.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAILED] Unexpected error during API request: {e}")
        sys.exit(1)

    print(f"\n[+] HTTP Response Status: {response.status_code} ({response.reason}) [Network RTT: {rtt_ms} ms]")

    try:
        response_json = response.json()
    except Exception:
        print("[ERROR] Response payload is not valid JSON:")
        print(response.text[:500])
        sys.exit(1)

    print("\n" + "-" * 80)
    print("                      RAW JSON API RESPONSE")
    print("-" * 80)
    print(json.dumps(response_json, indent=2))
    print("-" * 80)

    # Display structured summary
    if response.status_code == 200 and response_json.get("success"):
        pred = response_json.get("prediction", "Unknown")
        conf = response_json.get("confidence", 0.0)
        conf_pct = round(conf * 100, 2)
        probs = response_json.get("probabilities", {})
        model_ver = response_json.get("model_version", "Xception-v1.0")
        latency = response_json.get("processing_time_ms", 0.0)
        rec_id = response_json.get("id", "N/A")
        timestamp = response_json.get("timestamp", "N/A")

        print("\n================================================================================")
        print("                     SIMULATED IoT INFERENCE RESULTS")
        print("================================================================================")
        print(f"  Classification Result:    {pred.replace('_', ' ').upper()}")
        print(f"  Confidence Score:         {conf_pct}%")
        print(f"  Deep Learning Model:      {model_ver} (Inference Latency: {latency} ms)")
        print(f"  Database Record UUID:     {rec_id}")
        print(f"  Server Timestamp (UTC):   {timestamp}")
        print("\n  Softmax Class Probability Breakdown:")
        for category, prob in probs.items():
            bar_len = int(prob * 30)
            bar = "#" * bar_len + "-" * (30 - bar_len)
            print(f"    - {category.replace('_', ' '):<22} : {prob * 100:5.2f}%  [{bar}]")
        print("================================================================================")
        print("  [OK] Observation successfully persisted in database via IoT interface.")
        print("================================================================================\n")

        # Save result to log file
        if log_file:
            log_entry = {
                "execution_time": datetime.now().isoformat(),
                "simulated_device": metadata,
                "image_filename": image_path.name,
                "network_rtt_ms": rtt_ms,
                "api_response": response_json,
            }
            try:
                log_data = []
                if log_file.exists():
                    try:
                        with open(log_file, "r", encoding="utf-8") as lf:
                            log_data = json.load(lf)
                    except Exception:
                        log_data = []
                log_data.append(log_entry)
                with open(log_file, "w", encoding="utf-8") as lf:
                    json.dump(log_data, lf, indent=2)
                print(f"[*] Telemetry log updated: {log_file}")
            except Exception as e:
                print(f"[!] Warning: Could not write log file: {e}")

    else:
        error_msg = response_json.get("error", "Unknown error")
        print(f"\n[!] INFERENCE FAILED: {error_msg}\n")


def main():
    print_banner()

    parser = argparse.ArgumentParser(
        description="SKYsense AI - Simulated IoT Device Client (Demonstration Only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python simulate_device.py sky_photo.jpg
    python simulate_device.py --sample
    python simulate_device.py image.jpg --device-id ESP32-CAM-05 --temp 29.5 --humidity 82.0
        """
    )
    parser.add_argument("image_path", nargs="?", default=None, help="Path to cloud photograph (JPG/PNG)")
    parser.add_argument("--sample", action="store_true", help="Automatically use a verified test sample image")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help=f"Target API endpoint (default: {DEFAULT_ENDPOINT})")
    parser.add_argument("--device-id", default=None, help="Simulated hardware device ID")
    parser.add_argument("--lat", type=float, default=None, help="Simulated latitude coordinate")
    parser.add_argument("--lon", type=float, default=None, help="Simulated longitude coordinate")
    parser.add_argument("--temp", type=float, default=None, help="Simulated ground temperature (°C)")
    parser.add_argument("--humidity", type=float, default=None, help="Simulated relative humidity (%%)")

    args = parser.parse_args()

    # Determine image path
    if args.sample or not args.image_path:
        sample_img = find_sample_image()
        if sample_img:
            image_path = sample_img
            print(f"[*] Using verified test split specimen: {image_path}")
        else:
            if not args.image_path:
                print("[ERROR] No image file provided and no sample images found.")
                print("Usage: python simulate_device.py <path_to_image.jpg>")
                sys.exit(1)
            image_path = Path(args.image_path)
    else:
        image_path = Path(args.image_path)

    # Select simulated device profile
    profile = random.choice(SIMULATED_DEVICES).copy()
    if args.device_id:
        profile["device_id"] = args.device_id
    if args.lat is not None:
        profile["latitude"] = args.lat
    if args.lon is not None:
        profile["longitude"] = args.lon

    metadata = generate_simulated_telemetry(profile, temp_override=args.temp, hum_override=args.humidity)
    log_file = Path(__file__).parent / "simulated_telemetry_log.json"

    send_iot_prediction(image_path, args.endpoint, metadata, log_file=log_file)


if __name__ == "__main__":
    main()
