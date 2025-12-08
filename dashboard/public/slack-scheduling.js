/**
 * Slack-Aware Scheduling Widget
 * 
 * Visualizes temporal shifting with deadline flexibility
 * Based on CarbonFlex research - 57% CO2 reduction potential
 */

class SlackSchedulingWidget {
    constructor(containerId, apiBaseUrl) {
        this.container = document.getElementById(containerId);
        this.apiBaseUrl = apiBaseUrl;
        this.chart = null;
    }

    render() {
        this.container.innerHTML = `
            <div class="slack-widget">
                <div class="slack-header">
                    <h3>Slack-Aware Scheduling</h3>
                    <p class="slack-subtitle">Optimize execution time within deadline flexibility</p>
                </div>
                
                <div class="slack-config">
                    <h4>Workload Configuration</h4>
                    <div class="config-grid">
                        <div class="config-item">
                            <label>Region</label>
                            <select id="slack-region">
                                <option value="eu-west-2">eu-west-2 (London)</option>
                                <option value="eu-north-1">eu-north-1 (Stockholm)</option>
                                <option value="us-east-1">us-east-1 (N. Virginia)</option>
                                <option value="us-west-2">us-west-2 (Oregon)</option>
                            </select>
                        </div>
                        <div class="config-item">
                            <label>Duration (hours)</label>
                            <input type="number" id="slack-duration" value="4" min="0.5" step="0.5">
                        </div>
                        <div class="config-item">
                            <label>Deadline (hours)</label>
                            <input type="number" id="slack-deadline" value="12" min="1" step="1">
                        </div>
                        <div class="config-item">
                            <label>vCPUs</label>
                            <input type="number" id="slack-vcpus" value="8" min="1">
                        </div>
                        <div class="config-item">
                            <label>Memory (GB)</label>
                            <input type="number" id="slack-memory" value="16" min="1">
                        </div>
                        <div class="config-item">
                            <label>Current CI (gCO₂/kWh)</label>
                            <input type="number" id="slack-current-ci" value="250" min="0">
                        </div>
                    </div>
                    <button id="slack-optimize" class="slack-button">Find Optimal Schedule</button>
                </div>
                
                <div class="slack-status" id="slack-status" style="display:none;">
                    Optimizing schedule...
                </div>
                
                <div class="slack-results" id="slack-results" style="display:none;">
                    <div class="slack-comparison">
                        <div class="comparison-card immediate">
                            <div class="card-header">
                                <span class="card-title">Immediate Execution</span>
                            </div>
                            <div class="card-metric">
                                <span class="metric-value" id="immediate-carbon">-</span>
                                <span class="metric-unit">gCO₂</span>
                            </div>
                            <div class="card-detail" id="immediate-ci">-</div>
                        </div>
                        
                        <div class="comparison-arrow">
                            <div class="arrow-icon">→</div>
                            <div class="arrow-savings" id="savings-badge">-</div>
                        </div>
                        
                        <div class="comparison-card optimal">
                            <div class="card-header">
                                <span class="card-title">Optimal Execution</span>
                            </div>
                            <div class="card-metric">
                                <span class="metric-value" id="optimal-carbon">-</span>
                                <span class="metric-unit">gCO₂</span>
                            </div>
                            <div class="card-detail" id="optimal-delay">-</div>
                        </div>
                    </div>
                    
                    <div class="slack-recommendation" id="slack-recommendation">
                        <div class="rec-badge" id="rec-badge">-</div>
                        <div class="rec-text" id="rec-text">-</div>
                    </div>
                    
                    <div class="slack-timeline">
                        <h4>Scheduling Timeline</h4>
                        <canvas id="slack-timeline-chart"></canvas>
                    </div>
                    
                    <div class="slack-windows">
                        <h4>Top Scheduling Windows</h4>
                        <div id="slack-windows-list"></div>
                    </div>
                </div>
            </div>
        `;

        this.attachEventListeners();
    }

    attachEventListeners() {
        document.getElementById('slack-optimize').addEventListener('click', () => {
            this.optimizeSchedule();
        });
    }

    async optimizeSchedule() {
        const statusDiv = document.getElementById('slack-status');
        const resultsDiv = document.getElementById('slack-results');

        try {
            // Show loading
            statusDiv.style.display = 'block';
            resultsDiv.style.display = 'none';

            // Get configuration
            const config = {
                region: document.getElementById('slack-region').value,
                workload_duration_hours: parseFloat(document.getElementById('slack-duration').value),
                deadline_hours: parseFloat(document.getElementById('slack-deadline').value),
                current_carbon_intensity: parseFloat(document.getElementById('slack-current-ci').value),
                vcpu_count: parseInt(document.getElementById('slack-vcpus').value),
                memory_gb: parseFloat(document.getElementById('slack-memory').value)
            };

            // Validate
            if (config.deadline_hours < config.workload_duration_hours) {
                throw new Error('Deadline must be longer than workload duration');
            }

            // Fetch optimization
            const data = await this.fetchOptimization(config);

            // Hide loading, show results
            statusDiv.style.display = 'none';
            resultsDiv.style.display = 'block';

            // Display results
            this.displayResults(data);

        } catch (error) {
            statusDiv.style.display = 'block';
            
            if (error.message.includes('Feature not enabled')) {
                statusDiv.innerHTML = `
                    <div class="slack-disabled">
                        <div>
                            <strong>Slack Scheduling Feature Disabled</strong>
                            <p>Enable with: <code>ENABLE_SLACK_SCHEDULING=true</code></p>
                        </div>
                    </div>
                `;
            } else {
                statusDiv.innerHTML = `
                    <div class="slack-error">
                        <div>
                            <strong>Error</strong>
                            <p>${error.message}</p>
                        </div>
                    </div>
                `;
            }
        }
    }

