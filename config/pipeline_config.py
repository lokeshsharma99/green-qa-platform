"""
Pipeline Configuration for Green QA Platform

All AWS pipeline settings are centralized here.
Update these values with your actual pipeline details.

AWS Services Supported:
- CodePipeline: CI/CD pipelines
- CodeBuild: Build projects
- Step Functions: State machines
- EventBridge: Scheduled rules
"""

import os

# ============================================================================
# AWS GENERAL CONFIGURATION
# ============================================================================

AWS_CONFIG = {
    # AWS Region is NOT set here - it's passed dynamically based on
    # the scheduling decision (optimal region for lowest carbon)
    # Default fallback only used if no region is provided
    "default_region": os.environ.get("AWS_DEFAULT_REGION", "eu-west-2"),
    
    # AWS Account ID (optional, for cross-account)
    "account_id": os.environ.get("AWS_ACCOUNT_ID", ""),
    
    # IAM Role ARN for pipeline execution (optional)
    "execution_role_arn": os.environ.get("AWS_EXECUTION_ROLE_ARN", ""),
}

# ============================================================================
# CODEPIPELINE CONFIGURATION
# ============================================================================

CODEPIPELINE_CONFIG = {
    # Enable/disable CodePipeline triggering
    "enabled": os.environ.get("CODEPIPELINE_ENABLED", "false").lower() == "true",
    
    # Default pipeline name to trigger
    "default_pipeline_name": os.environ.get("CODEPIPELINE_NAME", ""),
    
    # Pipeline names mapped to workload types
    "pipelines": {
        "test_suite": os.environ.get("CODEPIPELINE_TEST_SUITE", ""),
        "integration_tests": os.environ.get("CODEPIPELINE_INTEGRATION", ""),
        "e2e_tests": os.environ.get("CODEPIPELINE_E2E", ""),
        "full_build": os.environ.get("CODEPIPELINE_FULL_BUILD", ""),
    },
    
    # Timeout for pipeline start (seconds)
    "start_timeout": int(os.environ.get("CODEPIPELINE_TIMEOUT", "30")),
}

# ============================================================================
# CODEBUILD CONFIGURATION
# ============================================================================

CODEBUILD_CONFIG = {
    # Enable/disable CodeBuild triggering
    "enabled": os.environ.get("CODEBUILD_ENABLED", "false").lower() == "true",
    
    # Default build project name
    "default_project_name": os.environ.get("CODEBUILD_PROJECT", ""),
    
    # Build projects mapped to workload types
    "projects": {
        "unit_tests": os.environ.get("CODEBUILD_UNIT_TESTS", ""),
        "integration_tests": os.environ.get("CODEBUILD_INTEGRATION", ""),
        "security_scan": os.environ.get("CODEBUILD_SECURITY", ""),
    },
    
    # Environment variables to pass to build
    "environment_variables": {
        "CARBON_AWARE": "true",
        "TRIGGERED_BY": "green-qa-scheduler",
    },
    
    # Source version (branch/commit)
    "source_version": os.environ.get("CODEBUILD_SOURCE_VERSION", "main"),
}

# ============================================================================
# STEP FUNCTIONS CONFIGURATION
# ============================================================================

STEPFUNCTIONS_CONFIG = {
    # Enable/disable Step Functions triggering
    "enabled": os.environ.get("STEPFUNCTIONS_ENABLED", "false").lower() == "true",
    
    # State machine ARN
    "state_machine_arn": os.environ.get("STEPFUNCTIONS_ARN", ""),
    
    # State machines mapped to workload types
    "state_machines": {
        "test_workflow": os.environ.get("STEPFUNCTIONS_TEST_WORKFLOW", ""),
        "deploy_workflow": os.environ.get("STEPFUNCTIONS_DEPLOY_WORKFLOW", ""),
    },
}

# ============================================================================
# EVENTBRIDGE SCHEDULER CONFIGURATION
# ============================================================================

EVENTBRIDGE_CONFIG = {
    # Enable/disable EventBridge scheduling
    "enabled": os.environ.get("EVENTBRIDGE_ENABLED", "false").lower() == "true",
    
    # Scheduler group name
    "scheduler_group": os.environ.get("EVENTBRIDGE_GROUP", "green-qa-schedules"),
    
    # Target ARN for scheduled events
    "target_arn": os.environ.get("EVENTBRIDGE_TARGET_ARN", ""),
    
    # IAM Role for scheduler
    "scheduler_role_arn": os.environ.get("EVENTBRIDGE_ROLE_ARN", ""),
}

