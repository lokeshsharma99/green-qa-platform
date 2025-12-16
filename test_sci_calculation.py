"""
Test SCI Calculation with Dummy Workload Data + Real Carbon Intensity APIs

Dummy inputs: AWS region, duration, vCPU count, memory
Real data: Carbon intensity from UK Carbon Intensity API / fallback sources

GSF SCI Formula: SCI = ((E × I) + M) / R
- E = Energy (kWh)
- I = Carbon Intensity (gCO2/kWh) - FROM REAL API
- M = Embodied Emissions (gCO2)
- R = Functional Unit
"""

import json
from urllib.request import urlopen, Request
from datetime import datetime

# ============================================================================
# CONSTANTS (from Cloud Carbon Footprint methodology)
# ============================================================================

CLOUD_PUE = {'aws': 1.15, 'gcp': 1.1, 'azure': 1.185}  # AWS 2024 Sustainability Report
VCPU_TDP_WATTS = 10.0  # Watts per vCPU (Intel Xeon default)
MEMORY_COEFFICIENT_KWH_PER_GB = 0.000392  # kWh per GB-hour
EMBODIED_EMISSIONS_G_PER_VCPU_HOUR = 2.5  # gCO2 per vCPU-hour

# Fallback carbon intensity values (gCO2/kWh)
FALLBACK_INTENSITY = {
    'eu-west-2': 250,    # UK
    'eu-north-1': 30,    # Sweden
    'eu-west-1': 300,    # Ireland
    'eu-west-3': 60,     # France
    'eu-central-1': 380, # Germany
    'us-east-1': 420,    # Virginia
    'us-west-2': 280,    # Oregon
}

# ============================================================================
# REAL API: UK Carbon Intensity (FREE, NO AUTH)
# ============================================================================

def get_real_carbon_intensity(region: str) -> dict:
    """Fetch real carbon intensity from UK Carbon Intensity API or use fallback."""
    
    # UK regions use the free UK Carbon Intensity API
    if region == 'eu-west-2':
        try:
            req = Request(
                'https://api.carbonintensity.org.uk/intensity',
                headers={'Accept': 'application/json'}
            )
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                current = data['data'][0]
                intensity = current['intensity']['actual'] or current['intensity']['forecast']
                return {
                    'intensity': intensity,
                    'index': current['intensity']['index'],
                    'source': 'UK Carbon Intensity API (Real-time)',
                    'is_realtime': True,
                    'timestamp': current['from']
                }
        except Exception as e:
            print(f"  ⚠ UK API failed: {e}, using fallback")
    
    # For other regions, use fallback (in production, would use WattTime/ElectricityMaps)
    return {
        'intensity': FALLBACK_INTENSITY.get(region, 400),
        'source': 'Static Fallback (Ember Climate)',
        'is_realtime': False,
        'index': None,
        'timestamp': datetime.utcnow().isoformat()
    }

# ============================================================================
# SCI CALCULATION
# ============================================================================

def calculate_energy_kwh(vcpu_count: int, memory_gb: float, duration_hours: float, pue: float) -> dict:
    """Calculate energy consumption in kWh."""
    # Compute energy: vCPU × TDP × hours / 1000
    compute_kwh = (vcpu_count * VCPU_TDP_WATTS * duration_hours) / 1000
    
    # Memory energy: GB × hours × coefficient
    memory_kwh = memory_gb * duration_hours * MEMORY_COEFFICIENT_KWH_PER_GB
    
    # Apply PUE (Power Usage Effectiveness)
    total_kwh = (compute_kwh + memory_kwh) * pue
    
    return {
        'compute_kwh': round(compute_kwh, 6),
        'memory_kwh': round(memory_kwh, 6),
        'total_kwh': round(total_kwh, 6),
        'pue_applied': pue
    }

def calculate_embodied_carbon(vcpu_count: int, duration_hours: float) -> float:
    """Calculate embodied carbon (M) in gCO2."""
    return vcpu_count * duration_hours * EMBODIED_EMISSIONS_G_PER_VCPU_HOUR

def calculate_sci(energy_kwh: float, carbon_intensity: float, embodied_g: float, functional_unit: float = 1.0) -> dict:
    """
    Calculate SCI using GSF formula: SCI = ((E × I) + M) / R
    
    Returns detailed breakdown.
    """
    # Operational emissions: E × I
    operational_g = energy_kwh * carbon_intensity
    
    # Total emissions: operational + embodied
    total_g = operational_g + embodied_g
    
    # SCI per functional unit
    sci = total_g / functional_unit if functional_unit > 0 else total_g
    
    return {
        'energy_kwh': round(energy_kwh, 6),
        'carbon_intensity_gco2_kwh': carbon_intensity,
        'operational_emissions_g': round(operational_g, 4),
        'embodied_emissions_g': round(embodied_g, 4),
        'total_emissions_g': round(total_g, 4),
        'total_emissions_kg': round(total_g / 1000, 6),
        'functional_unit': functional_unit,
        'sci_gco2_per_unit': round(sci, 4)
    }

