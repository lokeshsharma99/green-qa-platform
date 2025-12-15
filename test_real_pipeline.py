"""
Test with REAL AWS Pipeline Configuration

This script:
1. Loads configuration from config/.env
2. Gets real carbon intensity from UK API
3. Makes scheduling decision
4. Triggers ACTUAL AWS CodePipeline (if enabled)
5. Calculates SCI and savings
6. Stores result for UI

IMPORTANT: This will trigger a REAL pipeline execution!
Make sure CODEPIPELINE_ENABLED=true and AUTO_TRIGGER_RUN_NOW=true in .env
"""

import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

# ============================================================================
# LOAD .ENV FILE
# ============================================================================

def load_env_file(env_path: str = None):
    """Load environment variables from .env file."""
    if env_path is None:
        env_path = Path(__file__).parent / 'config' / '.env'
    
    if not os.path.exists(env_path):
        print(f"❌ .env file not found at: {env_path}")
        return False
    
    print(f"📁 Loading configuration from: {env_path}")
    
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                os.environ[key] = value
                print(f"   ✓ {key}={value[:50]}{'...' if len(value) > 50 else ''}")
    
    return True

# ============================================================================
# MAIN TEST
# ============================================================================

def main():
    print("=" * 70)
    print("REAL PIPELINE TRIGGER TEST")
    print("=" * 70)
    
    # Step 1: Load .env
    print("\n📋 Step 1: Loading .env configuration...")
    if not load_env_file():
        return
    
    # Step 2: Check configuration
    print("\n🔍 Step 2: Checking pipeline configuration...")
    
    pipeline_enabled = os.environ.get('CODEPIPELINE_ENABLED', 'false').lower() == 'true'
    pipeline_name = os.environ.get('CODEPIPELINE_NAME', '')
    auto_trigger = os.environ.get('AUTO_TRIGGER_RUN_NOW', 'false').lower() == 'true'
    
    print(f"   CODEPIPELINE_ENABLED: {pipeline_enabled}")
    print(f"   CODEPIPELINE_NAME: {pipeline_name}")
    print(f"   AUTO_TRIGGER_RUN_NOW: {auto_trigger}")
    
    if not pipeline_enabled:
        print("\n⚠️  CODEPIPELINE_ENABLED is false!")
        print("   To trigger real pipeline, set CODEPIPELINE_ENABLED=true in .env")
        
        response = input("\n   Do you want to continue with SIMULATION only? (y/n): ")
        if response.lower() != 'y':
            print("   Exiting.")
            return
        print("   Continuing with simulation...")
    
    if not pipeline_name:
        print("\n❌ CODEPIPELINE_NAME is not set!")
        print("   Please set the pipeline name in .env")
        return
    
    # Step 3: Get carbon intensity (SAME LOGIC AS UI)
    # - eu-west-2: UK Grid ESO + datacenter formula
    # - Other regions: ElectricityMaps API
    print("\n🌍 Step 3: Getting carbon intensity (same logic as UI)...")
    
    from urllib.request import urlopen, Request
    
    # Constants (same as UI)
    AWS_RENEWABLE_PCT = {
        'eu-west-2': 0.80,
        'eu-north-1': 0.98,
        'eu-west-3': 0.75,
        'eu-west-1': 0.85,
        'eu-central-1': 0.75,
        'eu-central-2': 0.85,
    }
    AWS_PUE = 1.135
    
    ELECTRICITYMAPS_TOKEN = '7Cq9hfFAKl0gAtYNhvc2'
    ELECTRICITYMAPS_URL = 'https://api.electricitymaps.com/v3/carbon-intensity/latest'
    
    REGIONS = ['eu-west-2', 'eu-north-1', 'eu-west-3', 'eu-west-1', 'eu-central-1', 'eu-central-2']
    default_region = 'eu-west-2'
    all_intensities = {}
    
    # For eu-west-2: Use UK Grid ESO + datacenter formula (SAME AS UI)
    print(f"\n   eu-west-2 (UK): Using UK Grid ESO + datacenter formula...")
    try:
        req = Request('https://api.carbonintensity.org.uk/intensity', headers={'Accept': 'application/json'})
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            grid_intensity = data['data'][0]['intensity']['actual'] or data['data'][0]['intensity']['forecast']
            index = data['data'][0]['intensity']['index']
            
            # Datacenter formula (SAME AS UI): grid × (1 - renewable%) × PUE
            renewable_pct = AWS_RENEWABLE_PCT['eu-west-2']
            datacenter_intensity = round(grid_intensity * (1 - renewable_pct) * AWS_PUE * 10) / 10
            
            all_intensities['eu-west-2'] = datacenter_intensity
            print(f"   ✓ eu-west-2: Grid={grid_intensity} × (1-{renewable_pct}) × {AWS_PUE} = {datacenter_intensity} gCO2/kWh ({index})")
    except Exception as e:
        print(f"   ⚠ UK Grid ESO failed: {e}")
        all_intensities['eu-west-2'] = 13  # fallback
    
    # For other regions: Use ElectricityMaps API
    print(f"\n   Other regions: Using ElectricityMaps API...")
    for region in REGIONS:
        if region == 'eu-west-2':
            continue  # Already fetched above
        try:
            url = f"{ELECTRICITYMAPS_URL}?dataCenterRegion={region}&dataCenterProvider=aws"
            req = Request(url, headers={'auth-token': ELECTRICITYMAPS_TOKEN})
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                intensity = round(data.get('carbonIntensity', 0))
                all_intensities[region] = intensity
                print(f"   ✓ {region}: {intensity} gCO2/kWh")
        except Exception as e:
            print(f"   ⚠ {region}: Failed - {e}")
    
    # Sort by intensity to find optimal
    sorted_regions = sorted(all_intensities.items(), key=lambda x: x[1])
    optimal_region = sorted_regions[0][0]
    optimal_intensity = sorted_regions[0][1]
    default_intensity = all_intensities.get(default_region, 13)
    
    print(f"\n   All regions (datacenter intensity):")
    for region, intensity in sorted_regions:
        marker = "← OPTIMAL" if region == optimal_region else ("← DEFAULT" if region == default_region else "")
        print(f"   {region}: {intensity} gCO2/kWh {marker}")
    
    print(f"\n   Default region ({default_region}): {default_intensity} gCO2/kWh")
    print(f"   Optimal region ({optimal_region}): {optimal_intensity} gCO2/kWh")
    
    # Step 4: Make scheduling decision
    print("\n🎯 Step 4: Making scheduling decision...")
    
    if optimal_intensity < default_intensity * 0.85:
        recommendation = 'relocate'
        target_region = optimal_region
        target_intensity = optimal_intensity
        reason = f"Running in {target_region} would save {((default_intensity - optimal_intensity) / default_intensity * 100):.0f}% carbon"
    else:
        recommendation = 'run_now'
        target_region = default_region
        target_intensity = default_intensity
        reason = "Current region has acceptable carbon intensity"
    
    print(f"   Recommendation: {recommendation.upper()}")
    print(f"   Reason: {reason}")
    print(f"   Optimal region: {target_region}")
    
    # Use optimal region for pipeline execution to minimize carbon footprint
    # The pipeline will be triggered in the region with lowest carbon intensity
    pipeline_region = target_region
    print(f"   Pipeline region: {pipeline_region} (where pipeline exists)")
    
    # Step 5: Calculate SCI
    print("\n📊 Step 5: Calculating SCI...")
    
    # Test workload parameters - these represent the EXPECTED pipeline runtime
    # Not the script execution time, but how long your CI/CD pipeline typically runs
    
    import sys
    
    if len(sys.argv) >= 4:
        duration_minutes = int(sys.argv[1])
        vcpu_count = int(sys.argv[2])
        memory_gb = float(sys.argv[3])
        print(f"   Using provided parameters: {duration_minutes}min, {vcpu_count} vCPUs, {memory_gb}GB")
    else:
        # Realistic defaults based on typical CodeBuild medium instances
        duration_minutes = 15  # More realistic for CI/CD
        vcpu_count = 4         # CodeBuild BUILD_GENERAL1_MEDIUM
        memory_gb = 7          # CodeBuild BUILD_GENERAL1_MEDIUM
        print(f"   Using CodeBuild medium instance estimates: {duration_minutes}min, {vcpu_count} vCPUs, {memory_gb}GB")
        print(f"   (Override with: python test_real_pipeline.py <minutes> <vcpus> <memory_gb>)")
    
    print(f"   💡 These are pre-execution estimates. Real AWS metrics will be collected automatically after completion.")
    
    # CCF constants
    PUE = 1.135
    VCPU_TDP_WATTS = 10
    MEMORY_COEFF = 0.000392
    EMBODIED_G_PER_VCPU_HOUR = 2.5
    
    duration_hours = duration_minutes / 60
    compute_kwh = (vcpu_count * VCPU_TDP_WATTS * duration_hours) / 1000
    memory_kwh = memory_gb * duration_hours * MEMORY_COEFF
    total_energy_kwh = (compute_kwh + memory_kwh) * PUE
    embodied_g = vcpu_count * duration_hours * EMBODIED_G_PER_VCPU_HOUR
    
    # Default region SCI
    default_operational_g = total_energy_kwh * default_intensity
    default_sci = default_operational_g + embodied_g
    
    # Optimal region SCI
    optimal_operational_g = total_energy_kwh * target_intensity
    optimal_sci = optimal_operational_g + embodied_g
    
    # Savings
    savings_g = default_sci - optimal_sci
    savings_percent = (savings_g / default_sci * 100) if default_sci > 0 else 0
    
    print(f"   Estimated workload: {duration_minutes}min, {vcpu_count} vCPUs, {memory_gb}GB RAM")
    print(f"   Estimated energy: {total_energy_kwh:.6f} kWh")
    print(f"   Estimated SCI ({default_region}): {default_sci:.4f} gCO2")
    print(f"   Estimated SCI ({target_region}): {optimal_sci:.4f} gCO2")
    print(f"   Estimated savings: {savings_g:.4f} gCO2 ({savings_percent:.2f}%)")
    print(f"   📊 Note: These are estimates. Real AWS metrics will be collected automatically.")
    
    # Step 6: Trigger pipeline
    print("\n🚀 Step 6: Triggering pipeline...")
    
    pipeline_status = 'not_triggered'
    execution_id = None
    
    if pipeline_enabled and auto_trigger:
        print(f"   Triggering CodePipeline: {pipeline_name}")
        print(f"   Pipeline region: {pipeline_region}")
        
        try:
            import boto3
            
            # Get credentials from environment
            aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
            aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
            aws_session_token = os.environ.get('AWS_SESSION_TOKEN')
            
            # Check if session token is needed (ASIA prefix = temporary credentials)
            if aws_access_key and aws_access_key.startswith('ASIA') and not aws_session_token:
                print(f"   ⚠ WARNING: Temporary credentials detected (ASIA prefix)")
                print(f"   ⚠ AWS_SESSION_TOKEN is required but not set!")
                print(f"   ⚠ Add AWS_SESSION_TOKEN to your .env file")
                raise Exception("AWS_SESSION_TOKEN required for temporary credentials")
            
            # Create client for PIPELINE region (where pipeline exists)
            # Note: We trigger in pipeline_region but calculate carbon savings for optimal_region
            if aws_session_token:
                codepipeline_client = boto3.client(
                    'codepipeline',
                    region_name=pipeline_region,
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key,
                    aws_session_token=aws_session_token
                )
                lambda_client = boto3.client(
                    'lambda',
                    region_name=pipeline_region,
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key,
                    aws_session_token=aws_session_token
                )
            else:
                codepipeline_client = boto3.client('codepipeline', region_name=pipeline_region)
                lambda_client = boto3.client('lambda', region_name=pipeline_region)
            
            response = codepipeline_client.start_pipeline_execution(name=pipeline_name)
            execution_id = response.get('pipelineExecutionId')
            pipeline_status = 'success'
            
            print(f"   ✅ Pipeline triggered successfully!")
            print(f"   Execution ID: {execution_id}")
            
            # Schedule monitoring Lambda to collect final data
            monitor_function_name = os.environ.get('PIPELINE_MONITOR_FUNCTION', 'green-qa-pipeline-monitor-prod')
            
            try:
                # Schedule immediate monitoring (will wait for completion)
                monitor_payload = {
                    'pipeline_name': pipeline_name,
                    'execution_id': execution_id,
                    'region': pipeline_region,
                    'trigger_source': 'zerocarb_script',
                    'wait_for_completion': True
                }
                
                lambda_client.invoke(
                    FunctionName=monitor_function_name,
                    InvocationType='Event',  # Asynchronous
                    Payload=json.dumps(monitor_payload)
                )
                
                print(f"   📊 Monitoring Lambda scheduled for execution: {execution_id}")
                print(f"   📈 Real AWS data will be collected automatically upon completion")
                
            except Exception as monitor_error:
                print(f"   ⚠ Warning: Could not schedule monitoring Lambda: {monitor_error}")
                print(f"   💡 You can manually collect data later using:")
                print(f"      python collect_pipeline_data.py {pipeline_name} {execution_id}")
            
        except Exception as e:
            pipeline_status = 'failed'
            print(f"   ❌ Pipeline trigger failed: {e}")
    else:
        print(f"   ⏭ Pipeline trigger SKIPPED (simulation mode)")
        print(f"   To enable: Set CODEPIPELINE_ENABLED=true and AUTO_TRIGGER_RUN_NOW=true")
        pipeline_status = 'skipped'
    
    # Step 7: Save result
    print("\n💾 Step 7: Saving result for UI and DynamoDB...")
    
    # Create comprehensive execution record for DynamoDB
    execution_record = {
        'execution_id': execution_id or f"sim-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        'timestamp': int(datetime.now(timezone.utc).timestamp()),
        'pipeline_name': pipeline_name,
        'pipeline_region': pipeline_region,
        'trigger_source': 'zerocarb_manual',
        'status': pipeline_status.upper() if pipeline_status != 'skipped' else 'SIMULATED',
        
        # Carbon Intelligence
        'carbon_analysis': {
            'decision': recommendation.upper(),
            'reason': reason,
            'default_region': default_region,
            'default_intensity': default_intensity,
            'optimal_region': target_region,
            'optimal_intensity': target_intensity,
            'savings_g': round(savings_g, 4),
            'savings_percent': round(savings_percent, 2)
        },
        
        # Workload Details
        'workload': {
            'duration_minutes': duration_minutes,
            'vcpu_count': vcpu_count,
            'memory_gb': memory_gb,
            'energy_kwh': round(total_energy_kwh, 6),
            'sci_score': round(optimal_sci, 4)
        },
        
        # Regional Context (all regions at time of execution)
        'regional_snapshot': {region: {'intensity': intensity, 'source': 'electricity_maps' if region != 'eu-west-2' else 'uk_grid_eso'} 
                            for region, intensity in all_intensities.items()},
        
        # Configuration
        'config': {
            'auto_trigger': auto_trigger,
            'min_savings_defer': int(os.environ.get('MIN_SAVINGS_DEFER', 15)),
            'max_defer_hours': int(os.environ.get('MAX_DEFER_HOURS', 24)),
            'pipeline_timeout': int(os.environ.get('CODEPIPELINE_TIMEOUT', 30))
        },
        
        # Metadata
        'created_at': datetime.now(timezone.utc).isoformat(),
    }
    
    # Try to store in DynamoDB (if available)
    try:
        # Import storage module (create if doesn't exist)
        sys.path.insert(0, str(Path(__file__).parent / 'lambda' / 'api'))
        from pipeline_storage import store_pipeline_execution_data
        
        success = store_pipeline_execution_data(execution_record)
        if success:
            print(f"   ✅ Stored execution data in DynamoDB")
        else:
            print(f"   ⚠ Failed to store in DynamoDB (continuing with file storage)")
    except ImportError:
        print(f"   ⚠ DynamoDB storage not available (lambda/api/pipeline_storage.py not found)")
        print(f"   💡 Deploy infrastructure first: deploy_monitoring.bat")
    except Exception as e:
        print(f"   ⚠ DynamoDB storage failed: {e}")
        if "ResourceNotFoundException" in str(e):
            print(f"   💡 DynamoDB tables not found. Deploy infrastructure first: deploy_monitoring.bat")
    
    # Create simplified result for dashboard file (backward compatibility)
    result = {
        'test_id': execution_record['execution_id'],
        'timestamp': execution_record['created_at'],
        'test_suite': f"Pipeline: {pipeline_name}",
        'duration_minutes': duration_minutes,
        'vcpu_count': vcpu_count,
        'memory_gb': memory_gb,
        'energy_kwh': round(total_energy_kwh, 6),
        'recommendation': recommendation,
        'default_region': default_region,
        'default_intensity': default_intensity,
        'default_sci': round(default_sci, 4),
        'optimal_region': target_region,
        'optimal_intensity': target_intensity,
        'optimal_sci': round(optimal_sci, 4),
        'savings_g': round(savings_g, 4),
        'savings_percent': round(savings_percent, 2),
        'pipeline_status': pipeline_status,
        'pipeline_execution_id': execution_id or '',
        'pipeline_name': pipeline_name
    }
    
    # Load existing history and prepend new result
    history_path = Path(__file__).parent / 'dashboard' / 'public' / 'test-history-data.js'
    
    existing_history = []
    if history_path.exists():
        try:
            content = history_path.read_text()
            # Extract JSON from JS file
            start = content.find('[')
            end = content.rfind(']') + 1
            if start >= 0 and end > start:
                existing_history = json.loads(content[start:end])
        except:
            pass
    
    # Prepend new result
    history = [result] + existing_history[:19]  # Keep last 20
    
    # Save
    js_content = f"""// Auto-generated test history data
// Last updated: {datetime.now().isoformat()}
// Includes REAL pipeline trigger results

const TEST_HISTORY_DATA = {json.dumps(history, indent=2)};

if (typeof window !== 'undefined') {{
    window.TEST_HISTORY_DATA = TEST_HISTORY_DATA;
}}
"""
    
    history_path.write_text(js_content)
    print(f"   ✅ Saved to: {history_path}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"""
   Pipeline: {pipeline_name}
   Status: {pipeline_status.upper()}
   Execution ID: {execution_id or 'N/A'}
   
   Carbon Analysis:
   - Default ({default_region}): {default_sci:.2f} gCO2 @ {default_intensity} gCO2/kWh
   - Optimal ({target_region}): {optimal_sci:.2f} gCO2 @ {target_intensity} gCO2/kWh
   - Savings: {savings_g:.2f} gCO2 ({savings_percent:.1f}%)
   
   Refresh the dashboard to see the new entry in Test History.
""")
    print("=" * 70)


if __name__ == '__main__':
    main()
