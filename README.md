# ZeroCarb Green QA Platform

**Real-Time Carbon Intelligence for AWS**

A carbon-aware platform that provides real-time carbon intensity monitoring across AWS regions, helping development teams make informed decisions about where and when to run their workloads for minimal environmental impact.

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              ZeroCarb Platform Architecture                      │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   AWS Lambda    │    │   Dashboard     │
│                 │    │   Functions     │    │   Frontend      │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ UK Grid ESO     │───▶│ Carbon          │◀──▶│ Real-time       │
│ ElectricityMaps │    │ Ingestion       │    │ Monitoring      │
│ Ember Climate   │    │                 │    │                 │
└─────────────────┘    │ Schedule        │    │ Region          │
                       │ Optimizer       │    │ Comparison      │
┌─────────────────┐    │                 │    │                 │
│   Storage       │    │ API Gateway     │    │ Carbon          │
│                 │    │ Handler         │    │ Calculator      │
├─────────────────┤    └─────────────────┘    │                 │
│ DynamoDB        │           │               │ Interactive     │
│ - Regions       │◀──────────┘               │ Map             │
│ - History       │                           └─────────────────┘
└─────────────────┘    ┌─────────────────┐           │
                       │   CI/CD         │           │
┌─────────────────┐    │   Integration   │           │
│   Monitoring    │    ├─────────────────┤           │
├─────────────────┤    │ test_real_      │◀──────────┘
│ AWS CloudWatch  │    │ pipeline.py     │
│ EventBridge     │    └─────────────────┘
└─────────────────┘
```

## 🔄 Data Flow

```
1. Data Ingestion (Every 30 minutes)
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │ UK Grid ESO │───▶│   Lambda    │───▶│  DynamoDB   │
   │ (Free)      │    │  Ingestion  │    │   Storage   │
   └─────────────┘    └─────────────┘    └─────────────┘
   ┌─────────────┐           │                   │
   │ElectricityM.│───────────┘                   │
   │ (Global)    │                               │
   └─────────────┘                               │

2. API Access
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │ Developer   │───▶│ API Gateway │───▶│   Lambda    │
   │ Request     │    │             │    │  Handler    │
   └─────────────┘    └─────────────┘    └─────────────┘
                             │                   │
                             ▼                   ▼
   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
   │ Dashboard   │◀───│ JSON        │◀───│ DynamoDB    │
   │ Display     │    │ Response    │    │ Query       │
   └─────────────┘    └─────────────┘    └─────────────┘
```

## 🧩 Component Architecture

### Backend Services (AWS Lambda)

```
lambda/
├── carbon_ingestion/           # Carbon data collection
│   └── handler.py             # UK Grid ESO + ElectricityMaps integration
├── schedule_optimizer/         # Basic scheduling recommendations
│   └── handler.py             # Region comparison and optimization
└── api/                       # REST API endpoints
    └── handler.py             # Core API (/regions, /optimal, /calculate)