# ============================================================================
# MAIN TEST
# ============================================================================

def test_sci_with_dummy_data():
    """Test SCI calculation with dummy workload data and real carbon intensity."""
    
    print("=" * 70)
    print("SCI CALCULATION TEST - Dummy Workload + Real Carbon Intensity")
    print("=" * 70)
    
    # -------------------------------------------------------------------------
    # DUMMY INPUT DATA (you can modify these)
    # -------------------------------------------------------------------------
    test_cases = [
        {'region': 'eu-west-2', 'duration_minutes': 60, 'vcpu': 4, 'memory_gb': 8.0},
        {'region': 'eu-west-2', 'duration_minutes': 30, 'vcpu': 2, 'memory_gb': 4.0},
        {'region': 'eu-north-1', 'duration_minutes': 60, 'vcpu': 4, 'memory_gb': 8.0},
        {'region': 'us-east-1', 'duration_minutes': 120, 'vcpu': 8, 'memory_gb': 16.0},
    ]
    
    for i, tc in enumerate(test_cases, 1):
        print(f"\n{'─' * 70}")
        print(f"TEST CASE {i}")
        print(f"{'─' * 70}")
        
        region = tc['region']
        duration_hours = tc['duration_minutes'] / 60
        vcpu = tc['vcpu']
        memory_gb = tc['memory_gb']
        
        print(f"\n📋 DUMMY INPUT:")
        print(f"   Region:   {region}")
        print(f"   Duration: {tc['duration_minutes']} minutes ({duration_hours} hours)")
        print(f"   vCPUs:    {vcpu}")
        print(f"   Memory:   {memory_gb} GB")
        
        # Get real carbon intensity
        print(f"\n🌐 FETCHING REAL CARBON INTENSITY...")
        carbon_data = get_real_carbon_intensity(region)
        print(f"   Source:    {carbon_data['source']}")
        print(f"   Intensity: {carbon_data['intensity']} gCO2/kWh")
        if carbon_data.get('index'):
            print(f"   Index:     {carbon_data['index']}")
        print(f"   Real-time: {'Yes ✓' if carbon_data['is_realtime'] else 'No (fallback)'}")
        
        # Calculate energy
        pue = CLOUD_PUE['aws']
        energy = calculate_energy_kwh(vcpu, memory_gb, duration_hours, pue)
        
        print(f"\n⚡ ENERGY CALCULATION:")
        print(f"   Compute Energy: {energy['compute_kwh']} kWh")
        print(f"   Memory Energy:  {energy['memory_kwh']} kWh")
        print(f"   PUE Factor:     {energy['pue_applied']}")
        print(f"   Total Energy:   {energy['total_kwh']} kWh")
        
        # Calculate embodied carbon
        embodied = calculate_embodied_carbon(vcpu, duration_hours)
        print(f"\n🏭 EMBODIED CARBON:")
        print(f"   {embodied} gCO2 (M)")
        
        # Calculate SCI
        sci_result = calculate_sci(
            energy_kwh=energy['total_kwh'],
            carbon_intensity=carbon_data['intensity'],
            embodied_g=embodied,
            functional_unit=1.0
        )
        
        print(f"\n📊 SCI CALCULATION (GSF Formula):")
        print(f"   Formula: SCI = ((E × I) + M) / R")
        print(f"   E (Energy):     {sci_result['energy_kwh']} kWh")
        print(f"   I (Intensity):  {sci_result['carbon_intensity_gco2_kwh']} gCO2/kWh")
        print(f"   M (Embodied):   {sci_result['embodied_emissions_g']} gCO2")
        print(f"   R (Func Unit):  {sci_result['functional_unit']}")
        print(f"\n   Operational:    {sci_result['operational_emissions_g']} gCO2")
        print(f"   + Embodied:     {sci_result['embodied_emissions_g']} gCO2")
        print(f"   ─────────────────────────────")
        print(f"   TOTAL:          {sci_result['total_emissions_g']} gCO2")
        print(f"                   ({sci_result['total_emissions_kg']} kg CO2)")
        print(f"\n   ✅ SCI = {sci_result['sci_gco2_per_unit']} gCO2/unit")
        
        # Real-world equivalents
        phone_charges = sci_result['total_emissions_g'] / 8  # 1 phone charge ≈ 8g CO2
        print(f"\n🌱 EQUIVALENT TO:")
        print(f"   ~{phone_charges:.2f} smartphone charges")

    print(f"\n{'=' * 70}")
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == '__main__':
    test_sci_with_dummy_data()
