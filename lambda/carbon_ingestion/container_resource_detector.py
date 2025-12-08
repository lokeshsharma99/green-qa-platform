"""
Container Resource Detector
Auto-detect CPU and memory limits for Docker and Kubernetes containers
"""

import os
import re
from typing import Dict, Optional, Tuple


def read_cgroup_file(path: str) -> Optional[str]:
    """Safely read a cgroup file"""
    try:
        with open(path, 'r') as f:
            return f.read().strip()
    except (FileNotFoundError, PermissionError):
        return None


def parse_k8s_memory(memory_str: str) -> float:
    """
    Parse Kubernetes memory format to GB
    
    Examples:
        "4Gi" -> 4.0
        "2048Mi" -> 2.0
        "1G" -> 1.0
        "512M" -> 0.5
    """
    if not memory_str:
        return 0.0
    
    # Remove whitespace
    memory_str = memory_str.strip()
    
    # Parse with regex
    match = re.match(r'^(\d+(?:\.\d+)?)\s*([KMGT]i?)?$', memory_str, re.IGNORECASE)
    if not match:
        return 0.0
    
    value = float(match.group(1))
    unit = match.group(2) or ''
    
    # Convert to GB
    unit_upper = unit.upper()
    if unit_upper in ['G', 'GI']:
        return value
    elif unit_upper in ['M', 'MI']:
        return value / 1024
    elif unit_upper in ['K', 'KI']:
        return value / (1024 * 1024)
    elif unit_upper in ['T', 'TI']:
        return value * 1024
    else:
        # Assume bytes
        return value / (1024 ** 3)


def detect_docker_resources() -> Optional[Tuple[float, float]]:
    """
    Detect Docker container resource limits from cgroups
    
    Returns: (vcpu, memory_gb) or None if not in Docker
    """
    # Check if running in Docker
    if not os.path.exists('/.dockerenv'):
        return None
    
    vcpu = None
    memory_gb = None
    
    # Try cgroups v2 first (newer Docker)
    cpu_max = read_cgroup_file('/sys/fs/cgroup/cpu.max')
    if cpu_max:
        parts = cpu_max.split()
        if len(parts) == 2 and parts[0] != 'max':
            quota = int(parts[0])
            period = int(parts[1])
            vcpu = quota / period
    
    # Fallback to cgroups v1
    if vcpu is None:
        cpu_quota = read_cgroup_file('/sys/fs/cgroup/cpu/cpu.cfs_quota_us')
        cpu_period = read_cgroup_file('/sys/fs/cgroup/cpu/cpu.cfs_period_us')
        
        if cpu_quota and cpu_period:
            quota = int(cpu_quota)
            period = int(cpu_period)
            if quota > 0:  # -1 means unlimited
                vcpu = quota / period
    
    # Memory limit (cgroups v2)
    memory_max = read_cgroup_file('/sys/fs/cgroup/memory.max')
    if memory_max and memory_max != 'max':
        memory_gb = int(memory_max) / (1024 ** 3)
    
    # Memory limit (cgroups v1)
    if memory_gb is None:
        memory_limit = read_cgroup_file('/sys/fs/cgroup/memory/memory.limit_in_bytes')
        if memory_limit:
            limit = int(memory_limit)
            # Check if it's not the default "unlimited" value
            if limit < (1024 ** 4):  # Less than 1 TB (reasonable limit)
                memory_gb = limit / (1024 ** 3)
    
    # If we found at least one value, return
    if vcpu is not None or memory_gb is not None:
        return (vcpu, memory_gb)
    
    return None


def detect_kubernetes_resources() -> Optional[Tuple[float, float]]:
    """
    Detect Kubernetes pod resource limits from environment variables
    
    Returns: (vcpu, memory_gb) or None if not in Kubernetes
    """
    # Check if running in Kubernetes
    if not os.getenv('KUBERNETES_SERVICE_HOST'):
        return None
    
    vcpu = None
    memory_gb = None
    
    # Try standard Kubernetes downward API env vars
    # These need to be configured in the pod spec
    cpu_limit = os.getenv('KUBERNETES_CPU_LIMIT') or os.getenv('K8S_CPU_LIMIT')
    memory_limit = os.getenv('KUBERNETES_MEMORY_LIMIT') or os.getenv('K8S_MEMORY_LIMIT')
    
    if cpu_limit:
        try:
            vcpu = float(cpu_limit)
        except ValueError:
            pass
    
    if memory_limit:
        memory_gb = parse_k8s_memory(memory_limit)
    
    # Fallback: Try to read from cgroups (Kubernetes uses cgroups too)
    if vcpu is None or memory_gb is None:
        docker_resources = detect_docker_resources()
        if docker_resources:
            docker_vcpu, docker_memory = docker_resources
            if vcpu is None:
                vcpu = docker_vcpu
            if memory_gb is None:
                memory_gb = docker_memory
    
    if vcpu is not None or memory_gb is not None:
        return (vcpu, memory_gb)
    
    return None


