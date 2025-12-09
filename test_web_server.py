#!/usr/bin/env python3
"""
Test Web Server - Quick test of the web dashboard
"""
import sys
import time
import threading
import requests
from pathlib import Path

sys.path.insert(0, 'src')

from web.api.vlf_api import create_vlf_web_api
import uvicorn

def test_web_server():
    """Test the web server"""
    print("Testing SuperSID Pro Web Server")
    print("=" * 50)
    
    # Create web API
    web_api = create_vlf_web_api()
    
    print("Web API created successfully")
    
    # Test API endpoints
    print("Testing API endpoints...")
    
    # Note: This is a basic structure test
    # Full testing would require running the server
    
    app = web_api.app
    
    # Check if routes are registered
    routes = [route. path for route in app.routes]
    expected_routes = ['/', '/api/status', '/api/start', '/api/stop', '/ws']
    
    for route in expected_routes:
        if any(route in registered_route for registered_route in routes):
            print(f"{route}")
        else:
            print(f"{route} - Not found")
    
    print("\nWeb server ready!")
    print("To start the server, run:")
    print("   python web_server.py")
    print("   Then open: http://localhost:8000")
    
    return True

if __name__ == "__main__":
    test_web_server()