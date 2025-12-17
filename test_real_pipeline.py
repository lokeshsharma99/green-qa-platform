"""
Carbon-Aware Pipeline Trigger - Multi-Region Optimization

This script:
1. Takes pipeline name and region as arguments
2. Loads configuration from config/.env
3. Uses carbon_scheduler.py for optimal TIME_SHIFT vs SPACE_SHIFT decision
4. Triggers the CORRECT REGIONAL PIPELINE based on carbon optimization
5. Calculates SCI (Software Carbon Intensity) and savings
6. Stores result for UI dashboard

Usage:
  python test_real_pipeline.py                           # Uses .env defaults
  python test_real_pipeline.py --pipeline MyPipeline     # Specify pipeline
  python test_real_pipeline.py -p MyPipeline -r eu-west-2 -c normal

CARBON-AWARE PIPELINE SELECTION:
- eu-west-2 (London): gds-west-pipeline-pipeline
- eu-north-1 (Stockholm): gds-north-pipeline-pipeline

The script automatically selects the optimal strategy (TIME_SHIFT or SPACE_SHIFT)
based on which provides the highest carbon savings.

IMPORTANT: This will trigger a REAL pipeline execution!
Make sure CODEPIPELINE_ENABLED=true and AUTO_TRIGGER_RUN_NOW=true in .env
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

# ============================================================================
# REGIONAL PIPELINE CONFIGURATION
# Maps AWS regions to their respective pipeline names
# ============================================================================
REGIONAL_PIPELINES = {
    'eu-west-2': {
        'pipeline_name': 'gds-west-pipeline-pipeline',
        'pipeline_arn': 'arn:aws:codepipeline:eu-west-2:621836152823:gds-west-pipeline-pipeline',
        'region': 'eu-west-2',
        'location': 'London, UK',
        'description': 'Pipeline in London (UK grid)'
    },
    'eu-north-1': {
        'pipeline_name': 'gds-north-pipeline-pipeline',
        'pipeline_arn': 'arn:aws:codepipeline:eu-north-1:621836152823:gds-north-pipeline-pipeline',
        'region': 'eu-north-1',
        'location': 'Stockholm, Sweden',
        'description': 'Low-carbon pipeline in Stockholm (Nordic grid)'
    },
}

# Fallback pipeline if optimal region doesn't have a pipeline
DEFAULT_PIPELINE_REGION = 'eu-west-2'

# ============================================================================
# LOAD .ENV FILE
# ============================================================================

def load_env_file(env_path: str = None, verbose: bool = True):
    """Load environment variables from .env file."""
    if env_path is None:
        env_path = Path(__file__).parent / 'config' / '.env'
    
    if not os.path.exists(env_path):
        print(f"❌ .env file not found at: {env_path}")
        return False
    
    if verbose:
        print(f"📁 Loading configuration from: {env_path}")
    
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                # Strip inline comments
                value = value.split('#')[0].strip()
                # Remove quotes
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                os.environ[key] = value
    
    return True

# ============================================================================
# MAIN
# ============================================================================

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Carbon-Aware Pipeline Trigger with TIME_SHIFT/SPACE_SHIFT optimization',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_real_pipeline.py                              # Use .env defaults
  python test_real_pipeline.py -p MyPipeline                # Specify pipeline
  python test_real_pipeline.py -p MyPipeline -r eu-west-2   # Specify region
  python test_real_pipeline.py -p MyPipeline -c low         # Low criticality (max optimization)
  python test_real_pipeline.py --simulate                   # Simulation only (no trigger)
        """
    )
    parser.add_argument('--pipeline', '-p', help='Pipeline name (default: from .env)')
    parser.add_argument('--region', '-r', default='eu-west-2', help='Current AWS region (default: eu-west-2)')
    parser.add_argument('--criticality', '-c', default='normal',
                        choices=['critical', 'high', 'normal', 'low'],
                        help='Pipeline criticality (default: normal)')
    parser.add_argument('--simulate', '-s', action='store_true', help='Simulation only, do not trigger pipeline')
    parser.add_argument('--json', '-j', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    # Load .env
    load_env_file(verbose=not args.json)
    
    # Get pipeline name from args or .env
    pipeline_name = args.pipeline or os.environ.get('CODEPIPELINE_NAME', '')
    if not pipeline_name:
        print("❌ Pipeline name required. Use --pipeline or set CODEPIPELINE_NAME in .env")
        sys.exit(1)
    
    current_region = args.region
    criticality = args.criticality
    simulate = args.simulate or os.environ.get('AUTO_TRIGGER_RUN_NOW', 'false').lower() != 'true'
    
    if not args.json:
        print("=" * 70)
        print("CARBON-AWARE PIPELINE TRIGGER")
        print("=" * 70)
        print(f"\n📋 Configuration:")
        print(f"   Pipeline: {pipeline_name}")
        print(f"   Region: {current_region}")
        print(f"   Criticality: {criticality}")
        print(f"   Mode: {'SIMULATION' if simulate else 'LIVE TRIGGER'}")
    
    # =========================================================================
    # Use carbon_scheduler.py for optimal decision
    # =========================================================================
    if not args.json:
        print(f"\n🌍 Running Carbon Scheduler...")
    
    try:
        from carbon_scheduler import CarbonScheduler, Criticality, Strategy, load_config_from_env
        
        config = load_config_from_env()
        scheduler = CarbonScheduler(config)
        
        # Get optimal strategy
        crit_enum = Criticality(criticality)
        decision = scheduler.get_optimal_strategy(
            pipeline_name=pipeline_name,
            current_region=current_region,
            criticality=crit_enum
        )
        
    except ImportError as e:
        print(f"❌ Could not import carbon_scheduler: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Carbon scheduler error: {e}")
        sys.exit(1)
    
    # =========================================================================
    # Determine final pipeline based on strategy
    # =========================================================================
    target_region = decision.target_region
    target_intensity = decision.target_intensity
    strategy = decision.recommended_strategy
    
    # Select pipeline based on target region
    if target_region in REGIONAL_PIPELINES:
        selected_pipeline = REGIONAL_PIPELINES[target_region]
        final_pipeline_name = selected_pipeline['pipeline_name']
        final_pipeline_region = selected_pipeline['region']
    else:
        # Fallback to default if target region doesn't have a pipeline
        selected_pipeline = REGIONAL_PIPELINES[DEFAULT_PIPELINE_REGION]
        final_pipeline_name = selected_pipeline['pipeline_name']
        final_pipeline_region = selected_pipeline['region']
        if not args.json:
            print(f"   ⚠️ No pipeline in {target_region}, using {final_pipeline_region}")
    
    # =========================================================================
    # Calculate SCI
    # =========================================================================
    duration_minutes = int(os.environ.get('PIPELINE_DURATION_MINUTES', 40))
    vcpu_count = int(os.environ.get('PIPELINE_VCPU_COUNT', 2))
    memory_gb = float(os.environ.get('PIPELINE_MEMORY_GB', 2))
    
    PUE = 1.15
    VCPU_TDP_WATTS = 10
    MEMORY_COEFF = 0.000392
    EMBODIED_G_PER_VCPU_HOUR = 2.5
    
    duration_hours = duration_minutes / 60
    compute_kwh = (vcpu_count * VCPU_TDP_WATTS * duration_hours) / 1000
    memory_kwh = memory_gb * duration_hours * MEMORY_COEFF
    total_energy_kwh = (compute_kwh + memory_kwh) * PUE
    embodied_g = vcpu_count * duration_hours * EMBODIED_G_PER_VCPU_HOUR
    
    current_sci = total_energy_kwh * decision.current_intensity + embodied_g
    target_sci = total_energy_kwh * target_intensity + embodied_g
    savings_g = current_sci - target_sci
    savings_percent = (savings_g / current_sci * 100) if current_sci > 0 else 0
    
    # =========================================================================
    # Trigger or Schedule pipeline (if not simulation)
    # =========================================================================
    pipeline_status = 'skipped'
    execution_id = None
    schedule_name = None
    
    if not simulate:
        import boto3
        
        aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
        aws_session_token = os.environ.get('AWS_SESSION_TOKEN')
        
        def get_boto_client(service, region):
            if aws_session_token:
                return boto3.client(
                    service,
                    region_name=region,
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key,
                    aws_session_token=aws_session_token
                )
            return boto3.client(service, region_name=region)
        
        # Check if TIME_SHIFT - schedule for later using EventBridge Scheduler
        if strategy.value == 'time_shift' and decision.wait_hours > 0:
            if not args.json:
                print(f"\n⏰ Scheduling Pipeline (TIME_SHIFT)...")
                print(f"   Pipeline: {final_pipeline_name}")
                print(f"   Region: {final_pipeline_region}")
                print(f"   Scheduled: {decision.scheduled_time.strftime('%Y-%m-%d %H:%M UTC')}")
                print(f"   Wait: {decision.wait_hours:.1f} hours")
            
            try:
                scheduler = get_boto_client('scheduler', final_pipeline_region)
                
                # Create one-time schedule
                schedule_name = f"carbon-aware-{final_pipeline_name}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                schedule_time = decision.scheduled_time.strftime('%Y-%m-%dT%H:%M:%S')
                
                # Get pipeline ARN
                pipeline_arn = selected_pipeline.get('pipeline_arn', 
                    f"arn:aws:codepipeline:{final_pipeline_region}:621836152823:{final_pipeline_name}")
                
                # EventBridge Scheduler role ARN (must exist in your account)
                scheduler_role_arn = os.environ.get('EVENTBRIDGE_ROLE_ARN',
                    'arn:aws:iam::621836152823:role/EventBridgeSchedulerRole')
                
                response = scheduler.create_schedule(
                    Name=schedule_name,
                    ScheduleExpression=f"at({schedule_time})",
                    ScheduleExpressionTimezone='UTC',
                    FlexibleTimeWindow={'Mode': 'OFF'},
                    Target={
                        'Arn': pipeline_arn,
                        'RoleArn': scheduler_role_arn,
                        'Input': '{}'
                    },
                    ActionAfterCompletion='DELETE'  # Auto-delete after execution
                )
                
                execution_id = schedule_name
                pipeline_status = 'scheduled'
                
                if not args.json:
                    print(f"   ✅ Pipeline scheduled: {schedule_name}")
                    print(f"   📅 Will trigger at: {decision.scheduled_time.strftime('%Y-%m-%d %H:%M UTC')}")
                    
            except Exception as e:
                if not args.json:
                    print(f"   ⚠️ EventBridge scheduling failed: {e}")
                    print(f"   🔄 Falling back to immediate trigger...")
                # Fall through to immediate trigger
                strategy = Strategy.RUN_NOW
        
        # Immediate trigger (RUN_NOW, SPACE_SHIFT, HYBRID, or fallback)
        if pipeline_status != 'scheduled':
            if not args.json:
                print(f"\n🚀 Triggering Pipeline...")
                print(f"   Pipeline: {final_pipeline_name}")
                print(f"   Region: {final_pipeline_region}")
                print(f"   Strategy: {strategy.value.upper()}")
            
            try:
                client = get_boto_client('codepipeline', final_pipeline_region)
                
                response = client.start_pipeline_execution(name=final_pipeline_name)
                execution_id = response.get('pipelineExecutionId')
                pipeline_status = 'triggered'
                
                if not args.json:
                    print(f"   ✅ Pipeline triggered: {execution_id}")
                    
            except Exception as e:
                pipeline_status = 'failed'
                if not args.json:
                    print(f"   ❌ Trigger failed: {e}")
    
    # =========================================================================
    # Build result
    # =========================================================================
    result = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'pipeline_name': final_pipeline_name,
        'pipeline_region': final_pipeline_region,
        'execution_id': execution_id,
        'schedule_name': schedule_name,  # For TIME_SHIFT scheduled executions
        'status': pipeline_status,
        'strategy': strategy.value,
        'criticality': criticality,
        'carbon_analysis': {
            'current_region': current_region,
            'current_intensity': round(decision.current_intensity, 1),
            'target_region': target_region,
            'target_intensity': round(target_intensity, 1),
            'savings_percent': round(savings_percent, 1),
            'savings_g': round(savings_g, 4),
            'decision_reason': decision.decision_reason
        },
        'sci': {
            'current': round(current_sci, 4),
            'target': round(target_sci, 4),
            'energy_kwh': round(total_energy_kwh, 6)
        },
        'workload': {
            'duration_minutes': duration_minutes,
            'vcpu_count': vcpu_count,
            'memory_gb': memory_gb
        },
        'wait_hours': round(decision.wait_hours, 2),
        'scheduled_time': decision.scheduled_time.isoformat() if decision.scheduled_time else None,
        'data_sources': decision.data_sources,
        'available_pipelines': {r: p['pipeline_name'] for r, p in REGIONAL_PIPELINES.items()}
    }
    
    # =========================================================================
    # Output
    # =========================================================================
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("\n" + "=" * 70)
        print("CARBON-AWARE PIPELINE EXECUTION SUMMARY")
        print("=" * 70)
        
        # Show scheduled time for TIME_SHIFT
        scheduled_info = ""
        if pipeline_status == 'scheduled' and decision.scheduled_time:
            scheduled_info = f"\n   📅 Scheduled: {decision.scheduled_time.strftime('%Y-%m-%d %H:%M UTC')}"
        
        print(f"""
   🎯 STRATEGY: {strategy.value.upper()}
   ─────────────────────────────────────────
   Pipeline:    {final_pipeline_name}
   Region:      {final_pipeline_region} ({selected_pipeline['location']})
   Status:      {pipeline_status.upper()}
   Execution:   {execution_id or 'N/A'}{scheduled_info}
   
   🌍 CARBON OPTIMIZATION:
   ─────────────────────────────────────────
   Current ({current_region}): {decision.current_intensity:.1f} gCO2/kWh → SCI: {current_sci:.2f} gCO2
   Target ({target_region}):  {target_intensity:.1f} gCO2/kWh → SCI: {target_sci:.2f} gCO2
   
   💚 SAVINGS: {savings_g:.2f} gCO2 ({savings_percent:.1f}%)
   
   ⏱️ SCHEDULING:
   ─────────────────────────────────────────
   Wait: {decision.wait_hours:.1f} hours
   Reason: {decision.decision_reason}
   
   📊 AVAILABLE PIPELINES:""")
        for region, config in REGIONAL_PIPELINES.items():
            marker = " ← SELECTED" if region == final_pipeline_region else ""
            print(f"      {region}: {config['pipeline_name']}{marker}")
        print("\n" + "=" * 70)
    
    # =========================================================================
    # Save to history
    # =========================================================================
    history_path = Path(__file__).parent / 'dashboard' / 'public' / 'test-history-data.js'
    
    history_entry = {
        'test_id': execution_id or f"sim-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        'timestamp': result['timestamp'],
        'test_suite': f"Pipeline: {final_pipeline_name}",
        'duration_minutes': duration_minutes,
        'vcpu_count': vcpu_count,
        'memory_gb': memory_gb,
        'energy_kwh': round(total_energy_kwh, 6),
        'recommendation': strategy.value,
        'default_region': current_region,
        'default_intensity': round(decision.current_intensity, 1),
        'default_sci': round(current_sci, 4),
        'optimal_region': target_region,
        'optimal_intensity': round(target_intensity, 1),
        'optimal_sci': round(target_sci, 4),
        'savings_g': round(savings_g, 4),
        'savings_percent': round(savings_percent, 2),
        'pipeline_status': pipeline_status,
        'pipeline_execution_id': execution_id or '',
        'pipeline_name': final_pipeline_name
    }
    
    existing_history = []
    if history_path.exists():
        try:
            content = history_path.read_text()
            start = content.find('[')
            end = content.rfind(']') + 1
            if start >= 0 and end > start:
                existing_history = json.loads(content[start:end])
        except:
            pass
    
    history = [history_entry] + existing_history[:19]
    
    js_content = f"""// Auto-generated test history data
// Last updated: {datetime.now().isoformat()}
// Carbon-aware pipeline execution results

const TEST_HISTORY_DATA = {json.dumps(history, indent=2)};

if (typeof window !== 'undefined') {{
    window.TEST_HISTORY_DATA = TEST_HISTORY_DATA;
}}
"""
    
    history_path.write_text(js_content)
    if not args.json:
        print(f"\n   ✅ Saved to: {history_path}")


if __name__ == '__main__':
    main()
