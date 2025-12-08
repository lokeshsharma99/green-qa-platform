/**
 * Regression Tracking Dashboard
 * 
 * Track energy consumption across commits and detect regressions.
 * Most important feature for CI/CD integration.
 */

// Mock data for demonstration
const mockData = {
    main: {
        test_suite: {
            baseline: 5000,
            measurements: [
                { commit_sha: 'a1b2c3d', energy_j: 4900, timestamp: '2025-12-01T10:00:00Z', diff_percent: -2.0 },
                { commit_sha: 'e4f5g6h', energy_j: 5100, timestamp: '2025-12-02T10:00:00Z', diff_percent: 2.0 },
                { commit_sha: 'i7j8k9l', energy_j: 4950, timestamp: '2025-12-03T10:00:00Z', diff_percent: -1.0 },
                { commit_sha: 'm0n1o2p', energy_j: 5200, timestamp: '2025-12-04T10:00:00Z', diff_percent: 4.0 },
                { commit_sha: 'q3r4s5t', energy_j: 5800, timestamp: '2025-12-05T10:00:00Z', diff_percent: 16.0 },
                { commit_sha: 'u6v7w8x', energy_j: 5750, timestamp: '2025-12-06T10:00:00Z', diff_percent: 15.0 },
                { commit_sha: 'y9z0a1b', energy_j: 5100, timestamp: '2025-12-07T10:00:00Z', diff_percent: 2.0 },
                { commit_sha: 'c2d3e4f', energy_j: 4800, timestamp: '2025-12-08T10:00:00Z', diff_percent: -4.0 }
            ],
            trend: 'improving',
            slope: -25
        }
    }
};

let trendChart = null;
let currentBranch = 'main';
let currentWorkload = 'test_suite';
let performanceBudget = null;

// Carbon intensity (gCO2/kWh) - using average grid intensity
const CARBON_INTENSITY = 436; // Global average

// Carbon conversion helpers
function energyToCarbon(energyJ) {
    // Convert J to kWh: J / 3,600,000
    const energyKwh = energyJ / 3600000;
    // Calculate CO2 in grams
    const carbonG = energyKwh * CARBON_INTENSITY;
    return carbonG;
}

function formatCarbon(carbonG) {
    if (carbonG < 1) {
        return `${(carbonG * 1000).toFixed(1)} mg`;
    } else if (carbonG < 1000) {
        return `${carbonG.toFixed(2)} g`;
    } else {
        return `${(carbonG / 1000).toFixed(3)} kg`;
    }
}

function getCarbonEquivalent(carbonG) {
    // Phone charges (8g CO2 per charge)
    const phoneCharges = carbonG / 8;
    if (phoneCharges < 1) {
        return `${(phoneCharges * 60).toFixed(0)} seconds of phone charging`;
    } else if (phoneCharges < 10) {
        return `${phoneCharges.toFixed(1)} phone charges`;
    }
    
    // Miles driven (404g CO2 per mile)
    const miles = carbonG / 404;
    if (miles >= 0.1) {
        return `${miles.toFixed(2)} miles driven`;
    }
    
    return `${phoneCharges.toFixed(1)} phone charges`;
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    updateTimestamp();
    setInterval(updateTimestamp, 60000);
    loadData();
});

function setupEventListeners() {
    document.getElementById('loadDataBtn').addEventListener('click', loadData);
    document.getElementById('setBudgetBtn').addEventListener('click', setPerformanceBudget);
    document.getElementById('copyCicdBtn').addEventListener('click', copyCicdCode);
}

function updateTimestamp() {
    const now = new Date();
    document.getElementById('last-updated-time').textContent = 
        now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
}

function refreshData() {
    loadData();
}

function loadData() {
    currentBranch = document.getElementById('branchSelect').value;
    currentWorkload = document.getElementById('workloadSelect').value;
    
    const data = mockData[currentBranch]?.[currentWorkload];
    if (!data) {
        alert('No data available for this configuration');
        return;
    }
    
    displayData(data);
}

