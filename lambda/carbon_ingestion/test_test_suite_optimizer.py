"""
Tests for Test Suite Optimizer
"""

import pytest
from test_suite_optimizer import (
    TestSuiteOptimizer,
    OptimizationType,
    Priority
)


@pytest.fixture
def optimizer():
    """Create optimizer instance"""
    return TestSuiteOptimizer()


@pytest.fixture
def sample_profile():
    """Sample energy profile for testing"""
    return {
        'components': {
            'cpu': 6000,
            'gpu': 1500,
            'ram': 2000,
            'disk': 300,
            'network': 200
        },
        'phases': [
            {'name': 'setup', 'energy_j': 500, 'duration_s': 5},
            {'name': 'test_phase_1', 'energy_j': 3000, 'duration_s': 30},
            {'name': 'test_phase_2', 'energy_j': 4000, 'duration_s': 40},
            {'name': 'test_phase_3', 'energy_j': 2000, 'duration_s': 20},
            {'name': 'cleanup', 'energy_j': 500, 'duration_s': 5}
        ]
    }


class TestBasicAnalysis:
    """Test basic analysis functionality"""
    
    def test_analyze_returns_structure(self, optimizer, sample_profile):
        """Test that analyze returns expected structure"""
        result = optimizer.analyze_test_suite(sample_profile)
        
        assert 'total_energy_j' in result
        assert 'total_carbon_g' in result
        assert 'recommendations' in result
        assert 'total_potential_savings' in result
        assert 'priority_breakdown' in result
        assert 'quick_wins' in result
        assert 'implementation_roadmap' in result
    
    def test_total_energy_calculation(self, optimizer, sample_profile):
        """Test total energy is calculated correctly"""
        result = optimizer.analyze_test_suite(sample_profile)
        
        expected_total = sum(sample_profile['components'].values())
        assert result['total_energy_j'] == expected_total
    
    def test_carbon_calculation(self, optimizer, sample_profile):
        """Test carbon emissions are calculated"""
        result = optimizer.analyze_test_suite(sample_profile)
        
        assert result['total_carbon_g'] > 0
        # Check reasonable conversion (436 gCO2/kWh)
        energy_kwh = result['total_energy_j'] / 3600000
        expected_carbon = energy_kwh * 436
        assert abs(result['total_carbon_g'] - expected_carbon) < 0.01


class TestParallelizationAnalysis:
    """Test parallelization recommendations"""
    
    def test_detects_sequential_tests(self, optimizer, sample_profile):
        """Test detection of sequential test phases"""
        result = optimizer.analyze_test_suite(sample_profile)
        
        # Should detect parallelization opportunity
        parallel_recs = [r for r in result['recommendations'] 
                        if r['type'] == OptimizationType.PARALLELIZATION.value]
        
        assert len(parallel_recs) > 0
    
    def test_parallelization_savings_estimate(self, optimizer, sample_profile):
        """Test parallelization savings are reasonable"""
        result = optimizer.analyze_test_suite(sample_profile)
        
        parallel_recs = [r for r in result['recommendations'] 
                        if r['type'] == OptimizationType.PARALLELIZATION.value]
        
        if parallel_recs:
            rec = parallel_recs[0]
            # Savings should be 30-50% of test energy
            assert 25 <= rec['potential_savings']['percent'] <= 55


class TestResourceOptimization:
    """Test resource optimization recommendations"""
    
    def test_detects_cpu_intensive(self, optimizer):
        """Test detection of CPU-intensive workloads"""
        profile = {
            'components': {
                'cpu': 7000,  # 70% of total
                'gpu': 1000,
                'ram': 1000,
                'disk': 500,
                'network': 500
            },
            'phases': [
                {'name': 'processing', 'energy_j': 10000, 'duration_s': 100}
            ]
        }
        
        result = optimizer.analyze_test_suite(profile)
        
        # Should recommend CPU optimization
        cpu_recs = [r for r in result['recommendations'] 
                   if 'CPU' in r['title']]
        
        assert len(cpu_recs) > 0
    
    def test_detects_memory_intensive(self, optimizer):
        """Test detection of memory-intensive workloads"""
        profile = {
            'components': {
                'cpu': 3000,
                'gpu': 1000,
                'ram': 4000,  # 40% of total
                'disk': 1000,
                'network': 1000
            },
            'phases': [
                {'name': 'processing', 'energy_j': 10000, 'duration_s': 100}
            ]
        }
        
        result = optimizer.analyze_test_suite(profile)
        
        # Should recommend memory optimization
        ram_recs = [r for r in result['recommendations'] 
                   if 'Memory' in r['title']]
        
        assert len(ram_recs) > 0
    
    def test_detects_disk_intensive(self, optimizer):
        """Test detection of disk-intensive workloads"""
        profile = {
            'components': {
                'cpu': 3000,
                'gpu': 1000,
                'ram': 2000,
                'disk': 3000,  # 30% of total
                'network': 1000
            },
            'phases': [
                {'name': 'processing', 'energy_j': 10000, 'duration_s': 100}
            ]
        }
        
        result = optimizer.analyze_test_suite(profile)
        
        # Should recommend disk optimization
        disk_recs = [r for r in result['recommendations'] 
                    if 'Disk' in r['title']]
        
        assert len(disk_recs) > 0


