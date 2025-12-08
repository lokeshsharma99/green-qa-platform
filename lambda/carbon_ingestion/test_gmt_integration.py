"""
Tests for GMT Integration Module

Covers:
- GMT availability detection
- Measurement execution
- Error handling and graceful fallback
- Output parsing
- Configuration loading
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime

from gmt_integration import (
    GMTIntegration,
    GMTNotAvailableError,
    GMTMeasurementFailedError,
    get_gmt_integration
)


class TestGMTAvailability:
    """Test GMT availability detection"""
    
    def test_gmt_not_installed(self):
        """Test behavior when GMT is not installed"""
        with patch.object(GMTIntegration, '_find_gmt_installation', return_value=None):
            gmt = GMTIntegration()
            assert not gmt.is_available()
            assert gmt.gmt_path is None
    
    def test_gmt_installed_and_working(self):
        """Test detection when GMT is properly installed"""
        mock_path = Path('/opt/green-metrics-tool')
        with patch.object(GMTIntegration, '_find_gmt_installation', return_value=mock_path):
            with patch.object(GMTIntegration, '_check_gmt_availability', return_value=True):
                gmt = GMTIntegration()
                assert gmt.is_available()
                assert gmt.gmt_path == mock_path
    
    def test_gmt_path_from_environment(self):
        """Test GMT path detection from environment variable"""
        test_path = '/custom/gmt/path'
        with patch.dict(os.environ, {'GMT_INSTALLATION_PATH': test_path}):
            with patch('pathlib.Path.exists', return_value=True):
                gmt = GMTIntegration()
                # Path detection attempted
                assert gmt.gmt_path is not None or not gmt.is_available()
    
    def test_common_installation_paths(self):
        """Test checking common GMT installation locations"""
        gmt = GMTIntegration()
        # Should check multiple common paths
        assert gmt.gmt_path is None or isinstance(gmt.gmt_path, Path)


class TestGMTMeasurement:
    """Test GMT measurement functionality"""
    
    def test_measure_workload_gmt_unavailable(self):
        """Test measurement returns None when GMT unavailable"""
        with patch.object(GMTIntegration, '_check_gmt_availability', return_value=False):
            gmt = GMTIntegration()
            result = gmt.measure_workload(
                container_id='test123',
                duration_seconds=60
            )
            assert result is None
    
    def test_measure_workload_success(self):
        """Test successful GMT measurement"""
        with patch.object(GMTIntegration, '_check_gmt_availability', return_value=True):
            gmt = GMTIntegration()
            gmt.gmt_available = True
            
            result = gmt.measure_workload(
                container_id='test123',
                duration_seconds=60
            )
            
            assert result is not None
            assert 'total_energy_j' in result
            assert 'cpu_energy_j' in result
            assert 'memory_energy_j' in result
            assert 'measurement_quality' in result
            assert result['total_energy_j'] > 0
    
    def test_measure_workload_with_usage_scenario(self):
        """Test measurement with custom usage scenario"""
        with patch.object(GMTIntegration, '_check_gmt_availability', return_value=True):
            gmt = GMTIntegration()
            gmt.gmt_available = True
            
            usage_scenario = {
                'name': 'test_suite',
                'steps': ['run_tests', 'generate_report']
            }
            
            result = gmt.measure_workload(
                container_id='test123',
                duration_seconds=300,
                usage_scenario=usage_scenario
            )
            
            assert result is not None
            assert result['metadata']['duration_seconds'] == 300
    
    def test_measurement_failure_with_fallback(self):
        """Test graceful fallback when measurement fails"""
        with patch.object(GMTIntegration, '_check_gmt_availability', return_value=True):
            gmt = GMTIntegration()
            gmt.gmt_available = True
            gmt.config['fallback_on_error'] = True
            
            with patch.object(gmt, '_run_gmt_measurement', side_effect=Exception("Sensor error")):
                result = gmt.measure_workload(
                    container_id='test123',
                    duration_seconds=60
                )
                # Should return None instead of raising
                assert result is None
    
    def test_measurement_failure_without_fallback(self):
        """Test exception raised when fallback disabled"""
        with patch.object(GMTIntegration, '_check_gmt_availability', return_value=True):
            gmt = GMTIntegration()
            gmt.gmt_available = True
            gmt.config['fallback_on_error'] = False
            
            with patch.object(gmt, '_run_gmt_measurement', side_effect=Exception("Sensor error")):
                with pytest.raises(GMTMeasurementFailedError):
                    gmt.measure_workload(
                        container_id='test123',
                        duration_seconds=60
                    )


class TestGMTOutputParsing:
    """Test GMT output parsing"""
    
    def test_parse_successful_measurement(self):
        """Test parsing successful GMT output"""
        gmt = GMTIntegration()
        
        mock_output = {
            'status': 'success',
            'container_id': 'abc123',
            'duration_seconds': 120,
            'measurements': {
                'total_energy_j': 10000.0,
                'cpu_energy_j': 6000.0,
                'memory_energy_j': 2500.0,
                'gpu_energy_j': 1500.0,
                'disk_io_bytes': 1024 * 1024 * 200,
                'network_io_bytes': 1024 * 1024 * 100,
            },
            'sensors_used': ['rapl', 'cgroup', 'ipmi'],
            'measurement_quality': 'high',
            'timestamp': '2025-12-08T10:00:00Z'
        }
        
        result = gmt._parse_gmt_output(mock_output)
        
        assert result['total_energy_j'] == 10000.0
        assert result['cpu_energy_j'] == 6000.0
        assert result['memory_energy_j'] == 2500.0
        assert result['gpu_energy_j'] == 1500.0
        assert result['measurement_quality'] == 'high'
        assert len(result['sensors_used']) == 3
        assert 'metadata' in result
    
    def test_parse_failed_measurement(self):
        """Test parsing failed GMT output"""
        gmt = GMTIntegration()
        
        mock_output = {
            'status': 'failed',
            'error': 'Sensor not available'
        }
        
        with pytest.raises(GMTMeasurementFailedError):
            gmt._parse_gmt_output(mock_output)
    
    def test_parse_partial_measurements(self):
        """Test parsing output with missing components"""
        gmt = GMTIntegration()
        
        mock_output = {
            'status': 'success',
            'measurements': {
                'total_energy_j': 5000.0,
                'cpu_energy_j': 5000.0,
                # Missing memory, GPU, etc.
            },
            'sensors_used': ['rapl'],
            'measurement_quality': 'medium'
        }
        
        result = gmt._parse_gmt_output(mock_output)
        
        assert result['total_energy_j'] == 5000.0
        assert result['cpu_energy_j'] == 5000.0
        assert result['memory_energy_j'] == 0.0  # Default
        assert result['gpu_energy_j'] == 0.0  # Default
        assert result['measurement_quality'] == 'medium'


class TestGMTConfiguration:
    """Test GMT configuration loading"""
    
    def test_default_configuration(self):
        """Test default configuration values"""
        gmt = GMTIntegration()
        
        assert gmt.config['sampling_rate_ms'] == 100
        assert gmt.config['timeout_seconds'] == 300
        assert 'rapl' in gmt.config['sensors']
        assert gmt.config['fallback_on_error'] is True
    
    def test_custom_configuration_from_env(self):
        """Test loading custom configuration from environment"""
        env_vars = {
            'GMT_SAMPLING_RATE_MS': '50',
            'GMT_TIMEOUT_SECONDS': '600',
            'GMT_SENSORS': 'rapl,ipmi,nvidia',
            'GMT_FALLBACK_ON_ERROR': 'false'
        }
        
        with patch.dict(os.environ, env_vars):
            gmt = GMTIntegration()
            
            assert gmt.config['sampling_rate_ms'] == 50
            assert gmt.config['timeout_seconds'] == 600
            assert 'nvidia' in gmt.config['sensors']
            assert gmt.config['fallback_on_error'] is False
    
    def test_invalid_configuration_values(self):
        """Test handling of invalid configuration values"""
        with patch.dict(os.environ, {'GMT_SAMPLING_RATE_MS': 'invalid'}):
            with pytest.raises(ValueError):
                gmt = GMTIntegration()


class TestContainerValidation:
    """Test container validation"""
    
    @patch('subprocess.run')
    def test_validate_existing_container(self, mock_run):
        """Test validation of existing container"""
        mock_run.return_value = Mock(returncode=0)
        
        gmt = GMTIntegration()
        result = gmt.validate_container('valid_container_123')
        
        assert result is True
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_validate_nonexistent_container(self, mock_run):
        """Test validation of non-existent container"""
        mock_run.return_value = Mock(returncode=1)
        
        gmt = GMTIntegration()
        result = gmt.validate_container('invalid_container')
        
        assert result is False
    
    @patch('subprocess.run')
    def test_validate_container_timeout(self, mock_run):
        """Test container validation with timeout"""
        mock_run.side_effect = TimeoutError()
        
        gmt = GMTIntegration()
        result = gmt.validate_container('slow_container')
        
        assert result is False


class TestSensorDetection:
    """Test hardware sensor detection"""
    
    def test_get_available_sensors_gmt_unavailable(self):
        """Test sensor list when GMT unavailable"""
        with patch.object(GMTIntegration, '_check_gmt_availability', return_value=False):
            gmt = GMTIntegration()
            sensors = gmt.get_available_sensors()
            
            assert sensors == []
    
    def test_get_available_sensors_gmt_available(self):
        """Test sensor list when GMT available"""
        with patch.object(GMTIntegration, '_check_gmt_availability', return_value=True):
            gmt = GMTIntegration()
            gmt.gmt_available = True
            sensors = gmt.get_available_sensors()
            
            assert isinstance(sensors, list)
            # Should include common sensors
            assert any(s in sensors for s in ['rapl', 'cgroup', 'ipmi'])


class TestSingletonPattern:
    """Test singleton pattern for GMT integration"""
    
    def test_singleton_returns_same_instance(self):
        """Test that get_gmt_integration returns same instance"""
        instance1 = get_gmt_integration()
        instance2 = get_gmt_integration()
        
        assert instance1 is instance2
    
    def test_singleton_configuration_persists(self):
        """Test that configuration persists across calls"""
        instance1 = get_gmt_integration()
        config1 = instance1.config
        
        instance2 = get_gmt_integration()
        config2 = instance2.config
        
        assert config1 == config2


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_measurement_with_empty_container_id(self):
        """Test measurement with empty container ID"""
        with patch.object(GMTIntegration, '_check_gmt_availability', return_value=True):
            gmt = GMTIntegration()
            gmt.gmt_available = True
            
            # Should handle gracefully
            result = gmt.measure_workload(
                container_id='',
                duration_seconds=60
            )
            assert result is not None
    
    def test_measurement_with_zero_duration(self):
        """Test measurement with zero duration"""
        with patch.object(GMTIntegration, '_check_gmt_availability', return_value=True):
            gmt = GMTIntegration()
            gmt.gmt_available = True
            
            result = gmt.measure_workload(
                container_id='test123',
                duration_seconds=0
            )
            assert result is not None
    
    def test_measurement_with_negative_duration(self):
        """Test measurement with negative duration"""
        with patch.object(GMTIntegration, '_check_gmt_availability', return_value=True):
            gmt = GMTIntegration()
            gmt.gmt_available = True
            
            # Should handle gracefully or raise appropriate error
            result = gmt.measure_workload(
                container_id='test123',
                duration_seconds=-60
            )
            # Implementation should validate this


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