```

### Frontend Dashboard

```
dashboard/public/
├── index.html                 # Main dashboard (regions, calculator)
├── map.html                   # Interactive global map
├── app.js                     # Dashboard logic
└── styles.css                 # Minimal design system
```

### Data Storage (DynamoDB)

```
Tables:
├── carbon_intensity           # Real-time carbon intensity by region
└── test_executions           # Test execution history
```

## 📋 System Overview

ZeroCarb provides real-time carbon intelligence for AWS regions, helping development teams make informed decisions about where to run their workloads for minimal environmental impact.

### Core Capabilities

- **Real-Time Carbon Data**: Live carbon intensity monitoring across 8 AWS EU regions
- **Multi-Source Integration**: UK Grid ESO (free) + ElectricityMaps (global coverage)
- **Region Comparison**: Find the cleanest AWS regions for workload placement
- **Carbon Calculator**: GSF SCI formula implementation with Cloud Carbon Footprint methodology
- **Interactive Dashboard**: Clean, minimal interface for monitoring and analysis

### Key Features

| Feature | Description |
|---------|-------------|
| **Live Carbon Data** | Real-time carbon intensity across AWS EU regions |
| **Region Optimization** | Compare regions to find cleanest options |
| **Carbon Calculator** | Calculate workload carbon footprint using industry standards |
| **REST API** | Integrate with CI/CD pipelines and automation |
| **Interactive Map** | Global view of carbon intensity with D3.js visualization |

### Data Sources

- **UK Grid ESO**: Free, real-time UK carbon intensity data
- **ElectricityMaps**: Global carbon intensity with AWS datacenter adjustments
- **Ember Climate**: Static fallback data for reliability
- **Cloud Carbon Footprint**: PUE values and energy coefficients

## 🌱 Features

### Real-Time Carbon Intelligence
- **Multi-source carbon data**: UK Grid ESO (free), ElectricityMaps (global)
- **AWS region monitoring**: 8 EU regions with live carbon intensity
- **Region comparison**: Find cleanest regions for workload placement
- **Carbon calculator**: GSF SCI formula with Cloud Carbon Footprint methodology
- **Interactive dashboard**: Real-time monitoring with clean, minimal design

### Core API & Infrastructure
- **REST API**: `/regions`, `/optimal`, `/calculate`, `/current` endpoints
- **AWS Lambda**: Serverless carbon ingestion (30-minute intervals)
- **DynamoDB**: Real-time carbon intensity storage with TTL
- **CloudFormation**: Complete infrastructure as code

## 📁 Project Structure

```
green-qa-platform/
├── lambda/                              # AWS Lambda Functions
│   ├── carbon_ingestion/               # Carbon data collection
│   │   ├── handler.py                  # Main ingestion handler (UK Grid + ElectricityMaps)
│   │   └── aws_datacenter_carbon.py    # AWS-specific carbon calculations
│   ├── api/                            # REST API endpoints
│   │   └── handler.py                  # Core API (/regions, /optimal, /calculate)
│   └── schedule_optimizer/             # Basic scheduling
│       └── handler.py                  # Recommendation engine
├── dashboard/                          # Frontend Dashboard
│   └── public/
│       ├── index.html                  # Main dashboard
│       ├── app.js                      # Core dashboard logic
│       ├── styles.css                  # Minimal design system
│       ├── map.html                    # Interactive global map
│       └── global-regions-data.js      # Embedded region data
├── infrastructure/                     # AWS Infrastructure
│   └── cloudformation.yaml            # Lambda + DynamoDB + API Gateway
├── config/                             # Configuration
│   ├── .env                           # Environment variables
│   └── pipeline_config.py             # Pipeline configuration
├── test_real_pipeline.py              # Real AWS pipeline integration
└── README.md                          # This file
```

## 🔧 Carbon Data Sources

| Source | Coverage | Auth | Priority |
|--------|----------|------|----------|
| **UK Carbon Intensity** | UK only | None | 1st (UK) |
| **ElectricityMaps** | Global | Token | 1st (Other) |
| **Ember Climate** | Global | None | Fallback |

## 🧮 Carbon Calculation

### GSF SCI Formula
```
SCI = ((E × I) + M) / R

E = Energy (kWh) = vCPU × TDP × hours / 1000
I = Carbon Intensity (gCO2/kWh)
M = Embodied Emissions (gCO2)
R = Functional Unit
```

### Cloud Carbon Footprint Values
| Provider | PUE | TDP/vCPU |
|----------|-----|----------|
| AWS | 1.135 | 10W |

## 🚀 Quick Start

### 1. Deploy Infrastructure

```bash
# Navigate to infrastructure directory
cd infrastructure

# Deploy to AWS
aws cloudformation create-stack \
  --stack-name green-qa-platform-prod \
  --template-body file://cloudformation.yaml \
  --parameters ParameterKey=Environment,ParameterValue=prod \
  --capabilities CAPABILITY_IAM \
  --region eu-west-2

