"""
Real-time monitoring widget for SuperSID Pro
Combines charts, space weather, and station status
"""

from typing import Optional  # FIXED: Add missing import
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTabWidget,
    QGroupBox, QLabel, QFrame, QPushButton, QTextEdit, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

from core.config_manager import ConfigManager
from core.logger import get_logger
from gui.widgets.chart_widget import ChartWidget
from gui.widgets. space_weather_widget import SpaceWeatherWidget

class AlertPanel(QFrame):
    """Panel for displaying real-time alerts"""
    
    def __init__(self):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setMaximumHeight(150)
        
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Real-time Alerts")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #0078d4;")
        layout.addWidget(header_label)
        
        # Alerts area
        self.alerts_area = QTextEdit()
        self. alerts_area.setMaximumHeight(100)
        self.alerts_area.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #404040;
                border-radius: 4px;
                color: #ffffff;
                font-family: 'Courier New', monospace;
                font-size: 10px;
            }
        """)
        layout.addWidget(self.alerts_area)
        
        # Clear button
        clear_button = QPushButton("Clear Alerts")
        clear_button. clicked.connect(self.clear_alerts)
        clear_button.setMaximumWidth(100)
        layout.addWidget(clear_button)
    
    def add_alert(self, alert_type: str, message: str):
        """Add an alert to the panel"""
        from datetime import datetime
        
        timestamp = datetime.now(). strftime("%H:%M:%S")
        
        # Color code by alert type
        colors = {
            "solar_flare": "#ff4444",
            "geomagnetic_storm": "#ff8800", 
            "signal_drop": "#ffaa00",
            "info": "#00ff00"
        }
        
        color = colors.get(alert_type, "#ffffff")
        
        alert_html = f"""
        <p style="color: {color}; margin: 2px;">
        <b>[{timestamp}]</b> {alert_type. upper()}: {message}
        </p>
        """
        
        self.alerts_area.insertHtml(alert_html)
        self.alerts_area.ensureCursorVisible()
    
    def clear_alerts(self):
        """Clear all alerts"""
        self.alerts_area. clear()

class StationStatusPanel(QFrame):
    """Panel showing VLF station status"""
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setMaximumWidth(200)
        
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Station Status")
        header_label. setStyleSheet("font-weight: bold; font-size: 14px; color: #0078d4;")
        layout.addWidget(header_label)
        
        # Stations list
        self.stations_area = QScrollArea()
        self.stations_widget = QWidget()
        self. stations_layout = QVBoxLayout(self.stations_widget)
        
        self.stations_area.setWidget(self.stations_widget)
        self.stations_area.setWidgetResizable(True)
        layout.addWidget(self.stations_area)
        
        self.setup_stations()
    
    def setup_stations(self):
        """Setup station status displays"""
        stations = self.config_manager.get_vlf_stations()
        
        for station in stations:
            station_frame = QFrame()
            station_frame.setFrameStyle(QFrame.Shape.Box)
            station_frame.setMaximumHeight(80)
            
            station_layout = QVBoxLayout(station_frame)
            
            # Station name and code
            name_label = QLabel(f"{station.code}")
            name_label.setStyleSheet("font-weight: bold; color: #0078d4;")
            station_layout.addWidget(name_label)
            
            freq_label = QLabel(f"{station.frequency} kHz")
            freq_label. setStyleSheet("color: #b3b3b3; font-size: 10px;")
            station_layout.addWidget(freq_label)
            
            # Status indicator
            status_layout = QHBoxLayout()
            
            status_indicator = QLabel("●")
            if station.enabled:
                status_indicator.setStyleSheet("color: #00ff00; font-size: 16px;")
                status_text = "Active"
            else:
                status_indicator.setStyleSheet("color: #808080; font-size: 16px;")
                status_text = "Disabled"
            
            status_layout.addWidget(status_indicator)
            status_layout.addWidget(QLabel(status_text))
            status_layout.addStretch()
            
            station_layout.addLayout(status_layout)
            
            self.stations_layout.addWidget(station_frame)
        
        self.stations_layout.addStretch()

class MonitoringWidget(QWidget):
    """Main real-time monitoring widget"""
    
    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        
        self. setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Setup the monitoring interface"""
        layout = QHBoxLayout(self)
        
        # Main splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(main_splitter)
        
        # Left panel: Chart
        chart_panel = self.create_chart_panel()
        main_splitter.addWidget(chart_panel)
        
        # Right panel: Status and alerts
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # Set splitter proportions
        main_splitter. setSizes([800, 300])
    
    def create_chart_panel(self) -> QWidget:
        """Create the main chart panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Chart widget
        self.chart_widget = ChartWidget(self.config_manager)
        layout.addWidget(self.chart_widget)
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Create right panel with status and alerts"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Station status
        self.station_status = StationStatusPanel(self.config_manager)
        layout.addWidget(self.station_status)
        
        # Space weather (compact view)
        self.space_weather = SpaceWeatherWidget(self. config_manager)
        self.space_weather.setMaximumHeight(300)
        layout.addWidget(self.space_weather)
        
        # Alerts panel
        self.alerts_panel = AlertPanel()
        layout.addWidget(self.alerts_panel)
        
        layout.addStretch()
        
        return panel
    
    def connect_signals(self):
        """Connect widget signals"""
        # Chart events
        self.chart_widget. event_detected.connect(self.on_chart_event)
        
        # Space weather alerts
        self.space_weather. alert_triggered.connect(self.on_space_weather_alert)
    
    def on_chart_event(self, event_type: str, event_data: dict):
        """Handle chart events"""
        station = event_data.get('station', 'Unknown')
        
        if event_type == 'signal_drop':
            drop = event_data.get('drop', 0)
            message = f"Signal drop detected on {station}: {drop:. 1f}dB"
        else:
            message = f"Event detected on {station}: {event_type}"
        
        self.alerts_panel.add_alert(event_type, message)
        self.logger.info(f"Chart event: {event_type} - {message}")
    
    def on_space_weather_alert(self, alert_type: str, message: str):
        """Handle space weather alerts"""
        self.alerts_panel.add_alert(alert_type, message)
        self.logger.info(f"Space weather alert: {alert_type} - {message}")
    
    def update_space_weather_overlay(self, space_weather_data):
        """Update space weather overlay on chart"""
        self.chart_widget.add_space_weather_overlay(space_weather_data)