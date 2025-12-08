"""
Enhanced API Handler with Research-Backed Features

This module wraps the existing handler with new features that can be toggled on/off.
All existing endpoints continue to work exactly as before.

New endpoints (feature-flagged):
- GET  /v2/forecast          - CarbonX forecasting with uncertainty
- GET  /v2/excess-power      - Excess Power metric (replaces MCI)
- GET  /v2/rank-regions      - MAIZX region ranking
- POST /v2/optimize-schedule - Slack-aware scheduling

Usage:
    Enable features via environment variables:
    ENABLE_EXCESS_POWER=true
    ENABLE_CARBONX_FORECAST=true
"""

import sys
import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional

# Add carbon_ingestion to path
sys.path.insert(0, '/var/task')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import existing handler (backward compatibility)
from handler import (
    lambda_handler as original_handler,
    cors_response,
    get_optimal_regions,
    get_current_intensity,
    get_all_regions,
    calculate_carbon_footprint
)

# Import new feature modules
try:
    from carbon_ingestion.feature_flags import get_feature_flags, Feature
    from carbon_ingestion.excess_power_calculator import ExcessPowerCalculator
    from carbon_ingestion.carbonx_forecaster import CarbonXForecaster
    from carbon_ingestion.maizx_ranker import MAIZXRanker, WorkloadSpec
    from carbon_ingestion.slack_scheduler import SlackAwareScheduler
    FEATURES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"New features not available: {e}")
    FEATURES_AVAILABLE = False

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_excess_power_data(region: str) -> Dict:
    """
    Get Excess Power metric for a region with REAL data.
    
    Feature: EXCESS_POWER_METRIC
    Research: "Moving Beyond Marginal Carbon Intensity" paper
    
    Data sources (in order of preference):
    1. ElectricityMaps API (if token available)
    2. DynamoDB carbon intensity data (estimated grid parameters)
    """
    try:
        calculator = ExcessPowerCalculator(region)
        
        # Map AWS region to grid zone (for ElectricityMaps)
        region_to_grid_zone = {
            'eu-west-2': 'GB',
            'eu-west-1': 'IE',
            'eu-central-1': 'DE',
            'us-east-1': 'US-CAL-CISO',
            'us-west-2': 'US-NW-PACW',
            'us-west-1': 'US-CAL-CISO',
            'ap-southeast-1': 'SG',
            'ap-northeast-1': 'JP',
        }
        
        grid_zone = region_to_grid_zone.get(region, region)
        
        # Get real grid data (with automatic fallback)
        grid_data = calculator.get_grid_data_from_electricitymaps(grid_zone)
        
        # Calculate excess power
        excess_power_data = calculator.calculate_excess_power(
            timestamp=datetime.now(),
            total_generation_mw=grid_data['total_generation_mw'],
            demand_mw=grid_data['demand_mw'],
            renewable_generation_mw=grid_data['renewable_generation_mw'],
            grid_capacity_mw=grid_data['grid_capacity_mw']
        )
        
        # Add data source info
        excess_power_data['data_source'] = grid_data['source']
        if 'note' in grid_data:
            excess_power_data['note'] = grid_data['note']
        if 'carbon_intensity' in grid_data:
            excess_power_data['carbon_intensity'] = grid_data['carbon_intensity']
        
        return excess_power_data
    
    except Exception as e:
        logger.error(f"Error calculating excess power: {e}")
        # Return error response instead of raising
        return {
            'region': region,
            'error': str(e),
            'recommendation': 'UNAVAILABLE',
            'confidence': 'NONE',
            'reasoning': 'Could not fetch grid data',
            'timestamp': datetime.now().isoformat()
        }


def get_carbon_forecast(region: str, hours_ahead: int = 24) -> Dict:
    """
    Get carbon intensity forecast with uncertainty quantification.
    
    Feature: CARBONX_FORECASTING
    Research: "CarbonX" paper
    
    Automatically fetches historical data from DynamoDB.
    """
    try:
        forecaster = CarbonXForecaster(region)
        
        # Generate forecast (will auto-fetch historical data)
        forecast_data = forecaster.forecast_with_uncertainty(
            historical_data=None,  # Auto-fetch from DynamoDB
            hours_ahead=hours_ahead,
            confidence_level=0.95
        )
        
        return forecast_data
    
    except Exception as e:
        logger.error(f"Error generating forecast: {e}")
        raise


