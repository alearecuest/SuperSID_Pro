"""
Advanced real-time charting widget for SuperSID Pro
Displays VLF signal data, space weather overlays, and event detection
"""

import sys
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFrame,
    QComboBox, QLabel, QPushButton, QCheckBox, QSpinBox,
    QGroupBox, QGridLayout, QSlider, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtCharts import (
    QChart, QChartView, QLineSeries, QValueAxis, QDateTimeAxis,
    QScatterSeries, QLegend, QAreaSeries
)
from PyQt6.QtCore import QDateTime, QPointF

from core.config_manager import ConfigManager
from core. logger import get_logger, log_execution_time  # FIXED: Import correct decorator
from api.space_weather_mock import MockSpaceWeatherAPI

@dataclass
class ChartConfig:
    """Chart configuration settings"""
    title: str = "VLF Signal Monitor"
    time_range_hours: int = 24
    update_interval_ms: int = 1000
    max_data_points: int = 86400  # 24 hours at 1 second resolution
    auto_scale: bool = True
    show_grid: bool = True
    line_width: float = 1.5
    background_color: str = "#1e1e1e"
    text_color: str = "#ffffff"
    grid_color: str = "#404040"

@dataclass
class SignalData:
    """VLF signal data point"""
    timestamp: datetime
    station_code: str
    frequency: float
    amplitude: float
    phase: float = 0.0
    snr: float = 0.0

@dataclass
class EventMarker:
    """Event marker for overlays"""
    timestamp: datetime
    event_type: str  # 'flare', 'geomagnetic', 'manual'
    severity: str   # 'minor', 'moderate', 'major', 'extreme'
    description: str
    color: str = "#ff0000"

class DataGenerator(QObject):
    """Simulates real-time VLF signal data for development"""
    
    data_updated = pyqtSignal(object)  # SignalData
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        self.running = False
        
        # Simulation parameters
        self.base_amplitude = -80.0  # dB
        self.noise_level = 5.0
        self.trend_factor = 0.0
        
        # Get enabled VLF stations
        self.stations = self.config_manager.get_vlf_stations()
        self.enabled_stations = [s for s in self.stations if s. enabled]
        
        if not self.enabled_stations:
            # Add default stations if none configured
            from core.config_manager import VLFStation
            self.enabled_stations = [
                VLFStation(code="NAA", name="Cutler, ME", frequency=24.0, enabled=True),
                VLFStation(code="DHO38", name="Burlage, Germany", frequency=23.4, enabled=True)
            ]
        
        self.logger.info(f"Data generator initialized with {len(self.enabled_stations)} stations")
    
    def start_generation(self):
        """Start generating mock data"""
        self.running = True
        self.timer = QTimer()
        self. timer.timeout.connect(self. generate_data_point)
        self.timer.start(1000)  # Generate data every second
        
    def stop_generation(self):
        """Stop generating data"""
        self.running = False
        if hasattr(self, 'timer'):
            self.timer.stop()
    
    def generate_data_point(self):
        """Generate a simulated data point"""
        if not self.running:
            return
            
        current_time = datetime.now()
        
        for station in self.enabled_stations:
            # Simulate realistic VLF signal behavior
            
            # Base signal with slow trend
            base_signal = self. base_amplitude + self.trend_factor * np.sin(current_time.timestamp() / 3600)
            
            # Add noise
            noise = np.random.normal(0, self.noise_level)
            
            # Add solar activity influence (simulated)
            solar_influence = self._simulate_solar_influence(current_time, station. frequency)
            
            # Calculate final amplitude
            amplitude = base_signal + noise + solar_influence
            
            # Simulate phase and SNR
            phase = np.random.uniform(0, 360)
            snr = max(10, 40 + np.random.normal(0, 5))
            
            # Create data point
            data_point = SignalData(
                timestamp=current_time,
                station_code=station.code,
                frequency=station.frequency,
                amplitude=amplitude,
                phase=phase,
                snr=snr
            )
            
            self.data_updated.emit(data_point)
    
    def _simulate_solar_influence(self, timestamp: datetime, frequency: float) -> float:
        """Simulate solar activity influence on VLF signals"""
        # Simulate day/night effect
        hour = timestamp.hour
        day_factor = 1.0 if 6 <= hour <= 18 else 0.5
        
        # Simulate solar flare effect (random events)
        flare_probability = 0.001  # 0.1% chance per second
        if np.random.random() < flare_probability:
            # Simulate sudden ionospheric disturbance
            return -np.random.uniform(5, 20)  # Signal decrease
        
        # Normal solar influence
        return day_factor * np.random.uniform(-1, 1)

