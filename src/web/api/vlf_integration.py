"""
Integration between VLF System and Web API
"""
import asyncio
from typing import Dict, Optional
from core.vlf_system import VLFMonitoringSystem
from core.vlf_processor import VLFSignal
from core.config_manager import ConfigManager
from core.logger import get_logger

class VLFWebIntegration:
    """Integrates VLF monitoring with web API"""
    
    def __init__(self, config_manager: ConfigManager, web_api):
        self.config_manager = config_manager
        self.web_api = web_api
        self.logger = get_logger(__name__)
        self.vlf_system: Optional[VLFMonitoringSystem] = None
        
    async def initialize_vlf_system(self):
        """Initialize VLF system in simulation mode for web"""
        try:
            # Create VLF system
            self.vlf_system = VLFMonitoringSystem(self.config_manager)
            
            # Register callbacks
            self.vlf_system.register_data_callback(self._on_vlf_data)
            self. vlf_system.register_anomaly_callback(self._on_anomaly)
            
            # Start in simulation mode
            self.vlf_system.start_monitoring()
            
            self.logger.info("VLF system initialized for web interface")
            return True
            
        except Exception as e:
            self.logger. error(f"Failed to initialize VLF system: {e}")
            return False
    
    def _on_vlf_data(self, vlf_signals: Dict[str, VLFSignal]):
        """Handle VLF data from monitoring system"""
        # This is called from VLF system, send to web clients
        asyncio.create_task(self. web_api._on_vlf_data(vlf_signals))
    
    def _on_anomaly(self, anomalies, timestamp):
        """Handle anomaly detection"""
        asyncio.create_task(self. web_api._on_anomaly(anomalies, timestamp))