/**
 * SuperSID Pro Web Dashboard
 */

class VLFDashboard {
	constructor() {
			this.websocket = null;
			this.charts = {};
			this.isMonitoring = false;
			this.dataCount = 0;
			this.timeRange = 5 * 60 * 1000;
			this.observatoryConfig = null;
			this.totalDataPoints = 0;
			this.chartColors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF', '#5F27CD'];
			
			this.init();
	}

	init() {
			console.log('Initializing VLF Dashboard...');
			this.loadObservatoryConfig().then(() => {
					this.setupEventHandlers();
					this.connectWebSocket();
					this.initializeCharts();
					this.startTimeUpdate();
					this.startSpaceWeatherUpdates();
					this.setupChartClicks();
					console.log('Dashboard initialized successfully');
			});
	}

	async loadObservatoryConfig() {
			try {
					console.log('Loading observatory config...');
					const response = await fetch('/api/config');
					
					if (!response.ok) {
							throw new Error(`HTTP ${response.status}`);
					}
					
					const result = await response.json();
					this.observatoryConfig = result;
					console.log('Observatory config loaded:', this.observatoryConfig);
					
					this.updateObservatoryInfo();
					this.updateCurrentValuesSection();
					
			} catch (error) {
					console.error('Error loading observatory config:', error);
					this.observatoryConfig = {
							observatory: { 
								name: 'SuperSID Observatory',
								monitor_id: '---', 
								location: 'Please configure location',
								coordinates: { latitude: 0.0, longitude: 0.0 }
							},
							vlf_stations: { 
									monitored_stations: ['NPM', 'GQD', 'DHO38', 'NAA', 'NLK', 'NML'],
									station_frequencies: {
											'NPM': { freq: 21.4 },
											'GQD': { freq: 22.1 },
											'DHO38': { freq: 23.4 },
											'NAA': { freq: 24.0 },
											'NLK': { freq: 24.8 },
											'NML': { freq: 25.2 }
									}
							}
					};
					this.updateObservatoryInfo();
					this.updateCurrentValuesSection();
			}
	}

	updateObservatoryInfo() {
			if (!this.observatoryConfig) return;
			
			const obs = this.observatoryConfig.observatory || {};
			
			const elements = {
					obsName: obs.name || 'Unknown',
					obsMonitorId: obs.monitor_id || 'Unknown',
					obsLocation:  obs.location || 'Unknown'
			};

			Object.keys(elements).forEach(id => {
					const element = document.getElementById(id);
					if (element) element.textContent = elements[id];
			});
			
			const coords = obs.coordinates || {};
			const coordsElement = document.getElementById('obsCoordinates');
			if (coordsElement) {
					coordsElement.textContent = `${coords.latitude || 0}°, ${coords.longitude || 0}°`;
			}
			
			const footerElement = document.getElementById('observatoryFooter');
			if (footerElement) {
					footerElement.textContent = `${obs.name || 'Observatory'} Monitoring System`;
			}
	}

	updateCurrentValuesSection() {
			if (!this.observatoryConfig) return;
			
			const stations = this.observatoryConfig.vlf_stations?.monitored_stations || [];
			const stationFreqs = this.observatoryConfig.vlf_stations?.station_frequencies || {};
			
			const currentValuesDiv = document.getElementById('currentValues');
			if (!currentValuesDiv) return;
			
			currentValuesDiv.innerHTML = '';
			
			stations.forEach((station, index) => {
					const freq = stationFreqs[station]?.freq || 0;
					const div = document.createElement('div');
					div.className = 'value-row';
					div.innerHTML = `
							<span class="band-name">${station}:</span>
							<span class="band-value" id="station${index + 1}Value">0.000</span>
					`;
					currentValuesDiv.appendChild(div);
			});
	}

	initializeCharts() {
			this.createDynamicCharts();
			this.createOverviewChart();
	}

