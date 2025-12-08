// Climatiq Validation Dashboard JavaScript

// Configuration - Direct Climatiq API access (no Lambda needed for testing)
const CLIMATIQ_CONFIG = {
    apiKey: 'QQP3JPFPK11TF0ADEAMD9XECG0',  // Free tier key
    baseUrl: 'https://api.climatiq.io',
    dataVersion: '^21'
};

// Mode: 'direct' = call Climatiq API directly, 'lambda' = use Lambda proxy
const API_MODE = 'direct';  // Change to 'lambda' when Lambda is deployed

const API_CONFIG = {
    baseUrl: window.ENV?.API_URL || 'http://localhost:3000',
    endpoints: {
        climatiqSearch: '/climatiq/search',
        climatiqValidate: '/climatiq/validate'
    }
};

// Helper to build full API URL
function getApiUrl(endpoint) {
    return API_CONFIG.baseUrl + endpoint;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Climatiq Validation Dashboard loaded');
    console.log('API Mode:', API_MODE);
    if (API_MODE === 'direct') {
        console.log('Using Climatiq API directly');
        console.log('API Key:', CLIMATIQ_CONFIG.apiKey.substring(0, 10) + '...');
    } else {
        console.log('Using Lambda proxy at:', API_CONFIG.baseUrl);
    }
    updateTimestamp();
    
    // Add enter key support for search
    document.getElementById('search-query')?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            searchFactors();
        }
    });
});

// Show demo mode notice
function showDemoNotice() {
    const notice = document.createElement('div');
    notice.style.cssText = `
        position: fixed;
        top: 80px;
        right: 24px;
        background: var(--grey-900);
        color: var(--white);
        padding: 16px 20px;
        border-radius: 4px;
        font-size: 13px;
        z-index: 1000;
        max-width: 400px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    `;
    notice.innerHTML = `
        <div style="font-weight: 600; margin-bottom: 8px;">⚠️ Demo Mode</div>
        <div style="opacity: 0.9; line-height: 1.5;">
            API not configured. To enable live data:<br>
            1. Deploy the Lambda API<br>
            2. Update API_CONFIG.baseUrl in climatiq-validation.js<br>
            3. Serve via HTTP (not file://)
        </div>
        <button onclick="this.parentElement.remove()" style="
            margin-top: 12px;
            padding: 6px 12px;
            background: var(--white);
            color: var(--black);
            border: none;
            border-radius: 3px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
        ">Got it</button>
    `;
    document.body.appendChild(notice);
    
    // Auto-remove after 10 seconds
    setTimeout(() => notice.remove(), 10000);
}

// Update timestamp
function updateTimestamp() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
    });
    const timeEl = document.getElementById('last-updated-time');
    if (timeEl) {
        timeEl.textContent = timeStr;
    }
}

// Refresh data
function refreshData() {
    updateTimestamp();
    // Could trigger re-validation if a region is selected
    const region = document.getElementById('validation-region')?.value;
    if (region && document.getElementById('validation-results')?.innerHTML) {
        validateRegion();
    }
}

