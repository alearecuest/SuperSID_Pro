#!/usr/bin/env python3
"""
Test script for Space Weather Widget
Run this to test the space weather functionality independently
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
from core. logger import setup_logger
from gui.widgets. space_weather_widget import SpaceWeatherWidget
from gui.styles. dark_theme import DarkTheme
from api.space_weather_api import SpaceWeatherAPI

class SpaceWeatherTestWindow(QMainWindow):
    """Test window for space weather widget"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("SuperSID Pro - Space Weather Test")
        self.setGeometry(100, 100, 400, 600)
        
        # Setup config manager
        self.config_manager = ConfigManager('config/test_config.json')
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Add space weather widget
        self.space_weather = SpaceWeatherWidget(self. config_manager)
        
        # Connect alert signal for testing
        self.space_weather.alert_triggered.connect(self.on_alert)
        
        layout.addWidget(self.space_weather)
        
        # Apply dark theme
        self.setStyleSheet(DarkTheme. get_stylesheet())
    
    def on_alert(self, alert_type: str, message: str):
        """Handle space weather alerts"""
        print(f"🚨 ALERT [{alert_type. upper()}]: {message}")

async def test_api_directly():
    """Test the space weather API directly"""
    print("🧪 Testing Space Weather API directly...")
    
    config_manager = ConfigManager('config/test_config.json')
    
    try:
        async with SpaceWeatherAPI(config_manager) as api:
            print("✅ API initialized successfully")
            
            # Test NOAA current conditions
            print("📡 Fetching NOAA current conditions...")
            noaa_data = await api.get_noaa_current_conditions()
            print(f"📊 NOAA Data: {noaa_data}")
            
            # Test recent solar flares
            print("☀️ Fetching recent solar flares...")
            flares = await api.get_recent_solar_flares(hours=24)
            print(f"🔥 Found {len(flares)} recent flares")
            
            for flare in flares[:3]:  # Show first 3
                print(f"   - {flare.flare_class} at {flare.timestamp.strftime('%H:%M UTC')}")
            
            # Test complete summary
            print("📋 Fetching complete space weather summary...")
            summary = await api.get_current_conditions()
            
            print("📈 Space Weather Summary:")
            print(f"   - Timestamp: {summary.timestamp}")
            print(f"   - Solar Flares: {len(summary.solar_flares)}")
            print(f"   - Current Conditions Keys: {list(summary.current_conditions.keys())}")
            
            if summary.geomagnetic:
                print(f"   - Kp Index: {summary.geomagnetic.kp_index}")
                print(f"   - Activity Level: {summary.geomagnetic.activity_level}")
            
            if summary.solar_wind:
                print(f"   - Solar Wind Speed: {summary. solar_wind.speed} km/s")
                print(f"   - Bz Field: {summary.solar_wind. bz} nT")
            
            print("✅ API test completed successfully!")
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback. print_exc()

def test_widget_gui():
    """Test the space weather widget in GUI"""
    print("🖥️ Testing Space Weather Widget GUI...")
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setPalette(DarkTheme.create_palette())
    
    # Create test window
    window = SpaceWeatherTestWindow()
    window. show()
    
    print("✅ GUI test window opened")
    print("🔄 Widget will automatically start fetching data...")
    print("💡 Watch the console for alerts and the GUI for real-time updates")
    
    return app. exec()

def main():
    """Main test function"""
    # Setup logging
    setup_logger(debug=True)
    
    print("=" * 50)
    print("🚀 SuperSID Pro - Space Weather Test Suite")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        # Test API only
        print("🧪 Running API-only test...")
        asyncio.run(test_api_directly())
    else:
        # Test GUI
        print("🖥️ Running GUI test...")
        print("💡 Use 'python test_space_weather.py api' to test API only")
        test_widget_gui()

if __name__ == "__main__":
    main()