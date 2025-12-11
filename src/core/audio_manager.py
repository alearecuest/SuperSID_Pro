"""
Audio Manager - Handle audio device detection and configuration
"""
import pyaudio
import numpy as np
from typing import List, Dict, Optional
from core.logger import get_logger

class AudioManager: 
    """Manages audio input devices and streaming"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        
    def get_audio_devices(self) -> List[Dict]:
        """Get list of available audio input devices"""
        devices = []
        for i in range(self. audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                devices.append({
                    'index': i,
                    'name': device_info['name'],
                    'channels': device_info['maxInputChannels'],
                    'sample_rate': int(device_info['defaultSampleRate']),
                    'api':  self. audio.get_host_api_info_by_index(device_info['hostApi'])['name']
                })
        return devices
        
    def test_device(self, device_index: int, sample_rate: int = 11025, channels: int = 1) -> bool:
        """Test if device works with specified parameters"""
        try:
            test_stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=1024
            )
            test_stream.read(1024, exception_on_overflow=False)
            test_stream.stop_stream()
            test_stream. close()
            return True
        except Exception as e:
            self.logger.error(f"Device test failed: {e}")
            return False
            
    def start_recording(self, device_index: int, sample_rate: int = 11025, 
                       channels: int = 1, callback=None):
        """Start audio recording from specified device"""
        if self.is_recording:
            self.stop_recording()
            
        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=1024,
                stream_callback=callback
            )
            self.stream.start_stream()
            self.is_recording = True
            self.logger.info(f"Started recording from device {device_index}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start recording:  {e}")
            return False
            
    def stop_recording(self):
        """Stop audio recording"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            self.is_recording = False
            
    def cleanup(self):
        """Clean up audio resources"""
        self.stop_recording()
        self.audio.terminate()