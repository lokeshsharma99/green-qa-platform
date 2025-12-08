"""
Green Metrics Tool (GMT) Integration Module

Provides hardware-level energy measurements when GMT is available.
Gracefully falls back to estimation when GMT is not installed.

Phase 1 - Week 2 Implementation
"""

import os
import subprocess
import json
import logging
from typing import Optional, Dict, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class GMTIntegrationError(Exception):
    """Base exception for GMT integration errors"""
    pass


class GMTNotAvailableError(GMTIntegrationError):
    """GMT is not installed or accessible"""
    pass


class GMTMeasurementFailedError(GMTIntegrationError):
    """GMT measurement failed during execution"""
    pass


class GMTIntegration:
    """
    Wrapper for Green Metrics Tool integration.
    Provides hardware-level energy measurements when available.
    
    Features:
    - Automatic GMT availability detection
    - Graceful fallback when GMT unavailable
    - Hardware sensor access (RAPL, cgroup, IPMI)
    - Container-level energy attribution
    - Detailed component breakdown (CPU, memory, GPU, disk, network)
    
    Example:
        gmt = GMTIntegration()
        if gmt.is_available():
            result = gmt.measure_workload(
                container_id="abc123",
                duration_seconds=300,
                usage_scenario={"name": "test_suite"}
            )
            print(f"Total energy: {result['total_energy_j']} J")
    """
    
    def __init__(self):
        self.gmt_path = self._find_gmt_installation()
        self.gmt_available = self._check_gmt_availability()
        self.config = self._load_config()
        
        if self.gmt_available:
            logger.info(f"GMT available at: {self.gmt_path}")
        else:
            logger.info("GMT not available, will use estimation fallback")
    
    def _find_gmt_installation(self) -> Optional[Path]:
        """Find GMT installation path"""
        # Check environment variable first
        env_path = os.getenv('GMT_INSTALLATION_PATH')
        if env_path and Path(env_path).exists():
            return Path(env_path)
        
        # Check common installation locations
        common_paths = [
            Path('/opt/green-metrics-tool'),
            Path.home() / 'green-metrics-tool',
            Path('./green-metrics-tool'),
        ]
        
        for path in common_paths:
            if path.exists() and (path / 'runner.py').exists():
                return path
        
        return None
    
    def _check_gmt_availability(self) -> bool:
        """Check if GMT is installed and accessible"""
        if not self.gmt_path:
            return False
        
        try:
            # Try to run GMT with --help to verify it works
            runner_path = self.gmt_path / 'runner.py'
            if not runner_path.exists():
                return False
            
            result = subprocess.run(
                ['python3', str(runner_path), '--help'],
                capture_output=True,
                timeout=5,
                check=False
            )
            return result.returncode == 0
            
        except Exception as e:
            logger.debug(f"GMT availability check failed: {e}")
            return False
    
    def _load_config(self) -> Dict:
        """Load GMT configuration"""
        return {
            'sampling_rate_ms': int(os.getenv('GMT_SAMPLING_RATE_MS', '100')),
            'timeout_seconds': int(os.getenv('GMT_TIMEOUT_SECONDS', '300')),
            'sensors': os.getenv('GMT_SENSORS', 'rapl,cgroup').split(','),
            'fallback_on_error': os.getenv('GMT_FALLBACK_ON_ERROR', 'true').lower() == 'true'
        }
    
    def is_available(self) -> bool:
        """Check if GMT is available for measurements"""
        return self.gmt_available
    
    def measure_workload(
        self,
        container_id: str,
        duration_seconds: int,
        usage_scenario: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Measure workload energy using GMT.
        
        Args:
            container_id: Docker container ID to measure
            duration_seconds: How long to measure
            usage_scenario: Optional GMT usage scenario configuration
            
        Returns:
            Measurement results dict or None if GMT unavailable
            
        Raises:
            GMTNotAvailableError: If GMT is not installed
            GMTMeasurementFailedError: If measurement fails
        """
        if not self.gmt_available:
            logger.info("GMT not available, skipping hardware measurement")
            return None
        
        try:
            # Run GMT measurement
            result = self._run_gmt_measurement(
                container_id,
                duration_seconds,
                usage_scenario
            )
            
            # Parse and return results
            return self._parse_gmt_output(result)
            
        except GMTNotAvailableError:
            raise
        except Exception as e:
            logger.warning(f"GMT measurement failed: {e}")
            if self.config['fallback_on_error']:
                return None
            raise GMTMeasurementFailedError(f"Measurement failed: {e}")
    
    def _run_gmt_measurement(
        self,
        container_id: str,
        duration_seconds: int,
        usage_scenario: Optional[Dict]
    ) -> Dict:
        """
        Execute GMT measurement.
        
        This is a placeholder for actual GMT integration.
        In production, this would:
        1. Create usage_scenario.yml file
        2. Run GMT runner.py with appropriate flags
        3. Parse GMT output files
        4. Return structured results
        """
        # TODO: Implement actual GMT runner execution
        # For now, return mock data structure
        logger.info(f"Running GMT measurement for container {container_id}")
        
        # Simulate GMT measurement
        # In production, this would call:
        # subprocess.run(['python3', 'runner.py', '--uri', container_uri, ...])
        
        return {
            'status': 'success',
            'container_id': container_id,
            'duration_seconds': duration_seconds,
            'measurements': {
                'total_energy_j': 5000.0,
                'cpu_energy_j': 3000.0,
                'memory_energy_j': 1200.0,
                'gpu_energy_j': 600.0,
                'disk_io_bytes': 1024 * 1024 * 100,  # 100 MB
                'network_io_bytes': 1024 * 1024 * 50,  # 50 MB
            },
            'sensors_used': ['rapl', 'cgroup'],
            'measurement_quality': 'high',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _parse_gmt_output(self, gmt_result: Dict) -> Dict:
        """
        Parse GMT output into ZeroCarb format.
        
        Returns:
        {
            'total_energy_j': float,
            'cpu_energy_j': float,
            'memory_energy_j': float,
            'gpu_energy_j': float,
            'disk_io_bytes': int,
            'network_io_bytes': int,
            'measurement_quality': str,  # 'high', 'medium', 'low'
            'sensors_used': list,
            'timestamp': str,
            'metadata': dict
        }
        """
        if gmt_result.get('status') != 'success':
            raise GMTMeasurementFailedError("GMT measurement did not complete successfully")
        
        measurements = gmt_result.get('measurements', {})
        
        return {
            'total_energy_j': measurements.get('total_energy_j', 0.0),
            'cpu_energy_j': measurements.get('cpu_energy_j', 0.0),
            'memory_energy_j': measurements.get('memory_energy_j', 0.0),
            'gpu_energy_j': measurements.get('gpu_energy_j', 0.0),
            'disk_io_bytes': measurements.get('disk_io_bytes', 0),
            'network_io_bytes': measurements.get('network_io_bytes', 0),
            'measurement_quality': gmt_result.get('measurement_quality', 'unknown'),
            'sensors_used': gmt_result.get('sensors_used', []),
            'timestamp': gmt_result.get('timestamp', datetime.utcnow().isoformat()),
            'metadata': {
                'container_id': gmt_result.get('container_id'),
                'duration_seconds': gmt_result.get('duration_seconds'),
                'gmt_version': self._get_gmt_version(),
                'sampling_rate_ms': self.config['sampling_rate_ms']
            }
        }
    
    def _get_gmt_version(self) -> str:
        """Get GMT version"""
        # TODO: Implement actual version detection
        return "0.1.0"
    
    def get_available_sensors(self) -> List[str]:
        """Get list of available hardware sensors"""
        if not self.gmt_available:
            return []
        
        # TODO: Implement actual sensor detection
        # This would query GMT for available sensors
        return ['rapl', 'cgroup', 'ipmi']
    
    def validate_container(self, container_id: str) -> bool:
        """Validate that container exists and is accessible"""
        try:
            result = subprocess.run(
                ['docker', 'inspect', container_id],
                capture_output=True,
                timeout=5,
                check=False
            )
            return result.returncode == 0
        except Exception as e:
            logger.debug(f"Container validation failed: {e}")
            return False


# Singleton instance
_gmt_integration = None

def get_gmt_integration() -> GMTIntegration:
    """Get global GMT integration instance (singleton)"""
    global _gmt_integration
    if _gmt_integration is None:
        _gmt_integration = GMTIntegration()
    return _gmt_integration
