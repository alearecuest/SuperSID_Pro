#!/usr/bin/env python3
"""
Debug the fixed KML parsing
"""

import sys
import os
from pathlib import Path
sys.path. insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_fixed_parsing():
    """Test the parsing step by step"""
    
    from core.config_manager import ConfigManager
    from data.vlf_database import VLFDatabase
    import xml.etree.ElementTree as ET
    
    # Create detailed KML
    content = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://earth.google.com/kml/2.2">
<Document>
<name>Test VLF Stations</name>
<Placemark>
<name>NAA Cutler Maine</name>
<description>Frequency: 24.0 kHz
Power: 1000kW
Country: USA
Callsign: NAA</description>
<Point>
<coordinates>-67.2816,44.6449</coordinates>
</Point>
</Placemark>
</Document>
</kml>'''
    
    kml_file = Path("data/debug_fixed.kml")
    with open(kml_file, 'w', encoding='utf-8') as f:
        f. write(content)
    
    print("1. Created KML file with detailed content")
    
    # Test XML parsing manually with the same approach as the fixed code
    tree = ET.parse(kml_file)
    root = tree. getroot()
    
    print(f"2. Root tag: {root.tag}")
    
    # Test the fixed approach
    placemarks = []
    for elem in root.iter():
        if elem.tag. endswith("}Placemark") or elem.tag == "Placemark":
            placemarks. append(elem)
    
    print(f"3. Found {len(placemarks)} placemarks using fixed approach")
    
    if placemarks:
        placemark = placemarks[0]
        print("4. Testing element finding in first placemark:")
        
        # Test name finding
        name_elem = None
        for elem in placemark. iter():
            if elem.tag.endswith('}name') or elem.tag == 'name':
                name_elem = elem
                break
        print(f"   Name: {name_elem.text if name_elem else 'NOT FOUND'}")
        
        # Test description finding
        desc_elem = None
        for elem in placemark. iter():
            if elem.tag.endswith('}description') or elem.tag == 'description':
                desc_elem = elem
                break
        print(f"   Description: {desc_elem. text[:50] if desc_elem else 'NOT FOUND'}...")
        
        # Test coordinates finding
        coords_elem = None
        for elem in placemark. iter():
            if elem.tag.endswith('}coordinates') or elem.tag == 'coordinates':
                coords_elem = elem
                break
        print(f"   Coordinates: {coords_elem.text if coords_elem else 'NOT FOUND'}")
    
    # Now test the actual database import
    print("\n5. Testing actual database import:")
    
    config_manager = ConfigManager('config/test_config.json')
    config_manager._auto_save = False
    
    db = VLFDatabase(config_manager)
    
    # Clear any existing data to get accurate count
    import sqlite3
    with sqlite3.connect(db.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vlf_stations WHERE code LIKE 'NAA%' OR code LIKE 'TEST%'")
        conn.commit()
    
    print("   Cleared test data from database")
    
    # Import
    imported = db.import_from_kml(str(kml_file))
    print(f"   Import result: {imported}")
    
    # Check what's in database
    stations = db.get_all_stations()
    print(f"   Database contains: {len(stations)} stations total")
    
    for station in stations:
        print(f"     {station.code}: {station.name} ({station.frequency} kHz)")

if __name__ == "__main__":
    print("Testing Fixed KML Parsing")
    print("=" * 40)
    test_fixed_parsing()