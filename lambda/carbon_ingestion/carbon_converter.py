"""
Carbon Converter - Energy to CO₂ Emissions

Converts energy measurements (Joules, Watt-hours, kWh) to CO₂ emissions
based on grid carbon intensity.

Formula: CO₂ (g) = Energy (kWh) × Carbon Intensity (gCO₂/kWh)
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class CarbonConverter:
    """
    Convert energy measurements to CO₂ emissions.
    
    Features:
    - Multiple energy unit support (J, Wh, kWh)
    - Component-level breakdown
    - Carbon equivalents (miles driven, trees planted)
    - Regional carbon intensity
    
    Example:
        converter = CarbonConverter()
        
        # Convert energy to carbon
        result = converter.joules_to_carbon(
            energy_j=10000,
            carbon_intensity_g_per_kwh=250,
            region='eu-west-2'
        )
        
        print(f"Carbon: {result['carbon_g']} g")
        print(f"Equivalent: {result['equivalent']['miles_driven']} miles")
    """
    
    # Conversion constants
    JOULES_PER_KWH = 3_600_000
    JOULES_PER_WH = 3_600
    
    # Carbon equivalents (per gram of CO₂)
    MILES_PER_G_CO2 = 0.00000227  # Miles driven in average car
    TREES_PER_G_CO2 = 0.0000000476  # Trees needed to offset (per year)
    SMARTPHONE_CHARGES_PER_G_CO2 = 0.0833  # Smartphone charges (12g per charge)
    
    def __init__(self):
        self.default_carbon_intensity = 250  # gCO₂/kWh (global average)
    
    def joules_to_carbon(
        self,
        energy_j: float,
        carbon_intensity_g_per_kwh: Optional[float] = None,
        region: Optional[str] = None,
        include_equivalents: bool = True
    ) -> Dict:
        """
        Convert Joules to CO₂ emissions.
        
        Args:
            energy_j: Energy in Joules
            carbon_intensity_g_per_kwh: Grid carbon intensity (gCO₂/kWh)
            region: AWS region (for context)
            include_equivalents: Include carbon equivalents
        
        Returns:
        {
            'energy_j': float,
            'energy_kwh': float,
            'carbon_g': float,
            'carbon_kg': float,
            'carbon_intensity_g_per_kwh': float,
            'region': str,
            'equivalent': dict (optional)
        }
        """
        carbon_intensity = carbon_intensity_g_per_kwh or self.default_carbon_intensity
        
        # Convert to kWh
        energy_kwh = energy_j / self.JOULES_PER_KWH
        
        # Calculate carbon
        carbon_g = energy_kwh * carbon_intensity
        carbon_kg = carbon_g / 1000
        
        result = {
            'energy_j': energy_j,
            'energy_kwh': energy_kwh,
            'carbon_g': carbon_g,
            'carbon_kg': carbon_kg,
            'carbon_intensity_g_per_kwh': carbon_intensity,
            'region': region or 'unknown'
        }
        
        if include_equivalents:
            result['equivalent'] = self._calculate_equivalents(carbon_g)
        
        return result
    
    def kwh_to_carbon(
        self,
        energy_kwh: float,
        carbon_intensity_g_per_kwh: Optional[float] = None,
        region: Optional[str] = None
    ) -> Dict:
        """Convert kWh to CO₂ emissions"""
        carbon_intensity = carbon_intensity_g_per_kwh or self.default_carbon_intensity
        
        carbon_g = energy_kwh * carbon_intensity
        carbon_kg = carbon_g / 1000
        
        return {
            'energy_kwh': energy_kwh,
            'carbon_g': carbon_g,
            'carbon_kg': carbon_kg,
            'carbon_intensity_g_per_kwh': carbon_intensity,
            'region': region or 'unknown'
        }
    
    def watt_hours_to_carbon(
        self,
        energy_wh: float,
        carbon_intensity_g_per_kwh: Optional[float] = None,
        region: Optional[str] = None
    ) -> Dict:
        """Convert Watt-hours to CO₂ emissions"""
        energy_kwh = energy_wh / 1000
        return self.kwh_to_carbon(energy_kwh, carbon_intensity_g_per_kwh, region)
    
    def component_breakdown_to_carbon(
        self,
        breakdown: Dict,
        carbon_intensity_g_per_kwh: float,
        region: Optional[str] = None
    ) -> Dict:
        """
        Convert component energy breakdown to carbon breakdown.
        
        Args:
            breakdown: Dict with component energies in Joules
                {
                    'cpu_j': float,
                    'memory_j': float,
                    'gpu_j': float,
                    'disk_j': float,
                    'network_j': float
                }
            carbon_intensity_g_per_kwh: Grid carbon intensity
            region: AWS region
        
        Returns:
        {
            'total_carbon_g': float,
            'components': {
                'cpu_g': float,
                'memory_g': float,
                'gpu_g': float,
                'disk_g': float,
                'network_g': float
            },
            'percentages': {
                'cpu_percent': float,
                'memory_percent': float,
                ...
            }
        }
        """
        components = {}
        total_carbon_g = 0
        
        for component, energy_j in breakdown.items():
            if energy_j > 0:
                carbon_g = (energy_j / self.JOULES_PER_KWH) * carbon_intensity_g_per_kwh
                component_name = component.replace('_j', '_g')
                components[component_name] = carbon_g
                total_carbon_g += carbon_g
        
        # Calculate percentages
        percentages = {}
        if total_carbon_g > 0:
            for component, carbon_g in components.items():
                percent_name = component.replace('_g', '_percent')
                percentages[percent_name] = (carbon_g / total_carbon_g) * 100
        
        return {
            'total_carbon_g': total_carbon_g,
            'components': components,
            'percentages': percentages,
            'region': region or 'unknown',
            'carbon_intensity_g_per_kwh': carbon_intensity_g_per_kwh
        }
    
    def _calculate_equivalents(self, carbon_g: float) -> Dict:
        """
        Calculate carbon equivalents for better understanding.
        
        Returns:
        {
            'miles_driven': float,
            'trees_needed': float,
            'smartphone_charges': float,
            'lightbulb_hours': float
        }
        """
        return {
            'miles_driven': carbon_g * self.MILES_PER_G_CO2,
            'trees_needed': carbon_g * self.TREES_PER_G_CO2,
            'smartphone_charges': carbon_g * self.SMARTPHONE_CHARGES_PER_G_CO2,
            'lightbulb_hours': carbon_g / 10  # 10W LED bulb for 1 hour ≈ 1g CO₂
        }
    
    def compare_regions(
        self,
        energy_j: float,
        regions: Dict[str, float]
    ) -> Dict:
        """
        Compare carbon emissions across multiple regions.
        
        Args:
            energy_j: Energy in Joules
            regions: Dict of region -> carbon_intensity
                {'eu-west-2': 250, 'eu-north-1': 15, ...}
        
        Returns:
        {
            'energy_j': float,
            'regions': {
                'eu-west-2': {'carbon_g': float, 'carbon_intensity': float},
                'eu-north-1': {'carbon_g': float, 'carbon_intensity': float},
                ...
            },
            'best_region': str,
            'worst_region': str,
            'savings_percent': float
        }
        """
        energy_kwh = energy_j / self.JOULES_PER_KWH
        
        region_results = {}
        for region, carbon_intensity in regions.items():
            carbon_g = energy_kwh * carbon_intensity
            region_results[region] = {
                'carbon_g': carbon_g,
                'carbon_intensity': carbon_intensity
            }
        
        # Find best and worst
        best_region = min(region_results.items(), key=lambda x: x[1]['carbon_g'])[0]
        worst_region = max(region_results.items(), key=lambda x: x[1]['carbon_g'])[0]
        
        best_carbon = region_results[best_region]['carbon_g']
        worst_carbon = region_results[worst_region]['carbon_g']
        
        savings_percent = ((worst_carbon - best_carbon) / worst_carbon * 100) if worst_carbon > 0 else 0
        
        return {
            'energy_j': energy_j,
            'energy_kwh': energy_kwh,
            'regions': region_results,
            'best_region': best_region,
            'worst_region': worst_region,
            'savings_g': worst_carbon - best_carbon,
            'savings_percent': savings_percent
        }
    
    def format_carbon(self, carbon_g: float, precision: int = 2) -> str:
        """
        Format carbon emissions in human-readable format.
        
        Returns:
        - "0.12 g" for < 1g
        - "1.5 g" for 1-1000g
        - "1.2 kg" for > 1000g
        """
        if carbon_g < 1:
            return f"{carbon_g:.{precision}f} g"
        elif carbon_g < 1000:
            return f"{carbon_g:.{precision}f} g"
        else:
            return f"{carbon_g / 1000:.{precision}f} kg"
    
    def format_equivalent(self, carbon_g: float) -> str:
        """
        Format carbon as most relevant equivalent.
        
        Returns human-friendly string like:
        - "0.5 smartphone charges"
        - "2.3 miles driven"
        - "0.001 trees needed"
        """
        equivalents = self._calculate_equivalents(carbon_g)
        
        if carbon_g < 10:
            # Small amounts: smartphone charges
            charges = equivalents['smartphone_charges']
            return f"{charges:.1f} smartphone charge{'s' if charges != 1 else ''}"
        elif carbon_g < 1000:
            # Medium amounts: miles driven
            miles = equivalents['miles_driven']
            return f"{miles:.2f} mile{'s' if miles != 1 else ''} driven"
        else:
            # Large amounts: trees needed
            trees = equivalents['trees_needed']
            return f"{trees:.3f} tree{'s' if trees != 1 else ''} needed (per year)"


# Singleton instance
_carbon_converter = None

def get_carbon_converter() -> CarbonConverter:
    """Get global carbon converter instance (singleton)"""
    global _carbon_converter
    if _carbon_converter is None:
        _carbon_converter = CarbonConverter()
    return _carbon_converter


# Convenience functions
def joules_to_carbon(energy_j: float, carbon_intensity: float, region: str = None) -> Dict:
    """Quick conversion from Joules to carbon"""
    converter = get_carbon_converter()
    return converter.joules_to_carbon(energy_j, carbon_intensity, region)


def format_carbon(carbon_g: float) -> str:
    """Quick format carbon emissions"""
    converter = get_carbon_converter()
    return converter.format_carbon(carbon_g)


def format_equivalent(carbon_g: float) -> str:
    """Quick format carbon equivalent"""
    converter = get_carbon_converter()
    return converter.format_equivalent(carbon_g)
