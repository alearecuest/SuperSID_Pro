#!/usr/bin/env python3
"""
Observatory Setup - Configure your radio telescope monitor
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, 'src')
from core.config_manager import ConfigManager

def setup_observatory():
    """Interactive setup for observatory configuration"""
    print("SuperSID Pro Observatory Setup")
    print("=" * 50)
    
    # Observatory details
    print("\nObservatory Information:")
    observatory_name = input("Observatory Name [Default: My Observatory]: ") or "My Observatory"
    monitor_id = input("Monitor ID Number [e.g., 281]: ") or "281"
    
    print("\nLocation Information:")
    latitude = float(input("Latitude (decimal degrees): ") or "0.0")
    longitude = float(input("Longitude (decimal degrees): ") or "0.0")
    elevation = float(input("Elevation (meters): ") or "0.0")
    location = input("Location (City, Country): ") or "Unknown Location"
    
    print("\nContact Information:")
    contact_name = input("Your Name: ") or "Administrator"
    contact_email = input("Email: ") or "admin@observatory.local"
    
    print("\nVLF Stations to Monitor:")
    print("Available stations: NAA, NWC, DHO, GQD, NPM, etc.")
    stations_input = input("Station call signs (comma separated) [NAA,NWC]: ") or "NAA,NWC"
    stations = [s.strip().upper() for s in stations_input.split(",")]
    
    # Create configuration
    config = {
        "application": {
            "name": "SuperSID Pro",
            "version": "1.0.0",
            "debug": False,
            "first_run": False
        },
        "observatory": {
            "name": observatory_name,
            "monitor_id": monitor_id,
            "location": location,
            "coordinates": {
                "latitude": latitude,
                "longitude": longitude,
                "elevation": elevation
            },
            "timezone": "UTC",
            "contact": {
                "name": contact_name,
                "email": contact_email
            }
        },
        "vlf_stations": {
            "monitored_stations": stations,
            "station_frequencies": {
                "NAA": {"frequency": 24.0, "location": "Maine, USA"},
                "NWC": {"frequency": 19.8, "location": "Australia"},
                "DHO": {"frequency": 23.4, "location": "Germany"},
                "GQD": {"frequency": 19.6, "location": "UK"},
                "NPM": {"frequency": 21.4, "location": "Hawaii, USA"}
            }
        },
        "monitoring": {
            "auto_start": True,
            "data_retention_days": 30,
            "export_format": "csv",
            "screenshot_interval": 300
        },
        "reporting": {
            "ftp_upload": False,
            "ftp_server": "sid-ftp.stanford.edu",
            "ftp_directory": "/incoming/SuperSID/NEW/",
            "local_tmp": "/tmp",
            "report_interval": 86400
        },
        "space_weather": {
            "enable_spaceweatherlive": True,
            "spaceweatherlive_update_interval": 600,
            "enable_swpc_noaa": True,
            "swpc_update_interval": 600,
            "api_endpoints": {
                "spaceweatherlive": "https://www.spaceweatherlive.com/api",
                "swpc_noaa": "https://services.swpc.noaa.gov/json"
            }
        },
        "vlf_system": {
            "audio_sample_rate": 11025,
            "audio_buffer_size": 1024,
            "audio_device": None,
            "storage_batch_size": 10,
            "anomaly_detection": True,
            "baseline_update_interval": 300
        }
    }
    
    config_path = Path("config/default_config.json")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\nObservatory configuration saved!")
    print(f"Config file: {config_path}")
    print(f"Observatory: {observatory_name} (Monitor #{monitor_id})")
    print(f"Location: {location} ({latitude}°, {longitude}°)")
    print(f"Monitoring: {', '.join(stations)}")
    
    return config_path

if __name__ == "__main__":
    setup_observatory()