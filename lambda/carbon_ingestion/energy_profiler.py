"""
Energy Profiler - Identify Energy Hotspots

Provides detailed profiling of workloads to identify energy-intensive operations.
Inspired by Green Metrics Tool's profiling capabilities.

Features:
- Component-level breakdown (CPU, Memory, GPU, Disk, Network)
- Phase-based analysis
- Hotspot identification
- Optimization recommendations
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class EnergyProfile:
    """Represents an energy profile for a workload"""
    
    def __init__(self, workload_id: str, name: str):
        self.workload_id = workload_id
        self.name = name
        self.phases = []
        self.total_energy_j = 0
        self.breakdown = {
            'cpu_j': 0,
            'memory_j': 0,
            'gpu_j': 0,
            'disk_j': 0,
            'network_j': 0
        }
        self.hotspots = []
        self.timestamp = datetime.utcnow().isoformat()
    
    def add_phase(self, phase: Dict):
        """Add a measurement phase"""
        self.phases.append(phase)
        self.total_energy_j += phase.get('energy_j', 0)
        
        # Update breakdown
        for component in self.breakdown.keys():
            self.breakdown[component] += phase.get(component, 0)
    
    def identify_hotspots(self, threshold_percent: float = 20.0):
        """
        Identify energy hotspots (phases consuming >threshold% of total energy)
        """
        if self.total_energy_j == 0:
            return []
        
        self.hotspots = []
        for phase in self.phases:
            phase_energy = phase.get('energy_j', 0)
            percentage = (phase_energy / self.total_energy_j) * 100
            
            if percentage >= threshold_percent:
                self.hotspots.append({
                    'phase_name': phase.get('name', 'unknown'),
                    'energy_j': phase_energy,
                    'percentage': percentage,
                    'duration_s': phase.get('duration_s', 0),
                    'power_w': phase_energy / phase.get('duration_s', 1),
                    'recommendation': self._generate_recommendation(phase)
                })
        
        # Sort by energy consumption
        self.hotspots.sort(key=lambda x: x['energy_j'], reverse=True)
        return self.hotspots
    
    def _generate_recommendation(self, phase: Dict) -> str:
        """Generate optimization recommendation for a phase"""
        phase_name = phase.get('name', '').lower()
        
        # CPU-intensive
        if phase.get('cpu_j', 0) > phase.get('energy_j', 1) * 0.6:
            return "CPU-intensive: Consider algorithm optimization or parallelization"
        
        # Memory-intensive
        if phase.get('memory_j', 0) > phase.get('energy_j', 1) * 0.3:
            return "Memory-intensive: Consider reducing memory allocations or using streaming"
        
        # GPU-intensive
        if phase.get('gpu_j', 0) > phase.get('energy_j', 1) * 0.5:
            return "GPU-intensive: Consider batch size optimization or model quantization"
        
        # Disk I/O intensive
        if phase.get('disk_j', 0) > phase.get('energy_j', 1) * 0.2:
            return "Disk I/O intensive: Consider caching or reducing file operations"
        
        # Network intensive
        if phase.get('network_j', 0) > phase.get('energy_j', 1) * 0.2:
            return "Network intensive: Consider compression or reducing API calls"
        
        return "General optimization: Profile individual operations for bottlenecks"
    
    def get_component_breakdown(self) -> Dict:
        """Get percentage breakdown by component"""
        if self.total_energy_j == 0:
            return {k: 0.0 for k in self.breakdown.keys()}
        
        return {
            component: (energy / self.total_energy_j) * 100
            for component, energy in self.breakdown.items()
        }
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'workload_id': self.workload_id,
            'name': self.name,
            'total_energy_j': self.total_energy_j,
            'breakdown': self.breakdown,
            'breakdown_percent': self.get_component_breakdown(),
            'phases': self.phases,
            'hotspots': self.hotspots,
            'timestamp': self.timestamp
        }


class EnergyProfiler:
    """
    Energy profiler for identifying optimization opportunities.
    
    Features:
    - Phase-based profiling
    - Component breakdown
    - Hotspot identification
    - Optimization recommendations
    - Comparison between runs
    
    Example:
        profiler = EnergyProfiler()
        
        # Start profiling
        profile = profiler.start_profile('test-run-1', 'Test Suite')
        
        # Add phases
        profiler.add_phase(profile, {
            'name': 'setup',
            'energy_j': 100,
            'cpu_j': 80,
            'memory_j': 20,
            'duration_s': 5
        })
        
        # Identify hotspots
        hotspots = profiler.identify_hotspots(profile)
        print(f"Found {len(hotspots)} hotspots")
    """
    
    def __init__(self):
        self.profiles = {}
        self.config = {
            'hotspot_threshold_percent': 20.0,
            'min_phase_duration_s': 1.0,
            'enable_recommendations': True
        }
    
    def start_profile(self, workload_id: str, name: str) -> EnergyProfile:
        """Start a new energy profile"""
        profile = EnergyProfile(workload_id, name)
        self.profiles[workload_id] = profile
        logger.info(f"Started energy profile: {name} ({workload_id})")
        return profile
    
    def add_phase(self, profile: EnergyProfile, phase_data: Dict):
        """Add a measurement phase to the profile"""
        # Validate phase data
        if phase_data.get('duration_s', 0) < self.config['min_phase_duration_s']:
            logger.debug(f"Skipping short phase: {phase_data.get('name')}")
            return
        
        profile.add_phase(phase_data)
        logger.debug(f"Added phase: {phase_data.get('name')} - {phase_data.get('energy_j')} J")
    
    def identify_hotspots(
        self,
        profile: EnergyProfile,
        threshold_percent: Optional[float] = None
    ) -> List[Dict]:
        """Identify energy hotspots in the profile"""
        threshold = threshold_percent or self.config['hotspot_threshold_percent']
        hotspots = profile.identify_hotspots(threshold)
        
        logger.info(f"Identified {len(hotspots)} hotspots in {profile.name}")
        return hotspots
    
    def compare_profiles(
        self,
        profile1: EnergyProfile,
        profile2: EnergyProfile
    ) -> Dict:
        """
        Compare two energy profiles (e.g., before/after optimization).
        
        Returns:
        {
            'total_energy_diff_j': float,
            'total_energy_diff_percent': float,
            'component_diffs': dict,
            'phase_diffs': list,
            'improvement': bool,
            'summary': str
        }
        """
        total_diff_j = profile2.total_energy_j - profile1.total_energy_j
        total_diff_percent = (total_diff_j / profile1.total_energy_j * 100) if profile1.total_energy_j > 0 else 0
        
        # Component-level comparison
        component_diffs = {}
        for component in profile1.breakdown.keys():
            diff_j = profile2.breakdown[component] - profile1.breakdown[component]
            diff_percent = (diff_j / profile1.breakdown[component] * 100) if profile1.breakdown[component] > 0 else 0
            component_diffs[component] = {
                'diff_j': diff_j,
                'diff_percent': diff_percent,
                'before': profile1.breakdown[component],
                'after': profile2.breakdown[component]
            }
        
        # Phase-level comparison (match by name)
        phase_diffs = []
        phase1_map = {p['name']: p for p in profile1.phases}
        phase2_map = {p['name']: p for p in profile2.phases}
        
        for phase_name in set(phase1_map.keys()) | set(phase2_map.keys()):
            p1 = phase1_map.get(phase_name, {})
            p2 = phase2_map.get(phase_name, {})
            
            e1 = p1.get('energy_j', 0)
            e2 = p2.get('energy_j', 0)
            diff = e2 - e1
            diff_percent = (diff / e1 * 100) if e1 > 0 else 0
            
            phase_diffs.append({
                'phase_name': phase_name,
                'before_j': e1,
                'after_j': e2,
                'diff_j': diff,
                'diff_percent': diff_percent
            })
        
        # Sort by absolute difference
        phase_diffs.sort(key=lambda x: abs(x['diff_j']), reverse=True)
        
        # Generate summary
        improvement = total_diff_j < 0
        summary = self._generate_comparison_summary(
            total_diff_j,
            total_diff_percent,
            improvement,
            component_diffs
        )
        
        return {
            'profile1': profile1.name,
            'profile2': profile2.name,
            'total_energy_diff_j': total_diff_j,
            'total_energy_diff_percent': total_diff_percent,
            'component_diffs': component_diffs,
            'phase_diffs': phase_diffs,
            'improvement': improvement,
            'summary': summary
        }
    
    def _generate_comparison_summary(
        self,
        diff_j: float,
        diff_percent: float,
        improvement: bool,
        component_diffs: Dict
    ) -> str:
        """Generate human-readable comparison summary"""
        if improvement:
            summary = f"✓ Energy reduced by {abs(diff_j):.1f} J ({abs(diff_percent):.1f}%)"
        else:
            summary = f"✗ Energy increased by {diff_j:.1f} J ({diff_percent:.1f}%)"
        
        # Find biggest component change
        biggest_change = max(
            component_diffs.items(),
            key=lambda x: abs(x[1]['diff_j'])
        )
        component_name = biggest_change[0].replace('_j', '').upper()
        component_diff = biggest_change[1]['diff_percent']
        
        summary += f"\nBiggest change: {component_name} ({component_diff:+.1f}%)"
        
        return summary
    
    def generate_report(self, profile: EnergyProfile) -> Dict:
        """
        Generate comprehensive profiling report.
        
        Returns:
        {
            'summary': dict,
            'breakdown': dict,
            'hotspots': list,
            'recommendations': list,
            'phases': list
        }
        """
        hotspots = self.identify_hotspots(profile)
        
        # Generate recommendations
        recommendations = []
        if self.config['enable_recommendations']:
            for hotspot in hotspots[:3]:  # Top 3 hotspots
                recommendations.append({
                    'phase': hotspot['phase_name'],
                    'energy_j': hotspot['energy_j'],
                    'percentage': hotspot['percentage'],
                    'recommendation': hotspot['recommendation']
                })
        
        return {
            'summary': {
                'workload_id': profile.workload_id,
                'name': profile.name,
                'total_energy_j': profile.total_energy_j,
                'total_phases': len(profile.phases),
                'hotspot_count': len(hotspots),
                'timestamp': profile.timestamp
            },
            'breakdown': profile.get_component_breakdown(),
            'hotspots': hotspots,
            'recommendations': recommendations,
            'phases': profile.phases
        }
    
    def get_profile(self, workload_id: str) -> Optional[EnergyProfile]:
        """Get profile by workload ID"""
        return self.profiles.get(workload_id)
    
    def list_profiles(self) -> List[str]:
        """List all profile IDs"""
        return list(self.profiles.keys())


# Singleton instance
_energy_profiler = None

def get_energy_profiler() -> EnergyProfiler:
    """Get global energy profiler instance (singleton)"""
    global _energy_profiler
    if _energy_profiler is None:
        _energy_profiler = EnergyProfiler()
    return _energy_profiler
