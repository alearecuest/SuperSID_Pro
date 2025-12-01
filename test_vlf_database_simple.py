#!/usr/bin/env python3
"""
Simplified test for VLF Database System - no GUI components
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
        from data. vlf_database import VLFDatabase, VLFStationExtended
        from datetime import datetime
        
        # Setup config without auto-save
        config_manager = ConfigManager('config/test_config. json')
        config_manager._auto_save = False
        
        print("Config manager created")
        
        # Create database
        db = VLFDatabase(config_manager)
        print("Database created successfully")
        
        # Test database info
        db_info = db.get_database_info()
        print(f"Database contains {db_info. total_stations} stations")
        
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_sample_kml():
    """Create a simple sample KML"""
    content = '''<? xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://earth. google.com/kml/2.2">
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
    
    kml_file = Path("data/test_vlf. kml")
    kml_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(kml_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
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
        
        # Setup database
        config_manager = ConfigManager('config/test_config.json')
        config_manager._auto_save = False
        
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
        
        return True
        
    except Exception as e:
        print(f"KML import failed: {e}")
        import traceback
        traceback. print_exc()
        return False

def main():
    """Run simplified tests"""
    print("=" * 50)
    print("SuperSID Pro - VLF Database Simple Test")
    print("=" * 50)
    
    tests = [
        test_basic_functionality,
        test_kml_import,
    ]
    
    passed = 0
    for test_func in tests:
        if test_func():
            passed += 1
            print("PASSED\n")
        else:
            print("FAILED\n")
    
    print(f"Results: {passed}/{len(tests)} tests passed")
    return 0 if passed == len(tests) else 1

if __name__ == "__main__":
    sys.exit(main())