function displayData(data) {
    // Update status cards with carbon as primary, energy as detail
    const baselineCarbon = energyToCarbon(data.baseline);
    document.getElementById('baselineCarbon').textContent = formatCarbon(baselineCarbon);
    document.getElementById('baselineValue').textContent = `${data.baseline.toLocaleString()} J`;
    
    const latest = data.measurements[data.measurements.length - 1];
    const latestCarbon = energyToCarbon(latest.energy_j);
    document.getElementById('latestCarbon').textContent = formatCarbon(latestCarbon);
    document.getElementById('latestValue').textContent = `${latest.energy_j.toLocaleString()} J`;
    
    // Update trend
    const trendValue = document.getElementById('trendValue');
    const trendDetail = document.getElementById('trendDetail');
    
    if (data.trend === 'improving') {
        trendValue.textContent = 'Improving';
        const carbonSlope = energyToCarbon(Math.abs(data.slope));
        trendDetail.textContent = `-${formatCarbon(carbonSlope)}/commit`;
    } else if (data.trend === 'degrading') {
        trendValue.textContent = 'Degrading';
        const carbonSlope = energyToCarbon(Math.abs(data.slope));
        trendDetail.textContent = `+${formatCarbon(carbonSlope)}/commit`;
    } else {
        trendValue.textContent = 'Stable';
        trendDetail.textContent = 'no significant change';
    }
    
    // Count regressions
    const regressions = data.measurements.filter(m => m.diff_percent > 5);
    document.getElementById('regressionsCount').textContent = regressions.length;
    
    // Display trend chart
    displayTrendChart(data);
    
    // Display commits
    displayCommits(data.measurements, data.baseline);
    
    // Display regressions
    displayRegressions(regressions, data.baseline);
    
    // Update budget status
    if (performanceBudget) {
        updateBudgetStatus(latest.energy_j);
    }
}

function displayTrendChart(data) {
    const ctx = document.getElementById('trendChart').getContext('2d');
    
    if (trendChart) {
        trendChart.destroy();
    }
    
    const labels = data.measurements.map(m => m.commit_sha.substring(0, 7));
    const energies = data.measurements.map(m => m.energy_j);
    const baseline = Array(data.measurements.length).fill(data.baseline);
    
    // Color points based on regression status - minimal palette
    const pointColors = data.measurements.map(m => {
        if (m.diff_percent > 10) return '#ef4444';  // Danger
        if (m.diff_percent > 5) return '#f59e0b';   // Warning
        if (m.diff_percent < -5) return '#22c55e';  // Accent
        return '#000000';  // Black
    });
    
    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Energy',
                    data: energies,
                    borderColor: '#000000',
                    backgroundColor: 'rgba(0, 0, 0, 0.05)',
                    borderWidth: 2,
                    pointRadius: 5,
                    pointBackgroundColor: pointColors,
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    tension: 0.1,
                    fill: true
                },
                {
                    label: 'Baseline',
                    data: baseline,
                    borderColor: '#22c55e',
                    borderWidth: 1,
                    borderDash: [4, 4],
                    pointRadius: 0,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: { family: 'Inter', size: 12 },
                        color: '#737373',
                        usePointStyle: true,
                        padding: 16
                    }
                },
                tooltip: {
                    backgroundColor: '#171717',
                    titleColor: '#ffffff',
                    bodyColor: '#e5e5e5',
                    borderColor: '#404040',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            const measurement = data.measurements[context.dataIndex];
                            if (context.datasetIndex === 0) {
                                const carbon = energyToCarbon(measurement.energy_j);
                                return [
                                    `Energy: ${measurement.energy_j.toLocaleString()} J`,
                                    `Carbon: ${formatCarbon(carbon)}`,
                                    `Change: ${measurement.diff_percent > 0 ? '+' : ''}${measurement.diff_percent.toFixed(1)}%`
                                ];
                            }
                            const baselineCarbon = energyToCarbon(context.parsed.y);
                            return [
                                `Baseline: ${context.parsed.y.toLocaleString()} J`,
                                `Carbon: ${formatCarbon(baselineCarbon)}`
                            ];
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    grid: { color: '#e5e5e5', drawBorder: false },
                    ticks: { 
                        font: { family: 'JetBrains Mono', size: 11 },
                        color: '#737373'
                    }
                },
                x: {
                    grid: { display: false, drawBorder: false },
                    ticks: { 
                        font: { family: 'JetBrains Mono', size: 11 },
                        color: '#737373'
                    }
                }
            }
        }
    });
}

function displayCommits(measurements, baseline) {
    const container = document.getElementById('commitsContainer');
    
    // Show last 5 commits
    const recentCommits = measurements.slice(-5).reverse();
    
    container.innerHTML = recentCommits.map(commit => {
        let badgeClass = 'stable';
        let badgeText = 'Stable';
        let cardClass = '';
        
        if (commit.diff_percent > 10) {
            badgeClass = 'regression';
            badgeText = 'Critical';
            cardClass = 'regression';
        } else if (commit.diff_percent > 5) {
            badgeClass = 'minor';
            badgeText = 'Warning';
            cardClass = 'minor-regression';
        } else if (commit.diff_percent < -5) {
            badgeClass = 'improvement';
            badgeText = 'Improved';
            cardClass = 'improvement';
        }
        
        const carbon = energyToCarbon(commit.energy_j);
        
        return `
            <div class="commit-card ${cardClass}">
                <div class="commit-header">
                    <div class="commit-sha">${commit.commit_sha}</div>
                    <div class="commit-timestamp">${new Date(commit.timestamp).toLocaleDateString('en-GB')}</div>
                </div>
                <div class="commit-stats">
                    <div class="commit-stat">
                        <div class="commit-stat-label">Energy</div>
                        <div class="commit-stat-value">${commit.energy_j.toLocaleString()} J</div>
                    </div>
                    <div class="commit-stat">
                        <div class="commit-stat-label">Carbon</div>
                        <div class="commit-stat-value">${formatCarbon(carbon)}</div>
                    </div>
                    <div class="commit-stat">
                        <div class="commit-stat-label">vs Baseline</div>
                        <div class="commit-stat-value ${commit.diff_percent < 0 ? 'positive' : 'negative'}">
                            ${commit.diff_percent > 0 ? '+' : ''}${commit.diff_percent.toFixed(1)}%
                        </div>
                    </div>
                    <div class="commit-badge ${badgeClass}">${badgeText}</div>
                </div>
            </div>
        `;
    }).join('');
}

