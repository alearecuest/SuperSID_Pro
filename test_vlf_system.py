#!/usr/bin/env python3
"""
Test VLF Real-time Monitoring System
"""
import sys
import time
import threading
from pathlib import Path

sys.path.insert(0, 'src')

from core.vlf_system import VLFMonitoringSystem
from core.config_manager import ConfigManager
from core.logger import setup_logger

def data_callback(vlf_signals):
    """Callback for real-time data"""
    print(f"\nReal-time VLF Data:")
    for station, signal in vlf_signals.items():
        print(f"  {station}: {signal. amplitude:.4f} @ {signal.frequency:.2f}kHz")

def anomaly_callback(anomalies, timestamp):
    """Callback for anomalies"""
    print(f"\nANOMALY DETECTED at {timestamp}:")
    for anomaly in anomalies:
        print(f"  - {anomaly}")

def test_vlf_system():
    """Test the complete VLF monitoring system"""
    print("Testing VLF Real-time Monitoring System")
    print("=" * 50)
    
    # Setup logging
    setup_logger(debug=True)
    
    # Initialize configuration
    config_manager = ConfigManager('config/default_config.json')
    
    # Create VLF system
    vlf_system = VLFMonitoringSystem(config_manager)
    
    # Register callbacks
    vlf_system. register_data_callback(data_callback)
    vlf_system.register_anomaly_callback(anomaly_callback)
    
    print("VLF system initialized")
    
    # Check available audio devices
    devices = vlf_system.get_available_audio_devices()
    print(f"\nAvailable audio devices:")
    for device_id, device_name in devices[:5]:  # Show first 5
        print(f"  {device_id}: {device_name}")
    
    # Get system status
    status = vlf_system.get_system_status()
    print(f"\nSystem Status: {status}")
    
    try:
        # Start monitoring
        print(f"\nStarting VLF monitoring...")
        vlf_system.start_monitoring()
        
        print("Monitoring VLF signals for 30 seconds...")
        print("   (You should see real-time data updates)")
        
        # Monitor for 30 seconds
        time.sleep(30)
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        
    except Exception as e:
        print(f"\nError during monitoring: {e}")
        
    finally:
        # Stop monitoring
        print("\nStopping VLF monitoring...")
        vlf_system. stop_monitoring()
        
        # Final status
        final_status = vlf_system. get_system_status()
        print(f"Final Status: {final_status}")
        
    print("\nVLF system test completed")

if __name__ == "__main__":
    test_vlf_system()
