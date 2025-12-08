"""
Unified Carbon Calculator

Combines:
- GMT hardware measurements
- TEADS estimations
- Calibration engine
- Energy profiling
- Regression detection
- Lifecycle analysis
- A/B testing

Provides the most accurate carbon calculations by using all available data sources.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from gmt_integration import get_gmt_integration, GMTNotAvailableError
from calibration_engine import get_calibration_engine
from teads_enhanced_calculator import TeadsEnhancedCalculator
from energy_profiler import get_energy_profiler, EnergyProfile
from energy_regression_detector import get_regression_detector
from lifecycle_analyzer import get_lifecycle_analyzer, LifecyclePhase
from ab_testing import get_ab_test, create_ab_test
from feature_flags import get_feature_flags, Feature

logger = logging.getLogger(__name__)


class UnifiedCarbonCalculator:
    """
    Unified calculator that uses both estimation and measurement.
    Provides best available carbon data with confidence scores.
    
    Priority:
    1. GMT measurement (if available and enabled)
    2. Calibrated TEADS estimate (if calibration data exists)
    3. Raw TEADS estimate (fallback)
    
    Features:
    - Hardware measurement integration
    - Estimation with calibration
    - Energy profiling
    - Regression detection
    - Lifecycle tracking
    - A/B testing support
    
    Example:
        calculator = UnifiedCarbonCalculator()
        
        result = calculator.calculate_carbon(
            workload={
                'container_id': 'abc123',
                'duration_seconds': 300,
                'cpu_percent': 75,
                'memory_mb': 2048
            },
            region='us-east-1',
            carbon_intensity_g_per_kwh=250
        )
        
        print(f"Carbon: {result['carbon_g']} g")
        print(f"Method: {result['method']}")
        print(f"Confidence: {result['confidence']}")
    """
    
    def __init__(self):
        self.gmt = get_gmt_integration()
        self.teads = TeadsEnhancedCalculator()
        self.calibration = get_calibration_engine()
        self.profiler = get_energy_profiler()
        self.regression_detector = get_regression_detector()
        self.feature_flags = get_feature_flags()
    
    def calculate_carbon(
        self,
        workload: Dict,
        region: str,
        carbon_intensity_g_per_kwh: float,
        enable_profiling: bool = False,
        enable_regression_check: bool = False,
        commit_sha: Optional[str] = None,
        branch: Optional[str] = None
    ) -> Dict:
        """
        Calculate carbon using best available method.
        
        Args:
            workload: Workload configuration
            region: AWS region
            carbon_intensity_g_per_kwh: Grid carbon intensity
            enable_profiling: Enable energy profiling
            enable_regression_check: Check for energy regression
            commit_sha: Git commit SHA (for regression tracking)
            branch: Git branch (for regression tracking)
        
        Returns:
        {
            'carbon_g': float,
            'energy_j': float,
            'method': str,  # 'measured', 'calibrated', 'estimated'
            'confidence': float,  # 0-1
            'breakdown': dict,
            'metadata': dict,
            'profiling': dict (optional),
            'regression': dict (optional)
        }
        """
        result = {
            'carbon_g': 0,
            'energy_j': 0,
            'method': 'unknown',
            'confidence': 0.0,
            'breakdown': {},
            'metadata': {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Try GMT measurement first
        if self.feature_flags.is_enabled(Feature.GMT_INTEGRATION):
            gmt_result = self._try_gmt_measurement(workload)
            if gmt_result:
                result = self._format_measured_result(
                    gmt_result,
                    carbon_intensity_g_per_kwh,
                    region
                )
                
                # Store calibration data
                if self.feature_flags.is_enabled(Feature.GMT_CALIBRATION):
                    self._store_calibration(workload, gmt_result)
                
                # Enable profiling if requested
                if enable_profiling:
                    result['profiling'] = self._create_energy_profile(
                        workload,
                        gmt_result
                    )
                
                # Check for regression
                if enable_regression_check and commit_sha and branch:
                    result['regression'] = self._check_regression(
                        commit_sha,
                        branch,
                        result['energy_j'],
                        workload.get('workload_type', 'unknown')
                    )
                
                return result
        
        # Fall back to TEADS estimation
        teads_result = self._calculate_teads_estimate(workload, region)
        
        # Try calibration
        if self.feature_flags.is_enabled(Feature.GMT_CALIBRATION):
            calibrated = self._try_calibration(teads_result, workload)
            if calibrated and calibrated['confidence_score'] > 0.7:
                result = self._format_calibrated_result(
                    calibrated,
                    carbon_intensity_g_per_kwh,
                    region
                )
                
                if enable_regression_check and commit_sha and branch:
                    result['regression'] = self._check_regression(
                        commit_sha,
                        branch,
                        result['energy_j'],
                        workload.get('workload_type', 'unknown')
                    )
                
                return result
        
        # Return raw estimate
        result = self._format_estimated_result(
            teads_result,
            carbon_intensity_g_per_kwh,
            region
        )
        
        if enable_regression_check and commit_sha and branch:
            result['regression'] = self._check_regression(
                commit_sha,
                branch,
                result['energy_j'],
                workload.get('workload_type', 'unknown')
            )
        
        return result
    
    def _try_gmt_measurement(self, workload: Dict) -> Optional[Dict]:
        """Try to get GMT measurement"""
        if not self.gmt.is_available():
            return None
        
        try:
            return self.gmt.measure_workload(
                container_id=workload.get('container_id', ''),
                duration_seconds=workload.get('duration_seconds', 0),
                usage_scenario=workload.get('usage_scenario', {})
            )
        except Exception as e:
            logger.warning(f"GMT measurement failed: {e}")
            return None
    
    def _calculate_teads_estimate(self, workload: Dict, region: str) -> Dict:
        """Calculate TEADS estimate"""
        return self.teads.calculate(
            cpu_percent=workload.get('cpu_percent', 50),
            memory_mb=workload.get('memory_mb', 1024),
            duration_seconds=workload.get('duration_seconds', 300),
            region=region
        )
    
    def _try_calibration(self, teads_result: Dict, workload: Dict) -> Optional[Dict]:
        """Try to apply calibration"""
        workload_profile = {
            'cpu_utilization_percent': workload.get('cpu_percent', 50),
            'memory_usage_mb': workload.get('memory_mb', 1024),
            'duration_seconds': workload.get('duration_seconds', 300),
            'workload_type': workload.get('workload_type', 'unknown')
        }
        
        return self.calibration.get_calibrated_estimate(
            raw_estimate=teads_result.get('energy_j', 0),
            workload_profile=workload_profile
        )
    
    def _store_calibration(self, workload: Dict, gmt_result: Dict):
        """Store calibration data from GMT measurement"""
        teads_result = self._calculate_teads_estimate(
            workload,
            workload.get('region', 'us-east-1')
        )
        
        workload_profile = {
            'cpu_utilization_percent': workload.get('cpu_percent', 50),
            'memory_usage_mb': workload.get('memory_mb', 1024),
            'duration_seconds': workload.get('duration_seconds', 300),
            'workload_type': workload.get('workload_type', 'unknown')
        }
        
        self.calibration.calibrate_estimate(
            estimated_energy_j=teads_result.get('energy_j', 0),
            measured_energy_j=gmt_result.get('total_energy_j', 0),
            workload_profile=workload_profile
        )
    
    def _create_energy_profile(
        self,
        workload: Dict,
        gmt_result: Dict
    ) -> Dict:
        """Create energy profile from GMT measurement"""
        workload_id = workload.get('workload_id', 'unknown')
        profile = self.profiler.start_profile(
            workload_id,
            workload.get('name', 'Workload')
        )
        
        # Add phase data
        self.profiler.add_phase(profile, {
            'name': 'execution',
            'energy_j': gmt_result.get('total_energy_j', 0),
            'cpu_j': gmt_result.get('cpu_energy_j', 0),
            'memory_j': gmt_result.get('memory_energy_j', 0),
            'gpu_j': gmt_result.get('gpu_energy_j', 0),
            'duration_s': workload.get('duration_seconds', 0)
        })
        
        # Generate report
        return self.profiler.generate_report(profile)
    
    def _check_regression(
        self,
        commit_sha: str,
        branch: str,
        energy_j: float,
        workload_type: str
    ) -> Dict:
        """Check for energy regression"""
        return self.regression_detector.check_regression(
            commit_sha=commit_sha,
            branch=branch,
            energy_j=energy_j,
            workload_type=workload_type
        )
    
    def _format_measured_result(
        self,
        gmt_result: Dict,
        carbon_intensity: float,
        region: str
    ) -> Dict:
        """Format GMT measurement result"""
        energy_j = gmt_result.get('total_energy_j', 0)
        energy_kwh = energy_j / 3_600_000
        carbon_g = energy_kwh * carbon_intensity
        
        # Calculate component-level carbon
        breakdown_carbon = {
            'cpu_g': (gmt_result.get('cpu_energy_j', 0) / 3_600_000) * carbon_intensity,
            'memory_g': (gmt_result.get('memory_energy_j', 0) / 3_600_000) * carbon_intensity,
            'gpu_g': (gmt_result.get('gpu_energy_j', 0) / 3_600_000) * carbon_intensity,
        }
        
        return {
            'carbon_g': carbon_g,
            'energy_j': energy_j,
            'energy_kwh': energy_kwh,
            'method': 'measured',
            'confidence': 0.95,  # High confidence for hardware measurements
            'breakdown': {
                'cpu_j': gmt_result.get('cpu_energy_j', 0),
                'memory_j': gmt_result.get('memory_energy_j', 0),
                'gpu_j': gmt_result.get('gpu_energy_j', 0),
                'disk_io_bytes': gmt_result.get('disk_io_bytes', 0),
                'network_io_bytes': gmt_result.get('network_io_bytes', 0)
            },
            'breakdown_carbon': breakdown_carbon,
            'metadata': {
                'region': region,
                'carbon_intensity_g_per_kwh': carbon_intensity,
                'measurement_quality': gmt_result.get('measurement_quality', 'unknown'),
                'sensors_used': gmt_result.get('sensors_used', []),
                'timestamp': gmt_result.get('timestamp')
            }
        }
    
    def _format_calibrated_result(
        self,
        calibrated: Dict,
        carbon_intensity: float,
        region: str
    ) -> Dict:
        """Format calibrated estimate result"""
        energy_j = calibrated.get('calibrated_estimate_j', 0)
        energy_kwh = energy_j / 3_600_000
        carbon_g = energy_kwh * carbon_intensity
        
        return {
            'carbon_g': carbon_g,
            'energy_j': energy_j,
            'energy_kwh': energy_kwh,
            'method': 'calibrated',
            'confidence': calibrated.get('confidence_score', 0.5),
            'breakdown': {},
            'metadata': {
                'region': region,
                'carbon_intensity_g_per_kwh': carbon_intensity,
                'calibration_factor': calibrated.get('calibration_factor', 1.0),
                'sample_size': calibrated.get('sample_size', 0),
                'raw_estimate_j': calibrated.get('raw_estimate_j', 0)
            }
        }
    
    def _format_estimated_result(
        self,
        teads_result: Dict,
        carbon_intensity: float,
        region: str
    ) -> Dict:
        """Format TEADS estimate result"""
        energy_j = teads_result.get('energy_j', 0)
        energy_kwh = energy_j / 3_600_000
        carbon_g = energy_kwh * carbon_intensity
        
        return {
            'carbon_g': carbon_g,
            'energy_j': energy_j,
            'energy_kwh': energy_kwh,
            'method': 'estimated',
            'confidence': 0.6,  # Medium confidence for estimates
            'breakdown': {},
            'metadata': {
                'region': region,
                'carbon_intensity_g_per_kwh': carbon_intensity,
                'estimation_method': 'TEADS'
            }
        }


# Singleton instance
_unified_calculator = None

def get_unified_calculator() -> UnifiedCarbonCalculator:
    """Get global unified calculator instance (singleton)"""
    global _unified_calculator
    if _unified_calculator is None:
        _unified_calculator = UnifiedCarbonCalculator()
    return _unified_calculator
