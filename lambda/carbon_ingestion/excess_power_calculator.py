"""
Excess Power Metric Calculator
Based on: "Moving Beyond Marginal Carbon Intensity" research paper

Replaces unreliable Marginal Carbon Intensity (MCI) with actionable
Excess Power metric that reflects actual curtailment periods.
"""

from typing import Dict, Optional
from datetime import datetime
import logging
import os
import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger(__name__)

# DynamoDB configuration
CARBON_TABLE = os.environ.get('CARBON_TABLE', 'green-qa-carbon-intensity-prod')

# Initialize DynamoDB lazily to avoid errors when testing without AWS credentials
dynamodb = None
carbon_table = None

def _get_dynamodb_table():
    """Lazy initialization of DynamoDB table"""
    global dynamodb, carbon_table
    if carbon_table is None:
        region = os.environ.get('AWS_REGION', 'us-east-1')
        dynamodb = boto3.resource('dynamodb', region_name=region)
        carbon_table = dynamodb.Table(CARBON_TABLE)
    return carbon_table


class ExcessPowerCalculator:
    """
    Calculates excess renewable power available in a region.
    
    Key advantages over MCI:
    1. Reflects curtailment from ANY source (not just renewables)
    2. Quantifies available capacity (not just intensity)
    3. Observable and verifiable (not model-dependent)
    """
    
    def __init__(self, region: str):
        self.region = region
        self.logger = logger
    
    def calculate_excess_power(
        self, 
        timestamp: datetime,
        total_generation_mw: float,
        demand_mw: float,
        renewable_generation_mw: float,
        grid_capacity_mw: float
    ) -> Dict[str, any]:
        """
        Calculate excess power and provide scheduling recommendation.
        
        Args:
            timestamp: Time of measurement
            total_generation_mw: Total power generation
            demand_mw: Current demand
            renewable_generation_mw: Renewable generation only
            grid_capacity_mw: Maximum grid capacity
            
        Returns:
            Dict with excess power metrics and recommendation
        """
        
        # Calculate excess power (generation exceeds demand)
        excess_total = max(0, total_generation_mw - demand_mw)
        
        # Calculate how much renewable power is available but not being used
        # This happens when total generation > demand and we have renewables
        if total_generation_mw > demand_mw and renewable_generation_mw > 0:
            # Excess renewable is the portion of excess that comes from renewables
            renewable_fraction = renewable_generation_mw / total_generation_mw
            excess_renewable = excess_total * renewable_fraction
        else:
            excess_renewable = 0
        
        # Calculate curtailment percentage (what % of renewable capacity is wasted)
        curtailment_pct = (
            (excess_renewable / renewable_generation_mw * 100) 
            if renewable_generation_mw > 0 else 0
        )
        
        # Calculate available capacity for additional load
        available_capacity = grid_capacity_mw - demand_mw
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            excess_renewable, 
            curtailment_pct,
            available_capacity
        )
        
        return {
            'timestamp': timestamp.isoformat(),
            'region': self.region,
            'excess_renewable_mw': round(excess_renewable, 2),
            'excess_total_mw': round(excess_total, 2),
            'curtailment_percentage': round(curtailment_pct, 2),
            'available_capacity_mw': round(available_capacity, 2),
            'recommendation': recommendation['action'],
            'confidence': recommendation['confidence'],
            'reasoning': recommendation['reasoning']
        }
    
    def _generate_recommendation(
        self, 
        excess_mw: float, 
        curtailment_pct: float,
        available_capacity: float
    ) -> Dict[str, str]:
        """
        Generate actionable scheduling recommendation.
        
        Thresholds based on research findings:
        - High curtailment (>10%): Strong signal to schedule
        - Medium curtailment (5-10%): Good opportunity
        - Low curtailment (<5%): Defer if possible
        """
        
        if curtailment_pct > 10 and available_capacity > 100:
            return {
                'action': 'SCHEDULE_NOW',
                'confidence': 'HIGH',
                'reasoning': f'{curtailment_pct:.1f}% renewable curtailment detected. '
                           f'{excess_mw:.0f} MW excess power available.'
            }
        elif curtailment_pct > 5 and available_capacity > 50:
            return {
                'action': 'SCHEDULE_PREFERRED',
                'confidence': 'MEDIUM',
                'reasoning': f'{curtailment_pct:.1f}% curtailment. '
                           f'Good opportunity for carbon reduction.'
            }
        elif curtailment_pct > 2:
            return {
                'action': 'SCHEDULE_ACCEPTABLE',
                'confidence': 'LOW',
                'reasoning': f'Minimal curtailment ({curtailment_pct:.1f}%). '
                           f'Marginal carbon benefit.'
            }
        else:
            return {
                'action': 'DEFER',
                'confidence': 'HIGH',
                'reasoning': 'No significant excess renewable power. '
                           'Consider scheduling during lower-carbon period.'
            }
    
    def get_grid_data_from_electricitymaps(self, region: str) -> Dict:
        """
        Fetch real grid data from ElectricityMaps API.
        Falls back to DynamoDB if API unavailable.
        """
        try:
            # Try ElectricityMaps API first
            api_token = os.getenv('ELECTRICITYMAPS_API_TOKEN')
            
            if api_token:
                import requests
                url = f"https://api.electricitymap.org/v3/power-breakdown/latest?zone={region}"
                headers = {'auth-token': api_token}
                response = requests.get(url, headers=headers, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_electricitymaps_data(data)
            
            # Fallback to DynamoDB
            logger.info(f"ElectricityMaps API not available, using DynamoDB fallback for {region}")
            return self._get_grid_data_from_dynamodb(region)
        
        except Exception as e:
            logger.warning(f"Could not fetch grid data from ElectricityMaps: {e}")
            return self._get_grid_data_from_dynamodb(region)
    
    def _parse_electricitymaps_data(self, data: Dict) -> Dict:
        """Parse ElectricityMaps API response"""
        power_breakdown = data.get('powerConsumptionBreakdown', {})
        
        # Calculate totals
        total_generation = sum(v for v in power_breakdown.values() if v and v > 0)
        
        # Renewable sources
        renewable_sources = ['solar', 'wind', 'hydro', 'geothermal', 'biomass']
        renewable_generation = sum(
            power_breakdown.get(source, 0) or 0 
            for source in renewable_sources
        )
        
        # Get demand (consumption)
        demand = data.get('powerConsumptionTotal', total_generation)
        
        return {
            'total_generation_mw': total_generation,
            'demand_mw': demand,
            'renewable_generation_mw': renewable_generation,
            'grid_capacity_mw': total_generation * 1.2,  # Estimate: 20% headroom
            'timestamp': data.get('datetime'),
            'source': 'electricitymaps'
        }
    
    def _get_grid_data_from_dynamodb(self, region: str) -> Dict:
        """Fallback: Get data from DynamoDB and estimate grid parameters"""
        try:
            # Get DynamoDB table
            table = _get_dynamodb_table()
            
            # Query latest entry for region
            response = table.query(
                KeyConditionExpression=Key('region_id').eq(region),
                ScanIndexForward=False,
                Limit=1
            )
            
            items = response.get('Items', [])
            if not items:
                raise ValueError(f"No data for region {region}")
            
            item = items[0]
            ci = float(item['carbon_intensity'])
            timestamp = int(item['timestamp'])
            
            # Estimate grid parameters from carbon intensity
            # Lower intensity = more renewables
            # CI ranges: 0-100 (very clean) to 500+ (very dirty)
            renewable_pct = max(0, min(100, (500 - ci) / 5))  # Rough estimate
            
            # Estimate grid size based on region
            # These are rough estimates - in production, use actual grid data
            region_capacity_estimates = {
                'eu-west-2': 6000,  # UK ~60 GW
                'us-east-1': 15000,  # US East ~150 GW
                'us-west-2': 10000,  # US West ~100 GW
                'eu-central-1': 8000,  # Germany ~80 GW
                'ap-southeast-1': 7000,  # Singapore ~70 GW
            }
            
            grid_capacity = region_capacity_estimates.get(region, 5000)
            
            # Estimate current generation and demand
            # Assume 70-85% capacity utilization
            utilization = 0.75 + (renewable_pct / 400)  # Higher renewables = higher utilization
            total_gen = grid_capacity * utilization
            demand = total_gen * 0.95  # Assume 5% reserve margin
            renewable_gen = total_gen * (renewable_pct / 100)
            
            return {
                'total_generation_mw': total_gen,
                'demand_mw': demand,
                'renewable_generation_mw': renewable_gen,
                'grid_capacity_mw': grid_capacity,
                'timestamp': datetime.fromtimestamp(timestamp).isoformat(),
                'source': 'estimated',
                'note': f'Estimated from carbon intensity ({ci} gCO2/kWh)',
                'carbon_intensity': ci
            }
        
        except Exception as e:
            logger.error(f"Fallback data fetch failed for {region}: {e}")
            raise
    
    def get_historical_excess_power_pattern(
        self, 
        days_back: int = 7
    ) -> Dict[str, any]:
        """
        Analyze historical excess power patterns to identify
        recurring low-carbon opportunities.
        
        Returns:
            Pattern analysis with best scheduling windows
        """
        # TODO: Implement historical analysis
        # This will help identify recurring patterns (e.g., solar midday dip)
        pass


# Comparison utility for migration from MCI
class MCItoExcessPowerMigration:
    """
    Helper class to compare MCI vs Excess Power recommendations
    during migration period.
    """
    
    @staticmethod
    def compare_metrics(mci_value: float, excess_power_data: Dict) -> Dict:
        """
        Compare MCI-based recommendation vs Excess Power recommendation.
        
        This helps validate the migration and understand differences.
        """
        
        # MCI-based recommendation (old approach)
        mci_recommendation = "SCHEDULE" if mci_value < 100 else "DEFER"
        
        # Excess Power recommendation (new approach)
        ep_recommendation = excess_power_data['recommendation']
        
        agreement = mci_recommendation == ep_recommendation.split('_')[0]
        
        return {
            'mci_recommendation': mci_recommendation,
            'excess_power_recommendation': ep_recommendation,
            'agreement': agreement,
            'reasoning': excess_power_data['reasoning'],
            'migration_note': (
                'Recommendations align' if agreement 
                else 'Excess Power provides more nuanced guidance'
            )
        }
