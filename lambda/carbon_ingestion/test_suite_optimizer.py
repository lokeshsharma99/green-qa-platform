"""
Test Suite Optimizer
Analyzes test suites and provides actionable recommendations to reduce energy consumption
"""

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class OptimizationType(Enum):
    """Types of optimizations"""
    PARALLELIZATION = "parallelization"
    TEST_SELECTION = "test_selection"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    EXECUTION_ORDER = "execution_order"
    CLEANUP = "cleanup"
    CACHING = "caching"
    INFRASTRUCTURE = "infrastructure"


class Priority(Enum):
    """Optimization priority levels"""
    CRITICAL = "critical"  # >30% potential savings
    HIGH = "high"          # 15-30% potential savings
    MEDIUM = "medium"      # 5-15% potential savings
    LOW = "low"            # <5% potential savings


@dataclass
class Optimization:
    """Single optimization recommendation"""
    type: OptimizationType
    priority: Priority
    title: str
    description: str
    potential_savings_percent: float
    potential_savings_j: float
    potential_savings_co2_g: float
    effort: str  # "low", "medium", "high"
    implementation_steps: List[str]
    code_example: str = ""
    affected_tests: List[str] = None


class TestSuiteOptimizer:
    """Analyzes test suites and provides optimization recommendations"""
    
    def __init__(self):
        self.carbon_intensity = 436  # gCO2/kWh (global average)
    
    def analyze_test_suite(
        self,
        profile_data: Dict[str, Any],
        test_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze test suite and generate optimization recommendations
        
        Args:
            profile_data: Energy profile with components and phases
            test_metadata: Optional metadata about tests (duration, dependencies, etc.)
        
        Returns:
            Dictionary with analysis and recommendations
        """
        total_energy = sum(profile_data.get('components', {}).values())
        phases = profile_data.get('phases', [])
        
        # Analyze different aspects
        recommendations = []
        
        # 1. Analyze parallelization opportunities
        recommendations.extend(self._analyze_parallelization(phases, total_energy))
        
        # 2. Analyze test selection opportunities
        recommendations.extend(self._analyze_test_selection(phases, total_energy, test_metadata))
        
        # 3. Analyze resource optimization
        recommendations.extend(self._analyze_resource_optimization(
            profile_data.get('components', {}), total_energy
        ))
        
        # 4. Analyze execution order
        recommendations.extend(self._analyze_execution_order(phases, total_energy))
        
        # 5. Analyze cleanup opportunities
        recommendations.extend(self._analyze_cleanup(phases, total_energy))
        
        # 6. Analyze caching opportunities
        recommendations.extend(self._analyze_caching(phases, total_energy))
        
        # 7. Analyze infrastructure optimization
        recommendations.extend(self._analyze_infrastructure(
            profile_data.get('components', {}), total_energy
        ))
        
        # Sort by potential savings
        recommendations.sort(key=lambda x: x.potential_savings_percent, reverse=True)
        
        # Calculate total potential savings
        total_potential_savings_j = sum(r.potential_savings_j for r in recommendations)
        total_potential_savings_percent = (total_potential_savings_j / total_energy * 100) if total_energy > 0 else 0
        total_potential_savings_co2_g = self._energy_to_carbon(total_potential_savings_j)
        
        return {
            'total_energy_j': total_energy,
            'total_carbon_g': self._energy_to_carbon(total_energy),
            'recommendations': [self._optimization_to_dict(r) for r in recommendations],
            'total_potential_savings': {
                'energy_j': total_potential_savings_j,
                'energy_percent': total_potential_savings_percent,
                'carbon_g': total_potential_savings_co2_g,
                'carbon_equivalent': self._get_carbon_equivalent(total_potential_savings_co2_g)
            },
            'priority_breakdown': self._get_priority_breakdown(recommendations),
            'quick_wins': self._get_quick_wins(recommendations),
            'implementation_roadmap': self._generate_roadmap(recommendations)
        }
    
    def _analyze_parallelization(self, phases: List[Dict], total_energy: float) -> List[Optimization]:
        """Analyze opportunities for parallel test execution"""
        recommendations = []
        
        # Check if tests are running sequentially
        sequential_phases = [p for p in phases if 'test' in p.get('name', '').lower()]
        
        if len(sequential_phases) > 1:
            # Estimate savings from parallelization (typically 30-50% for independent tests)
            total_test_energy = sum(p.get('energy_j', 0) for p in sequential_phases)
            potential_savings = total_test_energy * 0.35  # Conservative 35% estimate
            
            recommendations.append(Optimization(
                type=OptimizationType.PARALLELIZATION,
                priority=Priority.CRITICAL if (potential_savings / total_energy) > 0.3 else Priority.HIGH,
                title="Parallelize Independent Tests",
                description=f"Running {len(sequential_phases)} test phases sequentially. "
                           f"Parallelizing independent tests can reduce execution time and energy by 30-50%.",
                potential_savings_percent=(potential_savings / total_energy * 100),
                potential_savings_j=potential_savings,
                potential_savings_co2_g=self._energy_to_carbon(potential_savings),
                effort="medium",
                implementation_steps=[
                    "Identify independent tests (no shared state/resources)",
                    "Configure test runner for parallel execution (e.g., pytest -n auto)",
                    "Set optimal worker count (typically CPU cores - 1)",
                    "Add test isolation (separate databases, temp directories)",
                    "Monitor for race conditions and flaky tests"
                ],
                code_example="""# pytest.ini
[pytest]
addopts = -n auto --dist loadscope

# Or in CI/CD
pytest -n 4 --dist loadfile tests/""",
                affected_tests=[p.get('name') for p in sequential_phases]
            ))
        
        return recommendations
    
    def _analyze_test_selection(
        self,
        phases: List[Dict],
        total_energy: float,
        test_metadata: Dict = None
    ) -> List[Optimization]:
        """Analyze opportunities for smart test selection"""
        recommendations = []
        
        # Check for long-running tests
        long_phases = [p for p in phases if p.get('duration_s', 0) > 60]
        
        if long_phases:
            long_energy = sum(p.get('energy_j', 0) for p in long_phases)
            potential_savings = long_energy * 0.5  # Run only on main branch
            
            recommendations.append(Optimization(
                type=OptimizationType.TEST_SELECTION,
                priority=Priority.HIGH if (potential_savings / total_energy) > 0.15 else Priority.MEDIUM,
                title="Implement Smart Test Selection",
                description=f"Found {len(long_phases)} long-running test phases (>60s). "
                           f"Run expensive tests only on main branch or nightly builds.",
                potential_savings_percent=(potential_savings / total_energy * 100),
                potential_savings_j=potential_savings,
                potential_savings_co2_g=self._energy_to_carbon(potential_savings),
                effort="low",
                implementation_steps=[
                    "Tag expensive tests with @pytest.mark.slow",
                    "Run fast tests on every commit",
                    "Run slow tests only on main branch or nightly",
                    "Use test impact analysis to run only affected tests",
                    "Implement test prioritization based on failure history"
                ],
                code_example="""# Mark slow tests
@pytest.mark.slow
def test_expensive_operation():
    pass

# CI/CD - Fast tests on PR
pytest -m "not slow" tests/

# CI/CD - All tests on main
pytest tests/""",
                affected_tests=[p.get('name') for p in long_phases]
            ))
        
        return recommendations
    
    def _analyze_resource_optimization(
        self,
        components: Dict[str, float],
        total_energy: float
    ) -> List[Optimization]:
        """Analyze component-level resource optimization"""
        recommendations = []
        
        # Skip if no energy
        if total_energy == 0:
            return recommendations
        
        # Check CPU usage
        cpu_energy = components.get('cpu', 0)
        if cpu_energy / total_energy > 0.5:  # CPU is >50% of total
            potential_savings = cpu_energy * 0.2  # 20% reduction possible
            
            recommendations.append(Optimization(
                type=OptimizationType.RESOURCE_OPTIMIZATION,
                priority=Priority.HIGH,
                title="Optimize CPU-Intensive Operations",
                description=f"CPU consumes {cpu_energy / total_energy * 100:.1f}% of total energy. "
                           f"Optimize algorithms and reduce computational complexity.",
                potential_savings_percent=(potential_savings / total_energy * 100),
                potential_savings_j=potential_savings,
                potential_savings_co2_g=self._energy_to_carbon(potential_savings),
                effort="medium",
                implementation_steps=[
                    "Profile CPU-intensive functions",
                    "Optimize algorithms (reduce O(n²) to O(n log n))",
                    "Use compiled extensions (Cython, Numba)",
                    "Reduce unnecessary computations",
                    "Cache expensive calculations"
                ],
                code_example="""# Before: O(n²)
for i in items:
    for j in items:
        if i == j:
            process(i)

# After: O(n) with set
item_set = set(items)
for i in items:
    if i in item_set:
        process(i)"""
            ))
        
        # Check RAM usage
        ram_energy = components.get('ram', 0)
        if ram_energy / total_energy > 0.3:  # RAM is >30% of total
            potential_savings = ram_energy * 0.25
            
            recommendations.append(Optimization(
                type=OptimizationType.RESOURCE_OPTIMIZATION,
                priority=Priority.MEDIUM,
                title="Reduce Memory Footprint",
                description=f"RAM consumes {ram_energy / total_energy * 100:.1f}% of total energy. "
                           f"Optimize memory usage to reduce energy consumption.",
                potential_savings_percent=(potential_savings / total_energy * 100),
                potential_savings_j=potential_savings,
                potential_savings_co2_g=self._energy_to_carbon(potential_savings),
                effort="medium",
                implementation_steps=[
                    "Use generators instead of lists for large datasets",
                    "Release large objects explicitly (del, gc.collect())",
                    "Use memory-efficient data structures",
                    "Stream data instead of loading all at once",
                    "Reduce test data size"
                ],
                code_example="""# Before: Loads all in memory
data = [process(x) for x in range(1000000)]

# After: Generator (memory efficient)
data = (process(x) for x in range(1000000))

# Or use smaller test datasets
test_data = sample_data[:100]  # Instead of full dataset"""
            ))
        
        # Check Disk I/O
        disk_energy = components.get('disk', 0)
        if disk_energy / total_energy > 0.2:  # Disk is >20% of total
            potential_savings = disk_energy * 0.3
            
            recommendations.append(Optimization(
                type=OptimizationType.RESOURCE_OPTIMIZATION,
                priority=Priority.MEDIUM,
                title="Optimize Disk I/O",
                description=f"Disk I/O consumes {disk_energy / total_energy * 100:.1f}% of total energy. "
                           f"Reduce file operations and use in-memory alternatives.",
                potential_savings_percent=(potential_savings / total_energy * 100),
                potential_savings_j=potential_savings,
                potential_savings_co2_g=self._energy_to_carbon(potential_savings),
                effort="low",
                implementation_steps=[
                    "Use in-memory databases for tests (SQLite :memory:)",
                    "Mock file operations where possible",
                    "Batch file operations",
                    "Use tmpfs for temporary files",
                    "Reduce logging verbosity in tests"
                ],
                code_example="""# Use in-memory database
DATABASE_URL = "sqlite:///:memory:"

# Or tmpfs in CI
pytest --basetemp=/dev/shm/pytest tests/

# Mock file operations
@patch('builtins.open', mock_open(read_data='test'))
def test_file_operation():
    pass"""
            ))
        
        return recommendations
    
    def _analyze_execution_order(self, phases: List[Dict], total_energy: float) -> List[Optimization]:
        """Analyze test execution order optimization"""
        recommendations = []
        
        # Check if there are setup/teardown phases
        setup_phases = [p for p in phases if 'setup' in p.get('name', '').lower() or 'init' in p.get('name', '').lower()]
        
        if len(setup_phases) > 1:
            setup_energy = sum(p.get('energy_j', 0) for p in setup_phases)
            potential_savings = setup_energy * 0.4  # Consolidate setups
            
            recommendations.append(Optimization(
                type=OptimizationType.EXECUTION_ORDER,
                priority=Priority.MEDIUM,
                title="Consolidate Test Setup",
                description=f"Found {len(setup_phases)} separate setup phases. "
                           f"Consolidating setup can reduce redundant initialization.",
                potential_savings_percent=(potential_savings / total_energy * 100),
                potential_savings_j=potential_savings,
                potential_savings_co2_g=self._energy_to_carbon(potential_savings),
                effort="low",
                implementation_steps=[
                    "Use pytest fixtures with appropriate scope (session, module)",
                    "Share expensive setup across tests",
                    "Avoid per-test database resets if not needed",
                    "Use class-level setup for related tests",
                    "Implement lazy initialization"
                ],
                code_example="""# Before: Setup in each test
def test_a():
    db = setup_database()
    # test

def test_b():
    db = setup_database()
    # test

# After: Shared fixture
@pytest.fixture(scope="module")
def db():
    return setup_database()

def test_a(db):
    # test

def test_b(db):
    # test"""
            ))
        
        return recommendations
    
    def _analyze_cleanup(self, phases: List[Dict], total_energy: float) -> List[Optimization]:
        """Analyze cleanup and resource leak opportunities"""
        recommendations = []
        
        # Skip if no energy
        if total_energy == 0:
            return recommendations
        
        # Check for cleanup phases
        cleanup_phases = [p for p in phases if 'cleanup' in p.get('name', '').lower() or 'teardown' in p.get('name', '').lower()]
        
        if not cleanup_phases:
            # No explicit cleanup - potential resource leaks
            potential_savings = total_energy * 0.05  # 5% from proper cleanup
            
            recommendations.append(Optimization(
                type=OptimizationType.CLEANUP,
                priority=Priority.LOW,
                title="Implement Proper Resource Cleanup",
                description="No explicit cleanup phase detected. Proper resource cleanup prevents leaks and reduces energy waste.",
                potential_savings_percent=(potential_savings / total_energy * 100),
                potential_savings_j=potential_savings,
                potential_savings_co2_g=self._energy_to_carbon(potential_savings),
                effort="low",
                implementation_steps=[
                    "Use context managers (with statements)",
                    "Implement pytest fixtures with yield for cleanup",
                    "Close database connections explicitly",
                    "Release file handles",
                    "Clear caches and temporary data"
                ],
                code_example="""# Use context managers
with open('file.txt') as f:
    data = f.read()

# Pytest fixture with cleanup
@pytest.fixture
def resource():
    r = create_resource()
    yield r
    r.cleanup()  # Automatic cleanup

# Explicit cleanup
try:
    conn = db.connect()
    # use connection
finally:
    conn.close()"""
            ))
        
        return recommendations
    
    def _analyze_caching(self, phases: List[Dict], total_energy: float) -> List[Optimization]:
        """Analyze caching opportunities"""
        recommendations = []
        
        # Look for repeated operations
        phase_names = [p.get('name', '') for p in phases]
        repeated = [name for name in phase_names if phase_names.count(name) > 1]
        
        if repeated:
            # Estimate savings from caching
            repeated_energy = sum(p.get('energy_j', 0) for p in phases if p.get('name') in repeated)
            potential_savings = repeated_energy * 0.6  # 60% reduction with caching
            
            recommendations.append(Optimization(
                type=OptimizationType.CACHING,
                priority=Priority.HIGH if (potential_savings / total_energy) > 0.15 else Priority.MEDIUM,
                title="Implement Result Caching",
                description=f"Detected repeated operations. Caching results can eliminate redundant computations.",
                potential_savings_percent=(potential_savings / total_energy * 100),
                potential_savings_j=potential_savings,
                potential_savings_co2_g=self._energy_to_carbon(potential_savings),
                effort="low",
                implementation_steps=[
                    "Use @lru_cache for pure functions",
                    "Cache API responses in tests",
                    "Use pytest-cache for expensive fixtures",
                    "Implement memoization for recursive functions",
                    "Cache compiled regexes and templates"
                ],
                code_example="""from functools import lru_cache

# Cache expensive function
@lru_cache(maxsize=128)
def expensive_computation(x):
    return complex_calculation(x)

# Cache API responses
@pytest.fixture(scope="session")
@pytest.mark.cache
def api_data():
    return fetch_from_api()

# Cache regex compilation
import re
PATTERN = re.compile(r'\\d+')  # Compile once
def process(text):
    return PATTERN.findall(text)"""
            ))
        
        return recommendations
    
    def _analyze_infrastructure(self, components: Dict[str, float], total_energy: float) -> List[Optimization]:
        """Analyze infrastructure optimization opportunities"""
        recommendations = []
        
        # Check if running on oversized infrastructure
        total_power = total_energy / 3600  # Rough estimate of power in Wh
        
        if total_power > 100:  # High power consumption
            potential_savings = total_energy * 0.15  # 15% from right-sizing
            
            recommendations.append(Optimization(
                type=OptimizationType.INFRASTRUCTURE,
                priority=Priority.MEDIUM,
                title="Right-Size Test Infrastructure",
                description=f"High power consumption detected ({total_power:.0f} Wh). "
                           f"Consider using smaller instances or spot instances.",
                potential_savings_percent=(potential_savings / total_energy * 100),
                potential_savings_j=potential_savings,
                potential_savings_co2_g=self._energy_to_carbon(potential_savings),
                effort="low",
                implementation_steps=[
                    "Profile actual resource usage",
                    "Use smaller EC2 instances (t3.medium instead of t3.xlarge)",
                    "Use spot instances for non-critical tests (60-90% cost savings)",
                    "Run tests in containers with resource limits",
                    "Use ARM-based instances (Graviton) for better efficiency"
                ],
                code_example="""# GitHub Actions - Use smaller runner
runs-on: ubuntu-latest  # Instead of self-hosted large runner

# Docker resource limits
docker run --cpus="2" --memory="4g" test-runner

# AWS - Use Graviton instances
instance_type: t4g.medium  # ARM-based, more efficient

# Spot instances in CI
spot_instance: true
max_price: "0.05"  # 60-90% cheaper"""
            ))
        
        return recommendations
    
    def _energy_to_carbon(self, energy_j: float) -> float:
        """Convert energy (J) to carbon (g CO₂)"""
        energy_kwh = energy_j / 3600000
        return energy_kwh * self.carbon_intensity
    
    def _get_carbon_equivalent(self, carbon_g: float) -> str:
        """Get human-readable carbon equivalent"""
        if carbon_g < 8:
            return f"{(carbon_g / 8 * 60):.0f} seconds of phone charging"
        elif carbon_g < 80:
            return f"{(carbon_g / 8):.1f} phone charges"
        else:
            return f"{(carbon_g / 404):.2f} miles driven"
    
    def _optimization_to_dict(self, opt: Optimization) -> Dict:
        """Convert Optimization to dictionary"""
        return {
            'type': opt.type.value,
            'priority': opt.priority.value,
            'title': opt.title,
            'description': opt.description,
            'potential_savings': {
                'percent': round(opt.potential_savings_percent, 1),
                'energy_j': round(opt.potential_savings_j, 2),
                'carbon_g': round(opt.potential_savings_co2_g, 4),
                'carbon_equivalent': self._get_carbon_equivalent(opt.potential_savings_co2_g)
            },
            'effort': opt.effort,
            'implementation_steps': opt.implementation_steps,
            'code_example': opt.code_example,
            'affected_tests': opt.affected_tests or []
        }
    
    def _get_priority_breakdown(self, recommendations: List[Optimization]) -> Dict:
        """Get breakdown by priority"""
        breakdown = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        for rec in recommendations:
            breakdown[rec.priority.value].append(rec.title)
        
        return {
            'critical': {'count': len(breakdown['critical']), 'items': breakdown['critical']},
            'high': {'count': len(breakdown['high']), 'items': breakdown['high']},
            'medium': {'count': len(breakdown['medium']), 'items': breakdown['medium']},
            'low': {'count': len(breakdown['low']), 'items': breakdown['low']}
        }
    
    def _get_quick_wins(self, recommendations: List[Optimization]) -> List[Dict]:
        """Get quick wins (high impact, low effort)"""
        quick_wins = [
            r for r in recommendations
            if r.effort == "low" and r.priority in [Priority.CRITICAL, Priority.HIGH]
        ]
        
        return [self._optimization_to_dict(r) for r in quick_wins[:3]]  # Top 3
    
    def _generate_roadmap(self, recommendations: List[Optimization]) -> Dict:
        """Generate implementation roadmap"""
        return {
            'phase_1_immediate': {
                'title': 'Quick Wins (Week 1)',
                'items': [r.title for r in recommendations if r.effort == "low" and r.priority == Priority.CRITICAL]
            },
            'phase_2_short_term': {
                'title': 'High Impact (Weeks 2-4)',
                'items': [r.title for r in recommendations if r.priority == Priority.HIGH]
            },
            'phase_3_medium_term': {
                'title': 'Medium Impact (Month 2)',
                'items': [r.title for r in recommendations if r.priority == Priority.MEDIUM]
            },
            'phase_4_long_term': {
                'title': 'Continuous Improvement (Ongoing)',
                'items': [r.title for r in recommendations if r.priority == Priority.LOW]
            }
        }
