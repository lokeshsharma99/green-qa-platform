"""
Analytics API Handler

Provides endpoints for retrieving pipeline analytics and carbon intelligence data.
"""

import json
import boto3
from datetime import datetime, timedelta
from decimal import Decimal
import logging
from typing import Dict, List

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# CORS headers
CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
}

def lambda_handler(event, context):
    """Main Lambda handler for analytics endpoints"""
    
    # Handle OPTIONS for CORS
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': ''
        }
    
    path = event.get('path', '')
    method = event.get('httpMethod', 'GET')
    
    try:
        if '/analytics/pipeline' in path:
            return handle_pipeline_analytics(event, method)
        elif '/analytics/carbon-trends' in path:
            return handle_carbon_trends(event, method)
        elif '/analytics/regional-insights' in path:
            return handle_regional_insights(event, method)
        elif '/analytics/leaderboard' in path:
            return handle_leaderboard(event, method)
        else:
            return {
                'statusCode': 404,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'Endpoint not found'})
            }
    except Exception as e:
        logger.error(f"Analytics API error: {e}")
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }


def handle_pipeline_analytics(event, method):
    """Handle pipeline analytics requests"""
    
    if method != 'GET':
        return {
            'statusCode': 405,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    # Get query parameters
    params = event.get('queryStringParameters') or {}
    pipeline_name = params.get('pipeline_name')
    days = int(params.get('days', 30))
    
    if not pipeline_name:
        return {
            'statusCode': 400,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'pipeline_name parameter required'})
        }
    
    # Get analytics data
    analytics = get_pipeline_analytics(pipeline_name, days)
    
    return {
        'statusCode': 200,
        'headers': CORS_HEADERS,
        'body': json.dumps(analytics, default=decimal_default)
    }


