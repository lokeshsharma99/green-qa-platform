"""
MAIZX Ranking Algorithm for Multi-Region Carbon Optimization

Based on: "MAIZX: A Carbon-Aware Framework for Optimizing Cloud Computing Emissions"
by Federico Ruilova et al. (2024)

Achieves 85.68% CO2 reduction through dynamic workload allocation based on:
- Current Carbon Footprint (CFP)
- Forecasted Carbon Footprint (FCFP)
- Computing Power Ratio (CP_RATIO)
- Schedule Weight (SCHEDULE_WEIGHT)
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

# Import existing modules
try:
    from carbonx_forecaster import CarbonXForecaster
    from cpu_power_lookup import get_cpu_lookup
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    logging.warning("Dependencies not available")

logger = logging.getLogger(__name__)


@dataclass
class WorkloadSpec:
    """Specification for a workload to be scheduled"""
    duration_hours: float
    cpu_utilization: float = 0.7  # Expected CPU utilization (0.0-1.0)
    memory_gb: float = 8.0
    vcpu_count: int = 4
    deadline_hours: Optional[float] = None  # Deadline flexibility
    priority: str = 'normal'  # 'low', 'normal', 'high', 'critical'


@dataclass
class RegionScore:
    """MAIZX ranking score for a region"""
    region: str
    maizx_score: float
    cfp: float  # Current Carbon Footprint
    fcfp: float  # Forecasted Carbon Footprint
    cp_ratio: float  # Computing Power Ratio
    schedule_weight: float
    carbon_intensity_current: float
    carbon_intensity_forecast: float
    power_consumption_w: float
    recommendation: str
    savings_vs_worst_percent: float = 0.0


class MAIZXRanker:
    """
    MAIZX ranking algorithm for AWS region selection.
    
    Dynamically ranks regions based on:
    1. Current carbon footprint
    2. Forecasted carbon footprint
    3. Computing power efficiency
    4. Scheduling constraints
    
    Achieves 85.68% CO2 reduction compared to baseline.
    """
    
    def __init__(
        self,
        w1: float = 0.4,  # Weight for current CFP
        w2: float = 0.3,  # Weight for forecasted CFP
        w3: float = 0.2,  # Weight for CP ratio
        w4: float = 0.1   # Weight for schedule
    ):
        """
        Initialize MAIZX ranker with configurable weights.
        
        Args:
            w1: Weight for current carbon footprint (default: 0.4)
            w2: Weight for forecasted carbon footprint (default: 0.3)
            w3: Weight for computing power ratio (default: 0.2)
            w4: Weight for schedule weight (default: 0.1)
        """
        # Validate weights sum to 1.0
        total = w1 + w2 + w3 + w4
        if abs(total - 1.0) > 0.01:
            logger.warning(f"Weights sum to {total}, normalizing to 1.0")
            w1, w2, w3, w4 = w1/total, w2/total, w3/total, w4/total
        
        self.w1 = w1
        self.w2 = w2
        self.w3 = w3
        self.w4 = w4
        
        logger.info(f"MAIZX Ranker initialized with weights: "
                   f"CFP={w1}, FCFP={w2}, CP_RATIO={w3}, SCHEDULE={w4}")
    
    def calculate_cfp(
        self,
        region: str,
        workload: WorkloadSpec,
        carbon_intensity: float
    ) -> Tuple[float, float]:
        """
        Calculate Current Carbon Footprint (CFP).
        
        Formula: CFP = Energy_Consumption × PUE × Carbon_Intensity
        
        Returns: (CFP in gCO2, Power in Watts)
        """
        # Get CPU power lookup if available
        if DEPENDENCIES_AVAILABLE:
            try:
                lookup = get_cpu_lookup()
                power_w = lookup.calculate_power_consumption(
                    cpu_model=None,  # Will use instance type fallback
                    cpu_utilization=workload.cpu_utilization,
                    instance_type=self._get_instance_type_for_region(region),
                    num_cpus=max(1, workload.vcpu_count // 8)
                )
            except Exception as e:
                logger.warning(f"CPU lookup failed, using estimate: {e}")
                power_w = workload.vcpu_count * 10 * workload.cpu_utilization
        else:
            # Fallback: estimate 10W per vCPU
            power_w = workload.vcpu_count * 10 * workload.cpu_utilization
        
        # Add memory power (0.000392 kWh per GB-hour)
        memory_power_w = (workload.memory_gb * 0.000392 * 1000) / 1  # Convert to W
        
        # Total power
        total_power_w = power_w + memory_power_w
        
        # Energy consumption for duration (kWh)
        energy_kwh = (total_power_w / 1000) * workload.duration_hours
        
        # Apply PUE (Power Usage Effectiveness) - AWS average is 1.135
        pue = 1.135
        energy_with_pue_kwh = energy_kwh * pue
        
        # Calculate carbon footprint (gCO2)
        cfp = energy_with_pue_kwh * carbon_intensity
        
        return cfp, total_power_w
    
    def calculate_fcfp(
        self,
        region: str,
        workload: WorkloadSpec
    ) -> Tuple[float, float]:
        """
        Calculate Forecasted Carbon Footprint (FCFP).
        
        Uses CarbonX forecaster to predict carbon intensity.
        
        Returns: (FCFP in gCO2, Forecast Carbon Intensity)
        """
        if not DEPENDENCIES_AVAILABLE:
            # Fallback: assume same as current
            logger.warning("Forecaster not available, using current CI")
            return 0.0, 0.0
        
        try:
            forecaster = CarbonXForecaster(region)
            
            # Get forecast for workload duration
            forecast_data = forecaster.forecast_with_uncertainty(
                historical_data=None,  # Auto-fetch
                hours_ahead=int(workload.duration_hours) + 1
            )
            
            # Calculate average forecast CI for workload duration
            forecasts = forecast_data['forecasts'][:int(workload.duration_hours)]
            avg_forecast_ci = sum(f['carbon_intensity'] for f in forecasts) / len(forecasts)
            
            # Calculate FCFP using forecast CI
            fcfp, _ = self.calculate_cfp(region, workload, avg_forecast_ci)
            
            return fcfp, avg_forecast_ci
        
        except Exception as e:
            logger.warning(f"Forecast failed for {region}: {e}")
            return 0.0, 0.0
    
    def calculate_cp_ratio(
        self,
        region: str,
        workload: WorkloadSpec,
        power_w: float
    ) -> float:
        """
        Calculate Computing Power Ratio (CP_RATIO).
        
        Measures energy efficiency: work done per watt.
        Higher is better (more efficient).
        
        Formula: CP_RATIO = (vCPUs × Utilization) / Power_Consumption
        """
        computing_power = workload.vcpu_count * workload.cpu_utilization
        cp_ratio = computing_power / power_w if power_w > 0 else 0
        
        return cp_ratio
    
    def calculate_schedule_weight(
        self,
        workload: WorkloadSpec
    ) -> float:
        """
        Calculate Schedule Weight based on priority and deadline.
        
        Higher weight = more urgent = prefer immediate execution.
        Lower weight = flexible = can wait for better carbon time.
        
        Returns: Weight between 0.0 (very flexible) and 1.0 (critical)
        """
        # Base weight from priority
        priority_weights = {
            'low': 0.2,
            'normal': 0.5,
            'high': 0.7,
            'critical': 1.0
        }
        base_weight = priority_weights.get(workload.priority, 0.5)
        
        # Adjust based on deadline flexibility
        if workload.deadline_hours:
            # More flexibility = lower weight (can wait)
            flexibility_factor = min(1.0, workload.deadline_hours / 24)
            adjusted_weight = base_weight * (1 - flexibility_factor * 0.5)
        else:
            adjusted_weight = base_weight
        
        return adjusted_weight
    
    def calculate_maizx_score(
        self,
        region: str,
        workload: WorkloadSpec,
        carbon_intensity_current: float
    ) -> RegionScore:
        """
        Calculate MAIZX ranking score for a region.
        
        Formula: MAIZX_RANKING = w1*CFP + w2*FCFP + w3*CP_RATIO + w4*SCHEDULE_WEIGHT
        
        Lower score = better (lower carbon footprint).
        """
        # Calculate components
        cfp, power_w = self.calculate_cfp(region, workload, carbon_intensity_current)
        fcfp, forecast_ci = self.calculate_fcfp(region, workload)
        cp_ratio = self.calculate_cp_ratio(region, workload, power_w)
        schedule_weight = self.calculate_schedule_weight(workload)
        
        # Normalize components to 0-1 range for fair weighting
        # CFP and FCFP: normalize by typical range (0-1000 gCO2)
        cfp_norm = min(1.0, cfp / 1000)
        fcfp_norm = min(1.0, fcfp / 1000) if fcfp > 0 else cfp_norm
        
        # CP_RATIO: invert so lower is better (0.01-0.1 typical range)
        cp_ratio_norm = 1.0 - min(1.0, cp_ratio / 0.1)
        
        # Schedule weight is already 0-1
        
        # Calculate MAIZX score (lower is better)
        maizx_score = (
            self.w1 * cfp_norm +
            self.w2 * fcfp_norm +
            self.w3 * cp_ratio_norm +
            self.w4 * schedule_weight
        )
        
        # Determine recommendation
        if maizx_score < 0.3:
            recommendation = "EXCELLENT"
        elif maizx_score < 0.5:
            recommendation = "GOOD"
        elif maizx_score < 0.7:
            recommendation = "FAIR"
        else:
            recommendation = "POOR"
        
        return RegionScore(
            region=region,
            maizx_score=maizx_score,
            cfp=cfp,
            fcfp=fcfp if fcfp > 0 else cfp,
            cp_ratio=cp_ratio,
            schedule_weight=schedule_weight,
            carbon_intensity_current=carbon_intensity_current,
            carbon_intensity_forecast=forecast_ci if forecast_ci > 0 else carbon_intensity_current,
            power_consumption_w=power_w,
            recommendation=recommendation
        )
    
    def rank_regions(
        self,
        workload: WorkloadSpec,
        regions_carbon_intensity: Dict[str, float],
        top_n: int = 5
    ) -> List[RegionScore]:
        """
        Rank all regions using MAIZX algorithm.
        
        Args:
            workload: Workload specification
            regions_carbon_intensity: Dict of {region: current_carbon_intensity}
            top_n: Number of top regions to return
            
        Returns:
            List of RegionScore objects, sorted by MAIZX score (best first)
        """
        scores = []
        
        for region, carbon_intensity in regions_carbon_intensity.items():
            try:
                score = self.calculate_maizx_score(region, workload, carbon_intensity)
                scores.append(score)
            except Exception as e:
                logger.error(f"Error scoring region {region}: {e}")
                continue
        
        # Sort by MAIZX score (lower is better)
        scores.sort(key=lambda x: x.maizx_score)
        
        # Calculate savings vs worst
        if scores:
            worst_cfp = max(s.cfp for s in scores)
            for score in scores:
                score.savings_vs_worst_percent = round(
                    ((worst_cfp - score.cfp) / worst_cfp * 100) if worst_cfp > 0 else 0,
                    2
                )
        
        return scores[:top_n]
    
    def recommend_optimal_region(
        self,
        workload: WorkloadSpec,
        regions_carbon_intensity: Dict[str, float]
    ) -> Dict:
        """
        Get optimal region recommendation with detailed analysis.
        
        Returns: Dict with recommendation and analysis
        """
        ranked_regions = self.rank_regions(workload, regions_carbon_intensity, top_n=3)
        
        if not ranked_regions:
            return {
                'error': 'No regions available',
                'timestamp': datetime.now().isoformat()
            }
        
        best = ranked_regions[0]
        
        return {
            'recommended_region': best.region,
            'maizx_score': round(best.maizx_score, 4),
            'recommendation': best.recommendation,
            'carbon_footprint_gco2': round(best.cfp, 2),
            'forecasted_carbon_footprint_gco2': round(best.fcfp, 2),
            'power_consumption_w': round(best.power_consumption_w, 2),
            'computing_power_ratio': round(best.cp_ratio, 4),
            'savings_vs_worst_percent': best.savings_vs_worst_percent,
            'top_3_regions': [
                {
                    'region': s.region,
                    'maizx_score': round(s.maizx_score, 4),
                    'recommendation': s.recommendation,
                    'carbon_footprint_gco2': round(s.cfp, 2),
                    'savings_percent': s.savings_vs_worst_percent
                }
                for s in ranked_regions
            ],
            'workload': {
                'duration_hours': workload.duration_hours,
                'vcpu_count': workload.vcpu_count,
                'memory_gb': workload.memory_gb,
                'priority': workload.priority
            },
            'weights': {
                'current_cfp': self.w1,
                'forecast_cfp': self.w2,
                'cp_ratio': self.w3,
                'schedule': self.w4
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_instance_type_for_region(self, region: str) -> str:
        """Get typical instance type for region (for CPU lookup)"""
        # Default to m5.large for most regions
        return 'm5.large'


# Example usage
if __name__ == '__main__':
    print("=== MAIZX Ranking Algorithm Test ===\n")
    
    # Create ranker
    ranker = MAIZXRanker()
    
    # Define workload
    workload = WorkloadSpec(
        duration_hours=4.0,
        cpu_utilization=0.7,
        memory_gb=16.0,
        vcpu_count=8,
        deadline_hours=24.0,
        priority='normal'
    )
    
    # Mock carbon intensity data for regions
    regions_ci = {
        'eu-west-2': 180.5,  # UK - low
        'eu-west-1': 350.2,  # Ireland - medium
        'eu-central-1': 420.8,  # Germany - high
        'us-east-1': 450.3,  # Virginia - high
        'us-west-2': 200.1,  # Oregon - low
        'us-west-1': 320.5,  # California - medium
    }
    
    # Get recommendation
    recommendation = ranker.recommend_optimal_region(workload, regions_ci)
    
    print(f"Recommended Region: {recommendation['recommended_region']}")
    print(f"MAIZX Score: {recommendation['maizx_score']}")
    print(f"Recommendation: {recommendation['recommendation']}")
    print(f"Carbon Footprint: {recommendation['carbon_footprint_gco2']} gCO2")
    print(f"Savings vs Worst: {recommendation['savings_vs_worst_percent']}%")
    print(f"\nTop 3 Regions:")
    for i, region in enumerate(recommendation['top_3_regions'], 1):
        print(f"  {i}. {region['region']}: {region['maizx_score']} "
              f"({region['recommendation']}, {region['carbon_footprint_gco2']} gCO2)")
    
    print("\n=== Test complete ===")
