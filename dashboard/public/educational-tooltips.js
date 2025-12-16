/**
 * Educational Tooltips & Learning System
 * Beginner-friendly explanations for carbon emission concepts
 * 
 * This module provides contextual help and educational content
 * to help users understand green software concepts.
 */

// ============================================
// Educational Content Database
// ============================================

const EDUCATIONAL_CONTENT = {
    // Carbon Intensity Concepts
    carbonIntensity: {
        title: "What is Carbon Intensity?",
        short: "How much CO₂ is released per unit of electricity",
        detailed: `Carbon intensity measures the amount of carbon dioxide (CO₂) released 
        per kilowatt-hour (kWh) of electricity generated. Lower values mean cleaner energy.
        
        • 0-50 gCO₂/kWh: Very clean (nuclear, hydro, wind, solar)
        • 50-200 gCO₂/kWh: Moderate (mixed sources)
        • 200-500 gCO₂/kWh: High (natural gas)
        • 500+ gCO₂/kWh: Very high (coal)`,
        learnMore: "https://learn.greensoftware.foundation/carbon-awareness"
    },
    
    sci: {
        title: "Software Carbon Intensity (SCI)",
        short: "A metric to measure software's carbon footprint",
        detailed: `SCI = ((E × I) + M) per R
        
        Where:
        • E = Energy consumed by software (kWh)
        • I = Carbon intensity of electricity (gCO₂/kWh)
        • M = Embodied carbon of hardware (gCO₂)
        • R = Functional unit (e.g., per API call, per user)
        
        Lower SCI = More sustainable software`,
        learnMore: "https://sci.greensoftware.foundation/"
    },
    
    pue: {
        title: "Power Usage Effectiveness (PUE)",
        short: "Data center energy efficiency ratio",
        detailed: `PUE = Total Facility Energy / IT Equipment Energy
        
        • PUE 1.0 = Perfect efficiency (theoretical minimum)
        • PUE 1.15 = AWS (2024 Sustainability Report)
        • PUE 1.25 = Public cloud industry average
        • PUE 1.63 = On-premises enterprise data centers
        • PUE 2.0+ = Inefficient
        
        AWS PUE of 1.15 means only 15% overhead for cooling, lighting, etc.
        This is 8% better than industry average and 29% better than on-premises.`,
        learnMore: "https://sustainability.aboutamazon.com/2024-amazon-sustainability-report-aws-summary.pdf"
    },
    
    wue: {
        title: "Water Use Effectiveness (WUE)",
        short: "Data center water efficiency ratio",
        detailed: `WUE = Total Water Used / IT Equipment Energy (L/kWh)
        
        • AWS WUE: 0.15 L/kWh (2024)
        • 17% improvement from 2023
        • 40% improvement since 2021
        
        AWS uses innovative cooling technologies including:
        • Direct-to-chip liquid cooling for AI workloads
        • Direct evaporative cooling systems
        • Real-time water monitoring and leak detection
        
        AWS is committed to being water positive by 2030.`,
        learnMore: "https://sustainability.aboutamazon.com/2024-amazon-sustainability-report-aws-summary.pdf"
    },
    
    embodiedCarbon: {
        title: "Embodied Carbon",
        short: "Carbon emitted during hardware manufacturing",
        detailed: `Embodied carbon includes emissions from:
        
        • Mining raw materials
        • Manufacturing components
        • Assembly and testing
        • Transportation
        • End-of-life disposal
        
        For servers, this can be 20-40% of total lifecycle emissions.
        Using cloud resources efficiently reduces embodied carbon per workload.`,
        learnMore: "https://learn.greensoftware.foundation/hardware-efficiency"
    },
    
    gridMix: {
        title: "Energy Grid Mix",
        short: "The combination of energy sources powering the grid",
        detailed: `The grid mix shows what energy sources are generating electricity:
        
        🌬️ Wind - Zero carbon, variable
        ☀️ Solar - Zero carbon, daytime only
        💧 Hydro - Zero carbon, location dependent
        ⚛️ Nuclear - Very low carbon, constant
        🔥 Gas - Moderate carbon, flexible
        🪨 Coal - High carbon, being phased out
        
        Regions with more renewables have lower carbon intensity.`,
        learnMore: "https://app.electricitymaps.com/"
    },
    
    carbonAwareness: {
        title: "Carbon-Aware Computing",
        short: "Running workloads when and where energy is cleanest",
        detailed: `Carbon-aware computing optimizes when and where to run workloads:
        
        🕐 Time Shifting: Run jobs when carbon intensity is lowest
        🌍 Location Shifting: Run jobs in regions with cleaner energy
        📊 Demand Shaping: Adjust workload based on carbon signals
        
        This can reduce emissions by 30-50% without changing code!`,
        learnMore: "https://learn.greensoftware.foundation/carbon-awareness"
    },
    
    awsRegions: {
        title: "AWS Region Selection",
        short: "Different regions have different carbon footprints",
        detailed: `AWS regions vary significantly in carbon intensity:
        
        🟢 eu-north-1 (Stockholm): ~15 gCO₂/kWh - Hydro powered
        🟢 eu-west-3 (Paris): ~25 gCO₂/kWh - Nuclear powered
        🟡 eu-west-2 (London): ~150 gCO₂/kWh - Mixed grid
        🟠 eu-central-1 (Frankfurt): ~300 gCO₂/kWh - Coal/gas mix
        
        Choosing the right region can reduce emissions by 90%+`,
        learnMore: "https://sustainability.aboutamazon.com/2024-amazon-sustainability-report-aws-summary.pdf"
    },
    
    renewableEnergy: {
        title: "AWS Renewable Energy",
        short: "AWS matches 100% of electricity with renewable sources",
        detailed: `AWS achieved 100% renewable energy matching in 2024:
        
        • 100% of electricity matched with renewable sources (2024)
        • World's largest corporate purchaser of renewable energy since 2020
        • 302 utility-scale wind and solar projects globally
        • 621 renewable energy projects (34 GW capacity)
        
        Methods include:
        • Power Purchase Agreements (PPAs) with wind/solar farms
        • Battery energy storage systems
        • Nuclear energy (including Small Modular Reactors)
        
        The "AWS Renewable %" shows location-based renewable estimates.`,
        learnMore: "https://sustainability.aboutamazon.com/2024-amazon-sustainability-report-aws-summary.pdf"
    },
    
    graviton: {
        title: "AWS Graviton Chips",
        short: "Energy-efficient ARM-based processors",
        detailed: `Graviton chips deliver better performance with less energy:
        
        • Up to 60% less energy for same performance
        • 12,000 MTCO₂e reduction from customer adoption (2024)
        • 71,000 MTCO₂e reduction from Amazon's own adoption
        • Over 70,000 customers using Graviton chips
        
        Other efficient chips:
        • Inferentia2: 50% better performance/watt
        • Trainium3: 40% more energy efficient than Trainium2`,
        learnMore: "https://sustainability.aboutamazon.com/2024-amazon-sustainability-report-aws-summary.pdf"
    },
    
    forecast: {
        title: "Carbon Intensity Forecast",
        short: "Predicted carbon intensity for the next 24-48 hours",
        detailed: `Forecasts help you plan when to run workloads:
        
        📈 High intensity periods: Avoid running non-urgent jobs
        📉 Low intensity periods: Ideal for batch processing
        
        Forecasts are based on:
        • Weather predictions (wind, solar)
        • Demand patterns (time of day)
        • Scheduled maintenance
        • Historical data`,
        learnMore: "https://carbonintensity.org.uk/"
    },
    
    pipeline: {
        title: "CI/CD Pipeline",
        short: "Automated software build and deployment process",
        detailed: `A CI/CD pipeline automates:
        
        • Building code
        • Running tests
        • Deploying applications
        
        Each pipeline run consumes energy. By tracking carbon emissions
        per pipeline, you can optimize when and where to run builds.`,
        learnMore: "https://docs.aws.amazon.com/codepipeline/"
    },
    
    baseline: {
        title: "Carbon Baseline",
        short: "Average carbon emissions for comparison",
        detailed: `The baseline is calculated from your historical data:
        
        • Average of last 5-10 pipeline runs
        • Used to measure improvement
        • Helps identify anomalies
        
        Runs below baseline = Good (green)
        Runs above baseline = Needs attention (red)`,
        learnMore: null
    }
};