# ============================================================================
# SCHEDULING BEHAVIOR CONFIGURATION
# ============================================================================

SCHEDULING_CONFIG = {
    # Auto-trigger pipeline on RUN_NOW recommendation
    "auto_trigger_on_run_now": os.environ.get("AUTO_TRIGGER_RUN_NOW", "false").lower() == "true",
    
    # Auto-schedule pipeline on DEFER recommendation
    "auto_schedule_on_defer": os.environ.get("AUTO_SCHEDULE_DEFER", "false").lower() == "true",
    
    # Minimum carbon savings (%) to trigger defer scheduling
    "min_savings_for_defer": float(os.environ.get("MIN_SAVINGS_DEFER", "15")),
    
    # Maximum defer window (hours)
    "max_defer_hours": int(os.environ.get("MAX_DEFER_HOURS", "24")),
    
    # Retry configuration
    "max_retries": int(os.environ.get("PIPELINE_MAX_RETRIES", "3")),
    "retry_delay_seconds": int(os.environ.get("PIPELINE_RETRY_DELAY", "5")),
}

# ============================================================================
# NOTIFICATION CONFIGURATION
# ============================================================================

NOTIFICATION_CONFIG = {
    # SNS Topic ARN for notifications
    "sns_topic_arn": os.environ.get("SNS_TOPIC_ARN", ""),
    
    # Enable notifications
    "enabled": os.environ.get("NOTIFICATIONS_ENABLED", "false").lower() == "true",
    
    # Notify on these events
    "notify_on": {
        "pipeline_triggered": True,
        "pipeline_scheduled": True,
        "pipeline_failed": True,
        "high_carbon_warning": True,
    },
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_pipeline_name(workload_type: str = None) -> str:
    """Get pipeline name for workload type or default."""
    if workload_type and workload_type in CODEPIPELINE_CONFIG["pipelines"]:
        name = CODEPIPELINE_CONFIG["pipelines"][workload_type]
        if name:
            return name
    return CODEPIPELINE_CONFIG["default_pipeline_name"]


def get_codebuild_project(workload_type: str = None) -> str:
    """Get CodeBuild project name for workload type or default."""
    if workload_type and workload_type in CODEBUILD_CONFIG["projects"]:
        name = CODEBUILD_CONFIG["projects"][workload_type]
        if name:
            return name
    return CODEBUILD_CONFIG["default_project_name"]


def get_state_machine_arn(workload_type: str = None) -> str:
    """Get Step Functions state machine ARN for workload type or default."""
    if workload_type and workload_type in STEPFUNCTIONS_CONFIG["state_machines"]:
        arn = STEPFUNCTIONS_CONFIG["state_machines"][workload_type]
        if arn:
            return arn
    return STEPFUNCTIONS_CONFIG["state_machine_arn"]


def is_pipeline_configured() -> bool:
    """Check if any pipeline service is configured and enabled."""
    return (
        (CODEPIPELINE_CONFIG["enabled"] and CODEPIPELINE_CONFIG["default_pipeline_name"]) or
        (CODEBUILD_CONFIG["enabled"] and CODEBUILD_CONFIG["default_project_name"]) or
        (STEPFUNCTIONS_CONFIG["enabled"] and STEPFUNCTIONS_CONFIG["state_machine_arn"])
    )


def get_config_summary() -> dict:
    """Get summary of current configuration for debugging."""
    return {
        "aws_default_region": AWS_CONFIG["default_region"],
        "region_note": "Region is dynamically set based on scheduling decision",
        "codepipeline_enabled": CODEPIPELINE_CONFIG["enabled"],
        "codepipeline_name": CODEPIPELINE_CONFIG["default_pipeline_name"] or "(not set)",
        "codebuild_enabled": CODEBUILD_CONFIG["enabled"],
        "codebuild_project": CODEBUILD_CONFIG["default_project_name"] or "(not set)",
        "stepfunctions_enabled": STEPFUNCTIONS_CONFIG["enabled"],
        "auto_trigger_run_now": SCHEDULING_CONFIG["auto_trigger_on_run_now"],
        "auto_schedule_defer": SCHEDULING_CONFIG["auto_schedule_on_defer"],
        "notifications_enabled": NOTIFICATION_CONFIG["enabled"],
    }