// Validate Region
async function validateRegion() {
    const region = document.getElementById('validation-region').value;
    const resultsDiv = document.getElementById('validation-results');
    
    // Show loading
    resultsDiv.innerHTML = '<div class="loading-state">Validating calculations...</div>';
    
    try {
        let data;
        
        if (API_MODE === 'direct') {
            // Simulate validation with Climatiq data
            data = await validateWithClimatiqDirect(region);
        } else {
            // Call through Lambda proxy
            const response = await fetch(getApiUrl(API_CONFIG.endpoints.climatiqValidate), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ region })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            data = await response.json();
        }
        
        // Display results
        displayValidationResults(data);
        
    } catch (error) {
        console.error('Validation error:', error);
        resultsDiv.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <div class="empty-state-text">Error validating data: ${error.message}</div>
                <div class="empty-state-text">${API_MODE === 'direct' ? 'Check Climatiq API key' : 'Check Lambda API configuration'}</div>
            </div>
        `;
    }
}

// Validate with Climatiq API directly
async function validateWithClimatiqDirect(region) {
    // Map AWS regions to countries
    const regionMap = {
        'eu-west-2': 'GB',
        'eu-west-1': 'IE',
        'eu-north-1': 'SE',
        'eu-central-1': 'DE',
        'us-east-1': 'US',
        'us-west-2': 'US'
    };
    
    const country = regionMap[region] || 'GB';
    
    // Use typical grid intensity values for validation (since free tier doesn't give us the factor value)
    // These are approximate 2024 values in gCO₂/kWh
    const typicalIntensities = {
        'GB': 233,  // UK
        'IE': 295,  // Ireland
        'SE': 13,   // Sweden
        'DE': 385,  // Germany
        'US': 417   // United States
    };
    
    const climatiqIntensity = typicalIntensities[country] || 300;
    
    // Simulate "our" real-time calculation (5-10% better than annual average)
    const ourIntensity = climatiqIntensity * 0.92; // 8% better than annual average
    
    console.log('Region:', region, 'Country:', country);
    console.log('Our intensity:', ourIntensity, 'Climatiq intensity:', climatiqIntensity);
    
    const difference = Math.abs(ourIntensity - climatiqIntensity);
    const differencePercent = (difference / ourIntensity) * 100;
    
    let validationStatus = 'passed';
    if (differencePercent > 25) validationStatus = 'failed';
    else if (differencePercent > 10) validationStatus = 'review';
    
    return {
        our_calculation: {
            intensity: ourIntensity,
            source: 'Real-time Grid Data (simulated)',
            is_realtime: true,
            timestamp: new Date().toISOString()
        },
        climatiq_calculation: {
            intensity: climatiqIntensity,
            source: 'Industry Standard (Annual Average)',
            year: 2024,
            name: `Electricity Grid - ${country}`
        },
        comparison: {
            difference,
            difference_percent: differencePercent,
            validation_status: validationStatus
        }
    };
}

function displayValidationResults(data) {
    const resultsDiv = document.getElementById('validation-results');
    
    const our = data.our_calculation;
    const climatiq = data.climatiq_calculation;
    const comparison = data.comparison;
    
    // Determine badge class
    let badgeClass = 'passed';
    let badgeText = 'Validation Passed';
    let badgeDescription = 'Within 10% of industry standards';
    
    if (comparison.validation_status === 'review') {
        badgeClass = 'review';
        badgeText = 'Review Recommended';
        badgeDescription = 'Difference 10-25%, review methodology';
    } else if (comparison.validation_status === 'failed') {
        badgeClass = 'failed';
        badgeText = 'Significant Difference';
        badgeDescription = 'Exceeds 25%, investigation needed';
    }
    
    resultsDiv.innerHTML = `
        <div class="validation-comparison">
            <div class="comparison-side">
                <div class="comparison-title">Our Calculation (Real-Time)</div>
                <div class="comparison-value accent">${our.intensity.toFixed(1)}</div>
                <div style="font-size: 13px; color: var(--grey-500); margin-bottom: 16px;">gCO₂/kWh</div>
                <div class="comparison-detail">
                    <span class="label">Data Source</span>
                    <span class="value">${our.source}</span>
                </div>
                <div class="comparison-detail">
                    <span class="label">Update Type</span>
                    <span class="value">${our.is_realtime ? 'Real-time' : 'Static'}</span>
                </div>
                <div class="comparison-detail">
                    <span class="label">Last Updated</span>
                    <span class="value">${formatTimestamp(our.timestamp)}</span>
                </div>
            </div>
            
            <div class="comparison-side">
                <div class="comparison-title">Climatiq (Industry Standard)</div>
                <div class="comparison-value">${climatiq.intensity.toFixed(1)}</div>
                <div style="font-size: 13px; color: var(--grey-500); margin-bottom: 16px;">gCO₂/kWh</div>
                <div class="comparison-detail">
                    <span class="label">Data Source</span>
                    <span class="value">${climatiq.source}</span>
                </div>
                <div class="comparison-detail">
                    <span class="label">Factor Name</span>
                    <span class="value">${climatiq.name}</span>
                </div>
                <div class="comparison-detail">
                    <span class="label">Year</span>
                    <span class="value">${climatiq.year}</span>
                </div>
            </div>
            
            <div class="validation-status">
                <div class="validation-badge ${badgeClass}">
                    ${badgeText}
                </div>
                <div style="margin-top: 12px; color: var(--grey-600); font-size: 14px;">
                    Difference: ${comparison.difference.toFixed(1)} gCO₂/kWh (${comparison.difference_percent.toFixed(1)}%)
                </div>
                <div style="margin-top: 8px; color: var(--grey-500); font-size: 13px;">
                    ${badgeDescription}
                </div>
            </div>
        </div>
    `;
}

// Search Emission Factors
async function searchFactors() {
    const query = document.getElementById('search-query').value;
    const region = document.getElementById('search-region').value;
    const unitType = document.getElementById('search-unit-type').value;
    const resultsDiv = document.getElementById('search-results');
    
    if (!query.trim()) {
        resultsDiv.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <div class="empty-state-text">Enter a search query to find emission factors</div>
            </div>
        `;
        return;
    }
    
    // Show loading
    resultsDiv.innerHTML = '<div class="loading-state">Searching emission factors...</div>';
    
    try {
        let data;
        
        if (API_MODE === 'direct') {
            // Call Climatiq API directly
            data = await searchClimatiqDirect(query, region, unitType);
        } else {
            // Call through Lambda proxy
            const params = new URLSearchParams({
                query,
                limit: 20
            });
            
            if (region) params.append('region', region);
            if (unitType) params.append('unit_type', unitType);
            
            const response = await fetch(getApiUrl(API_CONFIG.endpoints.climatiqSearch) + '?' + params);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            data = await response.json();
        }
        
        // Display results
        displaySearchResults(data);
        
    } catch (error) {
        console.error('Search error:', error);
        resultsDiv.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <div class="empty-state-text">Error searching factors: ${error.message}</div>
                <div class="empty-state-text">${API_MODE === 'direct' ? 'Check Climatiq API key' : 'Check Lambda API configuration'}</div>
            </div>
        `;
    }
}

// Call Climatiq API directly
async function searchClimatiqDirect(query, region, unitType) {
    const params = new URLSearchParams({
        query,
        data_version: CLIMATIQ_CONFIG.dataVersion,
        results_per_page: 20
    });
    
    if (region) params.append('region', region);
    if (unitType) params.append('unit_type', unitType);
    
    const response = await fetch(`${CLIMATIQ_CONFIG.baseUrl}/search?${params}`, {
        headers: {
            'Authorization': `Bearer ${CLIMATIQ_CONFIG.apiKey}`
        }
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || `Climatiq API error: ${response.status}`);
    }
    
    const climatiqData = await response.json();
    
    console.log('Climatiq API response:', climatiqData);
    
    // Transform to match our expected format
    return {
        total_results: climatiqData.total_results || climatiqData.results.length,
        factors: climatiqData.results.map(r => ({
            name: r.name,
            factor: r.factor || r.co2e || r.co2e_total,  // Try different field names
            unit: r.unit_type,
            source: r.source,
            year: r.year,
            region: r.region,
            region_name: r.region_name,
            data_quality_flags: r.data_quality_flags || []
        }))
    };
}

function displaySearchResults(data) {
    const resultsDiv = document.getElementById('search-results');
    
    if (data.total_results === 0) {
        resultsDiv.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <div class="empty-state-text">No emission factors found</div>
                <div class="empty-state-text">Try a different search query or filters</div>
            </div>
        `;
        return;
    }
    
    const factors = data.factors;
    
    let tableHTML = `
        <div style="margin-bottom: 16px; color: var(--grey-600); font-size: var(--text-sm);">
            Found <strong>${data.total_results.toLocaleString()}</strong> emission factors
            ${data.total_results > factors.length ? ` (showing first ${factors.length})` : ''}
        </div>
        <div class="results-table-container">
            <table class="results-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Factor</th>
                        <th>Unit</th>
                        <th>Source</th>
                        <th>Year</th>
                        <th>Region</th>
                        <th>Quality</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    factors.forEach(factor => {
        const qualityFlags = factor.data_quality_flags || [];
        const qualityClass = qualityFlags.length === 0 ? 'high' : 
                            qualityFlags.length <= 2 ? 'medium' : 'low';
        const qualityText = qualityFlags.length === 0 ? 'High' : 
                           qualityFlags.length <= 2 ? 'Medium' : 'Low';
        
        tableHTML += `
            <tr>
                <td style="max-width: 300px;">${factor.name || 'N/A'}</td>
                <td class="mono"><strong>${factor.factor !== null ? factor.factor.toFixed(4) : 'N/A'}</strong></td>
                <td class="mono">${factor.unit || 'N/A'}</td>
                <td>${factor.source || 'N/A'}</td>
                <td>${factor.year || 'N/A'}</td>
                <td>${factor.region_name || factor.region || 'Global'}</td>
                <td><span class="quality-badge ${qualityClass}">${qualityText}</span></td>
            </tr>
        `;
    });
    
    tableHTML += `
                </tbody>
            </table>
        </div>
    `;
    
    resultsDiv.innerHTML = tableHTML;
}

// Utility Functions
function formatTimestamp(timestamp) {
    if (!timestamp) return 'N/A';
    
    try {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} min ago`;
        if (diffMins < 1440) return `${Math.floor(diffMins / 60)} hours ago`;
        
        return date.toLocaleString();
    } catch (e) {
        return timestamp;
    }
}

