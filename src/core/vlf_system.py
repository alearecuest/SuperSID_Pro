"""
VLF Monitoring System - Real audio integration
"""
import asyncio
import numpy as np
import pyaudio
from typing import Dict, List, Callable, Optional
from core.vlf_processor import VLFProcessor, VLFSignal
from core.config_manager import ConfigManager
from core. logger import get_logger
from data.realtime_storage import RealtimeStorage
import threading
import queue
import time

class VLFMonitoringSystem:
    """Complete VLF monitoring system with real audio"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_monitoring = False
        
        config = config_manager.config
        audio_config = config.get('audio_settings', {})
        vlf_config = config.get('vlf_system', {})
        
        self.device_index = audio_config.get('device_index', None)
        self.sample_rate = audio_config.get('sample_rate', 11025) 
        self.buffer_size = audio_config.get('buffer_size', 1024)
        self.channels = audio_config.get('channels', 1)
        
        stations_config = config.get('vlf_stations', {})
        station_frequencies = stations_config.get('station_frequencies', {})
        
        self.vlf_processor = VLFProcessor(
            sample_rate=self.sample_rate,
            station_frequencies=station_frequencies
        )
        
        self.storage = RealtimeStorage()
        self.data_callbacks = []
        self.anomaly_callbacks = []
        
        self.audio_queue = queue.Queue(maxsize=10)
        self.processing_thread = None
        self.audio_thread = None
        
        self.logger.info("VLF Monitoring System initialized")
        
    def register_data_callback(self, callback: Callable[[Dict[str, VLFSignal]], None]):
        """Register callback for VLF data"""
        self.data_callbacks.append(callback)
        
    def register_anomaly_callback(self, callback: Callable[[List[str], any], None]):
        """Register callback for anomalies"""
        self.anomaly_callbacks.append(callback)
        
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback - runs in audio thread"""
        if status:
            self.logger.warning(f"Audio status: {status}")
            
        try:
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            
            audio_data = audio_data.astype(np. float32) / 32768.0
            
            try:
                self.audio_queue.put_nowait(audio_data)
            except queue.Full:
                try:
                    self.audio_queue.get_nowait()
                    self.audio_queue.put_nowait(audio_data)
                except queue.Empty:
                    pass
                    
        except Exception as e: 
            self.logger.error(f"Audio callback error: {e}")
            
        return (in_data, pyaudio. paContinue)
        
    def _processing_worker(self):
        """Background thread for VLF processing"""
        self.logger.info("VLF processing worker started")
        
        while self.is_monitoring:
            try:
                try:
                    audio_data = self.audio_queue.get(timeout=1.0)
                except queue. Empty:
                    continue
                    
                vlf_signals = self.vlf_processor.process_chunk(audio_data)
                
                if vlf_signals:
                    self.vlf_processor.update_baseline(vlf_signals)
                    
                    self._store_signals(vlf_signals)
                    
                    for callback in self.data_callbacks:
                        try:
                            callback(vlf_signals)
                        except Exception as e:
                            self. logger.error(f"Data callback error: {e}")
                    
                    anomalies = self.vlf_processor.detect_anomalies(vlf_signals)
                    if anomalies:
                        self.logger.info(f"Anomalies detected: {anomalies}")
                        
                        for callback in self.anomaly_callbacks:
                            try:
                                callback(anomalies, time.time())
                            except Exception as e:
                                self. logger.error(f"Anomaly callback error: {e}")
                
            except Exception as e:
                self.logger.error(f"Processing worker error: {e}")
                time.sleep(0.1)
                
        self.logger.info("VLF processing worker stopped")
        
    def _store_signals(self, vlf_signals: Dict[str, VLFSignal]):
        """Store VLF signals to database"""
        try:
            for signal in vlf_signals. values():
                self.storage. store_measurement(signal)
        except Exception as e:
            self.logger.error(f"Storage error: {e}")
            
    def start_monitoring(self) -> bool:
        """Start VLF monitoring with real audio"""
        if self.is_monitoring:
            self.logger.warning("Monitoring already active")
            return True
            
        try:
            if self.device_index is None:
                self. logger.warning("No audio device configured, using default")
                self.device_index = None
                
            if not self._test_audio_device():
                self.logger.error("Audio device test failed")
                return False
            
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.buffer_size,
                stream_callback=self._audio_callback
            )
            
            self.is_monitoring = True
            
            self.processing_thread = threading.Thread(
                target=self._processing_worker, 
                daemon=True
            )
            self.processing_thread.start()
            
            self.stream.start_stream()
            
            self.logger.info(f"VLF monitoring started - Device: {self.device_index}, "
                           f"Rate:  {self.sample_rate}Hz, Buffer: {self.buffer_size}")
            return True
            
        except Exception as e: 
            self.logger.error(f"Failed to start monitoring: {e}")
            self.stop_monitoring()
            return False
            
    def stop_monitoring(self):
        """Stop VLF monitoring"""
        self.logger.info("Stopping VLF monitoring...")
        
        self.is_monitoring = False
        
        if self. stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e: 
                self.logger.error(f"Error stopping audio stream: {e}")
            self.stream = None
            
        if self.processing_thread and self.processing_thread. is_alive():
            self.processing_thread.join(timeout=2.0)
            
        try: 
            while True:
                self.audio_queue.get_nowait()
        except queue.Empty:
            pass
            
        self.logger.info("VLF monitoring stopped")
        
    def _test_audio_device(self) -> bool:
        """Test if audio device works"""
        try:
            test_stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self. channels,
                rate=self. sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.buffer_size
            )
            
            test_data = test_stream.read(self. buffer_size, exception_on_overflow=False)
            test_stream.stop_stream()
            test_stream.close()
            
            self.logger.info(f"Audio device {self.device_index} test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Audio device test failed: {e}")
            return False
            
    def get_system_status(self) -> Dict:
        """Get system status"""
        return {
            "is_monitoring": self.is_monitoring,
            "sample_rate":  self.sample_rate,
            "buffer_size": self.buffer_size,
            "device_index": self.device_index,
            "audio_queue_size": self.audio_queue.qsize() if hasattr(self, 'audio_queue') else 0,
            "vlf_bands_count": len(self. vlf_processor.vlf_bands),
            "baselines_count": len(self.vlf_processor.baselines)
        }
        
    def cleanup(self):
        """Cleanup resources"""
        self.stop_monitoring()
        
        if hasattr(self, 'audio'):
            try:
                self.audio.terminate()
            except Exception as e:
                self.logger. error(f"Error terminating audio:  {e}")