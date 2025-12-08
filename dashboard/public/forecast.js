/**
 * CarbonX Forecast Widget
 * 
 * Displays carbon intensity forecasts with uncertainty bands
 * Based on CarbonX research paper
 */

class ForecastWidget {
    constructor(containerId, apiBaseUrl) {
        this.container = document.getElementById(containerId);
        this.apiBaseUrl = apiBaseUrl;
        this.chart = null;
        this.currentRegion = 'eu-west-2';
        this.forecastHours = 24;
    }

    async fetchForecast(region, hoursAhead = 24) {
        try {
            const response = await fetch(
                `${this.apiBaseUrl}/v2/forecast?region=${region}&hours_ahead=${hoursAhead}`
            );
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Failed to fetch forecast');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error fetching forecast:', error);
            throw error;
        }
    }

    render() {
        this.container.innerHTML = `
            <div class="forecast-widget">
                <div class="forecast-header">
                    <h3>Carbon Intensity Forecast</h3>
                    <div class="forecast-controls">
                        <select id="forecast-region" class="forecast-select">
                            <option value="eu-west-2">EU West 2 (London)</option>
                            <option value="eu-west-1">EU West 1 (Ireland)</option>
                            <option value="eu-central-1">EU Central 1 (Frankfurt)</option>
                            <option value="us-east-1">US East 1 (Virginia)</option>
                            <option value="us-west-2">US West 2 (Oregon)</option>
                            <option value="us-west-1">US West 1 (California)</option>
                        </select>
                        <select id="forecast-horizon" class="forecast-select">
                            <option value="24">24 hours</option>
                            <option value="48">48 hours (2 days)</option>
                            <option value="96">96 hours (4 days)</option>
                            <option value="168">168 hours (7 days)</option>
                        </select>
                        <button id="forecast-refresh" class="forecast-button">Refresh</button>
                    </div>
                </div>
                
                <div class="forecast-status" id="forecast-status">
                    Loading forecast...
                </div>
                
                <div class="forecast-chart-container" id="forecast-chart-container" style="display: none;">
                    <canvas id="forecast-chart"></canvas>
                </div>
                
                <div class="forecast-metrics" id="forecast-metrics" style="display: none;">
                    <div class="metric-card">
                        <div class="metric-label">Expected Accuracy</div>
                        <div class="metric-value" id="forecast-mape">-</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Confidence Level</div>
                        <div class="metric-value" id="forecast-confidence">95%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Forecast Horizon</div>
                        <div class="metric-value" id="forecast-horizon-display">-</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Model Type</div>
                        <div class="metric-value">CarbonX-inspired</div>
                    </div>
                </div>
                
                <div class="forecast-optimal-windows" id="forecast-optimal-windows" style="display: none;">
                    <h4>Optimal Execution Windows</h4>
                    <div id="optimal-windows-list"></div>
                </div>
            </div>
        `;

        this.attachEventListeners();
        this.loadForecast();
    }

    attachEventListeners() {
        const regionSelect = document.getElementById('forecast-region');
        const horizonSelect = document.getElementById('forecast-horizon');
        const refreshButton = document.getElementById('forecast-refresh');

        regionSelect.addEventListener('change', (e) => {
            this.currentRegion = e.target.value;
            this.loadForecast();
        });

        horizonSelect.addEventListener('change', (e) => {
            this.forecastHours = parseInt(e.target.value);
            this.loadForecast();
        });

        refreshButton.addEventListener('click', () => {
            this.loadForecast();
        });
    }

    async loadForecast() {
        const statusDiv = document.getElementById('forecast-status');
        const chartContainer = document.getElementById('forecast-chart-container');
        const metricsDiv = document.getElementById('forecast-metrics');
        const windowsDiv = document.getElementById('forecast-optimal-windows');

        try {
            // Show loading
            statusDiv.style.display = 'block';
            statusDiv.innerHTML = 'Loading forecast...';
            chartContainer.style.display = 'none';
            metricsDiv.style.display = 'none';
            windowsDiv.style.display = 'none';

            // Fetch forecast data
            const data = await this.fetchForecast(this.currentRegion, this.forecastHours);

            // Hide loading, show content
            statusDiv.style.display = 'none';
            chartContainer.style.display = 'block';
            metricsDiv.style.display = 'flex';

            // Update metrics
            this.updateMetrics(data);

            // Render chart
            this.renderChart(data);

            // Show optimal windows for shorter horizons
            if (this.forecastHours <= 48) {
                this.showOptimalWindows(data);
                windowsDiv.style.display = 'block';
            }

        } catch (error) {
            statusDiv.style.display = 'block';
            
            if (error.message.includes('Feature not enabled')) {
                statusDiv.innerHTML = `
                    <div class="forecast-disabled">
                        <div>
                            <strong>Forecast Feature Disabled</strong>
                            <p>Enable with: <code>ENABLE_CARBONX_FORECAST=true</code></p>
                        </div>
                    </div>
                `;
            } else if (error.message.includes('Failed to fetch')) {
                statusDiv.innerHTML = `
                    <div class="forecast-error">
                        <span class="icon">⚠️</span>
                        <div>
                            <strong>API Not Configured</strong>
                            <p>Configure API endpoint in app.js</p>
                        </div>
                    </div>
                `;
            } else {
                statusDiv.innerHTML = `
                    <div class="forecast-error">
                        <div>
                            <strong>Error Loading Forecast</strong>
                            <p>${error.message}</p>
                        </div>
                    </div>
                `;
            }
        }
    }

    updateMetrics(data) {
        const metrics = data.quality_metrics;
        
        document.getElementById('forecast-mape').textContent = 
            `${metrics.expected_mape_percent}% MAPE`;
        
        document.getElementById('forecast-confidence').textContent = 
            `${data.confidence_level * 100}%`;
        
        const hours = data.horizon_hours;
        const days = Math.floor(hours / 24);
        const remainingHours = hours % 24;
        let horizonText = '';
        if (days > 0) {
            horizonText = `${days} day${days > 1 ? 's' : ''}`;
            if (remainingHours > 0) {
                horizonText += ` ${remainingHours}h`;
            }
        } else {
            horizonText = `${hours} hours`;
        }
        document.getElementById('forecast-horizon-display').textContent = horizonText;
    }

    renderChart(data) {
        const canvas = document.getElementById('forecast-chart');
        const ctx = canvas.getContext('2d');

        // Destroy existing chart
        if (this.chart) {
            this.chart.destroy();
        }

        // Prepare data
        const labels = data.forecasts.map(f => {
            const date = new Date(f.timestamp);
            return date.toLocaleString('en-US', { 
                month: 'short', 
                day: 'numeric', 
                hour: '2-digit' 
            });
        });

        const forecastValues = data.forecasts.map(f => f.carbon_intensity);
        const upperBounds = data.prediction_intervals.map(i => i.upper_bound);
        const lowerBounds = data.prediction_intervals.map(i => i.lower_bound);

        // Create chart
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Forecast',
                        data: forecastValues,
                        borderColor: '#4CAF50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        borderWidth: 2,
                        pointRadius: 2,
                        fill: false
                    },
                    {
                        label: 'Upper Bound (95%)',
                        data: upperBounds,
                        borderColor: '#FF9800',
                        backgroundColor: 'rgba(255, 152, 0, 0.05)',
                        borderWidth: 1,
                        borderDash: [5, 5],
                        pointRadius: 0,
                        fill: '+1'
                    },
                    {
                        label: 'Lower Bound (95%)',
                        data: lowerBounds,
                        borderColor: '#FF9800',
                        backgroundColor: 'rgba(255, 152, 0, 0.05)',
                        borderWidth: 1,
                        borderDash: [5, 5],
                        pointRadius: 0,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    title: {
                        display: true,
                        text: `Carbon Intensity Forecast - ${data.region}`,
                        font: { size: 16 }
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y.toFixed(2)} gCO2/kWh`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'Carbon Intensity (gCO2/kWh)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Time'
                        },
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45
                        }
                    }
                }
            }
        });
    }

    showOptimalWindows(data) {
        // Calculate optimal windows for a 4-hour workload
        const forecasts = data.forecasts;
        const duration = 4;
        
        // Calculate rolling averages
        const windows = [];
        for (let i = 0; i <= forecasts.length - duration; i++) {
            const windowForecasts = forecasts.slice(i, i + duration);
            const avgCI = windowForecasts.reduce((sum, f) => sum + f.carbon_intensity, 0) / duration;
            
            windows.push({
                startHour: windowForecasts[0].hour,
                startTime: new Date(windowForecasts[0].timestamp),
                avgCI: avgCI
            });
        }
        
        // Sort by carbon intensity
        windows.sort((a, b) => a.avgCI - b.avgCI);
        
        // Take top 3
        const topWindows = windows.slice(0, 3);
        
        // Calculate savings vs immediate execution
        const immediateCI = forecasts.slice(0, duration).reduce((sum, f) => sum + f.carbon_intensity, 0) / duration;
        
        // Render windows
        const listDiv = document.getElementById('optimal-windows-list');
        listDiv.innerHTML = topWindows.map((window, i) => {
            const savings = ((immediateCI - window.avgCI) / immediateCI * 100).toFixed(1);
            const badgeClass = savings > 10 ? 'excellent' : savings > 5 ? 'good' : 'moderate';
            
            return `
                <div class="optimal-window">
                    <div class="window-rank">${badge} #${i + 1}</div>
                    <div class="window-details">
                        <div class="window-time">
                            ${window.startTime.toLocaleString('en-US', { 
                                month: 'short', 
                                day: 'numeric', 
                                hour: '2-digit',
                                minute: '2-digit'
                            })}
                        </div>
                        <div class="window-metrics">
                            <span class="window-ci">${window.avgCI.toFixed(1)} gCO2/kWh</span>
                            <span class="window-savings ${savings > 0 ? 'positive' : 'negative'}">
                                ${savings > 0 ? '↓' : '↑'} ${Math.abs(savings)}% vs now
                            </span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const apiBaseUrl = window.API_BASE_URL || 'https://your-api-id.execute-api.eu-west-2.amazonaws.com/Prod';
    const widget = new ForecastWidget('forecast-widget-container', apiBaseUrl);
    widget.render();
});
