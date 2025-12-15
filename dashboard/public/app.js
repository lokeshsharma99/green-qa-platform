/**
 * Green QA Platform v2.0 - Enhanced Dashboard
 * Carbon-Aware Test Scheduling with Real-time APIs
 * 
 * Data Sources:
 * - UK Carbon Intensity API (free, no auth) - eu-west-2
 * - Carbon-Aware-Computing forecasts (free, CC0) - Europe
 * - Ember Climate data (embedded) - Global fallback
 * - EEA emission factors - Europe fallback
 */

// ============================================
// Configuration
// ============================================

// API Configuration - UPDATE THIS AFTER DEPLOYMENT
const API_CONFIG = {
    // Replace with your actual API URL from CloudFormation outputs
    baseUrl: window.ENV?.API_URL || 'https://YOUR-API-ID.execute-api.eu-west-2.amazonaws.com/Prod',
    endpoints: {
        optimal: '/optimal',
        regions: '/regions',
        current: '/current',
        calculate: '/calculate',
        history: '/history',
        storeResult: '/store_result'
    }
};

const CONFIG = {
    refreshInterval: 5 * 60 * 1000, // 5 minutes
    forecastHours: 48,
    animationDuration: 300,
    useRealData: true // Set to false to use sample data for testing
};

// Carbon intensity thresholds (AWS Data Center adjusted)
// These reflect AWS data center intensity (grid + renewable energy + PUE)
// NOT raw grid intensity - AWS renewables significantly reduce actual emissions
const THRESHOLDS = {
    VERY_LOW: 25,   // Excellent: Stockholm, Montreal, Paris, Oregon (0-25 gCO2/kWh)
    LOW: 75,        // Good: London, Ireland, California, most EU (25-75 gCO2/kWh)
    MODERATE: 150,  // Acceptable: Virginia, Ohio, Tokyo, Sydney (75-150 gCO2/kWh)
    HIGH: 300       // Poor: Mumbai, Singapore, coal-heavy regions (>150 gCO2/kWh)
};

// AWS Europe Data Centers
// Renewable energy data from: AWS Sustainability Report 2023 & AWS Customer Carbon Footprint Tool
// Source: https://sustainability.aboutamazon.com/products-services/the-cloud
const AWS_REGIONS = {
    'eu-north-1': { name: 'eu-north-1', location: 'Stockholm, Sweden', country: 'SE', flag: '🇸🇪', lat: 59.33, lon: 18.07, aws_renewable_pct: 0.98 },
    'eu-west-3': { name: 'eu-west-3', location: 'Paris, France', country: 'FR', flag: '🇫🇷', lat: 48.86, lon: 2.35, aws_renewable_pct: 0.75 },
    'eu-west-2': { name: 'eu-west-2', location: 'London, UK', country: 'GB', flag: '🇬🇧', lat: 51.51, lon: -0.13, aws_renewable_pct: 0.80 },
    'eu-west-1': { name: 'eu-west-1', location: 'Dublin, Ireland', country: 'IE', flag: '🇮🇪', lat: 53.35, lon: -6.26, aws_renewable_pct: 0.85 },
    'eu-central-1': { name: 'eu-central-1', location: 'Frankfurt, Germany', country: 'DE', flag: '🇩🇪', lat: 50.11, lon: 8.68, aws_renewable_pct: 0.75 },
    'eu-south-1': { name: 'eu-south-1', location: 'Milan, Italy', country: 'IT', flag: '🇮🇹', lat: 45.46, lon: 9.19, aws_renewable_pct: 0.70 },
    'eu-south-2': { name: 'eu-south-2', location: 'Aragon, Spain', country: 'ES', flag: '🇪🇸', lat: 41.65, lon: -0.89, aws_renewable_pct: 0.75 },
    'eu-central-2': { name: 'eu-central-2', location: 'Zurich, Switzerland', country: 'CH', flag: '🇨🇭', lat: 47.38, lon: 8.54, aws_renewable_pct: 0.85 }
};

// Ember Climate data (from grid-intensity-go)
const EMBER_DATA = {
    'SE': 30, 'NO': 20, 'FR': 60, 'CH': 50, 'FI': 100, 'AT': 120,
    'DK': 150, 'BE': 170, 'ES': 200, 'GB': 250, 'IT': 280, 'IE': 300,
    'NL': 350, 'DE': 380, 'PL': 600
};

// Cloud Carbon Footprint constants
// Sources and references for all values below
const CCF = {
    // Power Usage Effectiveness (PUE)
    // Source: https://www.cloudcarbonfootprint.org/docs/methodology/#power-usage-effectiveness-pue
    PUE: { 
        aws: 1.135,    // AWS Sustainability Report 2021
        gcp: 1.1,      // GCP average
        azure: 1.185   // Azure average
    },
    
    // vCPU Thermal Design Power (Watts)
    // Source: https://github.com/cloud-carbon-footprint/cloud-carbon-footprint/blob/trunk/packages/aws/src/lib/AWSInstanceTypes.ts
    // Based on Intel Xeon Scalable processors (most common in AWS)
    VCPU_TDP_WATTS: 10,
    
    // Memory power coefficient (kWh per GB-hour)
    // Source: https://www.cloudcarbonfootprint.org/docs/methodology/#memory
    // Research: https://github.com/etsy/cloud-jewels
    MEMORY_COEFF: 0.000392,
    
    // Embodied carbon per vCPU-hour (gCO2)
    // Sources:
    // - Teads: https://medium.com/teads-engineering/building-an-aws-ec2-carbon-emissions-dataset-3f0fd76c98ac
    // - Dell LCA: https://i.dell.com/sites/csdocuments/CorpComm_Docs/en/carbon-footprint-poweredge-r740.pdf
    EMBODIED_G_PER_VCPU_HOUR: 2.5
};

// ============================================
// Application State
// ============================================

const state = {
    regions: {},
    globalRegions: [],
    forecast: [],
    generationMix: null,
    lastUpdated: null,
    totalCarbonSaved: 0,
    testsOptimized: 0,
    liveSourceCount: 0,
    dataSources: new Set(),
    pipelineHistory: [],
    testHistory: [],
    // Pagination state
    pagination: {
        currentPage: 1,
        itemsPerPage: 10,
        totalItems: 0,
        totalPages: 0,
        filteredData: []
    }
};

// ============================================
// Map Variables (Global) - Fixed initialization order
// ============================================

let svg = null, projection = null, path = null, g = null, zoom = null;
let mapInitialized = false;

// No sample test data - use only real data from API or generated test files

// ============================================
// Real Data API Functions
// ============================================

