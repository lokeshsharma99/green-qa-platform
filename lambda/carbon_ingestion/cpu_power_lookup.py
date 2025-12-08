"""
CPU Power Lookup Module

Uses CarbonTracker's CPU power database to get accurate TDP values
for carbon emission calculations.

Data source: carbontracker/carbontracker/data/cpu_power.csv
Contains 3,925+ CPU models with TDP (Thermal Design Power) values.
"""

import csv
import os
import re
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class CPUPowerLookup:
    """
    Lookup CPU TDP (Thermal Design Power) values for accurate carbon calculations.
    
    TDP represents the maximum power a CPU can consume under load.
    Actual power = TDP × CPU utilization
    """
    
    def __init__(self, csv_path: Optional[str] = None):
        """
        Initialize CPU power lookup.
        
        Args:
            csv_path: Path to cpu_power.csv. If None, uses default location.
        """
        if csv_path is None:
            # Default path - go up to workspace root, then to carbontracker
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # From: green-qa-platform/lambda/carbon_ingestion
            # To: carbontracker/carbontracker/data/cpu_power.csv
            workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            csv_path = os.path.join(
                workspace_root,
                'carbontracker', 
                'carbontracker', 
                'data', 
                'cpu_power.csv'
            )
        
        self.csv_path = csv_path
        self.cpu_data: Dict[str, int] = {}
        self._load_data()
    
    def _load_data(self):
        """Load CPU power data from CSV."""
        try:
            if not os.path.exists(self.csv_path):
                logger.warning(f"CPU power CSV not found at {self.csv_path}")
                return
            
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row['Name'].strip().lower()
                    try:
                        # Handle both integer and decimal TDP values
                        tdp = int(float(row['TDP']))
                        self.cpu_data[name] = tdp
                    except (ValueError, KeyError) as e:
                        logger.debug(f"Skipping invalid row: {row} - {e}")
                        continue
            
            logger.info(f"Loaded {len(self.cpu_data)} CPU power values")
        
        except Exception as e:
            logger.error(f"Error loading CPU power data: {e}")
    
    def get_tdp(self, cpu_model: str) -> Optional[int]:
        """
        Get TDP for a specific CPU model.
        
        Args:
            cpu_model: CPU model name (e.g., "Intel Xeon 6140", "AMD EPYC 7742")
            
        Returns:
            TDP in Watts, or None if not found
        """
        if not self.cpu_data:
            return None
        
        # Normalize input
        normalized = cpu_model.strip().lower()
        
        # Direct lookup
        if normalized in self.cpu_data:
            return self.cpu_data[normalized]
        
        # Try extracting model number
        # e.g., "Intel Xeon 6140" -> "6140"
        model_match = re.search(r'\b(\d{4}[a-z]*)\b', normalized)
        if model_match:
            model_num = model_match.group(1)
            if model_num in self.cpu_data:
                return self.cpu_data[model_num]
        
        # Try partial match
        for cpu_name, tdp in self.cpu_data.items():
            if cpu_name in normalized or normalized in cpu_name:
                logger.info(f"Partial match: {cpu_model} -> {cpu_name} ({tdp}W)")
                return tdp
        
        logger.debug(f"No TDP found for CPU: {cpu_model}")
        return None
    
    def get_tdp_with_fallback(
        self, 
        cpu_model: str, 
        instance_type: Optional[str] = None
    ) -> int:
        """
        Get TDP with intelligent fallback based on instance type.
        
        Args:
            cpu_model: CPU model name
            instance_type: AWS instance type (e.g., "m5.large")
            
        Returns:
            TDP in Watts (always returns a value)
        """
        # Try direct lookup
        tdp = self.get_tdp(cpu_model)
        if tdp:
            return tdp
        
        # Fallback based on instance type
        if instance_type:
            return self._estimate_from_instance_type(instance_type)
        
        # Default fallback
        return 100  # Conservative estimate
    
    def _estimate_from_instance_type(self, instance_type: str) -> int:
        """
        Estimate TDP from AWS instance type.
        
        Based on typical CPU configurations for each instance family.
        """
        instance_type = instance_type.lower()
        
        # Extract family (e.g., "m5" from "m5.large")
        family_match = re.match(r'^([a-z]\d+[a-z]?)', instance_type)
        if not family_match:
            return 100
        
        family = family_match.group(1)
        
        # Instance family TDP estimates
        # Based on typical CPUs used in each family
        family_tdp = {
            # General purpose
            't2': 45,   # Burstable, low power
            't3': 45,
            't4g': 40,  # ARM Graviton
            'm5': 115,  # Intel Xeon Platinum
            'm6i': 115,
            'm6a': 180, # AMD EPYC
            'm6g': 105, # ARM Graviton2
            'm7g': 105, # ARM Graviton3
            
            # Compute optimized
            'c5': 140,  # Intel Xeon Platinum
            'c6i': 140,
            'c6a': 225, # AMD EPYC
            'c6g': 105, # ARM Graviton2
            'c7g': 105, # ARM Graviton3
            
            # Memory optimized
            'r5': 140,
            'r6i': 140,
            'r6a': 225,
            'r6g': 105,
            'r7g': 105,
            'x1': 165,  # High memory
            'x2': 165,
            
            # Storage optimized
            'i3': 140,
            'i4i': 140,
            'd2': 115,
            'd3': 115,
            
            # Accelerated computing
            'p3': 165,  # GPU instances (CPU only)
            'p4': 280,
            'g4': 140,
            'g5': 165,
            'inf1': 115,
        }
        
        return family_tdp.get(family, 100)
    
    def calculate_power_consumption(
        self,
        cpu_model: str,
        cpu_utilization: float,
        instance_type: Optional[str] = None,
        num_cpus: int = 1
    ) -> float:
        """
        Calculate actual power consumption.
        
        Args:
            cpu_model: CPU model name
            cpu_utilization: CPU utilization (0.0 to 1.0)
            instance_type: AWS instance type for fallback
            num_cpus: Number of CPUs/cores
            
        Returns:
            Power consumption in Watts
        """
        tdp = self.get_tdp_with_fallback(cpu_model, instance_type)
        
        # Actual power = TDP × utilization × number of CPUs
        # Add 10% for idle power consumption
        idle_power = tdp * 0.1
        active_power = tdp * cpu_utilization
        
        total_power = (idle_power + active_power) * num_cpus
        
        return round(total_power, 2)
    
    def calculate_carbon_emissions(
        self,
        cpu_model: str,
        cpu_utilization: float,
        duration_hours: float,
        carbon_intensity: float,
        instance_type: Optional[str] = None,
        num_cpus: int = 1
    ) -> Dict[str, float]:
        """
        Calculate carbon emissions for a workload.
        
        Args:
            cpu_model: CPU model name
            cpu_utilization: CPU utilization (0.0 to 1.0)
            duration_hours: Workload duration in hours
            carbon_intensity: Grid carbon intensity (gCO2/kWh)
            instance_type: AWS instance type for fallback
            num_cpus: Number of CPUs
            
        Returns:
            Dict with emissions breakdown
        """
        # Calculate power consumption
        power_watts = self.calculate_power_consumption(
            cpu_model, 
            cpu_utilization, 
            instance_type, 
            num_cpus
        )
        
        # Convert to kWh
        energy_kwh = (power_watts / 1000) * duration_hours
        
        # Calculate emissions
        emissions_gco2 = energy_kwh * carbon_intensity
        
        return {
            'cpu_model': cpu_model,
            'tdp_watts': self.get_tdp_with_fallback(cpu_model, instance_type),
            'power_consumption_watts': power_watts,
            'energy_consumption_kwh': round(energy_kwh, 4),
            'carbon_emissions_gco2': round(emissions_gco2, 2),
            'carbon_emissions_kgco2': round(emissions_gco2 / 1000, 4),
            'duration_hours': duration_hours,
            'carbon_intensity_gco2_kwh': carbon_intensity,
            'cpu_utilization': cpu_utilization,
            'num_cpus': num_cpus
        }
    
    def get_stats(self) -> Dict:
        """Get statistics about loaded CPU data."""
        if not self.cpu_data:
            return {'loaded': False}
        
        tdp_values = list(self.cpu_data.values())
        
        return {
            'loaded': True,
            'total_cpus': len(self.cpu_data),
            'min_tdp': min(tdp_values),
            'max_tdp': max(tdp_values),
            'avg_tdp': round(sum(tdp_values) / len(tdp_values), 1),
            'csv_path': self.csv_path
        }


