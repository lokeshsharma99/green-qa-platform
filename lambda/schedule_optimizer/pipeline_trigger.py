"""
AWS Pipeline Trigger Module for Green QA Platform

Handles triggering of AWS pipelines based on scheduling decisions.
Supports: CodePipeline, CodeBuild, Step Functions, EventBridge Scheduler

All configuration is loaded from config/pipeline_config.py
"""

import boto3
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import sys
import os

# Add parent directory to path for config import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from config.pipeline_config import (
    AWS_CONFIG,
    CODEPIPELINE_CONFIG,
    CODEBUILD_CONFIG,
    STEPFUNCTIONS_CONFIG,
    EVENTBRIDGE_CONFIG,
    SCHEDULING_CONFIG,
    NOTIFICATION_CONFIG,
    get_pipeline_name,
    get_codebuild_project,
    get_state_machine_arn,
    is_pipeline_configured,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class PipelineTriggerError(Exception):
    """Base exception for pipeline trigger errors."""
    pass


class PipelineNotConfiguredError(PipelineTriggerError):
    """Raised when pipeline is not configured."""
    pass


class PipelineStartError(PipelineTriggerError):
    """Raised when pipeline fails to start."""
    pass


class PipelineScheduleError(PipelineTriggerError):
    """Raised when pipeline scheduling fails."""
    pass


class AWSClientError(PipelineTriggerError):
    """Raised when AWS client operation fails."""
    pass


# ============================================================================
# RESULT CLASSES
# ============================================================================

class TriggerStatus(Enum):
    """Status of pipeline trigger operation."""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    SCHEDULED = "scheduled"
    NOT_CONFIGURED = "not_configured"


