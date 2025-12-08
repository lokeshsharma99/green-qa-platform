"""
Test History API Handler for Green QA Platform

Stores and retrieves test execution history with:
- SCI calculations for both default and optimal regions
- Carbon savings comparison
- Pipeline trigger status

Endpoints:
- POST /history - Store a new test execution result
- GET /history - Retrieve test history
- GET /history/stats - Get aggregated statistics
"""

import boto3
import json
import os
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ============================================================================
# CONFIGURATION
# ============================================================================

TABLE_NAME = os.environ.get('TEST_HISTORY_TABLE', 'green_qa_test_history')
CARBON_TABLE = os.environ.get('DYNAMODB_TABLE', 'green_qa_carbon_intensity')
DEFAULT_REGION = 'eu-west-2'

# Cloud Carbon Footprint constants
CCF = {
    'PUE': 1.135,
    'VCPU_TDP_WATTS': 10,
    'MEMORY_COEFF': 0.000392,
    'EMBODIED_G_PER_VCPU_HOUR': 2.5
}

# Fallback carbon intensities (gCO2/kWh)
FALLBACK_INTENSITY = {
    'eu-west-2': 250,
    'eu-north-1': 30,
    'eu-west-1': 300,
    'eu-west-3': 60,
    'eu-central-1': 380,
    'us-east-1': 420,
    'us-west-2': 280,
    'ap-northeast-1': 450,
    'ap-southeast-1': 400,
}


# ============================================================================
# HELPER CLASSES
# ============================================================================

