@echo off
REM Deploy ZeroCarb Monitoring Infrastructure (Windows)
REM This script deploys the updated CloudFormation template with pipeline monitoring

echo ========================================================================
echo DEPLOYING ZEROCARB MONITORING INFRASTRUCTURE
echo ========================================================================

REM Configuration
set STACK_NAME=green-qa-platform-prod
set REGION=eu-west-2
set TEMPLATE_FILE=infrastructure/cloudformation.yaml

REM Check if AWS CLI is configured
aws sts get-caller-identity >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ AWS CLI not configured or credentials expired
    echo Please run 'aws configure' or refresh your credentials
    exit /b 1
)

echo ✅ AWS credentials verified

REM Check if template file exists
if not exist "%TEMPLATE_FILE%" (
    echo ❌ CloudFormation template not found: %TEMPLATE_FILE%
    exit /b 1
)

echo ✅ CloudFormation template found

REM Get current account ID
for /f "tokens=*" %%i in ('aws sts get-caller-identity --query Account --output text') do set ACCOUNT_ID=%%i
echo 📋 AWS Account: %ACCOUNT_ID%
echo 📋 Region: %REGION%
echo 📋 Stack: %STACK_NAME%

REM Check if stack exists
aws cloudformation describe-stacks --stack-name "%STACK_NAME%" --region "%REGION%" >nul 2>&1
if %errorlevel% equ 0 (
    echo 📦 Stack exists - updating...
    set ACTION=update-stack
) else (
    echo 📦 Stack doesn't exist - creating...
    set ACTION=create-stack
)

REM Deploy/Update stack
echo 🚀 Deploying infrastructure...

aws cloudformation %ACTION% ^
    --stack-name "%STACK_NAME%" ^
    --template-body file://"%TEMPLATE_FILE%" ^
    --parameters ^
        ParameterKey=Environment,ParameterValue=prod ^
        ParameterKey=ElectricityMapsToken,ParameterValue=7Cq9hfFAKl0gAtYNhvc2 ^
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM ^
    --region "%REGION%"

if %errorlevel% neq 0 (
    echo ❌ Failed to start stack deployment
    exit /b 1
)

echo ⏳ Waiting for stack deployment to complete...

REM Wait for completion
if "%ACTION%"=="create-stack" (
    aws cloudformation wait stack-create-complete --stack-name "%STACK_NAME%" --region "%REGION%"
) else (
    aws cloudformation wait stack-update-complete --stack-name "%STACK_NAME%" --region "%REGION%"
)

if %errorlevel% equ 0 (
    echo ✅ Stack deployment completed successfully!
) else (
    echo ❌ Stack deployment failed or timed out
    
    REM Show stack events for debugging
    echo 📋 Recent stack events:
    aws cloudformation describe-stack-events ^
        --stack-name "%STACK_NAME%" ^
        --region "%REGION%" ^
        --max-items 10 ^
        --query "StackEvents[?ResourceStatus=='CREATE_FAILED' || ResourceStatus=='UPDATE_FAILED'].[Timestamp,ResourceType,ResourceStatus,ResourceStatusReason]" ^
        --output table
    
    exit /b 1
)

REM Get stack outputs
echo.
echo 📊 Stack Outputs:
aws cloudformation describe-stacks ^
    --stack-name "%STACK_NAME%" ^
    --region "%REGION%" ^
    --query "Stacks[0].Outputs[?OutputKey=='PipelineMonitorFunctionName' || OutputKey=='PipelineExecutionsTableName' || OutputKey=='ApiEndpoint'].[OutputKey,OutputValue]" ^
    --output table

REM Get monitor function name
for /f "tokens=*" %%i in ('aws cloudformation describe-stacks --stack-name "%STACK_NAME%" --region "%REGION%" --query "Stacks[0].Outputs[?OutputKey=='PipelineMonitorFunctionName'].OutputValue" --output text') do set MONITOR_FUNCTION=%%i

if not "%MONITOR_FUNCTION%"=="" (
    echo.
    echo 📝 Updating .env file with monitor function name...
    
    REM Add or update PIPELINE_MONITOR_FUNCTION in .env
    findstr /c:"PIPELINE_MONITOR_FUNCTION=" config\.env >nul 2>&1
    if %errorlevel% equ 0 (
        REM Update existing line - create a temp file
        powershell -Command "(Get-Content config\.env) -replace 'PIPELINE_MONITOR_FUNCTION=.*', 'PIPELINE_MONITOR_FUNCTION=%MONITOR_FUNCTION%' | Set-Content config\.env.tmp"
        move config\.env.tmp config\.env >nul
    ) else (
        REM Add new line
        echo PIPELINE_MONITOR_FUNCTION=%MONITOR_FUNCTION% >> config\.env
    )
    
    echo ✅ Updated PIPELINE_MONITOR_FUNCTION=%MONITOR_FUNCTION%
)

echo.
echo ========================================================================
echo DEPLOYMENT COMPLETE
echo ========================================================================
echo.
echo ✅ Infrastructure deployed successfully!
echo ✅ Pipeline monitoring Lambda: %MONITOR_FUNCTION%
echo ✅ DynamoDB tables created
echo ✅ EventBridge rules configured
echo.
echo 🚀 You can now run:
echo    python test_real_pipeline.py
echo.
echo 📊 Or collect data for the previous execution:
echo    python collect_pipeline_data.py GDSDemoAppPipeline-Pipeline-mfCJVEV8nKQS 07fccc9c-460c-4bbc-a604-9de8ddf41a51
echo.
echo ========================================================================

pause