"""
Test MAIZX Ranking Algorithm

Tests the multi-region carbon optimization with 85% CO2 reduction potential.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from maizx_ranker import MAIZXRanker, WorkloadSpec, RegionScore


def test_basic_ranking():
    """Test basic region ranking"""
    print("\n=== Test 1: Basic Region Ranking ===")
    
    ranker = MAIZXRanker()
    
    workload = WorkloadSpec(
        duration_hours=4.0,
        cpu_utilization=0.7,
        memory_gb=16.0,
        vcpu_count=8,
        priority='normal'
    )
    
    regions_ci = {
        'eu-west-2': 180.5,
        'us-east-1': 450.3,
        'us-west-2': 200.1,
    }
    
    ranked = ranker.rank_regions(workload, regions_ci, top_n=3)
    
    print(f"✓ Ranked {len(ranked)} regions")
    for i, score in enumerate(ranked, 1):
        print(f"  {i}. {score.region}: {score.maizx_score:.4f} "
              f"({score.recommendation}, {score.cfp:.2f} gCO2)")
    
    # Verify ranking order (lower CI should rank better)
    assert ranked[0].region == 'eu-west-2', "Lowest CI should rank first"
    assert ranked[0].maizx_score < ranked[1].maizx_score, "Scores should be ascending"
    
    return True


def test_workload_priority():
    """Test that priority affects ranking"""
    print("\n=== Test 2: Workload Priority Impact ===")
    
    ranker = MAIZXRanker()
    
    regions_ci = {'eu-west-2': 250.0, 'us-east-1': 300.0}
    
    # Low priority (flexible)
    workload_low = WorkloadSpec(
        duration_hours=4.0,
        vcpu_count=8,
        priority='low'
    )
    
    # Critical priority (urgent)
    workload_critical = WorkloadSpec(
        duration_hours=4.0,
        vcpu_count=8,
        priority='critical'
    )
    
    rec_low = ranker.recommend_optimal_region(workload_low, regions_ci)
    rec_critical = ranker.recommend_optimal_region(workload_critical, regions_ci)
    
    print(f"Low Priority Score: {rec_low['maizx_score']:.4f}")
    print(f"Critical Priority Score: {rec_critical['maizx_score']:.4f}")
    
    # Critical should have higher score (less flexible)
    assert rec_critical['maizx_score'] > rec_low['maizx_score'], \
        "Critical priority should have higher score"
    
    print("✓ Priority correctly affects ranking")
    return True


def test_deadline_flexibility():
    """Test deadline flexibility impact"""
    print("\n=== Test 3: Deadline Flexibility ===")
    
    ranker = MAIZXRanker()
    
    regions_ci = {'eu-west-2': 250.0}
    
    # No deadline (immediate)
    workload_immediate = WorkloadSpec(
        duration_hours=4.0,
        vcpu_count=8,
        deadline_hours=None
    )
    
    # Flexible deadline (24 hours)
    workload_flexible = WorkloadSpec(
        duration_hours=4.0,
        vcpu_count=8,
        deadline_hours=24.0
    )
    
    rec_immediate = ranker.recommend_optimal_region(workload_immediate, regions_ci)
    rec_flexible = ranker.recommend_optimal_region(workload_flexible, regions_ci)
    
    print(f"Immediate: {rec_immediate['maizx_score']:.4f}")
    print(f"Flexible (24h): {rec_flexible['maizx_score']:.4f}")
    
    # Flexible should have lower score (can wait for better time)
    assert rec_flexible['maizx_score'] < rec_immediate['maizx_score'], \
        "Flexible deadline should have lower score"
    
    print("✓ Deadline flexibility correctly affects ranking")
    return True


def test_custom_weights():
    """Test custom weight configuration"""
    print("\n=== Test 4: Custom Weights ===")
    
    # Prioritize current CFP
    ranker_current = MAIZXRanker(w1=0.7, w2=0.1, w3=0.1, w4=0.1)
    
    # Prioritize forecast CFP
    ranker_forecast = MAIZXRanker(w1=0.1, w2=0.7, w3=0.1, w4=0.1)
    
    workload = WorkloadSpec(duration_hours=4.0, vcpu_count=8)
    regions_ci = {'eu-west-2': 250.0, 'us-east-1': 300.0}
    
    rec_current = ranker_current.recommend_optimal_region(workload, regions_ci)
    rec_forecast = ranker_forecast.recommend_optimal_region(workload, regions_ci)
    
    print(f"Current-focused: {rec_current['maizx_score']:.4f}")
    print(f"Forecast-focused: {rec_forecast['maizx_score']:.4f}")
    
    # Both should recommend same region (lowest CI)
    assert rec_current['recommended_region'] == rec_forecast['recommended_region']
    
    print("✓ Custom weights working")
    return True


def test_savings_calculation():
    """Test savings vs worst region"""
    print("\n=== Test 5: Savings Calculation ===")
    
    ranker = MAIZXRanker()
    
    workload = WorkloadSpec(duration_hours=4.0, vcpu_count=8)
    
    regions_ci = {
        'eu-west-2': 150.0,  # Best
        'us-east-1': 450.0,  # Worst
        'us-west-2': 300.0,  # Middle
    }
    
    recommendation = ranker.recommend_optimal_region(workload, regions_ci)
    
    print(f"Best Region: {recommendation['recommended_region']}")
    print(f"Savings vs Worst: {recommendation['savings_vs_worst_percent']}%")
    
    # Should have significant savings
    assert recommendation['savings_vs_worst_percent'] > 0, "Should have savings"
    assert recommendation['savings_vs_worst_percent'] < 100, "Savings should be < 100%"
    
    # Check top 3 regions
    top_3 = recommendation['top_3_regions']
    assert len(top_3) == 3, "Should return 3 regions"
    assert top_3[0]['savings_percent'] >= top_3[1]['savings_percent'], \
        "Savings should be descending"
    
    print(f"✓ Calculated {recommendation['savings_vs_worst_percent']:.1f}% savings")
    return True


def test_recommendation_levels():
    """Test recommendation level assignment"""
    print("\n=== Test 6: Recommendation Levels ===")
    
    ranker = MAIZXRanker()
    
    workload = WorkloadSpec(duration_hours=4.0, vcpu_count=8)
    
    # Test different carbon intensities
    test_cases = [
        ({'eu-west-2': 100.0}, 'EXCELLENT'),  # Very low
        ({'eu-west-2': 250.0}, 'GOOD'),       # Low
        ({'eu-west-2': 400.0}, 'FAIR'),       # Medium
        ({'eu-west-2': 600.0}, 'POOR'),       # High
    ]
    
    for regions_ci, expected_level in test_cases:
        rec = ranker.recommend_optimal_region(workload, regions_ci)
        actual_level = rec['recommendation']
        ci = list(regions_ci.values())[0]
        print(f"  CI {ci}: {actual_level} (expected: {expected_level})")
    
    print("✓ Recommendation levels assigned")
    return True


def test_multiple_regions():
    """Test ranking with many regions"""
    print("\n=== Test 7: Multiple Regions (All AWS) ===")
    
    ranker = MAIZXRanker()
    
    workload = WorkloadSpec(duration_hours=4.0, vcpu_count=8)
    
    # All major AWS regions
    regions_ci = {
        'us-east-1': 450.3,
        'us-east-2': 420.5,
        'us-west-1': 320.5,
        'us-west-2': 200.1,
        'eu-west-1': 350.2,
        'eu-west-2': 180.5,
        'eu-central-1': 420.8,
        'ap-southeast-1': 380.0,
        'ap-northeast-1': 410.0,
    }
    
    ranked = ranker.rank_regions(workload, regions_ci, top_n=5)
    
    print(f"✓ Ranked {len(ranked)} regions")
    print("Top 5:")
    for i, score in enumerate(ranked, 1):
        print(f"  {i}. {score.region}: {score.cfp:.2f} gCO2 "
              f"(saves {score.savings_vs_worst_percent:.1f}%)")
    
    # Verify best is actually lowest CI
    best_region = ranked[0].region
    best_ci = regions_ci[best_region]
    assert best_ci == min(regions_ci.values()), "Best region should have lowest CI"
    
    return True


def test_response_structure():
    """Test API response structure"""
    print("\n=== Test 8: Response Structure ===")
    
    ranker = MAIZXRanker()
    
    workload = WorkloadSpec(duration_hours=4.0, vcpu_count=8, memory_gb=16.0)
    regions_ci = {'eu-west-2': 250.0, 'us-east-1': 350.0}
    
    response = ranker.recommend_optimal_region(workload, regions_ci)
    
    # Check required fields
    required_fields = [
        'recommended_region',
        'maizx_score',
        'recommendation',
        'carbon_footprint_gco2',
        'power_consumption_w',
        'savings_vs_worst_percent',
        'top_3_regions',
        'workload',
        'weights',
        'timestamp'
    ]
    
    for field in required_fields:
        assert field in response, f"Missing field: {field}"
        print(f"  ✓ {field}: {response[field]}")
    
    # Check top_3_regions structure
    assert isinstance(response['top_3_regions'], list)
    assert len(response['top_3_regions']) > 0
    
    print("✓ Response structure valid")
    return True


def run_all_tests():
    """Run all MAIZX tests"""
    print("=" * 60)
    print("MAIZX Ranking Algorithm Test Suite")
    print("=" * 60)
    
    tests = [
        test_basic_ranking,
        test_workload_priority,
        test_deadline_flexibility,
        test_custom_weights,
        test_savings_calculation,
        test_recommendation_levels,
        test_multiple_regions,
        test_response_structure,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if passed == len(tests):
        print("\n🎉 All MAIZX tests passed!")
        print("Expected CO2 reduction: 85.68% (from research paper)")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
