# ZeroCarb Database Schema

## DynamoDB Tables Design

### 1. Pipeline Executions Table
**Table Name**: `pipeline_executions`
**Partition Key**: `execution_id` (String)
**Sort Key**: `timestamp` (Number)

```json
{
  "execution_id": "fe1a69cb-ee5a-48ea-819d-f0092b8447a6",
  "timestamp": 1702551000,
  "pipeline_name": "GDSDemoAppPipeline-Pipeline-mfCJVEV8nKQS",
  "pipeline_region": "eu-west-2",
  "trigger_source": "zerocarb_manual",
  "status": "SUCCESS",
  
  // Carbon Intelligence
  "carbon_analysis": {
    "decision": "RUN_NOW",
    "reason": "Current region has acceptable carbon intensity",
    "default_region": "eu-west-2",
    "default_intensity": 16.1,
    "optimal_region": "eu-west-2", 
    "optimal_intensity": 16.1,
    "savings_g": 0.0,
    "savings_percent": 0.0
  },
  
  // Workload Details
  "workload": {
    "duration_minutes": 40,
    "vcpu_count": 2,
    "memory_gb": 3,
    "energy_kwh": 0.016023,
    "sci_score": 3.5913
  },
  
  // Regional Context
  "regional_snapshot": {
    "eu-north-1": 16,
    "eu-west-2": 16.1,
    "eu-west-3": 26,
    "eu-central-2": 26,
    "eu-west-1": 143,
    "eu-central-1": 257
  },
  
  // Data Sources
  "data_sources": {
    "uk_grid_eso": {
      "grid_intensity": 71,
      "index": "low",
      "renewable_pct": 0.8,
      "datacenter_intensity": 16.1
    },
    "electricity_maps": {
      "regions_fetched": ["eu-north-1", "eu-west-3", "eu-west-1", "eu-central-1", "eu-central-2"],
      "success_rate": 1.0
    }
  },
  
  // Configuration
  "config": {
    "auto_trigger": true,
    "min_savings_defer": 15,
    "max_defer_hours": 24,
    "pipeline_timeout": 30
  },
  
  // Metadata
  "created_at": "2025-12-14T10:30:00Z",
  "ttl": 1734551000  // 1 year retention
}
```

### 2. Carbon Intensity History Table
**Table Name**: `carbon_intensity_history`
**Partition Key**: `region` (String)
**Sort Key**: `timestamp` (Number)

```json
{
  "region": "eu-west-2",
  "timestamp": 1702551000,
  "intensity": 16.1,
  "grid_intensity": 71,
  "renewable_pct": 0.8,
  "pue": 1.15,
  "index": "low",
  "source": "uk-grid-eso",
  "is_realtime": true,
  "ttl": 1705143000  // 30 days retention
}
```

### 3. Pipeline Performance Analytics Table
**Table Name**: `pipeline_analytics`
**Partition Key**: `pipeline_name` (String)
**Sort Key**: `date` (String, format: YYYY-MM-DD)

```json
{
  "pipeline_name": "GDSDemoAppPipeline-Pipeline-mfCJVEV8nKQS",
  "date": "2025-12-14",
  
  // Daily Aggregations
  "executions": {
    "total": 5,
    "successful": 4,
    "failed": 1,
    "success_rate": 0.8
  },
  
  // Carbon Metrics
  "carbon": {
    "total_emissions_g": 17.96,
    "avg_emissions_g": 3.59,
    "total_savings_g": 2.45,
    "avg_savings_percent": 12.5,
    "cleanest_region_used": "eu-north-1",
    "dirtiest_region_used": "eu-central-1"
  },
  
  // Performance Metrics
  "performance": {
    "avg_duration_minutes": 38,
    "avg_energy_kwh": 0.015,
    "avg_sci_score": 3.45,
    "total_vcpu_hours": 6.67,
    "total_memory_gb_hours": 10.0
  },
  
  // Decision Analytics
  "decisions": {
    "run_now": 3,
    "defer": 1,
    "relocate": 1,
    "defer_success_rate": 1.0,
    "avg_defer_hours": 2.5
  },
  
  "updated_at": "2025-12-14T23:59:59Z",
  "ttl": 1734551000  // 1 year retention
}
```

### 4. Regional Optimization Insights Table
**Table Name**: `regional_insights`
**Partition Key**: `date` (String, format: YYYY-MM-DD)
**Sort Key**: `hour` (Number, 0-23)

