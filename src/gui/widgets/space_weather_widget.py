"""
Space Weather monitoring widget for SuperSID Pro
Displays real-time space weather conditions and alerts
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QProgressBar, QFrame, QPushButton, QTextEdit, QScrollArea,
    QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio

from core.config_manager import ConfigManager
from core.logger import get_logger, log_exception
from api.space_weather_api import SpaceWeatherAPI, SpaceWeatherSummary, SolarFlare

class SpaceWeatherWorker(QObject):
    """Worker thread for fetching space weather data"""
    
    data_updated = pyqtSignal(object)  # SpaceWeatherSummary
    error_occurred = pyqtSignal(str)
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        self.running = False
    
    async def fetch_data(self):
        """Fetch space weather data"""
        try:
            async with SpaceWeatherAPI(self.config_manager) as api:
                summary = await api.get_current_conditions()
                self.data_updated.emit(summary)
        except Exception as e:
            log_exception(e, "Space weather data fetch")
            self.error_occurred. emit(str(e))
    
    def update_data(self):
        """Update data (called from timer)"""
        if not self.running:
            return
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.fetch_data())
            loop.close()
        except Exception as e:
            log_exception(e, "Space weather worker")
            self.error_occurred. emit(str(e))

class StatusIndicator(QLabel):
    """Custom status indicator widget"""
    
    def __init__(self, size: int = 12):
        super().__init__("●")
        self.setFixedSize(size, size)
        self.setAlignment(Qt. AlignmentFlag.AlignCenter)
        self.set_status("unknown")
    
    def set_status(self, status: str):
        """Set indicator status with color"""
        colors = {
            "good": "#00ff00",
            "warning": "#ffaa00", 
            "alert": "#ff4444",
            "critical": "#ff0000",
            "unknown": "#808080"
        }
        
        color = colors.get(status.lower(), "#808080")
        self.setStyleSheet(f"color: {color}; font-size: {self.height()-2}px; font-weight: bold;")

class ParameterDisplay(QFrame):
    """Widget for displaying a single space weather parameter"""
    
    def __init__(self, name: str, unit: str = "", format_str: str = "{:.1f}"):
        super().__init__()
        self.name = name
        self. unit = unit
        self.format_str = format_str
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup parameter display UI"""
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setFixedHeight(60)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)
        
        # Parameter name
        self.name_label = QLabel(self.name)
        self.name_label.setStyleSheet("""
            color: #b3b3b3;
            font-size: 10px;
            font-weight: bold;
        """)
        layout.addWidget(self.name_label)
        
        # Value and unit
        value_layout = QHBoxLayout()
        value_layout.setContentsMargins(0, 0, 0, 0)
        
        self.value_label = QLabel("--")
        self.value_label.setStyleSheet("""
            color: #ffffff;
            font-size: 14px;
            font-weight: bold;
        """)
        value_layout.addWidget(self.value_label)
        
        if self.unit:
            self. unit_label = QLabel(self.unit)
            self.unit_label.setStyleSheet("""
                color: #888888;
                font-size: 10px;
                margin-left: 2px;
            """)
            value_layout.addWidget(self.unit_label)
        
        value_layout.addStretch()
        layout.addLayout(value_layout)
        
        # Style the frame
        self.setStyleSheet("""
            ParameterDisplay {
                background-color: #1e1e1e;
                border: 1px solid #404040;
                border-radius: 4px;
            }
        """)
    
    def update_value(self, value: Any, status: str = "good"):
        """Update the displayed value"""
        try:
            if value is None or value == "":
                display_text = "--"
            elif isinstance(value, (int, float)):
                display_text = self.format_str.format(value)
            else:
                display_text = str(value)
            
            self.value_label.setText(display_text)
            
            # Set color based on status
            colors = {
                "good": "#00ff00",
                "warning": "#ffaa00",
                "alert": "#ff4444", 
                "critical": "#ff0000"
            }
            
            color = colors.get(status, "#ffffff")
            self.value_label.setStyleSheet(f"""
                color: {color};
                font-size: 14px;
                font-weight: bold;
            """)
            
        except Exception as e:
            self.value_label.setText("ERR")
            log_exception(e, f"Updating parameter {self.name}")

