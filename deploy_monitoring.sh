#!/bin/bash

# Deploy ZeroCarb Monitoring Infrastructure
# This script deploys the updated CloudFormation template with pipeline monitoring

set -e

echo "========================================================================"
echo "DEPLOYING ZEROCARB MONITORING INFRASTRUCTURE"
echo "========================================================================"

# Configuration
STACK_NAME="green-qa-platform-prod"
REGION="eu-west-2"
TEMPLATE_FILE="infrastructure/cloudformation.yaml"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI not configured or credentials expired"
    echo "Please run 'aws configure' or refresh your credentials"
    exit 1
fi

echo "✅ AWS credentials verified"

# Check if template file exists
if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "❌ CloudFormation template not found: $TEMPLATE_FILE"
    exit 1
fi

echo "✅ CloudFormation template found"

# Get current account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "📋 AWS Account: $ACCOUNT_ID"
echo "📋 Region: $REGION"
echo "📋 Stack: $STACK_NAME"

# Check if stack exists
if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" > /dev/null 2>&1; then
    echo "📦 Stack exists - updating..."
    ACTION="update-stack"
else
    echo "📦 Stack doesn't exist - creating..."
    ACTION="create-stack"
fi

# Deploy/Update stack
echo "🚀 Deploying infrastructure..."

aws cloudformation $ACTION \
    --stack-name "$STACK_NAME" \
    --template-body file://"$TEMPLATE_FILE" \
    --parameters \
        ParameterKey=Environment,ParameterValue=prod \
        ParameterKey=ElectricityMapsToken,ParameterValue=7Cq9hfFAKl0gAtYNhvc2 \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
    --region "$REGION"

echo "⏳ Waiting for stack deployment to complete..."

# Wait for completion
aws cloudformation wait stack-${ACTION%-stack}-complete \
    --stack-name "$STACK_NAME" \
    --region "$REGION"

if [ $? -eq 0 ]; then
    echo "✅ Stack deployment completed successfully!"
else
    echo "❌ Stack deployment failed or timed out"
    
    # Show stack events for debugging
    echo "📋 Recent stack events:"
    aws cloudformation describe-stack-events \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --max-items 10 \
        --query 'StackEvents[?ResourceStatus==`CREATE_FAILED` || ResourceStatus==`UPDATE_FAILED`].[Timestamp,ResourceType,ResourceStatus,ResourceStatusReason]' \
        --output table
    
    exit 1
fi

# Get stack outputs
echo ""
echo "📊 Stack Outputs:"
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`PipelineMonitorFunctionName` || OutputKey==`PipelineExecutionsTableName` || OutputKey==`ApiEndpoint`].[OutputKey,OutputValue]' \
    --output table

# Update .env file with new function name
MONITOR_FUNCTION=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`PipelineMonitorFunctionName`].OutputValue' \
    --output text)

if [ ! -z "$MONITOR_FUNCTION" ]; then
    echo ""
    echo "📝 Updating .env file with monitor function name..."
    
    # Add or update PIPELINE_MONITOR_FUNCTION in .env
    if grep -q "PIPELINE_MONITOR_FUNCTION=" config/.env; then
        # Update existing line
        sed -i.bak "s/PIPELINE_MONITOR_FUNCTION=.*/PIPELINE_MONITOR_FUNCTION=$MONITOR_FUNCTION/" config/.env
    else
        # Add new line
        echo "PIPELINE_MONITOR_FUNCTION=$MONITOR_FUNCTION" >> config/.env
    fi
    
    echo "✅ Updated PIPELINE_MONITOR_FUNCTION=$MONITOR_FUNCTION"
fi

echo ""
echo "========================================================================"
echo "DEPLOYMENT COMPLETE"
echo "========================================================================"
echo ""
echo "✅ Infrastructure deployed successfully!"
echo "✅ Pipeline monitoring Lambda: $MONITOR_FUNCTION"
echo "✅ DynamoDB tables created"
echo "✅ EventBridge rules configured"
echo ""
echo "🚀 You can now run:"
echo "   python test_real_pipeline.py"
echo ""
echo "📊 Or collect data for the previous execution:"
echo "   python collect_pipeline_data.py GDSDemoAppPipeline-Pipeline-mfCJVEV8nKQS 07fccc9c-460c-4bbc-a604-9de8ddf41a51"
echo ""
echo "========================================================================"