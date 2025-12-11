"""
Space Weather API Integration
Fetches data from spaceweatherlive.com and swpc.noaa.gov
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from core.logger import get_logger

class SpaceWeatherAPI:
    """Integration with Space Weather APIs"""
    
    def __init__(self, config_manager):
        self.config = config_manager. config
        self.logger = get_logger(__name__)
        self. session = None
        
        # API endpoints
        self.endpoints = {
            'spaceweatherlive': {
                'base': 'https://www.spaceweatherlive.com/api',
                'solar_wind': '/solar-wind',
                'aurora': '/aurora',
                'solar_activity': '/solar-activity'
            },
            'swpc_noaa': {
                'base': 'https://services.swpc.noaa.gov',
                'solar_wind': '/products/solar-wind/mag-1-day. json',
                'xray_flares': '/products/goes-xray-flare-events. json',
                'geomag_storm': '/products/geomag-storm-probability.json'
            }
        }
        
        self.latest_data = {
            'solar_wind': {},
            'aurora': {},
            'solar_activity': {},
            'geomagnetic': {},
            'last_update': None
        }
    
    async def start_monitoring(self):
        """Start space weather monitoring"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        self.logger.info("Starting space weather monitoring")
        
        asyncio.create_task(self._update_loop())
    
    async def stop_monitoring(self):
        """Stop space weather monitoring"""
        if self.session:
            await self.session.close()
            self.session = None
        
        self.logger.info("Space weather monitoring stopped")
    
    async def _update_loop(self):
        """Main update loop for space weather data"""
        update_interval = self.config.get('space_weather', {}).get('update_interval', 600)
        
        while self.session:
            try:
                await self. fetch_all_data()
                await asyncio.sleep(update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in space weather update loop: {e}")
                await asyncio.sleep(60)
    
    async def fetch_all_data(self):
        """Fetch data from all space weather sources"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        self.logger.info("Fetching space weather data")
        
        tasks = [
            self.  fetch_spaceweatherlive_data(),
            self. fetch_swpc_data()
        ]
    
        await asyncio.gather(*tasks, return_exceptions=True)
        self.latest_data['last_update'] = datetime.now(timezone.utc)
    
    async def fetch_spaceweatherlive_data(self):
        """Fetch data from spaceweatherlive.com"""
        if not self.config.get('space_weather', {}).get('enable_spaceweatherlive', False):
            self.logger.info("Spaceweatherlive disabled in config")
            return
        
        try:
            base_url = self.endpoints['spaceweatherlive']['base']
            self.logger.info(f"Fetching from spaceweatherlive: {base_url}")
            
            # Fetch solar wind data
            solar_wind_url = f"{base_url}/solar-wind"
            async with self.session.get(solar_wind_url) as response:
                self.logger.info(f"Spaceweatherlive solar wind response: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    self.latest_data['solar_wind']. update({
                        'source': 'spaceweatherlive',
                        'data': data,
                        'timestamp': datetime.now(timezone.utc). isoformat()
                    })
            
            # Fetch aurora data
            aurora_url = f"{base_url}/aurora"
            async with self.session.get(aurora_url) as response:
                if response.status == 200:
                    data = await response.json()
                    self.latest_data['aurora'].update({
                        'source': 'spaceweatherlive',
                        'data': data,
                        'timestamp': datetime.now(timezone. utc).isoformat()
                    })
            
            self.logger.info("Successfully fetched spaceweatherlive. com data")
            
        except Exception as e:
            self.logger.error(f"Error fetching spaceweatherlive data: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def fetch_swpc_data(self):
        """Fetch data from SWPC NOAA"""
        if not self.config.get('space_weather', {}).get('enable_swpc_noaa', False):
            self.logger.info("SWPC NOAA disabled in config")
            return
        
        self.logger.info("Starting SWPC data fetch...")
        
        try:
            base_url = self.endpoints['swpc_noaa']['base']
            self.logger.info(f"SWPC base URL: {base_url}")
            
            # Fetch solar wind data
            solar_wind_url = f"{base_url}/products/solar-wind/mag-1-day.json"
            self.logger.info(f"Fetching from: {solar_wind_url}")
            
            async with self.session.get(solar_wind_url) as response:
                self.logger.info(f"Response status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    self.logger.info(f"Received {len(data)} records from SWPC")
                    
                    self.latest_data['solar_wind'].update({
                        'swpc_source': 'noaa',
                        'swpc_data': data,
                        'swpc_timestamp': datetime.now(timezone.utc).isoformat()
                    })
                    
                    self.logger.info("SWPC solar wind data updated successfully")
                else:
                    self.logger. error(f"SWPC request failed with status: {response.status}")
            
            # Fetch X-ray flares
            xray_url = f"{base_url}/products/goes-xray-flare-events.json"
            async with self.session.get(xray_url) as response:
                if response.status == 200:
                    data = await response.json()
                    self. latest_data['solar_activity'].update({
                        'swpc_xray_flares': data,
                        'swpc_timestamp': datetime.now(timezone.utc).isoformat()
                    })
                    self.logger.info("SWPC X-ray data updated")
            
            # Fetch geomagnetic storm probability
            geomag_url = f"{base_url}/products/geomag-storm-probability.json"
            async with self.session.get(geomag_url) as response:
                if response.status == 200:
                    data = await response.json()
                    self.latest_data['geomagnetic'].update({
                        'swpc_storm_probability': data,
                        'swpc_timestamp': datetime. now(timezone.utc).isoformat()
                    })
                    self.logger.info("SWPC geomagnetic data updated")
            
            self. logger.info("Successfully fetched SWPC NOAA data")
            
        except Exception as e:
            self.logger.error(f"Error fetching SWPC data: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
    
    def get_latest_data(self) -> Dict:
        """Get the latest space weather data"""
        return self.latest_data
    
    def get_summary(self) -> Dict:
        """Get a summary of current space weather conditions"""
        try:
            self.logger.info(f"Getting summary, latest_data keys: {list(self.latest_data.keys())}")
            self.logger.info(f"Solar wind data: {len(self.latest_data. get('solar_wind', {}). get('swpc_data', []))} records")

            summary = {
                'status': 'normal',
                'alerts': [],
                'kp_index': 'unknown',
                'solar_wind_speed': 'unknown',
                'geomagnetic_status': 'quiet',
                'last_update': self.latest_data.get('last_update')
            }

            # Process NOAA solar wind data
            solar_wind = self.latest_data.get('solar_wind', {})
            swpc_data = solar_wind. get('swpc_data', [])
            self.logger.info(f"Processing {len(swpc_data)} SWPC data points")
            
            if len(swpc_data) > 1:
                latest_point = swpc_data[-1]
                
                if len(latest_point) >= 7:
                    try:
                        bx = float(latest_point[1]) if latest_point[1] != '' else 0
                        by = float(latest_point[2]) if latest_point[2] != '' else 0
                        bz = float(latest_point[3]) if latest_point[3] != '' else 0
                        bt = float(latest_point[6]) if latest_point[6] != '' else 0
                        
                        # Calculate approximate Kp index from magnetic field
                        # Simple approximation: higher magnetic field disturbance = higher Kp
                        magnetic_disturbance = abs(bz)
                        
                        if magnetic_disturbance < 3:
                            kp_approx = 0 + int(magnetic_disturbance)
                        elif magnetic_disturbance < 6:
                            kp_approx = 3 + int((magnetic_disturbance - 3) / 2)
                        else:
                            kp_approx = min(9, 5 + int((magnetic_disturbance - 6) / 3))
                        
                        summary['kp_index'] = str(kp_approx)
                        
                        # Estimate solar wind speed (rough approximation)
                        # Higher magnetic field often correlates with faster solar wind
                        estimated_speed = 300 + int(bt * 50)  # Base speed + magnetic enhancement
                        summary['solar_wind_speed'] = f"{estimated_speed} km/s"
                        
                        # Determine geomagnetic status
                        if kp_approx <= 2:
                            summary['geomagnetic_status'] = 'quiet'
                            summary['status'] = 'normal'
                        elif kp_approx <= 4:
                            summary['geomagnetic_status'] = 'unsettled'
                            summary['status'] = 'moderate'
                        elif kp_approx <= 6:
                            summary['geomagnetic_status'] = 'active'
                            summary['status'] = 'moderate'
                            summary['alerts'].append(f'Geomagnetic activity detected (Kp={kp_approx})')
                        else:
                            summary['geomagnetic_status'] = 'storm'
                            summary['status'] = 'storm'
                            summary['alerts']. append(f'Geomagnetic storm conditions (Kp={kp_approx})')
                        
                        self.logger.info(f"Processed space weather: Kp={kp_approx}, Speed={estimated_speed} km/s, Status={summary['status']}")
                        
                    except (ValueError, IndexError) as e:
                        self.logger.error(f"Error processing NOAA data: {e}")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating space weather summary: {e}")
            return {
                'status': 'error',
                'alerts': [f'Error: {str(e)}'],
                'kp_index': 'error',
                'solar_wind_speed': 'error',
                'geomagnetic_status': 'unknown',
                'last_update': None
            }