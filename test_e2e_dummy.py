"""
End-to-End Test with Dummy Pipeline Data

This script tests the complete flow:
1. Get scheduling recommendation (with real carbon intensity API)
2. Simulate pipeline trigger (dummy)
3. Calculate SCI for default vs optimal region
4. Calculate savings
5. Generate test history data for UI

Run this to generate sample data, then open the dashboard to see results.
"""

import json
import sys
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List
import random

# Add paths for imports
sys.path.insert(0, os.path.dirname(__file__))

# ============================================================================
# DUMMY PIPELINE CONFIGURATION
# ============================================================================
# In production, these come from config/pipeline_config.py via environment variables

DUMMY_PIPELINE_CONFIG = {
    "codepipeline": {
        "enabled": True,
        "name": "green-qa-test-pipeline",
        "region": None,  # Will be set dynamically based on decision
    },
    "test_suites": [
        "Unit Tests",
        "Integration Tests", 
        "E2E Tests",
        "Smoke Tests",
        "Regression Suite",
        "API Tests",
        "Performance Tests"
    ],
    "workload_profiles": [
        {"duration_minutes": 15, "vcpu_count": 2, "memory_gb": 4},
        {"duration_minutes": 30, "vcpu_count": 4, "memory_gb": 8},
        {"duration_minutes": 60, "vcpu_count": 4, "memory_gb": 8},
        {"duration_minutes": 45, "vcpu_count": 8, "memory_gb": 16},
        {"duration_minutes": 120, "vcpu_count": 8, "memory_gb": 32},
    ]
}

# ============================================================================
# CARBON INTENSITY (Real API + Fallback)
# ============================================================================

FALLBACK_INTENSITY = {
    'eu-west-2': 250,    # UK (default region)
    'eu-north-1': 30,    # Sweden (typically lowest)
    'eu-west-1': 300,    # Ireland
    'eu-west-3': 60,     # France
    'eu-central-1': 380, # Germany
    'us-east-1': 420,    # Virginia
    'us-west-2': 280,    # Oregon
}

def get_real_carbon_intensity(region: str) -> Dict:
    """Fetch real carbon intensity from UK API or use fallback."""
    from urllib.request import urlopen, Request
    
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
                    'is_realtime': True
                }
        except Exception as e:
            print(f"  ⚠ UK API failed: {e}")
    
    return {
        'intensity': FALLBACK_INTENSITY.get(region, 300),
        'source': 'Fallback (Ember Climate)',
        'is_realtime': False,
        'index': None
    }

def get_optimal_region() -> Dict:
    """Find the region with lowest carbon intensity."""
    best_region = 'eu-north-1'
    best_intensity = FALLBACK_INTENSITY['eu-north-1']
    
    # Check UK real-time
    uk_data = get_real_carbon_intensity('eu-west-2')
    if uk_data['intensity'] < best_intensity:
        best_region = 'eu-west-2'
        best_intensity = uk_data['intensity']
    
    return {
        'region': best_region,
        'intensity': best_intensity,
        'source': 'Optimal Region Finder'
    }

# ============================================================================
# SCI CALCULATION
# ============================================================================

CCF = {
    'PUE': 1.15,  # AWS 2024 Sustainability Report
    'VCPU_TDP_WATTS': 10,
    'MEMORY_COEFF': 0.000392,
    'EMBODIED_G_PER_VCPU_HOUR': 2.5
}

def calculate_sci(duration_minutes: float, vcpu_count: int, memory_gb: float, carbon_intensity: float) -> Dict:
    """Calculate SCI using GSF formula."""
    duration_hours = duration_minutes / 60
    
    compute_kwh = (vcpu_count * CCF['VCPU_TDP_WATTS'] * duration_hours) / 1000
    memory_kwh = memory_gb * duration_hours * CCF['MEMORY_COEFF']
    total_energy_kwh = (compute_kwh + memory_kwh) * CCF['PUE']
    
    operational_g = total_energy_kwh * carbon_intensity
    embodied_g = vcpu_count * duration_hours * CCF['EMBODIED_G_PER_VCPU_HOUR']
    total_g = operational_g + embodied_g
    
    return {
        'energy_kwh': round(total_energy_kwh, 6),
        'operational_g': round(operational_g, 4),
        'embodied_g': round(embodied_g, 4),
        'total_g': round(total_g, 4)
    }

