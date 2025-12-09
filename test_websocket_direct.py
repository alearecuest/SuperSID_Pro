#!/usr/bin/env python3
"""
Direct WebSocket test
"""
import asyncio
import websockets
import json

async def test_websocket():
    try:
        print("Testing WebSocket connection...")
        
        uri = "ws://localhost:8080/ws"
        async with websockets.connect(uri) as websocket:
            print("WebSocket connected!")
            
            # Send ping
            await websocket.send("ping")
            print("Sent ping")
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            print(f"Received: {response}")
            
            # Wait for any data messages
            try:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(message)
                    print(f"Data: {data. get('type', 'unknown')} - {len(str(message))} chars")
                    
                    if data.get('type') == 'vlf_data':
                        print(f"   Signals: {list(data.get('signals', {}).keys())}")
                        break
                        
            except asyncio.TimeoutError:
                print("No data received (normal if monitoring not started)")
                
    except Exception as e:
        print(f"WebSocket test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())