	createDynamicCharts() {
			if (!this.observatoryConfig) return;
			
			const stations = this.observatoryConfig.vlf_stations?.monitored_stations || [];
			const stationFreqs = this.observatoryConfig.vlf_stations?.station_frequencies || {};
			const chartsGrid = document.getElementById('chartsGrid');
			
			if (!chartsGrid) return;
			
			chartsGrid.innerHTML = '';
			
			stations.forEach((station, index) => {
					const freq = stationFreqs[station]?.freq || 0;
					
					const chartContainer = document.createElement('div');
					chartContainer.className = 'chart-container';
					chartContainer.innerHTML = `
							<div class="chart-header">
									<h4>${station} (${freq} kHz)</h4>
									<div class="chart-status" id="station${index + 1}Status">
											<span class="frequency">0.00 kHz</span>
											<span class="amplitude">0.000 V</span>
									</div>
							</div>
							<canvas id="station${index + 1}Chart"></canvas>
					`;
					
					chartsGrid.appendChild(chartContainer);
					
					const canvas = chartContainer.querySelector('canvas');
					const chartId = `station${index + 1}Chart`;
					const colorIndex = index % this.chartColors.length;
					
					this.charts[chartId] = new Chart(canvas.getContext('2d'), {
							type: 'line',
							data: {
									labels: [],
									datasets: [{
											label: 'Voltage',
											data: [],
											borderColor: this.chartColors[colorIndex],
											backgroundColor: this.chartColors[colorIndex] + '20',
											borderWidth: 2,
											fill: true,
											tension: 0.4,
											pointRadius: 0,
											pointHoverRadius:  4
									}]
							},
							options: {
									responsive: true,
									maintainAspectRatio: false,
									interaction: { intersect: false, mode: 'index' },
									scales: {
											x: {
													display: true,
													grid: { color: '#444444' },
													ticks:  { color: '#cccccc', maxTicksLimit: 6 }
											},
											y: {
													display:  true,
													grid: { color: '#444444' },
													ticks: { color:  '#cccccc' },
													beginAtZero:  true,
													title: {
															display: true,
															text: 'Voltage (V)',
															color: '#cccccc'
													}
											}
									},
									plugins: { legend: { display: false } },
									animation: { duration:  0 }
							}
					});
			});
			
			console.log(`Created ${stations.length} dynamic charts for stations:  ${stations.join(', ')}`);
	}

	createOverviewChart() {
			const overviewCtx = document.getElementById('overviewChart');
			if (!overviewCtx || this.charts.overviewChart) return;
			
			this.charts.overviewChart = new Chart(overviewCtx.getContext('2d'), {
					type: 'line',
					data: {
							labels: [],
							datasets: []
					},
					options: {
							responsive: true,
							maintainAspectRatio:  false,
							interaction: { intersect: false, mode: 'index' },
							scales: {
									x: {
											display: true,
											grid: { color: '#444444' },
											ticks:  { color: '#cccccc', maxTicksLimit: 10 }
									},
									y: {
											display: true,
											grid:  { color: '#444444' },
											ticks: { color: '#cccccc' },
											beginAtZero: true,
											title: {
													display: true,
													text: 'Voltage (V)',
													color: '#cccccc',
													font: { size: 14, weight: 'bold' }
											}
									}
							},
							plugins: {
									legend: {
											display: true,
											labels: { color: '#cccccc', usePointStyle: true }
									}
							},
							animation: { duration: 0 }
					}
			});
	}

	setupEventHandlers() {
			console.log('Setting up event handlers...');

			const startBtn = document.getElementById('startBtn');
			const stopBtn = document.getElementById('stopBtn');
			const clearBtn = document.getElementById('clearBtn');
			const settingsBtn = document.getElementById('settingsBtn');

			if (startBtn) {
					startBtn.addEventListener('click', () => this.startMonitoring());
					console.log('START button handler attached');
			}

			if (stopBtn) {
					stopBtn.addEventListener('click', () => this.stopMonitoring());
					console.log('STOP button handler attached');
			}

			if (clearBtn) {
					clearBtn.addEventListener('click', () => this.clearData());
					console.log('CLEAR button handler attached');
			}

			if (settingsBtn) {
					settingsBtn.addEventListener('click', () => {
							window.location.href = '/setup';
					});
					console.log('SETTINGS button handler attached');
			}

			const timeSelector = document.getElementById('timeRange');
			if (timeSelector) {
					timeSelector.addEventListener('change', (e) => this.changeTimeRange(e.target.value));
					console.log('Time selector handler attached');
			}
	}