class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles Decimal types from DynamoDB."""
    def default(self, obj):
        if isinstance(Decimal, type(obj)):
            return float(obj)
        return super().default(obj)


# ============================================================================
# SCI CALCULATION
# ============================================================================

def calculate_sci(
    duration_minutes: float,
    vcpu_count: int,
    memory_gb: float,
    carbon_intensity: float
) -> Dict:
    """
    Calculate Software Carbon Intensity using GSF formula.
    SCI = ((E × I) + M) / R
    
    Returns detailed breakdown.
    """
    duration_hours = duration_minutes / 60
    
    # Energy calculation (kWh)
    compute_kwh = (vcpu_count * CCF['VCPU_TDP_WATTS'] * duration_hours) / 1000
    memory_kwh = memory_gb * duration_hours * CCF['MEMORY_COEFF']
    total_energy_kwh = (compute_kwh + memory_kwh) * CCF['PUE']
    
    # Operational carbon (E × I)
    operational_g = total_energy_kwh * carbon_intensity
    
    # Embodied carbon (M)
    embodied_g = vcpu_count * duration_hours * CCF['EMBODIED_G_PER_VCPU_HOUR']
    
    # Total SCI
    total_g = operational_g + embodied_g
    
    return {
        'energy_kwh': round(total_energy_kwh, 6),
        'operational_g': round(operational_g, 4),
        'embodied_g': round(embodied_g, 4),
        'total_g': round(total_g, 4),
        'carbon_intensity': carbon_intensity,
        'sci': round(total_g, 4)
    }


def calculate_savings(default_sci: float, optimal_sci: float) -> Dict:
    """
    Calculate carbon savings between default and optimal region.
    
    Returns savings in grams and percentage.
    """
    if default_sci <= 0:
        return {'savings_g': 0, 'savings_percent': 0}
    
    savings_g = default_sci - optimal_sci
    savings_percent = (savings_g / default_sci) * 100 if default_sci > 0 else 0
    
    return {
        'savings_g': round(savings_g, 4),
        'savings_percent': round(savings_percent, 2)
    }


# ============================================================================
# CARBON INTENSITY FETCHING
# ============================================================================

def get_carbon_intensity(region: str) -> float:
    """
    Get carbon intensity for a region from DynamoDB or fallback.
    """
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(CARBON_TABLE)
        
        response = table.query(
            KeyConditionExpression='region_id = :r',
            ExpressionAttributeValues={':r': region},
            ScanIndexForward=False,
            Limit=1
        )
        
        if response.get('Items'):
            return float(response['Items'][0].get('carbon_intensity', FALLBACK_INTENSITY.get(region, 300)))
    except Exception as e:
        logger.warning(f"Error fetching carbon intensity for {region}: {e}")
    
    return FALLBACK_INTENSITY.get(region, 300)


def get_optimal_region() -> Dict:
    """
    Find the region with lowest carbon intensity.
    Returns region code and intensity.
    """
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(CARBON_TABLE)
        
        # Scan all regions and find lowest
        response = table.scan()
        items = response.get('Items', [])
        
        if items:
            # Get latest entry for each region
            region_data = {}
            for item in items:
                region = item.get('region_id')
                timestamp = item.get('timestamp', 0)
                if region not in region_data or timestamp > region_data[region].get('timestamp', 0):
                    region_data[region] = item
            
            # Find lowest intensity
            if region_data:
                best = min(region_data.values(), key=lambda x: float(x.get('carbon_intensity', 9999)))
                return {
                    'region': best.get('region_id'),
                    'intensity': float(best.get('carbon_intensity', 300)),
                    'source': best.get('source', 'unknown')
                }
    except Exception as e:
        logger.warning(f"Error finding optimal region: {e}")
    
    # Fallback to eu-north-1 (typically lowest)
    return {
        'region': 'eu-north-1',
        'intensity': FALLBACK_INTENSITY.get('eu-north-1', 30),
        'source': 'fallback'
    }


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def store_test_result(test_data: Dict) -> Dict:
    """
    Store a test execution result in DynamoDB.
    
    Expected test_data:
    - test_suite: Name of the test suite
    - duration_minutes: Test duration
    - vcpu_count: Number of vCPUs
    - memory_gb: Memory in GB
    - optimal_region: Region where test ran (from scheduler decision)
    - optimal_intensity: Carbon intensity of optimal region
    - pipeline_status: Status of pipeline trigger
    - pipeline_execution_id: Pipeline execution ID (if triggered)
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(TABLE_NAME)
    
    # Generate unique ID
    test_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Get workload parameters
    duration = float(test_data.get('duration_minutes', 60))
    vcpu = int(test_data.get('vcpu_count', 2))
    memory = float(test_data.get('memory_gb', 4))
    
    # Get optimal region data (from scheduler decision)
    optimal_region = test_data.get('optimal_region', DEFAULT_REGION)
    optimal_intensity = float(test_data.get('optimal_intensity', 0))
    
    # If optimal intensity not provided, fetch it
    if optimal_intensity <= 0:
        optimal_intensity = get_carbon_intensity(optimal_region)
    
    # Get default region intensity for comparison
    default_intensity = get_carbon_intensity(DEFAULT_REGION)
    
    # Calculate SCI for both regions
    optimal_sci = calculate_sci(duration, vcpu, memory, optimal_intensity)
    default_sci = calculate_sci(duration, vcpu, memory, default_intensity)
    
    # Calculate savings
    savings = calculate_savings(default_sci['total_g'], optimal_sci['total_g'])
    
    # Build item
    item = {
        'test_id': test_id,
        'timestamp': timestamp,
        'test_suite': test_data.get('test_suite', 'Unknown'),
        
        # Workload parameters
        'duration_minutes': Decimal(str(duration)),
        'vcpu_count': vcpu,
        'memory_gb': Decimal(str(memory)),
        
        # Optimal region (where test ran)
        'optimal_region': optimal_region,
        'optimal_intensity': Decimal(str(optimal_intensity)),
        'optimal_sci': Decimal(str(optimal_sci['total_g'])),
        'optimal_energy_kwh': Decimal(str(optimal_sci['energy_kwh'])),
        
        # Default region (for comparison)
        'default_region': DEFAULT_REGION,
        'default_intensity': Decimal(str(default_intensity)),
        'default_sci': Decimal(str(default_sci['total_g'])),
        
        # Savings
        'savings_g': Decimal(str(savings['savings_g'])),
        'savings_percent': Decimal(str(savings['savings_percent'])),
        
        # Pipeline status
        'pipeline_status': test_data.get('pipeline_status', 'not_triggered'),
        'pipeline_execution_id': test_data.get('pipeline_execution_id', ''),
        'recommendation': test_data.get('recommendation', 'run_now'),
        
        # TTL (30 days)
        'ttl': int(datetime.now(timezone.utc).timestamp()) + (30 * 24 * 60 * 60)
    }
    
    table.put_item(Item=item)
    
    logger.info(f"Stored test result: {test_id}, savings: {savings['savings_percent']}%")
    
    return {
        'test_id': test_id,
        'timestamp': timestamp,
        'optimal_region': optimal_region,
        'optimal_intensity': optimal_intensity,
        'optimal_sci': optimal_sci['total_g'],
        'default_region': DEFAULT_REGION,
        'default_intensity': default_intensity,
        'default_sci': default_sci['total_g'],
        'savings_g': savings['savings_g'],
        'savings_percent': savings['savings_percent'],
        'pipeline_status': item['pipeline_status']
    }