# Get API endpoint
aws cloudformation describe-stacks \
  --stack-name green-qa-platform-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text
```

### 2. Configure Dashboard

```bash
# Navigate to dashboard
cd dashboard

# Update API configuration in app.js
# Replace API_CONFIG.baseUrl with your actual API endpoint

# Deploy to S3 (optional)
aws s3 sync public/ s3://your-dashboard-bucket/ \
  --exclude "*.md" \
  --cache-control "max-age=3600"
```

### 3. Test Integration

```bash
# Set API endpoint
export ZEROCARB_API="https://your-api.execute-api.eu-west-2.amazonaws.com/Prod"

# Test real pipeline integration
python test_real_pipeline.py
```

## 📊 API Usage

### Get Current Carbon Intensity
```bash
curl "https://<api>/regions"
```

**Response:**
```json
{
  "regions": [
    {
      "name": "eu-west-2",
      "intensity": 245.5,
      "location": "London, UK",
      "timestamp": "2025-12-14T10:30:00Z"
    }
  ]
}
```

### Get Optimal Regions
```bash
curl "https://<api>/optimal?limit=3"
```

**Response:**
```json
{
  "optimal_regions": [
    {"region": "eu-north-1", "intensity": 30},
    {"region": "eu-west-3", "intensity": 60},
    {"region": "eu-west-2", "intensity": 150}
  ]
}
```

### Calculate Carbon Footprint
```bash
curl -X POST "https://<api>/calculate" \
  -d '{"region":"eu-west-2","duration_seconds":3600,"vcpu_count":2,"memory_gb":4}'
```

**Response:**
```json
{
  "energy_kwh": 0.00347,
  "operational_g": 0.851,
  "embodied_g": 0.005,
  "total_g": 0.856,
  "sci": 0.856
}
```

## ⚙️ Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DYNAMODB_TABLE` | Table name | Yes |
| `ELECTRICITY_MAPS_TOKEN` | ElectricityMaps token | For global data |

## 📈 Carbon Thresholds

| Index | Intensity (gCO2/kWh) |
|-------|---------------------|
| Very Low | ≤ 50 |
| Low | ≤ 150 |
| Moderate | ≤ 250 |
| High | ≤ 400 |
| Very High | > 400 |

## 🚀 Deployment Status

| Component | Status | Description |
|-----------|--------|-------------|
| **Core Platform** | ✅ **Production Ready** | Real-time carbon monitoring, basic API, main dashboard |
| **Infrastructure** | ✅ **Deployed** | CloudFormation, Lambda, DynamoDB, API Gateway |
| **Carbon Data** | ✅ **Live** | UK Grid ESO + ElectricityMaps integration |
| **Dashboard** | ✅ **Working** | Main dashboard, calculator, region comparison |
| **Documentation** | ✅ **Complete** | Comprehensive README + architecture docs |

### What's Working Right Now

```bash
# Get real-time carbon intensity
curl https://your-api/regions

# Get optimal regions
curl https://your-api/optimal?limit=3

# Calculate carbon footprint
curl -X POST https://your-api/calculate \
  -d '{"region":"eu-west-2","duration_seconds":3600,"vcpu_count":2}'

# View dashboard
open https://your-dashboard-url/index.html
```

## 🧪 Testing

### Run Real Pipeline Integration

```bash
# Set configuration in config/.env
CODEPIPELINE_ENABLED=true
CODEPIPELINE_NAME=your-pipeline-name
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret

# Run test
python test_real_pipeline.py
```

## 💰 Cost Estimation

Monthly costs (estimated for 1M requests):

- **Lambda**: $5-10
- **DynamoDB**: $10-20 (PAY_PER_REQUEST)
- **API Gateway**: $3-5
- **Total**: ~$20-35/month

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

---

**ZeroCarb** - Real-Time Carbon Intelligence for AWS 🌱

*Making software carbon-aware, one region at a time.*