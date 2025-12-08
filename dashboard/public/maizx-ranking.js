/**
 * MAIZX Region Ranking Widget
 * 
 * Multi-region carbon optimization with 85% CO2 reduction potential
 * Based on MAIZX research paper
 */

class MAIZXRankingWidget {
    constructor(containerId, apiBaseUrl) {
        this.container = document.getElementById(containerId);
        this.apiBaseUrl = apiBaseUrl;
    }

    async fetchRanking(workload, regions) {
        try {
            const response = await fetch(
                `${this.apiBaseUrl}/v2/rank-regions`,
                {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({workload, regions})
                }
            );
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Failed to fetch ranking');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error fetching MAIZX ranking:', error);
            throw error;
        }
    }

    render() {
        this.container.innerHTML = `
            <div class="maizx-widget">
                <div class="maizx-header">
                    <h3>Multi-Region Optimization (MAIZX)</h3>
                    <p class="maizx-subtitle">Find the best AWS region for your workload</p>
                </div>
                
                <div class="maizx-config">
                    <h4>Workload Configuration</h4>
                    <div class="config-grid">
                        <div class="config-item">
                            <label>Duration (hours)</label>
                            <input type="number" id="maizx-duration" value="4" min="0.5" step="0.5">
                        </div>
                        <div class="config-item">
                            <label>vCPUs</label>
                            <input type="number" id="maizx-vcpus" value="8" min="1">
                        </div>
                        <div class="config-item">
                            <label>Memory (GB)</label>
                            <input type="number" id="maizx-memory" value="16" min="1">
                        </div>
                        <div class="config-item">
                            <label>Priority</label>
                            <select id="maizx-priority">
                                <option value="low">Low</option>
                                <option value="normal" selected>Normal</option>
                                <option value="high">High</option>
                                <option value="critical">Critical</option>
                            </select>
                        </div>
                    </div>
                    <button id="maizx-calculate" class="maizx-button">Calculate Best Region</button>
                </div>
                
                <div class="maizx-status" id="maizx-status" style="display:none;">
                    Calculating optimal region...
                </div>
                
                <div class="maizx-results" id="maizx-results" style="display:none;">
                    <div class="maizx-recommendation">
                        <div class="rec-details">
                            <div class="rec-region" id="maizx-region">-</div>
                            <div class="rec-savings" id="maizx-savings">-</div>
                        </div>
                    </div>
                    
                    <div class="maizx-metrics">
                        <div class="metric">
                            <span class="metric-label">Carbon Footprint</span>
                            <span class="metric-value" id="maizx-cfp">-</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Power Consumption</span>
                            <span class="metric-value" id="maizx-power">-</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">MAIZX Score</span>
                            <span class="metric-value" id="maizx-score">-</span>
                        </div>
                    </div>
                    
                    <div class="maizx-top-regions">
                        <h4>Top 3 Regions</h4>
                        <div id="maizx-top-list"></div>
                    </div>
                </div>
            </div>
        `;

        this.attachEventListeners();
    }

    attachEventListeners() {
        document.getElementById('maizx-calculate').addEventListener('click', () => {
            this.calculateRanking();
        });
    }

    async calculateRanking() {
        const statusDiv = document.getElementById('maizx-status');
        const resultsDiv = document.getElementById('maizx-results');

        try {
            // Show loading
            statusDiv.style.display = 'block';
            resultsDiv.style.display = 'none';

            // Get workload config
            const workload = {
                duration_hours: parseFloat(document.getElementById('maizx-duration').value),
                vcpu_count: parseInt(document.getElementById('maizx-vcpus').value),
                memory_gb: parseFloat(document.getElementById('maizx-memory').value),
                cpu_utilization: 0.7,
                priority: document.getElementById('maizx-priority').value
            };

            // Mock regions data (in real app, fetch from API)
            const regions = {
                'us-east-1': 450,
                'us-east-2': 420,
                'us-west-1': 320,
                'us-west-2': 200,
                'eu-west-1': 350,
                'eu-west-2': 180,
                'eu-central-1': 420,
                'ap-southeast-1': 380,
                'ap-northeast-1': 410
            };

            // Fetch ranking
            const data = await this.fetchRanking(workload, regions);

            // Hide loading, show results
            statusDiv.style.display = 'none';
            resultsDiv.style.display = 'block';

            // Update UI
            this.displayResults(data);

        } catch (error) {
            statusDiv.style.display = 'block';
            
            if (error.message.includes('Feature not enabled')) {
                statusDiv.innerHTML = `
                    <div class="maizx-disabled">
                        <div>
                            <strong>MAIZX Feature Disabled</strong>
                            <p>Enable with: <code>ENABLE_MAIZX_RANKING=true</code></p>
                        </div>
                    </div>
                `;
            } else {
                statusDiv.innerHTML = `
                    <div class="maizx-error">
                        <div>
                            <strong>Error</strong>
                            <p>${error.message}</p>
                        </div>
                    </div>
                `;
            }
        }
    }

    displayResults(data) {
        // Region
        document.getElementById('maizx-region').textContent = 
            `Recommended: ${data.recommended_region}`;

        // Savings
        document.getElementById('maizx-savings').textContent = 
            `Saves ${data.savings_vs_worst_percent}% vs worst region (${data.recommendation})`;

        // Metrics
        document.getElementById('maizx-cfp').textContent = 
            `${data.carbon_footprint_gco2.toFixed(2)} gCO2`;
        document.getElementById('maizx-power').textContent = 
            `${data.power_consumption_w.toFixed(1)} W`;
        document.getElementById('maizx-score').textContent = 
            data.maizx_score.toFixed(4);

        // Top 3 regions
        const topList = document.getElementById('maizx-top-list');
        topList.innerHTML = data.top_3_regions.map((region, i) => `
            <div class="top-region">
                <div class="region-rank">${i + 1}</div>
                <div class="region-details">
                    <div class="region-name">${region.region}</div>
                    <div class="region-metrics">
                        <span>${region.carbon_footprint_gco2.toFixed(1)} gCO2</span>
                        <span class="savings ${region.savings_percent > 0 ? 'positive' : ''}">
                            ${region.savings_percent > 0 ? '↓' : ''} ${region.savings_percent}%
                        </span>
                        <span class="rec-level">${region.recommendation}</span>
                    </div>
                </div>
            </div>
        `).join('');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const apiBaseUrl = window.API_BASE_URL || 'https://your-api-id.execute-api.eu-west-2.amazonaws.com/Prod';
    const widget = new MAIZXRankingWidget('maizx-widget-container', apiBaseUrl);
    widget.render();
});
