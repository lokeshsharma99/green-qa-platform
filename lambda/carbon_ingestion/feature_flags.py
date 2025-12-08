"""
Feature Flags for Safe Rollout of Research-Backed Enhancements

This module allows gradual rollout of new features without breaking existing functionality.
All new features are OFF by default and can be enabled per-region or globally.
"""

import os
from typing import Dict, Optional
from enum import Enum


class Feature(Enum):
    """Available features that can be toggled"""
    EXCESS_POWER_METRIC = "excess_power_metric"
    CARBONX_FORECASTING = "carbonx_forecasting"
    MAIZX_RANKING = "maizx_ranking"
    SLACK_SCHEDULING = "slack_scheduling"
    WORKFLOW_DAG = "workflow_dag"
    MULTI_OBJECTIVE = "multi_objective"
    CONTAINER_TRACKING = "container_tracking"
    # GMT Integration Features (Phase 1)
    GMT_INTEGRATION = "gmt_integration"
    GMT_CALIBRATION = "gmt_calibration"
    GMT_DASHBOARD = "gmt_dashboard"


class FeatureFlags:
    """
    Manage feature flags for safe rollout.
    
    Features can be enabled:
    1. Globally via environment variables
    2. Per-region via configuration
    3. For specific users (beta testing)
    
    Example:
        flags = FeatureFlags()
        if flags.is_enabled(Feature.EXCESS_POWER_METRIC):
            # Use new Excess Power calculator
        else:
            # Use existing carbon intensity logic
    """
    
    def __init__(self):
        # Load feature flags from environment or config
        self._flags = self._load_flags()
        self._beta_users = self._load_beta_users()
        self._beta_regions = self._load_beta_regions()
    
    def _load_flags(self) -> Dict[str, bool]:
        """Load feature flags from environment variables"""
        return {
            Feature.EXCESS_POWER_METRIC.value: 
                os.getenv('ENABLE_EXCESS_POWER', 'false').lower() == 'true',
            Feature.CARBONX_FORECASTING.value: 
                os.getenv('ENABLE_CARBONX_FORECAST', 'false').lower() == 'true',
            Feature.MAIZX_RANKING.value: 
                os.getenv('ENABLE_MAIZX_RANKING', 'false').lower() == 'true',
            Feature.SLACK_SCHEDULING.value: 
                os.getenv('ENABLE_SLACK_SCHEDULING', 'false').lower() == 'true',
            Feature.WORKFLOW_DAG.value: 
                os.getenv('ENABLE_WORKFLOW_DAG', 'false').lower() == 'true',
            Feature.MULTI_OBJECTIVE.value: 
                os.getenv('ENABLE_MULTI_OBJECTIVE', 'false').lower() == 'true',
            Feature.CONTAINER_TRACKING.value: 
                os.getenv('ENABLE_CONTAINER_TRACKING', 'false').lower() == 'true',
            # GMT Integration (OFF by default for safe rollout)
            Feature.GMT_INTEGRATION.value: 
                os.getenv('ENABLE_GMT_INTEGRATION', 'false').lower() == 'true',
            Feature.GMT_CALIBRATION.value: 
                os.getenv('ENABLE_GMT_CALIBRATION', 'false').lower() == 'true',
            Feature.GMT_DASHBOARD.value: 
                os.getenv('ENABLE_GMT_DASHBOARD', 'false').lower() == 'true',
        }
    
    def _load_beta_users(self) -> set:
        """Load list of beta users who get early access to features"""
        beta_users_str = os.getenv('BETA_USERS', '')
        return set(beta_users_str.split(',')) if beta_users_str else set()
    
    def _load_beta_regions(self) -> set:
        """Load list of beta regions for gradual rollout"""
        beta_regions_str = os.getenv('BETA_REGIONS', '')
        return set(beta_regions_str.split(',')) if beta_regions_str else set()
    
    def is_enabled(
        self, 
        feature: Feature, 
        region: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Check if a feature is enabled.
        
        Args:
            feature: Feature to check
            region: Optional region for region-specific rollout
            user_id: Optional user ID for beta testing
            
        Returns:
            True if feature is enabled, False otherwise
        """
        
        # Check if globally enabled
        if self._flags.get(feature.value, False):
            return True
        
        # Check if user is beta tester
        if user_id and user_id in self._beta_users:
            return True
        
        # Check if region is in beta
        if region and region in self._beta_regions:
            return True
        
        return False
    
    def enable_feature(self, feature: Feature):
        """Enable a feature globally (for testing)"""
        self._flags[feature.value] = True
    
    def disable_feature(self, feature: Feature):
        """Disable a feature globally"""
        self._flags[feature.value] = False
    
    def get_enabled_features(self) -> list:
        """Get list of currently enabled features"""
        return [
            feature for feature, enabled in self._flags.items() 
            if enabled
        ]


# Global instance
_feature_flags = None

def get_feature_flags() -> FeatureFlags:
    """Get global feature flags instance (singleton)"""
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = FeatureFlags()
    return _feature_flags
