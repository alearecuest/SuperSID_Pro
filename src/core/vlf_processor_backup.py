"""
VLF Signal Processor - Real-time signal analysis
"""
import numpy as np
from scipy import signal
from dataclasses import dataclass
from typing import Dict, List, Tuple
from core.logger import get_logger

@dataclass
class VLFSignal:
    """VLF signal data structure"""
    timestamp: float
    frequency: float
    amplitude: float
    phase: float
    station_id: str

class VLFProcessor:
    """Real-time VLF signal processor"""
    
    def __init__(self, sample_rate: int = 11025):
        self.sample_rate = sample_rate
        self.logger = get_logger(__name__)
        
        # VLF-like frequency bands (adjusted for audio sampling)
        # Simulated bands since real VLF is above our sample rate
        self.vlf_bands = {
            'NAA_SIM': (0.5, 1.0),   # Simulated NAA signal (500Hz-1kHz)
            'NWC_SIM': (1.0, 1.5),   # Simulated NWC signal (1-1.5kHz)
            'DHO_SIM': (1.5, 2.0),   # Simulated DHO signal (1.5-2kHz)
            'GQD_SIM': (2.0, 2.5),   # Simulated GQD signal (2-2.5kHz)
        }
        
        # Initialize filters
        self._init_filters()
        
    def _init_filters(self):
        """Initialize band-pass filters for VLF-like signals"""
        self.filters = {}
        
        for station, (low, high) in self.vlf_bands.items():
            try:
                # Design band-pass filter
                nyquist = self.sample_rate / 2
                low_norm = low * 1000 / nyquist  # Convert kHz to normalized freq
                high_norm = high * 1000 / nyquist
                
                # Ensure frequencies are within valid range (0 < f < 1)
                low_norm = max(0.01, min(0.95, low_norm))
                high_norm = max(low_norm + 0.05, min(0.98, high_norm))
                
                b, a = signal.butter(4, [low_norm, high_norm], btype='band')
                self.filters[station] = (b, a)
                self.logger.debug(f"Created filter for {station}: {low_norm:.3f}-{high_norm:.3f}")
                
            except Exception as e:
                self.logger.error(f"Failed to create filter for {station}: {e}")
                
    def process_chunk(self, audio_data: np.ndarray) -> Dict[str, VLFSignal]:
        """Process audio chunk and extract VLF-like signals"""
        results = {}
        
        try:
            # Ensure we have enough data
            if len(audio_data) < 10:
                return results
                
            # Apply each filter and analyze
            for station, (b, a) in self.filters.items():
                try:
                    # Filter the signal
                    filtered = signal.filtfilt(b, a, audio_data)
                    
                    # Calculate signal strength (RMS)
                    rms = np.sqrt(np. mean(filtered**2))
                    
                    # Calculate dominant frequency
                    nperseg = min(len(filtered), 256)
                    if nperseg >= 4:
                        freqs, psd = signal.welch(filtered, self.sample_rate, nperseg=nperseg)
                        if len(psd) > 0:
                            dominant_freq_idx = np.argmax(psd)
                            dominant_freq = freqs[dominant_freq_idx] / 1000  # Convert to kHz
                        else:
                            dominant_freq = 0.0
                    else:
                        dominant_freq = 0.0
                    
                    # Calculate phase (simple approach)
                    if len(filtered) > 1:
                        analytic_signal = signal.hilbert(filtered)
                        phase = np.angle(analytic_signal)
                        mean_phase = np.mean(phase)
                    else:
                        mean_phase = 0.0
                    
                    # Create VLF signal object
                    vlf_signal = VLFSignal(
                        timestamp=np.time. time(),
                        frequency=dominant_freq,
                        amplitude=rms,
                        phase=mean_phase,
                        station_id=station
                    )
                    
                    results[station] = vlf_signal
                    
                except Exception as e:
                    self.logger.debug(f"Error processing {station}: {e}")
                
        except Exception as e:
            self.logger.error(f"VLF processing error: {e}")
            
        return results
        
    def detect_anomalies(self, signals: Dict[str, VLFSignal], baseline: Dict[str, float] = None) -> List[str]:
        """Detect signal anomalies (potential space weather events)"""
        anomalies = []
        
        if not baseline:
            return anomalies
            
        for station, signal_data in signals.items():
            if station in baseline:
                # Check for amplitude changes
                baseline_amp = baseline[station]
                if baseline_amp > 0:  # Avoid division by zero
                    amplitude_change = abs(signal_data.amplitude - baseline_amp) / baseline_amp
                    
                    if amplitude_change > 0.2:  # 20% threshold
                        anomalies.append(f"{station}: {amplitude_change:.1%} amplitude change")
                        
        return anomalies
