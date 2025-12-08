"""
Tests for Calibration Engine

Covers:
- Calibration factor calculation
- Workload similarity matching
- Confidence scoring
- Outlier filtering
- Statistical methods
"""

import pytest
from datetime import datetime, timedelta
from calibration_engine import (
    CalibrationEngine,
    InMemoryCalibrationStorage,
    get_calibration_engine
)


class TestCalibrationBasics:
    """Test basic calibration functionality"""
    
    def test_calibrate_estimate_basic(self):
        """Test basic calibration factor calculation"""
        engine = CalibrationEngine()
        
        factor = engine.calibrate_estimate(
            estimated_energy_j=5000,
            measured_energy_j=4800,
            workload_profile={'workload_type': 'test'}
        )
        
        assert factor == pytest.approx(0.96, rel=0.01)
    
    def test_calibrate_estimate_perfect_match(self):
        """Test calibration when estimate matches measurement"""
        engine = CalibrationEngine()
        
        factor = engine.calibrate_estimate(
            estimated_energy_j=5000,
            measured_energy_j=5000,
            workload_profile={'workload_type': 'test'}
        )
        
        assert factor == 1.0
    
    def test_calibrate_estimate_overestimation(self):
        """Test calibration when estimate is too high"""
        engine = CalibrationEngine()
        
        factor = engine.calibrate_estimate(
            estimated_energy_j=6000,
            measured_energy_j=5000,
            workload_profile={'workload_type': 'test'}
        )
        
        assert factor == pytest.approx(0.833, rel=0.01)
    
    def test_calibrate_estimate_underestimation(self):
        """Test calibration when estimate is too low"""
        engine = CalibrationEngine()
        
        factor = engine.calibrate_estimate(
            estimated_energy_j=4000,
            measured_energy_j=5000,
            workload_profile={'workload_type': 'test'}
        )
        
        assert factor == 1.25
    
    def test_calibrate_invalid_estimate(self):
        """Test handling of invalid estimate (zero or negative)"""
        engine = CalibrationEngine()
        
        factor = engine.calibrate_estimate(
            estimated_energy_j=0,
            measured_energy_j=5000,
            workload_profile={'workload_type': 'test'}
        )
        
        assert factor == 1.0  # Should return default


class TestCalibratedEstimates:
    """Test getting calibrated estimates"""
    
    def test_get_calibrated_estimate_no_data(self):
        """Test calibration with no historical data"""
        engine = CalibrationEngine()
        
        result = engine.get_calibrated_estimate(
            raw_estimate=5000,
            workload_profile={'workload_type': 'test'}
        )
        
        assert result['raw_estimate_j'] == 5000
        assert result['calibrated_estimate_j'] == 5000
        assert result['calibration_factor'] == 1.0
        assert result['confidence_score'] == 0.0
        assert result['method'] == 'raw'
    
    def test_get_calibrated_estimate_insufficient_samples(self):
        """Test calibration with too few samples"""
        engine = CalibrationEngine()
        engine.config['min_samples_for_calibration'] = 10
        
        # Add only 5 samples
        for i in range(5):
            engine.calibrate_estimate(
                estimated_energy_j=5000,
                measured_energy_j=4800,
                workload_profile={'workload_type': 'test', 'cpu_utilization_percent': 75}
            )
        
        result = engine.get_calibrated_estimate(
            raw_estimate=5000,
            workload_profile={'workload_type': 'test', 'cpu_utilization_percent': 75}
        )
        
        assert result['method'] == 'raw'
        assert result['sample_size'] < 10
    
    def test_get_calibrated_estimate_sufficient_samples(self):
        """Test calibration with enough samples"""
        engine = CalibrationEngine()
        engine.config['min_samples_for_calibration'] = 10
        engine.config['confidence_threshold'] = 0.5
        
        # Add 15 similar samples
        for i in range(15):
            engine.calibrate_estimate(
                estimated_energy_j=5000,
                measured_energy_j=4800,
                workload_profile={
                    'workload_type': 'test',
                    'cpu_utilization_percent': 75,
                    'memory_usage_mb': 2048
                }
            )
        
        result = engine.get_calibrated_estimate(
            raw_estimate=5000,
            workload_profile={
                'workload_type': 'test',
                'cpu_utilization_percent': 75,
                'memory_usage_mb': 2048
            }
        )
        
        assert result['method'] == 'calibrated'
        assert result['sample_size'] >= 10
        assert result['calibrated_estimate_j'] < 5000  # Should be adjusted down
        assert result['confidence_score'] > 0.5


