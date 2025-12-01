#!/usr/bin/env python3
"""
Check if all dependencies for space weather are available
"""

import sys

def check_dependencies():
    """Check all required dependencies"""
    
    required_packages = [
        ('PyQt6', 'PyQt6.QtWidgets'),
        ('aiohttp', 'aiohttp'),
        ('beautifulsoup4', 'bs4'),
        ('lxml', 'lxml'),
        ('requests', 'requests')
    ]
    
    missing = []
    available = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            available. append(package_name)
            print(f"✅ {package_name} - OK")
        except ImportError:
            missing.append(package_name)
            print(f"❌ {package_name} - MISSING")
    
    print(f"\n📊 Summary: {len(available)}/{len(required_packages)} packages available")
    
    if missing:
        print(f"\n🔧 To install missing packages:")
        print(f"pip install {' '.join(missing)}")
        return False
    else:
        print("✅ All dependencies are available!")
        return True

if __name__ == "__main__":
    check_dependencies()