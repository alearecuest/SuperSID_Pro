"""
Real-time VLF Visualization Widget
Professional real-time charts for VLF signal monitoring
"""
import sys
from pathlib import Path
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout, QPushButton)
from PyQt6.QtCore import QTimer, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QPalette
import pyqtgraph as pg
from collections import deque
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from core.vlf_processor import VLFSignal
from core.logger import get_logger

class RealtimeVLFWidget(QWidget):
    """Real-time VLF visualization dashboard"""
    
    # Signals for communication
    anomaly_detected = pyqtSignal(str, str)  # station, message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self. logger = get_logger(__name__)
        
        # Data storage for real-time plotting
        self.max_points = 1000  # Keep last 1000 data points
        self.time_data = deque(maxlen=self.max_points)
        self.amplitude_data = {
            'BAND_1': deque(maxlen=self.max_points),
            'BAND_2': deque(maxlen=self.max_points),
            'BAND_3': deque(maxlen=self.max_points),
            'BAND_4': deque(maxlen=self.max_points)
        }
        
        # Chart references
        self.charts = {}
        self.curves = {}
        
        # Setup UI
        self._setup_ui()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout. connect(self._update_charts)
        self.update_timer.start(100)  # Update every 100ms
        
        self.logger.info("Real-time VLF visualization widget initialized")
    
    def _setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Real-time VLF Signal Monitor")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Control panel
        self._create_control_panel(layout)
        
        # Charts area
        self._create_charts_area(layout)
        
        # Status panel
        self._create_status_panel(layout)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                padding: 5px;
            }
            QFrame {
                border: 1px solid #555555;
                border-radius: 5px;
                margin: 2px;
            }
        """)
    
    def _create_control_panel(self, parent_layout):
        """Create control panel with buttons and status"""
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        
        # Start/Stop button
        self. start_button = QPushButton("Start Monitoring")
        self.start_button.clicked.connect(self._toggle_monitoring)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        control_layout.addWidget(self. start_button)
        
        # Clear data button  
        clear_button = QPushButton("Clear Data")
        clear_button. clicked.connect(self._clear_data)
        clear_button. setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        control_layout. addWidget(clear_button)
        
        control_layout.addStretch()
        
        # Status indicators
        self.status_label = QLabel("Status: Ready")
        self.data_count_label = QLabel("Data Points: 0")
        control_layout.addWidget(self. status_label)
        control_layout.addWidget(self.data_count_label)
        
        parent_layout.addWidget(control_frame)
    
    def _create_charts_area(self, parent_layout):
        """Create the main charts area"""
        charts_frame = QFrame()
        charts_layout = QGridLayout(charts_frame)
        
        # Configure pyqtgraph for dark theme
        pg.setConfigOption('background', '#2b2b2b')
        pg.setConfigOption('foreground', '#ffffff')
        
        # Create individual band charts (2x2 grid)
        band_colors = {
            'BAND_1': '#FF6B6B',  # Red
            'BAND_2': '#4ECDC4',  # Teal  
            'BAND_3': '#45B7D1',  # Blue
            'BAND_4': '#96CEB4'   # Green
        }
        
        band_names = {
            'BAND_1': '200-400 Hz',
            'BAND_2': '400-800 Hz', 
            'BAND_3': '800-1200 Hz',
            'BAND_4': '1200-2000 Hz'
        }
        
        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
        
        for i, (band_id, color) in enumerate(band_colors.items()):
            row, col = positions[i]
            
            # Create plot widget
            plot_widget = pg. PlotWidget(title=f"{band_names[band_id]} - {band_id}")
            plot_widget.setLabel('left', 'Amplitude', 'V')
            plot_widget.setLabel('bottom', 'Time', 's')
            plot_widget.showGrid(x=True, y=True, alpha=0.3)
            
            # Create curve for this band
            curve = plot_widget.plot(pen=pg.mkPen(color, width=2))
            
            # Store references
            self.charts[band_id] = plot_widget
            self.curves[band_id] = curve
            
            charts_layout.addWidget(plot_widget, row, col)
        
        # Combined overview chart
        overview_widget = pg.PlotWidget(title="All Bands Overview")
        overview_widget.setLabel('left', 'Amplitude', 'V')
        overview_widget.setLabel('bottom', 'Time', 's')
        overview_widget. showGrid(x=True, y=True, alpha=0.3)
        
        # Add curves for all bands to overview
        self.overview_curves = {}
        for band_id, color in band_colors.items():
            curve = overview_widget.plot(pen=pg.mkPen(color, width=1.5), name=band_names[band_id])
            self.overview_curves[band_id] = curve
        
        # Add legend to overview
        overview_widget.addLegend()
        
        charts_layout. addWidget(overview_widget, 2, 0, 1, 2)  # Span 2 columns
        
        parent_layout.addWidget(charts_frame)
    
    def _create_status_panel(self, parent_layout):
        """Create status and statistics panel"""
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)
        
        # Current values display
        self.current_values = {}
        for band_id in ['BAND_1', 'BAND_2', 'BAND_3', 'BAND_4']:
            label = QLabel(f"{band_id}: 0. 000")
            label.setFont(QFont("Courier", 10))
            status_layout.addWidget(label)
            self. current_values[band_id] = label
        
        status_layout.addStretch()
        
        # Anomaly indicator
        self.anomaly_label = QLabel("Normal")
        self.anomaly_label.setStyleSheet("""
            QLabel {
                background-color: #4CAF50;
                color: white;
                padding: 5px 10px;
                border-radius: 3px;
            }
        """)
        status_layout.addWidget(self.anomaly_label)
        
        parent_layout.addWidget(status_frame)
    
    def add_vlf_data(self, vlf_signals: Dict[str, VLFSignal]):
        """Add new VLF data point for visualization"""
        current_time = datetime.now()
        
        # Add time point
        if not self.time_data or (current_time - self.time_data[-1]).total_seconds() > 0.1:
            self.time_data.append(current_time)
            
            # Add amplitude data for each band
            for band_id in self.amplitude_data. keys():
                if band_id in vlf_signals:
                    amplitude = vlf_signals[band_id].amplitude
                else:
                    amplitude = 0.0
                
                self. amplitude_data[band_id]. append(amplitude)
                
                # Update current value display
                if band_id in self.current_values:
                    self.current_values[band_id].setText(f"{band_id}: {amplitude:.3f}")
        
        # Update data count
        self.data_count_label.setText(f"Data Points: {len(self.time_data)}")
    
    def _update_charts(self):
        """Update all charts with current data"""
        if len(self.time_data) < 2:
            return
        
        try:
            # Convert time to seconds relative to first point
            time_array = np.array([(t - self.time_data[0]).total_seconds() for t in self.time_data])
            
            # Update individual band charts
            for band_id, curve in self.curves.items():
                if band_id in self.amplitude_data:
                    amplitude_array = np.array(list(self.amplitude_data[band_id]))
                    if len(amplitude_array) == len(time_array):
                        curve.setData(time_array, amplitude_array)
            
            # Update overview chart
            for band_id, curve in self. overview_curves.items():
                if band_id in self.amplitude_data:
                    amplitude_array = np.array(list(self.amplitude_data[band_id]))
                    if len(amplitude_array) == len(time_array):
                        curve. setData(time_array, amplitude_array)
                        
        except Exception as e:
            self.logger.debug(f"Chart update error: {e}")
    
    def _toggle_monitoring(self):
        """Toggle monitoring on/off"""
        # This will be connected to the VLF system
        if self.start_button.text() == "Start Monitoring":
            self. start_button.setText("Stop Monitoring")
            self.start_button.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
            self.status_label.setText("Status: Monitoring")
            # TODO: Start VLF monitoring system
        else:
            self. start_button.setText("Start Monitoring") 
            self.start_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
            """)
            self.status_label.setText("Status: Stopped")
            # TODO: Stop VLF monitoring system
    
    def _clear_data(self):
        """Clear all data from charts"""
        self.time_data.clear()
        for band_data in self.amplitude_data.values():
            band_data.clear()
        
        # Clear charts
        for curve in self.curves.values():
            curve.setData([], [])
        for curve in self.overview_curves. values():
            curve.setData([], [])
        
        # Reset displays
        for band_id, label in self.current_values.items():
            label.setText(f"{band_id}: 0. 000")
        
        self.data_count_label.setText("Data Points: 0")
        self.logger.info("Chart data cleared")
    
    def show_anomaly(self, station: str, message: str):
        """Display anomaly alert"""
        self. anomaly_label.setText(f"ANOMALY: {message}")
        self.anomaly_label.setStyleSheet("""
            QLabel {
                background-color: #f44336;
                color: white;
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;
            }
        """)
        
        # Reset to normal after 5 seconds
        QTimer.singleShot(5000, self._reset_anomaly_display)
        
        self.anomaly_detected.emit(station, message)
    
    def _reset_anomaly_display(self):
        """Reset anomaly display to normal"""
        self.anomaly_label.setText("Normal")
        self.anomaly_label.setStyleSheet("""
            QLabel {
                background-color: #4CAF50;
                color: white;
                padding: 5px 10px;
                border-radius: 3px;
            }
        """)