/**
 * Energy Profiling Dashboard
 * 
 * Visualizes energy consumption breakdown, identifies hotspots,
 * and provides optimization recommendations.
 */

// Mock data for demonstration
const mockProfiles = {
    'test-suite-v1': {
        workload_id: 'test-suite-v1',
        name: 'Test Suite v1.0',
        total_energy_j: 10000,
        breakdown: {
            cpu_j: 6000,
            memory_j: 2000,
            gpu_j: 1500,
            disk_j: 300,
            network_j: 200
        },
        breakdown_percent: {
            cpu_j: 60,
            memory_j: 20,
            gpu_j: 15,
            disk_j: 3,
            network_j: 2
        },
        phases: [
            { name: 'setup', energy_j: 500, cpu_j: 400, memory_j: 100, duration_s: 5 },
            { name: 'database_queries', energy_j: 4000, cpu_j: 2500, memory_j: 1000, gpu_j: 500, duration_s: 40 },
            { name: 'api_tests', energy_j: 3000, cpu_j: 2000, memory_j: 600, gpu_j: 400, duration_s: 30 },
            { name: 'integration_tests', energy_j: 2000, cpu_j: 1000, memory_j: 300, gpu_j: 600, disk_j: 100, duration_s: 20 },
            { name: 'cleanup', energy_j: 500, cpu_j: 100, network_j: 200, disk_j: 200, duration_s: 5 }
        ],
        hotspots: [
            {
                phase_name: 'database_queries',
                energy_j: 4000,
                percentage: 40,
                duration_s: 40,
                power_w: 100,
                recommendation: 'CPU-intensive: Consider query optimization, indexing, or connection pooling'
            },
            {
                phase_name: 'api_tests',
                energy_j: 3000,
                percentage: 30,
                duration_s: 30,
                power_w: 100,
                recommendation: 'Consider reducing API calls, implementing caching, or batching requests'
            }
        ],
        timestamp: new Date().toISOString()
    },
    'build-process-v1': {
        workload_id: 'build-process-v1',
        name: 'Docker Build v1.0',
        total_energy_j: 15000,
        breakdown: {
            cpu_j: 10000,
            memory_j: 3000,
            gpu_j: 0,
            disk_j: 1500,
            network_j: 500
        },
        breakdown_percent: {
            cpu_j: 66.7,
            memory_j: 20,
            gpu_j: 0,
            disk_j: 10,
            network_j: 3.3
        },
        phases: [
            { name: 'dependency_download', energy_j: 2000, cpu_j: 500, network_j: 500, disk_j: 1000, duration_s: 20 },
            { name: 'compilation', energy_j: 8000, cpu_j: 6000, memory_j: 1500, disk_j: 500, duration_s: 80 },
            { name: 'packaging', energy_j: 3000, cpu_j: 2000, memory_j: 800, disk_j: 200, duration_s: 30 },
            { name: 'image_push', energy_j: 2000, cpu_j: 1500, memory_j: 700, network_j: 300, duration_s: 20 }
        ],
        hotspots: [
            {
                phase_name: 'compilation',
                energy_j: 8000,
                percentage: 53.3,
                duration_s: 80,
                power_w: 100,
                recommendation: 'CPU-intensive: Consider incremental builds, build caching, or parallel compilation'
            }
        ],
        timestamp: new Date().toISOString()
    }
};

let currentProfile = null;
let componentChart = null;
let phaseChart = null;

// API Configuration
const API_BASE_URL = 'https://your-api-gateway-url.amazonaws.com/v2';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadProfileList();
    setupEventListeners();
});

function loadProfileList() {
    const profileSelect = document.getElementById('profileSelect');
    
    if (!profileSelect) {
        console.error('Profile select element not found');
        return;
    }
    
    Object.keys(mockProfiles).forEach(id => {
        const profile = mockProfiles[id];
        const option = new Option(profile.name, id);
        profileSelect.add(option);
    });
}

function setupEventListeners() {
    const loadBtn = document.getElementById('loadProfileBtn');
    if (loadBtn) {
        loadBtn.addEventListener('click', loadProfile);
    }
    
    const optimizerBtn = document.getElementById('runOptimizerBtn');
    if (optimizerBtn) {
        optimizerBtn.addEventListener('click', runOptimizer);
    }
}