	setupChartClicks() {
			console.log('Setting up chart click handlers...');
			
			document.addEventListener('click', (e) => {
					const chartElement = e.target.closest('.charts-grid .chart-container');
					
					if (chartElement) {
							console.log('Chart clicked! ', chartElement);
							this.expandChart(chartElement);
					}
			});

			setTimeout(() => {
					const charts = document.querySelectorAll('.charts-grid .chart-container');
					charts.forEach(chart => {
							chart.style.cursor = 'pointer';
							chart.title = 'Click to expand';
					});
					console.log(`Added pointer cursor to ${charts.length} charts`);
			}, 2000);
	}

	expandChart(chartElement) {
    console.log('Expanding chart.. .');

    document.querySelectorAll('.chart-expanded').forEach(chart => {
        chart.classList.remove('chart-expanded');
        const closeBtn = chart.querySelector('.chart-close-btn');
        if (closeBtn) closeBtn.remove();
    });

    chartElement.classList.add('chart-expanded');

    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '<i class="fas fa-times"></i> Close Chart';
    closeBtn.className = 'chart-close-btn';
    closeBtn.onclick = (e) => {
			e.stopPropagation();
      chartElement.classList.remove('chart-expanded');
      document.body.style.overflow = '';
      closeBtn.remove();
		};

    chartElement.appendChild(closeBtn);
		document.body.style.overflow = 'hidden';
	}

	changeTimeRange(value) {
			console.log('Changing time range to:', value);

			const timeRanges = {
					'1': 1 * 60 * 1000,
					'5': 5 * 60 * 1000,
					'15':  15 * 60 * 1000,
					'60': 60 * 60 * 1000
			};

			this.timeRange = timeRanges[value] || 5 * 60 * 1000;
			console.log(`Time range set to: ${this.timeRange / 60000} minutes`);
	}