class FlareListWidget(QScrollArea):
    """Widget for displaying recent solar flares"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup flare list UI"""
        self. setMaximumHeight(120)
        self.setWidgetResizable(True)
        
        # Create scroll content
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout. setContentsMargins(4, 4, 4, 4)
        self.content_layout.setSpacing(2)
        
        self.setWidget(self.content_widget)
        
        # No flares message
        self.no_flares_label = QLabel("No recent flares detected")
        self.no_flares_label.setAlignment(Qt.AlignmentFlag. AlignCenter)
        self. no_flares_label.setStyleSheet("color: #888888; font-style: italic;")
        self. content_layout.addWidget(self.no_flares_label)
        
        self.content_layout.addStretch()
        
        # Style
        self.setStyleSheet("""
            QScrollArea {
                background-color: #1e1e1e;
                border: 1px solid #404040;
                border-radius: 4px;
            }
        """)
    
    def update_flares(self, flares: list):
        """Update the flares list"""
        # Clear existing items
        for i in reversed(range(self. content_layout.count())):
            child = self.content_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        if not flares:
            self. no_flares_label = QLabel("No recent flares detected")
            self.no_flares_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.no_flares_label.setStyleSheet("color: #888888; font-style: italic;")
            self.content_layout.addWidget(self.no_flares_label)
        else:
            # Add flare items
            for flare in flares[:10]:  # Show last 10 flares
                flare_widget = self.create_flare_item(flare)
                self. content_layout.addWidget(flare_widget)
        
        self.content_layout. addStretch()
    
    def create_flare_item(self, flare) -> QWidget:
        """Create a single flare item widget"""
        widget = QFrame()
        widget.setFrameStyle(QFrame.Shape.StyledPanel)
        widget.setMaximumHeight(30)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(6, 2, 6, 2)
        
        # Flare class with color coding
        class_label = QLabel(flare.flare_class)
        class_label.setFixedWidth(40)
        class_label.setAlignment(Qt.AlignmentFlag. AlignCenter)
        
        # Color code by flare class
        flare_letter = flare.flare_class[0] if flare.flare_class else "A"
        colors = {
            "X": "#ff0000",  # Red for X-class
            "M": "#ff8800",  # Orange for M-class  
            "C": "#ffaa00",  # Yellow for C-class
            "B": "#88aa88",  # Green for B-class
            "A": "#888888"   # Gray for A-class
        }
        
        color = colors.get(flare_letter, "#888888")
        class_label.setStyleSheet(f"""
            background-color: {color};
            color: black;
            font-weight: bold;
            font-size: 10px;
            border-radius: 3px;
            padding: 2px;
        """)
        layout.addWidget(class_label)
        
        # Timestamp
        time_str = flare.timestamp.strftime("%H:%M")
        time_label = QLabel(time_str)
        time_label. setStyleSheet("color: #b3b3b3; font-size: 10px;")
        layout.addWidget(time_label)
        
        layout.addStretch()
        
        # Location if available
        if hasattr(flare, 'location') and flare.location:
            location_label = QLabel(flare.location)
            location_label.setStyleSheet("color: #888888; font-size: 9px;")
            layout.addWidget(location_label)
        
        widget.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 3px;
                margin: 1px;
            }
        """)
        
        return widget

class SpaceWeatherWidget(QGroupBox):
    """Space weather monitoring widget"""
    
    # Signals
    alert_triggered = pyqtSignal(str, str)  # alert_type, message
    
    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__("Space Weather", parent)
        
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        
        # Data worker
        self.worker = SpaceWeatherWorker(config_manager)
        self.worker_thread = QThread()
        self.worker. moveToThread(self.worker_thread)
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout. connect(self.worker.update_data)
        
        # Current data
        self.current_data: Optional[SpaceWeatherSummary] = None
        
        self.setup_ui()
        self.connect_signals()
        self.start_monitoring()
    
    def setup_ui(self):
        """Setup the widget UI"""
        self.setMaximumWidth(380)
        self.setMinimumHeight(450)
        
        main_layout = QVBoxLayout(self)
        
        # Status header
        self.create_status_header(main_layout)
        
        # Current conditions
        self.create_conditions_section(main_layout)
        
        # Solar activity
        self.create_solar_section(main_layout)
        
        # Geomagnetic activity
        self.create_geomagnetic_section(main_layout)
        
        # Recent flares
        self.create_flares_section(main_layout)
        
        # Control buttons
        self.create_controls_section(main_layout)
        
        # Apply styling
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #404040;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: #2d2d2d;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #0078d4;
                font-size: 14px;
            }
        """)
    
    def create_status_header(self, layout: QVBoxLayout):
        """Create status header section"""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        header_frame.setMaximumHeight(50)
        
        header_layout = QHBoxLayout(header_frame)
        
        # Overall status indicator
        self.status_indicator = StatusIndicator(16)
        header_layout.addWidget(self. status_indicator)
        
        # Status text
        self.status_label = QLabel("Initializing...")
        self.status_label.setStyleSheet("color: #ffaa00; font-weight: bold; font-size: 12px;")
        header_layout.addWidget(self.status_label)
        
        header_layout.addStretch()
        
        # Last update time
        self.last_update_label = QLabel("--:--")
        self.last_update_label.setStyleSheet("color: #888888; font-size: 10px;")
        header_layout.addWidget(self.last_update_label)
        
        layout.addWidget(header_frame)
    
    def create_conditions_section(self, layout: QVBoxLayout):
        """Create current conditions section"""
        conditions_group = QGroupBox("Current Conditions")
        conditions_layout = QGridLayout(conditions_group)
        conditions_layout.setSpacing(4)
        
        # Create parameter displays
        self.kp_display = ParameterDisplay("Kp Index", "", "{:.1f}")
        conditions_layout.addWidget(self. kp_display, 0, 0)
        
        self.sw_speed_display = ParameterDisplay("Solar Wind", "km/s", "{:.0f}")
        conditions_layout. addWidget(self.sw_speed_display, 0, 1)
        
        self.bz_display = ParameterDisplay("Bz Field", "nT", "{:.1f}")
        conditions_layout. addWidget(self.bz_display, 1, 0)
        
        self.density_display = ParameterDisplay("SW Density", "p/cm³", "{:.1f}")
        conditions_layout.addWidget(self.density_display, 1, 1)
        
        layout.addWidget(conditions_group)
    
    def create_solar_section(self, layout: QVBoxLayout):
        """Create solar activity section"""
        solar_group = QGroupBox("Solar Activity")
        solar_layout = QVBoxLayout(solar_group)
        
        # Solar flux and X-ray level
        solar_params_layout = QGridLayout()
        
        self.xray_display = ParameterDisplay("X-ray Level", "", "{}")
        solar_params_layout. addWidget(self.xray_display, 0, 0)
        
        self.flux_display = ParameterDisplay("Solar Flux", "sfu", "{:.0f}")
        solar_params_layout.addWidget(self.flux_display, 0, 1)
        
        solar_layout.addLayout(solar_params_layout)
        
        layout.addWidget(solar_group)
    
    def create_geomagnetic_section(self, layout: QVBoxLayout):
        """Create geomagnetic activity section"""
        geo_group = QGroupBox("Geomagnetic")
        geo_layout = QHBoxLayout(geo_group)
        
        # Activity level
        self.activity_level_label = QLabel("Quiet")
        self.activity_level_label.setAlignment(Qt.AlignmentFlag. AlignCenter)
        self. activity_level_label.setStyleSheet("""
            background-color: #1e1e1e;
            border: 1px solid #404040;
            border-radius: 4px;
            padding: 6px;
            color: #00ff00;
            font-weight: bold;
            font-size: 12px;
        """)
        geo_layout.addWidget(self.activity_level_label)
        
        layout.addWidget(geo_group)
    
    def create_flares_section(self, layout: QVBoxLayout):
        """Create recent flares section"""
        flares_group = QGroupBox("Recent Solar Flares (24h)")
        flares_layout = QVBoxLayout(flares_group)
        
        self.flares_list = FlareListWidget()
        flares_layout.addWidget(self.flares_list)
        
        layout.addWidget(flares_group)
    
    def create_controls_section(self, layout: QVBoxLayout):
        """Create control buttons section"""
        controls_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setIcon(QIcon("assets/icons/refresh.png"))
        self.refresh_button.clicked.connect(self.manual_refresh)
        controls_layout.addWidget(self.refresh_button)
        
        self. auto_update_button = QPushButton("Auto Update: ON")
        self.auto_update_button.setCheckable(True)
        self.auto_update_button.setChecked(True)
        self.auto_update_button.clicked.connect(self.toggle_auto_update)
        controls_layout.addWidget(self.auto_update_button)
        
        layout.addLayout(controls_layout)
        
        # Style buttons
        button_style = """
            QPushButton {
                background-color: #404040;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
            }
            
            QPushButton:hover {
                background-color: #0078d4;
            }
            
            QPushButton:checked {
                background-color: #00aa00;
            }
        """
        
        self.refresh_button.setStyleSheet(button_style)
        self.auto_update_button.setStyleSheet(button_style)
    
    def connect_signals(self):
        """Connect worker signals"""
        self.worker. data_updated.connect(self.update_display)
        self.worker.error_occurred.connect(self.handle_error)
    
    def start_monitoring(self):
        """Start space weather monitoring"""
        self.worker. running = True
        self.worker_thread.start()
        
        # Initial update
        self.manual_refresh()
        
        # Start timer for regular updates (10 minutes)
        self.update_timer.start(10 * 60 * 1000)
        
        self.logger.info("Space weather monitoring started")
    
    def stop_monitoring(self):
        """Stop space weather monitoring"""
        self.worker.running = False
        self.update_timer.stop()
        self.worker_thread.quit()
        self.worker_thread.wait()
        
        self.logger.info("Space weather monitoring stopped")
    
    def manual_refresh(self):
        """Manually refresh space weather data"""
        self.status_label.setText("Updating...")
        self.status_indicator.set_status("unknown")
        self.worker.update_data()
    
    def toggle_auto_update(self, checked: bool):
        """Toggle automatic updates"""
        if checked:
            self.update_timer.start(10 * 60 * 1000)
            self.auto_update_button.setText("Auto Update: ON")
        else:
            self.update_timer.stop()
            self.auto_update_button.setText("Auto Update: OFF")
    
    def update_display(self, summary: SpaceWeatherSummary):
        """Update display with new space weather data"""
        self.current_data = summary
        
        try:
            # Update timestamp
            self.last_update_label.setText(
                summary.timestamp.strftime("%H:%M UTC")
            )
            
            # Update current conditions
            if summary.geomagnetic:
                kp_value = summary.geomagnetic. kp_index
                self.kp_display.update_value(kp_value, self.get_kp_status(kp_value))
                
                # Update activity level
                self.activity_level_label.setText(summary.geomagnetic.activity_level)
                self.activity_level_label.setStyleSheet(f"""
                    background-color: #1e1e1e;
                    border: 1px solid #404040;
                    border-radius: 4px;
                    padding: 6px;
                    color: {self.get_activity_color(summary.geomagnetic.activity_level)};
                    font-weight: bold;
                    font-size: 12px;
                """)
            
            if summary.solar_wind:
                self.sw_speed_display.update_value(
                    summary.solar_wind. speed,
                    self.get_sw_speed_status(summary.solar_wind.speed)
                )
                
                self.bz_display.update_value(
                    summary.solar_wind.bz,
                    self.get_bz_status(summary.solar_wind. bz)
                )
                
                self.density_display. update_value(
                    summary.solar_wind.density,
                    "good"
                )
            
            # Update from current conditions dict
            if "xray_flux" in summary.current_conditions:
                self.xray_display.update_value(
                    summary.current_conditions["xray_flux"],
                    "good"
                )
            
            if "swl_solar_flux" in summary.current_conditions:
                self.flux_display.update_value(
                    summary.current_conditions["swl_solar_flux"],
                    "good"
                )
            
            # Update flares list
            self.flares_list.update_flares(summary. solar_flares)
            
            # Determine overall status
            overall_status = self.determine_overall_status(summary)
            self.status_indicator.set_status(overall_status)
            self.status_label.setText(f"Status: {overall_status. title()}")
            
            # Check for alerts
            self.check_alerts(summary)
            
        except Exception as e:
            log_exception(e, "Updating space weather display")
            self. handle_error(f"Display update error: {e}")
    
    def get_kp_status(self, kp_value: float) -> str:
        """Get status level for Kp index"""
        if kp_value >= 7:
            return "critical"
        elif kp_value >= 5:
            return "alert"
        elif kp_value >= 4:
            return "warning"
        else:
            return "good"
    
    def get_sw_speed_status(self, speed: float) -> str:
        """Get status level for solar wind speed"""
        if speed >= 800:
            return "alert"
        elif speed >= 600:
            return "warning"
        else:
            return "good"
    
    def get_bz_status(self, bz: float) -> str:
        """Get status level for Bz magnetic field"""
        if bz <= -10:
            return "alert"
        elif bz <= -5:
            return "warning"
        else:
            return "good"
    
    def get_activity_color(self, activity_level: str) -> str:
        """Get color for geomagnetic activity level"""
        colors = {
            "Quiet": "#00ff00",
            "Unsettled": "#88ff00", 
            "Active": "#ffaa00",
            "Minor Storm": "#ff8800",
            "Moderate Storm": "#ff4444",
            "Strong Storm": "#ff0000",
            "Severe Storm": "#cc0000",
            "Extreme Storm": "#990000"
        }
        return colors.get(activity_level, "#888888")
    
    def determine_overall_status(self, summary: SpaceWeatherSummary) -> str:
        """Determine overall space weather status"""
        alert_level = 0
        
        # Check geomagnetic conditions
        if summary.geomagnetic:
            if summary.geomagnetic.kp_index >= 7:
                alert_level = max(alert_level, 3)  # Critical
            elif summary.geomagnetic.kp_index >= 5:
                alert_level = max(alert_level, 2)  # Alert
            elif summary.geomagnetic.kp_index >= 4:
                alert_level = max(alert_level, 1)  # Warning
        
        # Check solar wind
        if summary.solar_wind:
            if summary.solar_wind.speed >= 800 or summary.solar_wind.bz <= -10:
                alert_level = max(alert_level, 2)
            elif summary.solar_wind.speed >= 600 or summary.solar_wind.bz <= -5:
                alert_level = max(alert_level, 1)
        
        # Check recent flares
        for flare in summary.solar_flares:
            if flare. flare_class. startswith("X"):
                alert_level = max(alert_level, 2)
            elif flare.flare_class.startswith("M"):
                alert_level = max(alert_level, 1)
        
        status_map = {
            0: "good",
            1: "warning", 
            2: "alert",
            3: "critical"
        }
        
        return status_map.get(alert_level, "unknown")
    
    def check_alerts(self, summary: SpaceWeatherSummary):
        """Check for alert conditions and emit signals"""
        # Check flare threshold
        flare_threshold = self.config_manager.get("alerts. flare_threshold", "M1. 0")
        threshold_class = flare_threshold[0]  # X, M, C, etc.
        
        for flare in summary.solar_flares:
            flare_class = flare.flare_class[0] if flare.flare_class else "A"
            
            # Simple threshold check (X > M > C > B > A)
            class_values = {"X": 5, "M": 4, "C": 3, "B": 2, "A": 1}
            if class_values. get(flare_class, 0) >= class_values.get(threshold_class, 0):
                self.alert_triggered. emit(
                    "solar_flare", 
                    f"Solar flare detected: {flare.flare_class} at {flare.timestamp.strftime('%H:%M UTC')}"
                )
                break
        
        # Check geomagnetic storm
        if summary.geomagnetic and summary.geomagnetic.kp_index >= 5:
            self.alert_triggered.emit(
                "geomagnetic_storm",
                f"Geomagnetic storm: {summary.geomagnetic. activity_level} (Kp={summary.geomagnetic.kp_index:. 1f})"
            )
    
    def handle_error(self, error_message: str):
        """Handle errors from data fetching"""
        self.status_label.setText("Error updating")
        self.status_indicator. set_status("alert")
        self.logger.error(f"Space weather error: {error_message}")
    
    def closeEvent(self, event):
        """Handle widget close event"""
        self.stop_monitoring()
        super().closeEvent(event)