"""
Green QA Platform - API Lambda Handler
Provides REST API endpoints for dashboard and CI/CD integration
"""
import boto3
import json
import os
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuration
CARBON_TABLE = os.environ.get('CARBON_TABLE', 'green-qa-carbon-intensity-prod')
HISTORY_TABLE = os.environ.get('HISTORY_TABLE', 'green-qa-test-history-prod')

dynamodb = boto3.resource('dynamodb')
carbon_table = dynamodb.Table(CARBON_TABLE)
history_table = dynamodb.Table(HISTORY_TABLE)


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder for DynamoDB Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def cors_response(status_code: int, body: Dict) -> Dict:
    """Create CORS-enabled response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps(body, cls=DecimalEncoder)
    }


def get_optimal_regions(limit: int = 5) -> List[Dict]:
    """Get regions with lowest carbon intensity"""
    try:
        # Get latest data for all regions
        regions_data = []
        
        # Scan for latest entries (in production, use GSI with timestamp)
        response = carbon_table.scan()
        items = response.get('Items', [])
        
        # Group by region and get latest
        region_latest = {}
        for item in items:
            region = item['region_id']
            timestamp = int(item['timestamp'])
            
            if region not in region_latest or timestamp > region_latest[region]['timestamp']:
                region_latest[region] = {
                    'region': region,
                    'intensity': float(item['carbon_intensity']),
                    'source': item.get('source', 'unknown'),
                    'timestamp': timestamp,
                    'is_realtime': item.get('is_realtime', False),
                    'country': item.get('country', ''),
                    'location': f"{item.get('country', '')} - {region}"
                }
        
        # Sort by intensity
        regions_data = sorted(region_latest.values(), key=lambda x: x['intensity'])
        
        return regions_data[:limit]
    
    except Exception as e:
        logger.error(f"Error getting optimal regions: {e}")
        return []


def get_current_intensity(region: str) -> Optional[Dict]:
    """Get current carbon intensity for a region"""
    try:
        # Query latest entry for region
        response = carbon_table.query(
            KeyConditionExpression=Key('region_id').eq(region),
            ScanIndexForward=False,
            Limit=1
        )
        
        items = response.get('Items', [])
        if not items:
            return None
        
        item = items[0]
        return {
            'region': region,
            'carbon_intensity': float(item['carbon_intensity']),
            'source': item.get('source', 'unknown'),
            'source_name': item.get('source_name', ''),
            'is_realtime': item.get('is_realtime', False),
            'timestamp': datetime.fromtimestamp(int(item['timestamp'])).isoformat(),
            'index': item.get('index'),
            'forecast': json.loads(item.get('forecast', '[]')) if item.get('forecast') else []
        }
    
    except Exception as e:
        logger.error(f"Error getting current intensity for {region}: {e}")
        return None


def get_all_regions() -> List[Dict]:
    """Get carbon intensity for all regions"""
    try:
        response = carbon_table.scan()
        items = response.get('Items', [])
        
        # Group by region and get latest
        region_latest = {}
        for item in items:
            region = item['region_id']
            timestamp = int(item['timestamp'])
            
            if region not in region_latest or timestamp > region_latest[region]['timestamp']:
                region_latest[region] = {
                    'region': region,
                    'intensity': float(item['carbon_intensity']),
                    'source': item.get('source', 'unknown'),
                    'source_name': item.get('source_name', ''),
                    'is_realtime': item.get('is_realtime', False),
                    'country': item.get('country', ''),
                    'timestamp': datetime.fromtimestamp(timestamp).isoformat()
                }
        
        # Sort by intensity
        regions_data = sorted(region_latest.values(), key=lambda x: x['intensity'])
        
        return regions_data
    
    except Exception as e:
        logger.error(f"Error getting all regions: {e}")
        return []


def calculate_carbon_footprint(region: str, duration_seconds: int, 
                               vcpu_count: int = 2, memory_gb: float = 4.0) -> Dict:
    """Calculate carbon footprint for a test execution"""
    try:
        # Get current intensity
        intensity_data = get_current_intensity(region)
        if not intensity_data:
            # Fallback to default
            carbon_intensity = 300
        else:
            carbon_intensity = intensity_data['carbon_intensity']
        
        # Constants from Cloud Carbon Footprint methodology
        # Sources: https://sustainability.aboutamazon.com/2024-amazon-sustainability-report-aws-summary.pdf
        PUE = 1.15  # AWS average PUE (2024 Sustainability Report)
        VCPU_TDP_WATTS = 10.0  # Intel Xeon Scalable (Watts per vCPU)
        MEMORY_COEFFICIENT_KWH_PER_GB = 0.000392  # Memory power (kWh per GB-hour)
        EMBODIED_EMISSIONS_G_PER_VCPU_HOUR = 2.5  # Manufacturing emissions (gCO2 per vCPU-hour)
        
        duration_hours = duration_seconds / 3600
        
        # Compute energy
        compute_kwh = (vcpu_count * VCPU_TDP_WATTS * duration_hours) / 1000
        
        # Memory energy
        memory_kwh = memory_gb * duration_hours * MEMORY_COEFFICIENT_KWH_PER_GB
        
        # Total with PUE
        total_energy_kwh = (compute_kwh + memory_kwh) * PUE
        
        # Embodied carbon
        embodied_carbon_g = vcpu_count * duration_hours * EMBODIED_EMISSIONS_G_PER_VCPU_HOUR
        
        # Operational emissions
        operational_emissions_g = total_energy_kwh * carbon_intensity
        
        # Total emissions
        total_emissions_g = operational_emissions_g + embodied_carbon_g
        
        # SCI score (per test run)
        sci = total_emissions_g
        
        return {
            'region': region,
            'duration_seconds': duration_seconds,
            'vcpu_count': vcpu_count,
            'memory_gb': memory_gb,
            'carbon_intensity_gco2_kwh': carbon_intensity,
            'pue': PUE,
            'compute_energy_kwh': round(compute_kwh, 6),
            'memory_energy_kwh': round(memory_kwh, 6),
            'total_energy_kwh': round(total_energy_kwh, 6),
            'operational_emissions_g': round(operational_emissions_g, 4),
            'embodied_carbon_g': round(embodied_carbon_g, 4),
            'carbon_emissions_g': round(total_emissions_g, 4),
            'carbon_emissions_kg': round(total_emissions_g / 1000, 6),
            'sci': round(sci, 4),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error calculating carbon footprint: {e}")
        raise


def store_test_result(test_data: Dict) -> Dict:
    """Store test execution result in history"""
    try:
        test_id = test_data.get('test_id', f"test_{int(datetime.utcnow().timestamp())}")
        timestamp = int(datetime.utcnow().timestamp())
        
        item = {
            'test_id': test_id,
            'timestamp': timestamp,
            'region_id': test_data.get('region', 'unknown'),
            'duration_seconds': test_data.get('duration_seconds', 0),
            'carbon_emissions_g': Decimal(str(test_data.get('carbon_g', 0))),
            'carbon_intensity': Decimal(str(test_data.get('carbon_intensity', 0))),
            'test_name': test_data.get('test_name', 'unknown'),
            'status': test_data.get('status', 'completed'),
            'metadata': json.dumps(test_data.get('metadata', {}))
        }
        
        history_table.put_item(Item=item)
        
        return {
            'test_id': test_id,
            'timestamp': timestamp,
            'message': 'Test result stored successfully'
        }
    
    except Exception as e:
        logger.error(f"Error storing test result: {e}")
        raise


def get_test_history(region: Optional[str] = None, limit: int = 50) -> List[Dict]:
    """Get test execution history"""
    try:
        if region:
            # Query by region using GSI
            response = history_table.query(
                IndexName='region-index',
                KeyConditionExpression=Key('region_id').eq(region),
                ScanIndexForward=False,
                Limit=limit
            )
        else:
            # Scan all (in production, use pagination)
            response = history_table.scan(Limit=limit)
        
        items = response.get('Items', [])
        
        # Format results
        history = []
        for item in items:
            history.append({
                'test_id': item['test_id'],
                'timestamp': datetime.fromtimestamp(int(item['timestamp'])).isoformat(),
                'region': item.get('region_id', 'unknown'),
                'duration_seconds': int(item.get('duration_seconds', 0)),
                'carbon_g': float(item.get('carbon_emissions_g', 0)),
                'carbon_intensity': float(item.get('carbon_intensity', 0)),
                'test_name': item.get('test_name', 'unknown'),
                'status': item.get('status', 'completed')
            })
        
        # Sort by timestamp descending
        history.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return history
    
    except Exception as e:
        logger.error(f"Error getting test history: {e}")
        return []


def lambda_handler(event: Dict, context) -> Dict:
    """
    Main API handler
    
    Routes:
        GET  /optimal       - Get optimal regions
        GET  /current       - Get current intensity for region
        GET  /regions       - Get all regions
        POST /calculate     - Calculate carbon footprint
        POST /store_result  - Store test result
        GET  /history       - Get test history
    """
    
    try:
        # Handle OPTIONS for CORS
        if event.get('httpMethod') == 'OPTIONS':
            return cors_response(200, {'message': 'OK'})
        
        path = event.get('path', '').rstrip('/')
        method = event.get('httpMethod', 'GET')
        
        # Parse query parameters
        params = event.get('queryStringParameters') or {}
        
        # Parse body for POST requests
        body = {}
        if method == 'POST' and event.get('body'):
            try:
                body = json.loads(event.get('body'))
            except json.JSONDecodeError:
                return cors_response(400, {'error': 'Invalid JSON in request body'})
        
        logger.info(f"{method} {path} - params: {params}, body: {body}")
        
        # Route handlers
        if path == '/optimal' and method == 'GET':
            limit = int(params.get('limit', 5))
            optimal = get_optimal_regions(limit)
            return cors_response(200, {
                'optimal_regions': optimal,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        elif path == '/current' and method == 'GET':
            region = params.get('region', 'eu-west-2')
            data = get_current_intensity(region)
            
            if not data:
                return cors_response(404, {'error': f'No data found for region {region}'})
            
            return cors_response(200, data)
        
        elif path == '/regions' and method == 'GET':
            regions = get_all_regions()
            return cors_response(200, {
                'regions': regions,
                'total': len(regions),
                'timestamp': datetime.utcnow().isoformat()
            })
        
        elif path == '/calculate' and method == 'POST':
            region = body.get('region', 'eu-west-2')
            duration = body.get('duration_seconds', 3600)
            vcpu = body.get('vcpu_count', 2)
            memory = body.get('memory_gb', 4.0)
            
            result = calculate_carbon_footprint(region, duration, vcpu, memory)
            return cors_response(200, result)
        
        elif path == '/store_result' and method == 'POST':
            result = store_test_result(body)
            return cors_response(200, result)
        
        elif path == '/history' and method == 'GET':
            region = params.get('region')
            limit = int(params.get('limit', 50))
            
            history = get_test_history(region, limit)
            return cors_response(200, {
                'tests': history,
                'count': len(history),
                'timestamp': datetime.utcnow().isoformat()
            })
        
        elif path == '/global-regions' and method == 'GET':
            # Import and use the global optimizer
            try:
                import sys
                sys.path.insert(0, '/var/task')
                from carbon_ingestion.aws_global_carbon_optimizer import (
                    get_all_regions_carbon_intensity,
                    AWS_REGIONS
                )
                
                regions_data = get_all_regions_carbon_intensity()
                
                # Format for dashboard
                formatted_regions = []
                for region in regions_data:
                    formatted_regions.append({
                        'region_code': region['region_code'],
                        'region_name': region['region_name'],
                        'location': region['location'],
                        'country': region['country'],
                        'grid_intensity': region['grid_intensity'],
                        'datacenter_intensity': region['datacenter_intensity'],
                        'aws_renewable_pct': region['aws_renewable_pct'],
                        'timezone': region['timezone'],
                        'lat': region['lat'],
                        'lon': region['lon']
                    })
                
                return cors_response(200, {
                    'regions': formatted_regions,
                    'total': len(formatted_regions),
                    'timestamp': datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"Error getting global regions: {e}")
                return cors_response(500, {'error': f'Failed to load global regions: {str(e)}'})
        
        elif path == '/climatiq/search' and method == 'GET':
            # Climatiq emission factor search
            try:
                import sys
                sys.path.insert(0, '/var/task')
                from carbon_ingestion.climatiq_client import ClimatiqClient
                
                query = params.get('query', '')
                region = params.get('region')
                year = params.get('year')
                unit_type = params.get('unit_type')
                limit = int(params.get('limit', 10))
                
                client = ClimatiqClient()
                results = client.search_emission_factors(
                    query=query,
                    region=region,
                    year=int(year) if year else None,
                    unit_type=unit_type,
                    results_per_page=min(limit, 20)
                )
                
                return cors_response(200, {
                    'total_results': results['total_results'],
                    'factors': results['results'],
                    'query': query,
                    'timestamp': datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"Climatiq search error: {e}")
                return cors_response(500, {'error': str(e)})
        
        elif path == '/climatiq/validate' and method == 'POST':
            # Validate our calculation against Climatiq
            try:
                import sys
                sys.path.insert(0, '/var/task')
                from carbon_ingestion.climatiq_client import ClimatiqClient
                
                region = body.get('region', 'eu-west-2')
                
                # Get our current intensity
                our_data = get_current_intensity(region)
                
                if not our_data:
                    return cors_response(404, {'error': f'No data for region {region}'})
                
                # Search Climatiq for equivalent factor
                client = ClimatiqClient()
                climatiq_results = client.search_emission_factors(
                    query=f'electricity {region}',
                    region=region,
                    year=datetime.now().year,
                    unit_type='Energy',
                    results_per_page=5
                )
                
                if climatiq_results['total_results'] > 0:
                    climatiq_factor = climatiq_results['results'][0]
                    climatiq_intensity = climatiq_factor.get('factor', 0)
                    
                    our_intensity = our_data['carbon_intensity']
                    
                    if climatiq_intensity and climatiq_intensity > 0:
                        difference = abs(our_intensity - climatiq_intensity)
                        difference_percent = (difference / our_intensity * 100)
                        
                        validation_status = 'passed' if difference_percent < 10 else 'review' if difference_percent < 25 else 'failed'
                        
                        return cors_response(200, {
                            'our_calculation': {
                                'intensity': our_intensity,
                                'source': our_data.get('source_name', 'Unknown'),
                                'is_realtime': our_data.get('is_realtime', False),
                                'timestamp': our_data.get('timestamp')
                            },
                            'climatiq_calculation': {
                                'intensity': climatiq_intensity,
                                'source': climatiq_factor.get('source', 'Unknown'),
                                'year': climatiq_factor.get('year'),
                                'name': climatiq_factor.get('name')
                            },
                            'comparison': {
                                'difference': round(difference, 2),
                                'difference_percent': round(difference_percent, 2),
                                'validation_status': validation_status
                            },
                            'timestamp': datetime.utcnow().isoformat()
                        })
                
                return cors_response(404, {'error': 'No Climatiq factors found for comparison'})
            
            except Exception as e:
                logger.error(f"Climatiq validation error: {e}")
                return cors_response(500, {'error': str(e)})
        
        else:
            return cors_response(404, {
                'error': f'Route not found: {method} {path}',
                'available_routes': [
                    'GET /optimal',
                    'GET /current?region=eu-west-2',
                    'GET /regions',
                    'GET /global-regions',
                    'POST /calculate',
                    'POST /store_result',
                    'GET /history?region=eu-west-2&limit=50',
                    'GET /climatiq/search?query=electricity&region=GB',
                    'POST /climatiq/validate'
                ]
            })
    
    except Exception as e:
        logger.error(f"Handler error: {e}", exc_info=True)
        return cors_response(500, {'error': str(e)})


if __name__ == '__main__':
    # Test locally
    print("=== API Handler Test ===\n")
    
    # Test optimal regions
    print("1. Testing /optimal endpoint...")
    event = {'path': '/optimal', 'httpMethod': 'GET', 'queryStringParameters': {'limit': '3'}}
    response = lambda_handler(event, None)
    print(f"   Status: {response['statusCode']}")
    
    # Test calculate
    print("\n2. Testing /calculate endpoint...")
    event = {
        'path': '/calculate',
        'httpMethod': 'POST',
        'body': json.dumps({
            'region': 'eu-west-2',
            'duration_seconds': 300,
            'vcpu_count': 2,
            'memory_gb': 4
        })
    }
    response = lambda_handler(event, None)
    print(f"   Status: {response['statusCode']}")
    if response['statusCode'] == 200:
        data = json.loads(response['body'])
        print(f"   Carbon: {data.get('carbon_emissions_g', 0)} g CO2")
    
    print("\n=== Tests complete ===")
