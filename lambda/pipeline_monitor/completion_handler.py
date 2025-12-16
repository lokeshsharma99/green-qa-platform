"""
Pipeline Completion Handler

EventBridge-triggered Lambda that monitors pipeline completion
and collects final execution data with accurate metrics.
"""

import json
import boto3
import os
from datetime import datetime, timezone
from pipeline_data_collector import (
    collect_pipeline_data, 
    calculate_accurate_sci,
    AWSPipelineDataCollector
)
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Handle pipeline completion events from EventBridge
    
    Event sources:
    1. CodePipeline state changes
    2. Scheduled checks for running pipelines
    3. Manual triggers for data collection
    """
    
    logger.info(f"Pipeline completion handler triggered: {json.dumps(event)}")
    
    try:
        # Determine event source and extract pipeline details
        pipeline_info = extract_pipeline_info(event)
        
        if not pipeline_info:
            logger.error("Could not extract pipeline information from event")
            return {'statusCode': 400, 'body': 'Invalid event format'}
        
        # Collect comprehensive pipeline data
        pipeline_data = collect_pipeline_data(
            pipeline_info['pipeline_name'],
            pipeline_info['execution_id'],
            pipeline_info.get('region', 'eu-west-2')
        )
        
        if pipeline_data.get('error'):
            logger.error(f"Error collecting pipeline data: {pipeline_data['error']}")
            return {'statusCode': 500, 'body': f"Data collection failed: {pipeline_data['error']}"}
        
        # Get current carbon intensity for accurate SCI calculation
        carbon_intensity = get_current_carbon_intensity(pipeline_info.get('region', 'eu-west-2'))
        
        # Calculate accurate SCI using real AWS data
        sci_calculation = calculate_accurate_sci(pipeline_data, carbon_intensity)
        
        # Store comprehensive execution record
        execution_record = create_execution_record(pipeline_data, sci_calculation, pipeline_info)
        
        # Store in DynamoDB
        success = store_execution_data(execution_record)
        
        if success:
            logger.info(f"Successfully processed pipeline completion: {pipeline_info['execution_id']}")
            
            # Send notification if configured
            send_completion_notification(execution_record)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Pipeline data collected successfully',
                    'execution_id': pipeline_info['execution_id'],
                    'sci_score': sci_calculation['sci'],
                    'carbon_intensity': carbon_intensity,
                    'duration_seconds': pipeline_data.get('duration_seconds'),
                    'status': pipeline_data.get('status')
                })
            }
        else:
            logger.error("Failed to store execution data")
            return {'statusCode': 500, 'body': 'Failed to store execution data'}
            
    except Exception as e:
        logger.error(f"Error in pipeline completion handler: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }


def extract_pipeline_info(event: dict) -> dict:
    """Extract pipeline information from various event sources"""
    
    # EventBridge CodePipeline state change
    if event.get('source') == 'aws.codepipeline':
        detail = event.get('detail', {})
        return {
            'pipeline_name': detail.get('pipeline'),
            'execution_id': detail.get('execution-id'),
            'state': detail.get('state'),
            'region': event.get('region', 'eu-west-2'),
            'event_source': 'codepipeline_state_change'
        }
    
    # Scheduled check event
    elif event.get('source') == 'aws.events' and 'pipeline_check' in str(event):
        # Custom scheduled event format
        detail = event.get('detail', {})
        return {
            'pipeline_name': detail.get('pipeline_name'),
            'execution_id': detail.get('execution_id'),
            'region': detail.get('region', 'eu-west-2'),
            'event_source': 'scheduled_check'
        }
    
    # Manual trigger (API Gateway or direct invocation)
    elif 'pipeline_name' in event and 'execution_id' in event:
        return {
            'pipeline_name': event['pipeline_name'],
            'execution_id': event['execution_id'],
            'region': event.get('region', 'eu-west-2'),
            'event_source': 'manual_trigger'
        }
    
    # Lambda test event
    elif event.get('Records'):
        # Handle SQS or SNS triggers if needed
        return None
    
    logger.warning(f"Unknown event format: {event}")
    return None


def get_current_carbon_intensity(region: str) -> float:
    """Get current carbon intensity for the region"""
    
    try:
        # Import carbon intensity fetching logic
        # This should use the same logic as the main carbon ingestion
        
        if region == 'eu-west-2':
            # UK Grid ESO API
            import urllib.request
            import json
            
            req = urllib.request.Request(
                'https://api.carbonintensity.org.uk/intensity',
                headers={'Accept': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                grid_intensity = data['data'][0]['intensity']['actual'] or data['data'][0]['intensity']['forecast']
                
                # Apply AWS datacenter formula
                aws_renewable_pct = 0.80  # 80% renewable for AWS eu-west-2
                pue = 1.15  # AWS 2024 Sustainability Report
                datacenter_intensity = grid_intensity * (1 - aws_renewable_pct) * pue
                
                return round(datacenter_intensity, 1)
        
        else:
            # ElectricityMaps API for other regions
            token = os.environ.get('ELECTRICITY_MAPS_TOKEN', '7Cq9hfFAKl0gAtYNhvc2')
            
            import urllib.request
            import json
            
            url = f'https://api.electricitymaps.com/v3/carbon-intensity/latest?dataCenterRegion={region}&dataCenterProvider=aws'
            req = urllib.request.Request(url, headers={'auth-token': token})
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                return round(data.get('carbonIntensity', 300), 1)
    
    except Exception as e:
        logger.error(f"Error fetching carbon intensity: {e}")
        return 300  # Fallback value


def create_execution_record(pipeline_data: dict, sci_calculation: dict, pipeline_info: dict) -> dict:
    """Create comprehensive execution record for storage"""
    
    # Extract build summaries
    build_summaries = []
    total_build_duration = 0
    
    for stage in pipeline_data.get('stages', []):
        for action in stage.get('actions', []):
            if action.get('build_details'):
                build_details = action['build_details']
                build_summaries.append({
                    'build_id': build_details.get('build_id'),
                    'project_name': build_details.get('project_name'),
                    'compute_type': build_details.get('compute_type'),
                    'duration_seconds': build_details.get('duration_seconds', 0),
                    'vcpu_count': build_details.get('vcpu_count', 0),
                    'memory_mb': build_details.get('memory_mb', 0),
                    'status': build_details.get('status')
                })
                total_build_duration += build_details.get('duration_seconds', 0)
    
    # Create comprehensive record
    record = {
        'execution_id': pipeline_data['execution_id'],
        'timestamp': int(datetime.now(timezone.utc).timestamp()),
        'pipeline_name': pipeline_data['pipeline_name'],
        'pipeline_region': pipeline_info.get('region', 'eu-west-2'),
        'trigger_source': 'aws_pipeline_completion',
        'status': pipeline_data.get('status', 'UNKNOWN'),
        
        # Timing information
        'timing': {
            'start_time': pipeline_data.get('start_time').isoformat() if pipeline_data.get('start_time') else None,
            'end_time': pipeline_data.get('end_time').isoformat() if pipeline_data.get('end_time') else None,
            'duration_seconds': pipeline_data.get('duration_seconds', 0),
            'total_build_duration_seconds': total_build_duration
        },
        
        # Carbon analysis (using real data)
        'carbon_analysis': {
            'calculation_method': sci_calculation.get('calculation_method', 'real_aws_data'),
            'carbon_intensity': sci_calculation['carbon_intensity'],
            'energy_kwh': sci_calculation['energy_kwh'],
            'operational_g': sci_calculation['operational_g'],
            'embodied_g': sci_calculation['embodied_g'],
            'total_g': sci_calculation['total_g'],
            'sci_score': sci_calculation['sci']
        },
        
        # Resource usage (actual AWS data)
        'resource_usage': {
            'total_vcpu_hours': sci_calculation.get('vcpu_hours', 0),
            'build_summaries': build_summaries,
            'total_builds': len(build_summaries)
        },
        
        # Pipeline structure
        'pipeline_structure': {
            'total_stages': len(pipeline_data.get('stages', [])),
            'total_actions': sum(len(stage.get('actions', [])) for stage in pipeline_data.get('stages', [])),
            'build_projects': pipeline_data.get('build_projects', [])
        },
        
        # Commit information
        'commit_details': pipeline_data.get('commit_details', {}),
        
        # Trigger information
        'trigger_details': pipeline_data.get('trigger', {}),
        
        # Event source
        'event_source': pipeline_info.get('event_source', 'unknown'),
        
        # Metadata
        'created_at': datetime.now(timezone.utc).isoformat(),
        'data_version': '2.0',  # Version of data collection
        'ttl': int((datetime.now(timezone.utc).timestamp()) + (365 * 24 * 3600))  # 1 year TTL
    }
    
    return record


def store_execution_data(execution_record: dict) -> bool:
    """Store execution data in DynamoDB"""
    
    try:
        # Import storage module
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        
        from api.pipeline_storage import store_pipeline_execution_data
        
        return store_pipeline_execution_data(execution_record)
        
    except Exception as e:
        logger.error(f"Error storing execution data: {e}")
        return False


def send_completion_notification(execution_record: dict):
    """Send completion notification if configured"""
    
    try:
        sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')
        if not sns_topic_arn:
            return
        
        sns = boto3.client('sns')
        
        # Create notification message
        status = execution_record['status']
        pipeline_name = execution_record['pipeline_name']
        duration = execution_record['timing']['duration_seconds']
        sci_score = execution_record['carbon_analysis']['sci_score']
        carbon_intensity = execution_record['carbon_analysis']['carbon_intensity']
        
        message = f"""
Pipeline Execution Complete

Pipeline: {pipeline_name}
Status: {status}
Duration: {duration // 60}m {duration % 60}s
Carbon Footprint: {sci_score:.2f}g CO₂
Carbon Intensity: {carbon_intensity} gCO₂/kWh

Execution ID: {execution_record['execution_id']}
        """.strip()
        
        sns.publish(
            TopicArn=sns_topic_arn,
            Subject=f'Pipeline {status}: {pipeline_name}',
            Message=message
        )
        
        logger.info("Completion notification sent")
        
    except Exception as e:
        logger.error(f"Error sending notification: {e}")


# Utility function for manual data collection
def collect_pipeline_data_manual(pipeline_name: str, execution_id: str, region: str = 'eu-west-2') -> dict:
    """Manual function to collect pipeline data (for testing)"""
    
    event = {
        'pipeline_name': pipeline_name,
        'execution_id': execution_id,
        'region': region
    }
    
    context = type('Context', (), {'aws_request_id': 'manual-request'})()
    
    return lambda_handler(event, context)