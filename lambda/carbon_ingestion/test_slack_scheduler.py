"""
Tests for Slack-Aware Scheduler

Tests temporal shifting optimization with deadline flexibility.
"""

import os
import sys
from datetime import datetime, timedelta

# Set feature flag for testing
os.environ['ENABLE_SLACK_SCHEDULING'] = 'true'

from slack_scheduler import SlackAwareScheduler


def test_basic_scheduling():
    """Test basic slack-aware scheduling."""
    print("\n=== Test 1: Basic Scheduling ===")
    
    scheduler = SlackAwareScheduler()
    
    result = scheduler.optimize_schedule(
        region='eu-west-2',
        workload_duration_hours=4,
        deadline_hours=12,
        current_carbon_intensity=250,
        vcpu_count=8,
        memory_gb=16
    )
    
    assert 'immediate_execution' in result
    assert 'optimal_execution' in result
    assert 'savings' in result
    assert 'recommendation' in result
    
    print(f"✓ Immediate: {result['immediate_execution']['carbon_footprint_gco2']} gCO2")
    if result['optimal_execution']:
        print(f"✓ Optimal: {result['optimal_execution']['carbon_footprint_gco2']} gCO2")
        print(f"✓ Savings: {result['savings']['percent']}%")
        print(f"✓ Recommendation: {result['recommendation']}")
    
    return True


def test_slack_time_calculation():
    """Test slack time calculation."""
    print("\n=== Test 2: Slack Time Calculation ===")
    
    scheduler = SlackAwareScheduler()
    
    # High flexibility (100% slack)
    result1 = scheduler.calculate_slack_time(
        workload_duration_hours=4,
        deadline_hours=8
    )
    assert result1['slack_hours'] == 4
    assert result1['flexibility'] == 'HIGH'
    print(f"✓ High flexibility: {result1['slack_hours']}h ({result1['slack_percent']}%)")
    
    # Medium flexibility (50% slack)
    result2 = scheduler.calculate_slack_time(
        workload_duration_hours=4,
        deadline_hours=6
    )
    assert result2['slack_hours'] == 2
    assert result2['flexibility'] == 'MEDIUM'
    print(f"✓ Medium flexibility: {result2['slack_hours']}h ({result2['slack_percent']}%)")
    
    # Low flexibility (25% slack)
    result3 = scheduler.calculate_slack_time(
        workload_duration_hours=4,
        deadline_hours=5
    )
    assert result3['slack_hours'] == 1
    assert result3['flexibility'] == 'LOW'
    print(f"✓ Low flexibility: {result3['slack_hours']}h ({result3['slack_percent']}%)")
    
    # No flexibility
    result4 = scheduler.calculate_slack_time(
        workload_duration_hours=4,
        deadline_hours=4
    )
    assert result4['slack_hours'] == 0
    assert result4['flexibility'] == 'NONE'
    print(f"✓ No flexibility: {result4['slack_hours']}h")
    
    return True


def test_deadline_too_short():
    """Test handling of deadline shorter than workload."""
    print("\n=== Test 3: Deadline Too Short ===")
    
    scheduler = SlackAwareScheduler()
    
    result = scheduler.calculate_slack_time(
        workload_duration_hours=8,
        deadline_hours=4
    )
    
    assert 'error' in result
    assert result['slack_hours'] == 0
    print(f"✓ Error handled: {result['error']}")
    
    return True


def test_recommendation_logic():
    """Test recommendation determination logic."""
    print("\n=== Test 4: Recommendation Logic ===")
    
    scheduler = SlackAwareScheduler()
    
    # High savings (>20%) - should recommend delay
    rec1 = scheduler._determine_recommendation(
        savings_percent=25,
        delay_hours=6,
        slack_hours=8
    )
    assert rec1 == 'DELAY_RECOMMENDED'
    print(f"✓ High savings (25%): {rec1}")
    
    # Moderate savings (10-20%) with short delay - optional
    rec2 = scheduler._determine_recommendation(
        savings_percent=15,
        delay_hours=2,
        slack_hours=8
    )
    assert rec2 == 'DELAY_OPTIONAL'
    print(f"✓ Moderate savings (15%), short delay: {rec2}")
    
    # Low savings (<10%) - execute now
    rec3 = scheduler._determine_recommendation(
        savings_percent=5,
        delay_hours=2,
        slack_hours=8
    )
    assert rec3 == 'EXECUTE_NOW'
    print(f"✓ Low savings (5%): {rec3}")
    
    # Moderate savings but long delay - execute now
    rec4 = scheduler._determine_recommendation(
        savings_percent=15,
        delay_hours=7,
        slack_hours=8
    )
    assert rec4 == 'EXECUTE_NOW'
    print(f"✓ Moderate savings (15%), long delay: {rec4}")
    
    return True


