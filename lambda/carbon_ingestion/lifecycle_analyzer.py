"""
Software Life Cycle Analysis (SLCA)

Tracks energy consumption across the entire software lifecycle:
- Development (coding, testing)
- Build (compilation, packaging)
- Deployment (container builds, infrastructure)
- Runtime (execution, serving)
- Training vs Inference (AI/ML models)

Inspired by Green Metrics Tool's lifecycle tracking capabilities.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class LifecyclePhase(Enum):
    """Software lifecycle phases"""
    DEVELOPMENT = "development"
    BUILD = "build"
    TEST = "test"
    DEPLOYMENT = "deployment"
    RUNTIME = "runtime"
    TRAINING = "training"
    INFERENCE = "inference"
    MAINTENANCE = "maintenance"


class LifecycleMeasurement:
    """Represents energy measurement for a lifecycle phase"""
    
    def __init__(
        self,
        phase: LifecyclePhase,
        energy_j: float,
        duration_s: float,
        metadata: Optional[Dict] = None
    ):
        self.phase = phase
        self.energy_j = energy_j
        self.duration_s = duration_s
        self.power_w = energy_j / duration_s if duration_s > 0 else 0
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            'phase': self.phase.value,
            'energy_j': self.energy_j,
            'duration_s': self.duration_s,
            'power_w': self.power_w,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }


class LifecycleAnalyzer:
    """
    Analyze energy consumption across software lifecycle.
    
    Features:
    - Track energy per lifecycle phase
    - Compare build vs runtime energy
    - Analyze training vs inference costs
    - Identify lifecycle hotspots
    - Calculate total cost of ownership (TCO)
    
    Example:
        analyzer = LifecycleAnalyzer()
        
        # Record build phase
        analyzer.record_phase(
            phase=LifecyclePhase.BUILD,
            energy_j=5000,
            duration_s=300,
            metadata={'docker_layers': 12}
        )
        
        # Record runtime phase
        analyzer.record_phase(
            phase=LifecyclePhase.RUNTIME,
            energy_j=50000,
            duration_s=3600,
            metadata={'requests': 10000}
        )
        
        # Analyze lifecycle
        analysis = analyzer.analyze_lifecycle()
        print(f"Build: {analysis['build_percent']}%")
        print(f"Runtime: {analysis['runtime_percent']}%")
    """
    
    def __init__(self, project_id: str, version: str):
        self.project_id = project_id
        self.version = version
        self.measurements = []
        self.config = {
            'enable_tco_calculation': True,
            'runtime_projection_hours': 720,  # 30 days
            'cost_per_kwh_usd': 0.12
        }
    
    def record_phase(
        self,
        phase: LifecyclePhase,
        energy_j: float,
        duration_s: float,
        metadata: Optional[Dict] = None
    ) -> LifecycleMeasurement:
        """Record energy measurement for a lifecycle phase"""
        measurement = LifecycleMeasurement(phase, energy_j, duration_s, metadata)
        self.measurements.append(measurement)
        
        logger.info(
            f"Recorded {phase.value}: {energy_j:.1f} J "
            f"({duration_s:.1f}s, {measurement.power_w:.1f}W)"
        )
        
        return measurement
    
    def get_phase_total(self, phase: LifecyclePhase) -> float:
        """Get total energy for a specific phase"""
        return sum(
            m.energy_j for m in self.measurements
            if m.phase == phase
        )
    
    def get_total_energy(self) -> float:
        """Get total energy across all phases"""
        return sum(m.energy_j for m in self.measurements)
    
    def analyze_lifecycle(self) -> Dict:
        """
        Analyze energy distribution across lifecycle.
        
        Returns:
        {
            'total_energy_j': float,
            'phase_breakdown': dict,
            'phase_percentages': dict,
            'dominant_phase': str,
            'build_vs_runtime_ratio': float,
            'recommendations': list
        }
        """
        total_energy = self.get_total_energy()
        
        if total_energy == 0:
            return {
                'total_energy_j': 0,
                'phase_breakdown': {},
                'phase_percentages': {},
                'dominant_phase': None,
                'build_vs_runtime_ratio': None,
                'recommendations': []
            }
        
        # Calculate per-phase totals
        phase_breakdown = {}
        phase_percentages = {}
        
        for phase in LifecyclePhase:
            phase_energy = self.get_phase_total(phase)
            phase_breakdown[phase.value] = phase_energy
            phase_percentages[phase.value] = (phase_energy / total_energy) * 100
        
        # Find dominant phase
        dominant_phase = max(phase_breakdown.items(), key=lambda x: x[1])[0]
        
        # Calculate build vs runtime ratio
        build_energy = self.get_phase_total(LifecyclePhase.BUILD)
        runtime_energy = self.get_phase_total(LifecyclePhase.RUNTIME)
        build_vs_runtime_ratio = (
            build_energy / runtime_energy if runtime_energy > 0 else None
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            phase_percentages,
            build_vs_runtime_ratio
        )
        
        return {
            'total_energy_j': total_energy,
            'phase_breakdown': phase_breakdown,
            'phase_percentages': phase_percentages,
            'dominant_phase': dominant_phase,
            'build_vs_runtime_ratio': build_vs_runtime_ratio,
            'recommendations': recommendations
        }
    
    def compare_build_vs_runtime(self) -> Dict:
        """
        Compare build-time vs runtime energy consumption.
        
        Returns:
        {
            'build_energy_j': float,
            'runtime_energy_j': float,
            'build_duration_s': float,
            'runtime_duration_s': float,
            'build_power_w': float,
            'runtime_power_w': float,
            'ratio': float,
            'summary': str
        }
        """
        build_measurements = [
            m for m in self.measurements
            if m.phase == LifecyclePhase.BUILD
        ]
        runtime_measurements = [
            m for m in self.measurements
            if m.phase == LifecyclePhase.RUNTIME
        ]
        
        build_energy = sum(m.energy_j for m in build_measurements)
        runtime_energy = sum(m.energy_j for m in runtime_measurements)
        
        build_duration = sum(m.duration_s for m in build_measurements)
        runtime_duration = sum(m.duration_s for m in runtime_measurements)
        
        build_power = build_energy / build_duration if build_duration > 0 else 0
        runtime_power = runtime_energy / runtime_duration if runtime_duration > 0 else 0
        
        ratio = build_energy / runtime_energy if runtime_energy > 0 else 0
        
        summary = self._generate_build_runtime_summary(
            build_energy,
            runtime_energy,
            ratio
        )
        
        return {
            'build_energy_j': build_energy,
            'runtime_energy_j': runtime_energy,
            'build_duration_s': build_duration,
            'runtime_duration_s': runtime_duration,
            'build_power_w': build_power,
            'runtime_power_w': runtime_power,
            'ratio': ratio,
            'summary': summary
        }
    
    def compare_training_vs_inference(self) -> Dict:
        """
        Compare AI/ML training vs inference energy.
        
        Returns:
        {
            'training_energy_j': float,
            'inference_energy_j': float,
            'training_duration_s': float,
            'inference_duration_s': float,
            'energy_per_inference': float,
            'break_even_inferences': int,
            'summary': str
        }
        """
        training_measurements = [
            m for m in self.measurements
            if m.phase == LifecyclePhase.TRAINING
        ]
        inference_measurements = [
            m for m in self.measurements
            if m.phase == LifecyclePhase.INFERENCE
        ]
        
        training_energy = sum(m.energy_j for m in training_measurements)
        inference_energy = sum(m.energy_j for m in inference_measurements)
        
        training_duration = sum(m.duration_s for m in training_measurements)
        inference_duration = sum(m.duration_s for m in inference_measurements)
        
        # Calculate energy per inference
        num_inferences = sum(
            m.metadata.get('num_inferences', 1)
            for m in inference_measurements
        )
        energy_per_inference = (
            inference_energy / num_inferences if num_inferences > 0 else 0
        )
        
        # Calculate break-even point
        break_even_inferences = (
            int(training_energy / energy_per_inference)
            if energy_per_inference > 0 else 0
        )
        
        summary = self._generate_training_inference_summary(
            training_energy,
            energy_per_inference,
            break_even_inferences
        )
        
        return {
            'training_energy_j': training_energy,
            'inference_energy_j': inference_energy,
            'training_duration_s': training_duration,
            'inference_duration_s': inference_duration,
            'energy_per_inference': energy_per_inference,
            'break_even_inferences': break_even_inferences,
            'num_inferences': num_inferences,
            'summary': summary
        }
    
    def calculate_tco(self, runtime_hours: Optional[int] = None) -> Dict:
        """
        Calculate Total Cost of Ownership (TCO) including energy costs.
        
        Returns:
        {
            'build_cost_usd': float,
            'runtime_cost_usd': float,
            'total_cost_usd': float,
            'runtime_projection_hours': int,
            'cost_per_hour_usd': float
        }
        """
        if not self.config['enable_tco_calculation']:
            return {}
        
        runtime_hours = runtime_hours or self.config['runtime_projection_hours']
        cost_per_kwh = self.config['cost_per_kwh_usd']
        
        # Build cost (one-time)
        build_energy_kwh = self.get_phase_total(LifecyclePhase.BUILD) / 3_600_000
        build_cost = build_energy_kwh * cost_per_kwh
        
        # Runtime cost (projected)
        runtime_energy_j = self.get_phase_total(LifecyclePhase.RUNTIME)
        runtime_duration_s = sum(
            m.duration_s for m in self.measurements
            if m.phase == LifecyclePhase.RUNTIME
        )
        
        if runtime_duration_s > 0:
            runtime_power_w = runtime_energy_j / runtime_duration_s
            projected_energy_kwh = (runtime_power_w * runtime_hours * 3600) / 3_600_000
            runtime_cost = projected_energy_kwh * cost_per_kwh
        else:
            runtime_cost = 0
        
        total_cost = build_cost + runtime_cost
        cost_per_hour = runtime_cost / runtime_hours if runtime_hours > 0 else 0
        
        return {
            'build_cost_usd': build_cost,
            'runtime_cost_usd': runtime_cost,
            'total_cost_usd': total_cost,
            'runtime_projection_hours': runtime_hours,
            'cost_per_hour_usd': cost_per_hour
        }
    
    def _generate_recommendations(
        self,
        phase_percentages: Dict,
        build_vs_runtime_ratio: Optional[float]
    ) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # Check build energy
        build_percent = phase_percentages.get('build', 0)
        if build_percent > 30:
            recommendations.append(
                "Build phase consumes >30% of energy. Consider: "
                "Docker layer caching, incremental builds, or build optimization."
            )
        
        # Check runtime energy
        runtime_percent = phase_percentages.get('runtime', 0)
        if runtime_percent > 70:
            recommendations.append(
                "Runtime dominates energy consumption. Focus on: "
                "algorithm optimization, caching, or resource efficiency."
            )
        
        # Check training energy
        training_percent = phase_percentages.get('training', 0)
        if training_percent > 50:
            recommendations.append(
                "Training consumes >50% of energy. Consider: "
                "model pruning, quantization, or efficient architectures."
            )
        
        # Check build vs runtime ratio
        if build_vs_runtime_ratio and build_vs_runtime_ratio > 0.5:
            recommendations.append(
                "Build energy is >50% of runtime. Optimize build process or "
                "increase runtime efficiency to amortize build costs."
            )
        
        return recommendations
    
    def _generate_build_runtime_summary(
        self,
        build_energy: float,
        runtime_energy: float,
        ratio: float
    ) -> str:
        """Generate build vs runtime summary"""
        if runtime_energy == 0:
            return "No runtime measurements available"
        
        return (
            f"Build: {build_energy:.1f} J | "
            f"Runtime: {runtime_energy:.1f} J | "
            f"Ratio: {ratio:.2f}:1"
        )
    
    def _generate_training_inference_summary(
        self,
        training_energy: float,
        energy_per_inference: float,
        break_even: int
    ) -> str:
        """Generate training vs inference summary"""
        if energy_per_inference == 0:
            return "No inference measurements available"
        
        return (
            f"Training: {training_energy:.1f} J | "
            f"Per inference: {energy_per_inference:.3f} J | "
            f"Break-even: {break_even:,} inferences"
        )
    
    def generate_report(self) -> Dict:
        """Generate comprehensive lifecycle report"""
        lifecycle_analysis = self.analyze_lifecycle()
        build_runtime = self.compare_build_vs_runtime()
        training_inference = self.compare_training_vs_inference()
        tco = self.calculate_tco()
        
        return {
            'project_id': self.project_id,
            'version': self.version,
            'lifecycle_analysis': lifecycle_analysis,
            'build_vs_runtime': build_runtime,
            'training_vs_inference': training_inference,
            'tco': tco,
            'measurements': [m.to_dict() for m in self.measurements]
        }


# Singleton storage
_lifecycle_analyzers = {}

def get_lifecycle_analyzer(project_id: str, version: str) -> LifecycleAnalyzer:
    """Get or create lifecycle analyzer for a project version"""
    key = f"{project_id}:{version}"
    if key not in _lifecycle_analyzers:
        _lifecycle_analyzers[key] = LifecycleAnalyzer(project_id, version)
    return _lifecycle_analyzers[key]
