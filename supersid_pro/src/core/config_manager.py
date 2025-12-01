"""
Configuration Manager for SuperSID Pro
Handles all application configuration and settings
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class ObservatoryConfig:
    """Observatory configuration data"""
    monitor_id: int
    name: str
    latitude: float
    longitude: float
    timezone: str
    elevation: float

@dataclass
class VLFStation:
    """VLF Station configuration"""
    code: str
    name: str
    frequency: float
    latitude: float
    longitude: float
    enabled: bool

class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_file: str):
        self.config_file = Path(config_file)
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.create_default_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self.create_default_config()
    
    def save_config(self) -> None:
        """Save configuration to file"""
        try:
            # Ensure directory exists
            self. config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def create_default_config(self) -> None:
        """Create default configuration"""
        self.config = {
            "application": {
                "name": "SuperSID Pro",
                "version": "1.0.0",
                "first_run": True,
                "last_updated": datetime.now().isoformat()
            },
            "observatory": {
                "monitor_id": 0,
                "name": "",
                "latitude": 0. 0,
                "longitude": 0.0,
                "timezone": "UTC",
                "elevation": 0.0
            },
            "vlf_stations": {
                "default_stations": []
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by key"""
        keys = key. split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_observatory_config(self) -> ObservatoryConfig:
        """Get observatory configuration as dataclass"""
        obs_config = self.get('observatory', {})
        return ObservatoryConfig(**obs_config)
    
    def set_observatory_config(self, observatory: ObservatoryConfig) -> None:
        """Set observatory configuration"""
        self.set('observatory', asdict(observatory))
    
    def get_vlf_stations(self) -> list[VLFStation]:
        """Get VLF stations configuration"""
        stations_data = self.get('vlf_stations. default_stations', [])
        return [VLFStation(**station) for station in stations_data]
    
    def add_vlf_station(self, station: VLFStation) -> None:
        """Add VLF station to configuration"""
        stations = self.get('vlf_stations.default_stations', [])
        stations.append(asdict(station))
        self. set('vlf_stations.default_stations', stations)
    
    def remove_vlf_station(self, station_code: str) -> None:
        """Remove VLF station from configuration"""
        stations = self.get('vlf_stations.default_stations', [])
        stations = [s for s in stations if s.get('code') != station_code]
        self.set('vlf_stations.default_stations', stations)