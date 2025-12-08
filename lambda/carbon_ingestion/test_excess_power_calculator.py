"""
Unit tests for Excess Power Calculator
"""

import pytest
from datetime import datetime
from excess_power_calculator import ExcessPowerCalculator, MCItoExcessPowerMigration


class TestExcessPowerCalculator:
    
    def setup_method(self):
        self.calculator = ExcessPowerCalculator(region="US-CAL-CISO")
    
    def test_high_curtailment_scenario(self):
        """Test scenario with high renewable curtailment (>10%)"""
        result = self.calculator.calculate_excess_power(
            timestamp=datetime.now(),
            total_generation_mw=5000,
            demand_mw=3000,
            renewable_generation_mw=2500,
            grid_capacity_mw=6000
        )
        
        assert result['recommendation'] == 'SCHEDULE_NOW'
        assert result['confidence'] == 'HIGH'
        assert result['curtailment_percentage'] > 10
        assert result['excess_renewable_mw'] > 0
    
    def test_no_curtailment_scenario(self):
        """Test scenario with no curtailment"""
        result = self.calculator.calculate_excess_power(
            timestamp=datetime.now(),
            total_generation_mw=3000,
            demand_mw=3500,
            renewable_generation_mw=1000,
            grid_capacity_mw=4000
        )
        
        assert result['recommendation'] == 'DEFER'
        assert result['curtailment_percentage'] == 0
        assert result['excess_renewable_mw'] == 0
    
    def test_medium_curtailment_scenario(self):
        """Test scenario with medium curtailment (5-10%)"""
        result = self.calculator.calculate_excess_power(
            timestamp=datetime.now(),
            total_generation_mw=4000,
            demand_mw=3700,  # Less excess to get 5-10% curtailment
            renewable_generation_mw=1500,
            grid_capacity_mw=5000
        )
        
        assert result['recommendation'] in ['SCHEDULE_PREFERRED', 'SCHEDULE_ACCEPTABLE']
        assert 0 < result['curtailment_percentage'] < 15
    
    def test_mci_comparison(self):
        """Test comparison between MCI and Excess Power recommendations"""
        excess_power_data = {
            'recommendation': 'SCHEDULE_NOW',
            'reasoning': 'High curtailment detected',
            'curtailment_percentage': 15.5
        }
        
        comparison = MCItoExcessPowerMigration.compare_metrics(
            mci_value=50,  # Low MCI suggests scheduling
            excess_power_data=excess_power_data
        )
        
        assert 'mci_recommendation' in comparison
        assert 'excess_power_recommendation' in comparison
        assert 'agreement' in comparison


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
