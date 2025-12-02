"""
Real-time data storage for VLF measurements
"""
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path
from core.logger import get_logger

@dataclass
class VLFMeasurement:
    """VLF measurement data point"""
    timestamp: datetime
    station_id: str
    frequency: float
    amplitude: float
    phase: float
    
class RealtimeStorage:
    """Real-time VLF data storage system"""
    
    def __init__(self, db_path: str = "data/vlf_realtime.db"):
        self. db_path = Path(db_path)
        self.logger = get_logger(__name__)
        self._lock = threading.Lock()
        
        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
    def _init_database(self):
        """Initialize the real-time database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vlf_measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    station_id TEXT NOT NULL,
                    frequency REAL NOT NULL,
                    amplitude REAL NOT NULL,
                    phase REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp_station 
                ON vlf_measurements(timestamp, station_id)
            """)
            
        self.logger.info("Real-time database initialized")
        
    def store_measurement(self, measurement: VLFMeasurement):
        """Store a single VLF measurement"""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT INTO vlf_measurements 
                        (timestamp, station_id, frequency, amplitude, phase)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        measurement.timestamp,
                        measurement.station_id,
                        measurement.frequency,
                        measurement.amplitude,
                        measurement.phase
                    ))
                    
            except Exception as e:
                self.logger.error(f"Failed to store measurement: {e}")
                
    def store_batch(self, measurements: List[VLFMeasurement]):
        """Store multiple measurements efficiently"""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    data = [
                        (m.timestamp, m.station_id, m.frequency, m.amplitude, m.phase)
                        for m in measurements
                    ]
                    
                    conn. executemany("""
                        INSERT INTO vlf_measurements 
                        (timestamp, station_id, frequency, amplitude, phase)
                        VALUES (?, ?, ?, ?, ?)
                    """, data)
                    
                self.logger.debug(f"Stored {len(measurements)} measurements")
                
            except Exception as e:
                self.logger.error(f"Failed to store batch: {e}")
                
    def get_recent_data(self, station_id: str, minutes: int = 60) -> List[VLFMeasurement]:
        """Get recent measurements for a station"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                cursor = conn.execute("""
                    SELECT timestamp, station_id, frequency, amplitude, phase
                    FROM vlf_measurements
                    WHERE station_id = ? 
                    AND timestamp > datetime('now', '-{} minutes')
                    ORDER BY timestamp DESC
                """.format(minutes), (station_id,))
                
                measurements = []
                for row in cursor:
                    measurements.append(VLFMeasurement(
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        station_id=row['station_id'],
                        frequency=row['frequency'],
                        amplitude=row['amplitude'],
                        phase=row['phase']
                    ))
                    
                return measurements
                
        except Exception as e:
            self.logger.error(f"Failed to get recent data: {e}")
            return []
            
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old measurements to manage database size"""
        try:
            with sqlite3.connect(self. db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM vlf_measurements
                    WHERE timestamp < datetime('now', '-{} days')
                """.format(days_to_keep))
                
                deleted_count = cursor.rowcount
                if deleted_count > 0:
                    self.logger.info(f"Cleaned up {deleted_count} old measurements")
                    
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
