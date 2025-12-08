"""
Test Enhanced API Handler with Real Data

This script tests the enhanced handler endpoints with real data integration.
"""

import os
import sys
import json

# Add paths
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from handler_enhanced import lambda_handler


def test_feature_status():
    """Test /v2/features endpoint"""
    print("\n" + "=" * 80)
    print("TEST 1: Feature Status Endpoint")
    print("=" * 80)
    
    event = {
        'path': '/v2/features',
        'httpMethod': 'GET'
    }
    
    response = lambda_handler(event, None)
    
    print(f"Status Code: {response['statusCode']}")
    
    if response['statusCode'] == 200:
        body = json.loads(response['body'])
        print("\n✅ Features:")
        for feature, enabled in body['features'].items():
            status = "🟢 ENABLED" if enabled else "⚪ DISABLED"
            print(f"   {status} - {feature}")
        print(f"\nTotal enabled: {body['enabled_count']}")
    else:
        print(f"❌ Error: {response['body']}")


def test_excess_power_disabled():
    """Test /v2/excess-power when feature is disabled"""
    print("\n" + "=" * 80)
    print("TEST 2: Excess Power Endpoint (Feature Disabled)")
    print("=" * 80)
    
    # Ensure feature is disabled
    if 'ENABLE_EXCESS_POWER' in os.environ:
        del os.environ['ENABLE_EXCESS_POWER']
    
    event = {
        'path': '/v2/excess-power',
        'httpMethod': 'GET',
        'queryStringParameters': {'region': 'eu-west-2'}
    }
    
    response = lambda_handler(event, None)
    
    print(f"Status Code: {response['statusCode']}")
    
    if response['statusCode'] == 403:
        print("✅ Correctly returns 403 when feature disabled")
        body = json.loads(response['body'])
        print(f"   Message: {body.get('message')}")
    else:
        print(f"❌ Unexpected response: {response['body']}")


def test_excess_power_enabled():
    """Test /v2/excess-power when feature is enabled"""
    print("\n" + "=" * 80)
    print("TEST 3: Excess Power Endpoint (Feature Enabled)")
    print("=" * 80)
    
    # Enable feature
    os.environ['ENABLE_EXCESS_POWER'] = 'true'
    
    test_regions = ['eu-west-2', 'us-east-1', 'eu-central-1']
    
    for region in test_regions:
        print(f"\n📍 Testing region: {region}")
        print("-" * 80)
        
        event = {
            'path': '/v2/excess-power',
            'httpMethod': 'GET',
            'queryStringParameters': {'region': region}
        }
        
        response = lambda_handler(event, None)
        
        print(f"   Status Code: {response['statusCode']}")
        
        if response['statusCode'] == 200:
            body = json.loads(response['body'])
            
            print(f"   ✅ Data source: {body.get('data_source', 'unknown')}")
            print(f"   Recommendation: {body.get('recommendation')}")
            print(f"   Confidence: {body.get('confidence')}")
            print(f"   Excess renewable: {body.get('excess_renewable_mw', 0):.0f} MW")
            print(f"   Curtailment: {body.get('curtailment_percentage', 0):.1f}%")
            
            if 'note' in body:
                print(f"   Note: {body['note']}")
            
            print(f"   💡 {body.get('reasoning', 'N/A')}")
        else:
            print(f"   ❌ Error: {response['body']}")


def test_enhanced_current_endpoint():
    """Test enhanced /current endpoint"""
    print("\n" + "=" * 80)
    print("TEST 4: Enhanced /current Endpoint")
    print("=" * 80)
    
    # Test with feature disabled
    print("\n📍 Test 4a: Feature disabled")
    if 'ENABLE_EXCESS_POWER' in os.environ:
        del os.environ['ENABLE_EXCESS_POWER']
    
    event = {
        'path': '/current',
        'httpMethod': 'GET',
        'queryStringParameters': {'region': 'eu-west-2'}
    }
    
    response = lambda_handler(event, None)
    
    if response['statusCode'] == 200:
        body = json.loads(response['body'])
        print(f"   ✅ Status: {response['statusCode']}")
        print(f"   Enhanced: {body.get('enhanced', False)}")
        print(f"   Has excess_power: {'excess_power' in body}")
    
    # Test with feature enabled
    print("\n📍 Test 4b: Feature enabled")
    os.environ['ENABLE_EXCESS_POWER'] = 'true'
    
    response = lambda_handler(event, None)
    
    if response['statusCode'] == 200:
        body = json.loads(response['body'])
        print(f"   ✅ Status: {response['statusCode']}")
        print(f"   Enhanced: {body.get('enhanced', False)}")
        print(f"   Has excess_power: {'excess_power' in body}")
        
        if 'excess_power' in body:
            ep = body['excess_power']
            print(f"   Excess Power recommendation: {ep.get('recommendation')}")


def test_backward_compatibility():
    """Test that existing endpoints still work"""
    print("\n" + "=" * 80)
    print("TEST 5: Backward Compatibility")
    print("=" * 80)
    
    # Test /optimal
    print("\n📍 Testing /optimal endpoint...")
    event = {
        'path': '/optimal',
        'httpMethod': 'GET',
        'queryStringParameters': {'limit': '3'}
    }
    
    response = lambda_handler(event, None)
    print(f"   Status: {response['statusCode']}")
    
    if response['statusCode'] == 200:
        print("   ✅ /optimal works")
    else:
        print(f"   ❌ /optimal failed: {response['body']}")
    
    # Test /regions
    print("\n📍 Testing /regions endpoint...")
    event = {
        'path': '/regions',
        'httpMethod': 'GET'
    }
    
    response = lambda_handler(event, None)
    print(f"   Status: {response['statusCode']}")
    
    if response['statusCode'] == 200:
        print("   ✅ /regions works")
    else:
        print(f"   ❌ /regions failed: {response['body']}")


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("ENHANCED API HANDLER - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    try:
        test_feature_status()
        test_excess_power_disabled()
        test_excess_power_enabled()
        test_enhanced_current_endpoint()
        test_backward_compatibility()
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    run_all_tests()
