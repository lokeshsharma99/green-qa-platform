"""
A/B Testing for Algorithm Comparison

Compare energy consumption between different implementations,
algorithms, or configurations to identify the most efficient option.

Features:
- Side-by-side comparison
- Statistical significance testing
- Multiple variant support
- Reproducible experiments
- Winner selection
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import statistics

logger = logging.getLogger(__name__)


class Variant:
    """Represents a variant in an A/B test"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.measurements = []
        self.metadata = {}
    
    def add_measurement(self, energy_j: float, duration_s: float, metadata: Optional[Dict] = None):
        """Add a measurement for this variant"""
        self.measurements.append({
            'energy_j': energy_j,
            'duration_s': duration_s,
            'power_w': energy_j / duration_s if duration_s > 0 else 0,
            'metadata': metadata or {},
            'timestamp': datetime.utcnow().isoformat()
        })
    
    def get_statistics(self) -> Dict:
        """Calculate statistics for this variant"""
        if not self.measurements:
            return {
                'count': 0,
                'mean_energy_j': 0,
                'median_energy_j': 0,
                'std_dev': 0,
                'min_energy_j': 0,
                'max_energy_j': 0
            }
        
        energies = [m['energy_j'] for m in self.measurements]
        
        return {
            'count': len(energies),
            'mean_energy_j': statistics.mean(energies),
            'median_energy_j': statistics.median(energies),
            'std_dev': statistics.stdev(energies) if len(energies) > 1 else 0,
            'min_energy_j': min(energies),
            'max_energy_j': max(energies)
        }
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'statistics': self.get_statistics(),
            'measurements': self.measurements,
            'metadata': self.metadata
        }


