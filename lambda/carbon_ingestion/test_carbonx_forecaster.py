"""
Test CarbonX Forecaster

Tests the enhanced forecasting functionality with real and synthetic data.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from carbonx_forecaster import CarbonXForecaster
import json


def test_synthetic_historical_data():
    """Test synthetic data generation"""
    print("\n=== Test 1: Synthetic Historical Data ===")
    
    forecaster = CarbonXForecaster('eu-west-2')
    historical = forecaster._generate_synthetic_historical_data(168)  # 7 days
    
    print(f"✓ Generated {len(historical)} hours of data")
    print(f"  Min: {min(historical):.2f} gCO2/kWh")
    print(f"  Max: {max(historical):.2f} gCO2/kWh")
    print(f"  Avg: {sum(historical)/len(historical):.2f} gCO2/kWh")
    
    assert len(historical) == 168, "Should generate 168 hours"
    assert all(h > 0 for h in historical), "All values should be positive"
    
    return True


def test_basic_forecast():
    """Test basic 24-hour forecast"""
    print("\n=== Test 2: Basic 24-Hour Forecast ===")
    
    forecaster = CarbonXForecaster('eu-west-2')
    
    # Use synthetic historical data
    historical = forecaster._generate_synthetic_historical_data(168)
    
    # Generate forecast
    forecast_data = forecaster.forecast_with_uncertainty(
        historical_data=historical,
        hours_ahead=24,
        confidence_level=0.95
    )
    
    print(f"✓ Region: {forecast_data['region']}")
    print(f"✓ Horizon: {forecast_data['horizon_hours']} hours")
    print(f"✓ Forecasts: {len(forecast_data['forecasts'])} points")
    print(f"✓ Confidence: {forecast_data['confidence_level']*100}%")
    
    # Check structure
    assert forecast_data['region'] == 'eu-west-2'
    assert forecast_data['horizon_hours'] == 24
    assert len(forecast_data['forecasts']) == 24
    assert len(forecast_data['prediction_intervals']) == 24
    
    # Check first forecast
    first_forecast = forecast_data['forecasts'][0]
    print(f"\n  First forecast (hour 1):")
    print(f"    Carbon Intensity: {first_forecast['carbon_intensity']} gCO2/kWh")
    print(f"    Timestamp: {first_forecast['timestamp']}")
    
    # Check prediction interval
    first_interval = forecast_data['prediction_intervals'][0]
    print(f"    Confidence Interval: [{first_interval['lower_bound']}, {first_interval['upper_bound']}]")
    print(f"    Interval Width: {first_interval['interval_width']:.2f}")
    
    return True


def test_multi_day_forecast():
    """Test multi-day forecast (96 hours)"""
    print("\n=== Test 3: Multi-Day Forecast (96 hours) ===")
    
    forecaster = CarbonXForecaster('us-east-1')
    
    # Use synthetic historical data
    historical = forecaster._generate_synthetic_historical_data(168)
    
    # Generate 4-day forecast
    forecast_data = forecaster.forecast_with_uncertainty(
        historical_data=historical,
        hours_ahead=96,
        confidence_level=0.95
    )
    
    print(f"✓ Region: {forecast_data['region']}")
    print(f"✓ Horizon: {forecast_data['horizon_hours']} hours ({forecast_data['horizon_hours']//24} days)")
    print(f"✓ Forecasts: {len(forecast_data['forecasts'])} points")
    
    # Check quality metrics
    metrics = forecast_data['quality_metrics']
    print(f"\n  Quality Metrics:")
    print(f"    Expected MAPE: {metrics['expected_mape_percent']}%")
    print(f"    Avg Interval Width: {metrics['average_interval_width_normalized']:.3f}")
    print(f"    Expected Coverage: {metrics['expected_coverage_percent']}%")
    
    assert len(forecast_data['forecasts']) == 96
    assert metrics['expected_mape_percent'] > 0
    
    return True


def test_optimal_scheduling_windows():
    """Test optimal scheduling window identification"""
    print("\n=== Test 4: Optimal Scheduling Windows ===")
    
    forecaster = CarbonXForecaster('eu-west-2')
    
    # Generate forecast
    historical = forecaster._generate_synthetic_historical_data(168)
    forecast_data = forecaster.forecast_with_uncertainty(
        historical_data=historical,
        hours_ahead=48,
        confidence_level=0.95
    )
    
    # Find optimal windows for 4-hour workload
    windows = forecaster.get_optimal_scheduling_windows(
        forecast_data=forecast_data,
        duration_hours=4,
        top_n=3
    )
    
    print(f"✓ Found {len(windows)} optimal windows for 4-hour workload")
    
    for i, window in enumerate(windows, 1):
        print(f"\n  Window {i}:")
        print(f"    Start: Hour {window['start_hour']} ({window['start_timestamp']})")
        print(f"    End: Hour {window['end_hour']}")
        print(f"    Avg Carbon: {window['average_carbon_intensity']} gCO2/kWh")
        print(f"    Expected Savings: {window['expected_savings_percent']:.2f}%")
    
    assert len(windows) == 3
    assert all('expected_savings_percent' in w for w in windows)
    
    return True


def test_auto_fetch_historical():
    """Test automatic historical data fetching"""
    print("\n=== Test 5: Auto-Fetch Historical Data ===")
    
    forecaster = CarbonXForecaster('eu-west-2')
    
    # Call without providing historical data (should auto-fetch/generate)
    forecast_data = forecaster.forecast_with_uncertainty(
        historical_data=None,  # Auto-fetch
        hours_ahead=24,
        confidence_level=0.95
    )
    
    print(f"✓ Auto-fetched historical data and generated forecast")
    print(f"  Region: {forecast_data['region']}")
    print(f"  Forecasts: {len(forecast_data['forecasts'])} points")
    
    assert len(forecast_data['forecasts']) == 24
    
    return True


def test_different_regions():
    """Test forecasting for different regions"""
    print("\n=== Test 6: Different Regions ===")
    
    regions = ['eu-west-2', 'us-east-1', 'ap-southeast-1']
    
    for region in regions:
        forecaster = CarbonXForecaster(region)
        historical = forecaster._generate_synthetic_historical_data(168)
        
        forecast_data = forecaster.forecast_with_uncertainty(
            historical_data=historical,
            hours_ahead=24
        )
        
        avg_ci = sum(f['carbon_intensity'] for f in forecast_data['forecasts']) / 24
        print(f"  {region}: Avg forecast = {avg_ci:.2f} gCO2/kWh")
    
    print("✓ All regions forecasted successfully")
    return True


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("CarbonX Forecaster Test Suite")
    print("=" * 60)
    
    tests = [
        test_synthetic_historical_data,
        test_basic_forecast,
        test_multi_day_forecast,
        test_optimal_scheduling_windows,
        test_auto_fetch_historical,
        test_different_regions,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