def test_carbon_footprint_calculation():
    """Test carbon footprint calculation."""
    print("\n=== Test 5: Carbon Footprint Calculation ===")
    
    scheduler = SlackAwareScheduler()
    
    # Test with known values
    carbon = scheduler._calculate_carbon_footprint(
        carbon_intensity=250,  # gCO2/kWh
        duration_hours=4,
        vcpu_count=8,
        memory_gb=16
    )
    
    # Expected calculation:
    # CPU: 8 * 10W * 4h / 1000 = 0.32 kWh
    # Memory: 16 * 0.000392 * 4 = 0.025088 kWh
    # Total: (0.32 + 0.025088) * 1.15 = 0.397 kWh
    # Carbon: 0.392 * 250 = 98 gCO2
    
    expected = 98  # Approximate
    assert abs(carbon - expected) < 10  # Within 10 gCO2
    print(f"✓ Carbon footprint: {carbon:.2f} gCO2 (expected ~{expected})")
    
    return True


def test_different_workload_sizes():
    """Test with different workload sizes."""
    print("\n=== Test 6: Different Workload Sizes ===")
    
    scheduler = SlackAwareScheduler()
    
    # Small workload (1 hour, 2 vCPU)
    result1 = scheduler.optimize_schedule(
        region='eu-west-2',
        workload_duration_hours=1,
        deadline_hours=6,
        current_carbon_intensity=250,
        vcpu_count=2,
        memory_gb=4
    )
    print(f"✓ Small workload: {result1['immediate_execution']['carbon_footprint_gco2']} gCO2")
    
    # Medium workload (4 hours, 8 vCPU)
    result2 = scheduler.optimize_schedule(
        region='eu-west-2',
        workload_duration_hours=4,
        deadline_hours=12,
        current_carbon_intensity=250,
        vcpu_count=8,
        memory_gb=16
    )
    print(f"✓ Medium workload: {result2['immediate_execution']['carbon_footprint_gco2']} gCO2")
    
    # Large workload (8 hours, 32 vCPU)
    result3 = scheduler.optimize_schedule(
        region='eu-west-2',
        workload_duration_hours=8,
        deadline_hours=24,
        current_carbon_intensity=250,
        vcpu_count=32,
        memory_gb=64
    )
    print(f"✓ Large workload: {result3['immediate_execution']['carbon_footprint_gco2']} gCO2")
    
    # Verify larger workloads have higher carbon
    assert result1['immediate_execution']['carbon_footprint_gco2'] < \
           result2['immediate_execution']['carbon_footprint_gco2'] < \
           result3['immediate_execution']['carbon_footprint_gco2']
    
    return True


def test_scheduling_windows():
    """Test finding multiple scheduling windows."""
    print("\n=== Test 7: Scheduling Windows ===")
    
    scheduler = SlackAwareScheduler()
    
    result = scheduler.optimize_schedule(
        region='eu-west-2',
        workload_duration_hours=2,
        deadline_hours=12,
        current_carbon_intensity=250,
        vcpu_count=4,
        memory_gb=8
    )
    
    if 'scheduling_windows' in result and result['scheduling_windows']:
        windows = result['scheduling_windows']
        print(f"✓ Found {len(windows)} scheduling windows")
        
        # Verify windows are sorted by carbon (lowest first)
        for i in range(len(windows) - 1):
            assert windows[i]['carbon_footprint_gco2'] <= windows[i+1]['carbon_footprint_gco2']
        print(f"✓ Windows sorted by carbon footprint")
        
        # Show top 3 windows
        for i, window in enumerate(windows[:3]):
            print(f"  Window {i+1}: {window['carbon_footprint_gco2']} gCO2 "
                  f"(delay: {window['delay_hours']}h)")
    
    return True


def test_feature_flag():
    """Test feature flag behavior."""
    print("\n=== Test 8: Feature Flag ===")
    
    # Disable feature
    os.environ['ENABLE_SLACK_SCHEDULING'] = 'false'
    scheduler = SlackAwareScheduler()
    
    result = scheduler.optimize_schedule(
        region='eu-west-2',
        workload_duration_hours=4,
        deadline_hours=12,
        current_carbon_intensity=250,
        vcpu_count=8,
        memory_gb=16
    )
    
    assert 'error' in result
    assert 'feature_flag' in result
    print(f"✓ Feature disabled: {result['error']}")
    
    # Re-enable for other tests
    os.environ['ENABLE_SLACK_SCHEDULING'] = 'true'
    
    return True


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Slack-Aware Scheduler Test Suite")
    print("=" * 60)
    
    tests = [
        test_basic_scheduling,
        test_slack_time_calculation,
        test_deadline_too_short,
        test_recommendation_logic,
        test_carbon_footprint_calculation,
        test_different_workload_sizes,
        test_scheduling_windows,
        test_feature_flag
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"✗ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ Test error: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
