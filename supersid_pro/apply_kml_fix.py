#!/usr/bin/env python3
"""
Apply complete KML parsing fix to vlf_database.py
"""

import re

def fix_vlf_database():
    """Fix the KML parsing in vlf_database.py"""
    
    file_path = 'src/data/vlf_database.py'
    
    # Read the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and replace the problematic line for finding placemarks
    old_pattern = r'placemarks = root\.findall\(.*? Placemark.*?\)'
    new_code = """# Find all Placemark elements (namespace-independent approach)
        placemarks = []
        for elem in root.iter():
            if elem.tag. endswith("}Placemark") or elem.tag == "Placemark":
                placemarks. append(elem)"""
    
    content = re.sub(old_pattern, new_code, content)
    
    # Fix name finding - search direct children
    old_name = "name_elem = placemark. find('kml:name', self.kml_namespaces)"
    new_name = """name_elem = None
        for child in placemark:
            if child.tag.endswith('}name') or child.tag == 'name':
                name_elem = child
                break"""
    content = content.replace(old_name, new_name)
    
    # Fix coordinates finding - look inside Point element  
    old_coords = "coords_elem = placemark.find('. //kml:coordinates', self. kml_namespaces)"
    new_coords = """coords_elem = None
        # Find Point first, then coordinates inside it
        point_elem = None
        for child in placemark:
            if child.tag.endswith('}Point') or child.tag == 'Point':
                point_elem = child
                break
        if point_elem is not None:
            for child in point_elem:
                if child.tag.endswith('}coordinates') or child. tag == 'coordinates':
                    coords_elem = child
                    break"""
    content = content. replace(old_coords, new_coords)
    
    # Fix description finding - search direct children
    old_desc = "desc_elem = placemark. find('kml:description', self.kml_namespaces)"
    new_desc = """desc_elem = None
        for child in placemark:
            if child.tag.endswith('}description') or child.tag == 'description':
                desc_elem = child
                break"""
    content = content.replace(old_desc, new_desc)
    
    # Write the fixed file
    with open(file_path, 'w', encoding='utf-8') as f:
        f. write(content)
    
    print("Applied complete KML parsing fix to vlf_database.py")
    print("   - Fixed Placemark finding")
    print("   - Fixed name element finding (search direct children)")  
    print("   - Fixed coordinates finding (Point->coordinates hierarchy)")
    print("   - Fixed description finding (search direct children)")

def verify_syntax():
    """Verify the file still has valid syntax"""
    import subprocess
    
    try:
        result = subprocess.run(['python', '-m', 'py_compile', 'src/data/vlf_database.py'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("File syntax is valid")
            return True
        else:
            print(f"Syntax error: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error checking syntax: {e}")
        return False

def test_fix():
    """Test if the fix works"""
    import subprocess
    
    try:
        result = subprocess.run(['python', 'test_kml_debug.py'], 
                              capture_output=True, text=True)
        
        output = result.stdout
        if "Name: NOT FOUND" not in output and "Import result: 0" not in output:
            print("KML parsing fix appears to work!")
            return True
        else:
            print("Fix may not be working completely.")
            print("Test output snippet:")
            lines = output.split('\n')
            for line in lines:
                if 'Name:' in line or 'Import result:' in line or 'stations total' in line:
                    print(f"   {line}")
            return False
    except Exception as e:
        print(f"Error testing fix: {e}")
        return False

if __name__ == "__main__":
    print("Applying complete KML parsing fix...")
    fix_vlf_database()
    
    print("\nVerifying syntax...")
    syntax_ok = verify_syntax()
    
    if syntax_ok:
        print("\nTesting fix...")
        if test_fix():
            print("\nSuccess! KML parsing fix is working.")
        else:
            print("\nFix applied but may need further adjustment.")
    else:
        print("\nSyntax errors - fix needs manual intervention.")