def get_maizx_ranking(workload_spec: Dict, regions_data: Dict) -> Dict:
    """
    Get MAIZX ranking for multi-region optimization.
    
    Feature: MAIZX_RANKING
    Research: "MAIZX" paper - 85.68% CO2 reduction
    """
    try:
        # Parse workload spec
        workload = WorkloadSpec(
            duration_hours=workload_spec.get('duration_hours', 4.0),
            cpu_utilization=workload_spec.get('cpu_utilization', 0.7),
            memory_gb=workload_spec.get('memory_gb', 16.0),
            vcpu_count=workload_spec.get('vcpu_count', 8),
            deadline_hours=workload_spec.get('deadline_hours'),
            priority=workload_spec.get('priority', 'normal')
        )
        
        # Create ranker with custom weights if provided
        weights = workload_spec.get('weights', {})
        ranker = MAIZXRanker(
            w1=weights.get('current_cfp', 0.4),
            w2=weights.get('forecast_cfp', 0.3),
            w3=weights.get('cp_ratio', 0.2),
            w4=weights.get('schedule', 0.1)
        )
        
        # Get recommendation
        recommendation = ranker.recommend_optimal_region(workload, regions_data)
        
        return recommendation
    
    except Exception as e:
        logger.error(f"Error calculating MAIZX ranking: {e}")
        raise


