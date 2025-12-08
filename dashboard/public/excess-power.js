/**
 * Excess Power Display Component
 * Shows real-time excess renewable power and scheduling recommendations
 */

class ExcessPowerWidget {
    constructor() {
        this.apiBaseUrl = API_CONFIG.baseUrl;
        this.currentRegion = 'eu-west-2';
        this.data = null;
    }

    async fetchData(region) {
        // Check if API is configured
        if (!this.apiBaseUrl || this.apiBaseUrl.includes('YOUR-API-ID')) {
            return { 
                error: 'API not configured', 
                notConfigured: true 
            };
        }

        try {
            const response = await fetch(
                `${this.apiBaseUrl}/v2/excess-power?region=${region}`
            );
            
            if (!response.ok) {
                if (response.status === 403) {
                    return { error: 'Feature not enabled', disabled: true };
                }
                throw new Error(`HTTP ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Error fetching excess power:', error);
            return { error: error.message };
        }
    }

    render(containerId, region) {
        this.currentRegion = region;
        const container = document.getElementById(containerId);
        if (!container) return;

        // Show loading state
        container.innerHTML = '<div class="loading">Loading excess power data...</div>';

        // Fetch and display
        this.fetchData(region).then(data => {
            this.data = data;
            container.innerHTML = this.generateHTML(data);
        });
    }

    generateHTML(data) {
        if (data.notConfigured) {
            return `
                <div class="excess-power-card disabled">
                    <p>⚙️ API not configured</p>
                    <p class="note">Configure your API endpoint in app.js to see live data</p>
                    <p class="note">Or use the <a href="test-excess-power.html">test page</a> to see the widget in action</p>
                </div>
            `;
        }

        if (data.disabled) {
            return `
                <div class="excess-power-card disabled">
                    <p>⚙️ Excess Power feature not enabled</p>
                    <p class="note">Set ENABLE_EXCESS_POWER=true to enable</p>
                </div>
            `;
        }

        if (data.error) {
            return `
                <div class="excess-power-card error">
                    <p>⚠️ ${data.error}</p>
                    <p class="note">Check console for details</p>
                </div>
            `;
        }

        const badge = this.getRecommendationBadge(data.recommendation);
        const confidence = this.getConfidenceBadge(data.confidence);

        return `
            <div class="excess-power-card">
                <div class="card-header">
                    <h3>Excess Power Analysis</h3>
                    <span class="data-source">${data.data_source || 'estimated'}</span>
                </div>

                <div class="recommendation-section ${badge.class}">
                    <div class="recommendation-badge">
                        <span class="icon">${badge.icon}</span>
                        <span class="text">${badge.text}</span>
                    </div>
                    <div class="confidence-badge ${confidence.class}">
                        ${confidence.text}
                    </div>
                </div>

                <div class="metrics-grid">
                    <div class="metric">
                        <span class="label">Excess Renewable</span>
                        <span class="value">${data.excess_renewable_mw.toFixed(0)} MW</span>
                    </div>
                    <div class="metric">
                        <span class="label">Curtailment</span>
                        <span class="value">${data.curtailment_percentage.toFixed(1)}%</span>
                    </div>
                    <div class="metric">
                        <span class="label">Available Capacity</span>
                        <span class="value">${data.available_capacity_mw.toFixed(0)} MW</span>
                    </div>
                </div>

                <div class="reasoning">
                    <p>${data.reasoning}</p>
                </div>

                ${data.note ? `<div class="note">${data.note}</div>` : ''}

                <div class="timestamp">
                    Updated: ${new Date(data.timestamp).toLocaleString()}
                </div>
            </div>
        `;
    }

    getRecommendationBadge(recommendation) {
        const badges = {
            'SCHEDULE_NOW': {
                text: 'Schedule Now',
                class: 'excellent'
            },
            'SCHEDULE_PREFERRED': {
                text: 'Good Time',
                class: 'good'
            },
            'SCHEDULE_ACCEPTABLE': {
                text: 'Acceptable',
                class: 'moderate'
            },
            'DEFER': {
                text: 'Defer',
                class: 'high'
            },
            'UNAVAILABLE': {
                text: 'Unavailable',
                class: 'unknown'
            }
        };
        return badges[recommendation] || badges['UNAVAILABLE'];
    }

    getConfidenceBadge(confidence) {
        const badges = {
            'HIGH': { text: 'High Confidence', class: 'confidence-high' },
            'MEDIUM': { text: 'Medium Confidence', class: 'confidence-medium' },
            'LOW': { text: 'Low Confidence', class: 'confidence-low' },
            'NONE': { text: 'No Data', class: 'confidence-none' }
        };
        return badges[confidence] || badges['NONE'];
    }
}

// Initialize on page load
let excessPowerWidget;

document.addEventListener('DOMContentLoaded', function() {
    excessPowerWidget = new ExcessPowerWidget();
    
    // Render if container exists
    const container = document.getElementById('excess-power-widget');
    if (container) {
        excessPowerWidget.render('excess-power-widget', 'eu-west-2');
    }
});

// Export for use in other scripts
window.ExcessPowerWidget = ExcessPowerWidget;