# ============================================================================
# DUMMY PIPELINE TRIGGER
# ============================================================================

def simulate_pipeline_trigger(pipeline_name: str, region: str) -> Dict:
    """Simulate triggering a pipeline (dummy for testing)."""
    # Simulate success/failure randomly (90% success rate)
    success = random.random() < 0.9
    
    if success:
        execution_id = f"exec-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
        return {
            'status': 'success',
            'service': 'CodePipeline',
            'message': f"Pipeline '{pipeline_name}' triggered in {region}",
            'execution_id': execution_id
        }
    else:
        return {
            'status': 'failed',
            'service': 'CodePipeline',
            'message': f"Pipeline '{pipeline_name}' failed to start",
            'error': 'Simulated failure for testing'
        }

# ============================================================================
# END-TO-END TEST FLOW
# ============================================================================

def run_optimized_test(test_suite: str, duration_minutes: int, vcpu_count: int, memory_gb: float) -> Dict:
    """
    Run the complete optimized test flow:
    1. Get optimal region
    2. Trigger pipeline (simulated)
    3. Calculate SCI for both regions
    4. Calculate savings
    """
    print(f"\n{'─' * 60}")
    print(f"Running: {test_suite}")
    print(f"{'─' * 60}")
    
    # Default region for comparison
    default_region = 'eu-west-2'
    
    # Step 1: Get carbon intensities
    print("\n📊 Step 1: Getting carbon intensities...")
    default_data = get_real_carbon_intensity(default_region)
    optimal_data = get_optimal_region()
    
    print(f"   Default ({default_region}): {default_data['intensity']} gCO2/kWh ({default_data['source']})")
    print(f"   Optimal ({optimal_data['region']}): {optimal_data['intensity']} gCO2/kWh")
    
    # Step 2: Determine recommendation
    optimal_region = optimal_data['region']
    optimal_intensity = optimal_data['intensity']
    default_intensity = default_data['intensity']
    
    if optimal_intensity < default_intensity * 0.85:
        recommendation = 'relocate'
        reason = f"Running in {optimal_region} saves {((default_intensity - optimal_intensity) / default_intensity * 100):.0f}% carbon"
    elif default_data.get('index') in ['very low', 'low']:
        recommendation = 'run_now'
        reason = f"Carbon intensity is {default_data.get('index', 'acceptable')}"
        optimal_region = default_region
        optimal_intensity = default_intensity
    else:
        recommendation = 'run_now'
        reason = "No significant benefit from relocating"
        optimal_region = default_region
        optimal_intensity = default_intensity
    
    print(f"\n🎯 Step 2: Recommendation = {recommendation.upper()}")
    print(f"   Reason: {reason}")
    print(f"   Target region: {optimal_region}")
    
    # Step 3: Trigger pipeline (simulated)
    print(f"\n🚀 Step 3: Triggering pipeline...")
    pipeline_result = simulate_pipeline_trigger(
        DUMMY_PIPELINE_CONFIG['codepipeline']['name'],
        optimal_region
    )
    print(f"   Status: {pipeline_result['status']}")
    print(f"   Message: {pipeline_result['message']}")
    if pipeline_result.get('execution_id'):
        print(f"   Execution ID: {pipeline_result['execution_id']}")
    
    # Step 4: Calculate SCI
    print(f"\n📈 Step 4: Calculating SCI...")
    default_sci = calculate_sci(duration_minutes, vcpu_count, memory_gb, default_intensity)
    optimal_sci = calculate_sci(duration_minutes, vcpu_count, memory_gb, optimal_intensity)
    
    print(f"   Default SCI ({default_region}): {default_sci['total_g']:.4f} gCO2")
    print(f"   Optimal SCI ({optimal_region}): {optimal_sci['total_g']:.4f} gCO2")
    
    # Step 5: Calculate savings
    savings_g = default_sci['total_g'] - optimal_sci['total_g']
    savings_percent = (savings_g / default_sci['total_g'] * 100) if default_sci['total_g'] > 0 else 0
    
    print(f"\n💰 Step 5: Carbon Savings")
    print(f"   Saved: {savings_g:.4f} gCO2 ({savings_percent:.2f}%)")
    
    # Build result
    result = {
        'test_id': f"test-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(100, 999)}",
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'test_suite': test_suite,
        'duration_minutes': duration_minutes,
        'vcpu_count': vcpu_count,
        'memory_gb': memory_gb,
        'energy_kwh': optimal_sci['energy_kwh'],
        'recommendation': recommendation,
        'default_region': default_region,
        'default_intensity': default_intensity,
        'default_sci': default_sci['total_g'],
        'optimal_region': optimal_region,
        'optimal_intensity': optimal_intensity,
        'optimal_sci': optimal_sci['total_g'],
        'savings_g': round(savings_g, 4),
        'savings_percent': round(savings_percent, 2),
        'pipeline_status': pipeline_result['status'],
        'pipeline_execution_id': pipeline_result.get('execution_id', '')
    }
    
    return result