	connectWebSocket() {
		const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

		console.log('Connecting to WebSocket:', wsUrl);

		this.websocket = new WebSocket(wsUrl);

		this.websocket. onopen = () => {
			console.log('WebSocket connected successfully! ');
			this.updateConnectionStatus(true);
			this.enableControls(true);

			this.checkSystemStatus();
		};

		this.websocket.onmessage = (event) => {
			try {
				const data = JSON.parse(event.data);
				console.log('Received message:', data. type);

				if (data.type === 'vlf_data') {
					this.handleVLFData(data);
				} else if (data.type === 'anomaly') {
						this.handleAnomalies(data);
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

	async checkSystemStatus() {
    try {
        const response = await fetch('/api/status');
        if (response.ok) {
            const data = await response.json();
            const isActive = data.vlf_system?. is_monitoring || false;
            console.log('System status checked:', isActive);
            this.updateMonitoringStatus(isActive);
        }
    } catch (error) {
        console.log('Could not check system status:', error);
    }
	}

	handleVLFData(data) {
			if (! this.observatoryConfig) return;
			
			const stations = this.observatoryConfig.vlf_stations?.monitored_stations || [];
			const timestamp = new Date(data.timestamp);
			this.totalDataPoints++;
			
			stations.forEach((station, index) => {
					const stationKey = station; //aca
					const signalData = data.signals[stationKey];
					
					if (signalData) {
							const valueElement = document.getElementById(`station${index + 1}Value`);
							if (valueElement) {
									valueElement.textContent = signalData.amplitude.toFixed(3);
							}
							
							const statusElement = document. getElementById(`station${index + 1}Status`);
							if (statusElement) {
									const freqSpan = statusElement.querySelector('.frequency');
									const ampSpan = statusElement.querySelector('.amplitude');
									if (freqSpan) freqSpan.textContent = `${signalData.frequency.toFixed(2)} kHz`;
									if (ampSpan) ampSpan.textContent = `${signalData.amplitude.toFixed(3)} V`;
							}
							
							this.updateChart(`station${index + 1}Chart`, timestamp, signalData.amplitude);
					}
			});
			
			this.updateOverviewChart(timestamp, data.signals);
			this.updateDataStats();
	}

	updateChart(chartId, timestamp, amplitude) {
			const chart = this.charts[chartId];
			if (!chart) return;
			
			const timeString = timestamp.toLocaleTimeString();
			
			chart.data.labels.push(timeString);
			chart.data.datasets[0].data.push(amplitude);
			
			const maxPoints = Math.floor(this.timeRange / 1000);
			
			if (chart.data.labels.length > maxPoints) {
					chart.data.labels.shift();
					chart.data.datasets[0].data.shift();
			}
			
			chart.update('none');
	}

	updateOverviewChart(timestamp, stationsData) {
			const overview = this.charts.overviewChart;
			if (!overview || !this.observatoryConfig) return;
			
			const stations = this.observatoryConfig.vlf_stations?.monitored_stations || [];
			const stationFreqs = this.observatoryConfig.vlf_stations?.station_frequencies || {};
			const timeString = timestamp.toLocaleTimeString();
			
			if (overview.data.datasets.length === 0) {
					stations.forEach((station, index) => {
							const freq = stationFreqs[station]?.freq || 0;
							const colorIndex = index % this.chartColors.length;
							overview.data.datasets.push({
									label: `${station} (${freq} kHz)`,
									stationId: station,
									data: [],
									borderColor: this.chartColors[colorIndex],
									backgroundColor: this.chartColors[colorIndex] + '20',
									borderWidth: 2,
									fill: false,
									tension: 0.4,
									pointRadius: 0,
									pointHoverRadius: 4
							});
					});
			}
			
			overview.data.labels.push(timeString);
			
			overview.data.datasets.forEach((dataset, index) => {
				const stationKey = dataset.stationId;
				const amplitude = stationsData[stationKey]?.amplitude || 0;
				dataset.data.push(amplitude);
			});
			
			const maxPoints = Math.floor(this.timeRange / 1000 / this.samplingInterval);
			
			if (overview. data.labels.length > maxPoints) {
					overview.data.labels.shift();
					overview. data.datasets.forEach(dataset => {
							dataset.data.shift();
					});
			}
			
			overview.update('none');
	}

	handleAnomalies(data) {
			const anomalyList = document.getElementById('anomalyList');
			if (!anomalyList) return;
			
			const noAnomalies = anomalyList.querySelector('.no-anomalies');
			if (noAnomalies) {
					noAnomalies.remove();
			}
			
			data.anomalies.forEach(anomaly => {
					const div = document.createElement('div');
					div.className = 'anomaly-item';
					div. innerHTML = `
							<span class="anomaly-time">${new Date(data.timestamp).toLocaleTimeString()}</span>
							<span class="anomaly-message">${anomaly}</span>
					`;
					anomalyList.insertBefore(div, anomalyList.firstChild);
			});
			
			while (anomalyList.children.length > 5) {
					anomalyList.removeChild(anomalyList.lastChild);
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

					console.log('Start response:', result);

					if (response.ok && result.status === 'success') {
							console.log('Monitoring started successfully');
							this.updateMonitoringStatus(true);
					} else {
							throw new Error(result.message || 'Failed to start monitoring');
					}
			} catch (error) {
					console.error('Error starting monitoring:', error);
					alert('Failed to start monitoring:  ' + error.message);
			}
	}

	async stopMonitoring() {
			console.log('🛑 Stopping monitoring...');

			try {
					const response = await fetch('/api/stop', { method: 'POST' });
					const result = await response.json();

					if (response.ok && (result.status === 'success' || result.status === 'stopped')) {
							console.log('Monitoring stopped successfully');
							this.updateMonitoringStatus(false);
					} else {
							throw new Error(result.message || 'Failed to stop monitoring');
					}
			} catch (error) {
					console.error('Error stopping monitoring:', error);
					alert('Failed to stop monitoring: ' + error.message);
			}
	}

	updateMonitoringStatus(monitoring) {
			const statusElement = document.getElementById('monitoringStatus');

			if (statusElement) {
					statusElement.textContent = monitoring ? 'Active' : 'Stopped';
					statusElement.style.color = monitoring ? '#4CAF50' : '#f44336';
			}

			const startBtn = document.getElementById('startBtn');
			const stopBtn = document.getElementById('stopBtn');

			if (startBtn) startBtn.disabled = monitoring;
			if (stopBtn) stopBtn.disabled = !monitoring;

			this.isMonitoring = monitoring;
			console.log(`Monitoring status updated: ${monitoring ? 'Active' : 'Stopped'}`);
	}

	async fetchSpaceWeather() {
			try {
					console.log('Fetching space weather data.. .');
					const response = await fetch('/api/space-weather/summary');

					if (response.ok) {
							const data = await response.json();
							console.log('Space weather data received:', data);
							this.updateSpaceWeatherDisplay(data);
					} else {
							console.error('Failed to fetch space weather:', response.status);

							this.updateSpaceWeatherDisplay({
								status: 'unknown',
                kp_index: '--',
                solar_wind_speed: '-- km/s',
                last_update: null
							});
					}
			} catch (error) {
					console.error('Error fetching space weather:', error);

					this.updateSpaceWeatherDisplay({
						status:  'unknown', 
            kp_index:  '--',
            solar_wind_speed: '-- km/s',
            last_update: null
					});
			}
	}

	updateSpaceWeatherDisplay(data) {
			const elements = {
					solarActivity: data.status || 'Unknown',
					kpIndex: data.kp_index || '--',
					solarWindSpeed: data.solar_wind_speed || '-- km/s'
			};

			Object.keys(elements).forEach(id => {
					const element = document.getElementById(id);
					if (element) {
							element. textContent = elements[id];
							if (id === 'solarActivity') {
									element.style.color = this.getSpaceWeatherColor(elements[id]);
							}
					}
			});

			const spaceWeatherUpdate = document.getElementById('spaceWeatherUpdate');
			if (spaceWeatherUpdate && data.last_update) {
					const updateTime = new Date(data.last_update);
					spaceWeatherUpdate.textContent = updateTime.toLocaleTimeString();
			}
	}

	getSpaceWeatherColor(status) {
			const colors = {
					'normal': '#4CAF50',
					'moderate': '#FF9800',
					'storm': '#f44336',
					'severe':  '#d32f2f'
			};
			return colors[status] || '#cccccc';
	}

	startSpaceWeatherUpdates() {
			console.log('Starting space weather updates...');

			this.fetchSpaceWeather();

			setInterval(() => {
					this.fetchSpaceWeather();
			}, 600000);
	}

	updateDataStats() {
			const totalPointsElement = document.getElementById('totalPoints');
			if (totalPointsElement) {
					totalPointsElement.textContent = this.totalDataPoints;
			}

			const dataRateElement = document.getElementById('dataRate');
			if (dataRateElement) {
					dataRateElement.textContent = this.isMonitoring ? '1.0 Hz' : '0 Hz';
			}
	}

	clearData() {
			console.log('Clearing data...');
			
			Object.values(this.charts).forEach(chart => {
					chart.data. labels = [];
					chart.data.datasets.forEach(dataset => {
							dataset.data = [];
					});
					chart.update();
			});
			
			document.querySelectorAll('.band-value').forEach(el => el.textContent = '0.000');
			
			const anomalyList = document.getElementById('anomalyList');
			if (anomalyList) {
					anomalyList.innerHTML = '<div class="no-anomalies">No anomalies detected</div>';
			}
			
			this.totalDataPoints = 0;
			this.updateDataStats();
			
			console.log('Charts and data cleared');
	}

	startTimeUpdate() {
			const updateTime = () => {
					const now = new Date();

					const timestampElement = document.getElementById('timestamp');
					const serverTimeElement = document.getElementById('serverTime');

					if (timestampElement) {
							timestampElement.textContent = now.toLocaleTimeString();
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