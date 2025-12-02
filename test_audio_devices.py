#!/usr/bin/env python3
"""
Test audio devices and VLF system capabilities
"""
import sys
sys.path.insert(0, 'src')

try:
    import sounddevice as sd
    from core.audio_capture import VLFAudioCapture, AudioConfig
    
    print("Available Audio Devices:")
    print("=" * 40)
    
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            print(f"  {i}: {device['name']} (Input: {device['max_input_channels']} channels)")
    
    print(f"\nDefault input device: {sd.query_devices(kind='input')['name']}")
    
except Exception as e:
    print(f"Audio system not available: {e}")
    print("Use simulation mode instead")
