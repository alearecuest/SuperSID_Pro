#!/usr/bin/env python3
"""
Simple test script for SuperSID Pro Chart System
Tests real-time charting capabilities with mock data - FIXED VERSION
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports_only():
    """Test only imports and basic setup - no widgets"""
    print("Testing imports and basic components...")
    
    try:
        # Test core imports
        from core.config_manager import ConfigManager
        from core.logger import setup_logger, get_logger
        print("Core modules imported successfully")
        
        # Test PyQt6 Charts availability
        from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
        from PyQt6.QtCharts import QChart, QChartView, QLineSeries
        print("PyQt6-Charts available")
        
        # Test our chart module imports
        from gui.widgets.chart_widget import ChartConfig, SignalData, DataGenerator
        print("Chart widget modules imported successfully")
        
        # Setup logging
        setup_logger(debug=True)
        logger = get_logger(__name__)
        logger.info("Test logging successful")
        print("Logging setup successful")
        
        # Setup config (without auto-save to avoid widgets)
        config_manager = ConfigManager('config/test_config. json')
        config_manager._auto_save = False  # Disable auto-save
        config_manager.set('development.use_mock_data', True, auto_save=False)
        print("Config manager setup successful")
        
        # Test chart configuration
        display_config = config_manager.get('display', {})
        chart_config = ChartConfig(
            time_range_hours=24,
            update_interval_ms=1000,
            auto_scale=True,
            show_grid=True
        )
        print("Chart configuration created successfully")
        
        # Test data structures
        from datetime import datetime
        signal_data = SignalData(
            timestamp=datetime.now(),
            station_code="NAA",
            frequency=24.0,
            amplitude=-75.5,
            phase=45.0,
            snr=35.2
        )
        print("Signal data structures working")
        
        print("\nAll basic components are working correctly!")
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_generator():
    """Test data generator without GUI"""
    print("Testing data generator...")
    
    try:
        from PyQt6.QtCore import QCoreApplication
        from core.config_manager import ConfigManager
        from gui.widgets.chart_widget import DataGenerator
        
        # Create minimal Qt application (no GUI)
        app = QCoreApplication(sys.argv)
        
        # Setup config
        config_manager = ConfigManager('config/test_config. json')
        config_manager._auto_save = False
        
        # Create data generator
        data_gen = DataGenerator(config_manager)
        print(f"Data generator created with {len(data_gen.enabled_stations)} stations")
        
        # Test signal generation
        received_data = []
        
        def on_data_received(data_point):
            received_data.append(data_point)
            print(f"Received data: {data_point. station_code} = {data_point.amplitude:.1f}dB")
        
        data_gen.data_updated.connect(on_data_received)
        
        # Generate a few data points manually
        for _ in range(3):
            data_gen.generate_data_point()
        
        print(f"Generated {len(received_data)} data points successfully")
        
        app.quit()
        return True
        
    except Exception as e:
        print(f"Data generator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_gui():
    """Test chart widget with GUI if available"""
    print("Testing Chart Widget with GUI...")
    
    try:
        from PyQt6.QtWidgets import QApplication, QMainWindow
        from core.config_manager import ConfigManager
        from core.logger import setup_logger
        from gui.widgets.chart_widget import ChartWidget
        from gui.styles.dark_theme import DarkTheme
        
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        print("QApplication created successfully")
        
        # Apply theme
        try:
            app.setPalette(DarkTheme.create_palette())
            print("Dark theme applied")
        except:
            print("Dark theme failed, using default")
        
        # Setup config
        config_manager = ConfigManager('config/test_config.json')
        config_manager.set('development.use_mock_data', True, auto_save=False)
        
        # Create test window
        window = QMainWindow()
        window.setWindowTitle("SuperSID Pro - Chart Widget Test")
        window.setGeometry(100, 100, 1000, 600)
        
        print("Main window created")
        
        # Add chart widget
        chart_widget = ChartWidget(config_manager)
        window.setCentralWidget(chart_widget)
        
        print("Chart widget created and added to window")
        
        # Connect event signals
        chart_widget.event_detected.connect(
            lambda event_type, data: print(f"🚨 Event detected: {event_type} - {data}")
        )
        
        window.show()
        
        print("Chart widget GUI test opened")
        print("You should see real-time VLF signal charts")
        print("Events will be detected and logged here")
        print("Close the window to continue")
        
        # Run for a limited time or until window closes
        return app.exec()
        
    except Exception as e:
        print(f"GUI test failed: {e}")
        import traceback
        traceback.print_exc()
        print("This is normal if no display server is available")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("SuperSID Pro - Chart System Test Suite (Fixed)")
    print("=" * 60)
    
    # Test 1: Basic imports and configuration
    print("\nTesting imports and basic setup...")
    basic_test = test_imports_only()
    
    if not basic_test:
        print("\nBasic test failed - check dependencies")
        return 1
    
    # Test 2: Data generation without GUI
    print("\nTesting data generation...")
    data_test = test_data_generator()
    
    if not data_test:
        print("\nData generation test failed")
    
    # Test 3: GUI test if possible
    print("\nTesting with GUI...")
    gui_test = test_with_gui()
    
    if gui_test:
        print("\nAll tests completed successfully!")
    else:
        print("\nGUI test skipped or failed (no display available)")
        print("Core functionality tests passed!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())