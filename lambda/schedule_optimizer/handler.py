"""
Green QA Platform - Enhanced Schedule Optimizer Lambda

ENHANCED VERSION integrating knowledge base tools:
- carbonaware_scheduler_client patterns (Section 2)
- CATS scheduling logic (Section 3)
- Cloud Carbon Footprint carbon savings calculation
- GSF SCI-based optimization
- AWS Pipeline Triggering (CodePipeline, CodeBuild, Step Functions)

References:
- carbonaware_scheduler: Multi-cloud scheduling patterns
- CATS: UK-focused time-shifting logic
- CCF: Carbon calculation methodology
- SCI: ((E × I) + M) per R
"""

import boto3
import json
import os
import logging
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# Add parent paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import pipeline trigger module
try:
    from lambda.schedule_optimizer.pipeline_trigger import (
        execute_pipeline_action,
        TriggerResult,
        TriggerStatus,
    )
    PIPELINE_TRIGGER_AVAILABLE = True
except ImportError:
    PIPELINE_TRIGGER_AVAILABLE = False

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ============================================================================
# CONFIGURATION
# ============================================================================

TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'green_qa_carbon_intensity')

# Thresholds from CATS (Climate-Aware Task Scheduler)
# Source: Section 3 of knowledge base
CARBON_THRESHOLD_VERY_LOW = 50     # Very low intensity
CARBON_THRESHOLD_LOW = 150        # Low intensity 
CARBON_THRESHOLD_MODERATE = 250   # Moderate intensity
CARBON_THRESHOLD_HIGH = 400       # High intensity

# Minimum improvement threshold to recommend deferral
DEFER_BENEFIT_THRESHOLD = float(os.environ.get('DEFER_BENEFIT_THRESHOLD', '0.15'))

# Maximum defer window (hours)
MAX_DEFER_HOURS = int(os.environ.get('MAX_DEFER_HOURS', '24'))

# Cloud Carbon Footprint PUE values
PUE_VALUES = {
    'aws': 1.135,
    'gcp': 1.1,
    'azure': 1.185
}

# Energy coefficient per vCPU (Watts)
VCPU_TDP_WATTS = 10.0


# ============================================================================
# DATA CLASSES (inspired by carbonaware_scheduler_client)
# ============================================================================

class RecommendationType(Enum):
    """Recommendation types based on CATS/GSF patterns."""
    RUN_NOW = "run_now"
    DEFER = "defer"
    RELOCATE = "relocate"
    RUN_WITH_WARNING = "run_with_warning"


class CarbonIndex(Enum):
    """Carbon intensity index (from UK Carbon Intensity API)."""
    VERY_LOW = "very low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very high"


@dataclass
class CarbonWindow:
    """
    A time window with carbon intensity data.
    Pattern from carbonaware_scheduler_client.
    """
    start_time: str
    end_time: str
    carbon_intensity: float
    index: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'start': self.start_time,
            'end': self.end_time,
            'intensity': self.carbon_intensity,
            'index': self.index
        }


