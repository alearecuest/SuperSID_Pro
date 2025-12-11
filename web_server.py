#!/usr/bin/env python3
"""
SuperSID Pro Web Server
Main entry point for the web dashboard
"""
import sys
import argparse
import asyncio
from pathlib import Path
import uvicorn

sys.path. insert(0, 'src')

from web.api.vlf_api import create_vlf_web_api
from core.config_manager import ConfigManager
from core.logger import setup_logger, get_logger

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse. ArgumentParser(description='SuperSID Pro Web Server')
    
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host to bind to (default: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Port to bind to (default: 8000)'
    )
    
    parser.add_argument(
        '--config',
        default='config/default_config.json',
        help='Configuration file path (default: config/default_config. json)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    
    parser.add_argument(
        '--reload',
        action='store_true',
        help='Enable auto-reload for development'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    return parser.parse_args()

def setup_environment():
    """Setup the environment and create necessary directories"""
    directories = [
        'data',
        'logs',
        'config',
        'src/web/static/css',
        'src/web/static/js',
        'src/web/templates'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    config_path = Path('config/default_config.json')
    if not config_path.exists():
        create_default_config(config_path)

def create_default_config(config_path: Path):
    """Create a default configuration file"""
    default_config = {
        "application": {
            "name": "SuperSID Pro",
            "version": "1.0.0",
            "debug": False,
            "first_run": True
        },
        "observatory": {
            "name": "Web Observatory",
            "location": "Unknown",
            "coordinates": {
                "latitude": 0.0,
                "longitude": 0.0,
                "elevation": 0.0
            },
            "timezone": "UTC",
            "contact": {
                "name": "Administrator",
                "email": "admin@observatory.local"
            }
        },
        "monitoring": {
            "auto_start": False,
            "data_retention_days": 30,
            "export_format": "csv",
            "screenshot_interval": 300
        },
        "visualization": {
            "chart_update_interval": 1000,
            "max_data_points": 1000,
            "color_scheme": "dark",
            "theme": {
                "primary_color": "#2196F3",
                "success_color": "#4CAF50",
                "warning_color": "#ff9800",
                "danger_color": "#f44336",
                "flare_marker": "#ff0000",
                "text": "#ffffff"
            },
            "update_interval": 1000,
            "history_hours": 24
        },
        "vlf_system": {
            "audio_sample_rate": 11025,
            "audio_buffer_size": 1024,
            "audio_device": None,
            "storage_batch_size": 10,
            "anomaly_detection": True,
            "baseline_update_interval": 300
        },
        "web_server": {
            "host": "0.0.0.0",
            "port": 8000,
            "cors_origins": ["*"],
            "max_connections": 100,
            "keepalive_timeout": 30
        }
    }
    
    import json
    with open(config_path, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    print(f"Created default configuration: {config_path}")

def validate_config(config_path: str):
    """Validate configuration file"""
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        config_manager = ConfigManager(config_path)
        logger = get_logger(__name__)
        logger.info(f"Configuration loaded from: {config_path}")
        return config_manager
    except Exception as e:
        raise ValueError(f"Invalid configuration file: {e}")

def print_startup_info(host: str, port: int, config_path: str, debug: bool):
    """Print startup information"""
    print("\n" + "=" * 60)
    print("SuperSID Pro Web Server")
    print("=" * 60)
    print(f"Server URL: http://{host}:{port}")
    print(f"Dashboard:  http://localhost:{port}")
    print(f"API Docs:   http://localhost:{port}/docs")
    print(f"Config:     {config_path}")
    print(f"Debug:      {'Enabled' if debug else 'Disabled'}")
    print("=" * 60)
    print("VLF Real-time Monitoring Dashboard")
    print("   - Real-time signal visualization")
    print("   - WebSocket-based data streaming") 
    print("   - Multi-band frequency analysis")
    print("   - Anomaly detection and alerts")
    print("=" * 60)
    print("Ready for VLF monitoring!")
    print("   Press Ctrl+C to stop the server")
    print("=" * 60 + "\n")

async def run_server(host: str, port: int, config_path: str, debug: bool, reload: bool, log_level: str):
    """Run the web server"""
    try:
        setup_logger(debug=(log_level == 'DEBUG'))
        logger = get_logger(__name__)
        
        setup_environment()
        
        config_manager = validate_config(config_path)
        
        web_api = create_vlf_web_api(config_path)
        
        print_startup_info(host, port, config_path, debug)
        
        uvicorn_config = uvicorn.Config(
            app=web_api. app,
            host=host,
            port=port,
            log_level=log_level. lower(),
            reload=reload,
            access_log=debug
        )
        
        server = uvicorn.Server(uvicorn_config)
        
        logger.info(f"Starting web server on {host}:{port}")
        await server.serve()
        
    except KeyboardInterrupt:
        logger. info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    args = parse_arguments()
    
    try:
        asyncio.run(run_server(
            host=args.host,
            port=args.port,
            config_path=args.config,
            debug=args.debug,
            reload=args.reload,
            log_level=args.log_level
        ))
        
    except KeyboardInterrupt:
        print("\nSuperSID Pro Web Server stopped")
    except Exception as e:
        print(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()