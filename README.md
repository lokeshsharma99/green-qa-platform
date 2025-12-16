# ZeroCarb

Carbon-aware CI/CD scheduling platform for AWS. Monitors real-time carbon intensity across AWS regions and helps teams run pipelines in cleaner regions.

## Live Dashboard

**URL**: https://d2jofykrotzoef.cloudfront.net

## What It Does

1. **Fetches real-time carbon intensity** from UK Grid ESO and ElectricityMaps API
2. **Compares AWS regions** to find the cleanest option
3. **Calculates carbon footprint** using GSF SCI formula + Cloud Carbon Footprint methodology
4. **Triggers CodePipeline** in optimal regions (or recommends deferral)
5. **Tracks pipeline history** with carbon metrics

## Project Structure

```
├── dashboard/public/          # Frontend (S3 + CloudFront)
│   ├── index.html            # Main dashboard
│   ├── app.js                # Core logic (4500+ lines)
│   └── *.css/js              # Features (dark mode, tooltips, etc.)
├── lambda/                    # AWS Lambda functions
│   ├── api/handler.py        # REST API endpoints
│   ├── carbon_ingestion/     # Data collection
│   └── pipeline_monitor/     # Pipeline tracking
├── infrastructure/
│   └── cloudformation.yaml   # DynamoDB, Lambda, API Gateway, EventBridge
├── test_real_pipeline.py     # CLI tool to trigger pipelines
└── deploy_cloudfront.py      # Dashboard deployment script
```

## Data Sources

| Source | Coverage | Auth | Used For |
|--------|----------|------|----------|
| UK Grid ESO | UK | None | eu-west-2 (London) |
| ElectricityMaps | Global | Token | All other regions |
| Ember Climate | Global | None | Fallback |

## Carbon Calculation

Uses GSF SCI formula with Cloud Carbon Footprint constants:

```
SCI = (E × I) + M

E = Energy (kWh) = (vCPU × 10W × hours + Memory × 0.000392 × hours) × PUE
I = Carbon Intensity (gCO2/kWh) = Grid × (1 - AWS_Renewable%) × 1.15
M = Embodied Carbon = vCPU × hours × 2.5g
```