function displayRegressions(regressions, baseline) {
    const container = document.getElementById('regressionsContainer');
    
    if (regressions.length === 0) {
        container.innerHTML = '<div class="empty-state success"><p>No regressions detected. All commits within acceptable range.</p></div>';
        return;
    }
    
    container.innerHTML = regressions.map(regression => {
        let severity = 'minor';
        let severityText = 'Minor Regression';
        
        if (regression.diff_percent > 25) {
            severity = 'critical';
            severityText = 'Critical Regression';
        } else if (regression.diff_percent > 10) {
            severity = 'major';
            severityText = 'Major Regression';
        }
        
        const diffJ = regression.energy_j - baseline;
        const carbon = energyToCarbon(regression.energy_j);
        const carbonDiff = energyToCarbon(diffJ);
        const equivalent = getCarbonEquivalent(carbonDiff);
        
        return `
            <div class="regression-alert ${severity}">
                <div class="regression-header">
                    <div class="regression-severity">${severityText}</div>
                    <div class="regression-percentage">+${regression.diff_percent.toFixed(1)}%</div>
                </div>
                <div class="regression-details">
                    <div class="regression-detail">
                        <div class="regression-detail-label">Commit</div>
                        <div class="regression-detail-value">${regression.commit_sha}</div>
                    </div>
                    <div class="regression-detail">
                        <div class="regression-detail-label">Energy</div>
                        <div class="regression-detail-value">${regression.energy_j.toLocaleString()} J</div>
                    </div>
                    <div class="regression-detail">
                        <div class="regression-detail-label">Carbon</div>
                        <div class="regression-detail-value">${formatCarbon(carbon)}</div>
                    </div>
                    <div class="regression-detail">
                        <div class="regression-detail-label">Increase</div>
                        <div class="regression-detail-value">+${diffJ.toLocaleString()} J</div>
                    </div>
                    <div class="regression-detail">
                        <div class="regression-detail-label">CO₂ Increase</div>
                        <div class="regression-detail-value">+${formatCarbon(carbonDiff)}</div>
                    </div>
                    <div class="regression-detail">
                        <div class="regression-detail-label">Equivalent</div>
                        <div class="regression-detail-value">${equivalent}</div>
                    </div>
                </div>
                <div class="regression-message">
                    Energy consumption increased significantly. Review this commit for performance issues.
                </div>
            </div>
        `;
    }).join('');
}

function setPerformanceBudget() {
    const budgetInput = document.getElementById('budgetInput');
    const budget = parseFloat(budgetInput.value);
    
    if (isNaN(budget) || budget <= 0) {
        alert('Please enter a valid budget value');
        return;
    }
    
    performanceBudget = budget;
    
    const data = mockData[currentBranch]?.[currentWorkload];
    if (data) {
        const latest = data.measurements[data.measurements.length - 1];
        updateBudgetStatus(latest.energy_j);
    }
}

function updateBudgetStatus(currentEnergy) {
    const container = document.getElementById('budgetStatus');
    const withinBudget = currentEnergy <= performanceBudget;
    const headroom = performanceBudget - currentEnergy;
    const headroomPercent = (headroom / performanceBudget) * 100;
    const carbonHeadroom = energyToCarbon(Math.abs(headroom));
    
    container.className = withinBudget ? 'within' : 'exceeded';
    container.innerHTML = `
        <div class="budget-value">${Math.abs(headroom).toLocaleString()} J</div>
        <div class="budget-message">
            ${withinBudget 
                ? `Within budget. ${headroomPercent.toFixed(1)}% headroom remaining (${formatCarbon(carbonHeadroom)} CO₂).`
                : `Budget exceeded by ${Math.abs(headroomPercent).toFixed(1)}% (+${formatCarbon(carbonHeadroom)} CO₂).`
            }
        </div>
    `;
}

function copyCicdCode() {
    const code = document.getElementById('cicdCode').textContent;
    navigator.clipboard.writeText(code).then(() => {
        const btn = document.getElementById('copyCicdBtn');
        const originalText = btn.textContent;
        btn.textContent = 'Copied';
        setTimeout(() => {
            btn.textContent = originalText;
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}