# Singleton instance
_cpu_lookup = None

def get_cpu_lookup() -> CPUPowerLookup:
    """Get singleton CPU lookup instance."""
    global _cpu_lookup
    if _cpu_lookup is None:
        _cpu_lookup = CPUPowerLookup()
    return _cpu_lookup


if __name__ == '__main__':
    # Test the lookup
    print("=== CPU Power Lookup Test ===\n")
    
    lookup = CPUPowerLookup()
    stats = lookup.get_stats()
    
    print(f"Loaded: {stats['loaded']}")
    if stats['loaded']:
        print(f"Total CPUs: {stats['total_cpus']}")
        print(f"TDP Range: {stats['min_tdp']}W - {stats['max_tdp']}W")
        print(f"Average TDP: {stats['avg_tdp']}W")
        print()
        
        # Test some lookups
        test_cpus = [
            "6140",
            "Intel Xeon 6140",
            "EPYC 7742",
            "m5.large",  # Should use fallback
        ]
        
        print("Test Lookups:")
        for cpu in test_cpus:
            tdp = lookup.get_tdp_with_fallback(cpu, "m5.large")
            print(f"  {cpu}: {tdp}W")
        
        print()
        
        # Test carbon calculation
        print("Carbon Calculation Example:")
        result = lookup.calculate_carbon_emissions(
            cpu_model="6140",
            cpu_utilization=0.7,
            duration_hours=1.0,
            carbon_intensity=250,  # gCO2/kWh
            num_cpus=2
        )
        
        for key, value in result.items():
            print(f"  {key}: {value}")
