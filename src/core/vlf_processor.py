"""
VLF Signal Processor - Clean and functional version
"""
import numpy as np
from scipy import signal
from dataclasses import dataclass
from typing import Dict, List
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
    """Simple and robust VLF signal processor"""
    
    def __init__(self, sample_rate: int = 11025):
        self.sample_rate = sample_rate
        self.logger = get_logger(__name__)
        
        # Simple frequency bands in Hz (well within Nyquist limit)
        self.vlf_bands = {
            'BAND_1': (200, 400),   # 200-400 Hz
            'BAND_2': (400, 800),   # 400-800 Hz  
            'BAND_3': (800, 1200),  # 800-1200 Hz
            'BAND_4': (1200, 2000), # 1200-2000 Hz
        }
        
        # Initialize filters
        self.filters = {}
        self._create_filters()
        
    def _create_filters(self):
        """Create band-pass filters for each band"""
        nyquist = self.sample_rate / 2.0
        
        for band_name, (low_hz, high_hz) in self. vlf_bands.items():
            try:
                # Normalize to [0, 1] range
                low_norm = low_hz / nyquist
                high_norm = high_hz / nyquist
                
                # Ensure valid range
                if low_norm >= 0.01 and high_norm <= 0.99 and low_norm < high_norm:
                    # Create simple 2nd order filter
                    b, a = signal.butter(2, [low_norm, high_norm], btype='band')
                    self.filters[band_name] = (b, a)
                    self.logger.debug(f"Filter {band_name}: {low_hz}-{high_hz}Hz created")
                else:
                    self.logger.warning(f"Invalid freq range for {band_name}: {low_hz}-{high_hz}Hz")
                    
            except Exception as e:
                self.logger.error(f"Filter creation failed for {band_name}: {e}")
    
    def process_chunk(self, audio_data: np.ndarray) -> Dict[str, VLFSignal]:
        """Process audio data and return VLF signals"""
        results = {}
        
        # Validate input
        if len(audio_data) < 50:
            return results
            
        try:
            # Ensure 1D array
            if audio_data.ndim > 1:
                audio_data = audio_data.flatten()
            
            # Process each frequency band
            for band_name, filter_coeffs in self.filters.items():
                try:
                    b, a = filter_coeffs
                    
                    # Apply band-pass filter
                    filtered_signal = signal.filtfilt(b, a, audio_data)
                    
                    # Calculate signal amplitude (RMS)
                    amplitude = np.sqrt(np.mean(filtered_signal**2))
                    
                    # Estimate frequency using FFT
                    if len(filtered_signal) >= 64:
                        fft = np.fft.fft(filtered_signal)
                        freqs = np.fft.fftfreq(len(filtered_signal), 1/self.sample_rate)
                        
                        # Find peak frequency in positive spectrum
                        positive_freqs = freqs[:len(freqs)//2]
                        positive_fft = np.abs(fft[:len(fft)//2])
                        
                        if len(positive_fft) > 0:
                            peak_idx = np.argmax(positive_fft)
                            peak_frequency = positive_freqs[peak_idx] / 1000.0  # Convert to kHz
                        else:
                            peak_frequency = 0.0
                    else:
                        peak_frequency = 0.0
                    
                    # Calculate phase
                    if amplitude > 0:
                        analytic = signal.hilbert(filtered_signal)
                        phase = np.mean(np.angle(analytic))
                    else:
                        phase = 0.0
                    
                    # Create VLF signal
                    vlf_signal = VLFSignal(
                        timestamp=time.time(),
                        frequency=peak_frequency,
                        amplitude=amplitude,
                        phase=phase,
                        station_id=band_name
                    )
                    
                    results[band_name] = vlf_signal
                    
                    # Log if significant signal detected
                    if amplitude > 0.001:
                        self.logger. debug(f"{band_name}: amp={amplitude:.6f}, freq={peak_frequency:.3f}kHz")
                
                except Exception as e:
                    self.logger.debug(f"Error processing {band_name}: {e}")
        
        except Exception as e:
            self.logger.error(f"VLF processing error: {e}")
        
        return results
    
    def detect_anomalies(self, signals: Dict[str, VLFSignal], baseline: Dict[str, float] = None) -> List[str]:
        """Detect signal anomalies"""
        anomalies = []
        
        if not baseline:
            return anomalies
            
        for station_id, signal_data in signals. items():
            if station_id in baseline and baseline[station_id] > 0:
                baseline_amp = baseline[station_id]
                amplitude_change = abs(signal_data.amplitude - baseline_amp) / baseline_amp
                
                if amplitude_change > 0.3:  # 30% threshold
                    anomalies.append(f"{station_id}: {amplitude_change:.1%} amplitude change")
        
        return anomalies
