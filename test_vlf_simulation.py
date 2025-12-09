#!/usr/bin/env python3
"""
VLF System Simulation Test - No audio hardware needed
"""
import sys
import time
import numpy as np
import threading
from pathlib import Path

sys.path.insert(0, 'src')

from core.vlf_system import VLFMonitoringSystem
from core.config_manager import ConfigManager
from core.logger import setup_logger
from core.vlf_processor import VLFProcessor, VLFSignal
from data.realtime_storage import RealtimeStorage, VLFMeasurement
from datetime import datetime, timezone

class VLFSimulator:
    """Simulate VLF data for testing"""
    
    def __init__(self):
        self.processor = VLFProcessor()
        self.storage = RealtimeStorage()
        self.is_running = False
        
    def generate_simulated_audio(self, duration_seconds: float = 1.0, sample_rate: int = 11025):
        """Generate simulated audio data"""
        # Generate time array
        t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds))
        
        # Create simulated VLF-like signals
        signal_data = np.zeros_like(t)
        
        # Add multiple frequency components
        signal_data += 0.1 * np.sin(2 * np.pi * 800 * t)   # NAA_SIM band
        signal_data += 0.08 * np.sin(2 * np.pi * 1200 * t)  # NWC_SIM band  
        signal_data += 0.06 * np.sin(2 * np.pi * 1700 * t)  # DHO_SIM band
        signal_data += 0.04 * np.sin(2 * np.pi * 2200 * t)  # GQD_SIM band
        
        # Add some noise
        noise = np.random.normal(0, 0.01, len(t))
        signal_data += noise
        
        return signal_data
    
    def run_simulation(self, duration_seconds: int = 30):
        """Run VLF simulation"""
        print(f"Starting VLF simulation for {duration_seconds} seconds...")
        
        self.is_running = True
        start_time = time.time()
        measurement_count = 0
        
        try:
            while self.is_running and (time.time() - start_time) < duration_seconds:
                # Generate simulated audio chunk
                audio_chunk = self.generate_simulated_audio(1.0)  # 1 second chunk
                
                # Process with VLF processor
                vlf_signals = self.processor.process_chunk(audio_chunk)
                
                # Convert to measurements and store
                timestamp = datetime.now(timezone.utc)
                measurements = []
                
                for station_id, signal_data in vlf_signals.items():
                    measurement = VLFMeasurement(
                        timestamp=timestamp,
                        station_id=station_id,
                        frequency=signal_data.frequency,
                        amplitude=signal_data. amplitude,
                        phase=signal_data.phase
                    )
                    measurements. append(measurement)
                    measurement_count += 1
                
                # Store measurements
                if measurements:
                    self.storage.store_batch(measurements)
                
                # Print real-time data
                print(f"\n📡 Real-time VLF Data (t={time.time()-start_time:.1f}s):")
                for station, signal in vlf_signals.items():
                    print(f"  {station}: {signal.amplitude:.4f} @ {signal.frequency:.2f}kHz")
                
                # Wait 1 second
                time.sleep(1.0)
                
        except KeyboardInterrupt:
            print("\nSimulation interrupted by user")
        
        self.is_running = False
        
        print(f"\nSimulation completed")
        print(f"Total measurements stored: {measurement_count}")
        
        return measurement_count

def test_vlf_simulation():
    """Test VLF system with simulated data"""
    print("Testing VLF System with Simulation Data")
    print("=" * 50)
    
    # Setup logging
    setup_logger(debug=True)
    
    # Create simulator
    simulator = VLFSimulator()
    
    print("VLF simulator initialized")
    
    # Test individual components
    print("\nTesting VLF Processor...")
    audio_data = simulator.generate_simulated_audio(2.0)
    vlf_signals = simulator.processor. process_chunk(audio_data)
    
    print(f"Processed {len(vlf_signals)} VLF signals:")
    for station, signal in vlf_signals.items():
        print(f"  {station}: {signal.amplitude:.4f} @ {signal.frequency:.2f}kHz")
    
    # Test storage
    print(f"\nTesting Data Storage...")
    timestamp = datetime.now(timezone.utc)
    test_measurements = [
        VLFMeasurement(timestamp, station, signal.frequency, signal.amplitude, signal.phase)
        for station, signal in vlf_signals.items()
    ]
    
    simulator.storage.store_batch(test_measurements)
    print(f"Stored {len(test_measurements)} test measurements")
    
    # Get recent data
    for station in vlf_signals. keys():
        recent = simulator. storage.get_recent_data(station, minutes=5)
        print(f"  {station}: {len(recent)} recent measurements")
    
    # Run full simulation
    print(f"\nStarting Full VLF Simulation...")
    measurement_count = simulator.run_simulation(15)  # 15 seconds
    
    print(f"\nFinal Statistics:")
    print(f"  - Total measurements: {measurement_count}")
    print(f"  - Database created: {simulator.storage.db_path}")
    print(f"  - Processing successful: ")
    
    return True

if __name__ == "__main__":
    test_vlf_simulation()
