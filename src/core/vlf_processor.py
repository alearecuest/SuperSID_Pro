"""
VLF Signal Processor - Real VLF frequencies version  
"""
import numpy as np
from scipy import signal
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from core.logger import get_logger
import time

@dataclass
class VLFSignal:
    """VLF signal data structure"""
    timestamp: float
    frequency: float
    amplitude: float
    phase: float
    station_id: str

class VLFProcessor:
    """Real VLF signal processor for 16-30 kHz bands"""
    
    def __init__(self, sample_rate: int = 11025, station_frequencies: Dict[str, Dict] = None):
        self.sample_rate = sample_rate
        self.logger = get_logger(__name__)
        
        if station_frequencies is None: 
            self.station_frequencies = {
                'NAA': {'freq': 24.0, 'bandwidth': 50},  # 24.0 kHz ± 25 Hz
                'NPM': {'freq': 21.4, 'bandwidth': 50},  # 21.4 kHz ± 25 Hz  
                'NLK': {'freq': 24.8, 'bandwidth': 50},  # 24.8 kHz ± 25 Hz
                'DHO38': {'freq': 23.4, 'bandwidth': 50} # 23.4 kHz ± 25 Hz
            }
        else:
            self.station_frequencies = station_frequencies
            
        self.test_mode = True
        
        if self.test_mode:
            self._create_test_bands()
        else:
            self._create_vlf_bands()
            
        self.filters = {}
        self.baselines = {}
        self._create_filters()
        
    def _create_test_bands(self):
        """Create test bands for audio frequency testing"""
        self.vlf_bands = {}
        
        audio_freqs = [300, 600, 900, 1200, 1500, 1800]  # Hz
        
        for i, (station, info) in enumerate(self.station_frequencies.items()):
            if i < len(audio_freqs):
                center_freq = audio_freqs[i]
                bandwidth = 50  # Hz
                
                self.vlf_bands[station] = (
                    center_freq - bandwidth/2, 
                    center_freq + bandwidth/2
                )
                
        self.logger.info(f"Test mode: Created {len(self.vlf_bands)} audio test bands")

    def _create_vlf_bands(self):
        """Create real VLF bands (requires high sample rate)"""
        self.vlf_bands = {}
        
        if self.sample_rate < 60000:
            self.logger.error(f"Sample rate {self.sample_rate} too low for VLF.  Need 60kHz+")
            return
            
        for station, info in self.station_frequencies.items():
            center_freq = info['freq'] * 1000  # Convert kHz to Hz
            bandwidth = info. get('bandwidth', 50)  # Hz
            
            self. vlf_bands[station] = (
                center_freq - bandwidth/2,
                center_freq + bandwidth/2  
            )
            
        self.logger.info(f"VLF mode: Created {len(self.vlf_bands)} VLF bands")
        
    def _create_filters(self):
        """Create band-pass filters for each station"""
        nyquist = self.sample_rate / 2.0
        
        for station, (low_hz, high_hz) in self.vlf_bands.items():
            try:
                low_norm = low_hz / nyquist
                high_norm = high_hz / nyquist
                
                if 0.01 <= low_norm < high_norm <= 0.99:
                    b, a = signal.butter(4, [low_norm, high_norm], btype='band')
                    self.filters[station] = (b, a)
                    self.logger.debug(f"Filter {station}: {low_hz:. 1f}-{high_hz:. 1f}Hz")
                else:
                    self.logger.warning(f"Invalid filter range {station}: {low_hz}-{high_hz}Hz")
                    
            except Exception as e:
                self.logger.error(f"Filter creation failed for {station}: {e}")
    
    def process_chunk(self, audio_data: np.ndarray) -> Dict[str, VLFSignal]:
        """Process audio data and extract VLF signals"""
        results = {}
        
        if len(audio_data) < 256:
            return results
            
        try:
            if audio_data.ndim > 1:
                audio_data = np.mean(audio_data, axis=1)
                
            if np.max(np.abs(audio_data)) > 0:
                audio_data = audio_data / np.max(np. abs(audio_data))
            
            for station, filter_coeffs in self.filters. items():
                try:
                    b, a = filter_coeffs
                    
                    if len(audio_data) >= len(b) * 3:
                        filtered = signal.filtfilt(b, a, audio_data)
                    else:
                        filtered = signal.lfilter(b, a, audio_data)
                    
                    rms_amplitude = np.sqrt(np. mean(filtered**2))
                    
                    dominant_freq = self._find_dominant_frequency(filtered)
                    
                    if self.test_mode:
                        station_info = self.station_frequencies. get(station, {'freq': 20.0})
                        display_freq = station_info['freq']
                    else:
                        display_freq = dominant_freq / 1000.0
                    
                    if rms_amplitude > 1e-6:
                        analytic = signal.hilbert(filtered)
                        phase = np. angle(np.mean(analytic))
                    else:
                        phase = 0.0
                    
                    vlf_signal = VLFSignal(
                        timestamp=time.time(),
                        frequency=display_freq,
                        amplitude=rms_amplitude,
                        phase=phase,
                        station_id=station
                    )
                    
                    results[station] = vlf_signal
                    
                except Exception as e:
                    self.logger.debug(f"Error processing {station}:  {e}")
        
        except Exception as e: 
            self.logger.error(f"VLF processing error: {e}")
        
        return results
    
    def _find_dominant_frequency(self, signal_data: np.ndarray) -> float:
        """Find the dominant frequency in a signal"""
        if len(signal_data) < 64:
            return 0.0
            
        # FFT
        fft_data = np.fft.fft(signal_data)
        freqs = np.fft.fftfreq(len(signal_data), 1/self.sample_rate)
        
        positive_mask = freqs > 0
        positive_freqs = freqs[positive_mask]
        positive_fft = np.abs(fft_data[positive_mask])
        
        if len(positive_fft) > 0:
            peak_idx = np.argmax(positive_fft)
            return positive_freqs[peak_idx]
        else:
            return 0.0
    
    def update_baseline(self, signals: Dict[str, VLFSignal]):
        """Update baseline levels for anomaly detection"""
        alpha = 0.1
        
        for station, signal_data in signals. items():
            if station not in self.baselines:
                self.baselines[station] = signal_data.amplitude
            else:
                self.baselines[station] = (alpha * signal_data.amplitude + 
                                         (1 - alpha) * self.baselines[station])
    
    def detect_anomalies(self, signals: Dict[str, VLFSignal]) -> List[str]:
        """Detect ionospheric anomalies"""
        anomalies = []
        
        for station, signal_data in signals.items():
            if station in self.baselines and self.baselines[station] > 1e-6:
                baseline = self.baselines[station]
                current = signal_data.amplitude
                
                # Calculate relative change
                change = abs(current - baseline) / baseline
                
                # Detect significant changes (ionospheric events)
                if change > 0.5:
                    direction = "increase" if current > baseline else "decrease"
                    anomalies. append(
                        f"{station}: {change:.1%} amplitude {direction} "
                        f"(baseline:  {baseline:.4f}, current: {current:.4f})"
                    )
        
        return anomalies
    
    def set_real_vlf_mode(self, sample_rate: int = 96000):
        """Switch to real VLF mode with high sample rate"""
        self. sample_rate = sample_rate
        self.test_mode = False
        self._create_vlf_bands()
        self. filters = {}
        self._create_filters()
        self.logger.info(f"Switched to real VLF mode @ {sample_rate}Hz")