// ============================================
// Tooltip System
// ============================================

class EducationalTooltips {
    constructor() {
        this.activeTooltip = null;
        this.tooltipElement = null;
        this.init();
    }
    
    init() {
        // Create tooltip container
        this.tooltipElement = document.createElement('div');
        this.tooltipElement.className = 'edu-tooltip';
        this.tooltipElement.innerHTML = `
            <div class="edu-tooltip-header">
                <span class="edu-tooltip-title"></span>
                <button class="edu-tooltip-close" onclick="eduTooltips.hide()">×</button>
            </div>
            <div class="edu-tooltip-content">
                <p class="edu-tooltip-short"></p>
                <div class="edu-tooltip-detailed"></div>
                <a class="edu-tooltip-learn-more" target="_blank" rel="noopener">Learn more →</a>
            </div>
        `;
        document.body.appendChild(this.tooltipElement);
        
        // Add click outside to close
        document.addEventListener('click', (e) => {
            if (this.activeTooltip && !this.tooltipElement.contains(e.target) && 
                !e.target.classList.contains('edu-help-icon')) {
                this.hide();
            }
        });
        
        // Initialize help icons
        this.initHelpIcons();
    }
    
    initHelpIcons() {
        // Find all elements with data-edu attribute and add help icons
        document.querySelectorAll('[data-edu]').forEach(element => {
            const topic = element.getAttribute('data-edu');
            if (EDUCATIONAL_CONTENT[topic]) {
                const helpIcon = document.createElement('span');
                helpIcon.className = 'edu-help-icon';
                helpIcon.innerHTML = '?';
                helpIcon.setAttribute('data-topic', topic);
                helpIcon.onclick = (e) => {
                    e.stopPropagation();
                    this.show(topic, e.target);
                };
                element.appendChild(helpIcon);
            }
        });
    }
    
