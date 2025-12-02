#!/usr/bin/env python3
"""
Debug VLF processing - clean version
"""
import sys
import numpy as np
sys.path.insert(0, 'src')

from core.vlf_processor import VLFProcessor
from core.logger import setup_logger

def debug_vlf_processing():
    print("Debugging VLF Processing")
    print("=" * 40)
    
    setup_logger(debug=True)
    
    # Create processor
    processor = VLFProcessor(sample_rate=11025)
    
    print(f"VLF Bands: {processor. vlf_bands}")
    print(f"Filters created: {len(processor.filters)}")
    
    for station, (b, a) in processor.filters. items():
        print(f"  {station}: filter coefficients b={len(b)}, a={len(a)}")
    
    # Generate test signal with multiple frequencies
    print(f"\nGenerating test signal...")
    t = np.linspace(0, 1.0, 11025)  # 1 second at 11025 Hz
    
    # Create composite signal with frequencies in our bands
    test_signal = np.zeros_like(t)
    test_signal += 0.1 * np.sin(2 * np.pi * 300 * t)   # BAND_1 (200-400Hz)
    test_signal += 0.08 * np.sin(2 * np.pi * 600 * t)  # BAND_2 (400-800Hz)
    test_signal += 0.06 * np.sin(2 * np.pi * 1000 * t) # BAND_3 (800-1200Hz)
    test_signal += 0.04 * np.sin(2 * np.pi * 1500 * t) # BAND_4 (1200-2000Hz)
    
    print(f"  Signal shape: {test_signal.shape}")
    print(f"  Signal range: {test_signal.min():.4f} to {test_signal. max():.4f}")
    print(f"  Signal RMS: {np.sqrt(np. mean(test_signal**2)):.4f}")
    
    # Process the signal
    print(f"\nProcessing signal...")
    try:
        vlf_signals = processor.process_chunk(test_signal)
        print(f"  Signals processed: {len(vlf_signals)}")
        
        for station, signal in vlf_signals. items():
            print(f"  {station}:")
            print(f"    Amplitude: {signal.amplitude:.6f}")
            print(f"    Frequency: {signal.frequency:.3f} kHz")
            print(f"    Phase: {signal.phase:.3f}")
    
    except Exception as e:
        print(f"Processing error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_vlf_processing()
