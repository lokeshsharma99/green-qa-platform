"""
GMT API Handler
Endpoints for Energy Profiling and Regression Tracking
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'carbon_ingestion'))

from energy_profiler import EnergyProfiler
from energy_regression_detector import EnergyRegressionDetector
from carbon_converter import CarbonConverter
from test_suite_optimizer import TestSuiteOptimizer
from feature_flags import FeatureFlags

# CORS headers
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
}

def lambda_handler(event, context):
    """Main Lambda handler for GMT endpoints"""
    
    # Handle OPTIONS for CORS
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': ''
        }
    
    # Check if GMT features are enabled
    if not FeatureFlags.GMT_INTEGRATION:
        return {
            'statusCode': 503,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'error': 'GMT features are currently disabled',
                'message': 'Contact administrator to enable GMT_INTEGRATION feature flag'
            })
        }
    
    # Route to appropriate handler
    path = event.get('path', '')
    method = event.get('httpMethod', 'GET')
    
    try:
        if '/energy-profile' in path:
            return handle_energy_profile(event, method)
        elif '/regression-tracking' in path:
            return handle_regression_tracking(event, method)
        elif '/calibration' in path:
            return handle_calibration(event, method)
        elif '/optimize-test-suite' in path:
            return handle_optimize_test_suite(event, method)
        else:
            return {
                'statusCode': 404,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Endpoint not found'})
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }


def handle_energy_profile(event, method):
    """Handle energy profiling endpoints"""
    
    if method == 'GET':
        # GET /v2/energy-profile/list - List all profiles
        if 'list' in event.get('path', ''):
            return list_energy_profiles()
        
        # GET /v2/energy-profile/{profile_id} - Get specific profile
        profile_id = event.get('pathParameters', {}).get('profile_id')
        if profile_id:
            return get_energy_profile(profile_id)
        
        return {
            'statusCode': 400,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Missing profile_id'})
        }
    
    elif method == 'POST':
        # POST /v2/energy-profile - Create new profile
        body = json.loads(event.get('body', '{}'))
        return create_energy_profile(body)
    
    return {
        'statusCode': 405,
        'headers': CORS_HEADERS,
        'body': json.dumps({'error': 'Method not allowed'})
    }


def handle_regression_tracking(event, method):
    """Handle regression tracking endpoints"""
    
    if method == 'GET':
        # GET /v2/regression-tracking/{branch}/{workload}
        params = event.get('pathParameters', {})
        branch = params.get('branch')
        workload = params.get('workload')
        
        if branch and workload:
            return get_regression_data(branch, workload)
        
        return {
            'statusCode': 400,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Missing branch or workload'})
        }
    
    elif method == 'POST':
        # POST /v2/regression-tracking/measurement - Add new measurement
        body = json.loads(event.get('body', '{}'))
        return add_regression_measurement(body)
    
    return {
        'statusCode': 405,
        'headers': CORS_HEADERS,
        'body': json.dumps({'error': 'Method not allowed'})
    }


def handle_calibration(event, method):
    """Handle calibration endpoints"""
    
    if method == 'GET':
        # GET /v2/calibration/status
        return get_calibration_status()
    
    elif method == 'POST':
        # POST /v2/calibration/update
        body = json.loads(event.get('body', '{}'))
        return update_calibration(body)
    
    return {
        'statusCode': 405,
        'headers': CORS_HEADERS,
        'body': json.dumps({'error': 'Method not allowed'})
    }


# Energy Profile Functions

def list_energy_profiles():
    """List all available energy profiles"""
    
    # Mock data for now - replace with database query
    profiles = [
        {
            'profile_id': 'test_suite_main_a1b2c3d',
            'workload_name': 'Test Suite',
            'branch': 'main',
            'commit_sha': 'a1b2c3d',
            'timestamp': '2025-12-08T10:00:00Z',
            'total_energy_j': 12500,
            'total_carbon_g': 1.512
        },
        {
            'profile_id': 'build_process_main_e4f5g6h',
            'workload_name': 'Build Process',
            'branch': 'main',
            'commit_sha': 'e4f5g6h',
            'timestamp': '2025-12-08T11:00:00Z',
            'total_energy_j': 25000,
            'total_carbon_g': 3.025
        }
    ]
    
    return {
        'statusCode': 200,
        'headers': CORS_HEADERS,
        'body': json.dumps({
            'profiles': profiles,
            'count': len(profiles)
        })
    }


def get_energy_profile(profile_id: str):
    """Get detailed energy profile"""
    
    # Mock data - replace with database query
    profiler = EnergyProfiler()
    converter = CarbonConverter()
    
    # Simulate profile data
    profile_data = {
        'cpu': 5000,
        'gpu': 3000,
        'ram': 2000,
        'disk': 1500,
        'network': 1000
    }
    
    phases = [
        {'name': 'initialization', 'energy_j': 2000, 'duration_s': 5},
        {'name': 'processing', 'energy_j': 8000, 'duration_s': 20},
        {'name': 'cleanup', 'energy_j': 2500, 'duration_s': 7}
    ]
    
    # Analyze profile
    analysis = profiler.analyze_profile(profile_data, phases)
    
    # Add carbon calculations
    total_energy = sum(profile_data.values())
    carbon_data = converter.convert_energy_to_carbon(total_energy, profile_data)
    
    return {
        'statusCode': 200,
        'headers': CORS_HEADERS,
        'body': json.dumps({
            'profile_id': profile_id,
            'workload_name': 'Test Suite',
            'branch': 'main',
            'commit_sha': profile_id.split('_')[-1],
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'total_energy_j': total_energy,
            'total_carbon_g': carbon_data['total_carbon_g'],
            'carbon_equivalent': carbon_data['equivalent'],
            'components': profile_data,
            'phases': phases,
            'hotspots': analysis['hotspots'],
            'recommendations': analysis['recommendations'],
            'avg_power_w': total_energy / sum(p['duration_s'] for p in phases)
        })
    }


def create_energy_profile(data: Dict[str, Any]):
    """Create new energy profile from measurement data"""
    
    # Validate required fields
    required = ['workload_name', 'branch', 'commit_sha', 'components', 'phases']
    for field in required:
        if field not in data:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': f'Missing required field: {field}'})
            }
    
    # Generate profile ID
    profile_id = f"{data['workload_name']}_{data['branch']}_{data['commit_sha']}"
    
    # Calculate totals
    total_energy = sum(data['components'].values())
    converter = CarbonConverter()
    carbon_data = converter.convert_energy_to_carbon(total_energy, data['components'])
    
    # Store in database (mock for now)
    profile = {
        'profile_id': profile_id,
        'workload_name': data['workload_name'],
        'branch': data['branch'],
        'commit_sha': data['commit_sha'],
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'total_energy_j': total_energy,
        'total_carbon_g': carbon_data['total_carbon_g'],
        'components': data['components'],
        'phases': data['phases']
    }
    
    return {
        'statusCode': 201,
        'headers': CORS_HEADERS,
        'body': json.dumps({
            'message': 'Profile created successfully',
            'profile': profile
        })
    }


# Regression Tracking Functions

def get_regression_data(branch: str, workload: str):
    """Get regression tracking data for branch/workload"""
    
    detector = EnergyRegressionDetector()
    
    # Mock baseline and measurements
    baseline = 5000
    measurements = [
        {'commit_sha': 'a1b2c3d', 'energy_j': 4900, 'timestamp': '2025-12-01T10:00:00Z'},
        {'commit_sha': 'e4f5g6h', 'energy_j': 5100, 'timestamp': '2025-12-02T10:00:00Z'},
        {'commit_sha': 'i7j8k9l', 'energy_j': 4950, 'timestamp': '2025-12-03T10:00:00Z'},
        {'commit_sha': 'm0n1o2p', 'energy_j': 5200, 'timestamp': '2025-12-04T10:00:00Z'},
        {'commit_sha': 'q3r4s5t', 'energy_j': 5800, 'timestamp': '2025-12-05T10:00:00Z'},
        {'commit_sha': 'u6v7w8x', 'energy_j': 5750, 'timestamp': '2025-12-06T10:00:00Z'},
        {'commit_sha': 'y9z0a1b', 'energy_j': 5100, 'timestamp': '2025-12-07T10:00:00Z'},
        {'commit_sha': 'c2d3e4f', 'energy_j': 4800, 'timestamp': '2025-12-08T10:00:00Z'}
    ]
    
    # Detect regressions
    results = []
    for m in measurements:
        result = detector.detect_regression(m['energy_j'], baseline, m['commit_sha'])
        result['timestamp'] = m['timestamp']
        results.append(result)
    
    # Calculate trend
    energies = [m['energy_j'] for m in measurements]
    trend_data = detector.calculate_trend(energies)
    
    return {
        'statusCode': 200,
        'headers': CORS_HEADERS,
        'body': json.dumps({
            'branch': branch,
            'workload': workload,
            'baseline': baseline,
            'measurements': results,
            'trend': trend_data['trend'],
            'slope': trend_data['slope'],
            'regressions': [r for r in results if r['is_regression']]
        })
    }


def add_regression_measurement(data: Dict[str, Any]):
    """Add new regression measurement"""
    
    # Validate required fields
    required = ['branch', 'workload', 'commit_sha', 'energy_j']
    for field in required:
        if field not in data:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': f'Missing required field: {field}'})
            }
    
    detector = EnergyRegressionDetector()
    
    # Get baseline (mock for now)
    baseline = 5000
    
    # Detect regression
    result = detector.detect_regression(
        data['energy_j'],
        baseline,
        data['commit_sha']
    )
    
    # Store in database (mock for now)
    measurement = {
        'measurement_id': f"{data['branch']}_{data['workload']}_{data['commit_sha']}",
        'branch': data['branch'],
        'workload': data['workload'],
        'commit_sha': data['commit_sha'],
        'energy_j': data['energy_j'],
        'baseline': baseline,
        'diff_percent': result['diff_percent'],
        'is_regression': result['is_regression'],
        'severity': result['severity'],
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    
    return {
        'statusCode': 201,
        'headers': CORS_HEADERS,
        'body': json.dumps({
            'message': 'Measurement added successfully',
            'measurement': measurement,
            'regression_detected': result['is_regression']
        })
    }


# Calibration Functions

def get_calibration_status():
    """Get calibration status"""
    
    # Mock calibration data
    status = {
        'calibration_enabled': FeatureFlags.GMT_CALIBRATION,
        'instance_types_calibrated': 5,
        'total_samples': 150,
        'average_accuracy_improvement': 15.3,
        'last_updated': '2025-12-08T10:00:00Z',
        'calibrations': [
            {
                'instance_type': 't3.medium',
                'calibration_factor': 1.05,
                'confidence': 0.92,
                'sample_count': 30
            },
            {
                'instance_type': 't3.large',
                'calibration_factor': 0.98,
                'confidence': 0.95,
                'sample_count': 40
            }
        ]
    }
    
    return {
        'statusCode': 200,
        'headers': CORS_HEADERS,
        'body': json.dumps(status)
    }


def update_calibration(data: Dict[str, Any]):
    """Update calibration with new measurement"""
    
    # Validate required fields
    required = ['instance_type', 'gmt_measurement', 'teads_estimate']
    for field in required:
        if field not in data:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': f'Missing required field: {field}'})
            }
    
    # Calculate calibration factor
    calibration_factor = data['gmt_measurement'] / data['teads_estimate']
    
    # Store in database (mock for now)
    calibration = {
        'calibration_id': f"{data['instance_type']}_{datetime.utcnow().timestamp()}",
        'instance_type': data['instance_type'],
        'gmt_measurement': data['gmt_measurement'],
        'teads_estimate': data['teads_estimate'],
        'calibration_factor': calibration_factor,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    
    return {
        'statusCode': 201,
        'headers': CORS_HEADERS,
        'body': json.dumps({
            'message': 'Calibration updated successfully',
            'calibration': calibration
        })
    }


# Test Suite Optimizer Functions

def handle_optimize_test_suite(event, method):
    """Handle test suite optimization endpoint"""
    
    if method == 'POST':
        # POST /v2/optimize-test-suite - Analyze and optimize test suite
        body = json.loads(event.get('body', '{}'))
        return optimize_test_suite(body)
    
    return {
        'statusCode': 405,
        'headers': CORS_HEADERS,
        'body': json.dumps({'error': 'Method not allowed'})
    }


def optimize_test_suite(data: Dict[str, Any]):
    """Analyze test suite and provide optimization recommendations"""
    
    # Validate required fields
    if 'profile_data' not in data:
        return {
            'statusCode': 400,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Missing required field: profile_data'})
        }
    
    profile_data = data['profile_data']
    test_metadata = data.get('test_metadata', {})
    
    # Validate profile_data structure
    if 'components' not in profile_data:
        return {
            'statusCode': 400,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'profile_data must contain components'})
        }
    
    # Run optimizer
    optimizer = TestSuiteOptimizer()
    analysis = optimizer.analyze_test_suite(profile_data, test_metadata)
    
    return {
        'statusCode': 200,
        'headers': CORS_HEADERS,
        'body': json.dumps({
            'message': 'Test suite analysis complete',
            'analysis': analysis,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    }
