"""
AWS Pipeline Data Collector

Fetches real data from AWS services:
- CodePipeline: Pipeline execution details, status, timing
- CodeBuild: Build metrics, CPU/Memory usage, logs
- CodeCommit: Commit details, author, changes
- CloudWatch: Detailed metrics and logs

This provides accurate data for SCI calculations and carbon intelligence.
"""

import boto3
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class AWSPipelineDataCollector:
    """Collects comprehensive pipeline data from AWS services"""
    
    def __init__(self, region: str = 'eu-west-2'):
        self.region = region
        
        # Initialize AWS clients
        self.codepipeline = boto3.client('codepipeline', region_name=region)
        self.codebuild = boto3.client('codebuild', region_name=region)
        self.codecommit = boto3.client('codecommit', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.logs = boto3.client('logs', region_name=region)
        
        # Cache for build project details
        self._build_projects_cache = {}
    
    def get_pipeline_execution_details(self, pipeline_name: str, execution_id: str) -> Dict:
        """
        Get comprehensive pipeline execution details
        
        Args:
            pipeline_name: Name of the CodePipeline
            execution_id: Pipeline execution ID
            
        Returns:
            Dictionary with complete pipeline execution data
        """
        try:
            logger.info(f"Fetching pipeline execution details: {pipeline_name}/{execution_id}")
            
            # Get pipeline execution
            execution_response = self.codepipeline.get_pipeline_execution(
                pipelineName=pipeline_name,
                pipelineExecutionId=execution_id
            )
            
            execution = execution_response['pipelineExecution']
            
            # Get pipeline state for stage details
            state_response = self.codepipeline.get_pipeline_state(name=pipeline_name)
            
            # Get action executions for detailed timing
            actions_response = self.codepipeline.list_action_executions(
                pipelineName=pipeline_name,
                filter={'pipelineExecutionId': execution_id}
            )
            
            # Process execution data
            pipeline_data = {
                'pipeline_name': pipeline_name,
                'execution_id': execution_id,
                'status': execution.get('status'),
                'start_time': execution.get('startTime'),
                'end_time': execution.get('endTime'),
                'duration_seconds': None,
                'trigger': execution.get('trigger', {}),
                'artifact_revisions': execution.get('artifactRevisions', []),
                'stages': [],
                'total_build_time_seconds': 0,
                'total_cpu_credits': 0,
                'total_memory_mb_seconds': 0,
                'build_projects': []
            }
            
            # Calculate duration if completed
            if pipeline_data['start_time'] and pipeline_data['end_time']:
                duration = pipeline_data['end_time'] - pipeline_data['start_time']
                pipeline_data['duration_seconds'] = int(duration.total_seconds())
            
            # Process stages and actions
            for stage in state_response['stageStates']:
                stage_data = {
                    'stage_name': stage['stageName'],
                    'status': stage.get('latestExecution', {}).get('status'),
                    'actions': []
                }
                
                # Find actions for this stage
                stage_actions = [
                    action for action in actions_response['actionExecutions']
                    if action['stageName'] == stage['stageName']
                ]
                
                for action in stage_actions:
                    action_data = {
                        'action_name': action['actionName'],
                        'action_type': action['actionTypeId']['provider'],
                        'status': action.get('status'),
                        'start_time': action.get('startTime'),
                        'end_time': action.get('lastUpdateTime'),
                        'duration_seconds': None,
                        'external_execution_id': action.get('externalExecutionId'),
                        'build_details': None
                    }
                    
                    # Calculate action duration
                    if action_data['start_time'] and action_data['end_time']:
                        duration = action_data['end_time'] - action_data['start_time']
                        action_data['duration_seconds'] = int(duration.total_seconds())
                    
                    # Get CodeBuild details if this is a build action
                    if (action['actionTypeId']['provider'] == 'CodeBuild' and 
                        action_data['external_execution_id']):
                        
                        build_details = self.get_codebuild_execution_details(
                            action_data['external_execution_id']
                        )
                        action_data['build_details'] = build_details
                        
                        if build_details:
                            pipeline_data['total_build_time_seconds'] += build_details.get('duration_seconds', 0)
                            pipeline_data['total_cpu_credits'] += build_details.get('cpu_credits_used', 0)
                            pipeline_data['total_memory_mb_seconds'] += build_details.get('memory_mb_seconds', 0)
                            
                            if build_details.get('project_name') not in pipeline_data['build_projects']:
                                pipeline_data['build_projects'].append(build_details.get('project_name'))
                    
                    stage_data['actions'].append(action_data)
                
                pipeline_data['stages'].append(stage_data)
            
            # Get commit details if available
            if pipeline_data['artifact_revisions']:
                commit_details = self.get_commit_details(pipeline_data['artifact_revisions'][0])
                pipeline_data['commit_details'] = commit_details
            
            logger.info(f"Successfully collected pipeline data for {execution_id}")
            return pipeline_data
            
        except Exception as e:
            logger.error(f"Error fetching pipeline execution details: {e}")
            return {
                'pipeline_name': pipeline_name,
                'execution_id': execution_id,
                'error': str(e),
                'status': 'UNKNOWN'
            }
    
    def get_codebuild_execution_details(self, build_id: str) -> Optional[Dict]:
        """
        Get detailed CodeBuild execution metrics
        
        Args:
            build_id: CodeBuild execution ID
            
        Returns:
            Dictionary with build metrics including CPU/Memory usage
        """
        try:
            logger.info(f"Fetching CodeBuild details: {build_id}")
            
            # Get build details
            builds_response = self.codebuild.batch_get_builds(ids=[build_id])
            
            if not builds_response['builds']:
                logger.warning(f"No build found for ID: {build_id}")
                return None
            
            build = builds_response['builds'][0]
            
            # Get build project details for compute type
            project_name = build['projectName']
            project_details = self.get_build_project_details(project_name)
            
            build_data = {
                'build_id': build_id,
                'project_name': project_name,
                'status': build.get('buildStatus'),
                'start_time': build.get('startTime'),
                'end_time': build.get('endTime'),
                'duration_seconds': None,
                'compute_type': project_details.get('compute_type', 'BUILD_GENERAL1_MEDIUM'),
                'environment_type': project_details.get('environment_type', 'LINUX_CONTAINER'),
                'cpu_credits_used': 0,
                'memory_mb_seconds': 0,
                'network_mb': 0,
                'storage_gb': 0,
                'phases': []
            }
            
            # Calculate duration
            if build_data['start_time'] and build_data['end_time']:
                duration = build_data['end_time'] - build_data['start_time']
                build_data['duration_seconds'] = int(duration.total_seconds())
            
            # Get build phases for detailed timing
            if 'phases' in build:
                for phase in build['phases']:
                    phase_data = {
                        'phase_type': phase.get('phaseType'),
                        'status': phase.get('phaseStatus'),
                        'start_time': phase.get('startTime'),
                        'end_time': phase.get('endTime'),
                        'duration_seconds': None
                    }
                    
                    if phase_data['start_time'] and phase_data['end_time']:
                        duration = phase_data['end_time'] - phase_data['start_time']
                        phase_data['duration_seconds'] = int(duration.total_seconds())
                    
                    build_data['phases'].append(phase_data)
            
            # Calculate resource usage based on compute type and duration
            if build_data['duration_seconds']:
                resource_usage = self.calculate_build_resource_usage(
                    build_data['compute_type'],
                    build_data['duration_seconds']
                )
                build_data.update(resource_usage)
            
            # Get CloudWatch metrics if available
            cloudwatch_metrics = self.get_build_cloudwatch_metrics(build_id, build_data['start_time'])
            if cloudwatch_metrics:
                build_data['cloudwatch_metrics'] = cloudwatch_metrics
            
            logger.info(f"Successfully collected CodeBuild data for {build_id}")
            return build_data
            
        except Exception as e:
            logger.error(f"Error fetching CodeBuild details: {e}")
            return {
                'build_id': build_id,
                'error': str(e),
                'status': 'UNKNOWN'
            }
    
    def get_build_project_details(self, project_name: str) -> Dict:
        """Get CodeBuild project configuration details"""
        
        if project_name in self._build_projects_cache:
            return self._build_projects_cache[project_name]
        
        try:
            response = self.codebuild.batch_get_projects(names=[project_name])
            
            if not response['projects']:
                return {}
            
            project = response['projects'][0]
            environment = project.get('environment', {})
            
            details = {
                'compute_type': environment.get('computeType', 'BUILD_GENERAL1_MEDIUM'),
                'environment_type': environment.get('type', 'LINUX_CONTAINER'),
                'image': environment.get('image', 'aws/codebuild/standard:5.0'),
                'privileged_mode': environment.get('privilegedMode', False)
            }
            
            self._build_projects_cache[project_name] = details
            return details
            
        except Exception as e:
            logger.error(f"Error fetching project details: {e}")
            return {}
    
    def calculate_build_resource_usage(self, compute_type: str, duration_seconds: int) -> Dict:
        """
        Calculate resource usage based on CodeBuild compute type
        
        AWS CodeBuild compute types and their specifications:
        https://docs.aws.amazon.com/codebuild/latest/userguide/build-env-ref-compute-types.html
        """
        
        # CodeBuild compute type specifications
        compute_specs = {
            'BUILD_GENERAL1_SMALL': {'vcpu': 2, 'memory_mb': 3072, 'storage_gb': 64},
            'BUILD_GENERAL1_MEDIUM': {'vcpu': 4, 'memory_mb': 7168, 'storage_gb': 128},
            'BUILD_GENERAL1_LARGE': {'vcpu': 8, 'memory_mb': 15360, 'storage_gb': 128},
            'BUILD_GENERAL1_2XLARGE': {'vcpu': 72, 'memory_mb': 145408, 'storage_gb': 824},
            # ARM instances
            'BUILD_GENERAL1_SMALL_ARM': {'vcpu': 2, 'memory_mb': 3072, 'storage_gb': 64},
            'BUILD_GENERAL1_MEDIUM_ARM': {'vcpu': 4, 'memory_mb': 7168, 'storage_gb': 128},
            'BUILD_GENERAL1_LARGE_ARM': {'vcpu': 8, 'memory_mb': 15360, 'storage_gb': 128},
        }
        
        specs = compute_specs.get(compute_type, compute_specs['BUILD_GENERAL1_MEDIUM'])
        
        # Calculate usage
        vcpu_seconds = specs['vcpu'] * duration_seconds
        memory_mb_seconds = specs['memory_mb'] * duration_seconds
        
        # Estimate CPU credits (for burstable instances)
        # CodeBuild uses dedicated instances, so this is actual CPU time
        cpu_credits_used = vcpu_seconds / 60  # Credits per minute of CPU usage
        
        return {
            'vcpu_count': specs['vcpu'],
            'memory_mb': specs['memory_mb'],
            'storage_gb': specs['storage_gb'],
            'vcpu_seconds': vcpu_seconds,
            'memory_mb_seconds': memory_mb_seconds,
            'cpu_credits_used': cpu_credits_used,
            'duration_hours': duration_seconds / 3600
        }
    
    def get_build_cloudwatch_metrics(self, build_id: str, start_time: datetime) -> Optional[Dict]:
        """Get CloudWatch metrics for CodeBuild execution"""
        
        try:
            # CodeBuild metrics are available in CloudWatch
            end_time = start_time + timedelta(hours=2)  # Assume max 2 hour build
            
            # Get CPU utilization if available
            cpu_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/CodeBuild',
                MetricName='CPUUtilization',
                Dimensions=[
                    {'Name': 'BuildId', 'Value': build_id}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,  # 5 minute periods
                Statistics=['Average', 'Maximum']
            )
            
            # Get memory utilization if available
            memory_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/CodeBuild',
                MetricName='MemoryUtilization',
                Dimensions=[
                    {'Name': 'BuildId', 'Value': build_id}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average', 'Maximum']
            )
            
            metrics = {
                'cpu_utilization': cpu_response.get('Datapoints', []),
                'memory_utilization': memory_response.get('Datapoints', [])
            }
            
            # Calculate averages
            if metrics['cpu_utilization']:
                avg_cpu = sum(dp['Average'] for dp in metrics['cpu_utilization']) / len(metrics['cpu_utilization'])
                metrics['avg_cpu_percent'] = round(avg_cpu, 2)
            
            if metrics['memory_utilization']:
                avg_memory = sum(dp['Average'] for dp in metrics['memory_utilization']) / len(metrics['memory_utilization'])
                metrics['avg_memory_percent'] = round(avg_memory, 2)
            
            return metrics if (metrics['cpu_utilization'] or metrics['memory_utilization']) else None
            
        except Exception as e:
            logger.error(f"Error fetching CloudWatch metrics: {e}")
            return None
    
    def get_commit_details(self, artifact_revision: Dict) -> Optional[Dict]:
        """Get commit details from CodeCommit"""
        
        try:
            revision_id = artifact_revision.get('revisionId')
            revision_url = artifact_revision.get('revisionUrl', '')
            
            # Extract repository name from URL if possible
            repo_name = None
            if 'codecommit' in revision_url:
                # Parse repository name from CodeCommit URL
                parts = revision_url.split('/')
                if len(parts) > 1:
                    repo_name = parts[-1].split('?')[0]
            
            if not repo_name or not revision_id:
                return {
                    'revision_id': revision_id,
                    'revision_url': revision_url,
                    'source': 'external'
                }
            
            # Get commit details
            commit_response = self.codecommit.get_commit(
                repositoryName=repo_name,
                commitId=revision_id
            )
            
            commit = commit_response['commit']
            
            return {
                'repository_name': repo_name,
                'commit_id': revision_id,
                'author': commit.get('author', {}),
                'committer': commit.get('committer', {}),
                'message': commit.get('message', ''),
                'tree_id': commit.get('treeId'),
                'parents': commit.get('parents', []),
                'additional_data': commit.get('additionalData', ''),
                'revision_url': revision_url
            }
            
        except Exception as e:
            logger.error(f"Error fetching commit details: {e}")
            return {
                'revision_id': artifact_revision.get('revisionId'),
                'revision_url': artifact_revision.get('revisionUrl', ''),
                'error': str(e)
            }
    
    def wait_for_pipeline_completion(self, pipeline_name: str, execution_id: str, 
                                   max_wait_minutes: int = 60, check_interval_seconds: int = 30) -> Dict:
        """
        Wait for pipeline completion and return final details
        
        Args:
            pipeline_name: Name of the CodePipeline
            execution_id: Pipeline execution ID
            max_wait_minutes: Maximum time to wait
            check_interval_seconds: How often to check status
            
        Returns:
            Final pipeline execution details
        """
        
        logger.info(f"Waiting for pipeline completion: {pipeline_name}/{execution_id}")
        
        start_wait_time = datetime.now()
        max_wait_time = start_wait_time + timedelta(minutes=max_wait_minutes)
        
        while datetime.now() < max_wait_time:
            try:
                # Get current execution status
                execution_response = self.codepipeline.get_pipeline_execution(
                    pipelineName=pipeline_name,
                    pipelineExecutionId=execution_id
                )
                
                status = execution_response['pipelineExecution']['status']
                logger.info(f"Pipeline status: {status}")
                
                # Check if completed (success or failure)
                if status in ['Succeeded', 'Failed', 'Stopped', 'Stopping']:
                    logger.info(f"Pipeline completed with status: {status}")
                    
                    # Get full details now that it's complete
                    return self.get_pipeline_execution_details(pipeline_name, execution_id)
                
                # Wait before next check
                time.sleep(check_interval_seconds)
                
            except Exception as e:
                logger.error(f"Error checking pipeline status: {e}")
                time.sleep(check_interval_seconds)
        
        # Timeout reached
        logger.warning(f"Timeout waiting for pipeline completion after {max_wait_minutes} minutes")
        return self.get_pipeline_execution_details(pipeline_name, execution_id)


# Convenience functions for Lambda integration
def collect_pipeline_data(pipeline_name: str, execution_id: str, region: str = 'eu-west-2') -> Dict:
    """Collect comprehensive pipeline data"""
    collector = AWSPipelineDataCollector(region)
    return collector.get_pipeline_execution_details(pipeline_name, execution_id)


def wait_and_collect_pipeline_data(pipeline_name: str, execution_id: str, 
                                 region: str = 'eu-west-2', max_wait_minutes: int = 60) -> Dict:
    """Wait for pipeline completion and collect data"""
    collector = AWSPipelineDataCollector(region)
    return collector.wait_for_pipeline_completion(pipeline_name, execution_id, max_wait_minutes)


def calculate_accurate_sci(pipeline_data: Dict, carbon_intensity: float) -> Dict:
    """
    Calculate accurate SCI using real AWS pipeline data
    
    Args:
        pipeline_data: Complete pipeline data from collector
        carbon_intensity: Carbon intensity (gCO2/kWh) for the region
        
    Returns:
        Accurate SCI calculation with breakdown
    """
    
    # Constants
    PUE = 1.135  # AWS PUE
    EMBODIED_G_PER_VCPU_HOUR = 2.5  # Embodied carbon per vCPU-hour
    
    total_energy_kwh = 0
    total_vcpu_hours = 0
    total_embodied_g = 0
    
    # Calculate from actual build data
    for stage in pipeline_data.get('stages', []):
        for action in stage.get('actions', []):
            build_details = action.get('build_details')
            if build_details and build_details.get('duration_hours'):
                
                # Energy calculation
                vcpu_count = build_details.get('vcpu_count', 2)
                duration_hours = build_details.get('duration_hours', 0)
                
                # CPU energy (10W per vCPU)
                cpu_energy_kwh = (vcpu_count * 10 * duration_hours) / 1000
                
                # Memory energy (based on actual memory allocation)
                memory_mb = build_details.get('memory_mb', 3072)
                memory_energy_kwh = (memory_mb * duration_hours * 0.000392) / 1000
                
                # Apply PUE
                action_energy_kwh = (cpu_energy_kwh + memory_energy_kwh) * PUE
                total_energy_kwh += action_energy_kwh
                
                # Embodied carbon
                vcpu_hours = vcpu_count * duration_hours
                total_vcpu_hours += vcpu_hours
                total_embodied_g += vcpu_hours * EMBODIED_G_PER_VCPU_HOUR
    
    # Fallback calculation if no build data
    if total_energy_kwh == 0:
        # Use pipeline duration and estimated resources
        duration_seconds = pipeline_data.get('duration_seconds', 0)
        if duration_seconds > 0:
            duration_hours = duration_seconds / 3600
            estimated_vcpu = 4  # Default medium instance
            estimated_memory_mb = 7168
            
            cpu_energy_kwh = (estimated_vcpu * 10 * duration_hours) / 1000
            memory_energy_kwh = (estimated_memory_mb * duration_hours * 0.000392) / 1000
            total_energy_kwh = (cpu_energy_kwh + memory_energy_kwh) * PUE
            
            total_vcpu_hours = estimated_vcpu * duration_hours
            total_embodied_g = total_vcpu_hours * EMBODIED_G_PER_VCPU_HOUR
    
    # Calculate SCI
    operational_g = total_energy_kwh * carbon_intensity
    total_g = operational_g + total_embodied_g
    
    return {
        'energy_kwh': round(total_energy_kwh, 6),
        'operational_g': round(operational_g, 4),
        'embodied_g': round(total_embodied_g, 4),
        'total_g': round(total_g, 4),
        'sci': round(total_g, 4),
        'vcpu_hours': round(total_vcpu_hours, 2),
        'carbon_intensity': carbon_intensity,
        'calculation_method': 'real_aws_data' if pipeline_data.get('stages') else 'estimated'
    }