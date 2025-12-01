#!/usr/bin/env python3
"""
Step by step test for debugging chart issues
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def step1_test_core():
    """Step 1: Test core modules only"""
    print("Step 1: Testing core modules...")
    
    try:
        from core.config_manager import ConfigManager
        from core.logger import setup_logger
        print("Core modules OK")
        
        setup_logger(debug=True)
        print("Logging OK")
        
        config = ConfigManager('config/test_config.json')
        config._auto_save = False
        print("Config manager OK")
        
        return True
    except Exception as e:
        print(f"Core test failed: {e}")
        return False

def step2_test_pyqt():
    """Step 2: Test PyQt6 and Charts"""
    print("Step 2: Testing PyQt6 Charts...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QCoreApplication
        from PyQt6.QtCharts import QChart, QLineSeries
        print("PyQt6 Charts OK")
        return True
    except Exception as e:
        print(f"PyQt6 Charts test failed: {e}")
        print("Try: pip install PyQt6-Charts")
        return False

def step3_test_chart_imports():
    """Step 3: Test chart widget imports only"""
    print("Step 3: Testing chart widget imports...")
    
    try:
        from gui.widgets.chart_widget import ChartConfig, SignalData
        print("Chart data structures OK")
        
        from gui.widgets.chart_widget import DataGenerator
        print("DataGenerator import OK")
        
        return True
    except Exception as e:
        print(f"Chart imports failed: {e}")
        return False

def step4_test_with_qapp():
    """Step 4: Test with QCoreApplication"""
    print("Step 4: Testing with Qt application...")
    
    try:
        from PyQt6.QtCore import QCoreApplication
        from core.config_manager import ConfigManager
        from gui.widgets.chart_widget import DataGenerator
        
        app = QCoreApplication(sys. argv)
        print("QCoreApplication created")
        
        config = ConfigManager('config/test_config. json')
        config._auto_save = False
        print("Config OK")
        
        data_gen = DataGenerator(config)
        print("DataGenerator created")
        
        app.quit()
        return True
        
    except Exception as e:
        print(f"QApp test failed: {e}")
        return False

def main():
    """Run step by step tests"""
    print("SuperSID Pro - Step by Step Debugging")
    print("=" * 50)
    
    steps = [
        ("Core Modules", step1_test_core),
        ("PyQt6 Charts", step2_test_pyqt),
        ("Chart Imports", step3_test_chart_imports),
        ("Qt Application", step4_test_with_qapp),
    ]
    
    for name, test_func in steps:
        print(f"\nTesting {name}...")
        if test_func():
            print(f"{name} - PASSED")
        else:
            print(f"{name} - FAILED")
            print("Stopping tests due to failure")
            return 1
    
    print("\nAll step-by-step tests passed!")
    print("Ready to test GUI components")
    return 0

if __name__ == "__main__":
    sys.exit(main())