    show(topic, anchorElement) {
        const content = EDUCATIONAL_CONTENT[topic];
        if (!content) return;
        
        this.activeTooltip = topic;
        
        // Update content
        this.tooltipElement.querySelector('.edu-tooltip-title').textContent = content.title;
        this.tooltipElement.querySelector('.edu-tooltip-short').textContent = content.short;
        this.tooltipElement.querySelector('.edu-tooltip-detailed').innerHTML = 
            content.detailed.replace(/\n/g, '<br>');
        
        const learnMoreLink = this.tooltipElement.querySelector('.edu-tooltip-learn-more');
        if (content.learnMore) {
            learnMoreLink.href = content.learnMore;
            learnMoreLink.style.display = 'block';
        } else {
            learnMoreLink.style.display = 'none';
        }
        
        // Position tooltip
        const rect = anchorElement.getBoundingClientRect();
        const tooltipRect = this.tooltipElement.getBoundingClientRect();
        
        let left = rect.left + rect.width / 2 - 150;
        let top = rect.bottom + 10;
        
        // Keep within viewport
        if (left < 10) left = 10;
        if (left + 300 > window.innerWidth) left = window.innerWidth - 310;
        if (top + 200 > window.innerHeight) top = rect.top - 210;
        
        this.tooltipElement.style.left = `${left}px`;
        this.tooltipElement.style.top = `${top}px`;
        this.tooltipElement.classList.add('visible');
    }
    
    hide() {
        this.activeTooltip = null;
        this.tooltipElement.classList.remove('visible');
    }
}

// ============================================
// Onboarding Tour
// ============================================

