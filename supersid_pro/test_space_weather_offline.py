#!/usr/bin/env python3
"""
Test script for Space Weather Widget - OFFLINE MODE
Tests the functionality without internet connection using mock data
"""

import sys
import os
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

# Import our modules
from core.config_manager import ConfigManager
from core.logger import setup_logger
from api.space_weather_mock import MockSpaceWeatherAPI

class SpaceWeatherTestWindow(QMainWindow):
    """Test window for space weather widget"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("SuperSID Pro - Space Weather Test (OFFLINE MODE)")
        self.setGeometry(100, 100, 400, 600)
        
        # Setup config manager with mock mode enabled
        self.config_manager = ConfigManager('config/test_config.json')
        self.config_manager.set('development. use_mock_data', True, auto_save=False)
        
        print("Test window initialized with mock data")

async def test_mock_api():
    """Test the mock space weather API directly"""
    print("Testing MOCK Space Weather API...")
    
    config_manager = ConfigManager('config/test_config.json')
    config_manager.set('development.use_mock_data', True, auto_save=False)
    
    try:
        # Test mock API
        async with MockSpaceWeatherAPI(config_manager) as api:
            print("Mock API initialized successfully")
            
            # Test complete summary
            print("Fetching mock space weather summary...")
            summary = await api. get_current_conditions()
            
            print("Mock Space Weather Summary:")
            print(f"   - Timestamp: {summary.timestamp}")
            print(f"   - Solar Flares: {len(summary.solar_flares)}")
            print(f"   - Current Conditions Keys: {list(summary.current_conditions.keys())}")
            
            if summary.geomagnetic:
                print(f"   - Kp Index: {summary.geomagnetic.kp_index:.1f}")  # FIXED: Format corrected
                print(f"   - Activity Level: {summary.geomagnetic.activity_level}")
            
            if summary.solar_wind:
                print(f"   - Solar Wind Speed: {summary. solar_wind.speed:.0f} km/s")
                print(f"   - Bz Field: {summary.solar_wind. bz:.1f} nT")
                print(f"   - Bt Field: {summary.solar_wind.bt:.1f} nT")
                print(f"   - Density: {summary.solar_wind. density:.1f} p/cm³")
            
            # Show flares if any
            if summary.solar_flares:
                print("Mock Solar Flares:")
                for flare in summary.solar_flares:
                    print(f"   - {flare.flare_class} at {flare.timestamp. strftime('%H:%M UTC')} ({flare.location})")
            else:
                print("No recent solar flares in mock data")
            
            print("Mock API test completed successfully!")
            
    except Exception as e:
        print(f"Mock API test failed: {e}")
        import traceback
        traceback.print_exc()

def test_widget_gui():
    """Test the space weather widget in GUI with mock data"""
    print("Testing Space Weather Widget GUI (OFFLINE MODE)...")
    
    try:
        from gui.widgets.space_weather_widget import SpaceWeatherWidget
        from gui.styles.dark_theme import DarkTheme
        
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        app.setPalette(DarkTheme. create_palette())
        
        # Create test window
        window = SpaceWeatherTestWindow()
        window. show()
        
        print("GUI test window opened")
        print("Widget is using MOCK DATA (no internet required)")
        print("Watch the console for alerts and the GUI for real-time updates")
        
        return app.exec()
    except ImportError as e:
        print(f"Cannot test GUI: Missing dependencies {e}")
        print("Running API test only...")
        asyncio.run(test_mock_api())

def main():
    """Main test function"""
    # Setup logging
    setup_logger(debug=True)
    
    print("=" * 50)
    print("SuperSID Pro - Space Weather Test Suite (OFFLINE)")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        # Test API only
        print("Running MOCK API-only test...")
        asyncio. run(test_mock_api())
    else:
        # Test GUI
        print("Running GUI test with MOCK data...")
        print("Use 'python test_space_weather_offline.py api' to test mock API only")
        test_widget_gui()

if __name__ == "__main__":
    main()