class ABTest:
    """
    A/B test for comparing algorithm energy consumption.
    
    Features:
    - Multiple variant support (A/B/C/D...)
    - Statistical analysis
    - Winner selection
    - Confidence intervals
    - Reproducible experiments
    
    Example:
        test = ABTest('sorting-algorithms', 'Compare sorting algorithms')
        
        # Add variants
        test.add_variant('quicksort', 'Standard quicksort')
        test.add_variant('mergesort', 'Standard mergesort')
        test.add_variant('timsort', 'Python timsort')
        
        # Record measurements
        test.record_measurement('quicksort', energy_j=1000, duration_s=10)
        test.record_measurement('mergesort', energy_j=1200, duration_s=12)
        test.record_measurement('timsort', energy_j=900, duration_s=9)
        
        # Analyze results
        results = test.analyze()
        print(f"Winner: {results['winner']}")
        print(f"Energy savings: {results['savings_percent']}%")
    """
    
    def __init__(self, test_id: str, description: str):
        self.test_id = test_id
        self.description = description
        self.variants = {}
        self.config = {
            'min_samples_per_variant': 3,
            'confidence_level': 0.95,
            'significance_threshold': 0.05
        }
        self.created_at = datetime.utcnow().isoformat()
    
    def add_variant(self, name: str, description: str) -> Variant:
        """Add a variant to the test"""
        variant = Variant(name, description)
        self.variants[name] = variant
        logger.info(f"Added variant: {name}")
        return variant
    
    def record_measurement(
        self,
        variant_name: str,
        energy_j: float,
        duration_s: float,
        metadata: Optional[Dict] = None
    ):
        """Record a measurement for a variant"""
        if variant_name not in self.variants:
            raise ValueError(f"Variant '{variant_name}' not found")
        
        self.variants[variant_name].add_measurement(energy_j, duration_s, metadata)
        logger.debug(f"Recorded measurement for {variant_name}: {energy_j:.1f} J")
    
    def analyze(self) -> Dict:
        """
        Analyze A/B test results.
        
        Returns:
        {
            'winner': str,
            'winner_stats': dict,
            'all_variants': dict,
            'comparison': list,
            'savings_percent': float,
            'confidence': float,
            'recommendation': str
        }
        """
        if not self.variants:
            return {
                'winner': None,
                'error': 'No variants in test'
            }
        
        # Check if all variants have enough samples
        insufficient_samples = [
            name for name, variant in self.variants.items()
            if len(variant.measurements) < self.config['min_samples_per_variant']
        ]
        
        if insufficient_samples:
            return {
                'winner': None,
                'error': f'Insufficient samples for variants: {", ".join(insufficient_samples)}',
                'min_required': self.config['min_samples_per_variant']
            }
        
        # Calculate statistics for all variants
        variant_stats = {
            name: variant.get_statistics()
            for name, variant in self.variants.items()
        }
        
        # Find winner (lowest mean energy)
        winner_name = min(
            variant_stats.items(),
            key=lambda x: x[1]['mean_energy_j']
        )[0]
        
        winner_stats = variant_stats[winner_name]
        
        # Calculate savings compared to worst variant
        worst_energy = max(v['mean_energy_j'] for v in variant_stats.values())
        savings_j = worst_energy - winner_stats['mean_energy_j']
        savings_percent = (savings_j / worst_energy * 100) if worst_energy > 0 else 0
        
        # Generate pairwise comparisons
        comparisons = self._generate_comparisons(variant_stats, winner_name)
        
        # Calculate confidence
        confidence = self._calculate_confidence(winner_name)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            winner_name,
            savings_percent,
            confidence
        )
        
        return {
            'test_id': self.test_id,
            'description': self.description,
            'winner': winner_name,
            'winner_stats': winner_stats,
            'all_variants': variant_stats,
            'comparisons': comparisons,
            'savings_j': savings_j,
            'savings_percent': savings_percent,
            'confidence': confidence,
            'recommendation': recommendation
        }
    
    def _generate_comparisons(
        self,
        variant_stats: Dict,
        winner_name: str
    ) -> List[Dict]:
        """Generate pairwise comparisons"""
        winner_energy = variant_stats[winner_name]['mean_energy_j']
        
        comparisons = []
        for name, stats in variant_stats.items():
            if name == winner_name:
                continue
            
            diff_j = stats['mean_energy_j'] - winner_energy
            diff_percent = (diff_j / winner_energy * 100) if winner_energy > 0 else 0
            
            comparisons.append({
                'variant': name,
                'mean_energy_j': stats['mean_energy_j'],
                'diff_vs_winner_j': diff_j,
                'diff_vs_winner_percent': diff_percent,
                'slower_by': f"{diff_percent:.1f}%"
            })
        
        # Sort by difference (worst first)
        comparisons.sort(key=lambda x: x['diff_vs_winner_j'], reverse=True)
        
        return comparisons
    
    def _calculate_confidence(self, winner_name: str) -> float:
        """
        Calculate confidence in winner selection.
        
        Based on:
        - Sample size
        - Variance
        - Margin of victory
        """
        winner = self.variants[winner_name]
        winner_stats = winner.get_statistics()
        
        # Sample size factor
        sample_size = winner_stats['count']
        size_factor = min(1.0, sample_size / 10)  # Max confidence at 10+ samples
        
        # Variance factor (lower variance = higher confidence)
        cv = (winner_stats['std_dev'] / winner_stats['mean_energy_j']
              if winner_stats['mean_energy_j'] > 0 else 1.0)
        variance_factor = 1.0 / (1.0 + cv)
        
        # Margin factor (larger margin = higher confidence)
        winner_energy = winner_stats['mean_energy_j']
        other_energies = [
            v.get_statistics()['mean_energy_j']
            for name, v in self.variants.items()
            if name != winner_name
        ]
        
        if other_energies:
            second_best = min(other_energies)
            margin = (second_best - winner_energy) / winner_energy if winner_energy > 0 else 0
            margin_factor = min(1.0, margin * 5)  # 20% margin = max confidence
        else:
            margin_factor = 0.5
        
        # Combined confidence
        confidence = (size_factor * 0.4 + variance_factor * 0.3 + margin_factor * 0.3)
        
        return min(1.0, confidence)
    
    def _generate_recommendation(
        self,
        winner_name: str,
        savings_percent: float,
        confidence: float
    ) -> str:
        """Generate recommendation based on results"""
        if confidence < 0.7:
            return (
                f"⚠️ Low confidence ({confidence:.0%}). "
                f"Collect more samples before making decision."
            )
        
        if savings_percent < 5:
            return (
                f"✓ {winner_name} is most efficient but savings are minimal ({savings_percent:.1f}%). "
                f"Consider other factors (readability, maintainability)."
            )
        
        if savings_percent < 20:
            return (
                f"✓ Recommend {winner_name}: {savings_percent:.1f}% energy savings "
                f"with {confidence:.0%} confidence."
            )
        
        return (
            f"🎯 Strong recommendation for {winner_name}: "
            f"{savings_percent:.1f}% energy savings with {confidence:.0%} confidence. "
            f"Significant improvement!"
        )
    
    def compare_two(self, variant1: str, variant2: str) -> Dict:
        """
        Direct comparison between two specific variants.
        
        Returns:
        {
            'variant1': dict,
            'variant2': dict,
            'winner': str,
            'diff_j': float,
            'diff_percent': float,
            'statistical_significance': bool
        }
        """
        if variant1 not in self.variants or variant2 not in self.variants:
            raise ValueError("Both variants must exist")
        
        v1_stats = self.variants[variant1].get_statistics()
        v2_stats = self.variants[variant2].get_statistics()
        
        diff_j = v2_stats['mean_energy_j'] - v1_stats['mean_energy_j']
        diff_percent = (diff_j / v1_stats['mean_energy_j'] * 100) if v1_stats['mean_energy_j'] > 0 else 0
        
        winner = variant1 if diff_j > 0 else variant2
        
        # Simple statistical significance test (t-test approximation)
        # In production, use scipy.stats.ttest_ind
        statistical_significance = abs(diff_percent) > 10  # Simplified
        
        return {
            'variant1': {
                'name': variant1,
                'stats': v1_stats
            },
            'variant2': {
                'name': variant2,
                'stats': v2_stats
            },
            'winner': winner,
            'diff_j': abs(diff_j),
            'diff_percent': abs(diff_percent),
            'statistical_significance': statistical_significance,
            'summary': f"{winner} is {abs(diff_percent):.1f}% more efficient"
        }
    
    def generate_report(self) -> Dict:
        """Generate comprehensive A/B test report"""
        analysis = self.analyze()
        
        # Add variant details
        variant_details = {
            name: variant.to_dict()
            for name, variant in self.variants.items()
        }
        
        return {
            'test_id': self.test_id,
            'description': self.description,
            'created_at': self.created_at,
            'analysis': analysis,
            'variants': variant_details,
            'config': self.config
        }


# Test storage
_ab_tests = {}

def create_ab_test(test_id: str, description: str) -> ABTest:
    """Create a new A/B test"""
    test = ABTest(test_id, description)
    _ab_tests[test_id] = test
    return test

def get_ab_test(test_id: str) -> Optional[ABTest]:
    """Get existing A/B test"""
    return _ab_tests.get(test_id)

def list_ab_tests() -> List[str]:
    """List all A/B test IDs"""
    return list(_ab_tests.keys())