class TestWorkloadSimilarity:
    """Test workload similarity matching"""
    
    def test_exact_workload_match(self):
        """Test similarity for identical workloads"""
        engine = CalibrationEngine()
        
        profile1 = {
            'workload_type': 'test',
            'cpu_utilization_percent': 75,
            'memory_usage_mb': 2048,
            'duration_seconds': 300
        }
        profile2 = profile1.copy()
        
        similarity = engine._calculate_similarity(profile1, profile2)
        
        assert similarity == 1.0
    
    def test_similar_workload_match(self):
        """Test similarity for similar workloads"""
        engine = CalibrationEngine()
        
        profile1 = {
            'workload_type': 'test',
            'cpu_utilization_percent': 75,
            'memory_usage_mb': 2048,
            'duration_seconds': 300
        }
        profile2 = {
            'workload_type': 'test',
            'cpu_utilization_percent': 80,  # Slightly different
            'memory_usage_mb': 2200,
            'duration_seconds': 320
        }
        
        similarity = engine._calculate_similarity(profile1, profile2)
        
        assert 0.8 < similarity < 1.0
    
    def test_different_workload_type(self):
        """Test similarity for different workload types"""
        engine = CalibrationEngine()
        
        profile1 = {
            'workload_type': 'test',
            'cpu_utilization_percent': 75,
            'memory_usage_mb': 2048
        }
        profile2 = {
            'workload_type': 'build',
            'cpu_utilization_percent': 75,
            'memory_usage_mb': 2048
        }
        
        similarity = engine._calculate_similarity(profile1, profile2)
        
        assert similarity < 1.0  # Should be lower due to different type
    
    def test_very_different_workloads(self):
        """Test similarity for very different workloads"""
        engine = CalibrationEngine()
        
        profile1 = {
            'workload_type': 'test',
            'cpu_utilization_percent': 10,
            'memory_usage_mb': 512,
            'duration_seconds': 60
        }
        profile2 = {
            'workload_type': 'build',
            'cpu_utilization_percent': 95,
            'memory_usage_mb': 8192,
            'duration_seconds': 1800
        }
        
        similarity = engine._calculate_similarity(profile1, profile2)
        
        assert similarity < 0.5


class TestOutlierFiltering:
    """Test outlier detection and filtering"""
    
    def test_filter_no_outliers(self):
        """Test filtering when all data is consistent"""
        engine = CalibrationEngine()
        
        calibrations = [
            {'calibration_factor': 0.95},
            {'calibration_factor': 0.96},
            {'calibration_factor': 0.97},
            {'calibration_factor': 0.94},
            {'calibration_factor': 0.96},
        ]
        
        filtered = engine._filter_outliers(calibrations)
        
        assert len(filtered) == len(calibrations)
    
    def test_filter_with_outliers(self):
        """Test filtering with obvious outliers"""
        engine = CalibrationEngine()
        engine.config['outlier_threshold_std'] = 1.5  # More aggressive filtering
        
        calibrations = [
            {'calibration_factor': 0.95},
            {'calibration_factor': 0.96},
            {'calibration_factor': 0.97},
            {'calibration_factor': 2.50},  # Outlier
            {'calibration_factor': 0.94},
            {'calibration_factor': 0.10},  # Outlier
        ]
        
        filtered = engine._filter_outliers(calibrations)
        
        # With aggressive filtering, outliers should be removed
        assert len(filtered) <= len(calibrations)
        factors = [c['calibration_factor'] for c in filtered]
        # At least one outlier should be filtered
        assert 2.50 not in factors or 0.10 not in factors
    
    def test_filter_insufficient_data(self):
        """Test filtering with too few data points"""
        engine = CalibrationEngine()
        
        calibrations = [
            {'calibration_factor': 0.95},
            {'calibration_factor': 2.50},
        ]
        
        filtered = engine._filter_outliers(calibrations)
        
        # Should not filter with < 3 points
        assert len(filtered) == len(calibrations)