def get_system_resources() -> Tuple[float, float]:
    """
    Get system resources (fallback for VMs)
    
    Returns: (vcpu, memory_gb)
    """
    # CPU count
    vcpu = float(os.cpu_count() or 2)
    
    # Total memory
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if line.startswith('MemTotal:'):
                    # MemTotal is in kB
                    mem_kb = int(line.split()[1])
                    memory_gb = mem_kb / (1024 ** 2)
                    return (vcpu, memory_gb)
    except (FileNotFoundError, PermissionError):
        pass
    
    # Fallback: assume 2 GB per vCPU (common ratio)
    memory_gb = vcpu * 2
    
    return (vcpu, memory_gb)


def detect_container_resources() -> Dict[str, any]:
    """
    Auto-detect container or VM resources
    
    Returns: Dict with vcpu, memory_gb, runtime, and detection_method
    """
    # Try Kubernetes first
    k8s_resources = detect_kubernetes_resources()
    if k8s_resources:
        vcpu, memory_gb = k8s_resources
        return {
            'vcpu': vcpu or get_system_resources()[0],
            'memory_gb': memory_gb or get_system_resources()[1],
            'runtime': 'kubernetes',
            'detection_method': 'kubernetes_env_vars',
            'is_container': True
        }
    
    # Try Docker
    docker_resources = detect_docker_resources()
    if docker_resources:
        vcpu, memory_gb = docker_resources
        return {
            'vcpu': vcpu or get_system_resources()[0],
            'memory_gb': memory_gb or get_system_resources()[1],
            'runtime': 'docker',
            'detection_method': 'cgroups',
            'is_container': True
        }
    
    # Fallback: VM or bare metal
    vcpu, memory_gb = get_system_resources()
    return {
        'vcpu': vcpu,
        'memory_gb': memory_gb,
        'runtime': 'vm',
        'detection_method': 'system',
        'is_container': False
    }


def estimate_container_overhead(is_container: bool, vcpu: float) -> float:
    """
    Estimate container runtime overhead
    
    Returns: Additional vCPU overhead
    """
    if not is_container:
        return 0.0
    
    # Container runtime overhead: ~10% of allocated resources
    # Includes: Docker daemon, containerd, kernel overhead
    return vcpu * 0.10


# Example usage and testing
if __name__ == '__main__':
    print("="*70)
    print(" Container Resource Detector")
    print("="*70)
    
    # Detect resources
    resources = detect_container_resources()
    
    print(f"\n📊 Detected Resources:")
    print(f"   vCPU: {resources['vcpu']:.2f}")
    print(f"   Memory: {resources['memory_gb']:.2f} GB")
    print(f"   Runtime: {resources['runtime']}")
    print(f"   Detection Method: {resources['detection_method']}")
    print(f"   Is Container: {resources['is_container']}")
    
    if resources['is_container']:
        overhead = estimate_container_overhead(True, resources['vcpu'])
        print(f"\n⚠️  Container Overhead:")
        print(f"   Additional vCPU: {overhead:.2f}")
        print(f"   Total vCPU (with overhead): {resources['vcpu'] + overhead:.2f}")
    
    # Test Kubernetes memory parsing
    print(f"\n🧪 Kubernetes Memory Parsing Tests:")
    test_cases = [
        "4Gi",
        "2048Mi",
        "1G",
        "512M",
        "1024Ki",
        "4294967296"  # 4 GB in bytes
    ]
    
    for test in test_cases:
        result = parse_k8s_memory(test)
        print(f"   {test:15s} -> {result:.2f} GB")
    
    print(f"\n{'='*70}\n")