**Constants** (Source: [AWS 2024 Sustainability Report](https://sustainability.aboutamazon.com/2024-amazon-sustainability-report-aws-summary.pdf)):
- AWS PUE: 1.15 (industry avg: 1.25, on-premises: 1.63)
- AWS WUE: 0.15 L/kWh (17% improvement from 2023)
- vCPU TDP: 10W (Graviton: up to 60% less energy)
- Memory coefficient: 0.000392 kWh/GB-hour
- Embodied carbon: 2.5g CO2/vCPU-hour
- AWS vs On-Premises: 4.1x more efficient, up to 99% carbon reduction

## AWS Infrastructure

**DynamoDB Tables**:
- `green_qa_carbon_intensity_{env}` - Real-time carbon data
- `pipeline_executions_{env}` - Pipeline run history
- `carbon_intensity_history_{env}` - Historical trends
- `pipeline_analytics_{env}` - Aggregated metrics

**Lambda Functions**:
- `green-qa-carbon-ingestion` - Fetches carbon data every 30 min
- `green-qa-schedule-optimizer` - API handler
- `green-qa-pipeline-monitor` - Tracks pipeline completions

**EventBridge Rules**:
- Carbon refresh: every 30 minutes
- Pipeline state changes: SUCCEEDED/FAILED/STOPPED

## API Endpoints

```bash
# Get all regions with carbon intensity
GET /regions

# Get optimal regions (lowest carbon)
GET /optimal?limit=3

# Get current intensity for a region
GET /current?region=eu-west-2

# Calculate carbon footprint
POST /calculate
{"region": "eu-west-2", "duration_seconds": 3600, "vcpu_count": 2, "memory_gb": 4}

# Store pipeline result
POST /store_result
{"test_id": "...", "region": "eu-west-2", "carbon_g": 0.85, ...}

# Get pipeline history
GET /history?limit=50
```

## Carbon Scheduler v2.0 (MAIZX Algorithm)

Research-backed scheduling engine with 85% emission reduction potential.

**Algorithms implemented**:
- **MAIZX Ranking** (KTH/NTNU) - Multi-factor weighted scoring
- **α-Fair Allocation** (Inria) - Prevents statistical bias in region selection
- **Dynamic Slack** (Green FL) - 20-60% extra savings by extending wait windows
- **CarbonFlex Scaling** (UMass) - Elastic resource scaling based on carbon intensity
- **HYBRID Strategy** - Combined time + space shifting

**Strategies**:
| Strategy | Description |
|----------|-------------|
| `RUN_NOW` | Execute immediately in current region |
| `TIME_SHIFT` | Wait for better time in same region |
| `SPACE_SHIFT` | Run now in cleaner region |
| `HYBRID` | Wait + switch region (maximum savings) |

**Usage**:
```bash
# Test scheduler with different criticality levels
python carbon_scheduler.py normal my-pipeline
python carbon_scheduler.py critical my-pipeline
python carbon_scheduler.py low my-pipeline
```

**MAIZX Formula**:
```
MAIZ_RANKING = w1×CFP + w2×FCFP + w3×CP_RATIO + w4×SCHEDULE_WEIGHT

CFP = Current Carbon Footprint (normalized)
FCFP = Forecasted Carbon Footprint
CP_RATIO = Computing Power Ratio (region efficiency)
SCHEDULE_WEIGHT = Deadline/priority factor
```

## CLI Usage

```bash
# Configure
cp config/.env.example config/.env
# Edit .env with your pipeline name and AWS credentials

# Run (simulation mode)
python test_real_pipeline.py

# Run with actual pipeline trigger
# Set CODEPIPELINE_ENABLED=true and AUTO_TRIGGER_RUN_NOW=true in .env
python test_real_pipeline.py

# Custom workload parameters
python test_real_pipeline.py 15 4 7  # 15 min, 4 vCPU, 7GB RAM
```

## Dashboard Features

- **Region comparison**: Side-by-side carbon intensity across 8 EU regions
- **Optimal time**: 48-hour forecast with best deployment window
- **Interactive map**: D3.js world map with all AWS regions
- **Pipeline history**: Paginated table with carbon metrics
- **Carbon calculator**: Manual SCI calculation
- **Dark mode**: Toggle in header
- **Educational tooltips**: Hover explanations for all metrics

## Deployment

**Dashboard** (S3 + CloudFront):
```bash
python deploy_cloudfront.py
```

**Infrastructure** (CloudFormation):
```bash
aws cloudformation create-stack \
  --stack-name green-qa-platform-prod \
  --template-body file://infrastructure/cloudformation.yaml \
  --parameters ParameterKey=Environment,ParameterValue=prod \
  --capabilities CAPABILITY_IAM \
  --region eu-west-2
```

## AWS Resources

| Resource | Name |
|----------|------|
| S3 Bucket | `zerocarb-dashboard` |
| CloudFront | `E2GRL6DDHNZU7I` |
| CodeCommit | `ZeroCarb` (eu-west-2) |

## Environment Variables

```bash
# Required
CODEPIPELINE_NAME=your-pipeline-name
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=...  # If using temporary credentials

# Optional
CODEPIPELINE_ENABLED=true
AUTO_TRIGGER_RUN_NOW=true
AWS_DEFAULT_REGION=eu-west-2
MIN_SAVINGS_DEFER=15
MAX_DEFER_HOURS=24

# Carbon Scheduler v2.0 (MAIZX Algorithm)
ALLOW_HYBRID=true                  # Enable combined time+space strategy
ALLOW_ELASTIC_SCALING=true         # Scale resources based on carbon
ALPHA_FAIRNESS=0.5                 # 0=fair, 1=greedy region selection
DYNAMIC_SLACK=true                 # Extend wait window for high savings
FORECAST_CONFIDENCE_THRESHOLD=0.7  # Min forecast confidence

# MAIZX Weights (sum to 1.0)
MAIZX_W_CFP=0.30                   # Current carbon footprint
MAIZX_W_FCFP=0.30                  # Forecasted carbon footprint
MAIZX_W_CP_RATIO=0.20              # Region efficiency
MAIZX_W_SCHEDULE=0.20              # Deadline priority
```

## Research Papers

The carbon scheduler implements algorithms from these papers (in `researchPaper/`):

| Paper | Algorithm | Impact |
|-------|-----------|--------|
| MAIZX Framework | Weighted ranking | 85% emission reduction |
| Green Federated Learning | α-fair allocation, slack optimization | 20-60% extra savings |
| CarbonFlex | Elastic scaling, historical learning | 57% reduction |
| CarbonX | Forecast uncertainty | Better reliability |
| CarbonScaler | Resource scaling | 51% reduction |