def generate_test_history(count: int = 10) -> List[Dict]:
    """Generate multiple test history entries for UI testing."""
    history = []
    
    for i in range(count):
        # Random test suite and workload
        suite = random.choice(DUMMY_PIPELINE_CONFIG['test_suites'])
        workload = random.choice(DUMMY_PIPELINE_CONFIG['workload_profiles'])
        
        result = run_optimized_test(
            test_suite=suite,
            duration_minutes=workload['duration_minutes'],
            vcpu_count=workload['vcpu_count'],
            memory_gb=workload['memory_gb']
        )
        
        # Adjust timestamp to spread over last few hours
        result['timestamp'] = (datetime.now(timezone.utc) - timedelta(minutes=i * 15)).isoformat()
        
        history.append(result)
    
    return history

# ============================================================================
# SAVE TEST DATA FOR UI
# ============================================================================

def save_test_data_for_ui(history: List[Dict]):
    """Save test history as JSON for the dashboard to load."""
    output_path = os.path.join(os.path.dirname(__file__), 'dashboard', 'public', 'test-history-data.js')
    
    # Format as JavaScript variable
    js_content = f"""// Auto-generated test history data for UI testing
// Generated: {datetime.now().isoformat()}
// This file is loaded by the dashboard when API is not available

const TEST_HISTORY_DATA = {json.dumps(history, indent=2)};

// Make available globally
if (typeof window !== 'undefined') {{
    window.TEST_HISTORY_DATA = TEST_HISTORY_DATA;
}}
"""
    
    with open(output_path, 'w') as f:
        f.write(js_content)
    
    print(f"\n✅ Test history saved to: {output_path}")
    return output_path

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("END-TO-END TEST WITH DUMMY PIPELINE DATA")
    print("=" * 70)
    print("\nThis test simulates the complete flow:")
    print("  1. Get carbon intensity (real UK API + fallback)")
    print("  2. Determine optimal region")
    print("  3. Trigger pipeline (simulated)")
    print("  4. Calculate SCI for default vs optimal region")
    print("  5. Calculate carbon savings")
    print("\nNote: Pipeline trigger is SIMULATED. In production,")
    print("      real pipeline names come from config/pipeline_config.py")
    
    # Generate test history
    print("\n" + "=" * 70)
    print("GENERATING TEST HISTORY (10 test runs)")
    print("=" * 70)
    
    history = generate_test_history(10)
    
    # Save for UI
    save_test_data_for_ui(history)
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    total_savings = sum(t['savings_g'] for t in history)
    avg_savings_pct = sum(t['savings_percent'] for t in history) / len(history)
    optimized_count = sum(1 for t in history if t['savings_percent'] > 0)
    
    print(f"\n📊 Test Results:")
    print(f"   Total tests: {len(history)}")
    print(f"   Tests optimized: {optimized_count}")
    print(f"   Total carbon saved: {total_savings:.2f} gCO2")
    print(f"   Average savings: {avg_savings_pct:.1f}%")
    
    print(f"\n📋 Test History:")
    print(f"   {'Suite':<20} {'Region':<15} {'SCI (gCO2)':<12} {'Savings':<10} {'Status'}")
    print(f"   {'-'*20} {'-'*15} {'-'*12} {'-'*10} {'-'*10}")
    for t in history:
        print(f"   {t['test_suite']:<20} {t['optimal_region']:<15} {t['optimal_sci']:<12.2f} {t['savings_percent']:<10.1f}% {t['pipeline_status']}")
    
    print("\n" + "=" * 70)
    print("To view in UI, open: dashboard/public/index.html")
    print("=" * 70)