def handle_carbon_trends(event, method):
    """Handle carbon trends requests"""
    
    if method != 'GET':
        return {
            'statusCode': 405,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    # Get query parameters
    params = event.get('queryStringParameters') or {}
    region = params.get('region', 'eu-west-2')
    hours = int(params.get('hours', 24))
    
    # Get carbon trends
    trends = get_carbon_trends(region, hours)
    
    return {
        'statusCode': 200,
        'headers': CORS_HEADERS,
        'body': json.dumps({
            'region': region,
            'hours': hours,
            'trends': trends
        }, default=decimal_default)
    }


def handle_regional_insights(event, method):
    """Handle regional insights requests"""
    
    if method != 'GET':
        return {
            'statusCode': 405,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    # Get query parameters
    params = event.get('queryStringParameters') or {}
    date = params.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    # Get regional insights
    insights = get_regional_insights(date)
    
    return {
        'statusCode': 200,
        'headers': CORS_HEADERS,
        'body': json.dumps({
            'date': date,
            'insights': insights
        }, default=decimal_default)
    }


def handle_leaderboard(event, method):
    """Handle leaderboard requests"""
    
    if method != 'GET':
        return {
            'statusCode': 405,
            'headers': CORS_HEADERS,
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    # Get query parameters
    params = event.get('queryStringParameters') or {}
    period = params.get('period', 'monthly')
    limit = int(params.get('limit', 10))
    
    # Get leaderboard data
    leaderboard = get_carbon_leaderboard(period, limit)
    
    return {
        'statusCode': 200,
        'headers': CORS_HEADERS,
        'body': json.dumps({
            'period': period,
            'leaderboard': leaderboard
        }, default=decimal_default)
    }


def get_pipeline_analytics(pipeline_name: str, days: int = 30) -> Dict:
    """Get comprehensive pipeline analytics"""
    
    dynamodb = boto3.resource('dynamodb')
    
    # Get recent executions
    executions_table = dynamodb.Table('pipeline_executions_prod')  # Adjust table name
    
    try:
        # Query recent executions
        end_time = int(datetime.now().timestamp())
        start_time = int((datetime.now() - timedelta(days=days)).timestamp())
        
        response = executions_table.query(
            IndexName='PipelineNameIndex',
            KeyConditionExpression='pipeline_name = :pipeline_name AND #ts BETWEEN :start_time AND :end_time',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={
                ':pipeline_name': pipeline_name,
                ':start_time': start_time,
                ':end_time': end_time
            },
            ScanIndexForward=False  # Most recent first
        )
        
        executions = response.get('Items', [])
        
        if not executions:
            return {
                'pipeline_name': pipeline_name,
                'error': 'No execution data found',
                'total_executions': 0
            }
        
        # Calculate analytics
        total_executions = len(executions)
        successful = sum(1 for e in executions if e.get('status') == 'SUCCESS')
        
        total_carbon = sum(float(e.get('workload', {}).get('sci_score', 0)) for e in executions)
        total_savings = sum(float(e.get('carbon_analysis', {}).get('savings_g', 0)) for e in executions)
        
        # Decision breakdown
        decisions = {}
        for execution in executions:
            decision = execution.get('carbon_analysis', {}).get('decision', 'RUN_NOW')
            decisions[decision] = decisions.get(decision, 0) + 1
        
        # Recent trends (last 7 days)
        recent_executions = [e for e in executions if e.get('timestamp', 0) > start_time + (days - 7) * 24 * 3600]
        recent_carbon = sum(float(e.get('workload', {}).get('sci_score', 0)) for e in recent_executions)
        
        return {
            'pipeline_name': pipeline_name,
            'period_days': days,
            'summary': {
                'total_executions': total_executions,
                'successful_executions': successful,
                'success_rate': successful / total_executions if total_executions > 0 else 0,
                'total_carbon_g': round(total_carbon, 2),
                'total_savings_g': round(total_savings, 2),
                'avg_carbon_per_execution': round(total_carbon / total_executions, 2) if total_executions > 0 else 0,
                'savings_rate': round(total_savings / total_carbon * 100, 1) if total_carbon > 0 else 0
            },
            'decisions': decisions,
            'recent_trend': {
                'last_7_days_carbon': round(recent_carbon, 2),
                'last_7_days_executions': len(recent_executions)
            },
            'recent_executions': executions[:10]  # Last 10 executions
        }
        
    except Exception as e:
        logger.error(f"Error getting pipeline analytics: {e}")
        return {
            'pipeline_name': pipeline_name,
            'error': str(e)
        }


def get_carbon_trends(region: str, hours: int = 24) -> List[Dict]:
    """Get carbon intensity trends for a region"""
    
    dynamodb = boto3.resource('dynamodb')
    carbon_table = dynamodb.Table('carbon_intensity_history_prod')  # Adjust table name
    
    try:
        start_time = int((datetime.now() - timedelta(hours=hours)).timestamp())
        
        response = carbon_table.query(
            KeyConditionExpression='region = :region AND #ts >= :start_time',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={
                ':region': region,
                ':start_time': start_time
            },
            ScanIndexForward=True  # Chronological order
        )
        
        trends = []
        for item in response.get('Items', []):
            trends.append({
                'timestamp': int(item['timestamp']),
                'datetime': datetime.fromtimestamp(int(item['timestamp'])).isoformat(),
                'intensity': float(item.get('intensity', 0)),
                'source': item.get('source', 'unknown'),
                'is_realtime': item.get('is_realtime', False)
            })
        
        return trends
        
    except Exception as e:
        logger.error(f"Error getting carbon trends: {e}")
        return []


def get_regional_insights(date: str) -> List[Dict]:
    """Get regional insights for a specific date"""
    
    dynamodb = boto3.resource('dynamodb')
    insights_table = dynamodb.Table('regional_insights_prod')  # Adjust table name
    
    try:
        response = insights_table.query(
            KeyConditionExpression='#date = :date',
            ExpressionAttributeNames={'#date': 'date'},
            ExpressionAttributeValues={':date': date},
            ScanIndexForward=True  # Hour order
        )
        
        insights = []
        for item in response.get('Items', []):
            insights.append({
                'hour': int(item['hour']),
                'rankings': item.get('rankings', []),
                'opportunities': item.get('opportunities', {}),
                'data_quality': item.get('data_quality', {})
            })
        
        return insights
        
    except Exception as e:
        logger.error(f"Error getting regional insights: {e}")
        return []


def get_carbon_leaderboard(period: str, limit: int = 10) -> List[Dict]:
    """Get carbon savings leaderboard"""
    
    # This would require aggregating data across pipelines
    # For now, return a placeholder structure
    return [
        {
            'rank': 1,
            'pipeline_name': 'example-pipeline-1',
            'total_savings_g': 1250.5,
            'executions': 45,
            'savings_rate': 22.3
        }
    ]


def decimal_default(obj):
    """JSON serializer for Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")