function loadProfile() {
    const profileId = document.getElementById('profileSelect').value;
    if (!profileId) {
        alert('Please select a profile');
        return;
    }
    
    currentProfile = mockProfiles[profileId];
    displayProfile(currentProfile);
}

function displayProfile(profile) {
    // Carbon intensity (example: UK grid average)
    const carbonIntensity = 250; // gCO₂/kWh
    
    // Convert energy to carbon
    const energyKwh = profile.total_energy_j / 3600000;
    const carbonG = energyKwh * carbonIntensity;
    
    // Calculate carbon equivalent
    const carbonEquivalent = getCarbonEquivalent(carbonG);
    
    // Update summary cards
    document.getElementById('totalEnergy').textContent = `${profile.total_energy_j.toLocaleString()} J`;
    document.getElementById('totalEnergyKwh').textContent = `${energyKwh.toFixed(4)} kWh`;
    document.getElementById('totalCarbon').textContent = formatCarbon(carbonG);
    document.getElementById('carbonEquivalent').textContent = carbonEquivalent;
    document.getElementById('hotspotsCount').textContent = profile.hotspots.length;
    
    const totalDuration = profile.phases.reduce((sum, p) => sum + p.duration_s, 0);
    document.getElementById('avgPower').textContent = `${(profile.total_energy_j / totalDuration).toFixed(1)} W`;
    
    // Display component breakdown
    displayComponentBreakdown(profile);
    
    // Display hotspots
    displayHotspots(profile.hotspots, carbonIntensity);
    
    // Display phase timeline
    displayPhaseTimeline(profile.phases);
    
    // Display recommendations
    displayRecommendations(profile.hotspots);
}

function formatCarbon(carbonG) {
    if (carbonG < 1) {
        return `${carbonG.toFixed(2)} g`;
    } else if (carbonG < 1000) {
        return `${carbonG.toFixed(1)} g`;
    } else {
        return `${(carbonG / 1000).toFixed(2)} kg`;
    }
}

function getCarbonEquivalent(carbonG) {
    // Carbon equivalents
    const milesPerGCO2 = 0.00000227;
    const smartphoneChargesPerGCO2 = 0.0833;
    
    if (carbonG < 10) {
        const charges = carbonG * smartphoneChargesPerGCO2;
        return `≈ ${charges.toFixed(1)} phone charges`;
    } else if (carbonG < 1000) {
        const miles = carbonG * milesPerGCO2;
        return `≈ ${miles.toFixed(2)} miles driven`;
    } else {
        const kg = carbonG / 1000;
        return `≈ ${kg.toFixed(2)} kg CO₂`;
    }
}

function displayComponentBreakdown(profile) {
    const ctx = document.getElementById('componentChart').getContext('2d');
    
    if (componentChart) {
        componentChart.destroy();
    }
    
    const components = ['CPU', 'Memory', 'GPU', 'Disk', 'Network'];
    const energies = [
        profile.breakdown.cpu_j,
        profile.breakdown.memory_j,
        profile.breakdown.gpu_j,
        profile.breakdown.disk_j,
        profile.breakdown.network_j
    ];
    const percentages = [
        profile.breakdown_percent.cpu_j,
        profile.breakdown_percent.memory_j,
        profile.breakdown_percent.gpu_j,
        profile.breakdown_percent.disk_j,
        profile.breakdown_percent.network_j
    ];
    
    // Professional color scheme - distinct and accessible
    const colors = [
        '#000000',  // Black for CPU (most important)
        '#22c55e',  // Accent green for Memory
        '#667eea',  // Purple for GPU
        '#f59e0b',  // Amber for Disk
        '#06b6d4'   // Cyan for Network
    ];
    
    componentChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: components,
            datasets: [{
                data: energies,
                backgroundColor: colors,
                borderWidth: 4,
                borderColor: '#ffffff',
                hoverBorderWidth: 6,
                hoverBorderColor: '#000000'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#000000',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    titleFont: {
                        size: 14,
                        weight: '600',
                        family: 'Inter'
                    },
                    bodyFont: {
                        size: 13,
                        family: 'JetBrains Mono'
                    },
                    borderColor: '#000000',
                    borderWidth: 1,
                    padding: 16,
                    displayColors: true,
                    boxWidth: 12,
                    boxHeight: 12,
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const percent = percentages[context.dataIndex];
                            return `${label}: ${value.toLocaleString()} J (${percent.toFixed(1)}%)`;
                        }
                    }
                }
            },
            animation: {
                animateRotate: true,
                animateScale: true,
                duration: 800,
                easing: 'easeInOutQuart'
            }
        }
    });
    
    // Update legend
    const legendContainer = document.getElementById('componentLegend');
    legendContainer.innerHTML = components.map((comp, i) => `
        <div class="legend-item">
            <div class="legend-color" style="background: ${colors[i]}"></div>
            <div class="legend-label">${comp}</div>
            <div class="legend-value">${percentages[i].toFixed(1)}%</div>
        </div>
    `).join('');
}