class OnboardingTour {
    constructor() {
        this.currentStep = 0;
        this.steps = [
            {
                target: '#impact-summary',
                title: 'Welcome to ZeroCarb!',
                content: 'This dashboard helps you understand and reduce the carbon footprint of your cloud computing workloads.',
                position: 'bottom'
            },
            {
                target: '.insight-card-region-optimizer',
                title: 'Region Comparison',
                content: 'Different AWS regions have different carbon intensities. Choose cleaner regions to reduce emissions.',
                position: 'right'
            },
            {
                target: '.insight-card-optimal-time',
                title: 'Optimal Timing',
                content: 'Carbon intensity varies throughout the day. Schedule workloads when energy is cleanest.',
                position: 'left'
            },
            {
                target: '#region-grid',
                title: 'Live Carbon Data',
                content: 'Real-time carbon intensity from multiple data sources. Green = clean, Red = high emissions.',
                position: 'top'
            },
            {
                target: '#history',
                title: 'Pipeline History',
                content: 'Track your CI/CD pipeline emissions over time. See trends and identify optimization opportunities.',
                position: 'top'
            },
            {
                target: '#calculator',
                title: 'Carbon Calculator',
                content: 'Estimate the carbon footprint of your workloads before running them.',
                position: 'top'
            }
        ];
        this.overlay = null;
        this.spotlight = null;
        this.dialog = null;
    }
    
    start() {
        // Check if user has completed tour
        if (localStorage.getItem('zerocarb_tour_completed')) {
            return;
        }
        
        this.createOverlay();
        this.showStep(0);
    }
    
    createOverlay() {
        // Create overlay
        this.overlay = document.createElement('div');
        this.overlay.className = 'tour-overlay';
        
        // Create spotlight
        this.spotlight = document.createElement('div');
        this.spotlight.className = 'tour-spotlight';
        
        // Create dialog
        this.dialog = document.createElement('div');
        this.dialog.className = 'tour-dialog';
        this.dialog.innerHTML = `
            <div class="tour-dialog-header">
                <span class="tour-step-indicator"></span>
                <button class="tour-skip" onclick="onboardingTour.skip()">Skip Tour</button>
            </div>
            <h3 class="tour-title"></h3>
            <p class="tour-content"></p>
            <div class="tour-actions">
                <button class="tour-prev" onclick="onboardingTour.prev()">← Previous</button>
                <button class="tour-next" onclick="onboardingTour.next()">Next →</button>
            </div>
        `;
        
        document.body.appendChild(this.overlay);
        document.body.appendChild(this.spotlight);
        document.body.appendChild(this.dialog);
    }
    
    showStep(index) {
        if (index < 0 || index >= this.steps.length) {
            this.complete();
            return;
        }
        
        this.currentStep = index;
        const step = this.steps[index];
        const target = document.querySelector(step.target);
        
        if (!target) {
            this.next();
            return;
        }
        
        // Scroll target into view
        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        setTimeout(() => {
            // Position spotlight
            const rect = target.getBoundingClientRect();
            this.spotlight.style.left = `${rect.left - 10}px`;
            this.spotlight.style.top = `${rect.top - 10}px`;
            this.spotlight.style.width = `${rect.width + 20}px`;
            this.spotlight.style.height = `${rect.height + 20}px`;
            
            // Update dialog
            this.dialog.querySelector('.tour-step-indicator').textContent = 
                `Step ${index + 1} of ${this.steps.length}`;
            this.dialog.querySelector('.tour-title').textContent = step.title;
            this.dialog.querySelector('.tour-content').textContent = step.content;
            
            // Position dialog
            this.positionDialog(rect, step.position);
            
            // Update buttons
            this.dialog.querySelector('.tour-prev').style.display = index === 0 ? 'none' : 'block';
            this.dialog.querySelector('.tour-next').textContent = 
                index === this.steps.length - 1 ? 'Finish' : 'Next →';
        }, 300);
    }
    
    positionDialog(targetRect, position) {
        const dialogRect = this.dialog.getBoundingClientRect();
        let left, top;
        
        switch (position) {
            case 'bottom':
                left = targetRect.left + targetRect.width / 2 - dialogRect.width / 2;
                top = targetRect.bottom + 20;
                break;
            case 'top':
                left = targetRect.left + targetRect.width / 2 - dialogRect.width / 2;
                top = targetRect.top - dialogRect.height - 20;
                break;
            case 'left':
                left = targetRect.left - dialogRect.width - 20;
                top = targetRect.top + targetRect.height / 2 - dialogRect.height / 2;
                break;
            case 'right':
                left = targetRect.right + 20;
                top = targetRect.top + targetRect.height / 2 - dialogRect.height / 2;
                break;
        }
        
        // Keep within viewport
        left = Math.max(10, Math.min(left, window.innerWidth - dialogRect.width - 10));
        top = Math.max(10, Math.min(top, window.innerHeight - dialogRect.height - 10));
        
        this.dialog.style.left = `${left}px`;
        this.dialog.style.top = `${top}px`;
    }
    
