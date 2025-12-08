"""
Energy Regression Detector - Track Energy Over Commits

Detects energy regressions in CI/CD pipelines by comparing measurements
across commits, branches, and releases.

Features:
- Commit-to-commit comparison
- Baseline tracking
- Regression alerts
- Trend analysis
- Performance budgets
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


class EnergyMeasurement:
    """Represents a single energy measurement for a commit"""
    
    def __init__(
        self,
        commit_sha: str,
        branch: str,
        energy_j: float,
        workload_type: str,
        timestamp: Optional[str] = None
    ):
        self.commit_sha = commit_sha
        self.branch = branch
        self.energy_j = energy_j
        self.workload_type = workload_type
        self.timestamp = timestamp or datetime.utcnow().isoformat()
        self.metadata = {}
    
    def to_dict(self) -> Dict:
        return {
            'commit_sha': self.commit_sha,
            'branch': self.branch,
            'energy_j': self.energy_j,
            'workload_type': self.workload_type,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }


class EnergyRegressionDetector:
    """
    Detect energy regressions across commits.
    
    Features:
    - Track energy consumption per commit
    - Compare against baseline
    - Detect regressions (energy increases)
    - Trend analysis
    - Performance budgets
    - Alert generation
    
    Example:
        detector = EnergyRegressionDetector()
        
        # Set baseline
        detector.set_baseline('main', 'test_suite', 5000)
        
        # Check for regression
        result = detector.check_regression(
            commit_sha='abc123',
            branch='feature/new-algo',
            energy_j=6000,
            workload_type='test_suite'
        )
        
        if result['is_regression']:
            print(f"⚠️ Regression detected: +{result['diff_percent']}%")
    """
    
    def __init__(self, storage_backend=None):
        self.storage = storage_backend or InMemoryRegressionStorage()
        self.config = {
            'regression_threshold_percent': 5.0,  # Alert if >5% increase
            'baseline_window_days': 7,  # Use last 7 days for baseline
            'min_samples_for_baseline': 3,
            'trend_window_commits': 10,
            'enable_performance_budgets': True
        }
        self.performance_budgets = {}  # workload_type -> max_energy_j
    
    def record_measurement(
        self,
        commit_sha: str,
        branch: str,
        energy_j: float,
        workload_type: str,
        metadata: Optional[Dict] = None
    ) -> EnergyMeasurement:
        """Record an energy measurement for a commit"""
        measurement = EnergyMeasurement(
            commit_sha=commit_sha,
            branch=branch,
            energy_j=energy_j,
            workload_type=workload_type
        )
        
        if metadata:
            measurement.metadata = metadata
        
        self.storage.store_measurement(measurement)
        logger.info(f"Recorded measurement: {commit_sha[:8]} - {energy_j:.1f} J")
        
        return measurement
    
    def set_baseline(
        self,
        branch: str,
        workload_type: str,
        energy_j: float
    ):
        """Set baseline energy for a workload type"""
        self.storage.set_baseline(branch, workload_type, energy_j)
        logger.info(f"Set baseline for {workload_type} on {branch}: {energy_j:.1f} J")
    
    def get_baseline(
        self,
        branch: str,
        workload_type: str
    ) -> Optional[float]:
        """
        Get baseline energy for a workload type.
        
        If no explicit baseline set, calculates from recent measurements.
        """
        # Check for explicit baseline
        baseline = self.storage.get_baseline(branch, workload_type)
        if baseline:
            return baseline
        
        # Calculate from recent measurements
        recent = self.storage.get_recent_measurements(
            branch=branch,
            workload_type=workload_type,
            days=self.config['baseline_window_days']
        )
        
        if len(recent) < self.config['min_samples_for_baseline']:
            logger.warning(f"Insufficient samples for baseline: {len(recent)}")
            return None
        
        # Use median as baseline (robust to outliers)
        energies = [m.energy_j for m in recent]
        baseline = statistics.median(energies)
        
        logger.info(f"Calculated baseline from {len(recent)} samples: {baseline:.1f} J")
        return baseline
    
    def check_regression(
        self,
        commit_sha: str,
        branch: str,
        energy_j: float,
        workload_type: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Check if current measurement represents a regression.
        
        Returns:
        {
            'is_regression': bool,
            'baseline_j': float,
            'current_j': float,
            'diff_j': float,
            'diff_percent': float,
            'severity': str,  # 'none', 'minor', 'major', 'critical'
            'message': str,
            'budget_exceeded': bool
        }
        """
        # Record measurement
        self.record_measurement(commit_sha, branch, energy_j, workload_type, metadata)
        
        # Get baseline
        baseline = self.get_baseline(branch, workload_type)
        if not baseline:
            return {
                'is_regression': False,
                'baseline_j': None,
                'current_j': energy_j,
                'diff_j': 0,
                'diff_percent': 0,
                'severity': 'none',
                'message': 'No baseline available for comparison',
                'budget_exceeded': False
            }
        
        # Calculate difference
        diff_j = energy_j - baseline
        diff_percent = (diff_j / baseline) * 100
        
        # Determine if regression
        is_regression = diff_percent > self.config['regression_threshold_percent']
        
        # Determine severity
        severity = self._calculate_severity(diff_percent)
        
        # Check performance budget
        budget_exceeded = False
        if self.config['enable_performance_budgets']:
            budget = self.performance_budgets.get(workload_type)
            if budget and energy_j > budget:
                budget_exceeded = True
        
        # Generate message
        message = self._generate_regression_message(
            is_regression,
            diff_j,
            diff_percent,
            severity,
            budget_exceeded
        )
        
        result = {
            'is_regression': is_regression,
            'baseline_j': baseline,
            'current_j': energy_j,
            'diff_j': diff_j,
            'diff_percent': diff_percent,
            'severity': severity,
            'message': message,
            'budget_exceeded': budget_exceeded,
            'commit_sha': commit_sha,
            'branch': branch,
            'workload_type': workload_type
        }
        
        if is_regression:
            logger.warning(f"⚠️ Regression detected: {message}")
        else:
            logger.info(f"✓ No regression: {diff_percent:+.1f}%")
        
        return result
    
    def _calculate_severity(self, diff_percent: float) -> str:
        """Calculate regression severity"""
        if diff_percent <= self.config['regression_threshold_percent']:
            return 'none'
        elif diff_percent <= 10:
            return 'minor'
        elif diff_percent <= 25:
            return 'major'
        else:
            return 'critical'
    
    def _generate_regression_message(
        self,
        is_regression: bool,
        diff_j: float,
        diff_percent: float,
        severity: str,
        budget_exceeded: bool
    ) -> str:
        """Generate human-readable regression message"""
        if not is_regression:
            if diff_j < 0:
                return f"✓ Energy improved by {abs(diff_j):.1f} J ({abs(diff_percent):.1f}%)"
            else:
                return f"✓ Energy within acceptable range (+{diff_percent:.1f}%)"
        
        emoji = {
            'minor': '⚠️',
            'major': '🔴',
            'critical': '🚨'
        }.get(severity, '⚠️')
        
        message = f"{emoji} {severity.upper()} regression: +{diff_j:.1f} J (+{diff_percent:.1f}%)"
        
        if budget_exceeded:
            message += " | Budget exceeded!"
        
        return message
    
    def analyze_trend(
        self,
        branch: str,
        workload_type: str,
        num_commits: Optional[int] = None
    ) -> Dict:
        """
        Analyze energy trend over recent commits.
        
        Returns:
        {
            'trend': str,  # 'improving', 'stable', 'degrading'
            'slope': float,  # Energy change per commit
            'measurements': list,
            'summary': str
        }
        """
        num_commits = num_commits or self.config['trend_window_commits']
        
        measurements = self.storage.get_recent_measurements(
            branch=branch,
            workload_type=workload_type,
            limit=num_commits
        )
        
        if len(measurements) < 3:
            return {
                'trend': 'unknown',
                'slope': 0,
                'measurements': [],
                'summary': 'Insufficient data for trend analysis'
            }
        
        # Calculate trend using linear regression
        energies = [m.energy_j for m in measurements]
        slope = self._calculate_trend_slope(energies)
        
        # Determine trend direction
        if slope < -10:  # Improving by >10 J per commit
            trend = 'improving'
        elif slope > 10:  # Degrading by >10 J per commit
            trend = 'degrading'
        else:
            trend = 'stable'
        
        summary = self._generate_trend_summary(trend, slope, len(measurements))
        
        return {
            'trend': trend,
            'slope': slope,
            'measurements': [m.to_dict() for m in measurements],
            'summary': summary
        }
    
    def _calculate_trend_slope(self, values: List[float]) -> float:
        """Calculate trend slope using simple linear regression"""
        n = len(values)
        if n < 2:
            return 0
        
        x = list(range(n))
        y = values
        
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0
        
        slope = numerator / denominator
        return slope
    
    def _generate_trend_summary(
        self,
        trend: str,
        slope: float,
        num_commits: int
    ) -> str:
        """Generate human-readable trend summary"""
        emoji = {
            'improving': '📉',
            'stable': '➡️',
            'degrading': '📈'
        }.get(trend, '❓')
        
        return f"{emoji} {trend.capitalize()} trend: {slope:+.1f} J/commit over {num_commits} commits"
    
    def set_performance_budget(
        self,
        workload_type: str,
        max_energy_j: float
    ):
        """Set performance budget for a workload type"""
        self.performance_budgets[workload_type] = max_energy_j
        logger.info(f"Set performance budget for {workload_type}: {max_energy_j:.1f} J")
    
    def get_performance_budget(self, workload_type: str) -> Optional[float]:
        """Get performance budget for a workload type"""
        return self.performance_budgets.get(workload_type)
    
    def generate_report(
        self,
        branch: str,
        workload_type: str
    ) -> Dict:
        """
        Generate comprehensive regression report.
        
        Returns:
        {
            'baseline': float,
            'recent_measurements': list,
            'trend': dict,
            'regressions': list,
            'improvements': list,
            'budget_status': dict
        }
        """
        baseline = self.get_baseline(branch, workload_type)
        recent = self.storage.get_recent_measurements(
            branch=branch,
            workload_type=workload_type,
            days=7
        )
        trend = self.analyze_trend(branch, workload_type)
        
        # Identify regressions and improvements
        regressions = []
        improvements = []
        
        if baseline:
            for m in recent:
                diff_percent = ((m.energy_j - baseline) / baseline) * 100
                if diff_percent > self.config['regression_threshold_percent']:
                    regressions.append({
                        'commit_sha': m.commit_sha,
                        'energy_j': m.energy_j,
                        'diff_percent': diff_percent
                    })
                elif diff_percent < -5:  # Improvement threshold
                    improvements.append({
                        'commit_sha': m.commit_sha,
                        'energy_j': m.energy_j,
                        'diff_percent': diff_percent
                    })
        
        # Budget status
        budget = self.get_performance_budget(workload_type)
        budget_status = None
        if budget and recent:
            latest = recent[0]
            budget_status = {
                'budget_j': budget,
                'current_j': latest.energy_j,
                'within_budget': latest.energy_j <= budget,
                'headroom_j': budget - latest.energy_j,
                'headroom_percent': ((budget - latest.energy_j) / budget) * 100
            }
        
        return {
            'baseline': baseline,
            'recent_measurements': [m.to_dict() for m in recent[:10]],
            'trend': trend,
            'regressions': regressions,
            'improvements': improvements,
            'budget_status': budget_status
        }