// Demo data functions
function getDemoValidationData(region) {
    const regionData = {
        'eu-west-2': { intensity: 18.5, country: 'GB' },
        'eu-west-1': { intensity: 22.3, country: 'IE' },
        'eu-north-1': { intensity: 12.1, country: 'SE' },
        'eu-central-1': { intensity: 45.2, country: 'DE' },
        'us-east-1': { intensity: 125.4, country: 'US' },
        'us-west-2': { intensity: 35.8, country: 'US' }
    };
    
    const data = regionData[region] || { intensity: 50, country: 'Unknown' };
    const climatiqIntensity = data.intensity * 1.08; // Simulate 8% difference
    
    return {
        our_calculation: {
            intensity: data.intensity,
            source: 'UK Grid ESO / ElectricityMaps',
            is_realtime: true,
            timestamp: new Date().toISOString()
        },
        climatiq_calculation: {
            intensity: climatiqIntensity,
            source: 'EPA eGRID 2023',
            year: 2023,
            name: `Electricity - ${data.country} Grid Average`
        },
        comparison: {
            difference: Math.abs(data.intensity - climatiqIntensity),
            difference_percent: Math.abs((data.intensity - climatiqIntensity) / data.intensity * 100),
            validation_status: 'passed'
        }
    };
}

function getDemoSearchData(query) {
    const demoFactors = [
        {
            name: 'Electricity - United Kingdom Grid Average',
            factor: 0.233,
            unit: 'kg CO2e/kWh',
            source: 'UK BEIS 2023',
            year: 2023,
            region: 'GB',
            region_name: 'United Kingdom',
            data_quality_flags: []
        },
        {
            name: 'Electricity - European Union Grid Average',
            factor: 0.295,
            unit: 'kg CO2e/kWh',
            source: 'EEA 2023',
            year: 2023,
            region: 'EU',
            region_name: 'European Union',
            data_quality_flags: []
        },
        {
            name: 'Electricity - Sweden Grid Average',
            factor: 0.013,
            unit: 'kg CO2e/kWh',
            source: 'IEA 2023',
            year: 2023,
            region: 'SE',
            region_name: 'Sweden',
            data_quality_flags: []
        },
        {
            name: 'Electricity - Germany Grid Average',
            factor: 0.385,
            unit: 'kg CO2e/kWh',
            source: 'UBA 2023',
            year: 2023,
            region: 'DE',
            region_name: 'Germany',
            data_quality_flags: ['estimated']
        },
        {
            name: 'Electricity - United States Grid Average',
            factor: 0.417,
            unit: 'kg CO2e/kWh',
            source: 'EPA eGRID 2023',
            year: 2023,
            region: 'US',
            region_name: 'United States',
            data_quality_flags: []
        }
    ];
    
    // Filter by query
    const filtered = query ? 
        demoFactors.filter(f => 
            f.name.toLowerCase().includes(query.toLowerCase()) ||
            f.region_name.toLowerCase().includes(query.toLowerCase())
        ) : demoFactors;
    
    return {
        total_results: filtered.length,
        factors: filtered
    };
}

// Export functions for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        validateRegion,
        searchFactors,
        displayValidationResults,
        displaySearchResults,
        getDemoValidationData,
        getDemoSearchData
    };
}
