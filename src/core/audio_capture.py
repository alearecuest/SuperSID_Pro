"""
Professional VLF Audio Capture System
Real-time audio processing for SuperSID Pro
"""
import numpy as np
import sounddevice as sd
import threading
import queue
from typing import Optional, Callable
from dataclasses import dataclass
from core.logger import get_logger

@dataclass
class AudioConfig:
    """Audio capture configuration"""
    sample_rate: int = 11025  # VLF optimal rate
    channels: int = 1         # Mono capture
    buffer_size: int = 1024   # Samples per buffer
    device: Optional[int] = None  # Auto-select device

class VLFAudioCapture:
    """Professional VLF audio capture system"""
    
    def __init__(self, config: AudioConfig, callback: Callable):
        self. config = config
        self.callback = callback
        self.logger = get_logger(__name__)
        
        self.is_capturing = False
        self.audio_queue = queue.Queue()
        self.capture_thread = None
        
    def start_capture(self):
        """Start real-time audio capture"""
        if self. is_capturing:
            return
        
        self.is_capturing = True
        self.logger. info(f"Starting VLF audio capture at {self.config. sample_rate}Hz")
        
        try:
            # Start audio stream
            self.stream = sd.InputStream(
                samplerate=self.config. sample_rate,
                channels=self.config.channels,
                callback=self._audio_callback,
                blocksize=self.config.buffer_size,
                device=self.config.device
            )
            self.stream.start()
            
            # Start processing thread
            self.capture_thread = threading.Thread(target=self._process_audio)
            self.capture_thread.daemon = True
            self.capture_thread. start()
            
            self. logger.info("VLF audio capture started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start audio capture: {e}")
            self.is_capturing = False
            
    def _audio_callback(self, indata, frames, time, status):
        """Real-time audio callback"""
        if status:
            self. logger. warning(f"Audio callback status: {status}")
        
        # Add audio data to processing queue
        self.audio_queue.put(indata.copy())
        
    def _process_audio(self):
        """Process audio data in separate thread"""
        while self. is_capturing:
            try:
                # Get audio data (with timeout)
                audio_data = self.audio_queue.get(timeout=1.0)
                
                # Process the audio chunk
                self._process_chunk(audio_data)
                
            except queue.Empty:
                continue  # Continue if no data
            except Exception as e:
                self. logger.error(f"Audio processing error: {e}")
                
    def _process_chunk(self, audio_data):
        """Process individual audio chunk"""
        # Convert to mono if needed
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
            
        # Call user callback with processed data
        self.callback(audio_data, self.config.sample_rate)
        
    def stop_capture(self):
        """Stop audio capture"""
        if not self.is_capturing:
            return
            
        self. is_capturing = False
        
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
            
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
            
        self.logger.info("VLF audio capture stopped")
        
    def get_available_devices(self):
        """Get list of available audio devices"""
        devices = sd.query_devices()
        return [(i, dev['name']) for i, dev in enumerate(devices) 
                if dev['max_input_channels'] > 0]