    next() {
        this.showStep(this.currentStep + 1);
    }
    
    prev() {
        this.showStep(this.currentStep - 1);
    }
    
    skip() {
        this.complete();
    }
    
    complete() {
        localStorage.setItem('zerocarb_tour_completed', 'true');
        this.overlay?.remove();
        this.spotlight?.remove();
        this.dialog?.remove();
    }
    
    reset() {
        localStorage.removeItem('zerocarb_tour_completed');
    }
}

// ============================================
// Quick Tips System
// ============================================

const QUICK_TIPS = [
    {
        icon: '💡',
        tip: 'Stockholm (eu-north-1) typically has the lowest carbon intensity due to hydroelectric power.',
        category: 'regions'
    },
    {
        icon: '🕐',
        tip: 'Run batch jobs during off-peak hours (night/early morning) when renewable energy is often higher.',
        category: 'timing'
    },
    {
        icon: '📊',
        tip: 'The SCI (Software Carbon Intensity) metric helps you compare the carbon efficiency of different software.',
        category: 'metrics'
    },
    {
        icon: '🌍',
        tip: 'Moving workloads to a cleaner region can reduce emissions by up to 90%.',
        category: 'regions'
    },
    {
        icon: '⚡',
        tip: 'AWS PUE of 1.15 (2024) means 15% of energy goes to cooling and infrastructure.',
        category: 'efficiency'
    },
    {
        icon: '🔋',
        tip: 'Embodied carbon (hardware manufacturing) can be 20-40% of total emissions.',
        category: 'metrics'
    },
    {
        icon: '🌬️',
        tip: 'Wind power is variable - carbon intensity often drops on windy days.',
        category: 'timing'
    },
    {
        icon: '☀️',
        tip: 'Solar power peaks at midday - some regions are cleanest during sunny afternoons.',
        category: 'timing'
    }
];

function showRandomTip() {
    const tip = QUICK_TIPS[Math.floor(Math.random() * QUICK_TIPS.length)];
    const tipContainer = document.getElementById('quick-tip');
    if (tipContainer) {
        tipContainer.innerHTML = `
            <span class="tip-icon">${tip.icon}</span>
            <span class="tip-text">${tip.tip}</span>
        `;
    }
}

// ============================================
// Initialize Educational Features
// ============================================

let eduTooltips;
let onboardingTour;

document.addEventListener('DOMContentLoaded', () => {
    // Initialize tooltips
    eduTooltips = new EducationalTooltips();
    
    // Initialize onboarding tour
    onboardingTour = new OnboardingTour();
    
    // Show random tip
    showRandomTip();
    setInterval(showRandomTip, 30000); // Change tip every 30 seconds
    
    // Start tour for new users (after a short delay)
    setTimeout(() => {
        onboardingTour.start();
    }, 2000);
});

// Export for global access
window.eduTooltips = eduTooltips;
window.onboardingTour = onboardingTour;
window.EDUCATIONAL_CONTENT = EDUCATIONAL_CONTENT;


// ============================================
// Glossary Panel Functions
// ============================================

function openGlossary() {
    const panel = document.getElementById('glossary-panel');
    if (panel) {
        panel.classList.add('open');
        populateGlossary();
    }
}

function closeGlossary() {
    const panel = document.getElementById('glossary-panel');
    if (panel) {
        panel.classList.remove('open');
    }
}

function populateGlossary() {
    const content = document.getElementById('glossary-content');
    if (!content) return;
    
    const sortedTerms = Object.entries(EDUCATIONAL_CONTENT)
        .sort((a, b) => a[1].title.localeCompare(b[1].title));
    
    content.innerHTML = sortedTerms.map(([key, term]) => `
        <div class="glossary-item" onclick="showGlossaryDetail('${key}')">
            <div class="glossary-item-title">${term.title}</div>
            <div class="glossary-item-short">${term.short}</div>
        </div>
    `).join('');
}