class RealtimeChartView(QChartView):
    """Real-time chart view with advanced features"""
    
    # Signals
    event_detected = pyqtSignal(str, dict)  # event_type, event_data
    
    def __init__(self, config: ChartConfig, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.config = config
        self.logger = get_logger(__name__)
        
        # Data storage
        self.signal_data: Dict[str, List[SignalData]] = {}
        self.event_markers: List[EventMarker] = []
        
        # Chart components
        self.chart = QChart()
        self.series: Dict[str, QLineSeries] = {}
        self.event_series: Dict[str, QScatterSeries] = {}
        
        # Axes
        self.time_axis = QDateTimeAxis()
        self.amplitude_axis = QValueAxis()
        
        self.setup_chart()
        self.setup_axes()
        self.apply_theme()
        
        # Performance tracking
        self.last_update_time = datetime.now()
        self.update_count = 0
    
    def setup_chart(self):
        """Setup the main chart"""
        self.chart. setTitle(self.config.title)
        self.chart.setAnimationOptions(QChart.AnimationOption.NoAnimation)
        self.chart.legend().setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.setChart(self.chart)
        self.setRenderHint(self.painter(). RenderHint.Antialiasing)
    
    def setup_axes(self):
        """Setup chart axes"""
        # Time axis (X)
        self.time_axis. setTitleText("Time (UTC)")
        self.time_axis.setFormat("hh:mm:ss")
        
        # Set time range
        now = QDateTime.currentDateTime()
        self.time_axis.setRange(
            now.addSecs(-self.config.time_range_hours * 3600),
            now
        )
        
        # Amplitude axis (Y)
        self.amplitude_axis.setTitleText("Signal Strength (dB)")
        self. amplitude_axis.setRange(-120, -40)  # Typical VLF range
        
        if self.config.show_grid:
            self.amplitude_axis.setGridLineVisible(True)
            self. time_axis.setGridLineVisible(True)
        
        self.chart.addAxis(self.time_axis, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(self. amplitude_axis, Qt.AlignmentFlag.AlignLeft)
    
    def apply_theme(self):
        """Apply dark theme to chart"""
        self. chart.setBackgroundBrush(QColor(self.config.background_color))
        self.chart.setTitleBrush(QColor(self.config.text_color))
        
        # Axes colors
        self.time_axis.setTitleBrush(QColor(self. config.text_color))
        self.time_axis.setLabelsBrush(QColor(self. config.text_color))
        self.time_axis.setGridLinePen(QColor(self.config.grid_color))
        
        self.amplitude_axis.setTitleBrush(QColor(self.config.text_color))
        self.amplitude_axis.setLabelsBrush(QColor(self.config.text_color))
        self.amplitude_axis.setGridLinePen(QColor(self.config. grid_color))
        
        # Legend
        legend = self.chart.legend()
        legend.setBrush(QColor(self. config.background_color))
        legend.setLabelBrush(QColor(self.config.text_color))
    
    def add_station(self, station_code: str, station_name: str, color: str):
        """Add a VLF station to the chart"""
        # Create main signal series
        series = QLineSeries()
        series.setName(f"{station_code} ({station_name})")
        series.setPen(QColor(color), self.config.line_width)
        
        self.chart.addSeries(series)
        series.attachAxis(self.time_axis)
        series.attachAxis(self.amplitude_axis)
        
        self.series[station_code] = series
        
        # Create event markers series
        event_series = QScatterSeries()
        event_series.setName(f"{station_code} Events")
        event_series.setMarkerSize(8)
        event_series.setBrush(QColor("#ff0000"))
        
        self.chart.addSeries(event_series)
        event_series.attachAxis(self.time_axis)
        event_series.attachAxis(self.amplitude_axis)
        
        self. event_series[station_code] = event_series
        
        # Initialize data storage
        self.signal_data[station_code] = []
        
        self.logger.info(f"Added station {station_code} to chart")
    
    @log_execution_time("Chart update")  # FIXED: Use correct decorator
    def update_data(self, data_point: SignalData):
        """Update chart with new data point"""
        station_code = data_point.station_code
        
        if station_code not in self.series:
            return
        
        # Add to data storage
        self.signal_data[station_code].append(data_point)
        
        # Limit data points to prevent memory issues
        if len(self.signal_data[station_code]) > self.config.max_data_points:
            self.signal_data[station_code] = self.signal_data[station_code][-self.config. max_data_points:]
        
        # Update chart series
        self._update_series(station_code)
        
        # Update time axis to show recent data
        self._update_time_axis()
        
        # Auto-scale if enabled
        if self.config.auto_scale:
            self._auto_scale_amplitude()
        
        # Check for events
        self._detect_events(data_point)
        
        self.update_count += 1
    
    def _update_series(self, station_code: str):
        """Update a specific station's series data"""
        series = self.series[station_code]
        data_points = self.signal_data[station_code]
        
        # Clear existing points
        series.clear()
        
        # Add recent points
        cutoff_time = datetime.now() - timedelta(hours=self. config.time_range_hours)
        recent_points = [p for p in data_points if p.timestamp > cutoff_time]
        
        for point in recent_points:
            qt_time = QDateTime.fromSecsSinceEpoch(int(point.timestamp. timestamp()))
            series.append(qt_time. toMSecsSinceEpoch(), point.amplitude)
    
    def _update_time_axis(self):
        """Update time axis range to show recent data"""
        now = QDateTime.currentDateTime()
        start_time = now.addSecs(-self.config.time_range_hours * 3600)
        
        self.time_axis.setRange(start_time, now)
    
    def _auto_scale_amplitude(self):
        """Auto-scale amplitude axis based on current data"""
        all_amplitudes = []
        cutoff_time = datetime.now() - timedelta(hours=self. config.time_range_hours)
        
        for data_points in self.signal_data.values():
            recent_amplitudes = [
                p.amplitude for p in data_points 
                if p.timestamp > cutoff_time
            ]
            all_amplitudes.extend(recent_amplitudes)
        
        if all_amplitudes:
            min_amp = min(all_amplitudes)
            max_amp = max(all_amplitudes)
            
            # Add some padding
            padding = (max_amp - min_amp) * 0.1
            self.amplitude_axis.setRange(
                min_amp - padding,
                max_amp + padding
            )
    
    def _detect_events(self, data_point: SignalData):
        """Detect significant events in the signal"""
        station_code = data_point.station_code
        station_data = self.signal_data[station_code]
        
        if len(station_data) < 10:  # Need some history
            return
        
        # Calculate recent baseline
        recent_data = station_data[-60:]  # Last 60 seconds
        baseline = np.mean([p.amplitude for p in recent_data[:-1]])
        current = data_point.amplitude
        
        # Detect sudden signal drop (possible flare effect)
        threshold = 5.0  # dB
        if baseline - current > threshold:
            event_data = {
                'station': station_code,
                'baseline': baseline,
                'current': current,
                'drop': baseline - current,
                'timestamp': data_point.timestamp
            }
            
            self._add_event_marker(
                data_point.timestamp,
                'signal_drop',
                'moderate' if event_data['drop'] < 10 else 'major',
                f"Signal drop: {event_data['drop']:.1f}dB"
            )
            
            self.event_detected. emit('signal_drop', event_data)
    
    def _add_event_marker(self, timestamp: datetime, event_type: str, severity: str, description: str):
        """Add event marker to chart"""
        # Color based on severity
        colors = {
            'minor': "#ffaa00",
            'moderate': "#ff8800", 
            'major': "#ff4444",
            'extreme': "#ff0000"
        }
        
        marker = EventMarker(
            timestamp=timestamp,
            event_type=event_type,
            severity=severity,
            description=description,
            color=colors. get(severity, "#ff0000")
        )
        
        self.event_markers.append(marker)
        
        # Add to all relevant event series
        qt_time = QDateTime.fromSecsSinceEpoch(int(timestamp.timestamp()))
        
        for station_code, event_series in self.event_series.items():
            if station_code in self.signal_data:
                # Get amplitude at this time (approximate)
                station_data = self.signal_data[station_code]
                amplitude = -70  # Default marker position
                
                for point in reversed(station_data):
                    if abs((point.timestamp - timestamp).total_seconds()) < 5:
                        amplitude = point. amplitude
                        break
                
                event_series.append(qt_time.toMSecsSinceEpoch(), amplitude)
    
    def add_space_weather_overlay(self, flares: list, geomagnetic_data):
        """Add space weather events as overlays"""
        for flare in flares:
            self._add_event_marker(
                flare. timestamp,
                'solar_flare',
                'major' if flare.flare_class. startswith('M') else 'extreme' if flare.flare_class.startswith('X') else 'moderate',
                f"Solar flare: {flare.flare_class}"
            )
    
    def set_time_range(self, hours: int):
        """Set the time range for display"""
        self.config.time_range_hours = hours
        self._update_time_axis()
        
        # Update all series
        for station_code in self.series. keys():
            self._update_series(station_code)
    
    def export_data(self, filename: str, format: str = "csv"):
        """Export current chart data"""
        import csv
        
        if format. lower() == "csv":
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Header
                writer.writerow(['Timestamp', 'Station', 'Frequency', 'Amplitude', 'Phase', 'SNR'])
                
                # Data
                for station_code, data_points in self.signal_data.items():
                    for point in data_points:
                        writer.writerow([
                            point.timestamp.isoformat(),
                            point.station_code,
                            point.frequency,
                            point.amplitude,
                            point. phase,
                            point.snr
                        ])
        
        self.logger.info(f"Chart data exported to {filename}")

class ChartWidget(QWidget):
    """Main chart widget with controls and multiple views"""
    
    # Signals
    event_detected = pyqtSignal(str, dict)
    
    def __init__(self, config_manager: ConfigManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        
        # Chart configuration
        display_config = config_manager.get('display', {})
        self.chart_config = ChartConfig(
            time_range_hours=display_config.get('history_hours', 24),
            update_interval_ms=display_config.get('update_interval', 1000),
            auto_scale=display_config.get('auto_scale', True),
            show_grid=display_config.get('show_grid', True),
            line_width=display_config.get('line_width', 1.5),
            background_color=display_config.get('chart_colors', {}).get('background', '#1e1e1e'),
            text_color=display_config.get('chart_colors', {}).get('text', '#ffffff'),
            grid_color=display_config.get('chart_colors', {}).get('grid', '#404040')
        )
        
        # Data generator
        self.data_generator = DataGenerator(config_manager)
        self.data_generator.data_updated.connect(self.on_data_updated)
        
        self.setup_ui()
        self.setup_stations()
        self.start_monitoring()
        
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Controls panel
        controls_panel = self.create_controls_panel()
        layout.addWidget(controls_panel)
        
        # Main chart view
        self.chart_view = RealtimeChartView(self.chart_config)
        self.chart_view.event_detected.connect(self.event_detected.emit)
        layout.addWidget(self.chart_view)
        
        # Status panel
        status_panel = self. create_status_panel()
        layout.addWidget(status_panel)
        
    def create_controls_panel(self) -> QWidget:
        """Create controls panel"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMaximumHeight(80)
        
        layout = QHBoxLayout(panel)
        
        # Time range control
        layout.addWidget(QLabel("Time Range:"))
        self.time_range_combo = QComboBox()
        self. time_range_combo.addItems(["1 hour", "6 hours", "12 hours", "24 hours", "48 hours"])
        self.time_range_combo.setCurrentText("24 hours")
        self.time_range_combo.currentTextChanged.connect(self.on_time_range_changed)
        layout.addWidget(self. time_range_combo)
        
        layout.addWidget(QLabel("  |  "))
        
        # Start/Stop monitoring
        self.monitor_button = QPushButton("Stop Monitoring")
        self.monitor_button.setCheckable(True)
        self. monitor_button.setChecked(True)
        self.monitor_button.clicked.connect(self. toggle_monitoring)
        layout. addWidget(self.monitor_button)
        
        layout.addWidget(QLabel("  |  "))
        
        # Auto-scale toggle
        self.autoscale_checkbox = QCheckBox("Auto Scale")
        self.autoscale_checkbox.setChecked(self.chart_config.auto_scale)
        self.autoscale_checkbox.toggled.connect(self.toggle_autoscale)
        layout.addWidget(self.autoscale_checkbox)
        
        layout.addStretch()
        
        # Export button
        self.export_button = QPushButton("Export Data")
        self.export_button.clicked.connect(self.export_data)
        layout.addWidget(self.export_button)
        
        return panel
    
    def create_status_panel(self) -> QWidget:
        """Create status information panel"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.Shape.StyledPanel)
        panel.setMaximumHeight(60)
        
        layout = QHBoxLayout(panel)
        
        # Data rate
        layout.addWidget(QLabel("Data Rate:"))
        self.data_rate_label = QLabel("0 Hz")
        layout.addWidget(self.data_rate_label)
        
        layout.addWidget(QLabel("  |  "))
        
        # Active stations
        layout.addWidget(QLabel("Active Stations:"))
        self. stations_label = QLabel("0")
        layout.addWidget(self.stations_label)
        
        layout.addWidget(QLabel("  |  "))
        
        # Events detected
        layout.addWidget(QLabel("Events:"))
        self.events_label = QLabel("0")
        layout.addWidget(self.events_label)
        
        layout.addStretch()
        
        # Current time
        self.time_label = QLabel()
        layout.addWidget(self.time_label)
        
        # Update timer
        self.status_timer = QTimer()
        self.status_timer.timeout. connect(self.update_status)
        self.status_timer. start(1000)
        
        return panel
    
    def setup_stations(self):
        """Setup VLF stations on the chart"""
        stations = self.config_manager.get_vlf_stations()
        enabled_stations = [s for s in stations if s.enabled]
        
        # Station colors
        colors = ["#00ff00", "#0080ff", "#ff8000", "#ff0080", "#80ff00", "#8000ff"]
        
        for i, station in enumerate(enabled_stations[:6]):  # Limit to 6 stations
            color = colors[i % len(colors)]
            self.chart_view.add_station(station.code, station.name, color)
        
        self.stations_label.setText(str(len(enabled_stations)))
        
        self.logger.info(f"Setup {len(enabled_stations)} VLF stations on chart")
    
    def start_monitoring(self):
        """Start data monitoring"""
        self.data_generator.start_generation()
        self.monitor_button.setChecked(True)
        self.monitor_button.setText("Stop Monitoring")
        
        self.logger.info("Chart monitoring started")
    
    def stop_monitoring(self):
        """Stop data monitoring"""
        self. data_generator.stop_generation()
        self.monitor_button.setChecked(False)
        self.monitor_button.setText("Start Monitoring")
        
        self.logger.info("Chart monitoring stopped")
    
    def toggle_monitoring(self):
        """Toggle monitoring on/off"""
        if self. monitor_button.isChecked():
            self.start_monitoring()
        else:
            self.stop_monitoring()
    
    def toggle_autoscale(self, enabled: bool):
        """Toggle auto-scaling"""
        self.chart_config. auto_scale = enabled
        self.logger.info(f"Auto-scale {'enabled' if enabled else 'disabled'}")
    
    def on_time_range_changed(self, text: str):
        """Handle time range change"""
        hours_map = {
            "1 hour": 1,
            "6 hours": 6,
            "12 hours": 12,
            "24 hours": 24,
            "48 hours": 48
        }
        
        hours = hours_map. get(text, 24)
        self.chart_view.set_time_range(hours)
        self.chart_config.time_range_hours = hours
        
        self.logger.info(f"Time range changed to {hours} hours")
    
    def on_data_updated(self, data_point: SignalData):
        """Handle new data point"""
        self.chart_view.update_data(data_point)
    
    def update_status(self):
        """Update status panel"""
        # Current time
        self.time_label.setText(datetime.now().strftime("%H:%M:%S UTC"))
        
        # Update event count
        event_count = len(self.chart_view.event_markers)
        self.events_label.setText(str(event_count))
        
        # Calculate data rate
        if hasattr(self. chart_view, 'update_count'):
            # Simple rate calculation
            self.data_rate_label.setText(f"~{self.chart_view.update_count} Hz")
    
    def export_data(self):
        """Export current chart data"""
        from PyQt6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Chart Data",
            f"vlf_data_{datetime.now(). strftime('%Y%m%d_%H%M%S')}. csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if filename:
            self.chart_view.export_data(filename)
    
    def add_space_weather_overlay(self, space_weather_data):
        """Add space weather events as overlays"""
        if hasattr(space_weather_data, 'solar_flares'):
            self.chart_view.add_space_weather_overlay(
                space_weather_data.solar_flares,
                space_weather_data.geomagnetic
            )
    
    def closeEvent(self, event):
        """Handle widget close"""
        self.stop_monitoring()
        super().closeEvent(event)