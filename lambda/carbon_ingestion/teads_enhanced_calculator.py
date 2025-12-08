"""
Enhanced Carbon Calculator with Teads Methodology + CPU Power Lookup
Incorporates load-level profiling and component-based embodied emissions

Based on:
- Teads Engineering EC2 Carbon Dataset (2021)
- Cloud Carbon Footprint methodology
- Dell PowerEdge R740 LCA
- CarbonTracker CPU Power Database (3,918 CPUs)
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

# Import CPU power lookup
try:
    from cpu_power_lookup import get_cpu_lookup
    CPU_LOOKUP_AVAILABLE = True
except ImportError:
    CPU_LOOKUP_AVAILABLE = False
    logging.warning("CPU power lookup not available")

logger = logging.getLogger(__name__)


class LoadLevel(Enum):
    """CPU load levels from Teads methodology"""
    IDLE = 'idle'
    LOW = 'low'        # ~10% utilization
    MEDIUM = 'medium'  # ~50% utilization
    HIGH = 'high'      # ~100% utilization


# Teads Load Profiles (Watts per Watt TDP)
# Source: https://medium.com/teads-engineering/building-an-aws-ec2-carbon-emissions-dataset-3f0fd76c98ac
TEADS_LOAD_PROFILES = {
    LoadLevel.IDLE: 0.12,    # 12% of TDP at idle
    LoadLevel.LOW: 0.25,     # 25% of TDP at 10% load
    LoadLevel.MEDIUM: 0.75,  # 75% of TDP at 50% load
    LoadLevel.HIGH: 1.00     # 100% of TDP at full load
}

# vCPU TDP (Thermal Design Power) in Watts
VCPU_TDP_WATTS = {
    'intel_xeon': 10.0,      # Intel Xeon Scalable (most common)
    'amd_epyc': 8.5,         # AMD EPYC
    'aws_graviton2': 7.0,    # AWS Graviton2 (ARM)
    'aws_graviton3': 6.5,    # AWS Graviton3 (improved)
    'default': 10.0
}

# Memory coefficient (kWh per GB-hour)
# Source: Cloud Carbon Footprint / Etsy Cloud Jewels
MEMORY_COEFFICIENT_KWH_PER_GB = 0.000392

# PUE (Power Usage Effectiveness)
CLOUD_PUE = {
    'aws': 1.135,
    'gcp': 1.10,
    'azure': 1.185
}

# Teads "Other Components" Factor
# Accounts for fans, storage, network cards not measured by RAPL
# Source: Teads on-premise validation (15-20% of CPU TDP)
OTHER_COMPONENTS_FACTOR = 0.20


@dataclass
class InstanceConfig:
    """EC2 instance configuration"""
    vcpu_count: int
    memory_gb: float
    cpu_type: str = 'intel_xeon'
    storage_drives: int = 0  # Number of NVMe SSDs
    gpu_count: int = 0
    provider: str = 'aws'
    cpu_model: Optional[str] = None  # Specific CPU model (e.g., "Xeon 6140")
    instance_type: Optional[str] = None  # AWS instance type (e.g., "m5.large")


@dataclass
class EmbodiedConfig:
    """Embodied emissions configuration (kg CO2eq)"""
    baseline_server: float = 1000.0  # Minimal server (1 CPU, 16 GB RAM)
    additional_cpu: float = 200.0    # Per extra CPU socket
    memory_per_32gb: float = 100.0   # Per 32 GB DRAM
    nvme_ssd: float = 50.0           # Per NVMe drive
    hdd: float = 30.0                # Per HDD
    gpu: float = 200.0               # Per GPU (estimated)
    lifespan_years: float = 4.0      # Server lifespan


class TeadsEnhancedCalculator:
    """
    Enhanced carbon calculator using Teads methodology
    
    Features:
    - Load-level power profiling (idle, low, medium, high)
    - Component-based embodied emissions
    - "Other components" factor for non-CPU/DRAM power
    - Detailed breakdown for transparency
    """
    
    def __init__(self, embodied_config: Optional[EmbodiedConfig] = None):
        self.embodied_config = embodied_config or EmbodiedConfig()
    
    def calculate_cpu_power(
        self,
        vcpu_count: int,
        cpu_type: str,
        load_level: LoadLevel,
        cpu_model: Optional[str] = None,
        instance_type: Optional[str] = None
    ) -> Tuple[float, Dict]:
        """
        Calculate CPU power consumption at specific load level
        
        Enhanced with CPU power lookup for accurate TDP values.
        Falls back to Teads estimates if CPU model not found.
        
        Returns: (Power in Watts, metadata dict)
        """
        metadata = {
            'method': 'teads_estimate',
            'cpu_model': cpu_model,
            'instance_type': instance_type
        }
        
        # Try CPU power lookup first
        if CPU_LOOKUP_AVAILABLE and (cpu_model or instance_type):
            try:
                lookup = get_cpu_lookup()
                
                # Get TDP for the specific CPU
                if cpu_model:
                    tdp_total = lookup.get_tdp_with_fallback(cpu_model, instance_type)
                else:
                    tdp_total = lookup._estimate_from_instance_type(instance_type)
                
                if tdp_total:
                    # TDP is for the whole CPU, divide by vCPUs for per-vCPU
                    # Assume physical CPU has 8-32 cores, use conservative 16
                    cores_per_cpu = 16
                    num_physical_cpus = max(1, vcpu_count // cores_per_cpu)
                    
                    # Total TDP for all CPUs
                    total_tdp = tdp_total * num_physical_cpus
                    
                    # Apply load factor
                    load_factor = TEADS_LOAD_PROFILES[load_level]
                    power = total_tdp * load_factor
                    
                    metadata['method'] = 'cpu_lookup'
                    metadata['tdp_per_cpu'] = tdp_total
                    metadata['num_physical_cpus'] = num_physical_cpus
                    metadata['total_tdp'] = total_tdp
                    
                    logger.info(f"Using CPU lookup: {cpu_model or instance_type} = {tdp_total}W TDP")
                    return power, metadata
            
            except Exception as e:
                logger.warning(f"CPU lookup failed, using Teads estimate: {e}")
        
        # Fallback to Teads per-vCPU estimates
        tdp_per_vcpu = VCPU_TDP_WATTS.get(cpu_type, VCPU_TDP_WATTS['default'])
        load_factor = TEADS_LOAD_PROFILES[load_level]
        power = vcpu_count * tdp_per_vcpu * load_factor
        
        metadata['tdp_per_vcpu'] = tdp_per_vcpu
        
        return power, metadata
    
    def calculate_memory_power(
        self,
        memory_gb: float,
        duration_hours: float
    ) -> float:
        """
        Calculate memory power consumption
        
        Returns: Energy in kWh
        """
        return memory_gb * duration_hours * MEMORY_COEFFICIENT_KWH_PER_GB
    
    def calculate_other_components_power(
        self,
        vcpu_count: int,
        cpu_type: str
    ) -> float:
        """
        Calculate power for "other components" (fans, storage, network)
        
        Uses Teads heuristic: 20% of CPU TDP
        
        Returns: Power in Watts
        """
        tdp_per_vcpu = VCPU_TDP_WATTS.get(cpu_type, VCPU_TDP_WATTS['default'])
        total_cpu_tdp = vcpu_count * tdp_per_vcpu
        
        return total_cpu_tdp * OTHER_COMPONENTS_FACTOR
    
    def calculate_total_power(
        self,
        instance: InstanceConfig,
        load_level: LoadLevel,
        duration_hours: float
    ) -> Dict[str, float]:
        """
        Calculate total power consumption with detailed breakdown
        
        Enhanced with CPU power lookup for accurate calculations.
        
        Returns: Dict with power breakdown in Watts and energy in kWh
        """
        # CPU power (Watts) - now returns metadata too
        cpu_power_w, cpu_metadata = self.calculate_cpu_power(
            instance.vcpu_count,
            instance.cpu_type,
            load_level,
            instance.cpu_model,
            instance.instance_type
        )
        
        # Memory energy (kWh)
        memory_energy_kwh = self.calculate_memory_power(
            instance.memory_gb,
            duration_hours
        )
        
        # Convert memory to average power (Watts)
        memory_power_w = (memory_energy_kwh / duration_hours) * 1000 if duration_hours > 0 else 0
        
        # Other components (Watts)
        other_power_w = self.calculate_other_components_power(
            instance.vcpu_count,
            instance.cpu_type
        )
        
        # Total power before PUE (Watts)
        total_power_w = cpu_power_w + memory_power_w + other_power_w
        
        # Total energy before PUE (kWh)
        total_energy_kwh = (total_power_w * duration_hours) / 1000
        
        # Apply PUE
        pue = CLOUD_PUE.get(instance.provider, 1.135)
        total_energy_with_pue_kwh = total_energy_kwh * pue
        
        return {
            'cpu_power_w': round(cpu_power_w, 2),
            'memory_power_w': round(memory_power_w, 2),
            'other_components_power_w': round(other_power_w, 2),
            'total_power_w': round(total_power_w, 2),
            'cpu_energy_kwh': round((cpu_power_w * duration_hours) / 1000, 6),
            'memory_energy_kwh': round(memory_energy_kwh, 6),
            'other_energy_kwh': round((other_power_w * duration_hours) / 1000, 6),
            'total_energy_kwh': round(total_energy_kwh, 6),
            'pue': pue,
            'total_energy_with_pue_kwh': round(total_energy_with_pue_kwh, 6),
            'load_level': load_level.value,
            'load_factor': TEADS_LOAD_PROFILES[load_level],
            'cpu_calculation_method': cpu_metadata['method'],
            'cpu_metadata': cpu_metadata
        }
    
    def calculate_embodied_emissions(
        self,
        instance: InstanceConfig,
        duration_hours: float
    ) -> Dict[str, float]:
        """
        Calculate embodied emissions using Teads component-based approach
        
        Returns: Dict with embodied emissions breakdown in gCO2
        """
        config = self.embodied_config
        
        # Baseline server (1 CPU, 16 GB RAM, Nitro cards)
        baseline_kg = config.baseline_server
        
        # Additional CPUs (assuming 1 CPU per 8-16 vCPUs)
        # Conservative: 1 extra CPU per 16 vCPUs beyond first 8
        extra_cpus = max(0, (instance.vcpu_count - 8) // 16)
        cpu_kg = extra_cpus * config.additional_cpu
        
        # Additional memory beyond 16 GB baseline
        extra_memory_gb = max(0, instance.memory_gb - 16)
        memory_32gb_units = extra_memory_gb / 32
        memory_kg = memory_32gb_units * config.memory_per_32gb
        
        # Storage drives
        storage_kg = instance.storage_drives * config.nvme_ssd
        
        # GPUs
        gpu_kg = instance.gpu_count * config.gpu
        
        # Total manufacturing emissions
        total_manufacturing_kg = baseline_kg + cpu_kg + memory_kg + storage_kg + gpu_kg
        
        # Amortize over lifespan
        lifespan_hours = config.lifespan_years * 8760
        embodied_per_hour_g = (total_manufacturing_kg * 1000) / lifespan_hours
        
        # For this duration
        total_embodied_g = embodied_per_hour_g * duration_hours
        
        return {
            'baseline_kg': baseline_kg,
            'additional_cpu_kg': cpu_kg,
            'memory_kg': memory_kg,
            'storage_kg': storage_kg,
            'gpu_kg': gpu_kg,
            'total_manufacturing_kg': round(total_manufacturing_kg, 2),
            'lifespan_hours': lifespan_hours,
            'embodied_per_hour_g': round(embodied_per_hour_g, 4),
            'total_embodied_g': round(total_embodied_g, 4)
        }
    
    def calculate_operational_emissions(
        self,
        energy_kwh: float,
        carbon_intensity: float
    ) -> float:
        """
        Calculate operational emissions
        
        Returns: Emissions in gCO2
        """
        return energy_kwh * carbon_intensity
    
    def calculate_full_footprint(
        self,
        instance: InstanceConfig,
        duration_seconds: float,
        carbon_intensity: float,
        load_level: LoadLevel = LoadLevel.MEDIUM
    ) -> Dict:
        """
        Calculate complete carbon footprint with Teads methodology
        
        Args:
            instance: Instance configuration
            duration_seconds: Test duration in seconds
            carbon_intensity: Grid carbon intensity (gCO2/kWh)
            load_level: Expected CPU load level
        
        Returns: Complete carbon footprint breakdown
        """
        duration_hours = duration_seconds / 3600
        
        # Power and energy calculation
        power_breakdown = self.calculate_total_power(
            instance,
            load_level,
            duration_hours
        )
        
        # Operational emissions
        operational_g = self.calculate_operational_emissions(
            power_breakdown['total_energy_with_pue_kwh'],
            carbon_intensity
        )
        
        # Embodied emissions
        embodied_breakdown = self.calculate_embodied_emissions(
            instance,
            duration_hours
        )
        
        # Total emissions
        total_g = operational_g + embodied_breakdown['total_embodied_g']
        
        # SCI score (per functional unit = 1 test run)
        sci = total_g
        
        return {
            'duration_seconds': duration_seconds,
            'duration_hours': round(duration_hours, 4),
            'instance': {
                'vcpu_count': instance.vcpu_count,
                'memory_gb': instance.memory_gb,
                'cpu_type': instance.cpu_type,
                'storage_drives': instance.storage_drives,
                'gpu_count': instance.gpu_count,
                'provider': instance.provider
            },
            'power_breakdown': power_breakdown,
            'carbon_intensity_gco2_kwh': carbon_intensity,
            'operational_emissions_g': round(operational_g, 4),
            'embodied_breakdown': embodied_breakdown,
            'total_emissions_g': round(total_g, 4),
            'total_emissions_kg': round(total_g / 1000, 6),
            'sci_gco2': round(sci, 4),
            'methodology': {
                'power_calculation': 'Teads load-level profiling',
                'embodied_calculation': 'Component-based amortization',
                'other_components_factor': OTHER_COMPONENTS_FACTOR,
                'sources': [
                    'Teads Engineering EC2 Dataset',
                    'Cloud Carbon Footprint',
                    'Dell R740 LCA'
                ]
            }
        }
    
    def compare_load_levels(
        self,
        instance: InstanceConfig,
        duration_seconds: float,
        carbon_intensity: float
    ) -> Dict:
        """
        Compare carbon footprint across different load levels
        
        Useful for understanding impact of load optimization
        """
        results = {}
        
        for load_level in LoadLevel:
            footprint = self.calculate_full_footprint(
                instance,
                duration_seconds,
                carbon_intensity,
                load_level
            )
            
            results[load_level.value] = {
                'total_emissions_g': footprint['total_emissions_g'],
                'operational_g': footprint['operational_emissions_g'],
                'embodied_g': footprint['embodied_breakdown']['total_embodied_g'],
                'power_w': footprint['power_breakdown']['total_power_w'],
                'energy_kwh': footprint['power_breakdown']['total_energy_with_pue_kwh']
            }
        
        # Calculate savings potential
        high_load = results['high']['total_emissions_g']
        medium_load = results['medium']['total_emissions_g']
        low_load = results['low']['total_emissions_g']
        
        savings = {
            'high_to_medium_percent': round(((high_load - medium_load) / high_load) * 100, 1),
            'high_to_low_percent': round(((high_load - low_load) / high_load) * 100, 1),
            'medium_to_low_percent': round(((medium_load - low_load) / medium_load) * 100, 1)
        }
        
        return {
            'load_levels': results,
            'savings_potential': savings,
            'recommendation': 'Run tests at lower load levels when possible to reduce carbon footprint'
        }


def calculate_instance_comparison(
    instances: list,
    duration_seconds: float,
    carbon_intensity: float,
    load_level: LoadLevel = LoadLevel.MEDIUM
) -> Dict:
    """
    Compare carbon footprint across different instance types
    
    Args:
        instances: List of InstanceConfig objects
        duration_seconds: Test duration
        carbon_intensity: Grid carbon intensity
        load_level: Expected load level
    
    Returns: Comparison results with recommendations
    """
    calculator = TeadsEnhancedCalculator()
    results = []
    
    for instance in instances:
        footprint = calculator.calculate_full_footprint(
            instance,
            duration_seconds,
            carbon_intensity,
            load_level
        )
        
        results.append({
            'instance_name': f"{instance.cpu_type}_{instance.vcpu_count}vcpu_{instance.memory_gb}gb",
            'total_emissions_g': footprint['total_emissions_g'],
            'operational_g': footprint['operational_emissions_g'],
            'embodied_g': footprint['embodied_breakdown']['total_embodied_g'],
            'power_w': footprint['power_breakdown']['total_power_w'],
            'instance': instance
        })
    
    # Sort by total emissions
    results.sort(key=lambda x: x['total_emissions_g'])
    
    # Calculate savings vs worst
    worst_emissions = results[-1]['total_emissions_g']
    best_emissions = results[0]['total_emissions_g']
    
    for result in results:
        result['savings_vs_worst_percent'] = round(
            ((worst_emissions - result['total_emissions_g']) / worst_emissions) * 100,
            1
        )
    
    return {
        'instances': results,
        'best_instance': results[0]['instance_name'],
        'worst_instance': results[-1]['instance_name'],
        'max_savings_percent': round(((worst_emissions - best_emissions) / worst_emissions) * 100, 1),
        'recommendation': f"Use {results[0]['instance_name']} for lowest carbon footprint"
    }


# Example usage
if __name__ == '__main__':
    print("=== Teads Enhanced Carbon Calculator ===\n")
    
    # Example 1: Single calculation with load profiling
    print("1. Single instance calculation (c5.2xlarge equivalent)")
    instance = InstanceConfig(
        vcpu_count=8,
        memory_gb=16,
        cpu_type='intel_xeon',
        storage_drives=1,
        provider='aws'
    )
    
    calculator = TeadsEnhancedCalculator()
    footprint = calculator.calculate_full_footprint(
        instance=instance,
        duration_seconds=3600,  # 1 hour
        carbon_intensity=250,   # gCO2/kWh
        load_level=LoadLevel.MEDIUM
    )
    
    print(f"   Total emissions: {footprint['total_emissions_g']:.2f} gCO2")
    print(f"   - Operational: {footprint['operational_emissions_g']:.2f} gCO2")
    print(f"   - Embodied: {footprint['embodied_breakdown']['total_embodied_g']:.2f} gCO2")
    print(f"   Power: {footprint['power_breakdown']['total_power_w']:.2f} W")
    print(f"   Load level: {footprint['power_breakdown']['load_level']}")
    
    # Example 2: Load level comparison
    print("\n2. Load level comparison")
    comparison = calculator.compare_load_levels(
        instance=instance,
        duration_seconds=3600,
        carbon_intensity=250
    )
    
    for level, data in comparison['load_levels'].items():
        print(f"   {level:8s}: {data['total_emissions_g']:7.2f} gCO2 ({data['power_w']:6.2f} W)")
    
    print(f"\n   Savings potential:")
    print(f"   - High to Medium: {comparison['savings_potential']['high_to_medium_percent']}%")
    print(f"   - High to Low: {comparison['savings_potential']['high_to_low_percent']}%")
    
    # Example 3: Instance type comparison
    print("\n3. Instance type comparison (Intel vs Graviton)")
    instances = [
        InstanceConfig(vcpu_count=4, memory_gb=8, cpu_type='intel_xeon', provider='aws'),
        InstanceConfig(vcpu_count=4, memory_gb=8, cpu_type='aws_graviton2', provider='aws'),
        InstanceConfig(vcpu_count=4, memory_gb=8, cpu_type='amd_epyc', provider='aws'),
    ]
    
    comparison = calculate_instance_comparison(
        instances=instances,
        duration_seconds=3600,
        carbon_intensity=250,
        load_level=LoadLevel.MEDIUM
    )
    
    for result in comparison['instances']:
        print(f"   {result['instance_name']:30s}: {result['total_emissions_g']:7.2f} gCO2 "
              f"(saves {result['savings_vs_worst_percent']:4.1f}%)")
    
    print(f"\n   Recommendation: {comparison['recommendation']}")
    
    print("\n=== Tests complete ===")
