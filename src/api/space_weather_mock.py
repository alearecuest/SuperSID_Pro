"""
Mock/Offline data provider for Space Weather API
Provides simulated data for development and testing
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import asdict

from api.space_weather_api import SpaceWeatherSummary, SolarFlare, GeomagnticData, SolarWindData
from core.logger import get_logger

class MockSpaceWeatherAPI:
    """Mock space weather API for offline development"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        self.logger.info("Using MOCK Space Weather API (offline mode)")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def get_current_conditions(self) -> SpaceWeatherSummary:
        """Get mock space weather conditions"""
        try:
            current_time = datetime.utcnow()
            
            # Mock geomagnetic data
            kp_index = random.uniform(0.0, 6.0)
            geomagnetic = GeomagnticData(
                timestamp=current_time,
                kp_index=kp_index,
                activity_level=self._get_activity_level(kp_index)
            )
            
            solar_wind = SolarWindData(
                timestamp=current_time,
                speed=random.uniform(300, 700),  # km/s
                density=random.uniform(1.0, 15.0),  # protons/cm³
                temperature=random.uniform(50000, 200000),  # K
                bz=random.uniform(-15.0, 10.0),  # nT
                bt=random.uniform(2.0, 20.0),  # nT
                phi=random.uniform(-180, 180)  # degrees
            )
            
            current_conditions = {
                "kp_index": kp_index,
                "kp_time": current_time. isoformat(),
                "sw_speed": solar_wind.speed,
                "sw_speed_time": current_time.isoformat(),
                "bz": solar_wind.bz,
                "bt": solar_wind.bt,
                "mag_time": current_time.isoformat(),
                "xray_flux": f"{random.uniform(1e-9, 1e-5):.2e}",
                "xray_time": current_time.isoformat(),
                "swl_sw_speed": int(solar_wind.speed),
                "swl_kp": kp_index,
                "swl_solar_flux": random.uniform(70, 150),
                "swl_last_update": current_time.isoformat()
            }
            
            solar_flares = self._generate_mock_flares()
            
            summary = SpaceWeatherSummary(
                timestamp=current_time,
                solar_flares=solar_flares,
                current_conditions=current_conditions,
                geomagnetic=geomagnetic,
                solar_wind=solar_wind
            )
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating mock data: {e}")
            return SpaceWeatherSummary(timestamp=datetime.utcnow())
    
    def _get_activity_level(self, kp_index: float) -> str:
        """Get geomagnetic activity level from Kp index"""
        if kp_index >= 9:
            return "Extreme Storm"
        elif kp_index >= 8:
            return "Severe Storm"
        elif kp_index >= 7:
            return "Strong Storm"
        elif kp_index >= 6:
            return "Moderate Storm"
        elif kp_index >= 5:
            return "Minor Storm"
        elif kp_index >= 4:
            return "Active"
        elif kp_index >= 3:
            return "Unsettled"
        else:
            return "Quiet"
    
    def _generate_mock_flares(self) -> List[SolarFlare]:
        """Generate mock solar flares"""
        flares = []
        current_time = datetime.utcnow()
        
        num_flares = random.randint(0, 3)
        
        for i in range(num_flares):
            flare_time = current_time - timedelta(hours=random.uniform(0, 24))
            
            flare_classes = ["A", "B", "C", "M", "X"]
            weights = [0.4, 0.3, 0.2, 0.08, 0.02]
            flare_class = random.choices(flare_classes, weights=weights)[0]
            
            magnitude = random. uniform(1.0, 9.9)
            
            locations = ["N15W28", "S20E35", "N08W45", "S12E12", "N25W60"]
            location = random.choice(locations)
            
            flare = SolarFlare(
                timestamp=flare_time,
                flare_class=f"{flare_class}{magnitude:.1f}",
                peak_time=flare_time,
                location=location,
                intensity=magnitude
            )
            
            flares.append(flare)
        
        return sorted(flares, key=lambda x: x.timestamp, reverse=True)

def create_space_weather_api(config_manager, force_mock=False):
    """Create appropriate space weather API instance"""
    
    use_mock = force_mock or config_manager.get('development. use_mock_data', False)
    
    if use_mock:
        return MockSpaceWeatherAPI(config_manager)
    else:
        try:
            from api.space_weather_api import SpaceWeatherAPI
            return SpaceWeatherAPI(config_manager)
        except Exception:
            get_logger(__name__).warning("Falling back to mock space weather API")
            return MockSpaceWeatherAPI(config_manager)