function filterGlossary(query) {
    const content = document.getElementById('glossary-content');
    if (!content) return;
    
    const lowerQuery = query.toLowerCase();
    
    const filteredTerms = Object.entries(EDUCATIONAL_CONTENT)
        .filter(([key, term]) => 
            term.title.toLowerCase().includes(lowerQuery) ||
            term.short.toLowerCase().includes(lowerQuery) ||
            term.detailed.toLowerCase().includes(lowerQuery)
        )
        .sort((a, b) => a[1].title.localeCompare(b[1].title));
    
    if (filteredTerms.length === 0) {
        content.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #64748b;">
                No terms found matching "${query}"
            </div>
        `;
        return;
    }
    
    content.innerHTML = filteredTerms.map(([key, term]) => `
        <div class="glossary-item" onclick="showGlossaryDetail('${key}')">
            <div class="glossary-item-title">${term.title}</div>
            <div class="glossary-item-short">${term.short}</div>
        </div>
    `).join('');
}

function showGlossaryDetail(key) {
    const term = EDUCATIONAL_CONTENT[key];
    if (!term) return;
    
    // Show detailed view in the glossary panel
    const content = document.getElementById('glossary-content');
    if (!content) return;
    
    content.innerHTML = `
        <div class="glossary-detail">
            <button class="glossary-back" onclick="populateGlossary()">← Back to list</button>
            <h3 class="glossary-detail-title">${term.title}</h3>
            <p class="glossary-detail-short">${term.short}</p>
            <div class="glossary-detail-content">${term.detailed.replace(/\n/g, '<br>')}</div>
            ${term.learnMore ? `<a href="${term.learnMore}" target="_blank" class="glossary-learn-more">Learn more →</a>` : ''}
        </div>
    `;
    if (eduTooltips) {
        const glossaryItem = document.querySelector(`[onclick="showGlossaryDetail('${key}')"]`);
        if (glossaryItem) {
            eduTooltips.show(key, glossaryItem);
        }
    }
}

// ============================================
// Beginner Mode Toggle
// ============================================

let beginnerModeEnabled = localStorage.getItem('zerocarb_beginner_mode') !== 'false';

function toggleBeginnerMode() {
    beginnerModeEnabled = !beginnerModeEnabled;
    localStorage.setItem('zerocarb_beginner_mode', beginnerModeEnabled);
    
    const toggle = document.getElementById('beginner-mode-toggle');
    if (toggle) {
        toggle.classList.toggle('active', beginnerModeEnabled);
    }
    
    // Show/hide educational elements
    document.querySelectorAll('.edu-help-icon').forEach(icon => {
        icon.style.display = beginnerModeEnabled ? 'inline-flex' : 'none';
    });
    
    document.querySelectorAll('.quick-tip-container').forEach(tip => {
        tip.style.display = beginnerModeEnabled ? 'flex' : 'none';
    });
    
    // Show notification
    showNotification(
        beginnerModeEnabled ? 
            '📚 Learning mode enabled - hover over ? icons for explanations' :
            '📚 Learning mode disabled'
    );
}

function showNotification(message) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: #1f2937;
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        font-size: 14px;
        z-index: 10001;
        animation: slideUp 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Add animation styles
const notificationStyles = document.createElement('style');
notificationStyles.textContent = `
    @keyframes slideUp {
        from { opacity: 0; transform: translateX(-50%) translateY(20px); }
        to { opacity: 1; transform: translateX(-50%) translateY(0); }
    }
    @keyframes fadeOut {
        from { opacity: 1; }
        to { opacity: 0; }
    }
`;
document.head.appendChild(notificationStyles);

// Initialize beginner mode state on load
document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('beginner-mode-toggle');
    if (toggle && beginnerModeEnabled) {
        toggle.classList.add('active');
    }
});

// Export functions
window.openGlossary = openGlossary;
window.closeGlossary = closeGlossary;
window.filterGlossary = filterGlossary;
window.showGlossaryDetail = showGlossaryDetail;
window.toggleBeginnerMode = toggleBeginnerMode;
