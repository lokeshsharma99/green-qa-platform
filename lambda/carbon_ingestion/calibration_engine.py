"""
Calibration Engine for GMT + TEADS Integration

Calibrates TEADS estimates using GMT measurements to improve accuracy over time.
Uses machine learning to find patterns and apply calibration factors.

Phase 1 - Week 3 Implementation
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import statistics

logger = logging.getLogger(__name__)


class CalibrationEngine:
    """
    Calibrates TEADS estimates using GMT measurements.
    Improves accuracy over time through data-driven calibration.
    
    Features:
    - Workload profile matching
    - Calibration factor calculation
    - Confidence scoring
    - Time-based decay for old calibrations
    - Outlier detection and filtering
    
    Example:
        engine = CalibrationEngine()
        
        # Store calibration data
        engine.calibrate_estimate(
            estimated_energy_j=5000,
            measured_energy_j=4800,
            workload_profile={'cpu_percent': 75, 'memory_mb': 2048}
        )
        
        # Get calibrated estimate
        result = engine.get_calibrated_estimate(
            raw_estimate=5000,
            workload_profile={'cpu_percent': 75, 'memory_mb': 2048}
        )
        print(f"Calibrated: {result['calibrated_estimate_j']} J")
    """
    
    def __init__(self, storage_backend=None):
        """
        Initialize calibration engine.
        
        Args:
            storage_backend: Optional storage backend (DynamoDB, etc.)
                           If None, uses in-memory storage
        """
        self.storage = storage_backend or InMemoryCalibrationStorage()
        self.config = {
            'min_samples_for_calibration': 10,
            'confidence_threshold': 0.7,
            'max_calibration_age_days': 30,
            'outlier_threshold_std': 2.0,
            'similarity_threshold': 0.8
        }
    
    def calibrate_estimate(
        self,
        estimated_energy_j: float,
        measured_energy_j: float,
        workload_profile: Dict
    ) -> float:
        """
        Calculate and store calibration factor.
        
        Args:
            estimated_energy_j: TEADS estimation
            measured_energy_j: GMT measurement
            workload_profile: Workload characteristics
                {
                    'cpu_utilization_percent': float,
                    'memory_usage_mb': int,
                    'duration_seconds': int,
                    'workload_type': str,
                    'region': str (optional)
                }
        
        Returns:
            Calibration factor (measured / estimated)
        """
        if estimated_energy_j <= 0:
            logger.warning("Invalid estimated energy, cannot calibrate")
            return 1.0
        
        calibration_factor = measured_energy_j / estimated_energy_j
        
        # Validate calibration factor (should be reasonable)
        if not (0.1 <= calibration_factor <= 10.0):
            logger.warning(f"Unusual calibration factor: {calibration_factor}, skipping")
            return calibration_factor
        
        # Store calibration data
        calibration_data = {
            'estimated_energy_j': estimated_energy_j,
            'measured_energy_j': measured_energy_j,
            'calibration_factor': calibration_factor,
            'workload_profile': workload_profile,
            'timestamp': datetime.utcnow().isoformat(),
            'confidence_score': 1.0  # Initial confidence
        }
        
        self.storage.store_calibration(calibration_data)
        
        logger.info(f"Stored calibration: factor={calibration_factor:.3f}, "
                   f"workload={workload_profile.get('workload_type', 'unknown')}")
        
        return calibration_factor
    
    def get_calibrated_estimate(
        self,
        raw_estimate: float,
        workload_profile: Dict
    ) -> Dict:
        """
        Apply calibration to improve estimate accuracy.
        
        Args:
            raw_estimate: Raw TEADS estimate
            workload_profile: Current workload characteristics
        
        Returns:
        {
            'raw_estimate_j': float,
            'calibrated_estimate_j': float,
            'calibration_factor': float,
            'confidence_score': float,  # 0-1
            'sample_size': int,
            'method': str  # 'calibrated' or 'raw'
        }
        """
        # Find similar workloads
        similar_calibrations = self._find_similar_workloads(workload_profile)
        
        # Not enough data for calibration
        if len(similar_calibrations) < self.config['min_samples_for_calibration']:
            return {
                'raw_estimate_j': raw_estimate,
                'calibrated_estimate_j': raw_estimate,
                'calibration_factor': 1.0,
                'confidence_score': 0.0,
                'sample_size': len(similar_calibrations),
                'method': 'raw'
            }
        
        # Filter outliers
        filtered_calibrations = self._filter_outliers(similar_calibrations)
        
        if not filtered_calibrations:
            return {
                'raw_estimate_j': raw_estimate,
                'calibrated_estimate_j': raw_estimate,
                'calibration_factor': 1.0,
                'confidence_score': 0.0,
                'sample_size': 0,
                'method': 'raw'
            }
        
        # Calculate weighted average calibration factor
        avg_factor = self._calculate_weighted_average(filtered_calibrations)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(filtered_calibrations)
        
        # Apply calibration if confidence is high enough
        if confidence >= self.config['confidence_threshold']:
            calibrated_estimate = raw_estimate * avg_factor
            method = 'calibrated'
        else:
            calibrated_estimate = raw_estimate
            avg_factor = 1.0
            method = 'raw'
        
        return {
            'raw_estimate_j': raw_estimate,
            'calibrated_estimate_j': calibrated_estimate,
            'calibration_factor': avg_factor,
            'confidence_score': confidence,
            'sample_size': len(filtered_calibrations),
            'method': method
        }
    
    def _find_similar_workloads(self, workload_profile: Dict) -> List[Dict]:
        """
        Find calibrations from similar workloads.
        
        Similarity based on:
        - Workload type (exact match preferred)
        - CPU utilization (within 20%)
        - Memory usage (within 30%)
        - Duration (within 50%)
        """
        all_calibrations = self.storage.get_recent_calibrations(
            days=self.config['max_calibration_age_days']
        )
        
        similar = []
        target_cpu = workload_profile.get('cpu_utilization_percent', 50)
        target_memory = workload_profile.get('memory_usage_mb', 1024)
        target_duration = workload_profile.get('duration_seconds', 300)
        target_type = workload_profile.get('workload_type', 'unknown')
        
        for cal in all_calibrations:
            profile = cal.get('workload_profile', {})
            
            # Calculate similarity score
            similarity = self._calculate_similarity(
                workload_profile,
                profile
            )
            
            if similarity >= self.config['similarity_threshold']:
                cal['similarity_score'] = similarity
                similar.append(cal)
        
        # Sort by similarity (most similar first)
        similar.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        
        return similar
    
    def _calculate_similarity(self, profile1: Dict, profile2: Dict) -> float:
        """
        Calculate similarity score between two workload profiles.
        
        Returns: 0.0 to 1.0 (1.0 = identical)
        """
        scores = []
        
        # Workload type match (most important)
        type1 = profile1.get('workload_type', 'unknown')
        type2 = profile2.get('workload_type', 'unknown')
        if type1 == type2:
            scores.append(1.0)
        else:
            scores.append(0.5)  # Partial credit
        
        # CPU utilization similarity
        cpu1 = profile1.get('cpu_utilization_percent', 50)
        cpu2 = profile2.get('cpu_utilization_percent', 50)
        cpu_diff = abs(cpu1 - cpu2) / 100.0
        scores.append(max(0, 1.0 - cpu_diff * 5))  # 20% diff = 0 score
        
        # Memory usage similarity
        mem1 = profile1.get('memory_usage_mb', 1024)
        mem2 = profile2.get('memory_usage_mb', 1024)
        mem_diff = abs(mem1 - mem2) / max(mem1, mem2)
        scores.append(max(0, 1.0 - mem_diff * 3))  # 33% diff = 0 score
        
        # Duration similarity
        dur1 = profile1.get('duration_seconds', 300)
        dur2 = profile2.get('duration_seconds', 300)
        dur_diff = abs(dur1 - dur2) / max(dur1, dur2)
        scores.append(max(0, 1.0 - dur_diff * 2))  # 50% diff = 0 score
        
        # Weighted average (workload type is most important)
        weights = [0.4, 0.25, 0.2, 0.15]
        return sum(s * w for s, w in zip(scores, weights))
    
    def _filter_outliers(self, calibrations: List[Dict]) -> List[Dict]:
        """
        Filter out outlier calibration factors using statistical methods.
        """
        if len(calibrations) < 3:
            return calibrations
        
        factors = [c['calibration_factor'] for c in calibrations]
        
        mean = statistics.mean(factors)
        stdev = statistics.stdev(factors) if len(factors) > 1 else 0
        
        if stdev == 0:
            return calibrations
        
        # Filter calibrations within N standard deviations
        threshold = self.config['outlier_threshold_std']
        filtered = [
            c for c in calibrations
            if abs(c['calibration_factor'] - mean) <= threshold * stdev
        ]
        
        logger.debug(f"Filtered {len(calibrations) - len(filtered)} outliers")
        
        return filtered if filtered else calibrations
    
    def _calculate_weighted_average(self, calibrations: List[Dict]) -> float:
        """
        Calculate weighted average calibration factor.
        
        Weights based on:
        - Similarity score (higher = more weight)
        - Recency (newer = more weight)
        """
        if not calibrations:
            return 1.0
        
        total_weight = 0
        weighted_sum = 0
        
        now = datetime.utcnow()
        
        for cal in calibrations:
            # Similarity weight
            similarity = cal.get('similarity_score', 0.5)
            
            # Recency weight (exponential decay)
            timestamp = datetime.fromisoformat(cal['timestamp'].replace('Z', '+00:00'))
            age_days = (now - timestamp).days
            recency = 0.95 ** age_days  # 5% decay per day
            
            # Combined weight
            weight = similarity * recency
            
            weighted_sum += cal['calibration_factor'] * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 1.0
    
    def _calculate_confidence(self, calibrations: List[Dict]) -> float:
        """
        Calculate confidence score for calibration.
        
        Based on:
        - Sample size (more = higher confidence)
        - Consistency (lower variance = higher confidence)
        - Recency (newer = higher confidence)
        """
        if not calibrations:
            return 0.0
        
        # Sample size factor (logarithmic)
        n = len(calibrations)
        size_factor = min(1.0, (n / 50) ** 0.5)  # Reaches 1.0 at 50 samples
        
        # Consistency factor (inverse of coefficient of variation)
        factors = [c['calibration_factor'] for c in calibrations]
        mean = statistics.mean(factors)
        stdev = statistics.stdev(factors) if len(factors) > 1 else 0
        cv = stdev / mean if mean > 0 else 1.0
        consistency_factor = 1.0 / (1.0 + cv)
        
        # Recency factor (average age)
        now = datetime.utcnow()
        ages = []
        for cal in calibrations:
            timestamp = datetime.fromisoformat(cal['timestamp'].replace('Z', '+00:00'))
            ages.append((now - timestamp).days)
        avg_age = statistics.mean(ages)
        recency_factor = 0.95 ** avg_age
        
        # Combined confidence
        confidence = (size_factor * 0.4 + 
                     consistency_factor * 0.4 + 
                     recency_factor * 0.2)
        
        return min(1.0, confidence)
    
    def get_calibration_stats(self, workload_type: Optional[str] = None) -> Dict:
        """
        Get calibration statistics.
        
        Args:
            workload_type: Optional filter by workload type
        
        Returns:
        {
            'total_measurements': int,
            'average_calibration_factor': float,
            'accuracy_improvement': str,
            'workload_types': dict,
            'recent_calibrations': int
        }
        """
        all_calibrations = self.storage.get_recent_calibrations(days=30)
        
        if workload_type:
            all_calibrations = [
                c for c in all_calibrations
                if c.get('workload_profile', {}).get('workload_type') == workload_type
            ]
        
        if not all_calibrations:
            return {
                'total_measurements': 0,
                'average_calibration_factor': 1.0,
                'accuracy_improvement': '0%',
                'workload_types': {},
                'recent_calibrations': 0
            }
        
        factors = [c['calibration_factor'] for c in all_calibrations]
        avg_factor = statistics.mean(factors)
        
        # Calculate accuracy improvement
        # If avg_factor is 0.9, estimates were 10% too high, so 10% improvement
        improvement = abs(1.0 - avg_factor) * 100
        
        # Group by workload type
        workload_types = {}
        for cal in all_calibrations:
            wtype = cal.get('workload_profile', {}).get('workload_type', 'unknown')
            if wtype not in workload_types:
                workload_types[wtype] = {'count': 0, 'factors': []}
            workload_types[wtype]['count'] += 1
            workload_types[wtype]['factors'].append(cal['calibration_factor'])
        
        # Calculate average factor per workload type
        for wtype in workload_types:
            factors = workload_types[wtype]['factors']
            workload_types[wtype]['avg_factor'] = statistics.mean(factors)
            del workload_types[wtype]['factors']
        
        return {
            'total_measurements': len(all_calibrations),
            'average_calibration_factor': round(avg_factor, 3),
            'accuracy_improvement': f"{improvement:.1f}%",
            'workload_types': workload_types,
            'recent_calibrations': len(all_calibrations)
        }


class InMemoryCalibrationStorage:
    """
    In-memory storage for calibration data.
    For production, replace with DynamoDB or similar.
    """
    
    def __init__(self):
        self.calibrations = []
    
    def store_calibration(self, calibration_data: Dict):
        """Store calibration data"""
        self.calibrations.append(calibration_data)
    
    def get_recent_calibrations(self, days: int = 30) -> List[Dict]:
        """Get calibrations from last N days"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        recent = []
        for cal in self.calibrations:
            timestamp = datetime.fromisoformat(cal['timestamp'].replace('Z', '+00:00'))
            if timestamp >= cutoff:
                recent.append(cal)
        
        return recent
    
    def clear(self):
        """Clear all calibrations (for testing)"""
        self.calibrations = []


# Singleton instance
_calibration_engine = None

def get_calibration_engine() -> CalibrationEngine:
    """Get global calibration engine instance (singleton)"""
    global _calibration_engine
    if _calibration_engine is None:
        _calibration_engine = CalibrationEngine()
    return _calibration_engine
