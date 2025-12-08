"""
Test CPU Power Lookup Integration with TEADS Calculator

Verifies that the enhanced calculator uses accurate CPU-specific power data.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from teads_enhanced_calculator import (
    TeadsEnhancedCalculator,
    InstanceConfig,
    LoadLevel
)


def test_cpu_lookup_integration():
    """Test that calculator uses CPU lookup when available"""
    print("\n=== Test 1: CPU Lookup Integration ===")
    
    calculator = TeadsEnhancedCalculator()
    
    # Test with specific CPU model
    instance = InstanceConfig(
        vcpu_count=8,
        memory_gb=16,
        cpu_type='intel_xeon',
        cpu_model='6140',  # Intel Xeon 6140 (115W TDP)
        instance_type='m5.2xlarge'
    )
    
    footprint = calculator.calculate_full_footprint(
        instance=instance,
        duration_seconds=3600,
        carbon_intensity=250,
        load_level=LoadLevel.MEDIUM
    )
    
    power_breakdown = footprint['power_breakdown']
    
    print(f"✓ CPU Model: {instance.cpu_model}")
    print(f"  Calculation Method: {power_breakdown['cpu_calculation_method']}")
    print(f"  CPU Power: {power_breakdown['cpu_power_w']}W")
    print(f"  Total Power: {power_breakdown['total_power_w']}W")
    print(f"  Total Emissions: {footprint['total_emissions_g']:.2f} gCO2")
    
    # Verify it used CPU lookup
    assert power_breakdown['cpu_calculation_method'] == 'cpu_lookup', \
        "Should use CPU lookup when model provided"
    
    return True


def test_fallback_to_teads():
    """Test fallback to TEADS estimates when CPU not found"""
    print("\n=== Test 2: Fallback to TEADS Estimates ===")
    
    calculator = TeadsEnhancedCalculator()
    
    # Test without CPU model (should use TEADS estimates)
    instance = InstanceConfig(
        vcpu_count=8,
        memory_gb=16,
        cpu_type='intel_xeon'
    )
    
    footprint = calculator.calculate_full_footprint(
        instance=instance,
        duration_seconds=3600,
        carbon_intensity=250,
        load_level=LoadLevel.MEDIUM
    )
    
    power_breakdown = footprint['power_breakdown']
    
    print(f"✓ No CPU Model Provided")
    print(f"  Calculation Method: {power_breakdown['cpu_calculation_method']}")
    print(f"  CPU Power: {power_breakdown['cpu_power_w']}W")
    print(f"  Total Power: {power_breakdown['total_power_w']}W")
    
    # Verify it used TEADS estimate
    assert power_breakdown['cpu_calculation_method'] == 'teads_estimate', \
        "Should use TEADS estimate when no CPU model"
    
    return True


def test_accuracy_comparison():
    """Compare accuracy between TEADS estimate and CPU lookup"""
    print("\n=== Test 3: Accuracy Comparison ===")
    
    calculator = TeadsEnhancedCalculator()
    
    # Same instance, with and without CPU model
    base_config = {
        'vcpu_count': 8,
        'memory_gb': 16,
        'cpu_type': 'intel_xeon',
        'instance_type': 'm5.2xlarge'
    }
    
    # Without CPU model (TEADS estimate)
    instance_teads = InstanceConfig(**base_config)
    footprint_teads = calculator.calculate_full_footprint(
        instance=instance_teads,
        duration_seconds=3600,
        carbon_intensity=250,
        load_level=LoadLevel.MEDIUM
    )
    
    # With CPU model (CPU lookup)
    instance_lookup = InstanceConfig(**base_config, cpu_model='6140')
    footprint_lookup = calculator.calculate_full_footprint(
        instance=instance_lookup,
        duration_seconds=3600,
        carbon_intensity=250,
        load_level=LoadLevel.MEDIUM
    )
    
    teads_power = footprint_teads['power_breakdown']['cpu_power_w']
    lookup_power = footprint_lookup['power_breakdown']['cpu_power_w']
    
    teads_emissions = footprint_teads['total_emissions_g']
    lookup_emissions = footprint_lookup['total_emissions_g']
    
    diff_percent = abs(teads_power - lookup_power) / teads_power * 100
    
    print(f"TEADS Estimate:")
    print(f"  CPU Power: {teads_power}W")
    print(f"  Total Emissions: {teads_emissions:.2f} gCO2")
    
    print(f"\nCPU Lookup (Xeon 6140):")
    print(f"  CPU Power: {lookup_power}W")
    print(f"  Total Emissions: {lookup_emissions:.2f} gCO2")
    
    print(f"\nDifference: {diff_percent:.1f}%")
    print(f"✓ CPU lookup provides {diff_percent:.1f}% different result")
    
    return True


def test_different_cpus():
    """Test with different CPU models"""
    print("\n=== Test 4: Different CPU Models ===")
    
    calculator = TeadsEnhancedCalculator()
    
    cpus = [
        ('6140', 'Intel Xeon 6140'),
        ('7742', 'AMD EPYC 7742'),
        ('8175m', 'Intel Xeon Platinum 8175M'),
    ]
    
    for cpu_model, cpu_name in cpus:
        instance = InstanceConfig(
            vcpu_count=8,
            memory_gb=16,
            cpu_model=cpu_model,
            instance_type='m5.2xlarge'
        )
        
        footprint = calculator.calculate_full_footprint(
            instance=instance,
            duration_seconds=3600,
            carbon_intensity=250,
            load_level=LoadLevel.MEDIUM
        )
        
        power = footprint['power_breakdown']['cpu_power_w']
        emissions = footprint['total_emissions_g']
        
        print(f"{cpu_name:30s}: {power:6.2f}W → {emissions:7.2f} gCO2")
    
    print("✓ All CPU models calculated successfully")
    return True


def test_load_level_with_cpu_lookup():
    """Test load level profiling with CPU lookup"""
    print("\n=== Test 5: Load Level Profiling with CPU Lookup ===")
    
    calculator = TeadsEnhancedCalculator()
    
    instance = InstanceConfig(
        vcpu_count=8,
        memory_gb=16,
        cpu_model='6140',
        instance_type='m5.2xlarge'
    )
    
    print(f"CPU: Intel Xeon 6140")
    print(f"Load Level → Power → Emissions")
    
    for load_level in LoadLevel:
        footprint = calculator.calculate_full_footprint(
            instance=instance,
            duration_seconds=3600,
            carbon_intensity=250,
            load_level=load_level
        )
        
        power = footprint['power_breakdown']['cpu_power_w']
        emissions = footprint['total_emissions_g']
        
        print(f"  {load_level.value:8s} → {power:6.2f}W → {emissions:7.2f} gCO2")
    
    print("✓ Load level profiling working with CPU lookup")
    return True


def test_instance_type_fallback():
    """Test instance type fallback when CPU model unknown"""
    print("\n=== Test 6: Instance Type Fallback ===")
    
    calculator = TeadsEnhancedCalculator()
    
    instances = [
        ('m5.large', 'General Purpose'),
        ('c5.large', 'Compute Optimized'),
        ('r5.large', 'Memory Optimized'),
        ('t3.medium', 'Burstable'),
    ]
    
    for instance_type, category in instances:
        instance = InstanceConfig(
            vcpu_count=2,
            memory_gb=8,
            instance_type=instance_type
        )
        
        footprint = calculator.calculate_full_footprint(
            instance=instance,
            duration_seconds=3600,
            carbon_intensity=250,
            load_level=LoadLevel.MEDIUM
        )
        
        power = footprint['power_breakdown']['cpu_power_w']
        method = footprint['power_breakdown']['cpu_calculation_method']
        
        print(f"{instance_type:12s} ({category:20s}): {power:6.2f}W [{method}]")
    
    print("✓ Instance type fallback working")
    return True


def run_all_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("CPU Power Lookup Integration Tests")
    print("=" * 60)
    
    tests = [
        test_cpu_lookup_integration,
        test_fallback_to_teads,
        test_accuracy_comparison,
        test_different_cpus,
        test_load_level_with_cpu_lookup,
        test_instance_type_fallback,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
