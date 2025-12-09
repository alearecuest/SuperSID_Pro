"""
VLF Web API - FastAPI backend for real-time VLF monitoring
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
import asyncio
import json
from datetime import datetime, timezone
from typing import List, Dict
import uvicorn
from pathlib import Path

from core.vlf_system import VLFMonitoringSystem
from core.vlf_processor import VLFSignal
from core.config_manager import ConfigManager
from data.realtime_storage import RealtimeStorage
from core.logger import get_logger
from core.space_weather import SpaceWeatherAPI

class VLFWebAPI:
    """Web API for VLF monitoring system"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self. logger = get_logger(__name__)
        
        # Initialize FastAPI
        self.app = FastAPI(
            title="SuperSID Pro Web API",
            description="Real-time VLF monitoring web interface",
            version="1. 0.0"
        )
        
        # Setup static files and templates
        web_path = Path("src/web")
        self.app.mount("/static", StaticFiles(directory=web_path / "static"), name="static")
        self.templates = Jinja2Templates(directory=web_path / "templates")
        
        # WebSocket connections
        self.websocket_connections: List[WebSocket] = []
        
        # VLF System
        self.vlf_system = None
        self.storage = RealtimeStorage()
        self._monitoring_task = None
        
        # Space Weather API
        self. space_weather = SpaceWeatherAPI(self.config_manager)
        
        # Setup routes
        self._setup_routes()
        
        self.logger.info("VLF Web API initialized")
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard(request: Request):
            """Main dashboard page"""
            # Check if this is first run
            if self.config_manager.config.get("application", {}).get("first_run", True):
                # Redirect to setup page
                return RedirectResponse(url="/setup")
            
            return self.templates.TemplateResponse("dashboard.html", {"request": request})
        
        @self.app.get("/api/config")
        async def get_config():
            """Get observatory configuration"""
            try:
                config = self.config_manager.config
                return {
                    "status": "ok",
                    "observatory": config.get("observatory", {}),
                    "vlf_stations": config.get("vlf_stations", {}),
                    "application": config.get("application", {})
                    }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/setup", response_class=HTMLResponse)
        async def setup_page(request: Request):
            """Observatory setup page"""
            return self. templates.TemplateResponse("setup.html", {"request": request})
        
        @self.app.post("/api/setup")
        async def save_setup(setup_data: dict):
            """Save observatory setup configuration"""
            try:
                # Get current configuration
                current_config = self.config_manager.config.copy()
                
                # Update with new setup data
                if 'observatory' in setup_data:
                    current_config['observatory'] = {
                        **current_config. get('observatory', {}),
                        **setup_data['observatory']
                    }
                
                if 'vlf_stations' in setup_data:
                    current_config['vlf_stations'] = {
                        **current_config.get('vlf_stations', {}),
                        **setup_data['vlf_stations']
                    }
                
                if 'application' in setup_data:
                    current_config['application'] = {
                        **current_config.get('application', {}),
                        **setup_data['application']
                    }
                
                # Add missing required sections if not present
                if 'space_weather' not in current_config:
                    current_config['space_weather'] = {
                        "enable_spaceweatherlive": True,
                        "enable_swpc_noaa": True,
                        "update_interval": 600
                    }
                
                if 'data_sources' not in current_config:
                    current_config['data_sources'] = {
                        "audio": {
                            "enabled": True,
                            "sample_rate": 11025,
                            "buffer_size": 1024
                        },
                        "simulation": {
                            "enabled": True,
                            "frequencies": [24.0, 19.8, 23.4, 19.6],
                            "amplitude_range": [0.001, 0.01]
                        }
                    }
                
                if 'vlf_system' not in current_config:
                    current_config['vlf_system'] = {
                        "audio_sample_rate": 11025,
                        "audio_buffer_size": 1024,
                        "audio_device": None,
                        "storage_batch_size": 10,
                        "anomaly_detection": True,
                        "baseline_update_interval": 300
                    }
                
                if 'monitoring' not in current_config:
                    current_config['monitoring'] = {
                        "auto_start": True,
                        "data_retention_days": 30,
                        "export_format": "csv",
                        "screenshot_interval": 300
                    }
                
                if 'reporting' not in current_config:
                    current_config['reporting'] = {
                        "ftp_upload": False,
                        "ftp_server": "sid-ftp.stanford.edu",
                        "ftp_directory": "/incoming/SuperSID/NEW/",
                        "local_tmp": "/tmp",
                        "report_interval": 86400
                    }
                
                # Update config manager
                self.config_manager.config = current_config
                self.config_manager.save_config()
                
                return {"status": "success", "message": "Observatory configuration saved successfully"}
                
            except Exception as e:
                self.logger.error(f"Error saving setup: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/status")
        async def get_status():
            """Get system status"""
            if self.vlf_system:
                status = self.vlf_system.get_system_status()
            else:
                status = {"is_monitoring": False, "message": "VLF system not initialized"}
            
            return {
                "status": "ok",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "vlf_system": status,
                "websocket_connections": len(self. websocket_connections)
            }
        
        @self.app.get("/api/space-weather")
        async def get_space_weather():
            """Get current space weather data"""
            try:
                data = self.space_weather.get_latest_data()
                summary = self.space_weather.get_summary()
                
                return {
                    "status": "ok",
                    "data": data,
                    "summary": summary,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/space-weather/summary")
        async def get_space_weather_summary():
            """Get space weather summary"""
            try:
                summary = self.space_weather.get_summary()
                return summary
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/space-weather-update")
        async def force_space_weather_update():
            """Force space weather data update (for debugging)"""
            try:
                self.logger.info("Forcing space weather update...")
                await self.space_weather.fetch_all_data()
                data = self.space_weather.get_latest_data()
                summary = self.space_weather.get_summary()
                
                return {
                    "status": "updated",
                    "message": "Space weather data updated",
                    "data_summary": {
                        "solar_wind_records": len(data.get('solar_wind', {}).get('swpc_data', [])),
                        "aurora_data": bool(data.get('aurora')),
                        "solar_activity_data": bool(data.get('solar_activity')),
                        "last_update": data.get('last_update')
                    },
                    "summary": summary,
                    "debug_info": {
                        "config_enabled": {
                            "spaceweatherlive": self.config_manager.config.get('space_weather', {}).get('enable_spaceweatherlive', False),
                            "swpc_noaa": self.config_manager.config.get('space_weather', {}).get('enable_swpc_noaa', False)
                        },
                        "raw_data_keys": list(data.keys())
                    }
                }
            except Exception as e:
                self.logger.error(f"Error in force update: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app. post("/api/start")
        async def start_monitoring():
            """Start VLF monitoring"""
            try:
                if not self.vlf_system:
                    self.vlf_system = VLFMonitoringSystem(self. config_manager)
                    self.vlf_system.register_data_callback(self._on_vlf_data)
                    self.vlf_system.register_anomaly_callback(self._on_anomaly)
                
                # Start VLF monitoring
                self.vlf_system.start_monitoring()
                
                # Start simulation task for demo purposes
                if not self._monitoring_task:
                    self._monitoring_task = asyncio.create_task(self._simulation_loop())
                
                # Start space weather monitoring
                try:
                    await self.space_weather.start_monitoring()
                    self.logger.info("Space weather monitoring started successfully")
                except Exception as e:
                    self.logger.warning(f"Failed to start space weather monitoring: {e}")
                
                return {"status": "started", "message": "VLF monitoring started"}
                
            except Exception as e:
                self.logger.error(f"Failed to start monitoring: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self. app.post("/api/stop")
        async def stop_monitoring():
            """Stop VLF monitoring"""
            try:
                if self. vlf_system:
                    self.vlf_system.stop_monitoring()
                
                # Stop simulation task
                if self._monitoring_task:
                    self._monitoring_task.cancel()
                    self._monitoring_task = None
                
                # Stop space weather monitoring
                try:
                    await self.space_weather. stop_monitoring()
                except Exception as e:
                    self.logger.warning(f"Failed to stop space weather monitoring: {e}")

                return {"status": "stopped", "message": "VLF monitoring stopped"}
                
            except Exception as e:
                self.logger.error(f"Failed to stop monitoring: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app. get("/api/data/recent/{station}")
        async def get_recent_data(station: str, minutes: int = 60):
            """Get recent data for a station"""
            try:
                measurements = self.storage.get_recent_data(station, minutes)
                
                data = []
                for measurement in measurements:
                    data.append({
                        "timestamp": measurement.timestamp. isoformat(),
                        "frequency": measurement.frequency,
                        "amplitude": measurement.amplitude,
                        "phase": measurement.phase
                    })
                
                return {
                    "station": station,
                    "count": len(data),
                    "data": data
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app. websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time data"""
            await websocket.accept()
            self.websocket_connections.append(websocket)
            
            # Send welcome message
            welcome_msg = {
                "type": "connection",
                "message": "Connected to SuperSID Pro VLF monitoring",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await websocket.send_text(json.dumps(welcome_msg))
            
            try:
                while True:
                    # Keep connection alive with ping/pong
                    message = await websocket.receive_text()
                    if message == "ping":
                        await websocket.send_text("pong")
                    
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)
    
    async def _simulation_loop(self):
        """Simulation loop for demo data (remove when using real hardware)"""
        import numpy as np
        
        while True:
            try:
                # Generate simulated VLF data
                current_time = datetime.now(timezone.utc)
                t = current_time.timestamp()
                
                # Create simulated signals for each band
                vlf_signals = {}
                
                for i, band in enumerate(['BAND_1', 'BAND_2', 'BAND_3', 'BAND_4'], 1):
                    # Vary amplitude with time for realistic simulation
                    base_amplitude = 0.001 * i
                    variation = 0.0005 * np.sin(t * 0.1 * i) + 0.0001 * np.random.randn()
                    amplitude = base_amplitude + variation
                    
                    # Vary frequency slightly
                    base_frequency = 0.2 + 0.4 * i  # kHz
                    freq_variation = 0.05 * np.sin(t * 0.05 * i)
                    frequency = base_frequency + freq_variation
                    
                    # Create VLFSignal object
                    signal = VLFSignal(
                        timestamp=current_time. timestamp(),
                        frequency=frequency,
                        amplitude=abs(amplitude),  # Ensure positive
                        phase=0.0,
                        station_id=band
                    )
                    
                    vlf_signals[band] = signal
                
                # Send data through callback
                self._on_vlf_data(vlf_signals)
                
                # Random anomaly generation (1% chance per loop)
                if np.random. random() < 0.01:
                    anomalies = [f"BAND_{np.random.randint(1, 5)}: Signal amplitude spike detected"]
                    self._on_anomaly(anomalies, current_time)
                
                await asyncio. sleep(1.0)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Simulation error: {e}")
                await asyncio. sleep(5.0)
    
    def _on_vlf_data(self, vlf_signals: Dict[str, VLFSignal]):
        """Handle VLF data callback"""
        # Convert to JSON-serializable format
        data = {
            "type": "vlf_data",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "signals": {}
        }
        
        for station, signal in vlf_signals. items():
            data["signals"][station] = {
                "frequency": signal.frequency,
                "amplitude": signal.amplitude,
                "phase": signal.phase
            }
        
        # Send to all connected clients
        asyncio.create_task(self._broadcast_to_websockets(data))
    
    def _on_anomaly(self, anomalies: List[str], timestamp):
        """Handle anomaly callback"""
        data = {
            "type": "anomaly",
            "timestamp": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
            "anomalies": anomalies
        }
        
        # Send to all connected clients
        asyncio.create_task(self._broadcast_to_websockets(data))
    
    async def _broadcast_to_websockets(self, data: Dict):
        """Broadcast data to all WebSocket connections"""
        if not self.websocket_connections:
            return
        
        message = json.dumps(data)
        
        # Send to all connections, remove disconnected ones
        disconnected = []
        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(message)
            except:
                disconnected.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected:
            if websocket in self.websocket_connections:
                self.websocket_connections.remove(websocket)
    
    def run(self, host: str = "0. 0.0.0", port: int = 8000, debug: bool = False):
        """Run the web server"""
        self. logger.info(f"Starting VLF Web API on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port, debug=debug)

def create_vlf_web_api(config_path: str = "config/default_config.json") -> VLFWebAPI:
    """Factory function to create VLF Web API"""
    config_manager = ConfigManager(config_path)
    return VLFWebAPI(config_manager)