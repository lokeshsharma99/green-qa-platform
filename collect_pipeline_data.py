#!/usr/bin/env python3
"""
Manual Pipeline Data Collection Utility

Collects comprehensive pipeline data from AWS services and stores it in DynamoDB.
This can be used to backfill data or collect data for completed pipelines.

Usage:
    python collect_pipeline_data.py <pipeline_name> <execution_id> [region]
    
Examples:
    python collect_pipeline_data.py MyPipeline abc123-def456 eu-west-2
    python collect_pipeline_data.py MyPipeline abc123-def456  # defaults to eu-west-2
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add lambda paths for imports
sys.path.insert(0, str(Path(__file__).parent / 'lambda' / 'pipeline_monitor'))
sys.path.insert(0, str(Path(__file__).parent / 'lambda' / 'api'))

def main():
    if len(sys.argv) < 3:
        print("Usage: python collect_pipeline_data.py <pipeline_name> <execution_id> [region]")
        print("\nExamples:")
        print("  python collect_pipeline_data.py MyPipeline abc123-def456 eu-west-2")
        print("  python collect_pipeline_data.py MyPipeline abc123-def456  # defaults to eu-west-2")
        sys.exit(1)
    
    pipeline_name = sys.argv[1]
    execution_id = sys.argv[2]
    region = sys.argv[3] if len(sys.argv) > 3 else 'eu-west-2'
    
    print("=" * 70)
    print("AWS PIPELINE DATA COLLECTION")
    print("=" * 70)
    print(f"Pipeline: {pipeline_name}")
    print(f"Execution ID: {execution_id}")
    print(f"Region: {region}")
    print()
    
    try:
        # Import the pipeline data collector
        from pipeline_data_collector import (
            collect_pipeline_data,
            calculate_accurate_sci,
            wait_and_collect_pipeline_data
        )
        
        # Check if pipeline is still running
        print("🔍 Step 1: Checking pipeline status...")
        
        import boto3
        codepipeline = boto3.client('codepipeline', region_name=region)
        
        try:
            execution_response = codepipeline.get_pipeline_execution(
                pipelineName=pipeline_name,
                pipelineExecutionId=execution_id
            )
            
            status = execution_response['pipelineExecution']['status']
            print(f"   Pipeline status: {status}")
            
            if status == 'InProgress':
                print("   ⏳ Pipeline is still running. Waiting for completion...")
                
                # Ask user if they want to wait
                response = input("   Wait for completion? (y/n): ")
                if response.lower() == 'y':
                    pipeline_data = wait_and_collect_pipeline_data(pipeline_name, execution_id, region, max_wait_minutes=60)
                else:
                    print("   Collecting current data (may be incomplete)...")
                    pipeline_data = collect_pipeline_data(pipeline_name, execution_id, region)
            else:
                print("   ✅ Pipeline completed. Collecting final data...")
                pipeline_data = collect_pipeline_data(pipeline_name, execution_id, region)
                
        except Exception as e:
            print(f"   ❌ Error checking pipeline status: {e}")
            print("   Attempting to collect available data...")
            pipeline_data = collect_pipeline_data(pipeline_name, execution_id, region)
        
        # Check if data collection was successful
        if pipeline_data.get('error'):
            print(f"❌ Error collecting pipeline data: {pipeline_data['error']}")
            sys.exit(1)
        
        print("✅ Pipeline data collected successfully!")
        
        # Step 2: Get carbon intensity
        print("\n🌍 Step 2: Getting current carbon intensity...")
        
        carbon_intensity = get_carbon_intensity(region)
        print(f"   Carbon intensity for {region}: {carbon_intensity} gCO₂/kWh")
        
        # Step 3: Calculate accurate SCI
        print("\n📊 Step 3: Calculating accurate SCI...")
        
        sci_calculation = calculate_accurate_sci(pipeline_data, carbon_intensity)
        
        print(f"   Calculation method: {sci_calculation.get('calculation_method', 'unknown')}")
        print(f"   Energy consumed: {sci_calculation['energy_kwh']:.6f} kWh")
        print(f"   vCPU hours: {sci_calculation.get('vcpu_hours', 0):.2f}")
        print(f"   Operational carbon: {sci_calculation['operational_g']:.4f} gCO₂")
        print(f"   Embodied carbon: {sci_calculation['embodied_g']:.4f} gCO₂")
        print(f"   Total SCI score: {sci_calculation['sci']:.4f} gCO₂")
        
        # Step 4: Store data
        print("\n💾 Step 4: Storing data in DynamoDB...")
        
        # Create execution record
        execution_record = create_execution_record(pipeline_data, sci_calculation, region)
        
        # Store in DynamoDB
        from pipeline_storage import store_pipeline_execution_data
        
        success = store_pipeline_execution_data(execution_record)
        
        if success:
            print("   ✅ Data stored successfully in DynamoDB!")
        else:
            print("   ❌ Failed to store data in DynamoDB")
            
            # Save to local file as backup
            backup_file = f"pipeline_data_{execution_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w') as f:
                json.dump(execution_record, f, indent=2, default=str)
            print(f"   💾 Data saved to local file: {backup_file}")
        
        # Step 5: Display summary
        print("\n" + "=" * 70)
        print("COLLECTION SUMMARY")
        print("=" * 70)
        
        print(f"Pipeline: {pipeline_name}")
        print(f"Execution ID: {execution_id}")
        print(f"Status: {pipeline_data.get('status', 'UNKNOWN')}")
        print(f"Duration: {pipeline_data.get('duration_seconds', 0)} seconds")
        print(f"Carbon Footprint: {sci_calculation['sci']:.4f} gCO₂")
        print(f"Energy Consumed: {sci_calculation['energy_kwh']:.6f} kWh")
        print(f"Carbon Intensity: {carbon_intensity} gCO₂/kWh")
        
        # Build information
        build_count = 0
        total_build_time = 0
        
        for stage in pipeline_data.get('stages', []):
            for action in stage.get('actions', []):
                if action.get('build_details'):
                    build_count += 1
                    total_build_time += action['build_details'].get('duration_seconds', 0)
        
        if build_count > 0:
            print(f"Build Jobs: {build_count}")
            print(f"Total Build Time: {total_build_time} seconds")
        
        print("\n✅ Data collection completed successfully!")
        print("=" * 70)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project root directory")
        print("and that all required modules are available.")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def get_carbon_intensity(region: str) -> float:
    """Get current carbon intensity for the region"""
    
    try:
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
                pue = 1.135
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
        print(f"   ⚠ Warning: Could not fetch carbon intensity: {e}")
        return 300  # Fallback value


def create_execution_record(pipeline_data: dict, sci_calculation: dict, region: str) -> dict:
    """Create execution record for storage"""
    
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
        'timestamp': int(datetime.now().timestamp()),
        'pipeline_name': pipeline_data['pipeline_name'],
        'pipeline_region': region,
        'trigger_source': 'manual_collection',
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
        
        # Metadata
        'created_at': datetime.now().isoformat(),
        'data_version': '2.0',
        'collection_method': 'manual_script'
    }
    
    return record


if __name__ == '__main__':
    main()