"""
Pipeline Data Storage Module

Handles storing pipeline execution data and carbon intelligence
to DynamoDB for analytics and reporting.
"""

import boto3
import json
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class PipelineDataStore:
    """Handles storage of pipeline execution data and carbon analytics"""
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        
        # Table names from environment or defaults
        self.executions_table = os.environ.get('PIPELINE_EXECUTIONS_TABLE', 'pipeline_executions')
        self.carbon_history_table = os.environ.get('CARBON_HISTORY_TABLE', 'carbon_intensity_history')
        self.analytics_table = os.environ.get('PIPELINE_ANALYTICS_TABLE', 'pipeline_analytics')
        self.insights_table = os.environ.get('REGIONAL_INSIGHTS_TABLE', 'regional_insights')
        
        # Initialize tables
        self.executions = self.dynamodb.Table(self.executions_table)
        self.carbon_history = self.dynamodb.Table(self.carbon_history_table)
        self.analytics = self.dynamodb.Table(self.analytics_table)
        self.insights = self.dynamodb.Table(self.insights_table)
    
    def store_pipeline_execution(self, execution_data: Dict) -> bool:
        """
        Store complete pipeline execution data
        
        Args:
            execution_data: Dictionary containing all execution details
            
        Returns:
            bool: Success status
        """
        try:
            # Convert floats to Decimal for DynamoDB
            execution_item = self._convert_to_dynamodb_format(execution_data)
            
            # Add TTL (1 year from now)
            execution_item['ttl'] = int((datetime.now() + timedelta(days=365)).timestamp())
            
            # Store execution record
            self.executions.put_item(Item=execution_item)
            
            logger.info(f"Stored pipeline execution: {execution_data['execution_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store pipeline execution: {e}")
            return False
    
    def store_carbon_intensity_snapshot(self, regional_data: Dict, timestamp: datetime) -> bool:
        """
        Store carbon intensity snapshot for all regions
        
        Args:
            regional_data: Dictionary of region -> intensity data
            timestamp: When the data was collected
            
        Returns:
            bool: Success status
        """
        try:
            timestamp_int = int(timestamp.timestamp())
            ttl = int((timestamp + timedelta(days=30)).timestamp())
            
            # Store each region's data
            with self.carbon_history.batch_writer() as batch:
                for region, data in regional_data.items():
                    item = {
                        'region': region,
                        'timestamp': timestamp_int,
                        'intensity': Decimal(str(data.get('intensity', 0))),
                        'source': data.get('source', 'unknown'),
                        'is_realtime': data.get('is_realtime', False),
                        'ttl': ttl
                    }
                    
                    # Add additional fields if available
                    if 'grid_intensity' in data:
                        item['grid_intensity'] = Decimal(str(data['grid_intensity']))
                    if 'renewable_pct' in data:
                        item['renewable_pct'] = Decimal(str(data['renewable_pct']))
                    if 'index' in data:
                        item['index'] = data['index']
                    
                    batch.put_item(Item=item)
            
            logger.info(f"Stored carbon intensity for {len(regional_data)} regions")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store carbon intensity snapshot: {e}")
            return False
    
    def update_daily_analytics(self, pipeline_name: str, execution_data: Dict) -> bool:
        """
        Update daily analytics for a pipeline
        
        Args:
            pipeline_name: Name of the pipeline
            execution_data: Execution data to aggregate
            
        Returns:
            bool: Success status
        """
        try:
            date_str = datetime.now().strftime('%Y-%m-%d')
            
            # Get existing analytics or create new
            try:
                response = self.analytics.get_item(
                    Key={'pipeline_name': pipeline_name, 'date': date_str}
                )
                analytics = response.get('Item', {})
            except:
                analytics = {}
            
            # Initialize if new
            if not analytics:
                analytics = {
                    'pipeline_name': pipeline_name,
                    'date': date_str,
                    'executions': {'total': 0, 'successful': 0, 'failed': 0},
                    'carbon': {'total_emissions_g': Decimal('0'), 'total_savings_g': Decimal('0')},
                    'performance': {'total_duration_minutes': 0, 'total_energy_kwh': Decimal('0')},
                    'decisions': {'run_now': 0, 'defer': 0, 'relocate': 0}
                }
            
            # Update counters
            analytics['executions']['total'] += 1
            
            if execution_data.get('status') == 'SUCCESS':
                analytics['executions']['successful'] += 1
            else:
                analytics['executions']['failed'] += 1
            
            # Update carbon metrics
            carbon_data = execution_data.get('carbon_analysis', {})
            workload_data = execution_data.get('workload', {})
            
            analytics['carbon']['total_emissions_g'] += Decimal(str(workload_data.get('sci_score', 0)))
            analytics['carbon']['total_savings_g'] += Decimal(str(carbon_data.get('savings_g', 0)))
            
            # Update performance metrics
            analytics['performance']['total_duration_minutes'] += workload_data.get('duration_minutes', 0)
            analytics['performance']['total_energy_kwh'] += Decimal(str(workload_data.get('energy_kwh', 0)))
            
            # Update decision counters
            decision = carbon_data.get('decision', 'run_now').lower()
            if decision in analytics['decisions']:
                analytics['decisions'][decision] += 1
            
            # Calculate rates
            total_exec = analytics['executions']['total']
            analytics['executions']['success_rate'] = analytics['executions']['successful'] / total_exec
            
            # Add metadata
            analytics['updated_at'] = datetime.now(timezone.utc).isoformat()
            analytics['ttl'] = int((datetime.now() + timedelta(days=365)).timestamp())
            
            # Store updated analytics
            self.analytics.put_item(Item=analytics)
            
            logger.info(f"Updated daily analytics for {pipeline_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update daily analytics: {e}")
            return False
    
    def store_regional_insights(self, regional_data: Dict, timestamp: datetime) -> bool:
        """
        Store hourly regional optimization insights
        
        Args:
            regional_data: Dictionary of region -> intensity data
            timestamp: When the data was collected
            
        Returns:
            bool: Success status
        """
        try:
            date_str = timestamp.strftime('%Y-%m-%d')
            hour = timestamp.hour
            
            # Create rankings
            rankings = []
            intensities = []
            
            for region, data in regional_data.items():
                intensity = data.get('intensity', 0)
                rankings.append({
                    'region': region,
                    'intensity': intensity,
                    'rank': 0  # Will be set after sorting
                })
                intensities.append(intensity)
            
            # Sort by intensity and assign ranks
            rankings.sort(key=lambda x: x['intensity'])
            for i, ranking in enumerate(rankings):
                ranking['rank'] = i + 1
            
            # Calculate optimization opportunities
            min_intensity = min(intensities) if intensities else 0
            max_intensity = max(intensities) if intensities else 0
            
            max_savings_percent = 0
            if max_intensity > 0:
                max_savings_percent = ((max_intensity - min_intensity) / max_intensity) * 100
            
            # Count regions below threshold (50 gCO2/kWh)
            regions_below_threshold = [r['region'] for r in rankings if r['intensity'] <= 50]
            
            insights_item = {
                'date': date_str,
                'hour': hour,
                'rankings': rankings,
                'opportunities': {
                    'max_savings_percent': Decimal(str(round(max_savings_percent, 1))),
                    'best_region': rankings[0]['region'] if rankings else '',
                    'worst_region': rankings[-1]['region'] if rankings else '',
                    'regions_below_threshold': regions_below_threshold
                },
                'data_quality': {
                    'regions_with_data': len(regional_data),
                    'data_freshness_minutes': 5  # Assuming 5-minute freshness
                },
                'created_at': timestamp.isoformat(),
                'ttl': int((timestamp + timedelta(days=60)).timestamp())
            }
            
            # Convert to DynamoDB format
            insights_item = self._convert_to_dynamodb_format(insights_item)
            
            # Store insights
            self.insights.put_item(Item=insights_item)
            
            logger.info(f"Stored regional insights for {date_str} hour {hour}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store regional insights: {e}")
            return False
    
    def get_pipeline_history(self, pipeline_name: str, limit: int = 50) -> List[Dict]:
        """
        Get recent execution history for a pipeline
        
        Args:
            pipeline_name: Name of the pipeline
            limit: Maximum number of records to return
            
        Returns:
            List of execution records
        """
        try:
            response = self.executions.query(
                IndexName='PipelineNameIndex',  # Assumes GSI exists
                KeyConditionExpression='pipeline_name = :pipeline_name',
                ExpressionAttributeValues={':pipeline_name': pipeline_name},
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            
            return response.get('Items', [])
            
        except Exception as e:
            logger.error(f"Failed to get pipeline history: {e}")
            return []
    
    def get_carbon_trends(self, region: str, hours: int = 24) -> List[Dict]:
        """
        Get carbon intensity trends for a region
        
        Args:
            region: AWS region name
            hours: Number of hours to look back
            
        Returns:
            List of carbon intensity records
        """
        try:
            start_time = int((datetime.now() - timedelta(hours=hours)).timestamp())
            
            response = self.carbon_history.query(
                KeyConditionExpression='region = :region AND #ts >= :start_time',
                ExpressionAttributeNames={'#ts': 'timestamp'},
                ExpressionAttributeValues={
                    ':region': region,
                    ':start_time': start_time
                },
                ScanIndexForward=True  # Chronological order
            )
            
            return response.get('Items', [])
            
        except Exception as e:
            logger.error(f"Failed to get carbon trends: {e}")
            return []
    
    def _convert_to_dynamodb_format(self, data: Dict) -> Dict:
        """Convert Python types to DynamoDB-compatible types"""
        if isinstance(data, dict):
            return {k: self._convert_to_dynamodb_format(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_to_dynamodb_format(item) for item in data]
        elif isinstance(data, float):
            return Decimal(str(data))
        else:
            return data


# Convenience functions for the test script
def store_pipeline_execution_data(execution_data: Dict) -> bool:
    """Store pipeline execution data - called from test_real_pipeline.py"""
    store = PipelineDataStore()
    
    # Store main execution record
    success = store.store_pipeline_execution(execution_data)
    
    if success:
        # Store carbon intensity snapshot
        regional_data = execution_data.get('regional_snapshot', {})
        if regional_data:
            timestamp = datetime.fromisoformat(execution_data['created_at'].replace('Z', '+00:00'))
            store.store_carbon_intensity_snapshot(regional_data, timestamp)
        
        # Update daily analytics
        pipeline_name = execution_data.get('pipeline_name', '')
        if pipeline_name:
            store.update_daily_analytics(pipeline_name, execution_data)
        
        # Store regional insights
        if regional_data:
            store.store_regional_insights(regional_data, timestamp)
    
    return success


def get_pipeline_analytics(pipeline_name: str, days: int = 30) -> Dict:
    """Get pipeline analytics for dashboard"""
    store = PipelineDataStore()
    
    # Get recent executions
    executions = store.get_pipeline_history(pipeline_name, limit=100)
    
    # Calculate analytics
    if not executions:
        return {'error': 'No execution data found'}
    
    total_executions = len(executions)
    successful = sum(1 for e in executions if e.get('status') == 'SUCCESS')
    
    total_carbon = sum(float(e.get('workload', {}).get('sci_score', 0)) for e in executions)
    total_savings = sum(float(e.get('carbon_analysis', {}).get('savings_g', 0)) for e in executions)
    
    return {
        'pipeline_name': pipeline_name,
        'total_executions': total_executions,
        'success_rate': successful / total_executions if total_executions > 0 else 0,
        'total_carbon_g': total_carbon,
        'total_savings_g': total_savings,
        'avg_carbon_per_execution': total_carbon / total_executions if total_executions > 0 else 0,
        'recent_executions': executions[:10]  # Last 10 executions
    }