@dataclass
class TriggerResult:
    """Result of a pipeline trigger operation."""
    status: TriggerStatus
    service: str
    message: str
    execution_id: Optional[str] = None
    scheduled_time: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        result = {
            "status": self.status.value,
            "service": self.service,
            "message": self.message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if self.execution_id:
            result["execution_id"] = self.execution_id
        if self.scheduled_time:
            result["scheduled_time"] = self.scheduled_time
        if self.error:
            result["error"] = self.error
        return result


# ============================================================================
# AWS CLIENT FACTORY
# ============================================================================

def get_aws_client(service_name: str, region: str = None):
    """
    Create AWS client with proper error handling.
    
    Args:
        service_name: AWS service name (codepipeline, codebuild, etc.)
        region: AWS region (dynamically set based on scheduling decision)
    
    Returns:
        boto3 client
    
    Raises:
        AWSClientError: If client creation fails
    """
    try:
        # Use provided region, or fall back to default
        target_region = region or AWS_CONFIG["default_region"]
        return boto3.client(
            service_name,
            region_name=target_region
        )
    except Exception as e:
        logger.error(f"Failed to create {service_name} client in {region}: {e}")
        raise AWSClientError(f"Failed to create {service_name} client: {e}")


# ============================================================================
# CODEPIPELINE TRIGGER
# ============================================================================

def trigger_codepipeline(
    pipeline_name: str = None,
    workload_type: str = None,
    client_request_token: str = None,
    region: str = None
) -> TriggerResult:
    """
    Trigger AWS CodePipeline execution.
    
    Args:
        pipeline_name: Explicit pipeline name (overrides config)
        workload_type: Workload type to look up pipeline name
        client_request_token: Idempotency token
        region: AWS region (from scheduling decision)
    
    Returns:
        TriggerResult with execution details
    """
    if not CODEPIPELINE_CONFIG["enabled"]:
        return TriggerResult(
            status=TriggerStatus.NOT_CONFIGURED,
            service="CodePipeline",
            message="CodePipeline triggering is disabled"
        )
    
    # Resolve pipeline name
    name = pipeline_name or get_pipeline_name(workload_type)
    if not name:
        return TriggerResult(
            status=TriggerStatus.NOT_CONFIGURED,
            service="CodePipeline",
            message="No pipeline name configured",
            error="CODEPIPELINE_NAME environment variable not set"
        )
    
    # Retry logic
    max_retries = SCHEDULING_CONFIG["max_retries"]
    retry_delay = SCHEDULING_CONFIG["retry_delay_seconds"]
    last_error = None
    target_region = region or AWS_CONFIG["default_region"]
    
    for attempt in range(max_retries):
        try:
            client = get_aws_client("codepipeline", region=target_region)
            
            params = {"name": name}
            if client_request_token:
                params["clientRequestToken"] = client_request_token
            
            response = client.start_pipeline_execution(**params)
            execution_id = response.get("pipelineExecutionId")
            
            logger.info(f"CodePipeline '{name}' triggered in {target_region}: {execution_id}")
            
            return TriggerResult(
                status=TriggerStatus.SUCCESS,
                service="CodePipeline",
                message=f"Pipeline '{name}' triggered in {target_region}",
                execution_id=execution_id
            )
            
        except client.exceptions.PipelineNotFoundException:
            return TriggerResult(
                status=TriggerStatus.FAILED,
                service="CodePipeline",
                message=f"Pipeline '{name}' not found",
                error="PipelineNotFoundException"
            )
            
        except client.exceptions.ConflictException as e:
            # Pipeline already running
            return TriggerResult(
                status=TriggerStatus.SKIPPED,
                service="CodePipeline",
                message=f"Pipeline '{name}' is already running",
                error=str(e)
            )
            
        except Exception as e:
            last_error = str(e)
            logger.warning(f"CodePipeline trigger attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    
    return TriggerResult(
        status=TriggerStatus.FAILED,
        service="CodePipeline",
        message=f"Failed to trigger pipeline '{name}' after {max_retries} attempts",
        error=last_error
    )


# ============================================================================
# CODEBUILD TRIGGER
# ============================================================================

def trigger_codebuild(
    project_name: str = None,
    workload_type: str = None,
    source_version: str = None,
    environment_variables: Dict = None,
    region: str = None
) -> TriggerResult:
    """
    Trigger AWS CodeBuild project.
    
    Args:
        project_name: Explicit project name (overrides config)
        workload_type: Workload type to look up project name
        source_version: Git branch/commit to build
        environment_variables: Additional env vars for build
        region: AWS region (from scheduling decision)
    
    Returns:
        TriggerResult with build details
    """
    if not CODEBUILD_CONFIG["enabled"]:
        return TriggerResult(
            status=TriggerStatus.NOT_CONFIGURED,
            service="CodeBuild",
            message="CodeBuild triggering is disabled"
        )
    
    # Resolve project name
    name = project_name or get_codebuild_project(workload_type)
    if not name:
        return TriggerResult(
            status=TriggerStatus.NOT_CONFIGURED,
            service="CodeBuild",
            message="No CodeBuild project configured",
            error="CODEBUILD_PROJECT environment variable not set"
        )
    
    max_retries = SCHEDULING_CONFIG["max_retries"]
    retry_delay = SCHEDULING_CONFIG["retry_delay_seconds"]
    last_error = None
    target_region = region or AWS_CONFIG["default_region"]
    
    for attempt in range(max_retries):
        try:
            client = get_aws_client("codebuild", region=target_region)
            
            params = {"projectName": name}
            
            # Source version
            version = source_version or CODEBUILD_CONFIG["source_version"]
            if version:
                params["sourceVersion"] = version
            
            # Environment variables
            env_vars = {**CODEBUILD_CONFIG["environment_variables"]}
            if environment_variables:
                env_vars.update(environment_variables)
            
            if env_vars:
                params["environmentVariablesOverride"] = [
                    {"name": k, "value": v, "type": "PLAINTEXT"}
                    for k, v in env_vars.items()
                ]
            
            response = client.start_build(**params)
            build_id = response.get("build", {}).get("id")
            
            logger.info(f"CodeBuild '{name}' triggered in {target_region}: {build_id}")
            
            return TriggerResult(
                status=TriggerStatus.SUCCESS,
                service="CodeBuild",
                message=f"Build project '{name}' triggered in {target_region}",
                execution_id=build_id
            )
            
        except client.exceptions.ResourceNotFoundException:
            return TriggerResult(
                status=TriggerStatus.FAILED,
                service="CodeBuild",
                message=f"Build project '{name}' not found",
                error="ResourceNotFoundException"
            )
            
        except client.exceptions.AccountLimitExceededException as e:
            return TriggerResult(
                status=TriggerStatus.FAILED,
                service="CodeBuild",
                message="Account build limit exceeded",
                error=str(e)
            )
            
        except Exception as e:
            last_error = str(e)
            logger.warning(f"CodeBuild trigger attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    
    return TriggerResult(
        status=TriggerStatus.FAILED,
        service="CodeBuild",
        message=f"Failed to trigger build '{name}' after {max_retries} attempts",
        error=last_error
    )


# ============================================================================
# STEP FUNCTIONS TRIGGER
# ============================================================================

def trigger_stepfunctions(
    state_machine_arn: str = None,
    workload_type: str = None,
    input_data: Dict = None,
    execution_name: str = None,
    region: str = None
) -> TriggerResult:
    """
    Trigger AWS Step Functions state machine.
    
    Args:
        state_machine_arn: Explicit ARN (overrides config)
        workload_type: Workload type to look up ARN
        input_data: JSON input for state machine
        execution_name: Custom execution name
        region: AWS region (from scheduling decision)
    
    Returns:
        TriggerResult with execution details
    """
    if not STEPFUNCTIONS_CONFIG["enabled"]:
        return TriggerResult(
            status=TriggerStatus.NOT_CONFIGURED,
            service="StepFunctions",
            message="Step Functions triggering is disabled"
        )
    
    # Resolve state machine ARN
    arn = state_machine_arn or get_state_machine_arn(workload_type)
    if not arn:
        return TriggerResult(
            status=TriggerStatus.NOT_CONFIGURED,
            service="StepFunctions",
            message="No state machine ARN configured",
            error="STEPFUNCTIONS_ARN environment variable not set"
        )
    
    max_retries = SCHEDULING_CONFIG["max_retries"]
    retry_delay = SCHEDULING_CONFIG["retry_delay_seconds"]
    last_error = None
    target_region = region or AWS_CONFIG["default_region"]
    
    for attempt in range(max_retries):
        try:
            client = get_aws_client("stepfunctions", region=target_region)
            
            params = {"stateMachineArn": arn}
            
            if input_data:
                params["input"] = json.dumps(input_data)
            
            if execution_name:
                params["name"] = execution_name
            else:
                # Generate unique name
                params["name"] = f"green-qa-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
            
            response = client.start_execution(**params)
            execution_arn = response.get("executionArn")
            
            logger.info(f"Step Functions execution started in {target_region}: {execution_arn}")
            
            return TriggerResult(
                status=TriggerStatus.SUCCESS,
                service="StepFunctions",
                message=f"State machine execution started in {target_region}",
                execution_id=execution_arn
            )
            
        except client.exceptions.StateMachineDoesNotExist:
            return TriggerResult(
                status=TriggerStatus.FAILED,
                service="StepFunctions",
                message="State machine not found",
                error="StateMachineDoesNotExist"
            )
            
        except client.exceptions.ExecutionAlreadyExists as e:
            return TriggerResult(
                status=TriggerStatus.SKIPPED,
                service="StepFunctions",
                message="Execution with this name already exists",
                error=str(e)
            )
            
        except Exception as e:
            last_error = str(e)
            logger.warning(f"Step Functions trigger attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    
    return TriggerResult(
        status=TriggerStatus.FAILED,
        service="StepFunctions",
        message=f"Failed to start execution after {max_retries} attempts",
        error=last_error
    )


# ============================================================================
# EVENTBRIDGE SCHEDULER (For DEFER recommendations)
# ============================================================================

def schedule_pipeline_execution(
    scheduled_time: datetime,
    pipeline_name: str = None,
    workload_type: str = None,
    schedule_name: str = None,
    region: str = None
) -> TriggerResult:
    """
    Schedule a pipeline execution for a future time using EventBridge Scheduler.
    Used when DEFER recommendation is made.
    
    Args:
        scheduled_time: When to execute the pipeline
        pipeline_name: Pipeline to trigger
        workload_type: Workload type for pipeline lookup
        schedule_name: Custom schedule name
        region: AWS region (from scheduling decision)
    
    Returns:
        TriggerResult with scheduling details
    """
    if not EVENTBRIDGE_CONFIG["enabled"]:
        return TriggerResult(
            status=TriggerStatus.NOT_CONFIGURED,
            service="EventBridge",
            message="EventBridge scheduling is disabled"
        )
    
    target_arn = EVENTBRIDGE_CONFIG["target_arn"]
    role_arn = EVENTBRIDGE_CONFIG["scheduler_role_arn"]
    
    if not target_arn or not role_arn:
        return TriggerResult(
            status=TriggerStatus.NOT_CONFIGURED,
            service="EventBridge",
            message="EventBridge target or role ARN not configured",
            error="EVENTBRIDGE_TARGET_ARN or EVENTBRIDGE_ROLE_ARN not set"
        )
    
    name = pipeline_name or get_pipeline_name(workload_type)
    target_region = region or AWS_CONFIG["default_region"]
    
    try:
        client = get_aws_client("scheduler", region=target_region)
        
        # Generate schedule name
        sched_name = schedule_name or f"green-qa-defer-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Schedule expression (one-time)
        schedule_expression = f"at({scheduled_time.strftime('%Y-%m-%dT%H:%M:%S')})"
        
        params = {
            "Name": sched_name,
            "GroupName": EVENTBRIDGE_CONFIG["scheduler_group"],
            "ScheduleExpression": schedule_expression,
            "ScheduleExpressionTimezone": "UTC",
            "FlexibleTimeWindow": {"Mode": "OFF"},
            "Target": {
                "Arn": target_arn,
                "RoleArn": role_arn,
                "Input": json.dumps({
                    "action": "trigger_pipeline",
                    "pipeline_name": name,
                    "region": target_region,
                    "scheduled_by": "green-qa-defer",
                    "original_schedule_time": scheduled_time.isoformat(),
                }),
            },
            "ActionAfterCompletion": "DELETE",  # One-time schedule
        }
        
        response = client.create_schedule(**params)
        schedule_arn = response.get("ScheduleArn")
        
        logger.info(f"Pipeline scheduled for {scheduled_time} in {target_region}: {schedule_arn}")
        
        return TriggerResult(
            status=TriggerStatus.SCHEDULED,
            service="EventBridge",
            message=f"Pipeline '{name}' scheduled for {scheduled_time.isoformat()} in {target_region}",
            execution_id=schedule_arn,
            scheduled_time=scheduled_time.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to schedule pipeline: {e}")
        return TriggerResult(
            status=TriggerStatus.FAILED,
            service="EventBridge",
            message="Failed to schedule pipeline execution",
            error=str(e)
        )


# ============================================================================
# SNS NOTIFICATIONS
# ============================================================================

def send_notification(
    subject: str,
    message: str,
    event_type: str = "pipeline_triggered"
) -> bool:
    """
    Send SNS notification for pipeline events.
    
    Args:
        subject: Notification subject
        message: Notification message
        event_type: Type of event for filtering
    
    Returns:
        True if sent successfully, False otherwise
    """
    if not NOTIFICATION_CONFIG["enabled"]:
        return False
    
    if not NOTIFICATION_CONFIG["notify_on"].get(event_type, False):
        return False
    
    topic_arn = NOTIFICATION_CONFIG["sns_topic_arn"]
    if not topic_arn:
        return False
    
    try:
        client = get_aws_client("sns")
        client.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message,
            MessageAttributes={
                "event_type": {
                    "DataType": "String",
                    "StringValue": event_type
                }
            }
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        return False


# ============================================================================
# MAIN TRIGGER FUNCTION (Called by Schedule Optimizer)
# ============================================================================

def execute_pipeline_action(
    recommendation: str,
    region: str,
    workload_type: str = None,
    optimal_window_start: str = None,
    carbon_intensity: float = None,
    estimated_savings: float = None
) -> TriggerResult:
    """
    Execute pipeline action based on scheduling recommendation.
    
    This is the main entry point called by the schedule optimizer.
    
    Args:
        recommendation: One of "run_now", "defer", "relocate", "run_with_warning"
        region: AWS region
        workload_type: Type of workload (test_suite, integration_tests, etc.)
        optimal_window_start: ISO timestamp for deferred execution
        carbon_intensity: Current carbon intensity
        estimated_savings: Estimated carbon savings percentage
    
    Returns:
        TriggerResult with action details
    """
    logger.info(f"Executing pipeline action: {recommendation} for {workload_type or 'default'}")
    
    # Check if any pipeline is configured
    if not is_pipeline_configured():
        return TriggerResult(
            status=TriggerStatus.NOT_CONFIGURED,
            service="None",
            message="No pipeline service is configured. Set environment variables to enable.",
            error="Pipeline configuration missing"
        )
    
    # Handle based on recommendation
    if recommendation == "run_now":
        if not SCHEDULING_CONFIG["auto_trigger_on_run_now"]:
            return TriggerResult(
                status=TriggerStatus.SKIPPED,
                service="None",
                message="Auto-trigger on RUN_NOW is disabled (AUTO_TRIGGER_RUN_NOW=false)"
            )
        
        # Try CodePipeline first, then CodeBuild, then Step Functions
        # Region is passed from the scheduling decision
        if CODEPIPELINE_CONFIG["enabled"]:
            result = trigger_codepipeline(workload_type=workload_type, region=region)
        elif CODEBUILD_CONFIG["enabled"]:
            result = trigger_codebuild(workload_type=workload_type, region=region)
        elif STEPFUNCTIONS_CONFIG["enabled"]:
            result = trigger_stepfunctions(
                workload_type=workload_type,
                region=region,
                input_data={
                    "region": region,
                    "carbon_intensity": carbon_intensity,
                    "triggered_by": "green-qa-run-now"
                }
            )
        else:
            result = TriggerResult(
                status=TriggerStatus.NOT_CONFIGURED,
                service="None",
                message="No pipeline service enabled"
            )
        
        # Send notification
        if result.status == TriggerStatus.SUCCESS:
            send_notification(
                subject=f"[Green QA] Pipeline Triggered - {region}",
                message=f"Pipeline triggered for {workload_type or 'default'} workload.\n"
                        f"Region: {region}\n"
                        f"Carbon Intensity: {carbon_intensity} gCO2/kWh\n"
                        f"Execution ID: {result.execution_id}",
                event_type="pipeline_triggered"
            )
        
        return result
    
    elif recommendation == "defer":
        if not SCHEDULING_CONFIG["auto_schedule_on_defer"]:
            return TriggerResult(
                status=TriggerStatus.SKIPPED,
                service="None",
                message="Auto-schedule on DEFER is disabled (AUTO_SCHEDULE_DEFER=false)"
            )
        
        if not optimal_window_start:
            return TriggerResult(
                status=TriggerStatus.FAILED,
                service="EventBridge",
                message="Cannot schedule: no optimal window start time provided",
                error="optimal_window_start is required for DEFER"
            )
        
        # Parse scheduled time
        try:
            scheduled_time = datetime.fromisoformat(optimal_window_start.replace('Z', '+00:00'))
        except ValueError as e:
            return TriggerResult(
                status=TriggerStatus.FAILED,
                service="EventBridge",
                message=f"Invalid scheduled time format: {optimal_window_start}",
                error=str(e)
            )
        
        result = schedule_pipeline_execution(
            scheduled_time=scheduled_time,
            workload_type=workload_type,
            region=region
        )
        
        # Send notification
        if result.status == TriggerStatus.SCHEDULED:
            send_notification(
                subject=f"[Green QA] Pipeline Scheduled - {region}",
                message=f"Pipeline scheduled for {workload_type or 'default'} workload.\n"
                        f"Scheduled Time: {scheduled_time.isoformat()}\n"
                        f"Estimated Savings: {estimated_savings:.1f}%\n"
                        f"Current Intensity: {carbon_intensity} gCO2/kWh",
                event_type="pipeline_scheduled"
            )
        
        return result
    
    elif recommendation == "run_with_warning":
        # Trigger but send warning notification
        if not SCHEDULING_CONFIG["auto_trigger_on_run_now"]:
            return TriggerResult(
                status=TriggerStatus.SKIPPED,
                service="None",
                message="Auto-trigger is disabled"
            )
        
        # Send high carbon warning
        send_notification(
            subject=f"[Green QA] ⚠️ High Carbon Warning - {region}",
            message=f"Pipeline triggered during HIGH carbon intensity period.\n"
                    f"Region: {region}\n"
                    f"Carbon Intensity: {carbon_intensity} gCO2/kWh\n"
                    f"Consider deferring non-urgent workloads.",
            event_type="high_carbon_warning"
        )
        
        # Still trigger the pipeline in the specified region
        if CODEPIPELINE_CONFIG["enabled"]:
            return trigger_codepipeline(workload_type=workload_type, region=region)
        elif CODEBUILD_CONFIG["enabled"]:
            return trigger_codebuild(workload_type=workload_type, region=region)
        else:
            return TriggerResult(
                status=TriggerStatus.NOT_CONFIGURED,
                service="None",
                message="No pipeline service enabled"
            )
    
    elif recommendation == "relocate":
        # Trigger pipeline in the optimal (alternative) region for carbon savings
        if not SCHEDULING_CONFIG["auto_trigger_on_run_now"]:
            return TriggerResult(
                status=TriggerStatus.SKIPPED,
                service="None",
                message="Auto-trigger is disabled (AUTO_TRIGGER_RUN_NOW=false)"
            )
        
        # Use the optimal region passed from scheduler for triggering
        # This enables actual carbon savings through geographic load shifting
        if CODEPIPELINE_CONFIG["enabled"]:
            result = trigger_codepipeline(workload_type=workload_type, region=region)
        elif CODEBUILD_CONFIG["enabled"]:
            result = trigger_codebuild(workload_type=workload_type, region=region)
        elif STEPFUNCTIONS_CONFIG["enabled"]:
            result = trigger_stepfunctions(
                workload_type=workload_type,
                region=region,
                input_data={
                    "region": region,
                    "carbon_intensity": carbon_intensity,
                    "triggered_by": "green-qa-relocate",
                    "estimated_savings_percent": estimated_savings
                }
            )
        else:
            return TriggerResult(
                status=TriggerStatus.NOT_CONFIGURED,
                service="None",
                message="No pipeline service enabled"
            )
        
        # Send notification about relocation
        if result.status == TriggerStatus.SUCCESS:
            send_notification(
                subject=f"[Green QA] Pipeline Relocated to {region}",
                message=f"Pipeline triggered in optimal region for carbon savings.\n"
                        f"Region: {region}\n"
                        f"Carbon Intensity: {carbon_intensity} gCO2/kWh\n"
                        f"Estimated Savings: {estimated_savings:.1f}%\n"
                        f"Execution ID: {result.execution_id}",
                event_type="pipeline_triggered"
            )
        
        return result
    
    else:
        return TriggerResult(
            status=TriggerStatus.FAILED,
            service="None",
            message=f"Unknown recommendation: {recommendation}",
            error="Invalid recommendation type"
        )


# ============================================================================
# TESTING / CLI
# ============================================================================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from config.pipeline_config import get_config_summary
    
    print("=" * 60)
    print("Pipeline Trigger Module - Configuration Check")
    print("=" * 60)
    
    config = get_config_summary()
    for key, value in config.items():
        if key == "region_note":
            print(f"  ℹ {value}")
        else:
            status = "✓" if value and value not in ["(not set)", False] else "✗"
            print(f"  {status} {key}: {value}")
    
    print("\n" + "=" * 60)
    print("IMPORTANT: Region is determined by scheduling decision")
    print("=" * 60)
    print("""
  The pipeline will run in the region recommended by the
  schedule optimizer based on lowest carbon intensity.
  
  Example flow:
  1. Schedule optimizer checks carbon intensity across regions
  2. Recommends optimal region (e.g., eu-north-1 for low carbon)
  3. Pipeline is triggered IN THAT REGION
    """)
    
    print("=" * 60)
    print("To enable pipeline triggering, set these environment variables:")
    print("=" * 60)
    print("""
  # Enable CodePipeline
  export CODEPIPELINE_ENABLED=true
  export CODEPIPELINE_NAME=your-pipeline-name
  
  # Enable auto-trigger on RUN_NOW
  export AUTO_TRIGGER_RUN_NOW=true
  
  # Enable auto-schedule on DEFER
  export AUTO_SCHEDULE_DEFER=true
  export EVENTBRIDGE_ENABLED=true
  export EVENTBRIDGE_TARGET_ARN=arn:aws:...
  export EVENTBRIDGE_ROLE_ARN=arn:aws:iam::...
    """)
