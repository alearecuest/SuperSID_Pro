"""
VLF Station Database Management for SuperSID Pro
Handles worldwide VLF transmitter database with KML import and geographic calculations
"""

import xml.etree.ElementTree as ET
import json
import math
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from geopy.distance import geodesic
import requests

from core.config_manager import ConfigManager, VLFStation
from core.logger import get_logger, log_exception

@dataclass
class VLFStationExtended:
    """Extended VLF station with additional metadata"""
    code: str
    name: str
    frequency: float
    latitude: float
    longitude: float
    enabled: bool = True
    power: str = ""
    country: str = ""
    callsign: str = ""
    notes: str = ""
    
    # Extended fields
    power_watts: Optional[int] = None
    antenna_type: str = ""
    operational_status: str = "active"  # active, inactive, unknown
    time_signals: bool = False
    owner: str = ""
    distance_km: Optional[float] = None  # Distance from observatory
    azimuth: Optional[float] = None      # Bearing from observatory
    signal_strength: Optional[float] = None  # Estimated signal strength
    priority: int = 5  # 1=highest, 10=lowest
    last_updated: Optional[str] = None

@dataclass
class VLFDatabaseInfo:
    """Database information and statistics"""
    total_stations: int = 0
    active_stations: int = 0
    countries: List[str] = None
    frequency_range: Tuple[float, float] = (0, 0)
    last_updated: Optional[str] = None
    data_sources: List[str] = None