async function loadPipelineHistory(limit = 50) {
    // First, try to use generated pipeline data (from test_e2e_dummy.py)
    if (typeof PIPELINE_HISTORY_DATA !== 'undefined' && PIPELINE_HISTORY_DATA.length > 0) {
        console.log(`✅ Loaded ${PIPELINE_HISTORY_DATA.length} pipeline entries from generated data`);
        return PIPELINE_HISTORY_DATA.slice(0, limit);
    }
    
    // Fallback to test history data if pipeline data not available
    if (typeof TEST_HISTORY_DATA !== 'undefined' && TEST_HISTORY_DATA.length > 0) {
        console.log(`✅ Loaded ${TEST_HISTORY_DATA.length} pipeline entries from test data`);
        return TEST_HISTORY_DATA.slice(0, limit);
    }
    
    // Try API if configured
    if (CONFIG.useRealData && !API_CONFIG.baseUrl.includes('YOUR-API-ID')) {
        try {
            const response = await fetch(`${API_CONFIG.baseUrl}${API_CONFIG.endpoints.history}?limit=${limit}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            console.log(`✅ Loaded ${data.pipelines?.length || data.tests?.length || 0} real pipeline executions from API`);
            return data.pipelines || data.tests || [];
        } catch (error) {
            console.error('❌ Error loading pipeline history:', error);
        }
    }
    
    // No fallback - return empty array to show proper empty state
    console.log('ℹ️ No pipeline history data available (API not configured)');
    return [];
}

function populatePipelineFilter(pipelines) {
    const pipelineFilter = document.getElementById('pipeline-filter');
    if (!pipelineFilter || !pipelines) return;
    
    // Get unique pipeline names
    const uniquePipelines = [...new Set(pipelines.map(p => 
        p.pipeline_name || p.test_suite || p.suite || 'Unknown'
    ))].sort();
    
    // Clear existing options except "All Pipelines"
    pipelineFilter.innerHTML = '<option value="all">All Pipelines</option>';
    
    // Add unique pipeline names
    uniquePipelines.forEach(pipelineName => {
        const option = document.createElement('option');
        option.value = pipelineName;
        option.textContent = pipelineName;
        pipelineFilter.appendChild(option);
    });
    
    console.log(`📋 Populated pipeline filter with ${uniquePipelines.length} unique pipelines`);
}

function calculateCarbonSavings(tests) {
    if (tests.length === 0) return { saved: 0, optimized: 0 };
    
    // Calculate what carbon would have been at highest intensity
    const regions = Object.values(state.regions);
    if (regions.length === 0) return { saved: 0, optimized: 0 };
    
    const maxIntensity = Math.max(...regions.map(r => r.intensity));
    
    let totalActual = 0;
    let totalPotential = 0;
    let optimizedCount = 0;
    
    tests.forEach(test => {
        const carbonG = test.carbon_g || test.carbon || 0;
        const intensity = test.carbon_intensity || test.intensity || maxIntensity;
        
        totalActual += carbonG;
        
        // Calculate what it would have been at max intensity
        const potentialCarbon = (carbonG / intensity) * maxIntensity;
        totalPotential += potentialCarbon;
        
        // Count as optimized if ran at <250 gCO2/kWh
        if (intensity < 250) {
            optimizedCount++;
        }
    });
    
    const saved = Math.round(totalPotential - totalActual);
    
    return {
        saved: saved > 0 ? saved : 0,
        optimized: optimizedCount
    };
}

// ============================================
// API Clients
// ============================================

const EmberAPI = {
    baseUrl: 'https://api.ember-energy.org/v1',
    apiKey: '270ca2d8-4b3c-c5dc-0156-ec804ef514e8',

    async getCarbonIntensity(countryCode) {
        try {
            const currentYear = new Date().getFullYear();
            const response = await fetch(
                `${this.baseUrl}/carbon-intensity/yearly?entity_code=${countryCode}&start_date=${currentYear - 1}&api_key=${this.apiKey}`
            );
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const result = await response.json();
            
            if (result.data && result.data.length > 0) {
                // Get most recent year's data
                const latest = result.data[result.data.length - 1];
                const intensity = Math.round(latest.emissions_intensity_gco2_per_kwh);
                console.log(`✅ Ember API: ${countryCode} = ${intensity} gCO₂/kWh (${latest.date})`);
                return {
                    intensity,
                    year: latest.date,
                    isRealtime: false,
                    source: 'Ember API'
                };
            }
            return null;
        } catch (error) {
            console.error(`❌ Ember API error for ${countryCode}:`, error);
            return null;
        }
    }
};

const ElectricityMapsAPI = {
    baseUrl: 'https://api.electricitymaps.com/v3',
    token: '7Cq9hfFAKl0gAtYNhvc2',

    async getCarbonIntensity(region) {
        try {
            const response = await fetch(
                `${this.baseUrl}/carbon-intensity/latest?dataCenterRegion=${region}&dataCenterProvider=aws`,
                { headers: { 'auth-token': this.token } }
            );
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            console.log(`✅ ElectricityMaps: ${region} = ${data.carbonIntensity} gCO₂/kWh`);
            return {
                intensity: Math.round(data.carbonIntensity),
                zone: data.zone,
                datetime: data.datetime,
                isEstimated: data.isEstimated,
                isRealtime: !data.isEstimated,
                source: data.isEstimated ? 'ElectricityMaps (estimated)' : 'ElectricityMaps'
            };
        } catch (error) {
            console.error(`❌ ElectricityMaps error for ${region}:`, error);
            return null;
        }
    },

    async getPowerBreakdown(region) {
        try {
            const response = await fetch(
                `${this.baseUrl}/power-breakdown/latest?dataCenterRegion=${region}&dataCenterProvider=aws`,
                { headers: { 'auth-token': this.token } }
            );
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            
            // Convert to percentage
            const total = Object.values(data.powerConsumptionBreakdown).reduce((sum, val) => sum + (val || 0), 0);
            const breakdown = Object.entries(data.powerConsumptionBreakdown)
                .filter(([_, val]) => val > 0)
                .map(([fuel, val]) => ({
                    fuel: fuel,
                    perc: (val / total) * 100
                }))
                .sort((a, b) => b.perc - a.perc);
            
            console.log(`✅ ElectricityMaps: Power breakdown for ${region}`);
            return breakdown;
        } catch (error) {
            console.error(`❌ ElectricityMaps power breakdown error for ${region}:`, error);
            return null;
        }
    },

    async getForecast24h(region) {
        try {
            const response = await fetch(
                `${this.baseUrl}/carbon-intensity/forecast?dataCenterRegion=${region}&dataCenterProvider=aws`,
                { headers: { 'auth-token': this.token } }
            );
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            
            // Convert to format similar to UK API
            const forecast = data.forecast.map(item => ({
                from: item.datetime,
                to: new Date(new Date(item.datetime).getTime() + 60 * 60 * 1000).toISOString(), // Add 1 hour
                intensity: Math.round(item.carbonIntensity),
                isEstimated: item.isEstimated || false
            }));
            
            console.log(`✅ ElectricityMaps: ${region} forecast = ${forecast.length} data points`);
            return forecast;
        } catch (error) {
            console.error(`❌ ElectricityMaps forecast error for ${region}:`, error);
            return null;
        }
    }
};

const UKCarbonAPI = {
    baseUrl: 'https://api.carbonintensity.org.uk',

    async getCurrentIntensity() {
        try {
            const response = await fetch(`${this.baseUrl}/intensity`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            const current = data.data[0];
            console.log('✅ UK Carbon API: Live data received');
            return {
                intensity: current.intensity.actual || current.intensity.forecast,
                index: current.intensity.index,
                from: current.from,
                to: current.to,
                isRealtime: true,
                source: 'UK National Grid ESO'
            };
        } catch (error) {
            console.error('❌ UK Carbon API error:', error);
            return null;
        }
    },

    async getForecast48h() {
        try {
            const now = new Date().toISOString().slice(0, 16) + 'Z';
            const response = await fetch(`${this.baseUrl}/intensity/${now}/fw48h`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            return data.data.map(item => ({
                from: item.from,
                to: item.to,
                intensity: item.intensity.forecast,
                index: item.intensity.index
            }));
        } catch (error) {
            console.error('❌ UK Carbon forecast error:', error);
            return [];
        }
    },

    async getGenerationMix() {
        try {
            const response = await fetch(`${this.baseUrl}/generation`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            
            // Debug: Log the actual response structure
            console.log('🔍 UK Generation API response:', JSON.stringify(data).substring(0, 200));
            
            // Validate response structure
            if (!data || !data.data) {
                console.error('❌ UK Generation mix: Missing data property', data);
                return null;
            }
            
            // Handle both array and object responses
            let generationData;
            if (Array.isArray(data.data)) {
                // Response is: { data: [{ generationmix: [...] }] }
                if (data.data.length === 0) {
                    console.error('❌ UK Generation mix: Empty data array');
                    return null;
                }
                generationData = data.data[0];
            } else if (typeof data.data === 'object') {
                // Response is: { data: { generationmix: [...] } }
                generationData = data.data;
            } else {
                console.error('❌ UK Generation mix: Unexpected data type', typeof data.data);
                return null;
            }
            
            if (!generationData || !generationData.generationmix) {
                console.error('❌ UK Generation mix: Missing generationmix property', generationData);
                return null;
            }
            
            console.log('✅ UK Generation mix: Loaded successfully');
            return generationData.generationmix;
        } catch (error) {
            console.error('❌ UK Generation mix error:', error);
            return null;
        }
    },

    async getCarbonFactors() {
        try {
            const response = await fetch(`${this.baseUrl}/intensity/factors`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            
            // Validate response structure
            if (!data || !data.data || !Array.isArray(data.data) || data.data.length === 0) {
                console.error('❌ UK Carbon factors: Invalid response structure', data);
                return null;
            }
            
            console.log('✅ UK Carbon Factors: Loaded fuel-specific emissions');
            return data.data[0];
        } catch (error) {
            console.error('❌ UK Carbon factors error:', error);
            return null;
        }
    }
};

// ============================================
// Helper Functions
// ============================================

function getIntensityClass(intensity) {
    if (intensity <= THRESHOLDS.VERY_LOW) return 'very-low';
    if (intensity <= THRESHOLDS.LOW) return 'low';
    if (intensity <= THRESHOLDS.MODERATE) return 'moderate';
    if (intensity <= THRESHOLDS.HIGH) return 'high';
    return 'very-high';
}

function getIntensityIndex(intensity) {
    if (intensity <= THRESHOLDS.VERY_LOW) return 'Very Low';
    if (intensity <= THRESHOLDS.LOW) return 'Low';
    if (intensity <= THRESHOLDS.MODERATE) return 'Moderate';
    if (intensity <= THRESHOLDS.HIGH) return 'High';
    return 'Very High';
}

function getIntensityColor(intensity) {
    if (intensity <= THRESHOLDS.VERY_LOW) return '#10b981';
    if (intensity <= THRESHOLDS.LOW) return '#22c55e';
    if (intensity <= THRESHOLDS.MODERATE) return '#eab308';
    if (intensity <= THRESHOLDS.HIGH) return '#f97316';
    return '#ef4444';
}

function formatTime(date) {
    return new Date(date).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
}

// ============================================
// UX Enhancement Functions
// ============================================

function getStatusBadge(intensity) {
    /**
     * Get user-friendly status badge for carbon intensity
     */
    if (intensity <= THRESHOLDS.VERY_LOW) {
        return { text: 'Excellent', icon: '🌟', class: 'excellent' };
    }
    if (intensity <= THRESHOLDS.LOW) {
        return { text: 'Good', icon: '✓', class: 'good' };
    }
    if (intensity <= THRESHOLDS.MODERATE) {
        return { text: 'Moderate', icon: '⚠', class: 'moderate' };
    }
    if (intensity <= THRESHOLDS.HIGH) {
        return { text: 'High', icon: '⚡', class: 'high' };
    }
    return { text: 'Very High', icon: '🔴', class: 'very-high' };
}

function getCarbonEquivalents(grams) {
    /**
     * Convert carbon grams to relatable real-world equivalents
     * Sources: EPA, DEFRA, scientific studies
     */
    return {
        // Transportation (EPA 2023 data)
        carKm: (grams / 180).toFixed(1),           // 1 km by average car = ~180g CO₂ (was 120g - too low)
        carMiles: (grams / 290).toFixed(1),        // 1 mile by average car = ~290g CO₂
        
        // Technology
        phoneCharges: Math.round(grams / 8),       // 1 smartphone charge = ~8g CO₂ ✓
        laptopHours: (grams / 50).toFixed(1),      // 1 hour laptop use = ~50g CO₂
        
        // Trees (USDA Forest Service data)
        treesYear: (grams / 21000).toFixed(2),     // 1 tree absorbs ~21kg CO₂/year (was inconsistent)
        treeDays: (grams / 58).toFixed(1),         // 1 tree absorbs ~58g CO₂/day ✓
        
        // Daily activities
        coffeeCups: Math.round(grams / 21),        // 1 cup of coffee = ~21g CO₂ ✓
        streamingHours: (grams / 36).toFixed(1),   // 1 hour HD streaming = ~36g CO₂ (was 55g - too high)
        
        // Energy
        ledBulbHours: Math.round(grams / 0.5),     // 1 hour LED bulb = ~0.5g CO₂ ✓
        kwh: (grams / 400).toFixed(2)              // 1 kWh electricity (UK grid avg) = ~400g CO₂
    };
}

function getTimeRecommendation(intensity, currentTime = new Date()) {
    /**
     * Get time-of-day recommendation based on carbon intensity
     */
    const hour = currentTime.getHours();
    
    if (intensity <= THRESHOLDS.VERY_LOW) {
        return {
            badge: '🌟 Perfect Time',
            class: 'excellent',
            message: 'Excellent carbon intensity right now!',
            action: 'Run tests now'
        };
    }
    
    if (intensity <= THRESHOLDS.LOW) {
        return {
            badge: '✓ Good Time',
            class: 'good',
            message: 'Good time to run tests',
            action: 'Run tests now'
        };
    }
    
    if (intensity <= THRESHOLDS.MODERATE) {
        return {
            badge: '⚠ Moderate',
            class: 'moderate',
            message: 'Acceptable carbon intensity',
            action: 'Consider waiting for better time'
        };
    }
    
    return {
        badge: '⚡ High Carbon',
        class: 'high',
        message: 'High carbon intensity',
        action: 'Wait or use different region'
    };
}

function createTooltipHTML(type, customExample = null) {
    /**
     * Generate tooltip HTML with title, content, breakdown, and example
     * Converts \n to <br> for proper line breaks in HTML
     */
    const info = getTooltipContent(type);
    let html = `
        <div class="tooltip">
            <div class="tooltip-title">${info.title}</div>
            <div class="tooltip-content">${info.content}</div>
    `;
    
    if (info.breakdown) {
        const breakdownHTML = info.breakdown.replace(/\n/g, '<br>');
        html += `<div class="tooltip-breakdown">${breakdownHTML}</div>`;
    }
    
    if (customExample || info.example) {
        const exampleHTML = (customExample || info.example).replace(/\n/g, '<br>');
        html += `<div class="tooltip-example">${exampleHTML}</div>`;
    }
    
    html += `</div>`;
    return html;
}

function getTooltipContent(type) {
    /**
     * Get educational tooltip content with calculation breakdowns
     */
    const tooltips = {
        'carbon-intensity': {
            title: 'Carbon Intensity',
            content: 'Grams of CO₂ emitted per kilowatt-hour (kWh) of electricity consumed.',
            breakdown: 'Grid Intensity measures how clean the electricity grid is at this moment.',
            example: '• 15 gCO₂/kWh = Very clean (wind, solar, hydro)\n• 150 gCO₂/kWh = Moderate (mixed sources)\n• 500 gCO₂/kWh = High (coal, gas)'
        },
        'renewable': {
            title: 'Renewable Energy %',
            content: 'Percentage of electricity from clean sources (solar, wind, hydro, nuclear).',
            breakdown: 'AWS purchases renewable energy to offset grid emissions. Higher % = lower carbon footprint.',
            example: '80% renewable means only 20% comes from fossil fuels'
        },
        'datacenter': {
            title: 'Data Center Carbon Intensity',
            content: 'Actual AWS data center carbon footprint after accounting for renewable energy and efficiency.',
            breakdown: 'Formula: Grid Intensity × (1 - Renewable %) × PUE\n\nPUE (Power Usage Effectiveness) = 1.135 for AWS',
            example: 'Grid: 66 gCO₂/kWh\nRenewable: 80%\nResult: 66 × 0.20 × 1.135 = 15 gCO₂/kWh'
        },
        'pue': {
            title: 'PUE (Power Usage Effectiveness)',
            content: 'Ratio of total data center energy to IT equipment energy. Lower is better.',
            breakdown: 'PUE = Total Facility Energy / IT Equipment Energy',
            example: 'AWS PUE: 1.135 (very efficient)\nTypical: 1.67\nPoor: 2.0+'
        },
        'gco2-kwh': {
            title: 'gCO₂/kWh',
            content: 'Grams of carbon dioxide per kilowatt-hour. The standard unit for measuring electricity carbon intensity.',
            breakdown: '1 kWh = running a 1000W device for 1 hour',
            example: '15 gCO₂/kWh = 15 grams of CO₂ per hour of 1000W usage'
        },
        'optimal-time': {
            title: 'Optimal Time',
            content: 'Best time in next 24 hours to run tests with lowest carbon emissions.',
            breakdown: 'Analyzes 48 half-hour forecast slots and recommends waiting only if savings ≥ 15% or (≥10% and wait < 3h)',
            example: 'Current: 20 gCO₂/kWh\nOptimal: 15 gCO₂/kWh at 23:00\nSavings: 25% → Worth waiting!'
        },
        'carbon-saved': {
            title: 'Carbon Saved',
            content: 'Total CO₂ emissions avoided by running tests at optimal times instead of high-carbon periods.',
            breakdown: 'Savings = (High Intensity - Actual Intensity) × Energy Used',
            example: 'If you used 1 kWh at 15 gCO₂/kWh instead of 150 gCO₂/kWh:\nSavings = (150 - 15) × 1 = 135g CO₂'
        },
        'potential-savings': {
            title: 'Potential Savings',
            content: 'How much cleaner the current best region is compared to the worst region.',
            breakdown: 'Savings % = (Highest - Lowest) / Highest × 100',
            example: 'Highest: 250 gCO₂/kWh\nLowest: 15 gCO₂/kWh\nSavings: (250-15)/250 = 94%'
        },
        'low-carbon-regions': {
            title: 'Low Carbon Regions',
            content: 'Regions with carbon intensity ≤ 75 gCO₂/kWh (after accounting for AWS renewable energy).',
            breakdown: 'Thresholds:\n• Very Low: ≤ 25\n• Low: ≤ 75\n• Moderate: ≤ 150\n• High: > 150',
            example: '4/8 regions = 50% of regions are low carbon right now'
        },
        'average-intensity': {
            title: 'Average Intensity',
            content: 'Mean carbon intensity across all monitored regions.',
            breakdown: 'Average = Sum of all intensities / Number of regions',
            example: 'Regions: 15, 20, 150, 200\nAverage: (15+20+150+200)/4 = 96.25'
        },
        'status-badge': {
            title: 'Status Badges',
            content: 'Quick visual indicator of carbon intensity level.',
            breakdown: '⭐ Excellent: ≤ 25 gCO₂/kWh\n✓ Good: ≤ 75 gCO₂/kWh\n⚠ Moderate: ≤ 150 gCO₂/kWh\n⚡ High: > 150 gCO₂/kWh',
            example: 'Use Excellent/Good regions for best environmental impact'
        },
        'embodied-carbon': {
            title: 'Embodied Carbon',
            content: 'CO₂ emissions from manufacturing, transporting, and disposing of hardware.',
            breakdown: 'Amortized over hardware lifetime (typically 4 years for servers)',
            example: 'Server manufacturing: ~1000 kg CO₂\nPer hour: ~0.03g CO₂/vCPU-hour'
        },
        'vcpu': {
            title: 'vCPU (Virtual CPU)',
            content: 'Virtual processor core allocated to your compute instance.',
            breakdown: 'Each vCPU consumes ~3.5W average power (TDP)',
            example: '4 vCPUs running 1 hour = 4 × 3.5W × 1h = 14Wh = 0.014 kWh'
        },
        'memory-power': {
            title: 'Memory Power Consumption',
            content: 'RAM consumes electricity even when idle.',
            breakdown: 'Coefficient: 0.000392 kWh per GB per hour',
            example: '16 GB RAM for 1 hour = 16 × 0.000392 = 0.00627 kWh'
        }
    };
    
    return tooltips[type] || { title: 'Info', content: 'Learn more about carbon-aware computing' };
}

function formatDateTime(date) {
    return new Date(date).toLocaleString('en-GB', {
        day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'
    });
}

function addVariation(value, percent = 10) {
    const variation = (Math.random() - 0.5) * 2 * (percent / 100);
    return Math.round(value * (1 + variation));
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// ============================================
// Carbon Calculations (GSF SCI + CCF)
// ============================================

function calculateCarbon(durationMinutes, vcpuCount, memoryGb, intensity, provider = 'aws') {
    const durationHours = durationMinutes / 60;
    const pue = CCF.PUE[provider] || 1.135;
    
    // Compute energy (kWh)
    const computeKwh = (vcpuCount * CCF.VCPU_TDP_WATTS * durationHours) / 1000;
    const memoryKwh = memoryGb * durationHours * CCF.MEMORY_COEFF;
    const totalEnergyKwh = (computeKwh + memoryKwh) * pue;
    
    // Embodied carbon
    const embodiedG = vcpuCount * durationHours * CCF.EMBODIED_G_PER_VCPU_HOUR;
    
    // Operational carbon
    const operationalG = totalEnergyKwh * intensity;
    
    // Total (SCI formula)
    const totalG = operationalG + embodiedG;
    
    return {
        energyKwh: totalEnergyKwh,
        operationalG,
        embodiedG,
        totalG,
        sci: totalG
    };
}

// ============================================
// Data Loading
// ============================================

// Embedded global regions data is loaded from global-regions-data.js
// This allows the dashboard to work with file:// protocol (no web server needed)

async function loadGlobalRegions() {
    console.log('🌍 Loading global AWS regions...');
    
    // Try to load from API first
    if (CONFIG.useRealData && !API_CONFIG.baseUrl.includes('YOUR-API-ID')) {
        try {
            const response = await fetch(`${API_CONFIG.baseUrl}/global-regions`);
            if (response.ok) {
                const data = await response.json();
                console.log(`✅ Loaded ${data.regions.length} global regions from API`);
                return data.regions;
            }
        } catch (error) {
            console.error('❌ Error loading global regions from API:', error);
        }
    }
    
    // Try embedded data first (works with file:// protocol)
    if (EMBEDDED_GLOBAL_REGIONS && EMBEDDED_GLOBAL_REGIONS.length > 0) {
        console.log(`✅ Loaded ${EMBEDDED_GLOBAL_REGIONS.length} global regions from embedded data`);
        return EMBEDDED_GLOBAL_REGIONS;
    }
    
    // Try to load from static JSON file (only works with http:// or https://)
    try {
        const response = await fetch('global-regions.json');
        if (response.ok) {
            const data = await response.json();
            console.log(`✅ Loaded ${data.regions.length} global regions from static file`);
            return data.regions;
        }
    } catch (error) {
        console.error('❌ Error loading global regions from file:', error);
    }
    
    // Final fallback: return empty array
    console.log('ℹ️ No global regions data available');
    return [];
}

function syncEuropeDataToGlobal(globalRegions) {
    /**
     * Sync Europe data to global regions for consistency
     * This ensures Europe section and Worldwide section show the same values
     */
    if (!state.regions || !globalRegions) {
        console.log('⚠️ Sync skipped: missing data', { 
            hasRegions: !!state.regions, 
            hasGlobal: !!globalRegions 
        });
        return;
    }
    
    let syncCount = 0;
    
    console.log('🔄 Starting sync...', {
        europeRegions: Object.keys(state.regions).length,
        globalRegions: globalRegions.length
    });
    
    // For each Europe region, sync to global (regardless of isRealtime flag)
    for (const [regionId, europeData] of Object.entries(state.regions)) {
        // Find matching region in global data
        const globalRegion = globalRegions.find(r => r.region_code === regionId);
        
        if (globalRegion) {
            // Update global region with Europe data
            globalRegion.grid_intensity = europeData.grid_intensity || europeData.intensity;
            globalRegion.datacenter_intensity = europeData.datacenter_intensity || europeData.intensity;
            globalRegion.isRealtime = europeData.isRealtime || false;
            globalRegion.source = europeData.source;
            syncCount++;
            
            console.log(`🔄 Synced ${regionId}: ${globalRegion.datacenter_intensity.toFixed(1)} gCO₂/kWh (${europeData.source})`);
        } else {
            console.log(`⚠️ No global region found for ${regionId}`);
        }
    }
    
    if (syncCount > 0) {
        console.log(`✅ Synced ${syncCount} regions with real-time data`);
    }
}

async function loadAllRegionData() {
    state.liveSourceCount = 0;
    state.dataSources = new Set();
    console.log('🌍 Loading Europe AWS carbon data...');
    
    // Try to use global regions data for consistency
    const globalRegionsMap = {};
    if (EMBEDDED_GLOBAL_REGIONS && EMBEDDED_GLOBAL_REGIONS.length > 0) {
        EMBEDDED_GLOBAL_REGIONS.forEach(region => {
            globalRegionsMap[region.region_code] = region;
        });
        console.log(`✅ Using global regions data for Europe (${Object.keys(globalRegionsMap).length} regions)`);
    }
    
    for (const [regionId, regionConfig] of Object.entries(AWS_REGIONS)) {
        let data = null;
        
        // FIRST: For UK (eu-west-2), prioritize real-time UK Grid ESO data
        if (regionId === 'eu-west-2') {
            const ukForecast = await UKCarbonAPI.getForecast48h();
            const ukMix = await UKCarbonAPI.getGenerationMix();
            
            if (ukForecast.length > 0) {
                state.forecast = ukForecast;
                state.dataSources.add('UK Grid ESO');
                
                // Update optimal time chart with new forecast data
                const selectedRegion = document.getElementById('optimal-time-region-select')?.value || 'eu-west-2';
                renderOptimalTimeChart(selectedRegion);
                
                // Use UK Grid ESO real-time data for eu-west-2
                const gridIntensity = ukForecast[0].intensity;
                const renewablePct = regionConfig.aws_renewable_pct || 0.80;
                const datacenterIntensity = Math.round(gridIntensity * (1 - renewablePct) * 1.135 * 10) / 10;
                
                data = {
                    intensity: datacenterIntensity,
                    grid_intensity: gridIntensity,
                    datacenter_intensity: datacenterIntensity,
                    index: ukForecast[0].index || getIntensityIndex(datacenterIntensity),
                    isRealtime: true,
                    source: 'UK National Grid ESO'
                };
            }
            
            if (ukMix) {
                state.generationMix = ukMix;
            }
        }
        
        // SECOND: Try ElectricityMaps for real-time data
        if (!data) {
            const emData = await ElectricityMapsAPI.getCarbonIntensity(regionId);
            if (emData) {
                // ElectricityMaps with dataCenterProvider=aws returns datacenter intensity
                data = {
                    ...emData,
                    datacenter_intensity: emData.intensity,
                    grid_intensity: Math.round(emData.intensity / ((1 - (regionConfig.aws_renewable_pct || 0.70)) * 1.135))
                };
                state.dataSources.add(emData.isRealtime ? 'ElectricityMaps' : 'ElectricityMaps (est)');
                
                if (!emData.isRealtime) {
                    console.log(`ℹ️ ElectricityMaps: ${regionId} using estimated data (TEST MODE token)`);
                }
            }
        }
        
        // THIRD: Use global regions data as fallback (pre-calculated, not real-time)
        if (!data && globalRegionsMap[regionId]) {
            const globalData = globalRegionsMap[regionId];
            data = {
                intensity: globalData.datacenter_intensity,
                grid_intensity: globalData.grid_intensity,
                datacenter_intensity: globalData.datacenter_intensity,
                index: getIntensityIndex(globalData.datacenter_intensity),
                isRealtime: false,
                source: 'AWS Global Carbon Optimizer'
            };
            state.dataSources.add('AWS Global Optimizer');
        }
        
        // Try Ember API if ElectricityMaps failed
        if (!data) {
            const emberData = await EmberAPI.getCarbonIntensity(regionConfig.country);
            if (emberData) {
                data = {
                    intensity: emberData.intensity,
                    index: getIntensityIndex(emberData.intensity),
                    isRealtime: false,
                    source: `Ember API (${emberData.year})`
                };
                state.dataSources.add('Ember API');
            }
        }
        
        // Use static Ember fallback if API failed
        if (!data) {
            const emberValue = EMBER_DATA[regionConfig.country];
            if (emberValue) {
                console.log(`⚠️ Using static Ember data for ${regionConfig.country}`);
                data = {
                    intensity: addVariation(emberValue, 15),
                    index: getIntensityIndex(emberValue),
                    isRealtime: false,
                    source: 'Ember Climate (static)'
                };
                state.dataSources.add('Ember Static');
            }
        }
        
        // Final fallback
        if (!data) {
            data = {
                intensity: 300,
                index: 'Moderate',
                isRealtime: false,
                source: 'Fallback'
            };
        }
        
        if (data.isRealtime) state.liveSourceCount++;
        
        // Ensure we have both grid and datacenter intensity
        let gridIntensity = data.grid_intensity || data.intensity;
        let datacenterIntensity = data.datacenter_intensity;
        
        // If datacenter intensity not provided, calculate it
        if (!datacenterIntensity) {
            const renewablePct = regionConfig.aws_renewable_pct || 0.70;
            const PUE = 1.135;
            datacenterIntensity = Math.round(gridIntensity * (1 - renewablePct) * PUE * 10) / 10;
        }
        
        // If grid intensity not provided, reverse-calculate it
        if (!data.grid_intensity && datacenterIntensity) {
            const renewablePct = regionConfig.aws_renewable_pct || 0.70;
            const PUE = 1.135;
            gridIntensity = Math.round(datacenterIntensity / ((1 - renewablePct) * PUE));
        }
        
        state.regions[regionId] = {
            ...regionConfig,
            ...data,
            grid_intensity: gridIntensity, // Store original grid intensity
            datacenter_intensity: datacenterIntensity, // AWS-specific intensity
            intensity: datacenterIntensity // Use datacenter intensity for display
        };
    }
    
    state.lastUpdated = new Date();
    // Remove mock data - calculate from real pipeline history
    const tests = await loadPipelineHistory();
    const savings = calculateCarbonSavings(tests);
    state.totalCarbonSaved = savings.saved;
    state.testsOptimized = savings.optimized;
    
    // Update sources display
    updateSourcesDisplay();
}

// ============================================
// UI Rendering
// ============================================

function updateSourcesDisplay() {
    const sourcesEl = document.getElementById('sources-list');
    if (!sourcesEl) return;
    
    const sources = Array.from(state.dataSources);
    if (sources.length === 0) {
        sourcesEl.textContent = 'Loading...';
        return;
    }
    
    sourcesEl.textContent = sources.join(', ');
}

function updateSummaryCards() {
    const regions = Object.values(state.regions);
    if (regions.length === 0) return;
    
    const lowest = regions.reduce((min, r) => r.intensity < min.intensity ? r : min);
    const highest = regions.reduce((max, r) => r.intensity > max.intensity ? r : max);
    const avgIntensity = (regions.reduce((sum, r) => sum + r.intensity, 0) / regions.length).toFixed(1);
    const lowCarbonCount = regions.filter(r => r.intensity <= THRESHOLDS.LOW).length;
    
    // Update Impact Summary
    updateImpactSummary();
    
    // Status
    document.getElementById('live-count').textContent = `${state.liveSourceCount} live`;
    document.getElementById('last-updated-time').textContent = formatTime(state.lastUpdated);
    
    // Update insights
    updateInsights(lowest, highest, avgIntensity, lowCarbonCount, regions.length);
}

async function updateImpactSummary() {
    // Load actual pipeline history to calculate real savings
    const tests = await loadPipelineHistory();
    
    if (tests.length === 0) {
        // No test data available - show empty state
        const monthlySavedEl = document.getElementById('monthly-carbon-saved');
        const drivingEl = document.getElementById('equivalent-driving');
        const treesEl = document.getElementById('equivalent-trees');
        
        if (monthlySavedEl) monthlySavedEl.textContent = 'No data yet';
        if (drivingEl) drivingEl.textContent = 'Run tests to see impact';
        if (treesEl) treesEl.textContent = 'No data yet';
        return;
    }
    
    // Calculate actual savings from test history
    const savings = calculateCarbonSavings(tests);
    const monthlySavingsG = savings.saved;
    const monthlySavingsKg = (monthlySavingsG / 1000).toFixed(1);
    
    // Update main savings display
    const monthlySavedEl = document.getElementById('monthly-carbon-saved');
    if (monthlySavedEl) {
        if (monthlySavingsG > 0) {
            monthlySavedEl.textContent = `${monthlySavingsKg}kg of CO₂`;
        } else {
            monthlySavedEl.textContent = 'No savings yet';
        }
    }
    
    // Calculate real-world equivalents only if there are savings
    if (monthlySavingsG > 0) {
        const equivalents = getCarbonEquivalents(monthlySavingsG);
        
        // Update driving equivalent
        const drivingEl = document.getElementById('equivalent-driving');
        if (drivingEl) {
            drivingEl.textContent = `${Math.round(parseFloat(equivalents.carKm))} km`;
        }
        
        // Update trees equivalent
        const treesEl = document.getElementById('equivalent-trees');
        if (treesEl) {
            // Trees absorb about 21kg CO₂ per year
            // For monthly savings, calculate how many trees would absorb this amount in a year
            const treesNeeded = monthlySavingsG / 21000; // grams to kg conversion
            
            if (treesNeeded < 0.1) {
                treesEl.textContent = `${Math.round(treesNeeded * 365)} tree-days`;
            } else if (treesNeeded < 1) {
                treesEl.textContent = `${treesNeeded.toFixed(1)} trees`;
            } else {
                treesEl.textContent = `${Math.round(treesNeeded)} trees`;
            }
        }
    } else {
        // No savings yet
        const drivingEl = document.getElementById('equivalent-driving');
        const treesEl = document.getElementById('equivalent-trees');
        
        if (drivingEl) drivingEl.textContent = 'Run optimized tests to see impact';
        if (treesEl) treesEl.textContent = 'No savings yet';
    }
}

function updateInsights(lowest, highest, avgIntensity, lowCarbonCount, totalRegions) {
    // Update the new combined region optimizer
    updateRegionComparison();
    
    // Removed elements - no longer updating:
    // - insight-best-region (now part of region optimizer)
    // - insight-savings (now part of region optimizer)
    // - insight-low-count (Low Carbon Regions card removed)
    // - insight-avg (Average Intensity card removed)
}

function updateRegionComparison() {
    const regionSelect = document.getElementById('comparison-region-select');
    const currentIntensityEl = document.getElementById('current-region-intensity');
    const bestRegionNameEl = document.getElementById('best-region-name');
    const bestRegionFlagEl = document.getElementById('best-region-flag');
    const bestIntensityEl = document.getElementById('best-region-intensity');
    const savingsPercentageEl = document.getElementById('savings-percentage');
    const savingsExplanationEl = document.getElementById('savings-explanation');
    const savingsBadgeEl = document.getElementById('savings-badge');
    
    if (!regionSelect) return;
    
    const selectedRegionCode = regionSelect.value;
    const regions = Object.values(state.regions);
    
    if (regions.length === 0) {
        if (currentIntensityEl) currentIntensityEl.textContent = 'Loading...';
        if (bestRegionNameEl) bestRegionNameEl.textContent = 'Loading...';
        if (bestIntensityEl) bestIntensityEl.textContent = 'Loading...';
        if (savingsPercentageEl) savingsPercentageEl.textContent = 'Loading...';
        if (savingsExplanationEl) savingsExplanationEl.textContent = 'Loading region comparison data...';
        return;
    }
    
    // Find the selected region and the best (lowest intensity) region
    const selectedRegion = regions.find(r => r.name === selectedRegionCode);
    const bestRegion = regions.reduce((min, r) => r.intensity < min.intensity ? r : min);
    
    if (!selectedRegion) return;
    
    // Update current region display
    if (currentIntensityEl) {
        currentIntensityEl.textContent = Math.round(selectedRegion.intensity);
    }
    
    // Update best region display
    if (bestRegionNameEl) {
        bestRegionNameEl.textContent = bestRegion.name;
    }
    if (bestIntensityEl) {
        bestIntensityEl.textContent = Math.round(bestRegion.intensity);
    }
    
    // Calculate and display savings
    const savingsPercent = Math.round(((selectedRegion.intensity - bestRegion.intensity) / selectedRegion.intensity) * 100);
    
    if (savingsPercent <= 0) {
        // Already optimal
        if (savingsPercentageEl) savingsPercentageEl.textContent = '0%';
        if (savingsExplanationEl) {
            savingsExplanationEl.textContent = `${selectedRegion.name} is already the cleanest option available!`;
        }
        if (savingsBadgeEl) {
            savingsBadgeEl.innerHTML = `
                <span class="savings-text">
                    <strong>Already optimal</strong> - cleanest region
                </span>
            `;
        }
    } else {
        // Show potential savings
        if (savingsPercentageEl) savingsPercentageEl.textContent = `${savingsPercent}%`;
        if (savingsExplanationEl) {
            savingsExplanationEl.textContent = `By switching from ${selectedRegion.name} to ${bestRegion.name}, you could reduce your environmental impact by ${savingsPercent}%`;
        }
        if (savingsBadgeEl) {
            savingsBadgeEl.innerHTML = `
                <span class="savings-text">
                    <strong>${savingsPercent}%</strong> less carbon emissions
                </span>
            `;
        }
    }
}

// Legacy function for backward compatibility
function updatePotentialSavings() {
    updateRegionComparison();
}



function renderRegionGrid() {
    const grid = document.getElementById('region-grid');
    grid.innerHTML = '';
    
    const sortedRegions = Object.values(state.regions).sort((a, b) => a.intensity - b.intensity);
    
    for (const region of sortedRegions) {
        const intensityClass = getIntensityClass(region.intensity);
        const renewablePct = region.aws_renewable_pct ? Math.round(region.aws_renewable_pct * 100) : null;
        // Show one decimal place for precision
        const intensityDisplay = typeof region.intensity === 'number' ? region.intensity.toFixed(1) : region.intensity;
        
        // Get status badge and time recommendation
        const statusBadge = getStatusBadge(region.intensity);
        const timeRec = getTimeRecommendation(region.intensity);
        
        const item = document.createElement('div');
        item.className = 'region-item';
        item.innerHTML = `
            <div class="region-info">
                <div class="region-name">${region.name}</div>
                <div class="region-location">${region.location}</div>
            </div>
            <div class="region-intensity">
                <div class="region-value ${intensityClass}">${intensityDisplay}</div>
                <div class="region-unit">
                    gCO₂/kWh
                    <span class="tooltip-trigger">
                        <span class="info-icon">i</span>
                        ${createTooltipHTML('gco2-kwh', `${intensityDisplay} gCO₂/kWh = ${statusBadge.text}`)}
                    </span>
                </div>
            </div>
            <span class="status-badge ${statusBadge.class}">${statusBadge.icon} ${statusBadge.text}</span>
            ${renewablePct !== null ? `
            <div class="region-renewable">
                <img src="renewable-energy-power-svgrepo-com.svg" alt="Renewable Energy" class="renewable-icon" width="12" height="12">
                <span>${renewablePct}% renewable</span>
            </div>
            ` : ''}
        `;
        
        // Make clickable
        item.addEventListener('click', () => openRegionModal(region));
        
        grid.appendChild(item);
    }
}

function renderGlobalRegionGrid(regions) {
    const grid = document.getElementById('global-region-grid');
    if (!grid) return;
    
    grid.innerHTML = '';
    
    if (!regions || regions.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1 / -1; padding: 40px; text-align: center; color: var(--grey-500);">
                <div style="font-size: 16px; margin-bottom: 8px;">Loading global regions...</div>
                <div style="font-size: 14px;">Fetching data from 28 AWS regions worldwide</div>
            </div>
        `;
        return;
    }
    
    // Sort by datacenter intensity
    const sortedRegions = [...regions].sort((a, b) => a.datacenter_intensity - b.datacenter_intensity);
    
    for (const region of sortedRegions) {
        // Show decimal value (1 decimal place)
        const intensity = region.datacenter_intensity.toFixed(1);
        const intensityClass = getIntensityClass(region.datacenter_intensity);
        const renewablePct = Math.round(region.aws_renewable_pct * 100);
        
        // Get status badge
        const statusBadge = getStatusBadge(region.datacenter_intensity);
        
        const item = document.createElement('div');
        item.className = 'global-region-item';
        item.innerHTML = `
            <div class="global-region-header">
                <div class="global-region-info">
                    <div class="global-region-code">${region.region_code}</div>
                    <div class="global-region-location" title="${region.location}">${region.location}</div>
                </div>
                <div class="global-region-intensity-value ${intensityClass}">${intensity}</div>
            </div>
            <span class="status-badge ${statusBadge.class}" style="margin: 4px 0;">${statusBadge.icon} ${statusBadge.text}</span>
            <div class="global-region-footer">
                <div class="global-region-renewable">
                    <img src="renewable-energy-power-svgrepo-com.svg" alt="Renewable Energy" class="renewable-icon" width="12" height="12">
                    <span>${renewablePct}%</span>
                </div>
                <div class="global-region-unit">gCO₂/kWh</div>
            </div>
        `;
        
        // Make clickable
        item.addEventListener('click', () => openGlobalRegionModal(region));
        
        grid.appendChild(item);
    }
    
    console.log(`✅ Rendered ${sortedRegions.length} global regions`);
}

// ============================================
// Enhanced Test History Analytics
// ============================================

function calculateHistoryMetrics(tests) {
    if (!tests || tests.length === 0) {
        return {
            baseline: { carbon: 0, commits: 0 },
            latest: { carbon: 0, commits: 0 },
            trend: { direction: 'stable', change: 0 },
            regressions: 0
        };
    }
    
    // Sort tests by timestamp
    const sortedTests = tests.sort((a, b) => new Date(a.timestamp || a.time) - new Date(b.timestamp || b.time));
    
    // Calculate baseline (first 5 tests average)
    const baselineTests = sortedTests.slice(0, Math.min(5, sortedTests.length));
    const baselineCarbon = baselineTests.reduce((sum, test) => sum + (test.carbon_g || test.carbon || 0), 0) / baselineTests.length;
    
    // Latest test
    const latestTest = sortedTests[sortedTests.length - 1];
    const latestCarbon = latestTest.carbon_g || latestTest.carbon || 0;
    
    // Trend calculation (last 5 vs previous 5)
    const recentTests = sortedTests.slice(-5);
    const previousTests = sortedTests.slice(-10, -5);
    
    const recentAvg = recentTests.reduce((sum, test) => sum + (test.carbon_g || test.carbon || 0), 0) / recentTests.length;
    const previousAvg = previousTests.length > 0 
        ? previousTests.reduce((sum, test) => sum + (test.carbon_g || test.carbon || 0), 0) / previousTests.length
        : baselineCarbon;
    
    const trendChange = recentAvg - previousAvg;
    const trendDirection = Math.abs(trendChange) < 5 ? 'stable' : (trendChange < 0 ? 'improving' : 'degrading');
    
    // Count regressions (tests significantly above baseline)
    const regressionThreshold = baselineCarbon * 1.2; // 20% above baseline
    const regressions = sortedTests.filter(test => {
        const carbon = test.carbon_g || test.carbon || 0;
        return carbon > regressionThreshold;
    }).length;
    
    console.log(`📊 Metrics calculated for ${sortedTests.length} pipelines: baseline=${baselineCarbon.toFixed(2)}mg, regressions=${regressions} (threshold=${regressionThreshold.toFixed(2)}mg)`);
    
    return {
        baseline: { carbon: baselineCarbon, commits: baselineTests.length },
        latest: { carbon: latestCarbon, commits: 1 },
        trend: { direction: trendDirection, change: trendChange },
        regressions
    };
}

function renderHistoryMetrics(pipelines) {
    const metrics = calculateHistoryMetrics(pipelines);
    
    // Update baseline
    const baselineEl = document.getElementById('baseline-carbon');
    const baselineCommitsEl = document.getElementById('baseline-commits');
    if (baselineEl) baselineEl.textContent = `${metrics.baseline.carbon.toFixed(1)} mg`;
    if (baselineCommitsEl) baselineCommitsEl.textContent = `${metrics.baseline.commits} pipelines`;
    
    // Update latest
    const latestEl = document.getElementById('latest-carbon');
    const latestCommitsEl = document.getElementById('latest-commits');
    if (latestEl) latestEl.textContent = `${metrics.latest.carbon.toFixed(1)} mg`;
    if (latestCommitsEl) latestCommitsEl.textContent = `${metrics.latest.commits} pipelines`;
    
    // Update trend
    const trendEl = document.getElementById('trend-direction');
    const trendChangeEl = document.getElementById('trend-change');
    if (trendEl) {
        trendEl.textContent = metrics.trend.direction === 'improving' ? 'Improving' : 
                             metrics.trend.direction === 'degrading' ? 'Degrading' : 'Stable';
        trendEl.className = `metric-value trend ${metrics.trend.direction}`;
    }
    if (trendChangeEl) {
        const changeText = metrics.trend.change >= 0 ? `+${metrics.trend.change.toFixed(1)}` : metrics.trend.change.toFixed(1);
        trendChangeEl.textContent = `${changeText} mg/pipeline`;
    }
    
    // Update regressions with visual warning
    const regressionsEl = document.getElementById('regressions-count');
    if (regressionsEl) {
        regressionsEl.textContent = metrics.regressions.toString();
        
        // Add visual warning styling for regressions
        const regressionCard = regressionsEl.closest('.metric-card');
        if (regressionCard) {
            if (metrics.regressions > 0) {
                regressionCard.classList.add('has-regressions');
                regressionCard.title = `${metrics.regressions} pipeline${metrics.regressions > 1 ? 's' : ''} with carbon emissions >20% above baseline`;
            } else {
                regressionCard.classList.remove('has-regressions');
                regressionCard.title = 'No carbon regressions detected';
            }
        }
    }
}

function renderTrendChart(tests, pipelineFilter = 'all') {
    const canvas = document.getElementById('trend-canvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // Filter tests by pipeline if specified
    let filteredTests = tests || [];
    if (pipelineFilter && pipelineFilter !== 'all') {
        filteredTests = filteredTests.filter(test => 
            (test.pipeline_name || test.test_suite || test.suite || 'Unknown') === pipelineFilter
        );
    }
    
    if (filteredTests.length === 0) {
        // Show empty state
        ctx.clearRect(0, 0, width, height);
        ctx.fillStyle = '#f8fafc';
        ctx.fillRect(0, 0, width, height);
        
        ctx.fillStyle = '#9ca3af';
        ctx.font = '14px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(pipelineFilter !== 'all' ? `No data for ${pipelineFilter}` : 'No pipeline data available', width / 2, height / 2);
        return;
    }
    
    // Better use of horizontal space - reduce padding for more chart area
    const padding = { top: 40, right: 40, bottom: 50, left: 70 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    // Clear canvas with white background
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, width, height);
    
    // Use more data points for better trend analysis (last 20 tests)
    const recentTests = filteredTests.slice(-20);
    const carbonValues = recentTests.map(test => test.carbon_g || test.carbon || 0);
    const maxCarbon = Math.max(...carbonValues);
    const minCarbon = Math.min(...carbonValues);
    const range = Math.max(maxCarbon - minCarbon, 0.5);
    
    // Add some padding to the range for better visualization
    const paddedMin = minCarbon - range * 0.1;
    const paddedMax = maxCarbon + range * 0.1;
    const paddedRange = paddedMax - paddedMin;
    
    // Calculate baseline from FILTERED data (not all tests)
    const baselineData = filteredTests.length >= 5 ? filteredTests.slice(0, 5) : filteredTests;
    const baseline = baselineData.length > 0 ? 
        baselineData.reduce((sum, test) => sum + (test.carbon_g || test.carbon || 0), 0) / baselineData.length : 0;
    
    // Draw subtle grid lines
    ctx.strokeStyle = '#f1f5f9';
    ctx.lineWidth = 1;
    
    // Horizontal grid lines
    for (let i = 0; i <= 4; i++) {
        const y = padding.top + (chartHeight / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(padding.left + chartWidth, y);
        ctx.stroke();
    }
    
    // Vertical grid lines
    for (let i = 0; i <= 6; i++) {
        const x = padding.left + (chartWidth / 6) * i;
        ctx.beginPath();
        ctx.moveTo(x, padding.top);
        ctx.lineTo(x, padding.top + chartHeight);
        ctx.stroke();
    }
    
    // Draw Y-axis labels
    ctx.fillStyle = '#64748b';
    ctx.font = '11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    
    for (let i = 0; i <= 4; i++) {
        const y = padding.top + (chartHeight / 4) * i;
        const value = paddedMax - (paddedRange / 4) * i;
        ctx.fillText(value.toFixed(1), padding.left - 10, y);
    }
    
    // Draw X-axis labels (time indicators)
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    
    recentTests.forEach((test, index) => {
        if (index % 2 === 0) { // Show every other label to avoid crowding
            const x = padding.left + (index / (recentTests.length - 1)) * chartWidth;
            const timestamp = new Date(test.timestamp || test.time);
            const timeLabel = timestamp.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            ctx.fillText(timeLabel, x, padding.top + chartHeight + 10);
        }
    });
    
    // Draw baseline line with subtle styling
    const baselineY = padding.top + chartHeight - ((baseline - paddedMin) / paddedRange) * chartHeight;
    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 1;
    ctx.setLineDash([8, 4]);
    ctx.beginPath();
    ctx.moveTo(padding.left, baselineY);
    ctx.lineTo(padding.left + chartWidth, baselineY);
    ctx.stroke();
    ctx.setLineDash([]);
    
    // Draw baseline label
    ctx.fillStyle = '#64748b';
    ctx.font = '10px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'bottom';
    ctx.fillText('Baseline', padding.left + 5, baselineY - 5);
    
    // Create gradient for area under curve
    const gradient = ctx.createLinearGradient(0, padding.top, 0, padding.top + chartHeight);
    gradient.addColorStop(0, 'rgba(16, 185, 129, 0.1)');
    gradient.addColorStop(1, 'rgba(16, 185, 129, 0.02)');
    
    // Draw area under curve
    ctx.fillStyle = gradient;
    ctx.beginPath();
    
    recentTests.forEach((test, index) => {
        const x = padding.left + (index / (recentTests.length - 1)) * chartWidth;
        const carbon = test.carbon_g || test.carbon || 0;
        const y = padding.top + chartHeight - ((carbon - paddedMin) / paddedRange) * chartHeight;
        
        if (index === 0) {
            ctx.moveTo(x, padding.top + chartHeight);
            ctx.lineTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    
    ctx.lineTo(padding.left + chartWidth, padding.top + chartHeight);
    ctx.lineTo(padding.left, padding.top + chartHeight);
    ctx.closePath();
    ctx.fill();
    
    // Draw main trend line with smooth curves
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 2.5;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.beginPath();
    
    recentTests.forEach((test, index) => {
        const x = padding.left + (index / (recentTests.length - 1)) * chartWidth;
        const carbon = test.carbon_g || test.carbon || 0;
        const y = padding.top + chartHeight - ((carbon - paddedMin) / paddedRange) * chartHeight;
        
        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            // Use straight lines instead of curves
            ctx.lineTo(x, y);
        }
    });
    
    ctx.stroke();
    
    // Draw enhanced data points
    recentTests.forEach((test, index) => {
        const x = padding.left + (index / (recentTests.length - 1)) * chartWidth;
        const carbon = test.carbon_g || test.carbon || 0;
        const y = padding.top + chartHeight - ((carbon - paddedMin) / paddedRange) * chartHeight;
        
        // Determine point color based on performance vs baseline
        const isAboveBaseline = carbon > baseline * 1.1;
        const isBelowBaseline = carbon < baseline * 0.9;
        
        // Draw outer ring (white)
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(x, y, 6, 0, 2 * Math.PI);
        ctx.fill();
        
        // Draw inner point with status color
        if (isAboveBaseline) {
            ctx.fillStyle = '#ef4444'; // Red for high carbon
        } else if (isBelowBaseline) {
            ctx.fillStyle = '#10b981'; // Green for low carbon
        } else {
            ctx.fillStyle = '#64748b'; // Gray for baseline
        }
        
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, 2 * Math.PI);
        ctx.fill();
        
        // Add subtle shadow
        ctx.shadowColor = 'rgba(0, 0, 0, 0.1)';
        ctx.shadowBlur = 2;
        ctx.shadowOffsetY = 1;
        ctx.fill();
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
        ctx.shadowOffsetY = 0;
    });
    
    // Draw chart title and legend
    ctx.fillStyle = '#1f2937';
    ctx.font = 'bold 14px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    
    // Show pipeline name in title if filtered
    const chartTitle = pipelineFilter && pipelineFilter !== 'all' 
        ? `Carbon Trend: ${pipelineFilter.length > 30 ? pipelineFilter.substring(0, 30) + '...' : pipelineFilter}`
        : 'Carbon Emissions Trend (All Pipelines)';
    ctx.fillText(chartTitle, padding.left, 8);
    
    // Draw legend
    const legendY = 8;
    const legendStartX = width - 200;
    
    // Energy line legend
    ctx.fillStyle = '#10b981';
    ctx.fillRect(legendStartX, legendY + 2, 12, 2);
    ctx.fillStyle = '#64748b';
    ctx.font = '11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Energy', legendStartX + 18, legendY);
    
    // Baseline legend
    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 2]);
    ctx.beginPath();
    ctx.moveTo(legendStartX + 70, legendY + 3);
    ctx.lineTo(legendStartX + 82, legendY + 3);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillText('Baseline', legendStartX + 88, legendY);
    
    console.log(`📊 Rendered enhanced trend chart with ${recentTests.length} data points`);
}

// Enhanced trend chart with animation support
function renderTrendChartAnimated(tests, pipelineFilter = 'all') {
    const canvas = document.getElementById('trend-canvas');
    if (!canvas || !tests || tests.length === 0) {
        renderTrendChart(tests, pipelineFilter);
        return;
    }
    
    // Filter tests by pipeline if specified
    let filteredTests = tests;
    if (pipelineFilter && pipelineFilter !== 'all') {
        filteredTests = tests.filter(test => 
            (test.pipeline_name || test.test_suite || test.suite || 'Unknown') === pipelineFilter
        );
    }
    
    if (filteredTests.length === 0) {
        renderTrendChart(tests, pipelineFilter);
        return;
    }
    
    // Set up animation
    let animationProgress = 0;
    const animationDuration = 800; // ms
    const startTime = Date.now();
    
    function animate() {
        const elapsed = Date.now() - startTime;
        animationProgress = Math.min(elapsed / animationDuration, 1);
        
        // Use easing function for smooth animation
        const easeProgress = 1 - Math.pow(1 - animationProgress, 3);
        
        // Render chart with current progress
        renderTrendChartWithProgress(filteredTests, easeProgress, pipelineFilter);
        
        if (animationProgress < 1) {
            requestAnimationFrame(animate);
        }
    }
    
    animate();
}

function renderTrendChartWithProgress(tests, progress, pipelineFilter = 'all') {
    const canvas = document.getElementById('trend-canvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    const padding = { top: 40, right: 40, bottom: 50, left: 70 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    // Filter tests by pipeline if specified
    let filteredTests = tests || [];
    if (pipelineFilter && pipelineFilter !== 'all') {
        filteredTests = filteredTests.filter(test => 
            (test.pipeline_name || test.test_suite || test.suite || 'Unknown') === pipelineFilter
        );
    }
    
    // Clear canvas
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, width, height);
    
    const recentTests = filteredTests.slice(-20);
    const carbonValues = recentTests.map(test => test.carbon_g || test.carbon || 0);
    const maxCarbon = Math.max(...carbonValues);
    const minCarbon = Math.min(...carbonValues);
    const range = Math.max(maxCarbon - minCarbon, 1);
    const paddedMin = minCarbon - range * 0.1;
    const paddedMax = maxCarbon + range * 0.1;
    const paddedRange = paddedMax - paddedMin;
    // Calculate baseline from FILTERED data
    const baselineData = filteredTests.length >= 5 ? filteredTests.slice(0, 5) : filteredTests;
    const baseline = baselineData.length > 0 ? 
        baselineData.reduce((sum, test) => sum + (test.carbon_g || test.carbon || 0), 0) / baselineData.length : 0;
    
    // Draw static elements (grid, labels) at full opacity
    ctx.globalAlpha = 1;
    
    // Grid lines
    ctx.strokeStyle = '#f1f5f9';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const y = padding.top + (chartHeight / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(padding.left + chartWidth, y);
        ctx.stroke();
    }
    
    // Y-axis labels
    ctx.fillStyle = '#64748b';
    ctx.font = '11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    for (let i = 0; i <= 4; i++) {
        const y = padding.top + (chartHeight / 4) * i;
        const value = paddedMax - (paddedRange / 4) * i;
        ctx.fillText(value.toFixed(1), padding.left - 10, y);
    }
    
    // Animate the data visualization
    ctx.globalAlpha = progress;
    
    // Baseline line
    const baselineY = padding.top + chartHeight - ((baseline - paddedMin) / paddedRange) * chartHeight;
    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 1;
    ctx.setLineDash([8, 4]);
    ctx.beginPath();
    ctx.moveTo(padding.left, baselineY);
    ctx.lineTo(padding.left + chartWidth * progress, baselineY);
    ctx.stroke();
    ctx.setLineDash([]);
    
    // Area under curve
    const gradient = ctx.createLinearGradient(0, padding.top, 0, padding.top + chartHeight);
    gradient.addColorStop(0, 'rgba(16, 185, 129, 0.1)');
    gradient.addColorStop(1, 'rgba(16, 185, 129, 0.02)');
    ctx.fillStyle = gradient;
    ctx.beginPath();
    
    const visiblePoints = Math.floor(recentTests.length * progress);
    for (let i = 0; i <= visiblePoints; i++) {
        if (i >= recentTests.length) break;
        
        const test = recentTests[i];
        const x = padding.left + (i / (recentTests.length - 1)) * chartWidth;
        const carbon = test.carbon_g || test.carbon || 0;
        const y = padding.top + chartHeight - ((carbon - paddedMin) / paddedRange) * chartHeight;
        
        if (i === 0) {
            ctx.moveTo(x, padding.top + chartHeight);
            ctx.lineTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    }
    
    if (visiblePoints > 0) {
        const lastX = padding.left + (visiblePoints / (recentTests.length - 1)) * chartWidth;
        ctx.lineTo(lastX, padding.top + chartHeight);
        ctx.lineTo(padding.left, padding.top + chartHeight);
        ctx.closePath();
        ctx.fill();
    }
    
    // Trend line
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 2.5;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.beginPath();
    
    for (let i = 0; i <= visiblePoints; i++) {
        if (i >= recentTests.length) break;
        
        const test = recentTests[i];
        const x = padding.left + (i / (recentTests.length - 1)) * chartWidth;
        const carbon = test.carbon_g || test.carbon || 0;
        const y = padding.top + chartHeight - ((carbon - paddedMin) / paddedRange) * chartHeight;
        
        if (i === 0) {
            ctx.moveTo(x, y);
        } else {
            // Use straight lines instead of curves
            ctx.lineTo(x, y);
        }
    }
    ctx.stroke();
    
    // Data points
    for (let i = 0; i <= visiblePoints; i++) {
        if (i >= recentTests.length) break;
        
        const test = recentTests[i];
        const x = padding.left + (i / (recentTests.length - 1)) * chartWidth;
        const carbon = test.carbon_g || test.carbon || 0;
        const y = padding.top + chartHeight - ((carbon - paddedMin) / paddedRange) * chartHeight;
        
        const isAboveBaseline = carbon > baseline * 1.1;
        const isBelowBaseline = carbon < baseline * 0.9;
        
        // Animate point scale
        const pointScale = Math.min(1, (progress * recentTests.length - i) * 2);
        if (pointScale <= 0) continue;
        
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(x, y, 6 * pointScale, 0, 2 * Math.PI);
        ctx.fill();
        
        if (isAboveBaseline) {
            ctx.fillStyle = '#ef4444';
        } else if (isBelowBaseline) {
            ctx.fillStyle = '#10b981';
        } else {
            ctx.fillStyle = '#64748b';
        }
        
        ctx.beginPath();
        ctx.arc(x, y, 4 * pointScale, 0, 2 * Math.PI);
        ctx.fill();
    }
    
    // Reset alpha
    ctx.globalAlpha = 1;
    
    // Title and legend (always visible)
    ctx.fillStyle = '#1f2937';
    ctx.font = 'bold 14px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.fillText('Carbon Emissions Trend', padding.left, 8);
}

function renderPipelineCards(pipelines) {
    const container = document.getElementById('cards-view');
    if (!container || !pipelines || pipelines.length === 0) {
        if (container) {
            container.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--grey-500);">
                    <div style="font-size: 16px; margin-bottom: 8px;">No pipeline history yet</div>
                    <div style="font-size: 14px;">Run pipelines via CI/CD to see execution data here</div>
                </div>
            `;
        }
        return;
    }
    
    // Show all pipelines in cards view, most recent first
    const sortedPipelines = [...pipelines].reverse();
    const baseline = pipelines.slice(0, 5).reduce((sum, pipeline) => sum + (pipeline.carbon_g || pipeline.carbon || 0), 0) / 5;
    
    container.innerHTML = sortedPipelines.map(pipeline => {
        const carbon = pipeline.carbon_g || pipeline.carbon || 0;
        const energy = pipeline.energy_j || (carbon * 1000) || 0; // Estimate if not available
        const changePercent = baseline > 0 ? ((carbon - baseline) / baseline) * 100 : 0;
        const status = Math.abs(changePercent) < 10 ? 'stable' : (changePercent > 20 ? 'critical' : 'stable');
        
        // Generate pipeline ID
        const pipelineId = pipeline.pipeline_id || pipeline.test_id || `pipeline-${Math.random().toString(36).substr(2, 6)}`;
        const shortId = pipelineId.substring(0, 8);
        
        return `
            <div class="commit-row">
                <div>
                    <div class="commit-id">${shortId}</div>
                    <div class="commit-date">${formatDateTime(pipeline.timestamp || pipeline.time)}</div>
                </div>
                <div class="commit-metrics">
                    <div class="commit-metric">
                        <div class="commit-metric-label">Energy</div>
                        <div class="commit-metric-value">${(energy / 1000).toFixed(0)} J</div>
                    </div>
                    <div class="commit-metric">
                        <div class="commit-metric-label">Carbon</div>
                        <div class="commit-metric-value">${carbon.toFixed(1)} mg</div>
                    </div>
                </div>
                <div class="commit-change ${changePercent >= 0 ? 'negative' : 'positive'}">
                    ${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(1)}%
                </div>
                <div class="commit-status ${status}">${status}</div>
            </div>
        `;
    }).join('');
}

function renderPipelineHistoryTable(pipelines) {
    // Store in state for export
    state.pipelineHistory = pipelines;
    
    // Populate pipeline filter dropdowns
    populatePipelineFilter(pipelines);
    populateTrendPipelineFilter(pipelines);
    
    // Get current pipeline filter value
    const pipelineFilter = document.getElementById('pipeline-filter')?.value || 'all';
    
    // Filter data for metrics and chart if a specific pipeline is selected
    let filteredForMetrics = pipelines;
    if (pipelineFilter !== 'all') {
        filteredForMetrics = pipelines.filter(p => 
            (p.pipeline_name || p.test_suite || p.suite || 'Unknown') === pipelineFilter
        );
    }
    
    // Render all analytics components with filtered data
    renderHistoryMetrics(filteredForMetrics.length > 0 ? filteredForMetrics : pipelines);
    renderTrendChartAnimated(pipelines, pipelineFilter);
    
    // Render both table and cards views (will be filtered by filterHistory if needed)
    renderPipelineTable(pipelines);
    renderPipelineCards(pipelines);
    
    // Apply any existing filters
    if (pipelineFilter !== 'all') {
        filterHistory();
    }
}

function renderPipelineTable(pipelines) {
    // Sort pipelines by descending time (most recent first)
    const sortedPipelines = [...pipelines].sort((a, b) => {
        const timeA = new Date(a.timestamp || a.time || 0);
        const timeB = new Date(b.timestamp || b.time || 0);
        return timeB - timeA; // Descending order
    });
    
    // Store sorted data for pagination
    state.pagination.filteredData = sortedPipelines;
    state.pagination.totalItems = sortedPipelines.length;
    state.pagination.totalPages = Math.ceil(sortedPipelines.length / state.pagination.itemsPerPage);
    
    // Ensure current page is valid
    if (state.pagination.currentPage > state.pagination.totalPages) {
        state.pagination.currentPage = Math.max(1, state.pagination.totalPages);
    }
    
    // Get current page data
    const startIndex = (state.pagination.currentPage - 1) * state.pagination.itemsPerPage;
    const endIndex = startIndex + state.pagination.itemsPerPage;
    const currentPageData = sortedPipelines.slice(startIndex, endIndex);
    
    // Render table
    const tbody = document.getElementById('history-table');
    if (!tbody) return;
    
    if (!pipelines || pipelines.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="10" style="text-align: center; padding: 40px; color: var(--grey-500);">
                    <div style="font-size: 16px; margin-bottom: 8px;">No pipeline history yet</div>
                    <div style="font-size: 14px;">Run pipelines via CI/CD to see execution data here</div>
                </td>
            </tr>
        `;
        // Hide pagination for empty state
        const paginationContainer = document.getElementById('pagination-container');
        if (paginationContainer) paginationContainer.style.display = 'none';
        return;
    }
    
    // Calculate baseline for comparison (from all data, not just current page)
    const baseline = sortedPipelines.slice(0, 5).reduce((sum, pipeline) => sum + (pipeline.carbon_g || pipeline.carbon || 0), 0) / 5;
    
    tbody.innerHTML = currentPageData.map(pipeline => {
        const timestamp = pipeline.timestamp || pipeline.time;
        const pipelineName = pipeline.pipeline_name || pipeline.test_suite || pipeline.suite || 'CI/CD Pipeline';
        const region = pipeline.optimal_region || pipeline.region || 'eu-west-2';
        const intensity = pipeline.optimal_intensity || pipeline.intensity || 0;
        const duration = pipeline.duration_minutes ? `${pipeline.duration_minutes}m` : (pipeline.duration || '--');
        const energy = pipeline.energy_j || (pipeline.carbon_g || pipeline.carbon || 0) * 1000; // Estimate if not available
        const carbon = pipeline.optimal_sci || pipeline.carbon_g || pipeline.carbon || 0;
        const status = pipeline.pipeline_status || pipeline.status || 'unknown';
        
        // Calculate vs baseline
        const baselineChange = baseline > 0 ? ((carbon - baseline) / baseline) * 100 : 0;
        const baselineDisplay = Math.abs(baselineChange) < 1 ? '—' : 
            `<span class="commit-change ${baselineChange >= 0 ? 'negative' : 'positive'}">
                ${baselineChange >= 0 ? '+' : ''}${baselineChange.toFixed(1)}%
            </span>`;
        
        // Status styling for pipelines
        let statusClass = 'status-normal';
        let statusLabel = status;
        if (status === 'successful' || status === 'optimized') {
            statusClass = 'status-optimized';
            statusLabel = 'Optimized';
        } else if (status === 'failed') {
            statusClass = 'status-warning';
            statusLabel = 'Failed';
        } else if (status === 'cancelled') {
            statusClass = 'status-normal';
            statusLabel = 'Cancelled';
        } else if (Math.abs(baselineChange) < 10) {
            statusClass = 'status-optimized';
            statusLabel = 'Stable';
        } else if (baselineChange > 20) {
            statusClass = 'status-warning';
            statusLabel = 'Critical';
        }
        
        const executionId = pipeline.execution_id || pipeline.pipeline_execution_id || '--';
        const shortExecutionId = executionId.length > 8 ? executionId.substring(0, 8) + '...' : executionId;
        
        return `
            <tr>
                <td class="text-mono text-sm">${formatDateTime(timestamp)}</td>
                <td>${pipelineName}</td>
                <td class="text-mono text-sm" title="${executionId}">${shortExecutionId}</td>
                <td class="text-mono">${region}</td>
                <td class="text-mono">${intensity.toFixed(0)} <span class="text-muted">gCO₂/kWh</span></td>
                <td class="text-mono">${duration}</td>
                <td class="text-mono">${(energy / 1000).toFixed(0)} <span class="text-muted">J</span></td>
                <td class="text-mono">${carbon.toFixed(1)} <span class="text-muted">mg</span></td>
                <td>${baselineDisplay}</td>
                <td><span class="commit-status ${statusClass}">${statusLabel}</span></td>
            </tr>
        `;
    }).join('');
    
    // Render pagination controls
    renderPaginationControls();
    
    console.log(`📊 Rendered paginated pipeline history: page ${state.pagination.currentPage}/${state.pagination.totalPages} (${currentPageData.length}/${sortedPipelines.length} entries)`);
}

// ============================================
// Pagination Functions
// ============================================

function renderPaginationControls() {
    const paginationContainer = document.getElementById('pagination-container');
    const paginationInfo = document.getElementById('pagination-info-text');
    const paginationPages = document.getElementById('pagination-pages');
    const prevBtn = document.getElementById('prev-page-btn');
    const nextBtn = document.getElementById('next-page-btn');
    
    if (!paginationContainer || !paginationInfo || !paginationPages || !prevBtn || !nextBtn) return;
    
    const { currentPage, totalPages, totalItems, itemsPerPage } = state.pagination;
    
    // Show pagination container
    paginationContainer.style.display = totalItems > 0 ? 'flex' : 'none';
    
    if (totalItems === 0) return;
    
    // Update info text
    const startItem = (currentPage - 1) * itemsPerPage + 1;
    const endItem = Math.min(currentPage * itemsPerPage, totalItems);
    paginationInfo.textContent = `Showing ${startItem}-${endItem} of ${totalItems} pipelines`;
    
    // Update prev/next buttons
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;
    
    // Generate page numbers
    paginationPages.innerHTML = generatePageNumbers(currentPage, totalPages);
}

function generatePageNumbers(currentPage, totalPages) {
    if (totalPages <= 1) return '';
    
    const pages = [];
    const maxVisiblePages = 5;
    
    if (totalPages <= maxVisiblePages) {
        // Show all pages if total is small
        for (let i = 1; i <= totalPages; i++) {
            pages.push(createPageButton(i, i === currentPage));
        }
    } else {
        // Show smart pagination with ellipsis
        pages.push(createPageButton(1, currentPage === 1));
        
        if (currentPage > 3) {
            pages.push('<span class="pagination-ellipsis">...</span>');
        }
        
        const start = Math.max(2, currentPage - 1);
        const end = Math.min(totalPages - 1, currentPage + 1);
        
        for (let i = start; i <= end; i++) {
            if (i !== 1 && i !== totalPages) {
                pages.push(createPageButton(i, i === currentPage));
            }
        }
        
        if (currentPage < totalPages - 2) {
            pages.push('<span class="pagination-ellipsis">...</span>');
        }
        
        if (totalPages > 1) {
            pages.push(createPageButton(totalPages, currentPage === totalPages));
        }
    }
    
    return pages.join('');
}

function createPageButton(pageNumber, isActive) {
    return `<button class="pagination-page ${isActive ? 'active' : ''}" onclick="goToPage(${pageNumber})">${pageNumber}</button>`;
}

function changePage(direction) {
    const newPage = state.pagination.currentPage + direction;
    if (newPage >= 1 && newPage <= state.pagination.totalPages) {
        goToPage(newPage);
    }
}

function goToPage(pageNumber) {
    if (pageNumber >= 1 && pageNumber <= state.pagination.totalPages) {
        state.pagination.currentPage = pageNumber;
        renderPipelineTable(state.pagination.filteredData);
    }
}

// Export pagination functions
window.changePage = changePage;
window.goToPage = goToPage;

// ============================================
// Chart Rendering
// ============================================

function renderForecastChart() {
    const canvas = document.getElementById('forecast-canvas');
    if (!canvas || state.forecast.length === 0) return;
    
    const ctx = canvas.getContext('2d');
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;
    
    const padding = { top: 20, right: 20, bottom: 30, left: 45 };
    const chartWidth = canvas.width - padding.left - padding.right;
    const chartHeight = canvas.height - padding.top - padding.bottom;
    
    const data = state.forecast.slice(0, CONFIG.forecastHours);
    const maxIntensity = Math.max(...data.map(d => d.intensity), 400);
    
    // Clear - white background for typographic style
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Grid lines - light grey
    ctx.strokeStyle = '#e5e5e5';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const y = padding.top + (chartHeight / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(canvas.width - padding.right, y);
        ctx.stroke();
        
        const value = Math.round(maxIntensity - (maxIntensity / 4) * i);
        ctx.fillStyle = '#737373';
        ctx.font = '11px Inter';
        ctx.textAlign = 'right';
        ctx.fillText(value.toString(), padding.left - 8, y + 4);
    }
    
    // Threshold line at 75 (LOW) - accent green
    const thresholdY = padding.top + chartHeight - (75 / maxIntensity) * chartHeight;
    ctx.strokeStyle = 'rgba(34, 197, 94, 0.4)';
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(padding.left, thresholdY);
    ctx.lineTo(canvas.width - padding.right, thresholdY);
    ctx.stroke();
    ctx.setLineDash([]);
    
    // Area gradient - subtle grey fill
    const gradient = ctx.createLinearGradient(0, padding.top, 0, canvas.height - padding.bottom);
    gradient.addColorStop(0, 'rgba(0, 0, 0, 0.08)');
    gradient.addColorStop(1, 'rgba(0, 0, 0, 0.0)');
    
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.moveTo(padding.left, canvas.height - padding.bottom);
    
    data.forEach((point, i) => {
        const x = padding.left + (chartWidth / (data.length - 1)) * i;
        const y = padding.top + chartHeight - (point.intensity / maxIntensity) * chartHeight;
        ctx.lineTo(x, y);
    });
    
    ctx.lineTo(padding.left + chartWidth, canvas.height - padding.bottom);
    ctx.closePath();
    ctx.fill();
    
    // Line - black for typographic style
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    data.forEach((point, i) => {
        const x = padding.left + (chartWidth / (data.length - 1)) * i;
        const y = padding.top + chartHeight - (point.intensity / maxIntensity) * chartHeight;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.stroke();
    
    // X-axis labels
    ctx.fillStyle = '#737373';
    ctx.font = '11px Inter';
    ctx.textAlign = 'center';
    data.forEach((point, i) => {
        if (i % 12 === 0) {
            const x = padding.left + (chartWidth / (data.length - 1)) * i;
            ctx.fillText(formatTime(point.from), x, canvas.height - 8);
        }
    });
    
    // Update stats
    const current = data[0]?.intensity || 0;
    const min24h = Math.min(...data.slice(0, 48).map(d => d.intensity));
    const max24h = Math.max(...data.slice(0, 48).map(d => d.intensity));
    const bestIdx = data.findIndex(d => d.intensity === min24h);
    const bestTime = bestIdx >= 0 ? formatTime(data[bestIdx].from) : '--';
    
    document.getElementById('forecast-current').textContent = current;
    document.getElementById('forecast-min').textContent = min24h;
    document.getElementById('forecast-max').textContent = max24h;
    document.getElementById('forecast-best-time').textContent = bestTime;
}

async function renderOptimalTimeChart(selectedRegion = 'eu-west-2') {
    const chartContainer = document.getElementById('optimal-time-chart');
    if (!chartContainer) return;
    
    let forecastData = null;
    let dataSource = '';
    
    // Get forecast data based on region
    if (selectedRegion === 'eu-west-2') {
        // Use UK Grid ESO data for London
        if (state.forecast && state.forecast.length > 0) {
            forecastData = state.forecast;
            dataSource = 'UK National Grid ESO';
        }
    } else {
        // Try ElectricityMaps forecast for other European regions
        console.log(`🔍 Fetching ElectricityMaps forecast for ${selectedRegion}...`);
        chartContainer.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #9ca3af;">
                <div style="font-size: 14px; margin-bottom: 8px;">📊 Loading forecast data...</div>
                <div style="font-size: 12px;">Fetching 24-hour predictions from ElectricityMaps</div>
            </div>
        `;
        
        try {
            forecastData = await ElectricityMapsAPI.getForecast24h(selectedRegion);
            if (forecastData && forecastData.length > 0) {
                dataSource = 'ElectricityMaps';
                console.log(`✅ Got ${forecastData.length} forecast points for ${selectedRegion}`);
            }
        } catch (error) {
            console.error(`❌ Failed to get forecast for ${selectedRegion}:`, error);
        }
    }
    
    // If no forecast data available, show current status
    if (!forecastData || forecastData.length === 0) {
        const currentRegion = Object.values(state.regions).find(r => r.name === selectedRegion);
        
        if (currentRegion) {
            chartContainer.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #9ca3af;">
                    <div style="font-size: 14px; margin-bottom: 8px;">📊 Current intensity: ${currentRegion.intensity.toFixed(1)} gCO₂/kWh</div>
                    <div style="font-size: 12px;">Forecast data not available for ${selectedRegion}</div>
                </div>
            `;
        } else {
            chartContainer.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #9ca3af;">
                    <div style="font-size: 14px; margin-bottom: 8px;">📊 Loading region data...</div>
                </div>
            `;
        }
        
        updateOptimalTimeUI('current-only', selectedRegion);
        return;
    }
    
    // Process forecast data based on source and filter out past times
    let sampledSlots = [];
    const now = new Date();
    
    if (selectedRegion === 'eu-west-2' && dataSource === 'UK National Grid ESO') {
        // UK data: 48 half-hour slots, filter future only, then sample every 4th (2 hours apart)
        const futureSlots = forecastData.filter(slot => new Date(slot.from) >= now);
        for (let i = 0; i < Math.min(48, futureSlots.length); i += 4) {
            sampledSlots.push(futureSlots[i]);
        }
    } else {
        // ElectricityMaps data: hourly data, filter future only, then sample every 2nd (2 hours apart)
        const futureSlots = forecastData.filter(slot => new Date(slot.from) >= now);
        for (let i = 0; i < Math.min(24, futureSlots.length); i += 2) {
            sampledSlots.push(futureSlots[i]);
        }
    }
    
    // Limit to 8 data points for compact display
    sampledSlots = sampledSlots.slice(0, 8);
    
    // Get current intensity and AWS renewable percentage for the selected region
    const currentRegion = Object.values(state.regions).find(r => r.name === selectedRegion);
    const regionConfig = AWS_REGIONS[selectedRegion];
    const currentIntensity = currentRegion ? currentRegion.intensity : (sampledSlots[0]?.intensity || 250);
    const AWS_RENEWABLE_PCT = regionConfig?.aws_renewable_pct || 0.75; // Default 75% renewable
    const PUE = 1.135;
    
    const datacenterSlots = sampledSlots.map(slot => ({
        ...slot,
        datacenterIntensity: Math.round(slot.intensity * (1 - AWS_RENEWABLE_PCT) * PUE * 10) / 10,
        time: new Date(slot.from).toLocaleTimeString('en-GB', { 
            hour: '2-digit', 
            minute: '2-digit',
            hour12: false 
        })
    }));
    
    // Add "Now" as first entry
    const nowSlot = {
        datacenterIntensity: Math.round(currentIntensity * (1 - AWS_RENEWABLE_PCT) * PUE * 10) / 10,
        time: 'Now',
        from: new Date().toISOString()
    };
    
    const allSlots = [nowSlot, ...datacenterSlots];
    const intensities = allSlots.map(slot => slot.datacenterIntensity);
    const times = allSlots.map(slot => slot.time);
    
    // Clear existing content
    chartContainer.innerHTML = '';
    
    // Create bars
    intensities.forEach((intensity, index) => {
        const bar = document.createElement('div');
        bar.className = 'forecast-bar';
        
        // Determine bar color based on AWS datacenter intensity thresholds
        if (intensity <= 25) {
            bar.classList.add('optimal');
        } else if (intensity <= 75) {
            bar.classList.add('moderate');
        } else {
            bar.classList.add('high');
        }
        
        // Set height based on intensity (normalize to 0-100%) - smaller for compact display
        const maxIntensity = Math.max(...intensities);
        const height = Math.max(12, (intensity / maxIntensity) * 40); // Min 12px, max 40px
        bar.style.height = `${height}px`;
        
        // Add time label
        const timeLabel = document.createElement('div');
        timeLabel.className = 'forecast-time';
        timeLabel.textContent = times[index];
        bar.appendChild(timeLabel);
        
        chartContainer.appendChild(bar);
    });
    
    // Find optimal time and calculate savings
    const optimalIndex = intensities.indexOf(Math.min(...intensities));
    const optimalIntensity = Math.min(...intensities);
    const savings = Math.round(((intensities[0] - optimalIntensity) / intensities[0]) * 100);
    
    // Update UI with real data
    updateOptimalTimeUI('real-data', {
        optimalIndex,
        savings,
        times,
        intensities,
        allSlots,
        selectedRegion,
        dataSource
    });
}

function updateOptimalTimeUI(mode, regionOrData = {}) {
    const optimalTimeText = document.getElementById('optimal-time-text');
    const optimalTimeWindow = document.getElementById('optimal-time-window');
    const optimalExplanation = document.getElementById('optimal-explanation');
    const optimalExplanationTitle = document.getElementById('optimal-explanation-title');
    const scheduleBtn = document.getElementById('btn-schedule');
    const scheduleTime = document.getElementById('schedule-time');
    
    if (mode === 'no-data') {
        // No forecast data available
        if (optimalTimeText) optimalTimeText.textContent = 'Run Now';
        if (optimalTimeWindow) optimalTimeWindow.textContent = 'Forecast data not available';
        if (optimalExplanationTitle) optimalExplanationTitle.textContent = 'Analysis';
        if (optimalExplanation) {
            optimalExplanation.textContent = 'Forecast optimization uses real-time data from UK National Grid ESO and ElectricityMaps.';
        }
        if (scheduleBtn) scheduleBtn.style.display = 'none';
        return;
    }
    
    if (mode === 'current-only') {
        const selectedRegion = regionOrData;
        const currentRegion = Object.values(state.regions).find(r => r.name === selectedRegion);
        const intensity = currentRegion ? currentRegion.intensity.toFixed(1) : '--';
        
        if (optimalTimeText) optimalTimeText.textContent = 'Run Now';
        if (optimalTimeWindow) {
            optimalTimeWindow.textContent = `Current intensity: ${intensity} gCO₂/kWh in ${selectedRegion}`;
        }
        if (optimalExplanationTitle) optimalExplanationTitle.textContent = `${selectedRegion} Analysis`;
        if (optimalExplanation) {
            const intensityLevel = currentRegion ? getIntensityAnalysis(currentRegion.intensity, selectedRegion) : 'Forecast data temporarily unavailable - try again in a moment.';
            optimalExplanation.textContent = intensityLevel;
        }
        if (scheduleBtn) scheduleBtn.style.display = 'none';
        return;
    }
    
    if (mode === 'real-data') {
        const { optimalIndex, savings, times, intensities, allSlots, selectedRegion, dataSource } = regionOrData;
        
        if (optimalIndex === 0 || savings < 10) {
            // Current time is optimal or savings are minimal
            if (optimalTimeText) optimalTimeText.textContent = 'Run Now';
            if (optimalTimeWindow) optimalTimeWindow.textContent = 'Current carbon intensity is optimal';
            if (optimalExplanationTitle) optimalExplanationTitle.textContent = `${selectedRegion} Analysis`;
            if (optimalExplanation) {
                optimalExplanation.textContent = `Grid intensity in ${selectedRegion} is currently at optimal levels. No significant benefit from waiting.`;
            }
            if (scheduleBtn) scheduleBtn.style.display = 'none';
        } else {
            // There's a better time to wait for
            const optimalSlot = allSlots[optimalIndex];
            const hoursFromNow = Math.round((new Date(optimalSlot.from) - new Date()) / (1000 * 60 * 60));
            const optimalTime = times[optimalIndex];
            const endTime = times[optimalIndex + 1] || times[optimalIndex];
            
            if (optimalTimeText) {
                optimalTimeText.textContent = hoursFromNow > 0 ? `In ${hoursFromNow} hours` : 'Soon';
            }
            
            if (optimalTimeWindow) {
                optimalTimeWindow.textContent = `Forecasted low intensity window (${optimalTime} - ${endTime})`;
            }
            
            if (optimalExplanationTitle) optimalExplanationTitle.textContent = `${selectedRegion} Forecast`;
            if (optimalExplanation) {
                const reason = getRegionSpecificExplanation(selectedRegion, intensities[0], savings, hoursFromNow);
                optimalExplanation.textContent = reason;
            }
            
            if (scheduleBtn && scheduleTime) {
                scheduleBtn.style.display = 'flex';
                scheduleTime.textContent = optimalTime;
            }
        }
    }
}

function getIntensityAnalysis(intensity, regionName) {
    if (intensity <= 25) {
        return `${regionName} has excellent carbon intensity due to high renewable energy usage. Perfect time to deploy.`;
    } else if (intensity <= 75) {
        return `${regionName} shows good carbon intensity with moderate renewable energy mix. Suitable for deployment.`;
    } else if (intensity <= 150) {
        return `${regionName} has moderate carbon intensity. Consider waiting for cleaner periods if possible.`;
    } else {
        return `${regionName} currently has high carbon intensity due to fossil fuel dependency. Waiting recommended.`;
    }
}

function getRegionSpecificExplanation(regionCode, currentIntensity, savings, hoursToWait) {
    // Region-specific explanations based on energy mix using AWS region codes
    const explanations = {
        'eu-north-1': `${regionCode}'s grid relies heavily on hydroelectric power. Waiting ${hoursToWait}h will align with peak hydro generation periods.`,
        'eu-west-3': `${regionCode} benefits from nuclear baseload power. The ${savings}% improvement comes from reduced peak demand periods.`,
        'eu-west-2': `${regionCode}'s grid varies with wind generation and gas peaking plants. Waiting ${hoursToWait}h avoids high-carbon peak periods.`,
        'eu-central-1': `${regionCode}'s grid includes significant renewable sources. The forecast shows ${savings}% improvement during off-peak hours.`,
        'eu-west-1': `${regionCode}'s grid benefits from wind power. Waiting ${hoursToWait}h aligns with forecasted wind generation increases.`,
        'eu-south-1': `${regionCode}'s grid includes solar and hydro sources. The ${savings}% improvement reflects optimal renewable generation timing.`,
        'eu-south-2': `${regionCode}'s grid has significant solar capacity. Waiting aligns with peak solar generation periods.`,
        'eu-central-2': `${regionCode} benefits from clean hydroelectric power. The forecast shows optimal low-carbon periods ahead.`
    };
    
    return explanations[regionCode] || `${regionCode}'s grid intensity will improve by ${savings}% in ${hoursToWait} hours due to increased renewable generation.`;
}

async function renderMixChart(regionId = 'eu-west-2') {
    const canvas = document.getElementById('mix-canvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;
    
    const legend = document.getElementById('mix-legend');
    const regionLabel = document.getElementById('mix-region-label');
    
    let mixData = null;
    
    // Try to get power breakdown from ElectricityMaps
    if (regionId !== 'eu-west-2') {
        mixData = await ElectricityMapsAPI.getPowerBreakdown(regionId);
        if (mixData && regionLabel) {
            regionLabel.textContent = regionId;
        }
    }
    
    // Fallback to UK data if available
    if (!mixData && state.generationMix) {
        mixData = state.generationMix;
        if (regionLabel) regionLabel.textContent = 'UK Only';
    }
    
    // No data available
    if (!mixData) {
        // Clear canvas - white background
        ctx.fillStyle = '#ffffff';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Show "No data" message
        ctx.fillStyle = '#a3a3a3';
        ctx.font = '14px Inter';
        ctx.textAlign = 'center';
        ctx.fillText('Power mix data available', canvas.width / 2, canvas.height / 2 - 10);
        ctx.fillText('for UK region only', canvas.width / 2, canvas.height / 2 + 10);
        
        legend.innerHTML = '<span class="mix-item" style="color: var(--grey-500);">Real-time data from UK National Grid ESO</span>';
        return;
    }
    
    // Monochrome palette with accent for renewables
    const colors = {
        'gas': '#404040', 'coal': '#171717', 'nuclear': '#737373',
        'wind': '#22c55e', 'solar': '#16a34a', 'hydro': '#15803d',
        'biomass': '#a3a3a3', 'imports': '#d4d4d4', 'other': '#e5e5e5'
    };
    
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = Math.min(centerX, centerY) - 30;
    
    // Clear - white background
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Draw pie
    let startAngle = -Math.PI / 2;
    mixData.forEach(item => {
        const sliceAngle = (item.perc / 100) * 2 * Math.PI;
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.arc(centerX, centerY, radius, startAngle, startAngle + sliceAngle);
        ctx.closePath();
        ctx.fillStyle = colors[item.fuel] || colors['other'];
        ctx.fill();
        // Add white border between slices
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
        ctx.stroke();
        startAngle += sliceAngle;
    });
    
    // Center hole (donut) - white center
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius * 0.6, 0, 2 * Math.PI);
    ctx.fillStyle = '#ffffff';
    ctx.fill();
    
    // Legend - update with monochrome colors
    legend.innerHTML = mixData.slice(0, 6).map(item => `
        <span class="mix-item">
            <span class="mix-dot" style="background: ${colors[item.fuel] || colors['other']}"></span>
            ${item.fuel} ${item.perc.toFixed(1)}%
        </span>
    `).join('');
}

// ============================================
// UI Calculator Handler
// ============================================

function calculateCarbonUI() {
    const region = document.getElementById('calc-region').value;
    const duration = parseFloat(document.getElementById('calc-duration').value) || 60;
    const vcpu = parseInt(document.getElementById('calc-vcpu').value) || 2;
    const memory = parseFloat(document.getElementById('calc-memory').value) || 4;
    
    // Get actual intensity for selected region from real-time data
    let intensity = 300; // fallback only if no data available
    let regionName = region; // Use AWS region code as display name
    
    if (state.regions[region]) {
        // Use actual real-time intensity data
        intensity = state.regions[region].intensity;
        regionName = region; // Keep AWS region code format
    } else if (region === 'us-east-1') {
        intensity = 380; // US East average (fallback for non-EU region)
        regionName = region;
    }
    
    const result = calculateCarbon(duration, vcpu, memory, intensity);
    
    // Update basic results
    document.getElementById('result-energy').textContent = `${result.energyKwh.toFixed(4)} kWh`;
    document.getElementById('result-operational').textContent = `${result.operationalG.toFixed(1)}g`;
    document.getElementById('result-embodied').textContent = `${result.embodiedG.toFixed(1)}g`;
    document.getElementById('result-total').textContent = `${result.totalG.toFixed(1)}g`;
    
    // Add real-world comparison
    updateCarbonComparison(result.totalG);
    
    // Add personalized suggestions
    updateSuggestions(region, intensity, result, duration, vcpu, memory);
    
    // Show results with animation
    const resultsEl = document.getElementById('calc-results');
    resultsEl.classList.add('calculated');
    
    // Scroll to results
    resultsEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    
    showToast(`Carbon footprint: ${result.totalG.toFixed(1)}g CO₂ in ${regionName}`, 'success');
}

function updateCarbonComparison(carbonGrams) {
    const comparisonEl = document.getElementById('result-comparison');
    if (!comparisonEl) return;
    
    // Real-world equivalents with corrected values
    const equivalents = getCarbonEquivalents(carbonGrams);
    
    let comparisonText = '';
    if (carbonGrams < 1) {
        comparisonText = `That's like charging your phone ${equivalents.phoneCharges} times`;
    } else if (carbonGrams < 10) {
        comparisonText = `Equivalent to ${equivalents.carKm} km by car or ${equivalents.coffeeCups} cups of coffee`;
    } else if (carbonGrams < 100) {
        comparisonText = `Same as driving ${equivalents.carKm} km or streaming HD video for ${equivalents.streamingHours} hours`;
    } else if (carbonGrams < 1000) {
        comparisonText = `Equivalent to ${equivalents.carKm} km of driving or ${equivalents.treesYear} trees growing for a year`;
    } else {
        comparisonText = `Equivalent to ${equivalents.carKm} km of driving or ${(carbonGrams/1000).toFixed(1)} kg of CO₂`;
    }
    
    comparisonEl.innerHTML = `
        <strong>Real-world comparison:</strong><br>
        ${comparisonText}
    `;
}

function updateSuggestions(region, intensity, result, duration, vcpu, memory) {
    const suggestionsEl = document.getElementById('suggestions-list');
    if (!suggestionsEl) return;
    
    const suggestions = [];
    
    // Find cleaner regions
    const allRegions = Object.values(state.regions);
    if (allRegions.length > 0) {
        const cleanestRegion = allRegions.reduce((min, r) => r.intensity < min.intensity ? r : min);
        const potentialSavings = Math.round(((intensity - cleanestRegion.intensity) / intensity) * 100);
        
        if (potentialSavings > 10) {
            suggestions.push(`Switch to ${cleanestRegion.location} to reduce emissions by ${potentialSavings}%`);
        }
    }
    
    // Duration optimization
    if (duration > 120) {
        suggestions.push('Consider breaking long-running tasks into smaller chunks');
    }
    
    // Resource optimization
    if (vcpu > 4) {
        suggestions.push('Optimize your code to use fewer CPU cores if possible');
    }
    
    if (memory > 16) {
        suggestions.push('Review memory usage - reducing RAM can lower energy consumption');
    }
    
    // Timing suggestions
    if (intensity > 150) {
        suggestions.push('Run workloads during off-peak hours when the grid is cleaner');
    }
    
    // General suggestions
    suggestions.push('Use auto-scaling to avoid running idle resources');
    suggestions.push('Consider serverless functions for short-running tasks');
    
    // Limit to top 4 suggestions
    const topSuggestions = suggestions.slice(0, 4);
    
    suggestionsEl.innerHTML = topSuggestions.map(suggestion => 
        `<li>${suggestion}</li>`
    ).join('');
}



// ============================================
// CSV Export
// ============================================

function exportCSV() {
    // Get current pipeline history data (from state only - no fallback)
    const pipelines = state.pipelineHistory || [];
    const headers = ['Time', 'Pipeline', 'Region', 'Intensity (gCO2/kWh)', 'Duration (min)', 'Carbon (gCO2)', 'Default SCI', 'Optimal SCI', 'Savings (gCO2)', 'Savings (%)', 'Status'];
    
    const rows = pipelines.map(pipeline => [
        pipeline.timestamp || formatDateTime(pipeline.time),
        pipeline.pipeline_name || pipeline.test_suite || pipeline.suite,
        pipeline.optimal_region || pipeline.region,
        pipeline.optimal_intensity || pipeline.intensity,
        pipeline.duration_minutes || pipeline.duration,
        (pipeline.optimal_sci || pipeline.carbon || 0).toFixed(2),
        (pipeline.default_sci || 0).toFixed(2),
        (pipeline.optimal_sci || 0).toFixed(2),
        (pipeline.savings_g || 0).toFixed(2),
        (pipeline.savings_percent || pipeline.savings || 0).toFixed(1),
        pipeline.pipeline_status || pipeline.status || 'unknown'
    ]);
    
    const csvContent = [
        headers.join(','),
        ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `green-qa-pipeline-history-${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    
    showToast('Pipeline history exported to CSV', 'success');
}

// ============================================
// History Table Rendering
// ============================================

/**
 * Render test history table with real API data
 * Shows: Time, Test Suite, Region, Intensity, Duration, Carbon (SCI), Savings, Status
 * 
 * Data comes from /history API endpoint which stores:
 * - SCI calculation for optimal region (where test ran)
 * - SCI calculation for default region (eu-west-2) for comparison
 * - Carbon savings (default_sci - optimal_sci)
 */
// Removed duplicate renderHistoryTable function - using enhanced version above

// ============================================
// Generation Mix Rendering
// ============================================

async function renderGenerationMix() {
    const section = document.getElementById('generation-mix');
    const canvas = document.getElementById('generation-mix-canvas');
    const list = document.getElementById('generation-mix-list');
    
    if (!section || !canvas || !list) return;
    
    // Keep section hidden - UK Energy Mix disabled
    // section.style.display = 'block';
    return; // Exit early to prevent rendering
    
    // If no data available, show loading/placeholder
    if (!state.generationMix || state.generationMix.length === 0) {
        list.innerHTML = '<div style="padding: 40px; text-align: center; color: var(--grey-500);">Loading UK generation mix data...</div>';
        console.log('⏳ Waiting for UK generation mix data...');
        return;
    }
    
    // Fetch carbon factors
    const carbonFactors = await UKCarbonAPI.getCarbonFactors();
    
    // Fuel type mapping (no icons for clean design)
    const fuelConfig = {
        'wind': { color: '#10b981', label: 'Wind' },
        'solar': { color: '#f59e0b', label: 'Solar' },
        'hydro': { color: '#3b82f6', label: 'Hydro' },
        'nuclear': { color: '#8b5cf6', label: 'Nuclear' },
        'biomass': { color: '#84cc16', label: 'Biomass' },
        'gas': { color: '#6b7280', label: 'Gas' },
        'coal': { color: '#1f2937', label: 'Coal' },
        'imports': { color: '#ec4899', label: 'Imports' },
        'other': { color: '#d4d4d4', label: 'Other' }
    };
    
    // Sort by percentage (highest first)
    const sortedMix = [...state.generationMix].sort((a, b) => b.perc - a.perc);
    
    // Render donut chart
    const ctx = canvas.getContext('2d');
    const size = 220;
    canvas.width = size;
    canvas.height = size;
    
    const centerX = size / 2;
    const centerY = size / 2;
    const radius = size / 2 - 20;
    const innerRadius = radius * 0.6;
    
    // Clear canvas
    ctx.clearRect(0, 0, size, size);
    
    // Draw donut chart
    let startAngle = -Math.PI / 2;
    sortedMix.forEach(item => {
        const sliceAngle = (item.perc / 100) * 2 * Math.PI;
        const config = fuelConfig[item.fuel] || fuelConfig['other'];
        
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, startAngle, startAngle + sliceAngle);
        ctx.arc(centerX, centerY, innerRadius, startAngle + sliceAngle, startAngle, true);
        ctx.closePath();
        ctx.fillStyle = config.color;
        ctx.fill();
        
        // White border
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 3;
        ctx.stroke();
        
        startAngle += sliceAngle;
    });
    
    // Center text
    ctx.fillStyle = '#000000';
    ctx.font = '600 14px Inter';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('UK Grid', centerX, centerY - 6);
    ctx.font = '400 11px Inter';
    ctx.fillStyle = '#737373';
    ctx.fillText('Live Mix', centerX, centerY + 6);
    
    // Render list with carbon factors
    list.innerHTML = sortedMix.map(item => {
        const config = fuelConfig[item.fuel] || fuelConfig['other'];
        const carbonFactor = carbonFactors ? getCarbonFactorForFuel(item.fuel, carbonFactors) : null;
        
        return `
            <div class="generation-mix-item">
                <div class="generation-mix-icon" style="background: ${config.color};"></div>
                <div class="generation-mix-percentage">${item.perc.toFixed(1)}%</div>
                <div class="generation-mix-info">
                    <div class="generation-mix-fuel">${config.label}</div>
                    <div class="generation-mix-carbon-factor">
                        ${carbonFactor !== null ? `${carbonFactor} gCO₂/kWh` : 'N/A'}
                    </div>
                </div>
                <span class="tooltip-trigger">
                    <span class="info-icon">i</span>
                    <div class="tooltip">
                        <div class="tooltip-title">${config.label} Carbon Factor</div>
                        <div class="tooltip-content">
                            ${getCarbonFactorDescription(item.fuel, carbonFactor)}
                        </div>
                        <div class="tooltip-breakdown">
                            Current contribution: ${item.perc.toFixed(1)}% of grid<br>
                            Carbon emissions: ${carbonFactor !== null ? `${carbonFactor} gCO₂ per kWh` : 'N/A'}
                        </div>
                        <div class="tooltip-example">
                            ${getCarbonFactorExample(item.fuel, carbonFactor, item.perc)}
                        </div>
                    </div>
                </span>
            </div>
        `;
    }).join('');
}

function getCarbonFactorForFuel(fuel, factors) {
    const mapping = {
        'biomass': factors.Biomass,
        'coal': factors.Coal,
        'gas': factors['Gas (Combined Cycle)'],
        'hydro': factors.Hydro,
        'nuclear': factors.Nuclear,
        'other': factors.Other,
        'solar': factors.Solar,
        'wind': factors.Wind,
        'imports': Math.round((factors['Dutch Imports'] + factors['French Imports'] + factors['Irish Imports']) / 3)
    };
    
    return mapping[fuel] !== undefined ? mapping[fuel] : null;
}

function getCarbonFactorDescription(fuel, factor) {
    const descriptions = {
        'wind': 'Wind power has zero direct emissions. The carbon factor accounts for manufacturing and maintenance of turbines.',
        'solar': 'Solar power has zero direct emissions. The carbon factor accounts for panel manufacturing and installation.',
        'hydro': 'Hydroelectric power has zero direct emissions. The carbon factor accounts for dam construction and maintenance.',
        'nuclear': 'Nuclear power has zero direct emissions. The carbon factor accounts for plant construction, fuel processing, and waste management.',
        'biomass': 'Biomass burns organic material. While renewable, it releases CO₂ during combustion.',
        'gas': 'Natural gas combined cycle plants are cleaner than coal but still emit significant CO₂.',
        'coal': 'Coal power plants have the highest carbon emissions of all generation types.',
        'imports': 'Imported electricity has varying carbon intensity depending on the source country\'s energy mix.',
        'other': 'Other generation sources include oil, pumped storage, and miscellaneous sources.'
    };
    
    return descriptions[fuel] || 'Carbon emissions from this fuel source.';
}

function getCarbonFactorExample(fuel, factor, percentage) {
    if (factor === null || factor === 0) {
        return `${percentage.toFixed(1)}% of current grid = Zero emissions from this source`;
    }
    
    const gridContribution = (factor * percentage / 100).toFixed(1);
    return `If grid is 100% ${fuel}: ${factor} gCO₂/kWh<br>Current ${percentage.toFixed(1)}% contribution: ~${gridContribution} gCO₂/kWh to grid average`;
}

// ============================================
// Main Refresh Function
// ============================================

async function refreshData() {
    console.log('🔄 Refreshing data...');
    
    const refreshBtn = document.querySelector('.btn-refresh');
    if (refreshBtn) {
        refreshBtn.classList.add('loading');
        refreshBtn.disabled = true;
    }
    
    try {
        // Load carbon intensity data (Europe with real-time)
        await loadAllRegionData();
        
        // Load global regions
        const globalRegions = await loadGlobalRegions();
        if (globalRegions && globalRegions.length > 0) {
            // Sync real-time Europe data with global regions
            syncEuropeDataToGlobal(globalRegions);
            
            // Store synced data
            state.globalRegions = globalRegions;
            
            // Force re-render with synced data
            console.log('🎨 Rendering global regions with synced data...');
            renderGlobalRegionGrid(state.globalRegions);
            
            // Refresh map with real-time data
            if (typeof refreshMapData === 'function' && mapInitialized) {
                setTimeout(() => refreshMapData(), 500);
            }
        }
        
        // Load real pipeline history from API
        const tests = await loadPipelineHistory(50);
        
        // Calculate real carbon savings
        const savings = calculateCarbonSavings(tests);
        state.totalCarbonSaved = savings.saved;
        state.testsOptimized = savings.optimized;
        
        console.log(`📊 Carbon saved: ${savings.saved}g from ${savings.optimized} optimized tests`);
        
        // Update all UI components
        updateSummaryCards();
        renderRegionGrid();
        renderPipelineHistoryTable(tests); // Pass real pipeline data
        
        // Update impact summary with real data
        await updateImpactSummary();
        
        // Render generation mix if available
        if (state.generationMix) {
            await renderGenerationMix();
        }
        
        // Update optimal time if UK forecast data is available
        if (state.forecast.length > 0) {
            updateOptimalTime();
            const selectedRegion = document.getElementById('optimal-time-region-select')?.value || 'eu-west-2';
            renderOptimalTimeChart(selectedRegion); // Update the new optimal time chart with real data
        }
        
        showToast('Data refreshed successfully', 'success');
        console.log('✅ All data refreshed');
        
    } catch (error) {
        console.error('❌ Refresh error:', error);
        showToast('Failed to refresh data', 'error');
    } finally {
        if (refreshBtn) {
            refreshBtn.classList.remove('loading');
            refreshBtn.disabled = false;
        }
    }
}

// ============================================
// Navigation Handling
// ============================================

function openGlobalRegionModal(region) {
    const modal = document.getElementById('region-modal');
    
    // Populate modal data
    document.getElementById('modal-region-name').textContent = region.region_code;
    document.getElementById('modal-region-location').textContent = region.location;
    document.getElementById('modal-intensity').textContent = region.datacenter_intensity.toFixed(1);
    document.getElementById('modal-index').textContent = getIntensityIndex(region.datacenter_intensity);
    document.getElementById('modal-region-id').textContent = region.region_code;
    document.getElementById('modal-country').textContent = region.country;
    document.getElementById('modal-coords').textContent = `${region.lat.toFixed(2)}°N, ${Math.abs(region.lon).toFixed(2)}°${region.lon >= 0 ? 'E' : 'W'}`;
    document.getElementById('modal-source').textContent = 'AWS Global Carbon Optimizer';
    
    // Find optimal region from global regions
    const allGlobalRegions = state.globalRegions || [];
    const optimalRegion = allGlobalRegions.length > 0 
        ? allGlobalRegions.reduce((min, r) => r.datacenter_intensity < min.datacenter_intensity ? r : min)
        : region;
    
    const optimalBadge = document.getElementById('modal-optimal-badge');
    const savingsEl = document.getElementById('modal-savings');
    
    document.getElementById('modal-optimal-location').textContent = optimalRegion.region_code;
    
    // Show badge if this is the optimal region
    if (optimalRegion.region_code === region.region_code) {
        optimalBadge.style.display = 'block';
        optimalBadge.innerHTML = `
            <div style="font-size: 13px; font-weight: 600; color: #16a34a; text-transform: uppercase; letter-spacing: 0.06em;">
                ✓ Optimal Region — Best carbon intensity worldwide
            </div>
        `;
        savingsEl.textContent = 'Current';
        savingsEl.classList.remove('accent');
        savingsEl.style.color = 'var(--grey-600)';
    } else {
        optimalBadge.style.display = 'none';
        const savingsPercent = Math.round(((region.datacenter_intensity - optimalRegion.datacenter_intensity) / region.datacenter_intensity) * 100);
        savingsEl.textContent = `${savingsPercent}%`;
        savingsEl.classList.add('accent');
        savingsEl.style.color = '';
    }
    
    // Hide time-based optimization (not available for all regions)
    const optimalTimeSection = document.getElementById('modal-optimal-time-section');
    optimalTimeSection.style.display = 'none';
    
    // Show renewable energy info
    const emberSection = document.getElementById('modal-ember-section');
    const liveSection = document.getElementById('modal-live-section');
    const estimatedSection = document.getElementById('modal-estimated-section');
    
    emberSection.style.display = 'none';
    liveSection.style.display = 'none';
    estimatedSection.style.display = 'block';
    
    estimatedSection.innerHTML = `
        <div class="modal-section-title">AWS Renewable Energy & Data Center Efficiency</div>
        <div style="font-size: 14px; line-height: 1.6; color: var(--grey-700);">
            <p style="margin-bottom: 12px;">
                <strong>Grid Intensity:</strong> ${region.grid_intensity.toFixed(1)} gCO₂/kWh<br>
                <strong>AWS Renewable Energy:</strong> ${Math.round(region.aws_renewable_pct * 100)}%<br>
                <strong>Data Center Intensity:</strong> ${region.datacenter_intensity.toFixed(1)} gCO₂/kWh
            </p>
            <p style="margin-bottom: 0;">
                AWS data centers use renewable energy and efficient infrastructure (PUE 1.135) 
                to significantly reduce carbon emissions compared to the regional grid average.
            </p>
        </div>
    `;
    
    // Show modal
    modal.style.display = 'flex';
    
    // Close on overlay click
    modal.onclick = (e) => {
        if (e.target === modal) {
            closeRegionModal();
        }
    };
}

function initNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    // Handle click events
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            // Skip external links (like advanced.html)
            if (link.classList.contains('nav-link-external') || !link.dataset.section) {
                return; // Allow default behavior for external links
            }
            
            e.preventDefault();
            
            const sectionId = link.dataset.section;
            const targetSection = document.getElementById(sectionId);
            
            if (targetSection) {
                // Calculate offset for sticky header
                const headerHeight = document.querySelector('.header').offsetHeight;
                const targetPosition = targetSection.offsetTop - headerHeight - 20;
                
                // Smooth scroll to section
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
                
                // Update active state
                updateActiveNavLink(sectionId);
            } else if (sectionId === 'dashboard') {
                // Scroll to top for dashboard
                window.scrollTo({ top: 0, behavior: 'smooth' });
                updateActiveNavLink('dashboard');
            }
        });
    });
    
    // Update active link based on scroll position
    window.addEventListener('scroll', throttle(updateActiveNavOnScroll, 100));
}

function updateActiveNavLink(sectionId) {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        if (link.dataset.section === sectionId) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

function updateActiveNavOnScroll() {
    const sections = ['stats-insights-section', 'regions', 'global-regions', 'calculator', 'history'];
    const headerHeight = document.querySelector('.header').offsetHeight;
    const scrollPosition = window.scrollY + headerHeight + 100;
    
    // Check if at top of page
    if (window.scrollY < 100) {
        updateActiveNavLink('dashboard');
        return;
    }
    
    // Find which section is currently in view
    for (let i = sections.length - 1; i >= 0; i--) {
        const section = document.getElementById(sections[i]);
        if (section && section.offsetTop <= scrollPosition) {
            updateActiveNavLink(sections[i]);
            break;
        }
    }
}

// Throttle function to limit scroll event firing
function throttle(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// ============================================
// Window Resize Handler
// ============================================

function handleResize() {
    // Reserved for future responsive features
}

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', async () => {
    console.log('Green QA Dashboard v2.0 — Initializing');
    
    // Initialize navigation
    initNavigation();
    
    // Add resize listener
    window.addEventListener('resize', handleResize);
    
    // Show generation mix section (will show loading state initially)
    await renderGenerationMix();
    
    // Initialize optimal time chart (will be populated when forecast data loads)
    renderOptimalTimeChart('eu-west-2');
    
    // Removed run-now-btn and schedule-btn event listeners
    
    // Initial data load
    await refreshData();
    
    // Set up auto-refresh
    setInterval(refreshData, CONFIG.refreshInterval);
    
    console.log('Dashboard initialized');
});

// ============================================
// Region Detail Modal
// ============================================

function openRegionModal(region) {
    const modal = document.getElementById('region-modal');
    
    // Populate modal data
    document.getElementById('modal-region-name').textContent = region.name;
    document.getElementById('modal-region-location').textContent = region.location;
    document.getElementById('modal-intensity').textContent = region.intensity;
    document.getElementById('modal-index').textContent = region.index || getIntensityIndex(region.intensity);
    document.getElementById('modal-region-id').textContent = region.name;
    document.getElementById('modal-country').textContent = `${region.flag} ${region.country}`;
    document.getElementById('modal-coords').textContent = `${region.lat.toFixed(2)}°N, ${Math.abs(region.lon).toFixed(2)}°${region.lon >= 0 ? 'E' : 'W'}`;
    document.getElementById('modal-source').textContent = region.source;
    
    // Calculate optimal location (lowest intensity region)
    const allRegions = Object.values(state.regions);
    const optimalRegion = allRegions.reduce((min, r) => r.intensity < min.intensity ? r : min);
    
    const optimalBadge = document.getElementById('modal-optimal-badge');
    const savingsEl = document.getElementById('modal-savings');
    
    document.getElementById('modal-optimal-location').textContent = optimalRegion.name;
    
    // Show badge if this is the optimal region
    if (optimalRegion.name === region.name) {
        optimalBadge.style.display = 'block';
        savingsEl.textContent = 'Current';
        savingsEl.classList.remove('accent');
        savingsEl.style.color = 'var(--grey-600)';
    } else {
        optimalBadge.style.display = 'none';
        const savingsPercent = Math.round(((region.intensity - optimalRegion.intensity) / region.intensity) * 100);
        savingsEl.textContent = `${savingsPercent}%`;
        savingsEl.classList.add('accent');
        savingsEl.style.color = '';
    }
    
    // Show optimal time if UK region with forecast data
    const optimalTimeSection = document.getElementById('modal-optimal-time-section');
    if (region.name === 'eu-west-2' && state.forecast.length > 0) {
        optimalTimeSection.style.display = 'block';
        
        // Get AWS renewable percentage for London
        const regionConfig = AWS_REGIONS['eu-west-2'];
        const renewablePct = regionConfig?.aws_renewable_pct || 0.80;
        const PUE = 1.135;
        
        // Convert grid forecast to AWS datacenter intensity
        const next24h = state.forecast.slice(0, 48).map(slot => ({
            ...slot,
            datacenterIntensity: Math.round(slot.intensity * (1 - renewablePct) * PUE * 10) / 10
        }));
        
        // Find optimal time based on AWS datacenter intensity
        const minDatacenterIntensity = Math.min(...next24h.map(f => f.datacenterIntensity));
        const optimalSlot = next24h.find(f => f.datacenterIntensity === minDatacenterIntensity);
        
        if (optimalSlot) {
            const optimalTime = new Date(optimalSlot.from);
            const now = new Date();
            
            // If optimal time is in the past, find next best time
            let displaySlot = optimalSlot;
            if (optimalTime < now) {
                const threshold = minDatacenterIntensity * 1.1;
                const futureSlots = next24h.filter(f => new Date(f.from) > now && f.datacenterIntensity <= threshold);
                if (futureSlots.length > 0) {
                    displaySlot = futureSlots[0];
                }
            }
            
            const displayTime = new Date(displaySlot.from);
            const timeStr = displayTime.toLocaleTimeString('en-GB', { 
                hour: '2-digit', 
                minute: '2-digit',
                hour12: false 
            });
            const dateStr = displayTime.toLocaleDateString('en-GB', { 
                month: 'short', 
                day: 'numeric' 
            });
            
            document.getElementById('modal-optimal-time').textContent = `${dateStr} at ${timeStr}`;
            document.getElementById('modal-forecast-min').textContent = `${displaySlot.datacenterIntensity} gCO₂/kWh (AWS DC)`;
            
            // Calculate time-shift savings using datacenter intensity
            const currentDatacenterIntensity = region.intensity; // Already AWS DC intensity
            const timeshiftSavings = Math.round(((currentDatacenterIntensity - displaySlot.datacenterIntensity) / currentDatacenterIntensity) * 100);
            if (timeshiftSavings > 0) {
                document.getElementById('modal-timeshift-savings').textContent = `${timeshiftSavings}%`;
            } else {
                document.getElementById('modal-timeshift-savings').textContent = 'Optimal now';
            }
        }
    } else {
        optimalTimeSection.style.display = 'none';
    }
    
    // Show/hide data source explanation
    const emberSection = document.getElementById('modal-ember-section');
    const liveSection = document.getElementById('modal-live-section');
    const estimatedSection = document.getElementById('modal-estimated-section');
    
    // Hide all sections first
    emberSection.style.display = 'none';
    liveSection.style.display = 'none';
    estimatedSection.style.display = 'none';
    
    // Show AWS renewable energy breakdown
    const renewablePct = region.aws_renewable_pct ? Math.round(region.aws_renewable_pct * 100) : 70;
    const gridIntensity = region.grid_intensity || region.intensity;
    const datacenterIntensity = region.datacenter_intensity || region.intensity;
    
    // Update the estimated section with AWS renewable energy info
    estimatedSection.innerHTML = `
        <div class="modal-section-title">AWS Renewable Energy & Data Center Efficiency</div>
        <div style="font-size: 14px; line-height: 1.6; color: var(--grey-700);">
            <p style="margin-bottom: 12px;">
                <strong>Grid Intensity:</strong> ${gridIntensity.toFixed(1)} gCO₂/kWh<br>
                <strong>AWS Renewable Energy:</strong> ${renewablePct}%<br>
                <strong>AWS PUE (Power Usage Effectiveness):</strong> 1.135<br>
                <strong>Data Center Intensity:</strong> ${datacenterIntensity.toFixed(1)} gCO₂/kWh
            </p>
            <p style="margin-bottom: 12px; padding: 12px; background: var(--grey-100); border-left: 3px solid var(--accent);">
                <strong>Calculation:</strong><br>
                ${gridIntensity.toFixed(1)} × (1 - ${renewablePct/100}) × 1.135 = ${datacenterIntensity.toFixed(1)} gCO₂/kWh
            </p>
            <p style="margin-bottom: 0;">
                AWS data centers use renewable energy and efficient infrastructure to significantly 
                reduce carbon emissions compared to the regional grid average. The displayed intensity 
                (${datacenterIntensity.toFixed(1)} gCO₂/kWh) represents the actual carbon footprint when 
                running workloads in AWS, not the grid average.
            </p>
            <p style="margin-top: 12px; font-size: 12px; color: var(--grey-600);">
                <strong>Data Sources:</strong><br>
                • Grid intensity: ${region.source}<br>
                • AWS renewable %: <a href="https://sustainability.aboutamazon.com/products-services/the-cloud" target="_blank" style="color: var(--accent);">AWS Sustainability Report 2023</a><br>
                • PUE: <a href="https://www.cloudcarbonfootprint.org/docs/methodology/" target="_blank" style="color: var(--accent);">Cloud Carbon Footprint</a>
            </p>
        </div>
    `;
    
    // Always show the estimated section with AWS breakdown
    estimatedSection.style.display = 'block';
    
    // Also show live section if real-time data
    if (region.isRealtime) {
        liveSection.style.display = 'block';
    }
    
    // Show modal
    modal.style.display = 'flex';
    
    // Close on overlay click
    modal.onclick = (e) => {
        if (e.target === modal) {
            closeRegionModal();
        }
    };
}

function closeRegionModal() {
    const modal = document.getElementById('region-modal');
    modal.style.display = 'none';
}

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeRegionModal();
    }
});

// ============================================
// Optimal Time Finder
// ============================================

function updateOptimalTime() {
    // Legacy function - now handled by renderOptimalTimeChart()
    // Just call the new chart rendering function
    const selectedRegion = document.getElementById('optimal-time-region-select')?.value || 'eu-west-2';
    renderOptimalTimeChart(selectedRegion);
}

function updateOptimalTimeForRegion() {
    const regionSelect = document.getElementById('optimal-time-region-select');
    if (!regionSelect) return;
    
    const selectedRegion = regionSelect.value;
    renderOptimalTimeChart(selectedRegion);
}

// New functions for enhanced optimal time functionality
function scheduleOptimalTime() {
    const scheduleTime = document.getElementById('schedule-time')?.textContent || '--:--';
    if (scheduleTime === '--:--') {
        showToast('Please wait for forecast data to load', 'warning');
        return;
    }
    showToast(`Tests scheduled for ${scheduleTime} when carbon intensity is lowest`, 'success');
    
    // Here you would integrate with your CI/CD system to actually schedule the tests
    console.log(`Scheduling tests for optimal time: ${scheduleTime}`);
}

// Removed runTestsNow function - no longer needed

function switchHistoryView(view) {
    const tableView = document.getElementById('table-view');
    const cardsView = document.getElementById('cards-view');
    const tableBtn = document.getElementById('table-view-btn');
    const cardsBtn = document.getElementById('cards-view-btn');
    
    if (view === 'table') {
        tableView.style.display = 'block';
        cardsView.style.display = 'none';
        tableBtn.classList.add('active');
        cardsBtn.classList.remove('active');
    } else {
        tableView.style.display = 'none';
        cardsView.style.display = 'block';
        tableBtn.classList.remove('active');
        cardsBtn.classList.add('active');
    }
}

// Expose functions globally for inline onclick handlers
window.refreshData = refreshData;
window.calculateCarbonUI = calculateCarbonUI;
window.exportCSV = exportCSV;
window.switchHistoryView = switchHistoryView;
window.closeRegionModal = closeRegionModal;
window.updateOptimalTime = updateOptimalTime;
window.updatePotentialSavings = updatePotentialSavings;
window.updateRegionComparison = updateRegionComparison;
window.updateOptimalTimeForRegion = updateOptimalTimeForRegion;
window.scheduleOptimalTime = scheduleOptimalTime;
window.runTestsNow = runTestsNow;


// ============================================
// D3.js World Map Visualization
// ============================================

function initWorldMap() {
    const container = document.getElementById('world-map-container');
    if (!container) return;
    
    const width = container.clientWidth;
    const height = container.clientHeight || 450;
    
    svg = d3.select('#world-map')
        .attr('width', width)
        .attr('height', height);
    
    // Clear existing content
    svg.selectAll('*').remove();
    
    // Add ocean/background
    svg.append('rect')
        .attr('width', width)
        .attr('height', height)
        .attr('fill', '#1e293b'); // Dark blue-gray ocean
    
    // Create projection
    projection = d3.geoMercator()
        .scale(150)
        .translate([width / 2, height / 1.5]);
    
    path = d3.geoPath().projection(projection);
    
    // Create main group first
    g = svg.append('g');
    
    // Create zoom behavior
    zoom = d3.zoom()
        .scaleExtent([1, 8])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
            currentZoomLevel = event.transform.k;
            
            // Adjust marker sizes based on zoom
            g.selectAll('.marker-group circle')
                .attr('r', 12 / Math.sqrt(currentZoomLevel));
            
            g.selectAll('.marker-group text')
                .attr('font-size', (10 / Math.sqrt(currentZoomLevel)) + 'px');
            
            // Show/hide region labels based on zoom
            g.selectAll('.region-label')
                .style('opacity', currentZoomLevel > 2 ? 1 : 0);
        });
    
    svg.call(zoom);
    
    // Load world map data (using Natural Earth data from CDN)
    console.log('🌍 Loading world map data...');
    d3.json('https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json')
        .then(world => {
            console.log('✅ World map data loaded');
            
            const features = topojson.feature(world, world.objects.countries).features;
            
            // Draw countries with carbon intensity coloring
            const countriesGroup = g.append('g').attr('class', 'countries');
            
            countriesGroup.selectAll('path')
                .data(features)
                .enter()
                .append('path')
                .attr('d', path)
                .attr('fill', d => getCountryColor(d))
                .attr('stroke', '#64748b')
                .attr('stroke-width', 0.5)
                .attr('opacity', 1)
                .on('mouseover', function(event, d) {
                    d3.select(this)
                        .attr('stroke', '#94a3b8')
                        .attr('stroke-width', 1.5);
                })
                .on('mouseout', function() {
                    d3.select(this)
                        .attr('stroke', '#64748b')
                        .attr('stroke-width', 0.5);
                });
            
            console.log('🗺️ World map rendered, now adding markers...');
            // Set map as initialized before adding markers
            mapInitialized = true;
            console.log('✅ mapInitialized set to:', mapInitialized);
            // Add AWS region markers
            renderRegionMarkers();
        })
        .catch(error => {
            console.error('❌ Error loading map data:', error);
            console.log('⚠️ Fallback: showing markers without world map');
            // Set map as initialized before adding markers (fallback mode)
            mapInitialized = true;
            // Fallback: just show markers without world map
            renderRegionMarkers();
        });
}

let currentZoomLevel = 1;

function applySpiderfy(markers) {
    // Detect overlapping markers and spread them out
    const minDistance = 30; // Minimum distance between markers
    const spreadRadius = 40; // How far to spread overlapping markers
    
    // Group markers that are too close
    const clusters = [];
    const processed = new Set();
    
    markers.forEach((marker, i) => {
        if (processed.has(i)) return;
        
        const cluster = [i];
        processed.add(i);
        
        // Find all markers within minDistance
        markers.forEach((other, j) => {
            if (i === j || processed.has(j)) return;
            
            const dx = marker.x - other.x;
            const dy = marker.y - other.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance < minDistance) {
                cluster.push(j);
                processed.add(j);
            }
        });
        
        if (cluster.length > 1) {
            clusters.push(cluster);
        }
    });
    
    // Spread out clustered markers in a circle
    clusters.forEach(cluster => {
        const centerX = cluster.reduce((sum, i) => sum + markers[i].originalX, 0) / cluster.length;
        const centerY = cluster.reduce((sum, i) => sum + markers[i].originalY, 0) / cluster.length;
        
        cluster.forEach((markerIndex, i) => {
            const angle = (2 * Math.PI * i) / cluster.length;
            markers[markerIndex].x = centerX + spreadRadius * Math.cos(angle);
            markers[markerIndex].y = centerY + spreadRadius * Math.sin(angle);
        });
    });
}

// Global helper functions for map coloring and status
function getColor(intensity) {
    if (intensity <= 25) return '#10b981';
    if (intensity <= 75) return '#22c55e';
    if (intensity <= 150) return '#eab308';
    return '#f97316';
}

// Removed duplicate getStatusBadge function - using the one at line 449 instead

function renderRegionMarkers() {
    console.log('📍 renderRegionMarkers called');
    console.log('g exists:', !!g);
    console.log('mapInitialized:', mapInitialized);
    
    // Check if map is properly initialized - only check g since mapInitialized might not be set yet during initial render
    if (!g) {
        console.log('⚠️ g not available, skipping marker rendering');
        return;
    }
    
    // Use synced real-time data from state.globalRegions (worldwide) if available
    let regionsData;
    if (state && state.globalRegions && state.globalRegions.length > 0) {
        // Use real-time synced worldwide data
        regionsData = state.globalRegions.map(region => ({
            ...region,
            region_code: region.region_code || region.name,
            datacenter_intensity: region.datacenter_intensity || region.intensity,
            lat: region.latitude || region.lat,
            lon: region.longitude || region.lon
        }));
        console.log('✅ Using real-time synced worldwide data:', regionsData.length, 'regions');
    } else {
        // Fallback to embedded data
        regionsData = window.GLOBAL_REGIONS_DATA || EMBEDDED_GLOBAL_REGIONS;
        console.log('⚠️ Using embedded static data:', regionsData ? regionsData.length + ' regions' : 'undefined');
    }
    
    if (!g) {
        console.error('❌ SVG group (g) not initialized');
        return;
    }
    
    if (!regionsData || regionsData.length === 0) {
        console.error('❌ No region data available');
        return;
    }
    
    console.log('✅ Rendering', regionsData.length, 'markers');
    
    // Add region name labels on country boundaries
    addRegionLabelsToCountries(regionsData);
    
    const tooltip = d3.select('#map-tooltip');
    
    // Detect overlapping markers and apply smart positioning
    const markerPositions = regionsData.map(d => {
        const lon = d.longitude || d.lon;
        const lat = d.latitude || d.lat;
        const coords = projection([lon, lat]);
        return {
            ...d,
            x: coords[0],
            y: coords[1],
            originalX: coords[0],
            originalY: coords[1]
        };
    });
    
    // Apply force simulation to spread overlapping markers
    applySpiderfy(markerPositions);
    
    // Add markers for each region with adjusted positions
    const markers = g.append('g')
        .attr('class', 'markers')
        .selectAll('g')
        .data(markerPositions)
        .enter()
        .append('g')
        .attr('class', 'marker-group')
        .attr('transform', d => `translate(${d.x}, ${d.y})`)
        .attr('data-region', d => d.region_code);
    
    // Add connection lines for spiderfied markers
    markers.each(function(d) {
        if (Math.abs(d.x - d.originalX) > 2 || Math.abs(d.y - d.originalY) > 2) {
            d3.select(this).append('line')
                .attr('x1', 0)
                .attr('y1', 0)
                .attr('x2', d.originalX - d.x)
                .attr('y2', d.originalY - d.y)
                .attr('stroke', '#999')
                .attr('stroke-width', 1)
                .attr('stroke-dasharray', '2,2')
                .attr('opacity', 0.5);
        }
    });
    
    // Add circles
    markers.append('circle')
        .attr('r', 12)
        .attr('fill', d => getColor(d.datacenter_intensity))
        .attr('stroke', '#ffffff')
        .attr('stroke-width', 2.5)
        .attr('opacity', 0.95)
        .style('cursor', 'pointer')
        .style('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))')
        .on('mouseover', function(event, d) {
            d3.select(this)
                .transition()
                .duration(200)
                .attr('r', 16);
            
            const renewablePct = Math.round(d.aws_renewable_pct * 100);
            const status = getStatusBadge(d.datacenter_intensity);
            
            tooltip
                .style('display', 'block')
                .style('left', (event.pageX + 15) + 'px')
                .style('top', (event.pageY - 15) + 'px')
                .html(`
                    <div style="font-weight: 700; font-size: 13px; margin-bottom: 2px; color: ${getColor(d.datacenter_intensity)};">${d.region_code}</div>
                    <div style="font-size: 11px; color: #ccc; margin-bottom: 8px;">${d.location}</div>
                    <div style="font-size: 20px; font-weight: 300; color: ${getColor(d.datacenter_intensity)};">
                        ${d.datacenter_intensity.toFixed(1)} <span style="font-size: 11px;">gCO₂/kWh</span>
                    </div>
                    <div style="margin-top: 6px; font-size: 11px;">
                        <span style="background: ${getColor(d.datacenter_intensity)}20; color: ${getColor(d.datacenter_intensity)}; padding: 2px 8px; border-radius: 8px; font-weight: 600;">${status.text}</span>
                    </div>
                    <div style="margin-top: 6px; font-size: 11px; color: #ccc;">⚡ ${renewablePct}% renewable</div>
                `);
        })
        .on('mouseout', function() {
            d3.select(this)
                .transition()
                .duration(200)
                .attr('r', 12);
            
            tooltip.style('display', 'none');
        })
        .on('click', function(event, d) {
            // Show HUD panel with region details
            showRegionHUD(d);
            
            // Optional: Zoom to region
            const lon = d.longitude || d.lon;
            const lat = d.latitude || d.lat;
            const coords = projection([lon, lat]);
            
            if (coords && !isNaN(coords[0]) && !isNaN(coords[1])) {
                const width = parseFloat(svg.attr('width'));
                const height = parseFloat(svg.attr('height'));
                
                svg.transition()
                    .duration(750)
                    .call(
                        zoom.transform,
                        d3.zoomIdentity
                            .translate(width / 2, height / 2)
                            .scale(3)
                            .translate(-coords[0], -coords[1])
                    );
            }
        });
    
    // Add text labels for intensity (inside circle)
    markers.append('text')
        .attr('dy', 4)
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('font-weight', '700')
        .attr('fill', '#ffffff')
        .attr('pointer-events', 'none')
        .style('text-shadow', '0 1px 2px rgba(0,0,0,0.5)')
        .text(d => Math.round(d.datacenter_intensity));
    
    // Add region code labels below markers
    markers.append('text')
        .attr('class', 'region-label')
        .attr('dy', 22)
        .attr('text-anchor', 'middle')
        .attr('font-size', '10px')
        .attr('font-weight', '700')
        .attr('fill', '#1f2937')
        .attr('pointer-events', 'none')
        .style('text-shadow', '0 0 4px white, 0 0 4px white, 0 0 4px white, 0 0 4px white')
        .style('opacity', 1)
        .text(d => d.region_code);
}

function zoomIn() {
    svg.transition().duration(300).call(zoom.scaleBy, 1.5);
}

function zoomOut() {
    svg.transition().duration(300).call(zoom.scaleBy, 0.67);
}

function switchView(view) {
    const mapContainer = document.getElementById('world-map-container');
    const gridContainer = document.getElementById('global-region-grid');
    const mapBtn = document.getElementById('map-view-btn');
    const gridBtn = document.getElementById('grid-view-btn');
    
    if (view === 'map') {
        mapContainer.style.display = 'block';
        gridContainer.style.display = 'none';
        mapBtn.classList.add('active');
        gridBtn.classList.remove('active');
        
        // Reinitialize map if needed
        if (!mapInitialized || !svg || svg.selectAll('*').empty()) {
            initWorldMap();
        }
    } else {
        mapContainer.style.display = 'none';
        gridContainer.style.display = 'grid';
        mapBtn.classList.remove('active');
        gridBtn.classList.add('active');
    }
}

// Initialize map when data is loaded
function initMapWhenReady() {
    console.log('🗺️ Checking if map data is ready...');
    console.log('EMBEDDED_GLOBAL_REGIONS available:', typeof EMBEDDED_GLOBAL_REGIONS !== 'undefined');
    
    if (typeof EMBEDDED_GLOBAL_REGIONS !== 'undefined' && EMBEDDED_GLOBAL_REGIONS.length > 0) {
        console.log('✅ Initializing map with', EMBEDDED_GLOBAL_REGIONS.length, 'regions');
        // Use EMBEDDED_GLOBAL_REGIONS directly
        window.GLOBAL_REGIONS_DATA = EMBEDDED_GLOBAL_REGIONS;
        initWorldMap();
    } else {
        console.log('⏳ Waiting for data...');
        setTimeout(initMapWhenReady, 500);
    }
}

window.addEventListener('load', () => {
    initMapWhenReady();
});

// Reinitialize map on window resize
let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        const mapContainer = document.getElementById('world-map-container');
        if (mapContainer && mapContainer.style.display !== 'none') {
            initWorldMap();
        }
    }, 250);
});

function refreshMapData() {
    console.log('🔄 Refreshing map with latest data...');
    // Check if map is initialized before trying to refresh
    if (mapInitialized && g && svg && !g.empty() && !svg.empty()) {
        try {
            // Remove existing markers
            g.selectAll('.markers').remove();
            // Re-render with updated data
            renderRegionMarkers();
        } catch (error) {
            console.warn('Map not ready for refresh:', error);
        }
    } else {
        console.log('Map not initialized yet, skipping refresh');
    }
}

// Expose functions globally
window.zoomIn = zoomIn;
window.zoomOut = zoomOut;
window.switchView = switchView;
window.refreshMapData = refreshMapData;


// ============================================
// Legend Filtering and Region Info
// ============================================

let activeFilter = 'all';

function getCategoryFromIntensity(intensity) {
    if (intensity <= 25) return 'excellent';
    if (intensity <= 75) return 'good';
    if (intensity <= 150) return 'moderate';
    return 'high';
}

function filterByCategory(category) {
    activeFilter = category;
    
    // Update legend item styling
    document.querySelectorAll('.legend-item-clickable').forEach(item => {
        const itemCategory = item.getAttribute('data-category');
        if (category === 'all' || itemCategory === category) {
            item.style.background = '#f3f4f6';
            item.style.fontWeight = '600';
        } else {
            item.style.background = 'transparent';
            item.style.fontWeight = '400';
            item.style.opacity = '0.5';
        }
    });
    
    // Filter markers
    if (!g) return;
    
    g.selectAll('.markers g').each(function(d) {
        const markerCategory = getCategoryFromIntensity(d.datacenter_intensity);
        const marker = d3.select(this);
        
        if (category === 'all' || markerCategory === category) {
            marker.style('opacity', 1);
            marker.style('pointer-events', 'auto');
        } else {
            marker.style('opacity', 0.15);
            marker.style('pointer-events', 'none');
        }
    });
    
    // Show region list for selected category
    if (category !== 'all') {
        showRegionList(category);
    } else {
        hideRegionList();
    }
}

function showRegionList(category) {
    const regionsData = window.GLOBAL_REGIONS_DATA || EMBEDDED_GLOBAL_REGIONS;
    if (!regionsData) return;
    
    // Filter regions by category
    const filteredRegions = regionsData.filter(r => 
        getCategoryFromIntensity(r.datacenter_intensity) === category
    ).sort((a, b) => a.datacenter_intensity - b.datacenter_intensity);
    
    // Create or update region list panel
    let panel = document.getElementById('region-list-panel');
    if (!panel) {
        panel = document.createElement('div');
        panel.id = 'region-list-panel';
        panel.style.cssText = `
            position: absolute;
            top: 80px;
            right: 20px;
            width: 320px;
            max-height: 500px;
            overflow-y: auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 999;
        `;
        document.getElementById('world-map-container').appendChild(panel);
    }
    
    const categoryNames = {
        excellent: 'Excellent Regions',
        good: 'Good Regions',
        moderate: 'Moderate Regions',
        high: 'High Carbon Regions'
    };
    
    const categoryColors = {
        excellent: '#10b981',
        good: '#22c55e',
        moderate: '#eab308',
        high: '#f97316'
    };
    
    panel.innerHTML = `
        <div style="padding: 16px; border-bottom: 1px solid #e5e5e5; background: ${categoryColors[category]}10;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h3 style="margin: 0; font-size: 14px; font-weight: 600; color: ${categoryColors[category]};">
                    ${categoryNames[category]}
                </h3>
                <button onclick="hideRegionList()" style="border: none; background: none; font-size: 20px; cursor: pointer; color: #666;">×</button>
            </div>
            <div style="font-size: 12px; color: #666; margin-top: 4px;">${filteredRegions.length} regions</div>
        </div>
        <div style="padding: 12px;">
            ${filteredRegions.map(region => `
                <div style="padding: 10px; margin-bottom: 8px; border: 1px solid #e5e5e5; border-radius: 6px; cursor: pointer; transition: all 0.2s;" 
                     onmouseover="this.style.background='#f9fafb'; this.style.borderColor='${categoryColors[category]}';"
                     onmouseout="this.style.background='white'; this.style.borderColor='#e5e5e5';"
                     onclick="zoomToRegion('${region.region_code}')">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <span style="font-weight: 600; font-size: 13px;">${region.region_code}</span>
                        <span style="font-size: 16px; font-weight: 300; color: ${categoryColors[category]};">${region.datacenter_intensity.toFixed(1)}</span>
                    </div>
                    <div style="font-size: 11px; color: #666;">${region.location}</div>
                    <div style="font-size: 10px; color: #999; margin-top: 4px;">⚡ ${Math.round(region.aws_renewable_pct * 100)}% renewable</div>
                </div>
            `).join('')}
        </div>
    `;
    
    panel.style.display = 'block';
}

function hideRegionList() {
    const panel = document.getElementById('region-list-panel');
    if (panel) {
        panel.style.display = 'none';
    }
    
    // Reset filter
    filterByCategory('all');
}

function zoomToRegion(regionCode) {
    const regionsData = window.GLOBAL_REGIONS_DATA || EMBEDDED_GLOBAL_REGIONS;
    const region = regionsData.find(r => r.region_code === regionCode);
    
    if (region && projection) {
        const lon = region.longitude || region.lon;
        const lat = region.latitude || region.lat;
        const coords = projection([lon, lat]);
        
        if (coords && !isNaN(coords[0]) && !isNaN(coords[1])) {
            const width = parseFloat(svg.attr('width'));
            const height = parseFloat(svg.attr('height'));
            
            svg.transition()
                .duration(750)
                .call(
                    zoom.transform,
                    d3.zoomIdentity
                        .translate(width / 2, height / 2)
                        .scale(5)
                        .translate(-coords[0], -coords[1])
                );
        }
    }
}

function updateLegendCounts() {
    const regionsData = window.GLOBAL_REGIONS_DATA || EMBEDDED_GLOBAL_REGIONS;
    if (!regionsData) return;
    
    const counts = {
        excellent: 0,
        good: 0,
        moderate: 0,
        high: 0
    };
    
    regionsData.forEach(region => {
        const category = getCategoryFromIntensity(region.datacenter_intensity);
        counts[category]++;
    });
    
    document.getElementById('count-excellent').textContent = counts.excellent;
    document.getElementById('count-good').textContent = counts.good;
    document.getElementById('count-moderate').textContent = counts.moderate;
    document.getElementById('count-high').textContent = counts.high;
}

// Update counts when map is initialized
window.addEventListener('load', () => {
    setTimeout(updateLegendCounts, 2000);
});

// Expose functions globally
window.filterByCategory = filterByCategory;
window.hideRegionList = hideRegionList;
window.zoomToRegion = zoomToRegion;


// ============================================
// Region HUD Panel Functions
// ============================================

function showRegionHUD(regionData) {
    const hud = document.getElementById('region-hud');
    if (!hud) return;
    
    // Populate HUD with region data
    document.getElementById('hud-flag').textContent = regionData.flag || '';
    document.getElementById('hud-region').textContent = regionData.region_code || regionData.name;
    document.getElementById('hud-location').textContent = regionData.location || '';
    
    // Carbon intensity with color
    const intensityBox = document.getElementById('hud-intensity-box');
    const intensity = regionData.datacenter_intensity || regionData.intensity;
    const color = getColor(intensity);
    document.getElementById('hud-intensity').textContent = intensity.toFixed(1);
    document.getElementById('hud-intensity').style.color = color;
    intensityBox.style.background = `${color}15`;
    intensityBox.style.border = `2px solid ${color}40`;
    
    // Grid carbon-free percentage (estimated: 100 - (intensity/500))
    // This estimates how much of the grid is carbon-free based on intensity
    // 500 gCO2/kWh is roughly coal-heavy grid, 0 is fully clean
    const gridIntensity = regionData.grid_intensity || intensity;
    const carbonFreePct = Math.max(0, Math.min(100, Math.round((1 - gridIntensity / 500) * 100)));
    document.getElementById('hud-carbon-free').textContent = carbonFreePct + '%';
    drawProgressRing('hud-carbon-free-ring', carbonFreePct, '#10b981');
    
    // AWS Renewable percentage (from AWS renewable energy purchases)
    const renewablePct = Math.round((regionData.aws_renewable_pct || 0) * 100);
    document.getElementById('hud-renewable').textContent = renewablePct + '%';
    drawProgressRing('hud-renewable-ring', renewablePct, '#3b82f6');
    
    // Status badge
    const status = getStatusBadge(intensity);
    const statusBadge = document.getElementById('hud-status-badge');
    statusBadge.textContent = status.text || status;
    statusBadge.style.background = `${color}20`;
    statusBadge.style.color = color;
    statusBadge.style.border = `1px solid ${color}40`;
    
    // Timestamp and source
    document.getElementById('hud-timestamp').textContent = 'Updated: ' + new Date().toLocaleTimeString();
    document.getElementById('hud-source').textContent = regionData.source || 'Real-time data';
    
    // Show HUD
    hud.style.display = 'block';
    
    // Draw connector line from HUD to pin
    drawHUDConnector(regionData);
}

function drawHUDConnector(regionData) {
    // Remove existing connector
    d3.select('#hud-connector').remove();
    
    if (!g || !projection) return;
    
    const lon = regionData.longitude || regionData.lon;
    const lat = regionData.latitude || regionData.lat;
    
    if (!lon || !lat) return;
    
    const coords = projection([lon, lat]);
    if (!coords || isNaN(coords[0]) || isNaN(coords[1])) return;
    
    // HUD panel position (right edge, middle)
    const hudX = 340; // 20px left + 320px width
    const hudY = 20 + 200; // 20px top + ~half height
    
    // Draw curved connector line
    const connector = g.append('g')
        .attr('id', 'hud-connector')
        .attr('class', 'hud-connector');
    
    // Create curved path
    const midX = (hudX + coords[0]) / 2;
    const midY = (hudY + coords[1]) / 2;
    
    const path = `M ${hudX} ${hudY} Q ${midX} ${midY - 50} ${coords[0]} ${coords[1]}`;
    
    connector.append('path')
        .attr('d', path)
        .attr('fill', 'none')
        .attr('stroke', getColor(regionData.datacenter_intensity || regionData.intensity))
        .attr('stroke-width', 2)
        .attr('stroke-dasharray', '5,5')
        .attr('opacity', 0.6)
        .attr('marker-end', 'url(#arrowhead)');
    
    // Add arrowhead marker definition if it doesn't exist
    if (svg.select('#arrowhead').empty()) {
        svg.append('defs')
            .append('marker')
            .attr('id', 'arrowhead')
            .attr('markerWidth', 10)
            .attr('markerHeight', 10)
            .attr('refX', 8)
            .attr('refY', 3)
            .attr('orient', 'auto')
            .append('polygon')
            .attr('points', '0 0, 10 3, 0 6')
            .attr('fill', getColor(regionData.datacenter_intensity || regionData.intensity));
    }
}

function closeRegionHUD() {
    const hud = document.getElementById('region-hud');
    if (hud) {
        hud.style.display = 'none';
    }
    // Remove connector line
    d3.select('#hud-connector').remove();
}

function drawProgressRing(svgId, percentage, color) {
    const svg = d3.select(`#${svgId}`);
    svg.selectAll('*').remove();
    
    const size = 60;
    const strokeWidth = 4;
    const radius = (size - strokeWidth) / 2;
    const circumference = 2 * Math.PI * radius;
    const progress = (percentage / 100) * circumference;
    
    const ringGroup = svg.append('g')
        .attr('transform', `translate(${size/2}, ${size/2})`);
    
    // Background circle
    ringGroup.append('circle')
        .attr('r', radius)
        .attr('fill', 'none')
        .attr('stroke', '#e5e7eb')
        .attr('stroke-width', strokeWidth);
    
    // Progress circle
    ringGroup.append('circle')
        .attr('r', radius)
        .attr('fill', 'none')
        .attr('stroke', color)
        .attr('stroke-width', strokeWidth)
        .attr('stroke-dasharray', `${progress} ${circumference}`)
        .attr('stroke-linecap', 'round')
        .attr('transform', 'rotate(-90)');
}

// ============================================
// Country Coloring Based on Carbon Intensity
// ============================================

function colorCountriesByIntensity() {
    if (!g || !state.globalRegions || state.globalRegions.length === 0) return;
    
    // Calculate average intensity per country
    const countryIntensities = {};
    state.globalRegions.forEach(region => {
        const country = region.country_code || region.country;
        if (!country) return;
        
        if (!countryIntensities[country]) {
            countryIntensities[country] = {
                total: 0,
                count: 0,
                regions: []
            };
        }
        
        countryIntensities[country].total += region.datacenter_intensity || region.intensity || 0;
        countryIntensities[country].count++;
        countryIntensities[country].regions.push(region);
    });
    
    // Calculate averages
    Object.keys(countryIntensities).forEach(country => {
        const data = countryIntensities[country];
        data.average = data.total / data.count;
    });
    
    // Color countries (this would require country code to map feature matching)
    // For now, we'll add a subtle overlay effect
    console.log('📊 Country intensity averages:', countryIntensities);
}


function getCountryColor(countryFeature) {
    // Get country code from feature properties
    const countryCode = countryFeature.properties?.iso_a2 || countryFeature.id;
    
    // Check if we have real-time region data for this country
    if (state && state.globalRegions && state.globalRegions.length > 0) {
        const countryRegions = state.globalRegions.filter(r => 
            (r.country === countryCode || r.country_code === countryCode)
        );
        
        if (countryRegions.length > 0) {
            // Calculate average intensity from actual region data
            const avgIntensity = countryRegions.reduce((sum, r) => 
                sum + (r.datacenter_intensity || r.intensity || 0), 0
            ) / countryRegions.length;
            
            // Return brighter colors for dark background
            if (avgIntensity <= 25) return '#10b981';
            if (avgIntensity <= 75) return '#22c55e';
            if (avgIntensity <= 150) return '#eab308';
            if (avgIntensity <= 300) return '#f97316';
            return '#ef4444';
        }
    }
    
    // Fallback: static mapping for countries without AWS regions
    const countryIntensityMap = {
        'SE': 30, 'NO': 20, 'FR': 60, 'CH': 50, 'FI': 100, 'AT': 120,
        'DK': 150, 'BE': 170, 'ES': 200, 'GB': 250, 'IT': 280, 'IE': 300,
        'NL': 350, 'DE': 380, 'PL': 600, 'CA': 150, 'US': 400, 'BR': 100,
        'JP': 450, 'KR': 500, 'CN': 550, 'IN': 600, 'AU': 650, 'SG': 400,
        'AE': 450, 'SA': 600, 'ZA': 850
    };
    
    const intensity = countryIntensityMap[countryCode];
    if (!intensity) return '#334155'; // Dark gray for unknown countries
    
    // Dimmer colors for non-AWS countries
    if (intensity <= 25) return '#10b98160';
    if (intensity <= 75) return '#22c55e60';
    if (intensity <= 150) return '#eab30860';
    if (intensity <= 300) return '#f9731660';
    return '#ef444460';
}

// Add region name labels directly on country boundaries
function addRegionLabelsToCountries(regionsData) {
    if (!g) return;
    
    // Don't add overlapping boxes - just enhance the existing country coloring
    // The region names will be shown via the pin markers and HUD
    console.log('📍 Region labels: Using pin markers for region identification');
}

// ============================================
// Collapsible Sections
// ============================================

function toggleSection(sectionId) {
    const section = document.getElementById(sectionId);
    const content = document.getElementById(sectionId + '-content');
    const collapseBtn = document.getElementById(sectionId + '-collapse-btn');
    const collapseIcon = collapseBtn?.querySelector('.collapse-icon');
    
    if (!section || !content) {
        console.error('Section or content not found:', sectionId);
        return;
    }
    
    const isCollapsed = section.classList.contains('collapsed');
    
    if (isCollapsed) {
        // Expand
        section.classList.remove('collapsed');
        content.classList.remove('collapsed');
        if (collapseIcon) collapseIcon.textContent = '−';
        
        // If this is the AWS regions section and worldwide tab is active, reinitialize map
        if (sectionId === 'aws-regions') {
            const worldwideTab = document.getElementById('worldwide-tab-content');
            const mapContainer = document.getElementById('world-map-container');
            if (worldwideTab && worldwideTab.classList.contains('active') && 
                mapContainer && mapContainer.style.display !== 'none') {
                // Small delay to ensure DOM is ready
                setTimeout(() => {
                    if (!mapInitialized || !svg || svg.selectAll('*').empty()) {
                        initWorldMap();
                    }
                }, 100);
            }
        }
    } else {
        // Collapse
        section.classList.add('collapsed');
        content.classList.add('collapsed');
        if (collapseIcon) collapseIcon.textContent = '+';
    }
}

function switchRegionTab(tabName) {
    // Update tab buttons
    const europeBtnEl = document.getElementById('europe-tab-btn');
    const worldwideBtnEl = document.getElementById('worldwide-tab-btn');
    
    // Update tab content
    const europeContentEl = document.getElementById('europe-tab-content');
    const worldwideContentEl = document.getElementById('worldwide-tab-content');
    
    if (tabName === 'europe') {
        // Activate Europe tab
        europeBtnEl.classList.add('active');
        worldwideBtnEl.classList.remove('active');
        europeContentEl.classList.add('active');
        worldwideContentEl.classList.remove('active');
    } else if (tabName === 'worldwide') {
        // Activate Worldwide tab
        europeBtnEl.classList.remove('active');
        worldwideBtnEl.classList.add('active');
        europeContentEl.classList.remove('active');
        worldwideContentEl.classList.add('active');
        
        // Initialize map if switching to worldwide tab and map view is active
        const mapContainer = document.getElementById('world-map-container');
        if (mapContainer && mapContainer.style.display !== 'none') {
            // Small delay to ensure DOM is ready
            setTimeout(() => {
                if (!mapInitialized || !svg || !svg.node() || svg.selectAll('*').empty()) {
                    initWorldMap();
                }
            }, 100);
        }
    }
}

function filterHistory() {
    const pipelineFilter = document.getElementById('pipeline-filter')?.value || 'all';
    const statusFilter = document.getElementById('status-filter')?.value || 'all';
    const regionFilter = document.getElementById('region-filter')?.value || 'all';
    
    // Use pipelineHistory or testHistory (whichever is available)
    const historyData = state.pipelineHistory || state.testHistory || [];
    if (!historyData || historyData.length === 0) return;
    
    let filteredTests = [...historyData];
    
    // Apply pipeline filter first (for metrics and chart)
    let pipelineFilteredTests = [...historyData];
    if (pipelineFilter !== 'all') {
        pipelineFilteredTests = pipelineFilteredTests.filter(test => 
            (test.pipeline_name || test.suite || 'Unknown') === pipelineFilter
        );
    }
    
    // Update metrics and trend chart with pipeline-filtered data
    renderHistoryMetrics(pipelineFilteredTests);
    renderTrendChart(historyData, pipelineFilter);
    
    // Apply all filters for the table
    if (statusFilter !== 'all') {
        filteredTests = filteredTests.filter(test => {
            const status = test.pipeline_status || test.status || 'unknown';
            if (statusFilter === 'optimized') return status === 'successful' || status === 'optimized';
            if (statusFilter === 'stable') return Math.abs(((test.carbon_g || test.carbon || 0) - 500) / 500) < 0.1;
            if (statusFilter === 'critical') return ((test.carbon_g || test.carbon || 0) - 500) / 500 > 0.2;
            return status === statusFilter;
        });
    }
    
    if (pipelineFilter !== 'all') {
        filteredTests = filteredTests.filter(test => 
            (test.pipeline_name || test.suite || 'Unknown') === pipelineFilter
        );
    }
    
    if (regionFilter !== 'all') {
        filteredTests = filteredTests.filter(test => 
            (test.optimal_region || test.region || 'eu-west-2') === regionFilter
        );
    }
    
    // Reset to first page when filtering
    state.pagination.currentPage = 1;
    
    // Re-render table with filtered data using pagination
    renderPipelineTable(filteredTests);
}

// Expose functions globally for onclick handlers
window.toggleSection = toggleSection;
window.switchRegionTab = switchRegionTab;
window.filterHistory = filterHistory;

// ============================================
// Trend Chart Pipeline Filter
// ============================================

function updateTrendChart() {
    const pipelineFilter = document.getElementById('trend-pipeline-filter')?.value || 'all';
    const historyData = state.pipelineHistory || state.testHistory || [];
    
    if (historyData.length > 0) {
        renderTrendChartAnimated(historyData, pipelineFilter);
    }
}

function populateTrendPipelineFilter(pipelines) {
    const trendFilter = document.getElementById('trend-pipeline-filter');
    if (!trendFilter || !pipelines) return;
    
    // Get unique pipeline names
    const uniquePipelines = [...new Set(pipelines.map(p => 
        p.pipeline_name || p.test_suite || p.suite || 'Unknown'
    ))].sort();
    
    // Clear existing options except "All Pipelines"
    trendFilter.innerHTML = '<option value="all">All Pipelines</option>';
    
    // Add unique pipeline names
    uniquePipelines.forEach(pipelineName => {
        const option = document.createElement('option');
        option.value = pipelineName;
        option.textContent = pipelineName;
        trendFilter.appendChild(option);
    });
    
    console.log(`📈 Populated trend chart filter with ${uniquePipelines.length} unique pipelines`);
}

// Enhanced smooth curve interpolation for trend chart
function drawStraightLines(ctx, points) {
    if (points.length < 2) return;
    
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    
    // Use straight lines for all connections
    for (let i = 1; i < points.length; i++) {
        ctx.lineTo(points[i].x, points[i].y);
    }
}

// Export functions
window.updateTrendChart = updateTrendChart;
window.populateTrendPipelineFilter = populateTrendPipelineFilter;

// ============================================
// Sync Pipeline Filters
// ============================================

function syncPipelineFilters(sourceFilterId, targetFilterId) {
    const sourceFilter = document.getElementById(sourceFilterId);
    const targetFilter = document.getElementById(targetFilterId);
    
    if (sourceFilter && targetFilter) {
        targetFilter.value = sourceFilter.value;
    }
}

// Enhanced filterHistory function to sync with trend chart
function filterHistoryAndSync() {
    // Get the current pipeline filter value
    const pipelineFilter = document.getElementById('pipeline-filter')?.value || 'all';
    
    // Sync with trend chart filter
    syncPipelineFilters('pipeline-filter', 'trend-pipeline-filter');
    
    // Update trend chart with new filter
    updateTrendChart();
    
    // Call original filter function
    filterHistory();
}

// Enhanced updateTrendChart to sync with table filter
function updateTrendChartAndSync() {
    // Get the current trend filter value
    const trendFilter = document.getElementById('trend-pipeline-filter')?.value || 'all';
    
    // Sync with table filter
    syncPipelineFilters('trend-pipeline-filter', 'pipeline-filter');
    
    // Update trend chart
    updateTrendChart();
    
    // Update table if needed
    if (document.getElementById('pipeline-filter')?.value !== trendFilter) {
        filterHistory();
    }
}

// Export enhanced functions
window.filterHistoryAndSync = filterHistoryAndSync;
window.updateTrendChartAndSync = updateTrendChartAndSync;