def get_optimal_schedule(workload_spec: Dict) -> Dict:
    """
    Get optimal schedule with slack time consideration.
    
    Feature: SLACK_SCHEDULING
    Research: "CarbonFlex" paper - 57% carbon reduction
    """
    try:
        scheduler = SlackAwareScheduler()
        
        # Extract parameters
        region = workload_spec.get('region', 'eu-west-2')
        workload_duration_hours = workload_spec.get('workload_duration_hours', 4.0)
        deadline_hours = workload_spec.get('deadline_hours', 12.0)
        current_carbon_intensity = workload_spec.get('current_carbon_intensity', 250.0)
        vcpu_count = workload_spec.get('vcpu_count', 8)
        memory_gb = workload_spec.get('memory_gb', 16.0)
        
        # Get optimal schedule
        result = scheduler.optimize_schedule(
            region=region,
            workload_duration_hours=workload_duration_hours,
            deadline_hours=deadline_hours,
            current_carbon_intensity=current_carbon_intensity,
            vcpu_count=vcpu_count,
            memory_gb=memory_gb
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Error optimizing schedule: {e}")
        return {
            'error': str(e),
            'message': 'Failed to optimize schedule'
        }


def enhanced_current_intensity(region: str) -> Dict:
    """
    Enhanced version of current intensity with Excess Power metric.
    
    Backward compatible: returns all original fields plus new ones.
    """
    # Get original data
    original_data = get_current_intensity(region)
    
    if not original_data:
        return None
    
    # Check if Excess Power feature is enabled
    flags = get_feature_flags()
    if flags.is_enabled(Feature.EXCESS_POWER_METRIC, region=region):
        try:
            # Add Excess Power data
            excess_power = get_excess_power_data(region)
            original_data['excess_power'] = excess_power
            original_data['enhanced'] = True
        except Exception as e:
            logger.warning(f"Could not add Excess Power data: {e}")
            original_data['enhanced'] = False
    else:
        original_data['enhanced'] = False
    
    return original_data


def enhanced_optimal_regions(limit: int = 5) -> Dict:
    """
    Enhanced version with MAIZX ranking (when enabled).
    
    Backward compatible: returns original format plus optional ranking scores.
    """
    # Get original data
    original_regions = get_optimal_regions(limit)
    
    # Check if MAIZX ranking is enabled
    flags = get_feature_flags()
    if flags.is_enabled(Feature.MAIZX_RANKING):
        try:
            # TODO: Add MAIZX ranking scores
            # For now, just add placeholder
            for region in original_regions:
                region['maizx_score'] = region['intensity']  # Placeholder
                region['ranking_method'] = 'MAIZX'
        except Exception as e:
            logger.warning(f"Could not add MAIZX ranking: {e}")
    
    return {
        'optimal_regions': original_regions,
        'ranking_method': 'MAIZX' if flags.is_enabled(Feature.MAIZX_RANKING) else 'carbon_intensity',
        'timestamp': datetime.utcnow().isoformat()
    }


def lambda_handler(event: Dict, context) -> Dict:
    """
    Enhanced API handler with backward compatibility.
    
    All existing endpoints work exactly as before.
    New v2 endpoints are feature-flagged.
    """
    
    try:
        path = event.get('path', '').rstrip('/')
        method = event.get('httpMethod', 'GET')
        params = event.get('queryStringParameters') or {}
        
        # Parse body for POST requests
        body = {}
        if method == 'POST' and event.get('body'):
            try:
                body = json.loads(event.get('body'))
            except json.JSONDecodeError:
                return cors_response(400, {'error': 'Invalid JSON in request body'})
        
        logger.info(f"{method} {path} - Enhanced handler")
        
        # Check if features are available
        if not FEATURES_AVAILABLE:
            # Fall back to original handler
            logger.info("Features not available, using original handler")
            return original_handler(event, context)
        
        flags = get_feature_flags()
        
        # ===== NEW V2 ENDPOINTS (Feature-Flagged) =====
        
        # V2: Excess Power endpoint
        if path == '/v2/excess-power' and method == 'GET':
            if not flags.is_enabled(Feature.EXCESS_POWER_METRIC):
                return cors_response(403, {
                    'error': 'Feature not enabled',
                    'feature': 'EXCESS_POWER_METRIC',
                    'message': 'Set ENABLE_EXCESS_POWER=true to enable this feature'
                })
            
            region = params.get('region', 'eu-west-2')
            data = get_excess_power_data(region)
            return cors_response(200, data)
        
        # V2: Forecast endpoint
        elif path == '/v2/forecast' and method == 'GET':
            if not flags.is_enabled(Feature.CARBONX_FORECASTING):
                return cors_response(403, {
                    'error': 'Feature not enabled',
                    'feature': 'CARBONX_FORECASTING',
                    'message': 'Set ENABLE_CARBONX_FORECAST=true to enable this feature'
                })
            
            region = params.get('region', 'eu-west-2')
            hours_ahead = int(params.get('hours_ahead', 24))
            
            data = get_carbon_forecast(region, hours_ahead)
            return cors_response(200, data)
        
        # V2: MAIZX ranking endpoint
        elif path == '/v2/rank-regions' and method == 'POST':
            if not flags.is_enabled(Feature.MAIZX_RANKING):
                return cors_response(403, {
                    'error': 'Feature not enabled',
                    'feature': 'MAIZX_RANKING',
                    'message': 'Set ENABLE_MAIZX_RANKING=true to enable this feature'
                })
            
            workload_spec = body.get('workload', {})
            regions_data = body.get('regions', {})
            
            if not regions_data:
                return cors_response(400, {
                    'error': 'Missing regions data',
                    'message': 'Provide regions with carbon intensity: {"regions": {"eu-west-2": 250, ...}}'
                })
            
            data = get_maizx_ranking(workload_spec, regions_data)
            return cors_response(200, data)
        
        # V2: Optimize schedule endpoint
        elif path == '/v2/optimize-schedule' and method == 'POST':
            if not flags.is_enabled(Feature.SLACK_SCHEDULING):
                return cors_response(403, {
                    'error': 'Feature not enabled',
                    'feature': 'SLACK_SCHEDULING',
                    'message': 'Set ENABLE_SLACK_SCHEDULING=true to enable this feature'
                })
            
            data = get_optimal_schedule(body)
            return cors_response(200, data)
        
        # V2: Feature status endpoint
        elif path == '/v2/features' and method == 'GET':
            enabled_features = flags.get_enabled_features()
            return cors_response(200, {
                'features': {
                    'excess_power_metric': flags.is_enabled(Feature.EXCESS_POWER_METRIC),
                    'carbonx_forecasting': flags.is_enabled(Feature.CARBONX_FORECASTING),
                    'maizx_ranking': flags.is_enabled(Feature.MAIZX_RANKING),
                    'slack_scheduling': flags.is_enabled(Feature.SLACK_SCHEDULING),
                },
                'enabled_count': len(enabled_features),
                'enabled_features': enabled_features
            })
        
        # ===== ENHANCED EXISTING ENDPOINTS (Backward Compatible) =====
        
        # Enhanced /current endpoint
        elif path == '/current' and method == 'GET':
            region = params.get('region', 'eu-west-2')
            data = enhanced_current_intensity(region)
            
            if not data:
                return cors_response(404, {'error': f'No data found for region {region}'})
            
            return cors_response(200, data)
        
        # Enhanced /optimal endpoint
        elif path == '/optimal' and method == 'GET':
            limit = int(params.get('limit', 5))
            data = enhanced_optimal_regions(limit)
            return cors_response(200, data)
        
        # ===== FALLBACK TO ORIGINAL HANDLER =====
        else:
            # All other endpoints use original handler
            return original_handler(event, context)
    
    except Exception as e:
        logger.error(f"Enhanced handler error: {e}", exc_info=True)
        return cors_response(500, {'error': str(e)})


if __name__ == '__main__':
    # Test enhanced handler
    print("=== Enhanced API Handler Test ===\n")
    
    # Test feature status
    print("1. Testing /v2/features endpoint...")
    event = {'path': '/v2/features', 'httpMethod': 'GET'}
    response = lambda_handler(event, None)
    print(f"   Status: {response['statusCode']}")
    print(f"   Body: {response['body']}\n")
    
    # Test enhanced current (should work even without features enabled)
    print("2. Testing enhanced /current endpoint...")
    event = {'path': '/current', 'httpMethod': 'GET', 'queryStringParameters': {'region': 'eu-west-2'}}
    response = lambda_handler(event, None)
    print(f"   Status: {response['statusCode']}")
    
    print("\n=== Tests complete ===")
