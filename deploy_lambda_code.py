#!/usr/bin/env python3
"""
Deploy Lambda Function Code

This script packages and deploys the actual Lambda function code to the 
infrastructure created by CloudFormation.
"""

import boto3
import zipfile
import os
import tempfile
import shutil
from pathlib import Path

def create_lambda_package(source_dir: str, handler_file: str) -> bytes:
    """Create a Lambda deployment package"""
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Copy source files
        source_path = Path(source_dir)
        for file_path in source_path.glob("*.py"):
            shutil.copy2(file_path, temp_path / file_path.name)
        
        # Create ZIP file in memory
        zip_buffer = tempfile.NamedTemporaryFile()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in temp_path.glob("*.py"):
                zip_file.write(file_path, file_path.name)
        
        zip_buffer.seek(0)
        return zip_buffer.read()

def deploy_lambda_functions():
    """Deploy all Lambda functions"""
    
    lambda_client = boto3.client('lambda', region_name='eu-west-2')
    
    # Function configurations
    functions = [
        {
            'name': 'green-qa-pipeline-monitor-prod',
            'source_dir': 'lambda/pipeline_monitor',
            'handler': 'completion_handler.lambda_handler',
            'description': 'Pipeline completion monitor with real AWS data collection'
        }
    ]
    
    for func_config in functions:
        try:
            print(f"📦 Packaging {func_config['name']}...")
            
            # Create deployment package
            zip_content = create_lambda_package(
                func_config['source_dir'], 
                func_config['handler'].split('.')[0] + '.py'
            )
            
            print(f"🚀 Deploying {func_config['name']}...")
            
            # Update function code
            response = lambda_client.update_function_code(
                FunctionName=func_config['name'],
                ZipFile=zip_content
            )
            
            print(f"✅ Successfully deployed {func_config['name']}")
            print(f"   Version: {response['Version']}")
            print(f"   Size: {len(zip_content)} bytes")
            
        except Exception as e:
            print(f"❌ Failed to deploy {func_config['name']}: {e}")

if __name__ == "__main__":
    print("========================================================================")
    print("DEPLOYING LAMBDA FUNCTION CODE")
    print("========================================================================")
    
    deploy_lambda_functions()
    
    print("\n========================================================================")
    print("DEPLOYMENT COMPLETE")
    print("========================================================================")
    print("\n✅ Lambda functions updated with real code")
    print("✅ Ready to collect pipeline data")
    print("\n🚀 Test with:")
    print("   python collect_pipeline_data.py GDSDemoAppPipeline-Pipeline-mfCJVEV8nKQS fe1a69cb-ee5a-48ea-819d-f0092b8447a6")