def get_test_history(limit: int = 50) -> List[Dict]:
    """
    Retrieve test history from DynamoDB.
    """
    try:
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(TABLE_NAME)
        
        response = table.scan(
            Limit=limit
        )
        
        items = response.get('Items', [])
        
        # Sort by timestamp descending
        items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Convert Decimals to floats
        result = []
        for item in items[:limit]:
            result.append({
                'test_id': item.get('test_id'),
                'timestamp': item.get('timestamp'),
                'test_suite': item.get('test_suite'),
                'duration_minutes': float(item.get('duration_minutes', 0)),
                'vcpu_count': int(item.get('vcpu_count', 0)),
                'memory_gb': float(item.get('memory_gb', 0)),
                'optimal_region': item.get('optimal_region'),
                'optimal_intensity': float(item.get('optimal_intensity', 0)),
                'optimal_sci': float(item.get('optimal_sci', 0)),
                'default_region': item.get('default_region'),
                'default_intensity': float(item.get('default_intensity', 0)),
                'default_sci': float(item.get('default_sci', 0)),
                'savings_g': float(item.get('savings_g', 0)),
                'savings_percent': float(item.get('savings_percent', 0)),
                'pipeline_status': item.get('pipeline_status'),
                'recommendation': item.get('recommendation')
            })
        
        return result
    
    except Exception as e:
        logger.error(f"Error fetching test history: {e}")
        return []


def get_history_stats() -> Dict:
    """
    Get aggregated statistics from test history.
    """
    history = get_test_history(limit=1000)
    
    if not history:
        return {
            'total_tests': 0,
            'total_savings_g': 0,
            'avg_savings_percent': 0,
            'tests_optimized': 0,
            'most_used_region': DEFAULT_REGION
        }
    
    total_savings = sum(t.get('savings_g', 0) for t in history)
    avg_savings = sum(t.get('savings_percent', 0) for t in history) / len(history)
    optimized = sum(1 for t in history if t.get('savings_percent', 0) > 0)
    
    # Find most used region
    region_counts = {}
    for t in history:
        region = t.get('optimal_region', DEFAULT_REGION)
        region_counts[region] = region_counts.get(region, 0) + 1
    most_used = max(region_counts, key=region_counts.get) if region_counts else DEFAULT_REGION
    
    return {
        'total_tests': len(history),
        'total_savings_g': round(total_savings, 2),
        'avg_savings_percent': round(avg_savings, 2),
        'tests_optimized': optimized,
        'most_used_region': most_used
    }


# ============================================================================
# LAMBDA HANDLER
# ============================================================================

def lambda_handler(event: Dict, context) -> Dict:
    """
    Main Lambda handler for test history API.
    
    Routes:
    - POST /history - Store test result
    - GET /history - Get test history
    - GET /history/stats - Get statistics
    """
    http_method = event.get('httpMethod', event.get('requestContext', {}).get('http', {}).get('method', 'GET'))
    path = event.get('path', event.get('rawPath', '/history'))
    
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
    }
    
    try:
        # Handle CORS preflight
        if http_method == 'OPTIONS':
            return {'statusCode': 200, 'headers': headers, 'body': ''}
        
        # POST - Store new test result
        if http_method == 'POST':
            body = json.loads(event.get('body', '{}'))
            result = store_test_result(body)
            
            return {
                'statusCode': 201,
                'headers': headers,
                'body': json.dumps({
                    'message': 'Test result stored successfully',
                    'result': result
                })
            }
        
        # GET /history/stats - Get statistics
        if '/stats' in path:
            stats = get_history_stats()
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(stats)
            }
        
        # GET /history - Get test history
        query_params = event.get('queryStringParameters') or {}
        limit = int(query_params.get('limit', 50))
        
        history = get_test_history(limit=limit)
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'tests': history,
                'count': len(history),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }
    
    except Exception as e:
        logger.error(f"Handler error: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }


# ============================================================================
# LOCAL TESTING
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("Test History API - Local Test")
    print("=" * 60)
    
    # Test SCI calculation
    print("\n1. Testing SCI calculation...")
    sci = calculate_sci(
        duration_minutes=60,
        vcpu_count=4,
        memory_gb=8,
        carbon_intensity=250
    )
    print(f"   SCI for eu-west-2 (250 gCO2/kWh): {sci['total_g']} gCO2")
    
    sci_optimal = calculate_sci(
        duration_minutes=60,
        vcpu_count=4,
        memory_gb=8,
        carbon_intensity=30
    )
    print(f"   SCI for eu-north-1 (30 gCO2/kWh): {sci_optimal['total_g']} gCO2")
    
    # Test savings calculation
    print("\n2. Testing savings calculation...")
    savings = calculate_savings(sci['total_g'], sci_optimal['total_g'])
    print(f"   Savings: {savings['savings_g']} gCO2 ({savings['savings_percent']}%)")
    
    print("\n" + "=" * 60)