@dataclass
class SchedulingRecommendation:
    """
    Scheduling recommendation result.
    Pattern from carbonaware_scheduler_client's schedule response.
    """
    recommendation: RecommendationType
    reason: str
    region: str
    current_intensity: float
    current_index: Optional[str] = None
    optimal_window: Optional[CarbonWindow] = None
    alternative_region: Optional[str] = None
    estimated_savings_g: Optional[float] = None
    estimated_savings_percent: Optional[float] = None
    confidence: str = "medium"
    pipeline_trigger_result: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        result = {
            'recommendation': self.recommendation.value,
            'reason': self.reason,
            'region': self.region,
            'current_intensity': self.current_intensity,
            'confidence': self.confidence,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if self.current_index:
            result['current_index'] = self.current_index
        
        if self.optimal_window:
            result['optimal_window'] = self.optimal_window.to_dict()
            result['optimal_intensity'] = self.optimal_window.carbon_intensity
        
        if self.alternative_region:
            result['alternative_region'] = self.alternative_region
        
        if self.estimated_savings_g is not None:
            result['estimated_savings_gCO2'] = round(self.estimated_savings_g, 2)
        
        if self.estimated_savings_percent is not None:
            result['estimated_savings_percent'] = round(self.estimated_savings_percent, 1)
        
        if self.pipeline_trigger_result:
            result['pipeline_trigger'] = self.pipeline_trigger_result
        
        return result


# ============================================================================
# JSON ENCODER
# ============================================================================

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


# ============================================================================
# DATABASE ACCESS
# ============================================================================

def get_carbon_data(region: str) -> Optional[Dict]:
    """Get latest carbon data from DynamoDB."""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(TABLE_NAME)
    
    try:
        response = table.query(
            KeyConditionExpression='region_id = :r',
            ExpressionAttributeValues={':r': region},
            ScanIndexForward=False,
            Limit=1
        )
        
        if response['Items']:
            return response['Items'][0]
        return None
    
    except Exception as e:
        logger.error(f"DynamoDB error for {region}: {e}")
        return None


def get_all_regions_data() -> List[Dict]:
    """Get latest data for all regions."""
    regions = [
        'eu-west-2', 'eu-north-1', 'eu-west-1', 'eu-west-3', 'eu-central-1',
        'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
        'ap-south-1', 'ap-northeast-1', 'ap-southeast-1', 'ap-southeast-2'
    ]
    
    results = []
    for region in regions:
        data = get_carbon_data(region)
        if data:
            results.append(data)
    
    return results


# ============================================================================
# CARBON CALCULATIONS (CCF methodology)
# ============================================================================

def calculate_energy_kwh(
    duration_seconds: float,
    vcpu_count: int,
    memory_gb: float = 0
) -> float:
    """
    Calculate energy consumption in kWh.
    Uses Cloud Carbon Footprint methodology.
    """
    duration_hours = duration_seconds / 3600
    
    # Compute energy
    compute_kwh = (vcpu_count * VCPU_TDP_WATTS * duration_hours) / 1000
    
    # Memory energy (0.000392 kWh per GB-hour)
    memory_kwh = memory_gb * duration_hours * 0.000392 if memory_gb else 0
    
    return compute_kwh + memory_kwh


def calculate_carbon_g(
    energy_kwh: float,
    carbon_intensity: float,
    pue: float = 1.135
) -> float:
    """
    Calculate carbon emissions in grams CO2.
    
    Formula: Carbon = Energy × PUE × Intensity
    """
    return energy_kwh * pue * carbon_intensity


def calculate_savings(
    current_intensity: float,
    optimal_intensity: float,
    energy_kwh: float,
    pue: float = 1.135
) -> Tuple[float, float]:
    """
    Calculate carbon savings from deferral.
    
    Returns:
        Tuple of (savings in grams, savings as percentage)
    """
    current_carbon = calculate_carbon_g(energy_kwh, current_intensity, pue)
    optimal_carbon = calculate_carbon_g(energy_kwh, optimal_intensity, pue)
    
    savings_g = current_carbon - optimal_carbon
    savings_percent = (savings_g / current_carbon * 100) if current_carbon > 0 else 0
    
    return savings_g, savings_percent


# ============================================================================
# SCHEDULING LOGIC (CATS + carbonaware_scheduler patterns)
# ============================================================================

def get_carbon_index(intensity: float) -> str:
    """
    Determine carbon index from intensity.
    Pattern from UK Carbon Intensity API.
    """
    if intensity <= CARBON_THRESHOLD_VERY_LOW:
        return CarbonIndex.VERY_LOW.value
    elif intensity <= CARBON_THRESHOLD_LOW:
        return CarbonIndex.LOW.value
    elif intensity <= CARBON_THRESHOLD_MODERATE:
        return CarbonIndex.MODERATE.value
    elif intensity <= CARBON_THRESHOLD_HIGH:
        return CarbonIndex.HIGH.value
    else:
        return CarbonIndex.VERY_HIGH.value


def find_optimal_window(
    forecast: List[Dict],
    duration_minutes: int = 30,
    max_defer_hours: int = MAX_DEFER_HOURS
) -> Optional[CarbonWindow]:
    """
    Find the optimal execution window in forecast.
    Pattern from CATS and carbonaware_scheduler_client.
    
    Args:
        forecast: List of forecast points with 'from', 'to', 'intensity'
        duration_minutes: Expected workload duration
        max_defer_hours: Maximum hours to look ahead
    
    Returns:
        CarbonWindow with lowest intensity, or None
    """
    if not forecast:
        return None
    
    # Limit to max defer window
    max_slots = (max_defer_hours * 60) // 30  # 30-min slots
    forecast = forecast[:min(len(forecast), max_slots)]
    
    # Find window with minimum intensity
    best_window = None
    best_intensity = float('inf')
    
    slots_needed = max(1, duration_minutes // 30)
    
    for i in range(len(forecast) - slots_needed + 1):
        window_slots = forecast[i:i + slots_needed]
        
        # Calculate average intensity across window
        avg_intensity = sum(
            float(s.get('intensity', 9999)) for s in window_slots
        ) / len(window_slots)
        
        if avg_intensity < best_intensity:
            best_intensity = avg_intensity
            best_window = CarbonWindow(
                start_time=window_slots[0].get('from', ''),
                end_time=window_slots[-1].get('to', ''),
                carbon_intensity=avg_intensity,
                index=get_carbon_index(avg_intensity)
            )
    
    return best_window


def find_lowest_carbon_region(
    exclude_region: str = None,
    max_results: int = 3
) -> List[Dict]:
    """
    Find regions with lowest current carbon intensity.
    Used for location-shifting recommendations.
    """
    all_data = get_all_regions_data()
    
    # Filter and sort
    filtered = [
        d for d in all_data
        if d.get('region_id') != exclude_region
    ]
    
    sorted_data = sorted(
        filtered,
        key=lambda x: float(x.get('carbon_intensity', 9999))
    )
    
    return [
        {
            'region': d['region_id'],
            'intensity': float(d['carbon_intensity']),
            'source': d.get('source')
        }
        for d in sorted_data[:max_results]
    ]


def _trigger_pipeline_for_recommendation(
    recommendation: SchedulingRecommendation,
    region: str,
    workload_type: str = None
) -> SchedulingRecommendation:
    """
    Helper to trigger pipeline based on recommendation.
    Adds pipeline_trigger_result to the recommendation.
    """
    if not PIPELINE_TRIGGER_AVAILABLE:
        recommendation.pipeline_trigger_result = {
            "status": "skipped",
            "message": "Pipeline trigger module not available"
        }
        return recommendation
    
    try:
        trigger_result = execute_pipeline_action(
            recommendation=recommendation.recommendation.value,
            region=region,
            workload_type=workload_type,
            optimal_window_start=recommendation.optimal_window.start_time if recommendation.optimal_window else None,
            carbon_intensity=recommendation.current_intensity,
            estimated_savings=recommendation.estimated_savings_percent
        )
        recommendation.pipeline_trigger_result = trigger_result.to_dict()
    except Exception as e:
        logger.error(f"Pipeline trigger failed: {e}")
        recommendation.pipeline_trigger_result = {
            "status": "failed",
            "service": "Unknown",
            "message": "Pipeline trigger failed",
            "error": str(e)
        }
    
    return recommendation


def get_scheduling_recommendation(
    region: str,
    duration_minutes: int = 30,
    vcpu_count: int = 2,
    memory_gb: float = 4.0,
    allow_defer: bool = True,
    allow_relocate: bool = False,
    max_defer_hours: int = MAX_DEFER_HOURS,
    workload_type: str = None,
    trigger_pipeline: bool = False
) -> SchedulingRecommendation:
    """
    Get intelligent scheduling recommendation.
    
    Combines patterns from:
    - carbonaware_scheduler_client: Multi-zone optimization
    - CATS: UK-focused time-shifting
    - Cloud Carbon Footprint: Carbon calculation
    
    Args:
        region: AWS region
        duration_minutes: Expected workload duration
        vcpu_count: Number of vCPUs
        memory_gb: Memory in GB
        allow_defer: Allow time-shifting recommendations
        allow_relocate: Allow location-shifting recommendations
        max_defer_hours: Maximum hours to defer
        workload_type: Type of workload (for pipeline lookup)
        trigger_pipeline: If True, actually trigger the pipeline
    
    Decision logic:
    1. If intensity is very low/low → run now
    2. If deferring can save >15% → defer
    3. If relocating can save >30% → suggest relocation
    4. Otherwise → run with appropriate confidence
    """
    # Get current carbon data
    carbon_data = get_carbon_data(region)
    
    if not carbon_data:
        rec = SchedulingRecommendation(
            recommendation=RecommendationType.RUN_NOW,
            reason="No carbon data available, defaulting to immediate execution",
            region=region,
            current_intensity=300,  # Fallback
            confidence="low"
        )
        if trigger_pipeline:
            rec = _trigger_pipeline_for_recommendation(rec, region, workload_type)
        return rec
    
    current_intensity = float(carbon_data.get('carbon_intensity', 300))
    current_index = carbon_data.get('index') or get_carbon_index(current_intensity)
    forecast = carbon_data.get('forecast', [])
    
    # Calculate energy for savings estimation
    energy_kwh = calculate_energy_kwh(
        duration_seconds=duration_minutes * 60,
        vcpu_count=vcpu_count,
        memory_gb=memory_gb
    )
    
    # ============================================================
    # DECISION 1: Check if intensity is already low
    # ============================================================
    if current_index in [CarbonIndex.VERY_LOW.value, CarbonIndex.LOW.value]:
        rec = SchedulingRecommendation(
            recommendation=RecommendationType.RUN_NOW,
            reason=f"Carbon intensity is {current_index} ({current_intensity:.0f} gCO2/kWh) - optimal to run now",
            region=region,
            current_intensity=current_intensity,
            current_index=current_index,
            confidence="high"
        )
        if trigger_pipeline:
            rec = _trigger_pipeline_for_recommendation(rec, region, workload_type)
        return rec
    
    # ============================================================
    # DECISION 2: Check if time-shifting would help
    # ============================================================
    if allow_defer and forecast:
        optimal_window = find_optimal_window(
            forecast,
            duration_minutes,
            max_defer_hours
        )
        
        if optimal_window and optimal_window.carbon_intensity < current_intensity:
            improvement = (current_intensity - optimal_window.carbon_intensity) / current_intensity
            
            if improvement >= DEFER_BENEFIT_THRESHOLD:
                savings_g, savings_percent = calculate_savings(
                    current_intensity,
                    optimal_window.carbon_intensity,
                    energy_kwh
                )
                
                rec = SchedulingRecommendation(
                    recommendation=RecommendationType.DEFER,
                    reason=f"Deferring to {optimal_window.start_time} can reduce carbon by {improvement:.0%}",
                    region=region,
                    current_intensity=current_intensity,
                    current_index=current_index,
                    optimal_window=optimal_window,
                    estimated_savings_g=savings_g,
                    estimated_savings_percent=savings_percent,
                    confidence="high"
                )
                if trigger_pipeline:
                    rec = _trigger_pipeline_for_recommendation(rec, region, workload_type)
                return rec
    
    # ============================================================
    # DECISION 3: Check if location-shifting would help
    # ============================================================
    if allow_relocate:
        alternatives = find_lowest_carbon_region(exclude_region=region, max_results=3)
        
        if alternatives:
            best_alt = alternatives[0]
            alt_intensity = best_alt['intensity']
            
            # Recommend relocation if >30% improvement
            if alt_intensity < current_intensity * 0.7:
                savings_g, savings_percent = calculate_savings(
                    current_intensity,
                    alt_intensity,
                    energy_kwh
                )
                
                rec = SchedulingRecommendation(
                    recommendation=RecommendationType.RELOCATE,
                    reason=f"Running in {best_alt['region']} would reduce carbon by {savings_percent:.0f}%",
                    region=region,
                    current_intensity=current_intensity,
                    current_index=current_index,
                    alternative_region=best_alt['region'],
                    optimal_window=CarbonWindow(
                        start_time=datetime.utcnow().isoformat(),
                        end_time="",
                        carbon_intensity=alt_intensity
                    ),
                    estimated_savings_g=savings_g,
                    estimated_savings_percent=savings_percent,
                    confidence="medium"
                )
                if trigger_pipeline:
                    rec = _trigger_pipeline_for_recommendation(rec, region, workload_type)
                return rec
    
    # ============================================================
    # DECISION 4: No better option, run with appropriate warning
    # ============================================================
    if current_index in [CarbonIndex.HIGH.value, CarbonIndex.VERY_HIGH.value]:
        rec = SchedulingRecommendation(
            recommendation=RecommendationType.RUN_WITH_WARNING,
            reason=f"Carbon intensity is {current_index} ({current_intensity:.0f} gCO2/kWh), but no better alternatives found",
            region=region,
            current_intensity=current_intensity,
            current_index=current_index,
            confidence="medium"
        )
        if trigger_pipeline:
            rec = _trigger_pipeline_for_recommendation(rec, region, workload_type)
        return rec
    
    rec = SchedulingRecommendation(
        recommendation=RecommendationType.RUN_NOW,
        reason=f"Carbon intensity is moderate ({current_intensity:.0f} gCO2/kWh), no significant benefit from deferring",
        region=region,
        current_intensity=current_intensity,
        current_index=current_index,
        confidence="medium"
    )
    if trigger_pipeline:
        rec = _trigger_pipeline_for_recommendation(rec, region, workload_type)
    return rec


# ============================================================================
# BATCH SCHEDULING (carbonaware_scheduler_client pattern)
# ============================================================================

def get_batch_recommendations(
    regions: List[str],
    duration_minutes: int = 30,
    vcpu_count: int = 2
) -> Dict:
    """
    Get recommendations for multiple regions.
    Pattern from carbonaware_scheduler_client's batch API.
    
    Returns sorted recommendations with the best option first.
    """
    results = []
    
    for region in regions:
        rec = get_scheduling_recommendation(
            region=region,
            duration_minutes=duration_minutes,
            vcpu_count=vcpu_count,
            allow_defer=True,
            allow_relocate=False
        )
        results.append(rec.to_dict())
    
    # Sort by current intensity
    results.sort(key=lambda x: x.get('current_intensity', 9999))
    
    return {
        'recommendations': results,
        'best_region': results[0]['region'] if results else None,
        'best_intensity': results[0]['current_intensity'] if results else None,
        'timestamp': datetime.utcnow().isoformat()
    }


# ============================================================================
# LAMBDA HANDLER
# ============================================================================

def lambda_handler(event: Dict, context) -> Dict:
    """
    Main Lambda handler.
    
    Actions:
        - get_recommendation: Single region recommendation
        - batch: Multi-region recommendations
        - get_optimal_regions: Find lowest-carbon regions
        - calculate_savings: Calculate savings for deferral
    """
    action = event.get('action', 'get_recommendation')
    
    try:
        if action == 'get_recommendation':
            rec = get_scheduling_recommendation(
                region=event.get('region', 'eu-west-2'),
                duration_minutes=event.get('duration_minutes', 30),
                vcpu_count=event.get('vcpu_count', 2),
                memory_gb=event.get('memory_gb', 4.0),
                allow_defer=event.get('allow_defer', True),
                allow_relocate=event.get('allow_relocate', False),
                max_defer_hours=event.get('max_defer_hours', MAX_DEFER_HOURS),
                workload_type=event.get('workload_type'),
                trigger_pipeline=event.get('trigger_pipeline', False)
            )
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(rec.to_dict(), cls=DecimalEncoder)
            }
        
        elif action == 'batch':
            regions = event.get('regions', ['eu-west-2', 'us-east-1', 'eu-north-1'])
            result = get_batch_recommendations(
                regions=regions,
                duration_minutes=event.get('duration_minutes', 30),
                vcpu_count=event.get('vcpu_count', 2)
            )
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result, cls=DecimalEncoder)
            }
        
        elif action == 'get_optimal_regions':
            limit = event.get('limit', 5)
            regions = find_lowest_carbon_region(max_results=limit)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'optimal_regions': regions,
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        elif action == 'calculate_savings':
            current = event.get('current_intensity', 400)
            optimal = event.get('optimal_intensity', 200)
            duration = event.get('duration_minutes', 60)
            vcpu = event.get('vcpu_count', 2)
            
            energy = calculate_energy_kwh(duration * 60, vcpu)
            savings_g, savings_pct = calculate_savings(current, optimal, energy)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'current_intensity': current,
                    'optimal_intensity': optimal,
                    'energy_kwh': round(energy, 6),
                    'current_carbon_g': round(calculate_carbon_g(energy, current), 2),
                    'optimal_carbon_g': round(calculate_carbon_g(energy, optimal), 2),
                    'savings_g': round(savings_g, 2),
                    'savings_percent': round(savings_pct, 1)
                })
            }
        
        elif action == 'run_optimized':
            """
            Full workflow: Get recommendation → Trigger pipeline → Calculate SCI → Store history
            
            This action:
            1. Gets scheduling recommendation (finds optimal region)
            2. Triggers pipeline in optimal region (if enabled)
            3. Calculates SCI for both default (eu-west-2) and optimal region
            4. Computes carbon savings
            5. Stores result in test history
            
            Returns complete execution details for UI display.
            """
            # Input parameters
            test_suite = event.get('test_suite', 'Test Suite')
            duration_minutes = event.get('duration_minutes', 60)
            vcpu_count = event.get('vcpu_count', 2)
            memory_gb = event.get('memory_gb', 4.0)
            workload_type = event.get('workload_type')
            trigger_pipeline = event.get('trigger_pipeline', False)
            
            # Default region for comparison
            default_region = 'eu-west-2'
            
            # Step 1: Get recommendation (finds optimal region)
            rec = get_scheduling_recommendation(
                region=default_region,
                duration_minutes=duration_minutes,
                vcpu_count=vcpu_count,
                memory_gb=memory_gb,
                allow_defer=True,
                allow_relocate=True,
                workload_type=workload_type,
                trigger_pipeline=trigger_pipeline
            )
            
            # Determine optimal region from recommendation
            if rec.recommendation == RecommendationType.RELOCATE and rec.alternative_region:
                optimal_region = rec.alternative_region
                optimal_intensity = rec.optimal_window.carbon_intensity if rec.optimal_window else rec.current_intensity
            else:
                optimal_region = rec.region
                optimal_intensity = rec.current_intensity
            
            # Get default region intensity
            default_data = get_carbon_data(default_region)
            default_intensity = float(default_data.get('carbon_intensity', 250)) if default_data else 250
            
            # Step 2: Calculate SCI for both regions
            duration_hours = duration_minutes / 60
            pue = PUE_VALUES.get('aws', 1.135)
            
            # Energy calculation
            compute_kwh = (vcpu_count * VCPU_TDP_WATTS * duration_hours) / 1000
            memory_kwh = memory_gb * duration_hours * 0.000392
            total_energy_kwh = (compute_kwh + memory_kwh) * pue
            
            # Embodied carbon
            embodied_g = vcpu_count * duration_hours * 2.5
            
            # SCI for default region (eu-west-2)
            default_operational_g = total_energy_kwh * default_intensity
            default_sci = default_operational_g + embodied_g
            
            # SCI for optimal region
            optimal_operational_g = total_energy_kwh * optimal_intensity
            optimal_sci = optimal_operational_g + embodied_g
            
            # Step 3: Calculate savings
            savings_g = default_sci - optimal_sci
            savings_percent = (savings_g / default_sci * 100) if default_sci > 0 else 0
            
            # Step 4: Build result
            result = {
                'test_suite': test_suite,
                'timestamp': datetime.utcnow().isoformat(),
                
                # Workload parameters
                'duration_minutes': duration_minutes,
                'vcpu_count': vcpu_count,
                'memory_gb': memory_gb,
                'energy_kwh': round(total_energy_kwh, 6),
                
                # Recommendation
                'recommendation': rec.recommendation.value,
                'recommendation_reason': rec.reason,
                'confidence': rec.confidence,
                
                # Default region (eu-west-2) - baseline
                'default_region': default_region,
                'default_intensity': round(default_intensity, 1),
                'default_sci': round(default_sci, 4),
                
                # Optimal region (from decision)
                'optimal_region': optimal_region,
                'optimal_intensity': round(optimal_intensity, 1),
                'optimal_sci': round(optimal_sci, 4),
                
                # Savings
                'savings_g': round(savings_g, 4),
                'savings_percent': round(savings_percent, 2),
                
                # Pipeline trigger result
                'pipeline_status': 'not_triggered',
                'pipeline_execution_id': None
            }
            
            # Add pipeline trigger info if available
            if rec.pipeline_trigger_result:
                result['pipeline_status'] = rec.pipeline_trigger_result.get('status', 'unknown')
                result['pipeline_execution_id'] = rec.pipeline_trigger_result.get('execution_id')
                result['pipeline_service'] = rec.pipeline_trigger_result.get('service')
                result['pipeline_message'] = rec.pipeline_trigger_result.get('message')
            
            # Step 5: Store in history (if history handler is available)
            try:
                from lambda.api.test_history_handler import store_test_result
                stored = store_test_result({
                    'test_suite': test_suite,
                    'duration_minutes': duration_minutes,
                    'vcpu_count': vcpu_count,
                    'memory_gb': memory_gb,
                    'optimal_region': optimal_region,
                    'optimal_intensity': optimal_intensity,
                    'pipeline_status': result['pipeline_status'],
                    'pipeline_execution_id': result.get('pipeline_execution_id', ''),
                    'recommendation': rec.recommendation.value
                })
                result['history_stored'] = True
                result['test_id'] = stored.get('test_id')
            except Exception as e:
                logger.warning(f"Could not store test history: {e}")
                result['history_stored'] = False
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(result)
            }
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Unknown action: {action}'})
            }
    
    except Exception as e:
        logger.error(f"Handler error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


# For local testing
if __name__ == '__main__':
    print("=== Enhanced Schedule Optimizer ===\n")
    
    # Test carbon index
    print("1. Testing carbon index classification...")
    for intensity in [30, 100, 200, 350, 500]:
        idx = get_carbon_index(intensity)
        print(f"   {intensity} gCO2/kWh → {idx}")
    
    # Test energy calculation
    print("\n2. Testing energy calculation (CCF methodology)...")
    energy = calculate_energy_kwh(
        duration_seconds=3600,  # 1 hour
        vcpu_count=4,
        memory_gb=8.0
    )
    print(f"   4 vCPU, 8GB, 1 hour → {energy:.6f} kWh")
    
    # Test savings calculation
    print("\n3. Testing savings calculation...")
    savings_g, savings_pct = calculate_savings(
        current_intensity=400,
        optimal_intensity=200,
        energy_kwh=0.05
    )
    print(f"   400 → 200 gCO2/kWh: {savings_g:.2f}g saved ({savings_pct:.1f}%)")
    
    print("\n=== Tests complete ===")