function displayHotspots(hotspots, carbonIntensity = 250) {
    const container = document.getElementById('hotspotsContainer');
    
    if (hotspots.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No hotspots detected (all phases <20% of total energy)</p></div>';
        return;
    }
    
    container.innerHTML = hotspots.map(hotspot => {
        const severity = hotspot.percentage > 40 ? 'critical' : hotspot.percentage > 25 ? 'major' : 'minor';
        
        // Calculate carbon for this hotspot
        const energyKwh = hotspot.energy_j / 3600000;
        const carbonG = energyKwh * carbonIntensity;
        
        return `
            <div class="hotspot-card ${severity}">
                <div class="hotspot-header">
                    <div class="hotspot-name">${hotspot.phase_name}</div>
                    <div class="hotspot-percentage">${hotspot.percentage.toFixed(1)}%</div>
                </div>
                <div class="hotspot-stats">
                    <div class="hotspot-stat">
                        <div class="hotspot-stat-label">Energy</div>
                        <div class="hotspot-stat-value">${hotspot.energy_j.toLocaleString()} J</div>
                    </div>
                    <div class="hotspot-stat">
                        <div class="hotspot-stat-label">Carbon</div>
                        <div class="hotspot-stat-value">${formatCarbon(carbonG)}</div>
                    </div>
                    <div class="hotspot-stat">
                        <div class="hotspot-stat-label">Power</div>
                        <div class="hotspot-stat-value">${hotspot.power_w.toFixed(1)} W</div>
                    </div>
                </div>
                <div class="hotspot-recommendation">${hotspot.recommendation}</div>
            </div>
        `;
    }).join('');
}