class VLFDatabase:
    """Comprehensive VLF station database manager"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        
        # Database file
        self.db_path = Path("data/vlf_stations.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Observatory location (for distance calculations)
        self. observatory_lat = None
        self.observatory_lon = None
        
        # Initialize database
        self. init_database()
        self.load_observatory_location()
        
        # KML namespaces
        self.kml_namespaces = {
            'kml': 'http://earth.google.com/kml/2.2',
            'gx': 'http://www. google.com/kml/ext/2.2'
        }
        
        self.logger.info("VLF Database manager initialized")
    
    def init_database(self):
        """Initialize SQLite database for VLF stations"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn. cursor()
                
                # Create main stations table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vlf_stations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        code TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        frequency REAL NOT NULL,
                        latitude REAL NOT NULL,
                        longitude REAL NOT NULL,
                        enabled BOOLEAN DEFAULT 1,
                        power TEXT DEFAULT '',
                        power_watts INTEGER,
                        country TEXT DEFAULT '',
                        callsign TEXT DEFAULT '',
                        notes TEXT DEFAULT '',
                        antenna_type TEXT DEFAULT '',
                        operational_status TEXT DEFAULT 'active',
                        time_signals BOOLEAN DEFAULT 0,
                        owner TEXT DEFAULT '',
                        distance_km REAL,
                        azimuth REAL,
                        signal_strength REAL,
                        priority INTEGER DEFAULT 5,
                        last_updated TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create index for efficient queries
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_frequency ON vlf_stations(frequency)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_country ON vlf_stations(country)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_enabled ON vlf_stations(enabled)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_distance ON vlf_stations(distance_km)")
                
                # Create metadata table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS database_metadata (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                
            self.logger.info("VLF database initialized successfully")
            
        except Exception as e:
            log_exception(e, "Initializing VLF database")
            raise
    
    def load_observatory_location(self):
        """Load observatory location for distance calculations"""
        obs_config = self.config_manager.get_observatory_config()
        self.observatory_lat = obs_config.latitude
        self.observatory_lon = obs_config.longitude
        
        if self.observatory_lat and self.observatory_lon:
            self.logger.info(f"Observatory location: {self.observatory_lat:.3f}, {self.observatory_lon:.3f}")
        else:
            self.logger. warning("Observatory location not set - distance calculations unavailable")
    
    def import_from_kml(self, kml_file: str, source_type: str = "vlf") -> int:
        """Import VLF stations from KML file"""
        kml_path = Path(kml_file)
        if not kml_path.exists():
            self.logger.error(f"KML file not found: {kml_file}")
            return 0
        
        try:
            self.logger.info(f"Importing VLF stations from {kml_file}")
            
            # Parse KML file
            tree = ET.parse(kml_path)
            root = tree.getroot()
            
            # Find all placemark elements
            placemarks = []
            for elem in root.iter():
                if elem.tag.endswith("}Placemark") or elem.tag == "Placemark":
                    placemarks.append(elem)
            
            imported_count = 0
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for placemark in placemarks:
                    try:
                        station = self._parse_kml_placemark(placemark, source_type)
                        if station:
                            # Calculate distance if observatory location is set
                            if self.observatory_lat and self.observatory_lon:
                                station.distance_km, station.azimuth = self._calculate_distance_azimuth(
                                    station.latitude, station.longitude
                                )
                            
                            # Insert or update station
                            self._insert_or_update_station(cursor, station)
                            imported_count += 1
                            
                    except Exception as e:
                        self.logger.warning(f"Error parsing placemark: {e}")
                        continue
                
                conn.commit()
            
            self.logger.info(f"Imported {imported_count} stations from {kml_file}")
            self._update_database_metadata()
            
            return imported_count
            
        except Exception as e:
            log_exception(e, f"Importing from KML file {kml_file}")
            return 0
    
    def _parse_kml_placemark(self, placemark: ET.Element, source_type: str) -> Optional[VLFStationExtended]:
        """Parse a single KML placemark into a VLF station"""
        try:
            # Get name
            name_elem = None
            for child in placemark:
                if child.tag.endswith('}name') or child.tag == 'name':
                    name_elem = child
                    break
            if name_elem is None:
                return None
            name = name_elem.text.strip()
            
            # Get coordinates
            coords_elem = None
            # Find Point first, then coordinates inside it
            point_elem = None
            for child in placemark:
                if child.tag.endswith('}Point') or child.tag == 'Point':
                    point_elem = child
                    break
            if point_elem is not None:
                for child in point_elem:
                    if child.tag.endswith('}coordinates') or child.tag == 'coordinates':
                        coords_elem = child
                        break
            if coords_elem is None:
                return None
                
            coords = coords_elem.text.strip(). split(',')
            if len(coords) < 2:
                return None
                
            longitude = float(coords[0])
            latitude = float(coords[1])
            
            # Get description (contains most metadata)
            desc_elem = None
            for child in placemark:
                if child.tag.endswith('}description') or child. tag == 'description':
                    desc_elem = child
                    break
            description = desc_elem.text if desc_elem is not None else ""
            
            # Parse metadata from description or name
            metadata = self._parse_station_metadata(name, description, source_type)
            
            station = VLFStationExtended(
                code=metadata.get('code', name[:10]. upper(). replace(' ', '')),
                name=name,
                frequency=metadata.get('frequency', 0.0),
                latitude=latitude,
                longitude=longitude,
                enabled=True,
                power=metadata.get('power', ''),
                power_watts=metadata.get('power_watts'),
                country=metadata.get('country', ''),
                callsign=metadata.get('callsign', ''),
                notes=description[:500] if description else '',  # Limit notes length
                antenna_type=metadata. get('antenna_type', ''),
                operational_status=metadata. get('status', 'active'),
                time_signals=metadata.get('time_signals', False),
                owner=metadata.get('owner', ''),
                priority=5,
                last_updated=datetime.now().isoformat()
            )
            
            return station
            
        except Exception as e:
            self.logger.warning(f"Error parsing placemark: {e}")
            return None
    
    def _parse_station_metadata(self, name: str, description: str, source_type: str) -> Dict[str, Any]:
        """Parse station metadata from name and description"""
        metadata = {}
        
        # Common patterns for different data
        text = f"{name} {description}".lower()
        
        # Extract frequency
        import re
        freq_patterns = [
            r'(\d+(?:\.\d+)?)\s*khz',
            r'(\d+(?:\.\d+)?)\s*kc',
            r'frequency[:\s]+(\d+(?:\.\d+)?)',
        ]
        
        for pattern in freq_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    freq = float(match.group(1))
                    # Convert to kHz if needed
                    if freq > 1000:  # Assume Hz if > 1000
                        freq = freq / 1000
                    metadata['frequency'] = freq
                    break
                except ValueError:
                    continue
        
        # Extract power
        power_patterns = [
            r'(\d+(?:\.\d+)?)\s*kw',
            r'(\d+(?:\.\d+)?)\s*kilowatt',
            r'power[:\s]+(\d+(?:\.\d+)?)',
        ]
        
        for pattern in power_patterns:
            match = re. search(pattern, text)
            if match:
                try:
                    power_val = float(match.group(1))
                    metadata['power'] = f"{power_val}kW"
                    metadata['power_watts'] = int(power_val * 1000)
                    break
                except ValueError:
                    continue
        
        # Extract country (basic patterns)
        country_patterns = [
            r'country[:\s]+([a-zA-Z\s]+)',
            r'([a-zA-Z]+)\s+navy',
            r'([a-zA-Z]+)\s+military',
        ]
        
        for pattern in country_patterns:
            match = re.search(pattern, text)
            if match:
                country = match.group(1).strip(). title()
                if len(country) > 2:
                    metadata['country'] = country
                    break
        
        # Extract callsign
        callsign_patterns = [
            r'\b([A-Z]{3,6})\b',  # 3-6 uppercase letters
            r'call[:\s]*([A-Z0-9]+)',
        ]
        
        for pattern in callsign_patterns:
            match = re.search(pattern, name)  # Search in name first
            if match:
                callsign = match.group(1)
                if 3 <= len(callsign) <= 6:
                    metadata['callsign'] = callsign
                    metadata['code'] = callsign
                    break
        
        # Detect time signals
        if any(word in text for word in ['time', 'clock', 'ntp', 'wwvb', 'msf', 'dcf']):
            metadata['time_signals'] = True
        
        # Detect operational status
        if any(word in text for word in ['inactive', 'closed', 'discontinued']):
            metadata['status'] = 'inactive'
        elif any(word in text for word in ['experimental', 'test']):
            metadata['status'] = 'experimental'
        
        return metadata
    
    def _calculate_distance_azimuth(self, station_lat: float, station_lon: float) -> Tuple[float, float]:
        """Calculate distance and azimuth from observatory to station"""
        if not self. observatory_lat or not self.observatory_lon:
            return None, None
        
        # Calculate distance using geopy
        obs_point = (self.observatory_lat, self.observatory_lon)
        station_point = (station_lat, station_lon)
        distance = geodesic(obs_point, station_point).kilometers
        
        # Calculate azimuth (bearing)
        azimuth = self._calculate_bearing(
            self.observatory_lat, self.observatory_lon,
            station_lat, station_lon
        )
        
        return distance, azimuth
    
    def _calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate bearing between two points"""
        lat1, lon1, lat2, lon2 = map(math. radians, [lat1, lon1, lat2, lon2])
        
        dlon = lon2 - lon1
        
        y = math.sin(dlon) * math.cos(lat2)
        x = (math.cos(lat1) * math.sin(lat2) - 
             math.sin(lat1) * math.cos(lat2) * math.cos(dlon))
        
        bearing = math.atan2(y, x)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360
        
        return bearing
    
    def _insert_or_update_station(self, cursor: sqlite3.Cursor, station: VLFStationExtended):
        """Insert or update station in database"""
        try:
            # Try to update first
            update_sql = """
                UPDATE vlf_stations SET
                    name=?, frequency=?, latitude=?, longitude=?, enabled=?,
                    power=?, power_watts=?, country=?, callsign=?, notes=?,
                    antenna_type=?, operational_status=?, time_signals=?, owner=?,
                    distance_km=?, azimuth=?, priority=?, last_updated=?  
                WHERE code=? 
            """
            
            cursor.execute(update_sql, (
                station.name, station.frequency, station.latitude, station.longitude,
                station. enabled, station.power, station. power_watts, station.country,
                station.callsign, station.notes, station.antenna_type,
                station.operational_status, station.time_signals, station.owner,
                station. distance_km, station.azimuth, station.priority,
                station.last_updated, station.code
            ))
            
            if cursor.rowcount == 0:
                # Insert new station
                insert_sql = """
                    INSERT INTO vlf_stations (
                        code, name, frequency, latitude, longitude, enabled,
                        power, power_watts, country, callsign, notes,
                        antenna_type, operational_status, time_signals, owner,
                        distance_km, azimuth, priority, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                cursor.execute(insert_sql, (
                    station.code, station.name, station.frequency, station.latitude,
                    station.longitude, station.enabled, station.power, station.power_watts,
                    station.country, station.callsign, station.notes, station.antenna_type,
                    station.operational_status, station.time_signals, station.owner,
                    station.distance_km, station.azimuth, station.priority,
                    station.last_updated
                ))
                
        except sqlite3.IntegrityError:
            # Station already exists with same code, update it
            self.logger.debug(f"Updating existing station: {station.code}")
    
    def get_all_stations(self) -> List[VLFStationExtended]:
        """Get all stations from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT code, name, frequency, latitude, longitude, enabled,
                           power, power_watts, country, callsign, notes,
                           antenna_type, operational_status, time_signals, owner,
                           distance_km, azimuth, signal_strength, priority, last_updated
                    FROM vlf_stations
                    ORDER BY priority ASC, distance_km ASC NULLS LAST
                """)
                
                stations = []
                for row in cursor.fetchall():
                    station = VLFStationExtended(
                        code=row[0], name=row[1], frequency=row[2],
                        latitude=row[3], longitude=row[4], enabled=bool(row[5]),
                        power=row[6] or "", power_watts=row[7],
                        country=row[8] or "", callsign=row[9] or "", notes=row[10] or "",
                        antenna_type=row[11] or "", operational_status=row[12] or "active",
                        time_signals=bool(row[13]), owner=row[14] or "",
                        distance_km=row[15], azimuth=row[16], signal_strength=row[17],
                        priority=row[18] or 5, last_updated=row[19]
                    )
                    stations.append(station)
                
                return stations
                
        except Exception as e:
            log_exception(e, "Getting all VLF stations")
            return []
    
    def filter_stations(self, 
                       frequency_min: float = None, frequency_max: float = None,
                       max_distance_km: float = None, countries: List[str] = None,
                       operational_only: bool = True, enabled_only: bool = False,
                       limit: int = None) -> List[VLFStationExtended]:
        """Filter stations by various criteria"""
        try:
            conditions = []
            params = []
            
            # Base query
            query = """
                SELECT code, name, frequency, latitude, longitude, enabled,
                       power, power_watts, country, callsign, notes,
                       antenna_type, operational_status, time_signals, owner,
                       distance_km, azimuth, signal_strength, priority, last_updated
                FROM vlf_stations WHERE 1=1
            """
            
            # Add filters
            if frequency_min is not None:
                conditions.append("frequency >= ?")
                params. append(frequency_min)
                
            if frequency_max is not None:
                conditions.append("frequency <= ?")
                params.append(frequency_max)
                
            if max_distance_km is not None:
                conditions.append("(distance_km <= ? OR distance_km IS NULL)")
                params. append(max_distance_km)
                
            if countries:
                country_placeholders = ",".join(["?" for _ in countries])
                conditions.append(f"country IN ({country_placeholders})")
                params.extend(countries)
                
            if operational_only:
                conditions.append("operational_status = 'active'")
                
            if enabled_only:
                conditions.append("enabled = 1")
            
            # Add conditions to query
            if conditions:
                query += " AND " + " AND ".join(conditions)
            
            # Add ordering and limit
            query += " ORDER BY priority ASC, distance_km ASC NULLS LAST"
            if limit:
                query += f" LIMIT {limit}"
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                stations = []
                for row in cursor.fetchall():
                    station = VLFStationExtended(
                        code=row[0], name=row[1], frequency=row[2],
                        latitude=row[3], longitude=row[4], enabled=bool(row[5]),
                        power=row[6] or "", power_watts=row[7],
                        country=row[8] or "", callsign=row[9] or "", notes=row[10] or "",
                        antenna_type=row[11] or "", operational_status=row[12] or "active",
                        time_signals=bool(row[13]), owner=row[14] or "",
                        distance_km=row[15], azimuth=row[16], signal_strength=row[17],
                        priority=row[18] or 5, last_updated=row[19]
                    )
                    stations. append(station)
                
                return stations
                
        except Exception as e:
            log_exception(e, "Filtering VLF stations")
            return []
    
    def get_recommended_stations(self, max_stations: int = 10) -> List[VLFStationExtended]:
        """Get recommended stations based on distance and signal strength"""
        self.load_observatory_location()  # Refresh location
        
        # Recalculate distances if observatory location changed
        if self.observatory_lat and self.observatory_lon:
            self._update_all_distances()
        
        # Get stations with good coverage
        recommended = self.filter_stations(
            frequency_min=15.0,  # VLF range
            frequency_max=30.0,
            max_distance_km=8000,  # Reasonable VLF propagation distance
            operational_only=True,
            limit=max_stations * 2  # Get more to filter later
        )
        
        # Score stations based on multiple criteria
        scored_stations = []
        for station in recommended:
            score = self._calculate_station_score(station)
            scored_stations.append((score, station))
        
        # Sort by score (higher is better) and return top stations
        scored_stations.sort(reverse=True)
        return [station for score, station in scored_stations[:max_stations]]
    
    def _calculate_station_score(self, station: VLFStationExtended) -> float:
        """Calculate a recommendation score for a station"""
        score = 100.0  # Base score
        
        # Distance penalty (closer is better)
        if station.distance_km:
            if station.distance_km < 2000:
                score += 20
            elif station.distance_km < 5000:
                score += 10
            elif station.distance_km > 8000:
                score -= 20
        
        # Power bonus
        if station.power_watts:
            if station.power_watts >= 1000000:  # 1 MW+
                score += 30
            elif station.power_watts >= 500000:  # 500 kW+
                score += 20
            elif station.power_watts >= 100000:  # 100 kW+
                score += 10
        
        # Frequency preference (good VLF monitoring frequencies)
        good_frequencies = [19.8, 20.9, 23.4, 24.0, 25.0]  # Common VLF frequencies
        if any(abs(station.frequency - freq) < 0.5 for freq in good_frequencies):
            score += 15
        
        # Priority bonus (lower number = higher priority)
        score += (10 - station.priority)
        
        # Time signal bonus (often stable and well-maintained)
        if station.time_signals:
            score += 10
        
        # Known good stations bonus
        well_known = ['NAA', 'DHO38', 'ICV', 'GQD', 'NLK', 'NWC', 'JJI', 'MSF', 'DCF77']
        if station.callsign in well_known or station.code in well_known:
            score += 25
        
        return score
    
    def _update_all_distances(self):
        """Recalculate distances for all stations"""
        if not self.observatory_lat or not self.observatory_lon:
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn. cursor()
                
                # Get all stations
                cursor.execute("SELECT id, latitude, longitude FROM vlf_stations")
                stations = cursor.fetchall()
                
                for station_id, lat, lon in stations:
                    distance, azimuth = self._calculate_distance_azimuth(lat, lon)
                    
                    cursor.execute("""
                        UPDATE vlf_stations SET distance_km=?, azimuth=?  WHERE id=?
                    """, (distance, azimuth, station_id))
                
                conn.commit()
                
            self.logger.info("Updated distances for all stations")
            
        except Exception as e:
            log_exception(e, "Updating station distances")
    
    def get_database_info(self) -> VLFDatabaseInfo:
        """Get database statistics and information"""
        try:
            with sqlite3.connect(self. db_path) as conn:
                cursor = conn.cursor()
                
                # Total stations
                cursor.execute("SELECT COUNT(*) FROM vlf_stations")
                total_stations = cursor.fetchone()[0]
                
                # Active stations
                cursor.execute("SELECT COUNT(*) FROM vlf_stations WHERE operational_status='active'")
                active_stations = cursor.fetchone()[0]
                
                # Countries
                cursor.execute("SELECT DISTINCT country FROM vlf_stations WHERE country != '' ORDER BY country")
                countries = [row[0] for row in cursor.fetchall()]
                
                # Frequency range
                cursor.execute("SELECT MIN(frequency), MAX(frequency) FROM vlf_stations WHERE frequency > 0")
                freq_result = cursor.fetchone()
                frequency_range = (freq_result[0] or 0, freq_result[1] or 0)
                
                # Last update
                cursor.execute("SELECT value FROM database_metadata WHERE key='last_update'")
                last_update_result = cursor.fetchone()
                last_updated = last_update_result[0] if last_update_result else None
                
                return VLFDatabaseInfo(
                    total_stations=total_stations,
                    active_stations=active_stations,
                    countries=countries,
                    frequency_range=frequency_range,
                    last_updated=last_updated,
                    data_sources=["KML Import", "Manual Entry"]
                )
                
        except Exception as e:
            log_exception(e, "Getting database info")
            return VLFDatabaseInfo()
    
    def _update_database_metadata(self):
        """Update database metadata"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO database_metadata (key, value, updated_at)
                    VALUES ('last_update', ?, CURRENT_TIMESTAMP)
                """, (datetime.now().isoformat(),))
                
                conn.commit()
                
        except Exception as e:
            log_exception(e, "Updating database metadata")
    
    def export_stations_config(self) -> List[VLFStation]:
        """Export stations in format compatible with config manager"""
        stations = self.get_all_stations()
        
        config_stations = []
        for station in stations:
            config_station = VLFStation(
                code=station.code,
                name=station.name,
                frequency=station.frequency,
                latitude=station.latitude,
                longitude=station.longitude,
                enabled=station.enabled,
                power=station.power,
                country=station.country,
                callsign=station.callsign,
                notes=station.notes[:100] if station.notes else ""  # Limit for config
            )
            config_stations.append(config_station)
        
        return config_stations
    
    def sync_with_config_manager(self):
        """Synchronize enabled stations with config manager"""
        try:
            # Get current enabled stations from database
            enabled_stations = self.filter_stations(enabled_only=True)
            
            # Convert to config format
            config_stations = []
            for station in enabled_stations:
                config_station = VLFStation(
                    code=station.code,
                    name=station.name,
                    frequency=station.frequency,
                    latitude=station. latitude,
                    longitude=station.longitude,
                    enabled=station.enabled,
                    power=station.power,
                    country=station.country,
                    callsign=station.callsign,
                    notes=station.notes[:100] if station.notes else ""
                )
                config_stations. append(config_station)
            
            # Update config manager
            stations_data = [asdict(station) for station in config_stations]
            self.config_manager. set('vlf_stations.default_stations', stations_data)
            
            self. logger.info(f"Synchronized {len(config_stations)} enabled stations with config")
            
        except Exception as e:
            log_exception(e, "Synchronizing with config manager")