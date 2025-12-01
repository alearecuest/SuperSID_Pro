"""
Space Weather API integration for SuperSID Pro
Handles data retrieval from spaceweatherlive.com and NOAA SWPC
"""

import aiohttp
import asyncio
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import re
from bs4 import BeautifulSoup

from core.logger import get_logger, log_exception, log_performance
from core.config_manager import ConfigManager

class FlareClass(Enum):
    """Solar flare classification"""
    A = "A"
    B = "B" 
    C = "C"
    M = "M"
    X = "X"

@dataclass
class SolarFlare:
    """Solar flare data"""
    timestamp: datetime
    flare_class: str  # e.g., "M2.1", "X1.5"
    peak_time: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None  # e.g., "N15W28"
    region: Optional[str] = None  # Active region number
    intensity: float = 0.0  # Numerical intensity

@dataclass
class GeomagnticData:
    """Geomagnetic activity data"""
    timestamp: datetime
    kp_index: float
    ap_index: Optional[int] = None
    dst_index: Optional[int] = None
    activity_level: str = "Quiet"  # Quiet, Unsettled, Active, Minor Storm, etc.  

@dataclass
class SolarWindData:
    """Solar wind parameters"""
    timestamp: datetime
    speed: float  # km/s
    density: float  # protons/cm³
    temperature: float  # K
    bz: float  # Magnetic field Z component (nT)
    bt: float  # Total magnetic field (nT)
    phi: float  # Phi angle (degrees)

@dataclass
class SpaceWeatherSummary:
    """Complete space weather summary"""
    timestamp: datetime
    solar_flares: List[SolarFlare] = field(default_factory=list)
    current_conditions: Dict[str, Any] = field(default_factory=dict)
    geomagnetic: Optional[GeomagnticData] = None
    solar_wind: Optional[SolarWindData] = None
    aurora_activity: Dict[str, float] = field(default_factory=dict)
    radio_conditions: Dict[str, str] = field(default_factory=dict)

