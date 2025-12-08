"""
Test Excess Power Calculator with Real Data

This script tests the calculator with real data from DynamoDB
and optionally from ElectricityMaps API.
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from excess_power_calculator import ExcessPowerCalculator


def test_with_real_data():
    """Test Excess Power calculator with real data"""
    
    # Test regions (AWS regions that map to grid zones)
    test_regions = [
        ('eu-west-2', 'GB'),  # London -> Great Britain
        ('us-east-1', 'US-CAL-CISO'),  # Virginia -> California ISO
        ('eu-central-1', 'DE'),  # Frankfurt -> Germany
        ('us-west-2', 'US-NW-PACW'),  # Oregon -> Pacific Northwest
    ]
    
    print("=" * 80)
    print("EXCESS POWER CALCULATOR - REAL DATA TEST")
    print("=" * 80)
    print()
    
    for aws_region, grid_zone in test_regions:
        print(f"\n{'=' * 80}")
        print(f"Testing: {aws_region} (Grid Zone: {grid_zone})")
        print('=' * 80)
        
        calculator = ExcessPowerCalculator(aws_region)
        
        try:
            # Get real grid data (will use DynamoDB fallback if ElectricityMaps unavailable)
            print("\n📊 Fetching grid data...")
            grid_data = calculator.get_grid_data_from_electricitymaps(grid_zone)
            
            print(f"   Data source: {grid_data['source']}")
            print(f"   Total generation: {grid_data['total_generation_mw']:.0f} MW")
            print(f"   Demand: {grid_data['demand_mw']:.0f} MW")
            print(f"   Renewable generation: {grid_data['renewable_generation_mw']:.0f} MW")
            print(f"   Grid capacity: {grid_data['grid_capacity_mw']:.0f} MW")
            
            if 'note' in grid_data:
                print(f"   Note: {grid_data['note']}")
            
            # Calculate excess power
            print("\n⚡ Calculating Excess Power...")
            result = calculator.calculate_excess_power(
                timestamp=datetime.now(),
                total_generation_mw=grid_data['total_generation_mw'],
                demand_mw=grid_data['demand_mw'],
                renewable_generation_mw=grid_data['renewable_generation_mw'],
                grid_capacity_mw=grid_data['grid_capacity_mw']
            )
            
            # Display results
            print("\n✅ RESULTS:")
            print(f"   Recommendation: {result['recommendation']}")
            print(f"   Confidence: {result['confidence']}")
            print(f"   Excess renewable: {result['excess_renewable_mw']:.0f} MW")
            print(f"   Curtailment: {result['curtailment_percentage']:.1f}%")
            print(f"   Available capacity: {result['available_capacity_mw']:.0f} MW")
            print(f"\n   💡 Reasoning: {result['reasoning']}")
            
            # Recommendation badge
            badge_colors = {
                'SCHEDULE_NOW': '🟢',
                'SCHEDULE_PREFERRED': '🟡',
                'SCHEDULE_ACCEPTABLE': '🟠',
                'DEFER': '🔴'
            }
            badge = badge_colors.get(result['recommendation'], '⚪')
            print(f"\n   {badge} {result['recommendation'].replace('_', ' ')}")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


def test_single_region(region: str):
    """Test a single region in detail"""
    
    print("=" * 80)
    print(f"DETAILED TEST: {region}")
    print("=" * 80)
    
    calculator = ExcessPowerCalculator(region)
    
    try:
        # Test with DynamoDB fallback
        print("\n1. Testing DynamoDB fallback...")
        grid_data = calculator._get_grid_data_from_dynamodb(region)
        
        print(f"   ✅ Data retrieved:")
        print(f"      Source: {grid_data['source']}")
        print(f"      Total generation: {grid_data['total_generation_mw']:.0f} MW")
        print(f"      Demand: {grid_data['demand_mw']:.0f} MW")
        print(f"      Renewable: {grid_data['renewable_generation_mw']:.0f} MW")
        
        if 'carbon_intensity' in grid_data:
            print(f"      Carbon intensity: {grid_data['carbon_intensity']:.0f} gCO2/kWh")
        
        # Calculate excess power
        print("\n2. Calculating Excess Power...")
        result = calculator.calculate_excess_power(
            timestamp=datetime.now(),
            **{k: v for k, v in grid_data.items() 
               if k in ['total_generation_mw', 'demand_mw', 'renewable_generation_mw', 'grid_capacity_mw']}
        )
        
        print(f"   ✅ Calculation complete:")
        print(f"      Recommendation: {result['recommendation']}")
        print(f"      Confidence: {result['confidence']}")
        print(f"      Reasoning: {result['reasoning']}")
        
        # Test with ElectricityMaps (will fallback if not available)
        print("\n3. Testing ElectricityMaps integration...")
        grid_data_em = calculator.get_grid_data_from_electricitymaps('GB')
        print(f"   ✅ Data source: {grid_data_em['source']}")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Excess Power Calculator with real data')
    parser.add_argument('--region', type=str, help='Test a single region (e.g., eu-west-2)')
    parser.add_argument('--all', action='store_true', help='Test all regions')
    
    args = parser.parse_args()
    
    if args.region:
        test_single_region(args.region)
    else:
        test_with_real_data()
