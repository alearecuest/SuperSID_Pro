#!/usr/bin/env python3
"""
Test VLF Backend without GUI - No display needed
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, 'src')

from core.vlf_processor import VLFProcessor, VLFSignal
from data.realtime_storage import RealtimeStorage, VLFMeasurement
from core.config_manager import ConfigManager
from core.logger import setup_logger
from datetime import datetime, timezone
import numpy as np

def test_vlf_backend():
    """Test VLF backend components without GUI"""
    print("Testing VLF Backend Components")
    print("=" * 50)
    
    setup_logger(debug=True)
    
    # Test 1: VLF Processor
    print("\nTesting VLF Processor...")
    processor = VLFProcessor(sample_rate=11025)
    
    # Generate test signal
    t = np.linspace(0, 1.0, 11025)
    test_signal = (0.1 * np.sin(2 * np.pi * 300 * t) +
                   0.08 * np.sin(2 * np.pi * 600 * t) +
                   0.06 * np.sin(2 * np.pi * 1000 * t) +
                   0.04 * np.sin(2 * np.pi * 1500 * t))
    
    vlf_signals = processor.process_chunk(test_signal)
    print(f"Processed {len(vlf_signals)} bands")
    for band, signal in vlf_signals.items():
        print(f"   {band}: amp={signal.amplitude:.4f}, freq={signal.frequency:.2f}kHz")
    
    # Test 2: Storage System
    print("\nTesting Storage System...")
    storage = RealtimeStorage()
    
    # Convert to measurements
    measurements = []
    timestamp = datetime.now(timezone.utc)
    for band_id, signal in vlf_signals.items():
        measurement = VLFMeasurement(
            timestamp=timestamp,
            station_id=band_id,
            frequency=signal.frequency,
            amplitude=signal.amplitude,
            phase=signal.phase
        )
        measurements.append(measurement)
    
    storage.store_batch(measurements)
    print(f"Stored {len(measurements)} measurements")
    
    # Test recent data retrieval
    for band_id in vlf_signals.keys():
        recent = storage.get_recent_data(band_id, minutes=1)
        print(f"   {band_id}: {len(recent)} recent measurements")
    
    print(f"\nBackend testing completed successfully!")
    print(f"Database file created: {storage.db_path}")
    
    return True

if __name__ == "__main__":
    test_vlf_backend()