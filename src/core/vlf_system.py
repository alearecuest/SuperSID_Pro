"""
VLF Real-time Monitoring System - Main Integration Hub
Connects audio capture, signal processing, and data storage
"""
import time
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass

from core.audio_capture import VLFAudioCapture, AudioConfig
from core.vlf_processor import VLFProcessor, VLFSignal
from data. realtime_storage import RealtimeStorage, VLFMeasurement
from core.logger import get_logger
from core.config_manager import ConfigManager

@dataclass
class VLFSystemConfig:
    """Configuration for the VLF monitoring system"""
    audio_sample_rate: int = 11025
    audio_buffer_size: int = 1024
    audio_device: Optional[int] = None
    storage_batch_size: int = 10
    anomaly_detection: bool = True
    baseline_update_interval: int = 300  # seconds

class VLFMonitoringSystem:
    """
    Main VLF Real-time Monitoring System
    Integrates all components for continuous VLF monitoring
    """
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        
        # Load VLF system configuration
        self.vlf_config = self._load_vlf_config()
        
        # Initialize components
        self._init_components()
        
        # Data storage
        self.measurement_buffer: List[VLFMeasurement] = []
        self.baseline_data: Dict[str, float] = {}
        self.last_baseline_update = 0
        
        # Callbacks for real-time updates
        self.data_callbacks: List[Callable] = []
        self.anomaly_callbacks: List[Callable] = []
        
        self.logger.info("VLF Monitoring System initialized")
        
    def _load_vlf_config(self) -> VLFSystemConfig:
        """Load VLF configuration from config manager"""
        config_data = self.config_manager.get('vlf_system', {})
        
        return VLFSystemConfig(
            audio_sample_rate=config_data.get('audio_sample_rate', 11025),
            audio_buffer_size=config_data.get('audio_buffer_size', 1024),
            audio_device=config_data.get('audio_device'),
            storage_batch_size=config_data.get('storage_batch_size', 10),
            anomaly_detection=config_data.get('anomaly_detection', True),
            baseline_update_interval=config_data.get('baseline_update_interval', 300)
        )
        
    def _init_components(self):
        """Initialize all system components"""
        # Audio configuration
        audio_config = AudioConfig(
            sample_rate=self.vlf_config.audio_sample_rate,
            buffer_size=self.vlf_config.audio_buffer_size,
            device=self.vlf_config.audio_device
        )
        
        # Initialize components
        self.audio_capture = VLFAudioCapture(audio_config, self._process_audio_data)
        self.vlf_processor = VLFProcessor(self.vlf_config. audio_sample_rate)
        self.storage = RealtimeStorage()
        
        self.logger.info("VLF system components initialized")
        
    def _process_audio_data(self, audio_data: np.ndarray, sample_rate: int):
        """Main audio processing callback"""
        try:
            # Process VLF signals
            vlf_signals = self.vlf_processor.process_chunk(audio_data)
            
            # Convert to measurements
            timestamp = datetime.now(timezone.utc)
            measurements = []
            
            for station_id, signal_data in vlf_signals.items():
                measurement = VLFMeasurement(
                    timestamp=timestamp,
                    station_id=station_id,
                    frequency=signal_data.frequency,
                    amplitude=signal_data.amplitude,
                    phase=signal_data.phase
                )
                measurements.append(measurement)
            
            # Buffer measurements for batch storage
            self.measurement_buffer. extend(measurements)
            
            # Store batch if buffer is full
            if len(self.measurement_buffer) >= self. vlf_config.storage_batch_size:
                self. storage.store_batch(self. measurement_buffer)
                self. measurement_buffer. clear()
            
            # Check for anomalies
            if self.vlf_config.anomaly_detection:
                anomalies = self. vlf_processor.detect_anomalies(vlf_signals, self.baseline_data)
                if anomalies:
                    self._handle_anomalies(anomalies, timestamp)
            
            # Update baseline periodically
            current_time = time.time()
            if current_time - self. last_baseline_update > self.vlf_config.baseline_update_interval:
                self._update_baseline()
                self. last_baseline_update = current_time
            
            # Call registered callbacks with real-time data
            self._notify_data_callbacks(vlf_signals)
            
        except Exception as e:
            self.logger.error(f"Error processing audio data: {e}")
    
    def _handle_anomalies(self, anomalies: List[str], timestamp: datetime):
        """Handle detected anomalies"""
        self.logger.warning(f"VLF anomalies detected at {timestamp}: {anomalies}")
        
        # Notify anomaly callbacks
        for callback in self.anomaly_callbacks:
            try:
                callback(anomalies, timestamp)
            except Exception as e:
                self.logger. error(f"Error in anomaly callback: {e}")
    
    def _update_baseline(self):
        """Update baseline signal levels"""
        try:
            # Get recent data for each station
            for station in ['NAA', 'NWC', 'DHO', 'GQD']:
                recent_data = self. storage.get_recent_data(station, minutes=30)
                
                if recent_data:
                    # Calculate average amplitude as baseline
                    amplitudes = [m.amplitude for m in recent_data]
                    self.baseline_data[station] = np.mean(amplitudes)
            
            self.logger.debug("Updated baseline data")
            
        except Exception as e:
            self.logger.error(f"Error updating baseline: {e}")
    
    def _notify_data_callbacks(self, vlf_signals: Dict[str, VLFSignal]):
        """Notify registered callbacks with new data"""
        for callback in self.data_callbacks:
            try:
                callback(vlf_signals)
            except Exception as e:
                self.logger.error(f"Error in data callback: {e}")
    
    def start_monitoring(self):
        """Start the VLF monitoring system"""
        try:
            self.logger.info("Starting VLF monitoring system...")
            
            # Start audio capture
            self. audio_capture.start_capture()
            
            self.logger.info("VLF monitoring system started successfully")
            
        except Exception as e:
            self.logger. error(f"Failed to start VLF monitoring: {e}")
            raise
    
    def stop_monitoring(self):
        """Stop the VLF monitoring system"""
        try:
            self. logger.info("Stopping VLF monitoring system...")
            
            # Stop audio capture
            self. audio_capture.stop_capture()
            
            # Store any remaining buffered measurements
            if self.measurement_buffer:
                self.storage.store_batch(self.measurement_buffer)
                self.measurement_buffer.clear()
            
            self.logger.info("VLF monitoring system stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping VLF monitoring: {e}")
    
    def register_data_callback(self, callback: Callable[[Dict[str, VLFSignal]], None]):
        """Register callback for real-time data updates"""
        self.data_callbacks.append(callback)
        
    def register_anomaly_callback(self, callback: Callable[[List[str], datetime], None]):
        """Register callback for anomaly notifications"""
        self.anomaly_callbacks.append(callback)
    
    def get_system_status(self) -> Dict:
        """Get current system status"""
        return {
            'is_monitoring': self.audio_capture.is_capturing if hasattr(self, 'audio_capture') else False,
            'buffer_size': len(self.measurement_buffer),
            'baseline_stations': list(self.baseline_data.keys()),
            'last_baseline_update': self.last_baseline_update,
            'available_devices': self.audio_capture.get_available_devices() if hasattr(self, 'audio_capture') else []
        }
    
    def get_available_audio_devices(self) -> List[tuple]:
        """Get available audio input devices"""
        if hasattr(self, 'audio_capture'):
            return self. audio_capture.get_available_devices()
        return []
