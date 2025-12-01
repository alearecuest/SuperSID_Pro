#!/usr/bin/env python3
"""
Debug script for KML parsing issues
"""

import sys
import os
import xml.etree.ElementTree as ET
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def debug_kml_parsing():
    """Debug KML parsing step by step"""
    
    # Create test KML
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
    
    kml_file = Path("data/debug_test.kml")
    kml_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(kml_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"1. Created KML file: {kml_file}")
    print(f"   Size: {kml_file.stat().st_size} bytes")
    
    # Test XML parsing
    try:
        tree = ET.parse(kml_file)
        root = tree.getroot()
        print(f"2. XML parsing successful")
        print(f"   Root tag: {root.tag}")
        print(f"   Root namespace: {root.tag.split('}')[0] + '}' if '}' in root.tag else 'None'}")
        
        # Test namespace
        kml_ns = {'kml': 'http://earth.google.com/kml/2.2'}
        placemarks = root.findall('. //kml:Placemark', kml_ns)
        print(f"3. Found {len(placemarks)} placemarks with namespace")
        
        if placemarks:
            placemark = placemarks[0]
            print("4. First placemark details:")
            
            # Name
            name_elem = placemark.find('kml:name', kml_ns)
            print(f"   Name: {name_elem.text if name_elem is not None else 'NOT FOUND'}")
            
            # Description
            desc_elem = placemark.find('kml:description', kml_ns)
            print(f"   Description: {desc_elem.text if desc_elem is not None else 'NOT FOUND'}")
            
            # Coordinates
            coords_elem = placemark.find('. //kml:coordinates', kml_ns)
            print(f"   Coordinates: {coords_elem.text if coords_elem is not None else 'NOT FOUND'}")
            
            if coords_elem is not None:
                coords = coords_elem.text.strip(). split(',')
                if len(coords) >= 2:
                    lon, lat = float(coords[0]), float(coords[1])
                    print(f"   Parsed: lat={lat}, lon={lon}")
        
        return True
        
    except Exception as e:
        print(f"2. XML parsing failed: {e}")
        return False

def test_actual_import():
    """Test the actual import function"""
    print("\n" + "="*50)
    print("Testing actual VLF Database import...")
    
    try:
        from core.config_manager import ConfigManager
        from data.vlf_database import VLFDatabase
        
        # Setup
        config_manager = ConfigManager('config/test_config.json')
        config_manager._auto_save = False
        
        db = VLFDatabase(config_manager)
        
        # Create test KML
        content = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://earth.google.com/kml/2. 2">
<Document>
<name>Test VLF Stations</name>
<Placemark>
<name>NAA Cutler Maine</name>
<description>Frequency: 24.0 kHz
Power: 1000kW
Country: USA</description>
<Point>
<coordinates>-67.2816,44.6449</coordinates>
</Point>
</Placemark>
<Placemark>
<name>DHO38 Burlage Germany</name>
<description>Frequency: 23.4 kHz
Power: 800kW
Country: Germany</description>
<Point>
<coordinates>7.615,53.0789</coordinates>
</Point>
</Placemark>
</Document>
</kml>'''
        
        kml_file = Path("data/test_import. kml")
        with open(kml_file, 'w', encoding='utf-8') as f:
            f. write(content)
        
        print(f"Created test KML: {kml_file}")
        
        # Import with debug
        imported = db.import_from_kml(str(kml_file))
        print(f"Import result: {imported} stations")
        
        # Check what's in database
        stations = db.get_all_stations()
        print(f"Database contains: {len(stations)} stations")
        
        for station in stations:
            print(f"  {station.code}: {station.name} ({station.frequency} kHz)")
        
        return imported > 0
        
    except Exception as e:
        print(f"Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("VLF Database KML Debug Tool")
    print("="*50)
    
    # Step 1: Debug XML parsing
    if debug_kml_parsing():
        print("\nXML parsing works correctly!")
    else:
        print("\nXML parsing failed!")
        return 1
    
    # Step 2: Test actual import
    if test_actual_import():
        print("\nKML import works correctly!")
        return 0
    else:
        print("\nKML import still has issues!")
        return 1

if __name__ == "__main__":
    sys.exit(main())