class TestConfidenceScoring:
    """Test confidence score calculation"""
    
    def test_confidence_no_data(self):
        """Test confidence with no calibrations"""
        engine = CalibrationEngine()
        
        confidence = engine._calculate_confidence([])
        
        assert confidence == 0.0
    
    def test_confidence_few_samples(self):
        """Test confidence with few samples"""
        engine = CalibrationEngine()
        
        calibrations = [
            {
                'calibration_factor': 0.95,
                'timestamp': datetime.utcnow().isoformat()
            },
            {
                'calibration_factor': 0.96,
                'timestamp': datetime.utcnow().isoformat()
            }
        ]
        
        confidence = engine._calculate_confidence(calibrations)
        
        # With few samples, confidence should be lower than with many samples
        assert 0.0 < confidence < 1.0
    
    def test_confidence_many_consistent_samples(self):
        """Test confidence with many consistent samples"""
        engine = CalibrationEngine()
        
        calibrations = []
        for i in range(50):
            calibrations.append({
                'calibration_factor': 0.95 + (i % 3) * 0.01,  # Very consistent
                'timestamp': datetime.utcnow().isoformat()
            })
        
        confidence = engine._calculate_confidence(calibrations)
        
        assert confidence > 0.8  # High confidence
    
    def test_confidence_old_data(self):
        """Test confidence decreases with old data"""
        engine = CalibrationEngine()
        
        # Recent calibrations
        recent_calibrations = []
        for i in range(20):
            recent_calibrations.append({
                'calibration_factor': 0.95,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        # Old calibrations
        old_calibrations = []
        old_date = datetime.utcnow() - timedelta(days=25)
        for i in range(20):
            old_calibrations.append({
                'calibration_factor': 0.95,
                'timestamp': old_date.isoformat()
            })
        
        recent_confidence = engine._calculate_confidence(recent_calibrations)
        old_confidence = engine._calculate_confidence(old_calibrations)
        
        assert recent_confidence > old_confidence


class TestCalibrationStats:
    """Test calibration statistics"""
    
    def test_stats_no_data(self):
        """Test stats with no calibrations"""
        engine = CalibrationEngine()
        
        stats = engine.get_calibration_stats()
        
        assert stats['total_measurements'] == 0
        assert stats['average_calibration_factor'] == 1.0
        assert stats['accuracy_improvement'] == '0%'
    
    def test_stats_with_data(self):
        """Test stats with calibration data"""
        engine = CalibrationEngine()
        
        # Add calibrations
        for i in range(20):
            engine.calibrate_estimate(
                estimated_energy_j=5000,
                measured_energy_j=4800,
                workload_profile={'workload_type': 'test'}
            )
        
        stats = engine.get_calibration_stats()
        
        assert stats['total_measurements'] == 20
        assert stats['average_calibration_factor'] < 1.0
        assert 'test' in stats['workload_types']
    
    def test_stats_multiple_workload_types(self):
        """Test stats with multiple workload types"""
        engine = CalibrationEngine()
        
        # Add test workloads
        for i in range(10):
            engine.calibrate_estimate(
                estimated_energy_j=5000,
                measured_energy_j=4800,
                workload_profile={'workload_type': 'test'}
            )
        
        # Add build workloads
        for i in range(15):
            engine.calibrate_estimate(
                estimated_energy_j=8000,
                measured_energy_j=7600,
                workload_profile={'workload_type': 'build'}
            )
        
        stats = engine.get_calibration_stats()
        
        assert stats['total_measurements'] == 25
        assert 'test' in stats['workload_types']
        assert 'build' in stats['workload_types']
        assert stats['workload_types']['test']['count'] == 10
        assert stats['workload_types']['build']['count'] == 15
    
    def test_stats_filtered_by_workload_type(self):
        """Test stats filtered by specific workload type"""
        engine = CalibrationEngine()
        
        # Add multiple types
        for i in range(10):
            engine.calibrate_estimate(
                estimated_energy_j=5000,
                measured_energy_j=4800,
                workload_profile={'workload_type': 'test'}
            )
        for i in range(15):
            engine.calibrate_estimate(
                estimated_energy_j=8000,
                measured_energy_j=7600,
                workload_profile={'workload_type': 'build'}
            )
        
        stats = engine.get_calibration_stats(workload_type='test')
        
        assert stats['total_measurements'] == 10
        assert 'test' in stats['workload_types']
        assert 'build' not in stats['workload_types']


class TestStorage:
    """Test calibration storage"""
    
    def test_in_memory_storage(self):
        """Test in-memory storage backend"""
        storage = InMemoryCalibrationStorage()
        
        data = {
            'calibration_factor': 0.95,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        storage.store_calibration(data)
        recent = storage.get_recent_calibrations(days=30)
        
        assert len(recent) == 1
        assert recent[0]['calibration_factor'] == 0.95
    
    def test_storage_recent_filter(self):
        """Test filtering by recency"""
        storage = InMemoryCalibrationStorage()
        
        # Add recent calibration
        storage.store_calibration({
            'calibration_factor': 0.95,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Add old calibration
        old_date = datetime.utcnow() - timedelta(days=40)
        storage.store_calibration({
            'calibration_factor': 0.90,
            'timestamp': old_date.isoformat()
        })
        
        recent = storage.get_recent_calibrations(days=30)
        
        assert len(recent) == 1
        assert recent[0]['calibration_factor'] == 0.95
    
    def test_storage_clear(self):
        """Test clearing storage"""
        storage = InMemoryCalibrationStorage()
        
        storage.store_calibration({
            'calibration_factor': 0.95,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        assert len(storage.get_recent_calibrations()) == 1
        
        storage.clear()
        
        assert len(storage.get_recent_calibrations()) == 0


class TestSingleton:
    """Test singleton pattern"""
    
    def test_singleton_returns_same_instance(self):
        """Test that get_calibration_engine returns same instance"""
        engine1 = get_calibration_engine()
        engine2 = get_calibration_engine()
        
        assert engine1 is engine2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
