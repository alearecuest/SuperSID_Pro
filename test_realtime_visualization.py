#!/usr/bin/env python3
"""
Test Real-time VLF Visualization
Complete test of the visualization dashboard
"""
import sys
import time
import threading
from pathlib import Path

sys.path.insert(0, 'src')

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer
import numpy as np
from datetime import datetime

from gui.widgets.realtime_vlf_widget import RealtimeVLFWidget
from core.vlf_processor import VLFSignal
from core.logger import setup_logger

class TestVLFApp(QMainWindow):
    """Test application for VLF visualization"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VLF Real-time Visualization Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Create VLF widget
        self. vlf_widget = RealtimeVLFWidget()
        layout.addWidget(self.vlf_widget)
        
        # Setup data simulation
        self.setup_simulation()
    
    def setup_simulation(self):
        """Setup simulation of VLF data"""
        self.simulation_timer = QTimer()
        self.simulation_timer.timeout. connect(self.generate_test_data)
        self.simulation_timer.start(500)  # Generate data every 500ms
        
        self.time_counter = 0
    
    def generate_test_data(self):
        """Generate simulated VLF data"""
        self.time_counter += 0.5
        
        # Create realistic VLF signals with some variation
        vlf_signals = {}
        
        # BAND_1: 200-400 Hz
        vlf_signals['BAND_1'] = VLFSignal(
            timestamp=time.time(),
            frequency=0.3 + 0.05 * np.sin(self.time_counter * 0.1),
            amplitude=0.001 + 0.0005 * np.sin(self. time_counter * 0.2) + 0.0001 * np.random.randn(),
            phase=0.0,
            station_id='BAND_1'
        )
        
        # BAND_2: 400-800 Hz  
        vlf_signals['BAND_2'] = VLFSignal(
            timestamp=time.time(),
            frequency=0.6 + 0.1 * np.sin(self. time_counter * 0.15),
            amplitude=0.002 + 0.001 * np.sin(self.time_counter * 0.3) + 0.0002 * np.random.randn(),
            phase=0.0,
            station_id='BAND_2'
        )
        
        # BAND_3: 800-1200 Hz
        vlf_signals['BAND_3'] = VLFSignal(
            timestamp=time.time(),
            frequency=1.0 + 0.15 * np.sin(self. time_counter * 0.12),
            amplitude=0.003 + 0.0015 * np.sin(self. time_counter * 0.25) + 0.0003 * np.random.randn(),
            phase=0.0,
            station_id='BAND_3'
        )
        
        # BAND_4: 1200-2000 Hz
        vlf_signals['BAND_4'] = VLFSignal(
            timestamp=time.time(),
            frequency=1.6 + 0.2 * np.sin(self.time_counter * 0.08),
            amplitude=0.004 + 0.002 * np.sin(self.time_counter * 0.4) + 0.0004 * np.random.randn(),
            phase=0.0,
            station_id='BAND_4'
        )
        
        # Simulate occasional anomaly
        if self.time_counter % 20 < 1:  # Every 20 seconds
            self.vlf_widget.show_anomaly("BAND_2", "Amplitude spike detected")
        
        # Send data to widget
        self.vlf_widget.add_vlf_data(vlf_signals)

def test_visualization():
    """Test the VLF visualization system"""
    print("Testing VLF Real-time Visualization")
    print("=" * 50)
    
    # Setup logging
    setup_logger(debug=True)
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create test window
    window = TestVLFApp()
    window.show()
    
    print("VLF visualization test window opened")
    print("You should see:")
    print("   - 4 individual frequency band charts")
    print("   - 1 combined overview chart") 
    print("   - Real-time data updating every 500ms")
    print("   - Periodic anomaly alerts")
    print("   - Control buttons working")
    print("\nClose the window to finish the test.")
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    test_visualization()