class InMemoryRegressionStorage:
    """In-memory storage for regression data"""
    
    def __init__(self):
        self.measurements = []
        self.baselines = {}  # (branch, workload_type) -> energy_j
    
    def store_measurement(self, measurement: EnergyMeasurement):
        self.measurements.append(measurement)
    
    def get_recent_measurements(
        self,
        branch: Optional[str] = None,
        workload_type: Optional[str] = None,
        days: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[EnergyMeasurement]:
        """Get recent measurements with optional filters"""
        filtered = self.measurements
        
        # Filter by branch
        if branch:
            filtered = [m for m in filtered if m.branch == branch]
        
        # Filter by workload type
        if workload_type:
            filtered = [m for m in filtered if m.workload_type == workload_type]
        
        # Filter by time
        if days:
            cutoff = datetime.utcnow() - timedelta(days=days)
            filtered = [
                m for m in filtered
                if datetime.fromisoformat(m.timestamp.replace('Z', '+00:00')) >= cutoff
            ]
        
        # Sort by timestamp (newest first)
        filtered.sort(key=lambda m: m.timestamp, reverse=True)
        
        # Limit results
        if limit:
            filtered = filtered[:limit]
        
        return filtered
    
    def set_baseline(self, branch: str, workload_type: str, energy_j: float):
        key = (branch, workload_type)
        self.baselines[key] = energy_j
    
    def get_baseline(self, branch: str, workload_type: str) -> Optional[float]:
        key = (branch, workload_type)
        return self.baselines.get(key)
    
    def clear(self):
        self.measurements = []
        self.baselines = {}


# Singleton instance
_regression_detector = None

def get_regression_detector() -> EnergyRegressionDetector:
    """Get global regression detector instance (singleton)"""
    global _regression_detector
    if _regression_detector is None:
        _regression_detector = EnergyRegressionDetector()
    return _regression_detector
