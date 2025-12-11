"""
Advanced Configuration Manager for SuperSID Pro
Handles all application settings with validation and automatic updates
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from enum import Enum
import copy

from core.logger import get_logger, log_exception

class ThemeType(Enum):
    """Available UI themes"""
    DARK = "dark"
    LIGHT = "light"
    AUTO = "auto"

class LanguageType(Enum):
    """Supported languages"""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"

@dataclass
class ObservatoryConfig:
    """Observatory configuration data"""
    monitor_id: int = 0
    name: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    timezone: str = "UTC"
    elevation: float = 0.0
    contact_email: str = ""
    website: str = ""
    description: str = ""
    established: Optional[str] = None

@dataclass 
class VLFStation:
    """VLF Station configuration"""
    code: str = ""
    name: str = ""
    frequency: float = 0.0
    latitude: float = 0.0
    longitude: float = 0.0
    enabled: bool = True
    power: str = ""
    country: str = ""
    callsign: str = ""
    notes: str = ""

@dataclass
class DataSourceConfig:
    """External data source configuration"""
    enabled: bool = True
    url: str = ""
    api_key: str = ""
    update_interval: int = 600  # seconds
    timeout: int = 30
    retry_count: int = 3
    last_update: Optional[str] = None

@dataclass
class SamplingConfig:
    """Audio sampling configuration"""
    sample_rate: int = 48000
    buffer_size: int = 1024
    audio_device: str = "default"
    channels: int = 1
    format: str = "float32"
    gain: float = 1.0
    filter_enabled: bool = True
    filter_low: float = 15000.0
    filter_high: float = 25000.0

@dataclass
class DisplayConfig:
    """Display and visualization configuration"""
    chart_colors: Dict[str, str] = field(default_factory=lambda: {
        "background": "#1e1e1e",
        "grid": "#404040", 
        "signal": "#00ff00",
        "flare_marker": "#ff0000",
        "text": "#ffffff",
        "primary": "#0078d4",
        "warning": "#ffaa00",
        "error": "#ff4444"
    })
    update_interval: int = 1000
    history_hours: int = 24
    chart_style: str = "dark"
    show_grid: bool = True
    auto_scale: bool = True
    line_width: float = 1.5
    marker_size: int = 6

@dataclass
class AlertConfig:
    """Alert and notification configuration"""
    sound_enabled: bool = True
    desktop_notifications: bool = True
    email_notifications: bool = False
    flare_threshold: str = "M1. 0"
    signal_threshold: float = -3.0
    email_recipients: List[str] = field(default_factory=list)
    sound_file: str = ""
    notification_cooldown: int = 300  # seconds

class ConfigManager:
    """Advanced configuration manager with validation and auto-save"""
    
    def __init__(self, config_file: str = "config/default_config.json"):
        self. config_file = Path(config_file)
        self.config: Dict[str, Any] = {}
        self.logger = get_logger(__name__)
        
        self._original_config = {}
        self._auto_save = True
        self._validation_errors = []
        self._saving = False
        
        self. load_config()
        self._original_config = copy.deepcopy(self.config)
    
    def load_config(self) -> bool:
        """Load configuration from file with error handling"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                
                self. logger.info(f"Configuration loaded from {self.config_file}")
                
                self._validate_and_upgrade()
                return True
            else:
                self.logger. warning(f"Config file not found: {self.config_file}")
                self.create_default_config()
                return False
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in config file: {e}")
            log_exception(e, f"Loading config from {self.config_file}")
            self.create_default_config()
            return False
        except Exception as e:
            self.logger. error(f"Error loading config: {e}")
            log_exception(e, f"Loading config from {self.config_file}")
            self.create_default_config()
            return False
    
    def save_config(self, backup: bool = True) -> bool:
        """Save configuration to file with backup"""
        if self._saving:
            return False
        
        self._saving = True
        
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            if backup and self.config_file.exists():
                backup_file = self.config_file.with_suffix('.bak')
                backup_file.write_bytes(self.config_file.read_bytes())
            
            if 'application' not in self.config:
                self.config['application'] = {}
            self.config['application']['last_updated'] = datetime.now().isoformat()
            
            with open(self. config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            self.logger.info(f"Configuration saved to {self.config_file}")
            self._original_config = copy.deepcopy(self.config)
            return True
            
        except Exception as e:
            self.logger. error(f"Error saving config: {e}")
            log_exception(e, f"Saving config to {self.config_file}")
            return False
        finally:
            self._saving = False
    
    def create_default_config(self) -> None:
        """Create comprehensive default configuration"""
        self.config = {
            "application": {
                "name": "SuperSID Pro",
                "version": "1.0.0",
                "language": "en",
                "theme": "dark",
                "auto_save_interval": 300,
                "first_run": True,
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            },
            
            "development": {
                "use_mock_data": False
            },
            
            "observatory": {
                "monitor_id": 0,
                "name": "",
                "latitude": 0.0,
                "longitude": 0.0,
                "timezone": "UTC",
                "elevation": 0.0,
                "contact_email": "",
                "website": "",
                "description": "",
                "established": None
            },
            
            "vlf_stations": {
                "default_stations": [
                    {
                        "code": "NAA",
                        "name": "Cutler, ME",
                        "frequency": 24.0,
                        "latitude": 44.6449,
                        "longitude": -67.2816,
                        "enabled": True,
                        "power": "1000kW",
                        "country": "USA",
                        "callsign": "NAA",
                        "notes": "US Navy VLF transmitter"
                    },
                    {
                        "code": "DHO38", 
                        "name": "Burlage, Germany",
                        "frequency": 23.4,
                        "latitude": 53.0789,
                        "longitude": 7.615,
                        "enabled": True,
                        "power": "800kW",
                        "country": "Germany",
                        "callsign": "DHO38",
                        "notes": "German Navy VLF transmitter"
                    }
                ]
            },
            
            "data_sources": {
                "spaceweather_live": {
                    "enabled": True,
                    "url": "https://www.spaceweatherlive.com",
                    "api_key": "",
                    "update_interval": 600,
                    "timeout": 30,
                    "retry_count": 3,
                    "last_update": None
                },
                "noaa_swpc": {
                    "enabled": True,
                    "url": "https://services.swpc.noaa.gov/json/",
                    "api_key": "",
                    "update_interval": 300,
                    "timeout": 15,
                    "retry_count": 3,
                    "last_update": None
                }
            },
            
            "sampling": {
                "sample_rate": 48000,
                "buffer_size": 1024,
                "audio_device": "default",
                "channels": 1,
                "format": "float32",
                "gain": 1.0,
                "filter_enabled": True,
                "filter_low": 15000.0,
                "filter_high": 25000.0
            },
            
            "display": asdict(DisplayConfig()),
            "alerts": asdict(AlertConfig())
        }
        
        self.logger.info("Default configuration created")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any, auto_save: bool = None) -> None:
        """Set configuration value by dot-notation key - FIXED TO PREVENT RECURSION"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        
        should_auto_save = auto_save if auto_save is not None else self._auto_save
        if should_auto_save and not self._saving and self.has_changes():
            self.save_config(backup=False)
    
    def has_changes(self) -> bool:
        """Check if configuration has unsaved changes"""
        return self. config != self._original_config
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values"""
        self.create_default_config()
        self.save_config()
        self. logger.warning("Configuration reset to defaults")
    
    def get_observatory_config(self) -> ObservatoryConfig:
        """Get observatory configuration as dataclass"""
        obs_config = self.get('observatory', {})
        return ObservatoryConfig(**obs_config)
    
    def set_observatory_config(self, observatory: ObservatoryConfig) -> None:
        """Set observatory configuration"""
        self.set('observatory', asdict(observatory))
    
    def get_vlf_stations(self) -> List[VLFStation]:
        """Get VLF stations configuration"""
        stations_data = self.get('vlf_stations. default_stations', [])
        return [VLFStation(**station) for station in stations_data]
    
    def add_vlf_station(self, station: VLFStation) -> bool:
        """Add VLF station to configuration"""
        try:
            stations = self.get('vlf_stations.default_stations', [])
            
            if any(s.get('code') == station.code for s in stations):
                self.logger.warning(f"Station {station.code} already exists")
                return False
            
            stations.append(asdict(station))
            self. set('vlf_stations.default_stations', stations)
            
            self.logger.info(f"Added VLF station: {station. code}")
            return True
            
        except Exception as e:
            log_exception(e, f"Adding VLF station {station.code}")
            return False
    
    def remove_vlf_station(self, station_code: str) -> bool:
        """Remove VLF station from configuration"""
        try:
            stations = self.get('vlf_stations.default_stations', [])
            original_count = len(stations)
            
            stations = [s for s in stations if s.get('code') != station_code]
            
            if len(stations) < original_count:
                self. set('vlf_stations.default_stations', stations)
                self. logger.info(f"Removed VLF station: {station_code}")
                return True
            else:
                self.logger.warning(f"Station {station_code} not found")
                return False
                
        except Exception as e:
            log_exception(e, f"Removing VLF station {station_code}")
            return False
    
    def get_data_source_config(self, source_name: str) -> Optional[DataSourceConfig]:
        """Get data source configuration"""
        source_data = self.get(f'data_sources.{source_name}')
        if source_data:
            return DataSourceConfig(**source_data)
        return None
    
    def update_data_source(self, source_name: str, last_update: datetime) -> None:
        """Update data source last update timestamp"""
        self.set(f'data_sources.{source_name}. last_update', last_update. isoformat())
    
    def _validate_and_upgrade(self) -> None:
        """Validate and upgrade configuration structure"""
        self._validation_errors. clear()
        
        required_sections = ['application', 'observatory', 'vlf_stations', 'data_sources']
        for section in required_sections:
            if section not in self.config:
                self. config[section] = {}
                self._validation_errors.append(f"Missing section: {section}")
        
        obs = self.config. get('observatory', {})
        lat = obs.get('latitude', 0)
        lon = obs.get('longitude', 0)
        
        if not (-90 <= lat <= 90):
            self._validation_errors. append(f"Invalid latitude: {lat}")
        if not (-180 <= lon <= 180):
            self._validation_errors.append(f"Invalid longitude: {lon}")
        
        stations = self.get('vlf_stations. default_stations', [])
        for i, station in enumerate(stations):
            if not isinstance(station, dict):
                continue
            
            freq = station.get('frequency', 0)
            if not (10 <= freq <= 100):
                self._validation_errors.append(f"Station {i}: Invalid frequency {freq}")
        
        if self._validation_errors:
            self.logger.warning(f"Configuration validation found {len(self._validation_errors)} issues")
            for error in self._validation_errors:
                self.logger.warning(f"  - {error}")
    
    def get_validation_errors(self) -> List[str]:
        """Get list of validation errors"""
        return self._validation_errors. copy()
    
    def export_config(self, export_path: str) -> bool:
        """Export configuration to specified path"""
        try:
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            
            self.logger.info(f"Configuration exported to {export_path}")
            return True
            
        except Exception as e:
            log_exception(e, f"Exporting config to {export_path}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """Import configuration from specified path"""
        try:
            import_file = Path(import_path)
            if not import_file.exists():
                self.logger.error(f"Import file not found: {import_path}")
                return False
            
            with open(import_file, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            self. save_config(backup=True)
            
            self.config = imported_config
            self._validate_and_upgrade()
            
            self.save_config()
            
            self. logger.info(f"Configuration imported from {import_path}")
            return True
            
        except Exception as e:
            log_exception(e, f"Importing config from {import_path}")
            return False