"""
VLF Web API - FastAPI backend for real-time VLF monitoring
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
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

class VLFWebAPI:
    """Web API for VLF monitoring system"""
    
    def __init__(self, config_manager: ConfigManager):
        self. config_manager = config_manager
        self.logger = get_logger(__name__)
        
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
        
        # Setup routes
        self._setup_routes()
        
        self.logger.info("VLF Web API initialized")
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard(request: Request):
            """Main dashboard page"""
            return self. templates.TemplateResponse("dashboard.html", {"request": request})
        
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
                "vlf_system": status
            }
        
        @self.app.post("/api/start")
        async def start_monitoring():
            """Start VLF monitoring"""
            try:
                if not self.vlf_system:
                    self.vlf_system = VLFMonitoringSystem(self.config_manager)
                    self.vlf_system.register_data_callback(self._on_vlf_data)
                    self.vlf_system.register_anomaly_callback(self._on_anomaly)
                
                self.vlf_system.start_monitoring()
                return {"status": "started", "message": "VLF monitoring started"}
                
            except Exception as e:
                self.logger.error(f"Failed to start monitoring: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/stop")
        async def stop_monitoring():
            """Stop VLF monitoring"""
            try:
                if self.vlf_system:
                    self.vlf_system.stop_monitoring()
                return {"status": "stopped", "message": "VLF monitoring stopped"}
                
            except Exception as e:
                self.logger.error(f"Failed to stop monitoring: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/data/recent/{station}")
        async def get_recent_data(station: str, minutes: int = 60):
            """Get recent data for a station"""
            try:
                measurements = self.storage.get_recent_data(station, minutes)
                
                data = []
                for measurement in measurements:
                    data.append({
                        "timestamp": measurement. timestamp.isoformat(),
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
            
            try:
                while True:
                    # Keep connection alive
                    await websocket.receive_text()
                    
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)
    
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
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, debug: bool = False):
        """Run the web server"""
        self.logger.info(f"Starting VLF Web API on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port, debug=debug)

def create_vlf_web_api(config_path: str = "config/default_config.json") -> VLFWebAPI:
    """Factory function to create VLF Web API"""
    config_manager = ConfigManager(config_path)
    return VLFWebAPI(config_manager)