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
    },
    
    // CO₂ Equivalents - Educational content for Impact Summary
    carbonEquivalents: {
        title: "Understanding CO₂ Equivalents",
        short: "Real-world comparisons to help visualize carbon emissions",
        detailed: `CO₂ equivalents help you understand abstract carbon numbers by comparing them to everyday activities.

        🚗 CAR DRIVING EQUIVALENT
        Formula: km = kg CO₂ ÷ 0.2
        • An average car emits ~200g CO₂ per km (0.2 kg/km)
        • Example: 0.6 kg CO₂ = 3 km of driving
        
        🌳 TREE ABSORPTION EQUIVALENT  
        Formula: tree-days = (kg CO₂ ÷ 20) × 365
        • A mature tree absorbs ~20 kg CO₂ per year
        • Example: 0.6 kg CO₂ = ~11 tree-days
        
        ⚠️ IMPORTANT DISCLAIMER
        These equivalents are illustrative only and should not be used for formal GHG inventories or carbon offsets. Emissions are calculated in accordance with GHG Protocol / ISO 14064 standards. Equivalents use factors from EPA, DEFRA, and EEA/ICCT.`,
        learnMore: "https://www.epa.gov/energy/greenhouse-gas-equivalencies-calculator"
    },
    
    carEquivalent: {
        title: "Car Driving Equivalent",
        short: "How far a car would drive to emit the same CO₂",
        detailed: `🚗 CAR DRIVING FORMULA
        
        km = kg CO₂ ÷ 0.2 kg/km
        
        This assumes an average petrol car emitting 200g CO₂ per km.
        
        Examples:
        • 0.1 kg CO₂ = 0.5 km (500 meters)
        • 0.6 kg CO₂ = 3 km
        • 1.0 kg CO₂ = 5 km
        • 10 kg CO₂ = 50 km
        
        Regional variations:
        • EU new cars average: ~106 g/km
        • US fleet average: ~250 g/km
        • We use 200 g/km as a global average.`,
        learnMore: "https://www.eea.europa.eu/en/topics/in-depth/transport-and-mobility"
    },
    
    treeEquivalent: {
        title: "Tree Absorption Equivalent",
        short: "How long a tree would need to absorb this CO₂",
        detailed: `🌳 TREE ABSORPTION FORMULA
        
        tree-days = (kg CO₂ ÷ 20) × 365
        
        This assumes a mature temperate tree absorbs ~20 kg CO₂ per year.
        
        Examples:
        • 0.1 kg CO₂ = ~2 tree-days
        • 0.6 kg CO₂ = ~11 tree-days
        • 1.0 kg CO₂ = ~18 tree-days
        • 20 kg CO₂ = 1 tree-year
        
        Note: Actual absorption varies by:
        • Tree species (oak vs pine vs tropical)
        • Tree age (young trees absorb less)
        • Climate and growing conditions`,
        learnMore: "https://www.usda.gov/media/blog/2015/03/17/power-one-tree-very-air-we-breathe"
    },

    // ============================================
    // FUNDAMENTALS - Beginner-friendly explanations
    // ============================================
    
    carbon: {
        title: "What is Carbon (CO₂)?",
        short: "The main greenhouse gas causing climate change",
        detailed: `Carbon dioxide (CO₂) is like a blanket around Earth that traps heat.

        🌍 THE BASICS
        • CO₂ is released when we burn fossil fuels (coal, oil, gas)
        • Power plants, cars, and factories all release CO₂
        • Data centers use electricity, which often comes from fossil fuels
        
        💡 WHY IT MATTERS FOR SOFTWARE
        • Every line of code you run uses electricity
        • That electricity often comes from burning fossil fuels
        • More efficient code = less electricity = less CO₂
        
        Think of it like this: Running your code is like driving a car. 
        The more you drive, the more fuel you burn, the more CO₂ you emit.`,
        learnMore: "https://learn.greensoftware.foundation/carbon-efficiency"
    },

    emissions: {
        title: "What are Emissions?",
        short: "Greenhouse gases released into the atmosphere",
        detailed: `Emissions are gases released into the air that contribute to climate change.

        🏭 TYPES OF GREENHOUSE GASES
        • CO₂ (Carbon Dioxide) - From burning fuels, ~76% of emissions
        • CH₄ (Methane) - From agriculture, landfills, ~16% of emissions
        • N₂O (Nitrous Oxide) - From fertilizers, ~6% of emissions
        • F-gases - From refrigerants, ~2% of emissions
        
        📊 IN SOFTWARE TERMS
        When we talk about "carbon emissions" from software, we mean:
        • The CO₂ released by power plants to generate electricity
        • That electricity powers the servers running your code
        
        We measure emissions in grams (g) or kilograms (kg) of CO₂.`,
        learnMore: "https://learn.greensoftware.foundation/carbon-efficiency"
    },

    ghgProtocol: {
        title: "GHG Protocol",
        short: "The global standard for measuring carbon emissions",
        detailed: `The GHG Protocol is like a rulebook for counting carbon emissions.

        📏 WHAT IT DOES
        • Provides standard methods to measure emissions
        • Used by 92% of Fortune 500 companies
        • Created by World Resources Institute & WBCSD
        
        🎯 THE THREE SCOPES
        • Scope 1: Direct emissions (your own fuel burning)
        • Scope 2: Electricity emissions (power you buy)
        • Scope 3: Everything else (supply chain, travel, etc.)
        
        💻 FOR SOFTWARE
        Your cloud computing falls under Scope 2 (electricity) and 
        Scope 3 (cloud provider's infrastructure).`,
        learnMore: "https://ghgprotocol.org/"
    },

    scope1: {
        title: "Scope 1 Emissions",
        short: "Direct emissions from sources you own or control",
        detailed: `Scope 1 = Emissions from things YOU directly burn or release.

        🔥 EXAMPLES
        • Company vehicles burning petrol/diesel
        • On-site generators burning fuel
        • Gas boilers heating your office
        • Refrigerant leaks from AC units
        
        💻 FOR MOST SOFTWARE COMPANIES
        Scope 1 is usually small because you don't burn much fuel directly.
        Most of your emissions come from Scope 2 (electricity) and Scope 3 (cloud).`,
        learnMore: "https://ghgprotocol.org/scope-1-and-scope-2-inventory-guidance"
    },

    scope2: {
        title: "Scope 2 Emissions",
        short: "Indirect emissions from purchased electricity",
        detailed: `Scope 2 = Emissions from the electricity you buy.

        ⚡ HOW IT WORKS
        • You buy electricity from the grid
        • Power plants generate that electricity
        • Those plants may burn coal, gas, or use renewables
        • The emissions from generation are your Scope 2
        
        💻 FOR SOFTWARE
        • Running servers in your office = Scope 2
        • Your office lights and AC = Scope 2
        • Cloud computing is usually Scope 3 (it's the cloud provider's Scope 2)
        
        📊 TWO WAYS TO MEASURE
        • Location-based: Average grid emissions where you are
        • Market-based: Based on your energy contracts/RECs`,
        learnMore: "https://ghgprotocol.org/scope-1-and-scope-2-inventory-guidance"
    },

    scope3: {
        title: "Scope 3 Emissions",
        short: "All other indirect emissions in your value chain",
        detailed: `Scope 3 = Everything else not in Scope 1 or 2.

        🌐 THIS IS THE BIG ONE
        Scope 3 is typically 70-90% of a company's total emissions!
        
        📦 EXAMPLES
        • Cloud computing (AWS, Azure, GCP)
        • Business travel
        • Employee commuting
        • Purchased goods and services
        • Product use by customers
        • Waste disposal
        
        💻 FOR SOFTWARE COMPANIES
        Your cloud infrastructure is Scope 3 - it's the cloud provider's 
        Scope 1 & 2, but YOUR Scope 3.
        
        This dashboard helps you reduce your Scope 3 cloud emissions!`,
        learnMore: "https://ghgprotocol.org/scope-3-calculation-guidance"
    },

    energy: {
        title: "Energy (kWh)",
        short: "The electricity consumed, measured in kilowatt-hours",
        detailed: `Energy is measured in kilowatt-hours (kWh) - think of it as "electricity units".

        💡 WHAT IS A kWh?
        • 1 kWh = running a 1000W appliance for 1 hour
        • A laptop uses about 50W, so 20 hours = 1 kWh
        • A server might use 200-500W continuously
        
        🔌 EXAMPLES
        • Charging your phone: ~0.01 kWh
        • Running a laptop for 1 hour: ~0.05 kWh
        • Running a CI/CD pipeline: ~0.1-1 kWh
        • Training an AI model: 100-1000+ kWh
        
        📊 THE FORMULA
        Carbon = Energy (kWh) × Carbon Intensity (gCO₂/kWh)
        
        Less energy = less carbon (always)
        Same energy + cleaner grid = less carbon`,
        learnMore: "https://learn.greensoftware.foundation/energy-efficiency"
    },

    carbonFactors: {
        title: "Carbon Emission Factors",
        short: "Conversion rates from energy to carbon emissions",
        detailed: `Emission factors tell you how much CO₂ is released per unit of energy.

        📊 THE KEY FORMULA
        Carbon (g) = Energy (kWh) × Emission Factor (gCO₂/kWh)
        
        🌍 EXAMPLE FACTORS BY REGION
        • Sweden: ~20 gCO₂/kWh (mostly hydro/nuclear)
        • France: ~50 gCO₂/kWh (mostly nuclear)
        • UK: ~200 gCO₂/kWh (mixed)
        • Germany: ~350 gCO₂/kWh (coal/gas)
        • Poland: ~700 gCO₂/kWh (coal heavy)
        
        🏢 AWS DATACENTER ADJUSTMENT
        We also factor in:
        • PUE (1.15) - datacenter overhead
        • AWS renewable energy purchases
        
        Final = Grid Intensity × (1 - Renewable%) × PUE`,
        learnMore: "https://www.cloudcarbonfootprint.org/docs/methodology"
    },

    awsEfficiency: {
        title: "AWS Data Center Efficiency",
        short: "Why cloud is greener than on-premises",
        detailed: `AWS data centers are much more efficient than typical corporate data centers.

        📊 THE NUMBERS (2024)
        • AWS PUE: 1.15 (only 15% overhead)
        • Industry average: 1.25
        • On-premises: 1.63
        
        🌱 WHY AWS IS GREENER
        • 100% renewable energy matching (2024)
        • Custom efficient chips (Graviton, Inferentia)
        • Advanced cooling systems
        • Higher server utilization (less waste)
        • Continuous efficiency improvements
        
        💡 THE RESULT
        AWS estimates customers can reduce carbon footprint by up to 
        80% compared to running the same workloads on-premises.`,
        learnMore: "https://sustainability.aboutamazon.com/2024-amazon-sustainability-report-aws-summary.pdf"
    },

    netZero: {
        title: "Net Zero",
        short: "Balancing emissions with removals to reach zero",
        detailed: `Net Zero means removing as much CO₂ as you emit.

        ⚖️ THE CONCEPT
        Emissions Released - Emissions Removed = 0
        
        🎯 HOW TO GET THERE
        1. Reduce emissions as much as possible (efficiency)
        2. Switch to renewable energy
        3. Offset remaining emissions (carbon credits)
        4. Invest in carbon removal (trees, technology)
        
        🌍 AMAZON'S COMMITMENT
        • Net-zero carbon by 2040 (10 years ahead of Paris Agreement)
        • 100% renewable energy by 2025 ✓ (achieved early!)
        • Climate Pledge signed by 500+ companies`,
        learnMore: "https://sustainability.aboutamazon.com/climate-pledge"
    },

    co2e: {
        title: "CO₂ Equivalent (CO₂e)",
        short: "A standard unit for comparing different greenhouse gases",
        detailed: `CO₂e lets us compare different greenhouse gases on the same scale.

        🔄 WHY WE NEED IT
        Different gases trap different amounts of heat:
        • CO₂ = 1x (baseline)
        • Methane (CH₄) = 28x more potent
        • Nitrous Oxide (N₂O) = 265x more potent
        • Some F-gases = 23,000x more potent!
        
        📊 THE CONVERSION
        CO₂e = Amount of gas × Global Warming Potential (GWP)
        
        Example: 1 kg of methane = 28 kg CO₂e
        
        💻 FOR THIS DASHBOARD
        We primarily track CO₂ from electricity, so CO₂ ≈ CO₂e.
        The "e" reminds us we're using a standardized measure.`,
        learnMore: "https://learn.greensoftware.foundation/carbon-efficiency"
    },

    functionalUnit: {
        title: "Functional Unit (R in SCI)",
        short: "What you measure carbon emissions per",
        detailed: `The functional unit is the "per what" in your carbon measurement.

        📏 THE SCI FORMULA
        SCI = ((E × I) + M) per R
        
        R = Your functional unit
        
        🎯 EXAMPLES
        • Per API call
        • Per user
        • Per transaction
        • Per pipeline run
        • Per 1000 requests
        
        💡 WHY IT MATTERS
        Without a functional unit, you can't compare:
        • Is 100g CO₂ good or bad?
        • It depends! Per user? Per million requests?
        
        This dashboard uses "per pipeline run" as the functional unit.`,
        learnMore: "https://sci.greensoftware.foundation/"
    },

    greenSoftwareFoundation: {
        title: "Green Software Foundation",
        short: "The organization behind green software standards",
        detailed: `The Green Software Foundation (GSF) creates standards for sustainable software.

        🏛️ WHO THEY ARE
        • Non-profit under Linux Foundation
        • Founded by Microsoft, GitHub, Accenture, Thoughtworks
        • Members include AWS, Google, Intel, and 40+ organizations
        
        📚 WHAT THEY DO
        • Created the SCI specification
        • Publish green software patterns
        • Provide free training and certification
        • Build open-source tools
        
        🎓 FREE RESOURCES
        • Green Software Practitioner certification
        • Carbon Aware SDK
        • Impact Framework`,
        learnMore: "https://greensoftware.foundation/"
    },

    marginalEmissions: {
        title: "Marginal vs Average Emissions",
        short: "Two ways to measure grid carbon intensity",
        detailed: `There are two ways to calculate carbon intensity - and they give different answers!

        📊 AVERAGE EMISSIONS
        Total grid emissions ÷ Total electricity generated
        • Simpler to calculate
        • Good for reporting
        • Used by most carbon calculators
        
        📈 MARGINAL EMISSIONS
        Emissions from the NEXT unit of electricity
        • More accurate for decision-making
        • Shows impact of your specific demand
        • Usually higher than average
        
        💡 WHICH TO USE?
        • For reporting: Average (location-based)
        • For optimization: Marginal (shows real impact)
        
        This dashboard uses average intensity for simplicity.`,
        learnMore: "https://www.electricitymaps.com/blog/marginal-vs-average-real-time-decision-making"
    },

    carbonBudget: {
        title: "Carbon Budget",
        short: "The total CO₂ we can emit to limit warming",
        detailed: `The carbon budget is like a global "spending limit" for CO₂.

        🌡️ THE SCIENCE
        To limit warming to 1.5°C, we can only emit ~400 billion more tonnes of CO₂.
        At current rates, we'll use this up in about 10 years.
        
        📊 WHAT THIS MEANS
        • Every tonne of CO₂ matters
        • We need to reduce emissions by ~50% by 2030
        • Net zero by 2050 is essential
        
        💻 FOR SOFTWARE
        The tech sector is ~2-4% of global emissions (similar to aviation).
        As software grows, so does its share of the carbon budget.
        
        Every optimization you make helps preserve the budget!`,
        learnMore: "https://www.ipcc.ch/sr15/"
    },

    vcpu: {
        title: "vCPU (Virtual CPU)",
        short: "A share of a physical processor in the cloud",
        detailed: `A vCPU is a portion of a real CPU that's allocated to your workload.

        💻 HOW IT WORKS
        • Physical servers have multiple CPU cores
        • Cloud providers divide these into vCPUs
        • You rent vCPUs, not whole servers
        
        ⚡ ENERGY IMPACT
        More vCPUs = More energy = More carbon
        
        📊 TYPICAL POWER USAGE
        • 1 vCPU at 100% ≈ 5-10 watts
        • Idle vCPU ≈ 1-2 watts
        • Depends on chip type (Graviton is more efficient!)
        
        💡 OPTIMIZATION TIP
        Right-size your instances! Using 8 vCPUs when you need 2 
        wastes energy and money.`,
        learnMore: "https://www.cloudcarbonfootprint.org/docs/methodology"
    },

    tdp: {
        title: "TDP (Thermal Design Power)",
        short: "Maximum power a processor can use",
        detailed: `TDP tells you the maximum watts a chip will consume.

        🔌 WHAT IT MEANS
        • TDP 100W = chip can use up to 100 watts
        • Used for cooling system design
        • Actual usage is usually lower
        
        📊 EXAMPLE TDPs
        • Intel Xeon (server): 150-250W
        • AMD EPYC (server): 120-280W
        • AWS Graviton3: ~100W (estimated)
        • Laptop CPU: 15-45W
        
        💡 FOR CARBON CALCULATIONS
        We use TDP to estimate energy consumption:
        Energy = TDP × Utilization × Time
        
        Lower TDP chips (like Graviton) = less energy = less carbon`,
        learnMore: "https://www.cloudcarbonfootprint.org/docs/methodology"
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
        
        // Position tooltip with better viewport handling
        const rect = anchorElement.getBoundingClientRect();
        const tooltipWidth = 340;
        const tooltipMaxHeight = window.innerHeight * 0.8;
        const padding = 20;
        
        // Calculate horizontal position (center on anchor, but keep in viewport)
        let left = rect.left + rect.width / 2 - tooltipWidth / 2;
        if (left < padding) left = padding;
        if (left + tooltipWidth > window.innerWidth - padding) {
            left = window.innerWidth - tooltipWidth - padding;
        }
        
        // Calculate vertical position (prefer below, but flip if needed)
        let top = rect.bottom + 10;
        const spaceBelow = window.innerHeight - rect.bottom - padding;
        const spaceAbove = rect.top - padding;
        
        // If not enough space below and more space above, position above
        if (spaceBelow < 200 && spaceAbove > spaceBelow) {
            top = Math.max(padding, rect.top - Math.min(tooltipMaxHeight, spaceAbove) - 10);
        } else {
            // Ensure tooltip doesn't go below viewport
            top = Math.min(top, window.innerHeight - tooltipMaxHeight - padding);
        }
        
        // Ensure top is never negative
        top = Math.max(padding, top);
        
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