class SpaceWeatherAPI:
    """Space weather data provider"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        
        # API endpoints (URLs actualizadas)
        self.noaa_base_url = "https://services. swpc.noaa.gov/json/"
        self.spaceweather_base_url = "https://www.spaceweatherlive.com"
        
        # Cache for reducing API calls
        self._cache = {}
        self._cache_timeout = 300  # 5 minutes
        
        # Session for HTTP requests
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._session:
            await self._session. close()
    
    async def get_current_conditions(self) -> SpaceWeatherSummary:
        """Get current space weather conditions"""
        try:
            # Get data from multiple sources in parallel
            tasks = [
                self. get_noaa_current_conditions(),
                self.get_spaceweatherlive_data(),
                self.get_recent_solar_flares(),
                self.get_geomagnetic_data(),
                self.get_solar_wind_data()
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results
            summary = SpaceWeatherSummary(timestamp=datetime.utcnow())
            
            # Process each result
            if not isinstance(results[0], Exception):
                summary.current_conditions. update(results[0])
            
            if not isinstance(results[1], Exception):
                summary.current_conditions.update(results[1])
            
            if not isinstance(results[2], Exception):
                summary.solar_flares = results[2]
            
            if not isinstance(results[3], Exception):
                summary.geomagnetic = results[3]
            
            if not isinstance(results[4], Exception):
                summary.solar_wind = results[4]
            
            return summary
            
        except Exception as e:
            log_exception(e, "Getting space weather conditions")
            # Return empty summary on error
            return SpaceWeatherSummary(timestamp=datetime.utcnow())
    
    async def get_noaa_current_conditions(self) -> Dict[str, Any]:
        """Get current conditions from NOAA SWPC"""
        try:
            # URLs actualizadas para NOAA SWPC
            endpoints = [
                "planetary_k_index. json",  # Cambió de 1m a datos principales
                "solar_wind_speed. json",    # URL simplificada
                "solar_wind_mag_field.json", # URL simplificada
                "goes_xrs.json",           # URL simplificada para X-ray flux
            ]
            
            conditions = {}
            
            for endpoint in endpoints:
                url = f"{self.noaa_base_url}{endpoint}"
                data = await self._fetch_json(url)
                
                if data and len(data) > 0:
                    latest = data[-1]  # Get most recent data point
                    
                    if "planetary_k_index" in endpoint:
                        conditions["kp_index"] = float(latest. get("kp_index", 0))
                        conditions["kp_time"] = latest.get("time_tag")
                    
                    elif "solar_wind_speed" in endpoint:
                        conditions["sw_speed"] = float(latest. get("speed", 0))
                        conditions["sw_speed_time"] = latest.get("time_tag")
                    
                    elif "solar_wind_mag_field" in endpoint:
                        conditions["bz"] = float(latest.get("bz_gsm", 0))
                        conditions["bt"] = float(latest.get("bt", 0))
                        conditions["mag_time"] = latest.get("time_tag")
                    
                    elif "goes_xrs" in endpoint:
                        conditions["xray_flux"] = latest.get("flux")
                        conditions["xray_time"] = latest.get("time_tag")
            
            return conditions
            
        except Exception as e:
            log_exception(e, "NOAA current conditions")
            return {}
    
    async def get_spaceweatherlive_data(self) -> Dict[str, Any]:
        """Scrape current data from spaceweatherlive.com"""
        try:
            url = f"{self.spaceweather_base_url}/en"
            html = await self._fetch_html(url)
            
            if not html:
                return {}
            
            soup = BeautifulSoup(html, 'html. parser')
            conditions = {}
            
            # Look for current values in the main page
            # This is website-specific scraping, may need updates
            
            # Try to find solar wind speed
            speed_elements = soup.find_all(text=re.compile(r'\d+\s*km/s'))
            if speed_elements:
                for elem in speed_elements:
                    match = re.search(r'(\d+)\s*km/s', elem)
                    if match:
                        conditions["swl_sw_speed"] = int(match.group(1))
                        break
            
            # Try to find Kp index
            kp_elements = soup.find_all(text=re.compile(r'Kp.*? (\d+\.  ?\d*)'))
            if kp_elements:
                for elem in kp_elements:
                    match = re.search(r'Kp.*?(\d+\. ?\d*)', elem)
                    if match:
                        conditions["swl_kp"] = float(match.group(1))
                        break
            
            # Try to find solar flux
            flux_elements = soup. find_all(text=re. compile(r'(\d+\. ?\d*)\s*sfu'))
            if flux_elements:
                for elem in flux_elements:
                    match = re.search(r'(\d+\.?\d*)\s*sfu', elem)
                    if match:
                        conditions["swl_solar_flux"] = float(match. group(1))
                        break
            
            conditions["swl_last_update"] = datetime.utcnow(). isoformat()
            
            return conditions
            
        except Exception as e:
            log_exception(e, "SpaceWeatherLive data scraping")
            return {}
    
    async def get_recent_solar_flares(self, hours: int = 24) -> List[SolarFlare]:
        """Get recent solar flares from NOAA"""
        try:
            # Intentar múltiples endpoints para X-ray data
            possible_endpoints = [
                "goes_xrs.json",
                "xray_5m.json",
                "goes_xrs_1m.json"
            ]
            
            data = None
            for endpoint in possible_endpoints:
                url = f"{self.noaa_base_url}{endpoint}"
                test_data = await self._fetch_json(url)
                if test_data:
                    data = test_data
                    break
            
            if not data:
                self.logger.warning("No X-ray data available from NOAA")
                return []
            
            flares = []
            current_time = datetime.utcnow()
            cutoff_time = current_time - timedelta(hours=hours)
            
            # Process X-ray data to detect flares
            for i, point in enumerate(data):
                try:
                    timestamp = datetime.fromisoformat(point["time_tag"]. replace('Z', '+00:00'))
                    
                    if timestamp < cutoff_time:
                        continue
                    
                    flux = float(point.get("flux", 0))
                    
                    # Detect flare based on flux level
                    flare_class = self._classify_xray_flux(flux)
                    
                    if flare_class and flare_class != "A":  # Only report B-class and above
                        # Check if this is a peak (simple peak detection)
                        is_peak = True
                        if i > 0 and i < len(data) - 1:
                            prev_flux = float(data[i-1].get("flux", 0))
                            next_flux = float(data[i+1].get("flux", 0))
                            is_peak = flux >= prev_flux and flux >= next_flux
                        
                        if is_peak:
                            intensity = flux * 1e6  # Convert to micro-watts per square meter
                            
                            flare = SolarFlare(
                                timestamp=timestamp,
                                flare_class=f"{flare_class}{intensity:.1f}",
                                peak_time=timestamp,
                                intensity=intensity
                            )
                            flares.append(flare)
                
                except (ValueError, KeyError) as e:
                    continue
            
            # Remove duplicate/overlapping flares (keep strongest in time window)
            filtered_flares = self._filter_duplicate_flares(flares)
            
            return sorted(filtered_flares, key=lambda x: x.timestamp, reverse=True)
            
        except Exception as e:
            log_exception(e, "Getting recent solar flares")
            return []
    
    def _classify_xray_flux(self, flux: float) -> Optional[str]:
        """Classify X-ray flux into flare classes"""
        if flux >= 1e-4:
            return "X"
        elif flux >= 1e-5:
            return "M"
        elif flux >= 1e-6:
            return "C"
        elif flux >= 1e-7:
            return "B"
        elif flux >= 1e-8:
            return "A"
        else:
            return None
    
    def _filter_duplicate_flares(self, flares: List[SolarFlare], window_minutes: int = 30) -> List[SolarFlare]:
        """Filter out duplicate flares within a time window"""
        if not flares:
            return []
        
        filtered = []
        window = timedelta(minutes=window_minutes)
        
        for flare in sorted(flares, key=lambda x: x.timestamp):
            # Check if this flare is too close to any existing flare
            is_duplicate = False
            
            for existing in filtered:
                if abs(flare.timestamp - existing.timestamp) < window:
                    # Keep the stronger flare
                    if flare.intensity > existing.intensity:
                        filtered.remove(existing)
                        filtered.append(flare)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered.append(flare)
        
        return filtered
    
    async def get_geomagnetic_data(self) -> Optional[GeomagnticData]:
        """Get current geomagnetic conditions"""
        try:
            # Intentar múltiples endpoints para Kp index
            possible_endpoints = [
                "planetary_k_index. json",
                "kp_index.json", 
                "planetary_k_index_1m. json"
            ]
            
            data = None
            for endpoint in possible_endpoints:
                url = f"{self.noaa_base_url}{endpoint}"
                test_data = await self._fetch_json(url)
                if test_data:
                    data = test_data
                    break
            
            if not data:
                self.logger.warning("No Kp index data available from NOAA")
                return None
            
            latest = data[-1]
            timestamp = datetime.fromisoformat(latest["time_tag"].replace('Z', '+00:00'))
            kp_index = float(latest. get("kp_index", 0))
            
            # Determine activity level
            activity_level = self._get_activity_level(kp_index)
            
            return GeomagnticData(
                timestamp=timestamp,
                kp_index=kp_index,
                activity_level=activity_level
            )
            
        except Exception as e:
            log_exception(e, "Getting geomagnetic data")
            return None
    
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
    
    async def get_solar_wind_data(self) -> Optional[SolarWindData]:
        """Get current solar wind parameters"""
        try:
            # Intentar múltiples endpoints para solar wind
            wind_endpoints = [
                ("solar_wind_speed.json", "speed"),
                ("solar_wind_mag_field.json", "magnetic"),
                ("solar_wind_plasma. json", "plasma")
            ]
            
            wind_data = {}
            
            for endpoint, data_type in wind_endpoints:
                url = f"{self.noaa_base_url}{endpoint}"
                data = await self._fetch_json(url)
                
                if data and len(data) > 0:
                    latest = data[-1]
                    
                    if data_type == "speed":
                        wind_data["speed"] = float(latest.get("speed", 0))
                        wind_data["timestamp"] = latest.get("time_tag")
                    
                    elif data_type == "magnetic":
                        wind_data["bz"] = float(latest.get("bz_gsm", 0))
                        wind_data["bt"] = float(latest.get("bt", 0))
                        wind_data["phi"] = float(latest.get("phi_gsm", 0))
                    
                    elif data_type == "plasma":
                        wind_data["density"] = float(latest.get("density", 0))
                        wind_data["temperature"] = float(latest.get("temperature", 0))
            
            if "timestamp" in wind_data:
                timestamp = datetime.fromisoformat(wind_data["timestamp"].replace('Z', '+00:00'))
                
                return SolarWindData(
                    timestamp=timestamp,
                    speed=wind_data. get("speed", 0),
                    density=wind_data. get("density", 0),
                    temperature=wind_data. get("temperature", 0),
                    bz=wind_data.get("bz", 0),
                    bt=wind_data.get("bt", 0),
                    phi=wind_data.get("phi", 0)
                )
            
            return None
            
        except Exception as e:
            log_exception(e, "Getting solar wind data")
            return None
    
    async def _fetch_json(self, url: str) -> Optional[Dict]:
        """Fetch JSON data from URL with caching"""
        # Check cache first
        cache_key = f"json_{url}"
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if datetime.utcnow() - cached_time < timedelta(seconds=self._cache_timeout):
                return cached_data
        
        try:
            if not self._session:
                raise Exception("No active session")
            
            async with self._session.get(url) as response:
                if response. status == 200:
                    data = await response.json()
                    
                    # Cache the result
                    self._cache[cache_key] = (datetime.utcnow(), data)
                    
                    return data
                else:
                    self.logger.warning(f"HTTP {response.status} for {url}")
                    return None
                    
        except Exception as e:
            log_exception(e, f"Fetching JSON from {url}")
            return None
    
    async def _fetch_html(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL with caching"""
        # Check cache first
        cache_key = f"html_{url}"
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if datetime.utcnow() - cached_time < timedelta(seconds=self._cache_timeout):
                return cached_data
        
        try:
            if not self._session:
                raise Exception("No active session")
            
            async with self._session.get(url) as response:
                if response.status == 200:
                    text = await response.text()
                    
                    # Cache the result
                    self._cache[cache_key] = (datetime.utcnow(), text)
                    
                    return text
                else:
                    self.logger.warning(f"HTTP {response.status} for {url}")
                    return None
                    
        except Exception as e:
            log_exception(e, f"Fetching HTML from {url}")
            return None

# Convenience functions for synchronous usage
def get_space_weather_sync(config_manager: ConfigManager) -> SpaceWeatherSummary:
    """Get space weather data synchronously"""
    async def _get_data():
        async with SpaceWeatherAPI(config_manager) as api:
            return await api.get_current_conditions()
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(_get_data())