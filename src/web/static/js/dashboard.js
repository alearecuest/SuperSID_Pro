/**
 * SuperSID Pro Web Dashboard - SIMPLE WORKING VERSION
 */

class VLFDashboard {
    constructor() {
        this.websocket = null;
        this. charts = {};
        this.isMonitoring = false;
        this.dataCount = 0;
        
        this.init();
    }
    
    init() {
        console.log('Initializing VLF Dashboard...');
        this.setupEventHandlers();
        this.connectWebSocket();
        this.startTimeUpdate();
				this.startSpaceWeatherUpdates();
    }
    
    setupEventHandlers() {
        console.log('Setting up event handlers.. .');
        
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document. getElementById('stopBtn');
        const clearBtn = document.getElementById('clearBtn');
        
        if (startBtn) {
            startBtn.addEventListener('click', () => this.startMonitoring());
        }
        
        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.stopMonitoring());
        }
        
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearData());
        }
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        console.log('Connecting to WebSocket:', wsUrl);
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            console. log('WebSocket connected successfully! ');
            this.updateConnectionStatus(true);
            this.enableControls(true);
        };
        
        this.websocket.onmessage = (event) => {
            try {
                const data = JSON. parse(event.data);
                console.log('Received message:', data. type);
                
                if (data.type === 'vlf_data') {
                    this.handleVLFData(data);
                }
            } catch (error) {
                console.error('Error parsing message:', error);
            }
        };
        
        this.websocket.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateConnectionStatus(false);
            this.enableControls(false);
            
            setTimeout(() => this.connectWebSocket(), 3000);
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateConnectionStatus(false);
        };
    }
    
    handleVLFData(data) {
        console.log('Processing VLF data.. .');
        
        const signals = data.signals || {};
        Object.keys(signals).forEach(band => {
            const signal = signals[band];
            this.updateCurrentValue(band, signal.amplitude);
        });
        
        this.dataCount += Object.keys(signals).length;
        this.updateDataCount();
    }
    
    updateCurrentValue(band, amplitude) {
        const valueElement = document.getElementById(`${band. toLowerCase()}Value`);
        if (valueElement) {
            valueElement. textContent = amplitude.toFixed(4);
        }
    }
    
    updateDataCount() {
        const totalPointsElement = document.getElementById('totalPoints');
        if (totalPointsElement) {
            totalPointsElement.textContent = this.dataCount;
        }
        
        const dataRateElement = document.getElementById('dataRate');
        if (dataRateElement) {
            const rate = Math.min(4, this.dataCount / 10);
            dataRateElement. textContent = `${rate.toFixed(1)} Hz`;
        }
    }
    
    updateConnectionStatus(connected) {
        console.log(`Connection status: ${connected ? 'Connected' : 'Disconnected'}`);
        
        const statusElement = document.getElementById('connectionStatus');
        const wsStatusElement = document.getElementById('wsStatus');
        
        if (statusElement) {
            const statusText = statusElement.querySelector('span');
            if (statusText) {
                statusText. textContent = connected ? 'Connected' : 'Connecting...';
            }
            
            statusElement.className = connected ? 'status-indicator connected' : 'status-indicator disconnected';
        }
        
        if (wsStatusElement) {
            wsStatusElement.textContent = connected ? 'Connected' : 'Disconnected';
        }
    }
    
    enableControls(enabled) {
        console.log(`Controls ${enabled ? 'enabled' : 'disabled'}`);
        
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        
        if (startBtn) startBtn.disabled = !enabled;
        if (stopBtn) stopBtn.disabled = !enabled;
    }
    
    async startMonitoring() {
        console.log('Starting monitoring...');
        
        try {
            const response = await fetch('/api/start', { method: 'POST' });
            const result = await response.json();
            
            if (response.ok) {
                console.log('Monitoring started successfully');
                this.updateMonitoringStatus(true);
            } else {
                throw new Error(result.detail || 'Failed to start monitoring');
            }
        } catch (error) {
            console.error('Error starting monitoring:', error);
            alert('Failed to start monitoring: ' + error.message);
        }
    }
    
    async stopMonitoring() {
        console.log('Stopping monitoring...');
        
        try {
            const response = await fetch('/api/stop', { method: 'POST' });
            const result = await response.json();
            
            if (response.ok) {
                console.log('Monitoring stopped successfully');
                this. updateMonitoringStatus(false);
            } else {
                throw new Error(result.detail || 'Failed to stop monitoring');
            }
        } catch (error) {
            console.error('Error stopping monitoring:', error);
            alert('Failed to stop monitoring: ' + error.message);
        }
    }
    
		async fetchSpaceWeather() {
			try {
				console.log('Fetching space weather data...');
				const response = await fetch('/api/space-weather/summary');
				
				if (response.ok) {
					const data = await response.json();
					console.log('Space weather data received:', data);
					this.updateSpaceWeatherDisplay(data);
				} else {
					console.error('Failed to fetch space weather:', response.status);
				}
			} catch (error) {
				console.error('Error fetching space weather:', error);
			}
		}
		
		updateSpaceWeatherDisplay(data) {
			console.log('Updating space weather display with:', data);
			
			const solarActivity = document.getElementById('solarActivity');
			if (solarActivity) {
				const status = data.status || 'Unknown';
        solarActivity.textContent = status;
        solarActivity.style.color = this.getSpaceWeatherColor(status);
			}
			
			const kpIndex = document.getElementById('kpIndex');
			if (kpIndex) {
				kpIndex.textContent = data.kp_index || '--';
			}
			
			const solarWindSpeed = document.getElementById('solarWindSpeed');
			if (solarWindSpeed) {
				solarWindSpeed.textContent = data.solar_wind_speed || '-- km/s';
			}
			
			const spaceWeatherUpdate = document.getElementById('spaceWeatherUpdate');
			if (spaceWeatherUpdate && data.last_update) {
				const updateTime = new Date(data.last_update);
				spaceWeatherUpdate. textContent = updateTime.toLocaleTimeString();
			}
		}
		
		getSpaceWeatherColor(status) {
			switch(status) {
				case 'normal': return '#4CAF50';
				case 'moderate': return '#FF9800';
        case 'storm': return '#f44336';
        case 'severe': return '#d32f2f';
        default: return '#cccccc';
			}
		}
		
		startSpaceWeatherUpdates() {
			console.log('Starting space weather updates.. .');
			
			this.fetchSpaceWeather();
			
			setInterval(() => {
				this.fetchSpaceWeather();
			}, 600000);
		}

		updateMonitoringStatus(monitoring) {
        const statusElement = document.getElementById('monitoringStatus');
        
        if (statusElement) {
            statusElement.textContent = monitoring ? 'Active' : 'Stopped';
            statusElement.style.color = monitoring ? '#4CAF50' : '#f44336';
        }
    }
    
    clearData() {
        console.log('Clearing data...');
        this.dataCount = 0;
        this.updateDataCount();
    }
    
    startTimeUpdate() {
        const updateTime = () => {
            const now = new Date();
            
            const timestampElement = document.getElementById('timestamp');
            const serverTimeElement = document.getElementById('serverTime');
            
            if (timestampElement) {
                timestampElement.textContent = now. toLocaleTimeString();
            }
            
            if (serverTimeElement) {
                serverTimeElement.textContent = now.toLocaleString();
            }
        };
        
        updateTime();
        setInterval(updateTime, 1000);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing dashboard...');
    window.vlfDashboard = new VLFDashboard();
});