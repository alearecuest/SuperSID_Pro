"""
VLF System GUI Integration
Connects VLF monitoring with real-time visualization
"""
from PyQt6.QtCore import QObject, QThread, pyqtSignal, QTimer
from PyQt6.QtWidgets import QMessageBox
from typing import Dict, Optional
import time

from core.vlf_system import VLFMonitoringSystem
from core.vlf_processor import VLFSignal
from core.config_manager import ConfigManager
from core.logger import get_logger

class VLFWorkerThread(QThread):
    """Worker thread for VLF monitoring to avoid blocking GUI"""
    
    data_received = pyqtSignal(dict)  # VLF signals data
    anomaly_detected = pyqtSignal(list, object)  # anomalies, timestamp
    status_changed = pyqtSignal(str)  # status message
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        self.vlf_system = None
        self.is_monitoring = False
        
    def start_monitoring(self):
        """Start VLF monitoring"""
        try:
            if not self.vlf_system:
                self. vlf_system = VLFMonitoringSystem(self.config_manager)
                
                # Register callbacks
                self.vlf_system.register_data_callback(self._on_vlf_data)
                self. vlf_system.register_anomaly_callback(self._on_anomaly)
            
            self.vlf_system.start_monitoring()
            self.is_monitoring = True
            self.status_changed.emit("VLF monitoring started")
            self.logger.info("VLF monitoring started from GUI")
            
        except Exception as e:
            self.logger.error(f"Failed to start VLF monitoring: {e}")
            self.status_changed.emit(f"Error: {e}")
    
    def stop_monitoring(self):
        """Stop VLF monitoring"""
        try:
            if self.vlf_system:
                self. vlf_system.stop_monitoring()
            self.is_monitoring = False
            self.status_changed.emit("VLF monitoring stopped")
            self.logger.info("VLF monitoring stopped from GUI")
            
        except Exception as e:
            self.logger.error(f"Error stopping VLF monitoring: {e}")
            self.status_changed.emit(f"Stop error: {e}")
    
    def _on_vlf_data(self, vlf_signals: Dict[str, VLFSignal]):
        """Handle VLF data callback"""
        # Convert VLFSignal objects to dict for signal emission
        signal_data = {}
        for station, signal in vlf_signals. items():
            signal_data[station] = {
                'timestamp': signal.timestamp,
                'frequency': signal.frequency,
                'amplitude': signal.amplitude,
                'phase': signal.phase,
                'station_id': signal.station_id
            }
        
        self. data_received.emit(signal_data)
    
    def _on_anomaly(self, anomalies, timestamp):
        """Handle anomaly detection callback"""
        self.anomaly_detected.emit(anomalies, timestamp)
    
    def run(self):
        """Main thread loop"""
        while self.is_monitoring:
            time.sleep(0.1)  # Small delay to prevent high CPU usage

class VLFGUIIntegration(QObject):
    """Integration layer between VLF system and GUI"""
    
    def __init__(self, config_manager: ConfigManager, vlf_widget):
        super().__init__()
        self.config_manager = config_manager
        self.vlf_widget = vlf_widget
        self.logger = get_logger(__name__)
        
        # Create worker thread
        self.worker = VLFWorkerThread(config_manager)
        
        # Connect signals
        self._connect_signals()
        
        self.logger.info("VLF GUI integration initialized")
    
    def _connect_signals(self):
        """Connect worker signals to GUI"""
        # Connect worker signals to methods
        self.worker.data_received.connect(self._handle_vlf_data)
        self.worker.anomaly_detected.connect(self._handle_anomaly)
        self.worker. status_changed.connect(self._handle_status_change)
        
        # Connect GUI signals to worker
        self.vlf_widget.start_button.clicked.connect(self._toggle_monitoring)
    
    def _handle_vlf_data(self, signal_data: Dict):
        """Handle incoming VLF data"""
        # Convert back to VLFSignal objects for the widget
        vlf_signals = {}
        for station, data in signal_data.items():
            # Create a simple object with the required attributes
            class SimpleSignal:
                def __init__(self, data):
                    self.timestamp = data['timestamp']
                    self.frequency = data['frequency']
                    self.amplitude = data['amplitude']
                    self. phase = data['phase']
                    self.station_id = data['station_id']
            
            vlf_signals[station] = SimpleSignal(data)
        
        # Send to visualization widget
        self.vlf_widget.add_vlf_data(vlf_signals)
    
    def _handle_anomaly(self, anomalies, timestamp):
        """Handle anomaly detection"""
        for anomaly in anomalies:
            # Extract station from anomaly message
            station = anomaly.split(':')[0] if ':' in anomaly else 'Unknown'
            self.vlf_widget.show_anomaly(station, anomaly)
        
        self.logger.warning(f"Anomalies detected: {anomalies}")
    
    def _handle_status_change(self, status: str):
        """Handle status changes"""
        self.vlf_widget.status_label.setText(f"Status: {status}")
        self.logger.info(f"VLF status: {status}")
    
    def _toggle_monitoring(self):
        """Toggle VLF monitoring on/off"""
        if not self.worker.is_monitoring:
            # Start monitoring
            self.worker. start_monitoring()
            if not self.worker.isRunning():
                self.worker.start()
        else:
            # Stop monitoring
            self.worker. stop_monitoring()
    
    def cleanup(self):
        """Cleanup resources"""
        if self.worker.is_monitoring:
            self.worker.stop_monitoring()
        if self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()