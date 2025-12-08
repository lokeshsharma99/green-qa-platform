"""
Slack-Aware Scheduler - Phase 2 Week 6

Based on CarbonFlex research paper:
"CarbonFlex: Enabling Carbon-aware Provisioning and Scheduling"

Key Concept:
- Allow workload to extend beyond minimum duration
- Schedule during lowest-carbon periods within deadline window
- Achieve 20-60% carbon reduction through temporal shifting

Expected Impact: 57% carbon reduction (from paper)
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from carbonx_forecaster import CarbonXForecaster


class SlackAwareScheduler:
    """
    Temporal shifting scheduler with deadline flexibility.
    
    Enables carbon optimization by allowing workloads to be scheduled
    within a flexible time window (slack time) rather than immediately.
    """
    
    def __init__(self):
        self.feature_enabled = os.environ.get('ENABLE_SLACK_SCHEDULING', 'false').lower() == 'true'
    
    def optimize_schedule(
        self,
        region: str,
        workload_duration_hours: float,
        deadline_hours: float,
        current_carbon_intensity: float,
        vcpu_count: int = 2,
        memory_gb: float = 4.0
    ) -> Dict:
        """
        Find optimal execution time within deadline window.
        
        Args:
            region: AWS region code
            workload_duration_hours: How long the workload takes
            deadline_hours: Maximum hours from now to complete
            current_carbon_intensity: Current CI (gCO2/kWh)
            vcpu_count: Number of vCPUs
            memory_gb: Memory in GB
            
        Returns:
            {
                'immediate_execution': {...},
                'optimal_execution': {...},
                'savings': {...},
                'recommendation': str,
                'scheduling_windows': [...]
            }
        """
        if not self.feature_enabled:
            return {
                'error': 'Slack scheduling feature not enabled',
                'feature_flag': 'ENABLE_SLACK_SCHEDULING=true'
            }
        
        # Calculate slack time
        slack_hours = deadline_hours - workload_duration_hours
        
        if slack_hours < 0:
            return {
                'error': 'Deadline shorter than workload duration',
                'deadline_hours': deadline_hours,
                'workload_duration_hours': workload_duration_hours
            }
        
        # Get forecast for deadline window
        forecast_hours = min(int(deadline_hours) + 1, 168)  # Max 7 days
        forecaster = CarbonXForecaster(region=region)
        forecast_data = forecaster.forecast_with_uncertainty(
            hours_ahead=forecast_hours
        )
        
        if 'error' in forecast_data:
            # Fallback: use current CI
            return self._fallback_immediate_execution(
                current_carbon_intensity,
                workload_duration_hours,
                vcpu_count,
                memory_gb
            )
        
        # Find optimal scheduling windows
        windows = self._find_optimal_windows(
            forecast_data['forecasts'],
            workload_duration_hours,
            deadline_hours,
            vcpu_count,
            memory_gb
        )
        
        # Calculate immediate execution carbon
        immediate_carbon = self._calculate_carbon_footprint(
            current_carbon_intensity,
            workload_duration_hours,
            vcpu_count,
            memory_gb
        )
        
        # Get best window
        best_window = windows[0] if windows else None
        
        if not best_window:
            return {
                'immediate_execution': {
                    'carbon_footprint_gco2': immediate_carbon,
                    'start_time': 'now',
                    'carbon_intensity': current_carbon_intensity
                },
                'optimal_execution': None,
                'savings': {'percent': 0, 'gco2': 0},
                'recommendation': 'EXECUTE_NOW',
                'reason': 'No better windows found within deadline'
            }
        
        # Calculate savings
        savings_gco2 = immediate_carbon - best_window['carbon_footprint_gco2']
        savings_percent = (savings_gco2 / immediate_carbon * 100) if immediate_carbon > 0 else 0
        
        # Determine recommendation
        recommendation = self._determine_recommendation(
            savings_percent,
            best_window['delay_hours'],
            slack_hours
        )
        
        return {
            'immediate_execution': {
                'carbon_footprint_gco2': round(immediate_carbon, 2),
                'start_time': 'now',
                'carbon_intensity': current_carbon_intensity,
                'duration_hours': workload_duration_hours
            },
            'optimal_execution': {
                'carbon_footprint_gco2': round(best_window['carbon_footprint_gco2'], 2),
                'start_time': best_window['start_time'],
                'delay_hours': best_window['delay_hours'],
                'carbon_intensity': best_window['avg_carbon_intensity'],
                'duration_hours': workload_duration_hours
            },
            'savings': {
                'gco2': round(savings_gco2, 2),
                'percent': round(savings_percent, 1)
            },
            'recommendation': recommendation,
            'reason': self._get_recommendation_reason(recommendation, savings_percent, best_window['delay_hours']),
            'scheduling_windows': windows[:5],  # Top 5 windows
            'slack_hours': slack_hours,
            'deadline_hours': deadline_hours
        }
    
    def _find_optimal_windows(
        self,
        forecasts: List[Dict],
        workload_duration_hours: float,
        deadline_hours: float,
        vcpu_count: int,
        memory_gb: float
    ) -> List[Dict]:
        """
        Find all possible scheduling windows within deadline.
        
        Returns list of windows sorted by carbon footprint (lowest first).
        """
        windows = []
        
        # Convert duration to number of forecast intervals
        intervals_needed = int(workload_duration_hours)
        if intervals_needed == 0:
            intervals_needed = 1
        
        # Find all possible windows within deadline
        max_start_hour = int(deadline_hours - workload_duration_hours)
        
        for start_hour in range(max_start_hour + 1):
            # Get forecasts for this window
            window_forecasts = forecasts[start_hour:start_hour + intervals_needed]
            
            if len(window_forecasts) < intervals_needed:
                continue
            
            # Calculate average carbon intensity for window
            avg_ci = sum(f['carbon_intensity'] for f in window_forecasts) / len(window_forecasts)
            
            # Calculate carbon footprint
            carbon_footprint = self._calculate_carbon_footprint(
                avg_ci,
                workload_duration_hours,
                vcpu_count,
                memory_gb
            )
            
            # Get start time
            start_time = window_forecasts[0]['timestamp']
            
            windows.append({
                'start_hour': start_hour,
                'start_time': start_time,
                'delay_hours': start_hour,
                'avg_carbon_intensity': round(avg_ci, 2),
                'carbon_footprint_gco2': round(carbon_footprint, 2),
                'window_forecasts': window_forecasts
            })
        
        # Sort by carbon footprint (lowest first)
        windows.sort(key=lambda w: w['carbon_footprint_gco2'])
        
        return windows
    
    def _calculate_carbon_footprint(
        self,
        carbon_intensity: float,
        duration_hours: float,
        vcpu_count: int,
        memory_gb: float
    ) -> float:
        """
        Calculate carbon footprint for workload.
        
        Uses TEADS methodology:
        - CPU: vCPU * 10W * hours / 1000 = kWh
        - Memory: GB * 0.000392 * hours = kWh
        - PUE: 1.135 (AWS average)
        """
        # CPU energy
        cpu_power_w = vcpu_count * 10  # 10W per vCPU (average)
        cpu_energy_kwh = (cpu_power_w * duration_hours) / 1000
        
        # Memory energy
        memory_energy_kwh = memory_gb * 0.000392 * duration_hours
        
        # Total energy with PUE
        total_energy_kwh = (cpu_energy_kwh + memory_energy_kwh) * 1.135
        
        # Carbon footprint
        carbon_footprint_gco2 = total_energy_kwh * carbon_intensity
        
        return carbon_footprint_gco2
    
    def _determine_recommendation(
        self,
        savings_percent: float,
        delay_hours: float,
        slack_hours: float
    ) -> str:
        """
        Determine scheduling recommendation based on savings and delay.
        
        Categories:
        - DELAY_RECOMMENDED: High savings, reasonable delay
        - DELAY_OPTIONAL: Moderate savings, short delay
        - EXECUTE_NOW: Low savings or long delay
        """
        # High savings (>20%) - recommend delay even if longer
        if savings_percent >= 20:
            return 'DELAY_RECOMMENDED'
        
        # Moderate savings (10-20%) - recommend if delay is short
        if savings_percent >= 10 and delay_hours <= slack_hours * 0.5:
            return 'DELAY_OPTIONAL'
        
        # Low savings (<10%) or long delay - execute now
        return 'EXECUTE_NOW'
    
    def _get_recommendation_reason(
        self,
        recommendation: str,
        savings_percent: float,
        delay_hours: float
    ) -> str:
        """Get human-readable reason for recommendation."""
        if recommendation == 'DELAY_RECOMMENDED':
            return f'High carbon savings ({savings_percent:.1f}%) justify {delay_hours:.1f}h delay'
        elif recommendation == 'DELAY_OPTIONAL':
            return f'Moderate savings ({savings_percent:.1f}%) with short {delay_hours:.1f}h delay'
        else:
            return f'Low savings ({savings_percent:.1f}%) or long delay - execute immediately'
    
    def _fallback_immediate_execution(
        self,
        current_ci: float,
        duration_hours: float,
        vcpu_count: int,
        memory_gb: float
    ) -> Dict:
        """Fallback when forecast unavailable."""
        carbon = self._calculate_carbon_footprint(
            current_ci,
            duration_hours,
            vcpu_count,
            memory_gb
        )
        
        return {
            'immediate_execution': {
                'carbon_footprint_gco2': round(carbon, 2),
                'start_time': 'now',
                'carbon_intensity': current_ci
            },
            'optimal_execution': None,
            'savings': {'percent': 0, 'gco2': 0},
            'recommendation': 'EXECUTE_NOW',
            'reason': 'Forecast unavailable - executing immediately',
            'scheduling_windows': []
        }
    
    def calculate_slack_time(
        self,
        workload_duration_hours: float,
        deadline_hours: float
    ) -> Dict:
        """
        Calculate available slack time.
        
        Returns:
            {
                'slack_hours': float,
                'slack_percent': float,
                'flexibility': str  # 'HIGH', 'MEDIUM', 'LOW', 'NONE'
            }
        """
        slack_hours = deadline_hours - workload_duration_hours
        
        if slack_hours < 0:
            return {
                'slack_hours': 0,
                'slack_percent': 0,
                'flexibility': 'NONE',
                'error': 'Deadline shorter than workload duration'
            }
        
        slack_percent = (slack_hours / workload_duration_hours * 100) if workload_duration_hours > 0 else 0
        
        # Determine flexibility level
        if slack_percent >= 100:
            flexibility = 'HIGH'
        elif slack_percent >= 50:
            flexibility = 'MEDIUM'
        elif slack_percent > 0:
            flexibility = 'LOW'
        else:
            flexibility = 'NONE'
        
        return {
            'slack_hours': round(slack_hours, 2),
            'slack_percent': round(slack_percent, 1),
            'flexibility': flexibility,
            'workload_duration_hours': workload_duration_hours,
            'deadline_hours': deadline_hours
        }


# Example usage
if __name__ == '__main__':
    scheduler = SlackAwareScheduler()
    
    # Example: 4-hour test suite with 12-hour deadline
    result = scheduler.optimize_schedule(
        region='eu-west-2',
        workload_duration_hours=4,
        deadline_hours=12,
        current_carbon_intensity=250,
        vcpu_count=8,
        memory_gb=16
    )
    
    print("=== Slack-Aware Scheduling Result ===")
    print(f"Immediate: {result['immediate_execution']['carbon_footprint_gco2']} gCO2")
    if result['optimal_execution']:
        print(f"Optimal: {result['optimal_execution']['carbon_footprint_gco2']} gCO2")
        print(f"Savings: {result['savings']['percent']}%")
        print(f"Delay: {result['optimal_execution']['delay_hours']} hours")
    print(f"Recommendation: {result['recommendation']}")
    print(f"Reason: {result['reason']}")