function displayPhaseTimeline(phases) {
    const ctx = document.getElementById('phaseChart').getContext('2d');
    
    if (phaseChart) {
        phaseChart.destroy();
    }
    
    phaseChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: phases.map(p => p.name),
            datasets: [{
                label: 'Energy (J)',
                data: phases.map(p => p.energy_j),
                backgroundColor: '#667eea',
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Energy: ${context.parsed.y.toLocaleString()} J`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Energy (J)'
                    }
                }
            }
        }
    });
}

function displayRecommendations(hotspots) {
    const container = document.getElementById('recommendationsContainer');
    
    if (!container) return;
    
    if (hotspots.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No specific recommendations. Energy distribution is well-balanced.</p></div>';
        return;
    }
    
    container.innerHTML = hotspots.slice(0, 3).map((hotspot, i) => `
        <div class="recommendation-card">
            <div class="recommendation-title">
                ${i + 1}. Optimize ${hotspot.phase_name}
            </div>
            <div class="recommendation-text">
                ${hotspot.recommendation}
            </div>
            <div class="recommendation-impact">
                Potential savings: ${hotspot.energy_j.toLocaleString()} J (${hotspot.percentage.toFixed(1)}% of total)
            </div>
        </div>
    `).join('');
}

// Utility functions for timestamp
function updateTimestamp() {
    const elem = document.getElementById('last-updated-time');
    if (elem) {
        const now = new Date();
        elem.textContent = now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
    }
}

function refreshData() {
    location.reload();
}

// Initialize timestamp
updateTimestamp();
setInterval(updateTimestamp, 60000);

// Test Suite Optimizer Functions

async function runOptimizer() {
    if (!currentProfile) {
        alert('Please load a profile first');
        return;
    }
    
    const btn = document.getElementById('runOptimizerBtn');
    btn.textContent = 'Analyzing...';
    btn.disabled = true;
    
    try {
        // Prepare profile data for optimizer
        const profileData = {
            components: {
                cpu: currentProfile.breakdown.cpu_j,
                gpu: currentProfile.breakdown.gpu_j,
                ram: currentProfile.breakdown.memory_j,
                disk: currentProfile.breakdown.disk_j,
                network: currentProfile.breakdown.network_j
            },
            phases: currentProfile.phases
        };
        
        // Call optimizer API (mock for now)
        const analysis = await analyzeTestSuite(profileData);
        
        // Display results
        displayOptimizerResults(analysis);
        
    } catch (error) {
        console.error('Optimizer error:', error);
        alert('Failed to analyze test suite. Please try again.');
    } finally {
        btn.textContent = 'Analyze Test Suite';
        btn.disabled = false;
    }
}

async function analyzeTestSuite(profileData) {
    // Mock implementation - replace with actual API call
    // const response = await fetch(`${API_BASE_URL}/optimize-test-suite`, {
    //     method: 'POST',
    //     headers: { 'Content-Type': 'application/json' },
    //     body: JSON.stringify({ profile_data: profileData })
    // });
    // return await response.json();
    
    // Mock data for demonstration
    return {
        total_energy_j: profileData.components.cpu + profileData.components.gpu + 
                       profileData.components.ram + profileData.components.disk + 
                       profileData.components.network,
        total_carbon_g: 1.512,
        recommendations: [
            {
                type: 'parallelization',
                priority: 'critical',
                title: 'Parallelize Independent Tests',
                description: 'Running 5 test phases sequentially. Parallelizing independent tests can reduce execution time and energy by 30-50%.',
                potential_savings: {
                    percent: 35.0,
                    energy_j: 3500,
                    carbon_g: 0.529,
                    carbon_equivalent: '≈ 0.07 phone charges'
                },
                effort: 'medium',
                implementation_steps: [
                    'Identify independent tests (no shared state/resources)',
                    'Configure test runner for parallel execution (e.g., pytest -n auto)',
                    'Set optimal worker count (typically CPU cores - 1)',
                    'Add test isolation (separate databases, temp directories)',
                    'Monitor for race conditions and flaky tests'
                ],
                code_example: '# pytest.ini\n[pytest]\naddopts = -n auto --dist loadscope\n\n# Or in CI/CD\npytest -n 4 --dist loadfile tests/'
            },
            {
                type: 'resource_optimization',
                priority: 'high',
                title: 'Optimize CPU-Intensive Operations',
                description: 'CPU consumes 60.0% of total energy. Optimize algorithms and reduce computational complexity.',
                potential_savings: {
                    percent: 12.0,
                    energy_j: 1200,
                    carbon_g: 0.181,
                    carbon_equivalent: '≈ 0.02 phone charges'
                },
                effort: 'medium',
                implementation_steps: [
                    'Profile CPU-intensive functions',
                    'Optimize algorithms (reduce O(n²) to O(n log n))',
                    'Use compiled extensions (Cython, Numba)',
                    'Reduce unnecessary computations',
                    'Cache expensive calculations'
                ],
                code_example: '# Before: O(n²)\nfor i in items:\n    for j in items:\n        if i == j:\n            process(i)\n\n# After: O(n) with set\nitem_set = set(items)\nfor i in items:\n    if i in item_set:\n        process(i)'
            },
            {
                type: 'caching',
                priority: 'high',
                title: 'Implement Result Caching',
                description: 'Detected repeated operations. Caching results can eliminate redundant computations.',
                potential_savings: {
                    percent: 18.0,
                    energy_j: 1800,
                    carbon_g: 0.272,
                    carbon_equivalent: '≈ 0.03 phone charges'
                },
                effort: 'low',
                implementation_steps: [
                    'Use @lru_cache for pure functions',
                    'Cache API responses in tests',
                    'Use pytest-cache for expensive fixtures',
                    'Implement memoization for recursive functions',
                    'Cache compiled regexes and templates'
                ],
                code_example: 'from functools import lru_cache\n\n@lru_cache(maxsize=128)\ndef expensive_computation(x):\n    return complex_calculation(x)'
            },
            {
                type: 'resource_optimization',
                priority: 'medium',
                title: 'Reduce Memory Footprint',
                description: 'RAM consumes 20.0% of total energy. Optimize memory usage to reduce energy consumption.',
                potential_savings: {
                    percent: 5.0,
                    energy_j: 500,
                    carbon_g: 0.076,
                    carbon_equivalent: '≈ 0.01 phone charges'
                },
                effort: 'medium',
                implementation_steps: [
                    'Use generators instead of lists for large datasets',
                    'Release large objects explicitly (del, gc.collect())',
                    'Use memory-efficient data structures',
                    'Stream data instead of loading all at once',
                    'Reduce test data size'
                ],
                code_example: '# Before: Loads all in memory\ndata = [process(x) for x in range(1000000)]\n\n# After: Generator\ndata = (process(x) for x in range(1000000))'
            },
            {
                type: 'test_selection',
                priority: 'medium',
                title: 'Implement Smart Test Selection',
                description: 'Found 2 long-running test phases (>60s). Run expensive tests only on main branch or nightly builds.',
                potential_savings: {
                    percent: 15.0,
                    energy_j: 1500,
                    carbon_g: 0.227,
                    carbon_equivalent: '≈ 0.03 phone charges'
                },
                effort: 'low',
                implementation_steps: [
                    'Tag expensive tests with @pytest.mark.slow',
                    'Run fast tests on every commit',
                    'Run slow tests only on main branch or nightly',
                    'Use test impact analysis to run only affected tests',
                    'Implement test prioritization based on failure history'
                ],
                code_example: '@pytest.mark.slow\ndef test_expensive_operation():\n    pass\n\n# CI/CD - Fast tests on PR\npytest -m "not slow" tests/'
            }
        ],
        total_potential_savings: {
            energy_j: 8500,
            energy_percent: 85.0,
            carbon_g: 1.285,
            carbon_equivalent: '≈ 0.16 phone charges'
        },
        priority_breakdown: {
            critical: { count: 1, items: ['Parallelize Independent Tests'] },
            high: { count: 2, items: ['Optimize CPU-Intensive Operations', 'Implement Result Caching'] },
            medium: { count: 2, items: ['Reduce Memory Footprint', 'Implement Smart Test Selection'] },
            low: { count: 0, items: [] }
        },
        quick_wins: [
            {
                type: 'caching',
                priority: 'high',
                title: 'Implement Result Caching',
                description: 'Detected repeated operations. Caching results can eliminate redundant computations.',
                potential_savings: {
                    percent: 18.0,
                    energy_j: 1800,
                    carbon_g: 0.272,
                    carbon_equivalent: '≈ 0.03 phone charges'
                },
                effort: 'low',
                implementation_steps: [
                    'Use @lru_cache for pure functions',
                    'Cache API responses in tests',
                    'Use pytest-cache for expensive fixtures'
                ],
                code_example: 'from functools import lru_cache\n\n@lru_cache(maxsize=128)\ndef expensive_computation(x):\n    return complex_calculation(x)'
            },
            {
                type: 'test_selection',
                priority: 'medium',
                title: 'Implement Smart Test Selection',
                description: 'Found 2 long-running test phases (>60s). Run expensive tests only on main branch.',
                potential_savings: {
                    percent: 15.0,
                    energy_j: 1500,
                    carbon_g: 0.227,
                    carbon_equivalent: '≈ 0.03 phone charges'
                },
                effort: 'low',
                implementation_steps: [
                    'Tag expensive tests with @pytest.mark.slow',
                    'Run fast tests on every commit',
                    'Run slow tests only on main branch'
                ],
                code_example: '@pytest.mark.slow\ndef test_expensive():\n    pass'
            }
        ],
        implementation_roadmap: {
            phase_1_immediate: {
                title: 'Quick Wins (Week 1)',
                items: ['Parallelize Independent Tests']
            },
            phase_2_short_term: {
                title: 'High Impact (Weeks 2-4)',
                items: ['Optimize CPU-Intensive Operations', 'Implement Result Caching']
            },
            phase_3_medium_term: {
                title: 'Medium Impact (Month 2)',
                items: ['Reduce Memory Footprint', 'Implement Smart Test Selection']
            },
            phase_4_long_term: {
                title: 'Continuous Improvement (Ongoing)',
                items: []
            }
        }
    };
}

function displayOptimizerResults(analysis) {
    // Show results section
    document.getElementById('optimizerResults').style.display = 'block';
    
    // Update summary stats
    document.getElementById('potentialSavingsCO2').textContent = formatCarbon(analysis.total_potential_savings.carbon_g);
    document.getElementById('potentialSavingsEnergy').textContent = `${analysis.total_potential_savings.energy_j.toLocaleString()} J`;
    document.getElementById('potentialSavingsPercent').textContent = `${analysis.total_potential_savings.energy_percent.toFixed(1)}%`;
    document.getElementById('potentialSavingsEquivalent').textContent = analysis.total_potential_savings.carbon_equivalent;
    document.getElementById('recommendationCount').textContent = analysis.recommendations.length;
    document.getElementById('quickWinsCount').textContent = `${analysis.quick_wins.length} quick wins`;
    
    // Display quick wins
    displayQuickWins(analysis.quick_wins);
    
    // Display all recommendations
    displayAllRecommendations(analysis.recommendations);
    
    // Display roadmap
    displayRoadmap(analysis.implementation_roadmap);
    
    // Scroll to results
    document.getElementById('optimizerResults').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function displayQuickWins(quickWins) {
    const container = document.getElementById('quickWinsContainer');
    
    if (quickWins.length === 0) {
        container.innerHTML = '<div class="empty-state"><p>No quick wins identified. All optimizations require medium to high effort.</p></div>';
        return;
    }
    
    container.innerHTML = quickWins.map(rec => `
        <div class="recommendation-card quick-win">
            <div class="recommendation-header">
                <div class="recommendation-title">${rec.title}</div>
                <div class="recommendation-badge ${rec.priority}">${rec.priority}</div>
            </div>
            <div class="recommendation-description">${rec.description}</div>
            <div class="recommendation-savings">
                <div class="savings-item">
                    <span class="savings-label">Potential Savings:</span>
                    <span class="savings-value">${formatCarbon(rec.potential_savings.carbon_g)} (${rec.potential_savings.percent.toFixed(1)}%)</span>
                </div>
                <div class="savings-item">
                    <span class="savings-label">Effort:</span>
                    <span class="savings-value">${rec.effort}</span>
                </div>
            </div>
            <div class="recommendation-steps">
                <div class="steps-title">Implementation Steps:</div>
                <ol>
                    ${rec.implementation_steps.map(step => `<li>${step}</li>`).join('')}
                </ol>
            </div>
            ${rec.code_example ? `
                <div class="recommendation-code">
                    <div class="code-title">Code Example:</div>
                    <pre><code>${escapeHtml(rec.code_example)}</code></pre>
                </div>
            ` : ''}
        </div>
    `).join('');
}

function displayAllRecommendations(recommendations) {
    const container = document.getElementById('allRecommendationsContainer');
    
    // Group by priority
    const grouped = {
        critical: recommendations.filter(r => r.priority === 'critical'),
        high: recommendations.filter(r => r.priority === 'high'),
        medium: recommendations.filter(r => r.priority === 'medium'),
        low: recommendations.filter(r => r.priority === 'low')
    };
    
    let html = '';
    
    for (const [priority, recs] of Object.entries(grouped)) {
        if (recs.length === 0) continue;
        
        html += `
            <div class="priority-section">
                <h5 class="priority-title ${priority}">${priority.toUpperCase()} Priority (${recs.length})</h5>
                ${recs.map(rec => `
                    <div class="recommendation-card compact">
                        <div class="recommendation-header">
                            <div class="recommendation-title">${rec.title}</div>
                            <div class="recommendation-meta">
                                <span class="meta-item">${formatCarbon(rec.potential_savings.carbon_g)}</span>
                                <span class="meta-item">${rec.potential_savings.percent.toFixed(1)}%</span>
                                <span class="meta-item">Effort: ${rec.effort}</span>
                            </div>
                        </div>
                        <div class="recommendation-description">${rec.description}</div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    container.innerHTML = html;
}

function displayRoadmap(roadmap) {
    const container = document.getElementById('roadmapContainer');
    
    const phases = [
        { key: 'phase_1_immediate', icon: '🚀' },
        { key: 'phase_2_short_term', icon: '📈' },
        { key: 'phase_3_medium_term', icon: '🎯' },
        { key: 'phase_4_long_term', icon: '♻️' }
    ];
    
    container.innerHTML = phases.map(phase => {
        const data = roadmap[phase.key];
        if (!data || data.items.length === 0) return '';
        
        return `
            <div class="roadmap-phase">
                <div class="roadmap-header">
                    <span class="roadmap-icon">${phase.icon}</span>
                    <span class="roadmap-title">${data.title}</span>
                </div>
                <ul class="roadmap-items">
                    ${data.items.map(item => `<li>${item}</li>`).join('')}
                </ul>
            </div>
        `;
    }).join('');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