    async fetchOptimization(config) {
        try {
            const response = await fetch(
                `${this.apiBaseUrl}/v2/optimize-schedule`,
                {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(config)
                }
            );
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Failed to optimize schedule');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error fetching optimization:', error);
            throw error;
        }
    }

    displayResults(data) {
        // Immediate execution
        document.getElementById('immediate-carbon').textContent = 
            data.immediate_execution.carbon_footprint_gco2.toFixed(1);
        document.getElementById('immediate-ci').textContent = 
            `${data.immediate_execution.carbon_intensity} gCO₂/kWh`;

        // Optimal execution
        if (data.optimal_execution) {
            document.getElementById('optimal-carbon').textContent = 
                data.optimal_execution.carbon_footprint_gco2.toFixed(1);
            document.getElementById('optimal-delay').textContent = 
                `Delay: ${data.optimal_execution.delay_hours}h`;
        }

        // Savings
        const savingsPercent = data.savings.percent;
        document.getElementById('savings-badge').textContent = 
            `${savingsPercent}% SAVINGS`;
        document.getElementById('savings-badge').className = 
            `arrow-savings ${savingsPercent >= 20 ? 'high' : savingsPercent >= 10 ? 'medium' : 'low'}`;

        // Recommendation
        const recText = {
            'DELAY_RECOMMENDED': 'RECOMMENDED',
            'DELAY_OPTIONAL': 'OPTIONAL',
            'EXECUTE_NOW': 'EXECUTE NOW'
        };
        document.getElementById('rec-badge').textContent = 
            recText[data.recommendation] || data.recommendation;
        document.getElementById('rec-text').textContent = data.reason;

        // Timeline chart
        if (data.scheduling_windows && data.scheduling_windows.length > 0) {
            this.renderTimelineChart(data.scheduling_windows, data.immediate_execution.carbon_footprint_gco2);
        }

        // Windows list
        this.renderWindowsList(data.scheduling_windows);
    }

    renderTimelineChart(windows, immediateCarbon) {
        const ctx = document.getElementById('slack-timeline-chart');
        
        if (this.chart) {
            this.chart.destroy();
        }

        const labels = windows.map(w => `+${w.delay_hours}h`);
        const carbonData = windows.map(w => w.carbon_footprint_gco2);
        const savingsData = windows.map(w => 
            ((immediateCarbon - w.carbon_footprint_gco2) / immediateCarbon * 100).toFixed(1)
        );

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Carbon Footprint (gCO₂)',
                    data: carbonData,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            afterLabel: function(context) {
                                const savings = savingsData[context.dataIndex];
                                return `Savings: ${savings}%`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'Carbon Footprint (gCO₂)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Delay from Now'
                        }
                    }
                }
            }
        });
    }

    renderWindowsList(windows) {
        const listDiv = document.getElementById('slack-windows-list');
        
        if (!windows || windows.length === 0) {
            listDiv.innerHTML = '<p>No scheduling windows available</p>';
            return;
        }

        listDiv.innerHTML = windows.slice(0, 5).map((window, i) => `
            <div class="window-item ${i === 0 ? 'best' : ''}">
                <div class="window-rank">${i + 1}</div>
                <div class="window-details">
                    <div class="window-time">
                        ${window.delay_hours === 0 ? 'Now' : `+${window.delay_hours}h`}
                        ${window.start_time ? `(${new Date(window.start_time).toLocaleTimeString()})` : ''}
                    </div>
                    <div class="window-metrics">
                        <span class="metric">${window.carbon_footprint_gco2.toFixed(1)} gCO₂</span>
                        <span class="metric">${window.avg_carbon_intensity.toFixed(0)} gCO₂/kWh</span>
                    </div>
                </div>
                ${i === 0 ? '<div class="window-badge">Best</div>' : ''}
            </div>
        `).join('');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const apiBaseUrl = window.API_BASE_URL || 'https://your-api-id.execute-api.eu-west-2.amazonaws.com/Prod';
    const widget = new SlackSchedulingWidget('slack-widget-container', apiBaseUrl);
    widget.render();
});
