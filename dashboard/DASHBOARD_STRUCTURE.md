# Dashboard Structure

The dashboard is split into two pages for better organization and performance.

## Pages

### 1. index.html - Core Features (V1)
**Essential carbon-aware monitoring and calculation**

Features:
- Dashboard Overview (stats, charts)
- Europe Regions (15 AWS regions)
- Worldwide Regions (34 AWS regions)
- Carbon Calculator
- Test History

Navigation: Main landing page

### 2. advanced.html - Advanced Features (V2)
**Research-based optimization algorithms**

Features:
- Carbon Intensity Forecast (CarbonX-inspired)
- Excess Power Analysis (renewable curtailment)
- MAIZX Multi-Region Ranking (85% CO₂ reduction)
- Slack-Aware Scheduling (57% CO₂ reduction)

Navigation: Click "Advanced" in main navigation

### 3. map.html - Interactive Map
**Visual exploration of global carbon intensity**

Features:
- Interactive world map with D3.js
- Real-time region markers
- Detailed region popups

Navigation: Separate page, linked from footer

---

## File Organization

```
green-qa-platform/dashboard/public/
├── index.html              # V1: Core features
├── advanced.html           # V2: Advanced features
├── map.html                # Interactive map
├── styles.css              # Shared design system
├── app.js                  # Core functionality
│
├── excess-power.js/css     # Advanced: Excess power widget
├── forecast.js/css         # Advanced: Forecast widget
├── maizx-ranking.js/css    # Advanced: MAIZX widget
├── slack-scheduling.js/css # Advanced: Slack widget
│
└── global-regions-data.js  # Shared data
```

---

## Benefits of Split Structure

### Performance
- Faster initial page load (index.html)
- Advanced features loaded only when needed
- Reduced JavaScript bundle size

### User Experience
- Clear separation of basic vs advanced
- Simpler navigation for new users
- Power users can access advanced features

### Maintainability
- Easier to test individual features
- Clear feature boundaries
- Independent deployment possible

---

## Navigation Flow

```
index.html (V1)
├── Dashboard
├── Europe
├── Worldwide
├── Calculator
├── History
└── Advanced → advanced.html (V2)
                ├── Forecast
                ├── Excess Power
                ├── MAIZX
                └── Slack
```

---

## Feature Flags

Both pages respect the same feature flags:
- `ENABLE_EXCESS_POWER`
- `ENABLE_CARBONX_FORECAST`
- `ENABLE_MAIZX_RANKING`
- `ENABLE_SLACK_SCHEDULING`

Disabled features show appropriate messages.

---

## API Endpoints

### V1 (Core)
- `GET /current` - Current carbon intensity
- `GET /regions` - All regions data
- `POST /calculate` - Carbon calculation

### V2 (Advanced)
- `POST /v2/forecast` - Carbon forecast
- `POST /v2/excess-power` - Excess power analysis
- `POST /v2/rank-regions` - MAIZX ranking
- `POST /v2/optimize-schedule` - Slack scheduling

---

## Testing

### V1 Testing
```bash
# Open in browser
open green-qa-platform/dashboard/public/index.html
```

### V2 Testing
```bash
# Open in browser
open green-qa-platform/dashboard/public/advanced.html
```

### Individual Widget Testing
```bash
# Test files in tests/ directory
open green-qa-platform/dashboard/tests/test-forecast.html
open green-qa-platform/dashboard/tests/test-excess-power.html
open green-qa-platform/dashboard/tests/test-maizx.html
open green-qa-platform/dashboard/tests/test-slack.html
```

---

## Deployment

Both pages share the same deployment:
```bash
aws s3 sync green-qa-platform/dashboard/public/ s3://your-bucket/ --exclude "tests/*"
```

---

**Status**: ✅ Two-page structure implemented
**Version**: V1 (Core) + V2 (Advanced)
**Last Updated**: December 8, 2025
