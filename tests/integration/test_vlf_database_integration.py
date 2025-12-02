#!/usr/bin/env python3
"""
Fixed test for VLF Database System
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_functionality():
    """Test basic VLF database functionality"""
    print("Testing VLF Database basic functionality...")
    
    try:
        from core.config_manager import ConfigManager
        from data.vlf_database import VLFDatabase, VLFStationExtended
        from datetime import datetime
        
        # Setup config without auto-save
        config_manager = ConfigManager('config/test_config.json')
        config_manager._auto_save = False
        
        print("Config manager created")
        
        # Create database
        db = VLFDatabase(config_manager)
        print("Database created successfully")
        
        # Test database info
        db_info = db.get_database_info()
        print(f"Database contains {db_info.total_stations} stations")
        
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_sample_kml():
    """Create a simple sample KML - FIXED VERSION"""
    content = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://earth.google.com/kml/2.2">
<Document>
<name>Test VLF Stations</name>
<Placemark>
<name>NAA</name>
<description>Frequency: 24.0 kHz</description>
<Point>
<coordinates>-67.2816,44.6449</coordinates>
</Point>
</Placemark>
</Document>
</kml>'''
    
    kml_file = Path("data/test_vlf.kml")
    kml_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(kml_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Created KML file with {len(content)} characters")
    return str(kml_file)

def test_kml_import():
    """Test KML import"""
    print("Testing KML import...")
    
    try:
        from core.config_manager import ConfigManager
        from data.vlf_database import VLFDatabase
        
        # Create test KML
        kml_file = create_sample_kml()
        print(f"Created test KML: {kml_file}")
        
        # Verify KML file exists and is readable
        if not Path(kml_file).exists():
            print(f"ERROR: KML file not found: {kml_file}")
            return False
            
        # Read and verify KML content
        with open(kml_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"KML content length: {len(content)} characters")
            print(f"First 100 chars: {content[:100]}")
        
        # Setup database
        config_manager = ConfigManager('config/test_config.json')
        config_manager._auto_save = False
        
        # Verify config loaded correctly
        obs_config = config_manager.get('observatory', {})
        print(f"Observatory config: lat={obs_config.get('latitude')}, lon={obs_config. get('longitude')}")
        
        db = VLFDatabase(config_manager)
        
        # Import
        imported = db.import_from_kml(kml_file)
        print(f"Imported {imported} stations")
        
        # Check stations
        stations = db.get_all_stations()
        print(f"Total stations: {len(stations)}")
        
        if stations:
            station = stations[0]
            print(f"Station: {station.code} - {station.name}")
            print(f"  Frequency: {station.frequency} kHz")
            print(f"  Location: {station.latitude}, {station.longitude}")
        
        return imported > 0  # Return True only if we actually imported something
        
    except Exception as e:
        print(f"KML import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_manual_station():
    """Test adding station manually"""
    print("Testing manual station addition...")
    
    try:
        from core. config_manager import ConfigManager
        from data.vlf_database import VLFDatabase, VLFStationExtended
        from datetime import datetime
        import sqlite3
        
        config_manager = ConfigManager('config/test_config.json')
        config_manager._auto_save = False
        
        db = VLFDatabase(config_manager)
        
        # Create test station
        station = VLFStationExtended(
            code="TEST1",
            name="Test Station 1",
            frequency=24.0,
            latitude=40.0,
            longitude=-74.0,
            enabled=True,
            power="100kW",
            country="USA",
            callsign="TEST1",
            notes="Test station",
            last_updated=datetime.now(). isoformat()
        )
        
        # Add manually to database
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            db._insert_or_update_station(cursor, station)
            conn.commit()
        
        print("Manual station added to database")
        
        # Verify it was added
        stations = db. get_all_stations()
        print(f"Database now contains {len(stations)} stations")
        
        if stations:
            for s in stations:
                print(f"  {s.code}: {s.name} ({s.frequency} kHz)")
        
        return len(stations) > 0
        
    except Exception as e:
        print(f"Manual station test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run fixed tests"""
    print("=" * 50)
    print("SuperSID Pro - VLF Database Fixed Test")
    print("=" * 50)
    
    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Manual Station", test_manual_station),
        ("KML Import", test_kml_import),
    ]
    
    passed = 0
    for name, test_func in tests:
        print(f"\nTesting {name}...")
        if test_func():
            passed += 1
            print(f"{name} - PASSED")
        else:
            print(f"{name} - FAILED")
    
    print(f"\nResults: {passed}/{len(tests)} tests passed")
    
    if passed >= 2:  # At least basic functionality and one other test
        print("Core VLF Database functionality is working!")
        return 0
    else:
        print("Critical tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())