class TestTestSelection:
    """Test smart test selection recommendations"""
    
    def test_detects_long_running_tests(self, optimizer):
        """Test detection of long-running test phases"""
        profile = {
            'components': {
                'cpu': 5000,
                'gpu': 2000,
                'ram': 2000,
                'disk': 500,
                'network': 500
            },
            'phases': [
                {'name': 'fast_test', 'energy_j': 1000, 'duration_s': 10},
                {'name': 'slow_test_1', 'energy_j': 4000, 'duration_s': 80},
                {'name': 'slow_test_2', 'energy_j': 5000, 'duration_s': 100}
            ]
        }
        
        result = optimizer.analyze_test_suite(profile)
        
        # Should recommend test selection
        selection_recs = [r for r in result['recommendations'] 
                         if r['type'] == OptimizationType.TEST_SELECTION.value]
        
        assert len(selection_recs) > 0


class TestCachingAnalysis:
    """Test caching recommendations"""
    
    def test_detects_repeated_operations(self, optimizer):
        """Test detection of repeated operations"""
        profile = {
            'components': {
                'cpu': 5000,
                'gpu': 2000,
                'ram': 2000,
                'disk': 500,
                'network': 500
            },
            'phases': [
                {'name': 'operation_a', 'energy_j': 2000, 'duration_s': 20},
                {'name': 'operation_a', 'energy_j': 2000, 'duration_s': 20},
                {'name': 'operation_b', 'energy_j': 3000, 'duration_s': 30},
                {'name': 'operation_b', 'energy_j': 3000, 'duration_s': 30}
            ]
        }
        
        result = optimizer.analyze_test_suite(profile)
        
        # Should recommend caching
        cache_recs = [r for r in result['recommendations'] 
                     if r['type'] == OptimizationType.CACHING.value]
        
        assert len(cache_recs) > 0


class TestPriorityAssignment:
    """Test priority assignment logic"""
    
    def test_critical_priority_for_high_savings(self, optimizer):
        """Test critical priority for >30% savings"""
        profile = {
            'components': {
                'cpu': 5000,
                'gpu': 2000,
                'ram': 2000,
                'disk': 500,
                'network': 500
            },
            'phases': [
                {'name': 'test_1', 'energy_j': 3000, 'duration_s': 30},
                {'name': 'test_2', 'energy_j': 4000, 'duration_s': 40},
                {'name': 'test_3', 'energy_j': 3000, 'duration_s': 30}
            ]
        }
        
        result = optimizer.analyze_test_suite(profile)
        
        # Should have critical priority recommendations
        critical_recs = [r for r in result['recommendations'] 
                        if r['priority'] == Priority.CRITICAL.value]
        
        assert len(critical_recs) > 0
    
    def test_priority_breakdown_structure(self, optimizer, sample_profile):
        """Test priority breakdown has correct structure"""
        result = optimizer.analyze_test_suite(sample_profile)
        
        breakdown = result['priority_breakdown']
        
        assert 'critical' in breakdown
        assert 'high' in breakdown
        assert 'medium' in breakdown
        assert 'low' in breakdown
        
        for priority in breakdown.values():
            assert 'count' in priority
            assert 'items' in priority


class TestQuickWins:
    """Test quick wins identification"""
    
    def test_quick_wins_are_low_effort(self, optimizer, sample_profile):
        """Test quick wins are low effort"""
        result = optimizer.analyze_test_suite(sample_profile)
        
        for win in result['quick_wins']:
            assert win['effort'] == 'low'
    
    def test_quick_wins_are_high_priority(self, optimizer, sample_profile):
        """Test quick wins are high priority"""
        result = optimizer.analyze_test_suite(sample_profile)
        
        for win in result['quick_wins']:
            assert win['priority'] in [Priority.CRITICAL.value, Priority.HIGH.value]
    
    def test_quick_wins_limited_to_three(self, optimizer, sample_profile):
        """Test quick wins are limited to top 3"""
        result = optimizer.analyze_test_suite(sample_profile)
        
        assert len(result['quick_wins']) <= 3


