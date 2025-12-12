"""
VLF Audio Processor - Real-time VLF signal processing from radio telescope
"""
import numpy as np
from scipy import signal
from scipy.signal import windows
from typing import Dict, List, Tuple, Optional
import threading
import time
from datetime import datetime, timezone
from core.logger import get_logger
from core. vlf_processor import VLFSignal

class VLFAudioProcessor:   
    """Processes real-time audio from radio telescope to extract VLF station data"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        
        audio_config = self.config_manager.config.get('vlf_system', {})
        self.sample_rate = audio_config.get('audio_sample_rate', 44100)
        self.buffer_size = audio_config.get('audio_buffer_size', 4096)
        
        if self.sample_rate < 70000:
            self.logger.warning(f"Sample rate {self.sample_rate} Hz may be too low for VLF frequencies up to 80kHz")
            self.logger.warning("Recommended: 160000 Hz or higher")
            
        self.overlap = 0.5
        
        self.vlf_min_freq = 3000   # 3 kHz
        self.vlf_max_freq = 80000  # 80 kHz
        
        self.is_processing = False
        self.data_callback = None
        self.anomaly_callback = None
        
        self.stations = []
        self.station_freqs = {}
        self.load_station_config()
        
        self.window = windows.hann(self.buffer_size)
        self.freq_bins = np.fft.fftfreq(self.buffer_size, 1/self.sample_rate)
        
        self._cached_windows = {}
        self._cached_freq_bins = {}
        
        self.baselines = {}
        self.baseline_samples = 300
        self.baseline_history = {station: [] for station in self.stations}
        
        self.logger.info(f"VLF Audio Processor initialized for {len(self.stations)} stations")
    
    def validate_audio_config(self, device_info: dict) -> bool:
        """Validate if device supports required parameters"""
        device_sample_rate = device_info.get('sample_rate', 0)
        
        min_required_rate = 60000
        
        if device_sample_rate < min_required_rate:
            self.logger.error(f"Device sample rate {device_sample_rate} too low for VLF")
            self.logger.error(f"Need at least {min_required_rate} Hz for 30kHz VLF signals")
            return False
        
        return True
    
    def load_station_config(self):
        """Load VLF station configuration"""
        config = self.config_manager.config
        self.stations = config.get('vlf_stations', {}).get('monitored_stations', [])
        self.station_freqs = config.get('vlf_stations', {}).get('station_frequencies', {})
        
        self.logger.info(f"Loaded {len(self.stations)} VLF stations for processing")
    
    def register_callbacks(self, data_callback=None, anomaly_callback=None):
        """Register callbacks for data and anomaly notifications"""
        self.data_callback = data_callback
        self.anomaly_callback = anomaly_callback
    
    def _get_window_and_freqs(self, buffer_size: int):
        """Get window and frequency bins for given buffer size (with caching)"""
        if buffer_size not in self._cached_windows:
            self._cached_windows[buffer_size] = windows. hann(buffer_size)
            self._cached_freq_bins[buffer_size] = np.fft.fftfreq(buffer_size, 1/self.sample_rate)
        
        return self._cached_windows[buffer_size], self._cached_freq_bins[buffer_size]
    
    def process_audio_buffer(self, audio_data: np.ndarray) -> Dict[str, VLFSignal]:  
        """Process audio buffer and extract VLF station data"""
        try:
            if audio_data is None or len(audio_data) == 0:
                return {}
                
            if not np.isfinite(audio_data).all():
                if not hasattr(self, '_nan_warning_logged'):
                    self.logger.warning("Audio device producing invalid data - cleaning automatically")
                    self._nan_warning_logged = True
                audio_data = np.nan_to_num(audio_data, nan=0.0, posinf=0.0, neginf=0.0)
            
            if audio_data.dtype != np.float64:
                audio_data = audio_data.astype(np.float64)
            
            actual_buffer_size = len(audio_data)
            
            window, freq_bins = self._get_window_and_freqs(actual_buffer_size)
            
            windowed_data = audio_data * window
            
            fft_data = np.fft.fft(windowed_data)
            power_spectrum = np.abs(fft_data) ** 2
            
            if not np.isfinite(power_spectrum).all():
                self. logger.warning("Power spectrum contains invalid values")
                power_spectrum = np.nan_to_num(power_spectrum, nan=0.0, posinf=0.0, neginf=0.0)
            
            vlf_signals = {}
            current_time = time.time()
            
            for i, station in enumerate(self.stations):
                try:
                    station_info = self.station_freqs. get(station, {})
                    target_freq = station_info.get('freq', 20.0) * 1000
                    
                    if target_freq < self.vlf_min_freq or target_freq > self.vlf_max_freq:
                        continue
                    
                    freq_bin_idx = np.argmin(np.abs(freq_bins - target_freq))
                    
                    bandwidth_bins = max(1, int(100 / (self.sample_rate / actual_buffer_size)))
                    start_bin = max(0, freq_bin_idx - bandwidth_bins // 2)
                    end_bin = min(len(power_spectrum), freq_bin_idx + bandwidth_bins // 2 + 1)
                    
                    band_power = np.mean(power_spectrum[start_bin:end_bin])
                    
                    if not np.isfinite(band_power) or band_power < 0:
                        band_power = 0.0
                    
                    raw_amplitude = np.sqrt(band_power) / actual_buffer_size
                    amplitude = float(raw_amplitude) if np.isfinite(raw_amplitude) else 0.0
                    
                    raw_freq = freq_bins[freq_bin_idx] / 1000
                    actual_freq = float(raw_freq) if np.isfinite(raw_freq) else target_freq / 1000
                    
                    amplitude = max(0.0, min(amplitude, 1.0))
                    
                    band_id = station
                    signal_obj = VLFSignal(
                        timestamp=current_time,
                        frequency=actual_freq,
                        amplitude=amplitude,
                        phase=0.0,
                        station_id=band_id
                    )
                    
                    vlf_signals[band_id] = signal_obj
                    
                    if np.isfinite(amplitude):
                        self.update_baseline(station, amplitude)
                    
                except Exception as e:  
                    self.logger. warning(f"Error processing station {station}:  {e}")
                    continue
            
            #self.check_anomalies(vlf_signals, current_time)
            
            return vlf_signals
            
        except Exception as e:
            self.logger.error(f"Error in audio processing:  {e}")
            return {}
    
    def update_baseline(self, station: str, amplitude:  float):
        """Update baseline amplitude for anomaly detection"""
        if not np.isfinite(amplitude):
            return
            
        if station not in self. baseline_history:
            self.baseline_history[station] = []
        
        self.baseline_history[station].append(amplitude)
        
        if len(self.baseline_history[station]) > self.baseline_samples:
            self.baseline_history[station]. pop(0)
        
        if len(self.baseline_history[station]) >= 10:
            values = self.baseline_history[station]
            mean_val = np.mean(values)
            std_val = np.std(values)
            min_val = np.min(values)
            max_val = np.max(values)
            
            if all(np.isfinite([mean_val, std_val, min_val, max_val])):
                self.baselines[station] = {
                    'mean': float(mean_val),
                    'std':  float(std_val),
                    'min': float(min_val),
                    'max':  float(max_val)
                }
    
    def check_anomalies(self, vlf_signals: Dict[str, VLFSignal], timestamp: float):
        """Check for signal anomalies"""
        anomalies = []
        
        for band_id, signal in vlf_signals.items():
            try:
                band_num = int(band_id.split('_')[1]) - 1
                if band_num >= len(self. stations):
                    continue
                
                station = self.stations[band_num]
                
                if station in self.baselines:
                    baseline = self.baselines[station]
                    amplitude = signal.amplitude
                    
                    if not np.isfinite(amplitude):
                        continue
                        
                    if baseline['std'] > 0: 
                        z_score = abs(amplitude - baseline['mean']) / baseline['std']
                        if np.isfinite(z_score) and z_score > 3.0:
                            if amplitude > baseline['mean']: 
                                anomalies.append(f"{band_id} ({station}): Signal spike detected (amplitude: {amplitude:.4f}, baseline: {baseline['mean']:.4f})")
                            else:
                                anomalies.append(f"{band_id} ({station}): Signal drop detected (amplitude: {amplitude:.4f}, baseline: {baseline['mean']:.4f})")
                    
                    if amplitude < baseline['mean'] * 0.1 and baseline['mean'] > 0.001:
                        anomalies.append(f"{band_id} ({station}): Possible signal loss")
            
            except Exception as e: 
                self.logger.warning(f"Error checking anomalies for {band_id}:  {e}")
        
        if anomalies and self.anomaly_callback:
            try: 
                self.anomaly_callback(anomalies, datetime.fromtimestamp(timestamp, tz=timezone.utc))
            except Exception as e:
                self. logger.error(f"Error sending anomaly callback: {e}")
    
    def start_processing(self):
        """Start VLF processing"""
        self.is_processing = True
        self.logger.info("VLF Audio Processor started")
    
    def stop_processing(self):
        """Stop VLF processing"""
        self.is_processing = False
        self.logger.info("VLF Audio Processor stopped")
    
    def get_status(self) -> Dict:
        """Get processor status"""
        return {
            'is_processing':  self.is_processing,
            'stations_configured': len(self.stations),
            'sample_rate': self.sample_rate,
            'buffer_size': self.buffer_size,
            'baselines_established': len(self.baselines)
        }