```json
{
  "date": "2025-12-14",
  "hour": 10,
  
  // Hourly Regional Rankings
  "rankings": [
    {"region": "eu-north-1", "intensity": 16, "rank": 1},
    {"region": "eu-west-2", "intensity": 16.1, "rank": 2},
    {"region": "eu-west-3", "intensity": 26, "rank": 3},
    {"region": "eu-central-2", "intensity": 26, "rank": 4},
    {"region": "eu-west-1", "intensity": 143, "rank": 5},
    {"region": "eu-central-1", "intensity": 257, "rank": 6}
  ],
  
  // Optimization Opportunities
  "opportunities": {
    "max_savings_percent": 93.7,  // (257-16)/257
    "best_region": "eu-north-1",
    "worst_region": "eu-central-1",
    "regions_below_threshold": ["eu-north-1", "eu-west-2", "eu-west-3", "eu-central-2"]
  },
  
  // Data Quality
  "data_quality": {
    "regions_with_data": 6,
    "realtime_sources": 1,
    "estimated_sources": 5,
    "data_freshness_minutes": 5
  },
  
  "created_at": "2025-12-14T10:00:00Z",
  "ttl": 1707551000  // 60 days retention
}
```

### 5. Carbon Savings Leaderboard Table
**Table Name**: `carbon_leaderboard`
**Partition Key**: `period` (String: daily/weekly/monthly)
**Sort Key**: `identifier` (String: pipeline_name or team_name)

```json
{
  "period": "monthly",
  "identifier": "GDSDemoAppPipeline-Pipeline-mfCJVEV8nKQS",
  "period_start": "2025-12-01",
  "period_end": "2025-12-31",
  
  // Carbon Achievements
  "carbon_metrics": {
    "total_emissions_g": 450.5,
    "total_savings_g": 125.3,
    "savings_rate": 0.218,
    "executions_optimized": 45,
    "total_executions": 67,
    "optimization_rate": 0.672
  },
  
  // Rankings
  "rankings": {
    "carbon_savings_rank": 3,
    "optimization_rate_rank": 1,
    "total_executions_rank": 5
  },
  
  // Achievements
  "achievements": [
    "carbon_saver_bronze",
    "optimization_champion",
    "consistency_award"
  ],
  
  "updated_at": "2025-12-14T10:30:00Z",
  "ttl": 1739551000  // 2 years retention
}
```

## Global Secondary Indexes (GSI)

### 1. Pipeline Name Index
- **Partition Key**: `pipeline_name`
- **Sort Key**: `timestamp`
- **Purpose**: Query all executions for a specific pipeline

### 2. Status Index
- **Partition Key**: `status`
- **Sort Key**: `timestamp`
- **Purpose**: Query failed/successful executions across all pipelines

### 3. Carbon Savings Index
- **Partition Key**: `carbon_analysis.decision`
- **Sort Key**: `carbon_analysis.savings_g`
- **Purpose**: Find highest carbon savings opportunities

### 4. Region Performance Index
- **Partition Key**: `carbon_analysis.optimal_region`
- **Sort Key**: `timestamp`
- **Purpose**: Track which regions are most frequently optimal

## Analytics Queries

### 1. Pipeline Performance Dashboard
```python
# Get pipeline success rate over time
def get_pipeline_performance(pipeline_name, days=30):
    # Query pipeline_analytics table
    # Aggregate success rates, carbon savings, performance metrics
    pass

# Get carbon savings trends
def get_carbon_trends(pipeline_name, days=30):
    # Query pipeline_executions with pipeline_name GSI
    # Calculate daily/weekly carbon savings trends
    pass
```

### 2. Regional Optimization Insights
```python
# Find best times to run in each region
def get_optimal_times_by_region(region, days=7):
    # Query carbon_intensity_history
    # Identify patterns in carbon intensity by hour/day
    pass

# Get regional performance comparison
def compare_regional_performance(days=30):
    # Query regional_insights table
    # Compare average intensities, optimization opportunities
    pass
```

### 3. Carbon Intelligence Reports
```python
# Generate monthly carbon report
def generate_carbon_report(month, year):
    # Aggregate data from multiple tables
    # Calculate total emissions, savings, trends
    # Generate insights and recommendations
    pass

# Get real-time optimization recommendations
def get_optimization_recommendations():
    # Query current carbon intensities
    # Compare with historical patterns
    # Suggest optimal regions and timing
    pass
```

## Data Retention Strategy

| Table | Retention Period | Reason |
|-------|------------------|--------|
| `pipeline_executions` | 1 year | Detailed execution history for analysis |
| `carbon_intensity_history` | 30 days | High-frequency data, patterns emerge quickly |
| `pipeline_analytics` | 1 year | Daily aggregations for trend analysis |
| `regional_insights` | 60 days | Hourly patterns for optimization |
| `carbon_leaderboard` | 2 years | Long-term achievements and comparisons |

## Cost Optimization

### Read/Write Patterns
- **High Write**: `carbon_intensity_history` (every 30 minutes × 8 regions)
- **High Read**: `pipeline_executions` (dashboard queries)
- **Batch Write**: `pipeline_analytics` (daily aggregation job)
- **Occasional Read**: `carbon_leaderboard` (monthly reports)

### DynamoDB Configuration
- Use **PAY_PER_REQUEST** for variable workloads
- Enable **TTL** on all tables for automatic cleanup
- Use **Point-in-time recovery** for critical tables
- Consider **DynamoDB Streams** for real-time analytics