class TestImplementationRoadmap:
    """Test implementation roadmap generation"""
    
    def test_roadmap_has_phases(self, optimizer, sample_profile):
        """Test roadmap has all phases"""
        result = optimizer.analyze_test_suite(sample_profile)
        
        roadmap = result['implementation_roadmap']
        
        assert 'phase_1_immediate' in roadmap
        assert 'phase_2_short_term' in roadmap
        assert 'phase_3_medium_term' in roadmap
        assert 'phase_4_long_term' in roadmap
    
    def test_roadmap_phase_structure(self, optimizer, sample_profile):
        """Test each phase has title and items"""
        result = optimizer.analyze_test_suite(sample_profile)
        
        roadmap = result['implementation_roadmap']
        
        for phase in roadmap.values():
            assert 'title' in phase
            assert 'items' in phase
            assert isinstance(phase['items'], list)


class TestRecommendationDetails:
    """Test recommendation details"""
    
    def test_recommendations_have_required_fields(self, optimizer, sample_profile):
        """Test recommendations have all required fields"""
        result = optimizer.analyze_test_suite(sample_profile)
        
        for rec in result['recommendations']:
            assert 'type' in rec
            assert 'priority' in rec
            assert 'title' in rec
            assert 'description' in rec
            assert 'potential_savings' in rec
            assert 'effort' in rec
            assert 'implementation_steps' in rec
    
    def test_potential_savings_structure(self, optimizer, sample_profile):
        """Test potential savings has correct structure"""
        result = optimizer.analyze_test_suite(sample_profile)
        
        for rec in result['recommendations']:
            savings = rec['potential_savings']
            
            assert 'percent' in savings
            assert 'energy_j' in savings
            assert 'carbon_g' in savings
            assert 'carbon_equivalent' in savings
    
    def test_implementation_steps_not_empty(self, optimizer, sample_profile):
        """Test implementation steps are provided"""
        result = optimizer.analyze_test_suite(sample_profile)
        
        for rec in result['recommendations']:
            assert len(rec['implementation_steps']) > 0


class TestTotalSavings:
    """Test total potential savings calculation"""
    
    def test_total_savings_sum(self, optimizer, sample_profile):
        """Test total savings is sum of all recommendations"""
        result = optimizer.analyze_test_suite(sample_profile)
        
        manual_sum = sum(r['potential_savings']['energy_j'] 
                        for r in result['recommendations'])
        
        assert abs(result['total_potential_savings']['energy_j'] - manual_sum) < 0.01
    
    def test_total_savings_percentage(self, optimizer, sample_profile):
        """Test total savings percentage is reasonable"""
        result = optimizer.analyze_test_suite(sample_profile)
        
        # Should be between 0 and 100%
        assert 0 <= result['total_potential_savings']['energy_percent'] <= 100


class TestEdgeCases:
    """Test edge cases"""
    
    def test_empty_phases(self, optimizer):
        """Test handling of empty phases"""
        profile = {
            'components': {
                'cpu': 5000,
                'gpu': 2000,
                'ram': 2000,
                'disk': 500,
                'network': 500
            },
            'phases': []
        }
        
        result = optimizer.analyze_test_suite(profile)
        
        # Should still return valid structure
        assert 'recommendations' in result
        assert isinstance(result['recommendations'], list)
    
    def test_single_phase(self, optimizer):
        """Test handling of single phase"""
        profile = {
            'components': {
                'cpu': 5000,
                'gpu': 2000,
                'ram': 2000,
                'disk': 500,
                'network': 500
            },
            'phases': [
                {'name': 'single_test', 'energy_j': 10000, 'duration_s': 100}
            ]
        }
        
        result = optimizer.analyze_test_suite(profile)
        
        # Should not recommend parallelization for single phase
        parallel_recs = [r for r in result['recommendations'] 
                        if r['type'] == OptimizationType.PARALLELIZATION.value]
        
        assert len(parallel_recs) == 0
    
    def test_zero_energy(self, optimizer):
        """Test handling of zero energy"""
        profile = {
            'components': {
                'cpu': 0,
                'gpu': 0,
                'ram': 0,
                'disk': 0,
                'network': 0
            },
            'phases': []
        }
        
        result = optimizer.analyze_test_suite(profile)
        
        # Should handle gracefully
        assert result['total_energy_j'] == 0
        assert result['total_potential_savings']['energy_percent'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
