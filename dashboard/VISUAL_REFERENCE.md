# Dashboard Visual Reference

## Global Regions Section Layout

### Grid Structure
```
┌─────────────────────────────────────────────────────────────────────────┐
│  AWS WORLDWIDE REGIONS                                                  │
│  All 28 AWS regions · Data center carbon intensity with renewable      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  │ eu-north-1   │  │ ca-central-1 │  │ us-west-2    │  │ eu-west-3    │
│  │ Stockholm,   │  │ Montreal,    │  │ Oregon, USA  │  │ Paris, France│
│  │ Sweden       │  │ Canada       │  │              │  │              │
│  │              │  │              │  │              │  │              │
│  │          0.7 │  │          2.3 │  │         15.9 │  │         17.0 │
│  │              │  │              │  │              │  │              │
│  │ ⚡ 98% renew │  │ ⚡ 90% renew │  │ ⚡ 95% renew │  │ ⚡ 75% renew │
│  │   gCO₂/kWh   │  │   gCO₂/kWh   │  │   gCO₂/kWh   │  │   gCO₂/kWh   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  │ eu-central-2 │  │ eu-west-2    │  │ us-west-1    │  │ sa-east-1    │
│  │ Zurich,      │  │ London, UK   │  │ California,  │  │ São Paulo,   │
│  │ Switzerland  │  │              │  │ USA          │  │ Brazil       │
│  │              │  │              │  │              │  │              │
│  │         17.0 │  │         20.9 │  │         25.4 │  │         42.6 │
│  │              │  │              │  │              │  │              │
│  │ ⚡ 85% renew │  │ ⚡ 80% renew │  │ ⚡ 92% renew │  │ ⚡ 75% renew │
│  │   gCO₂/kWh   │  │   gCO₂/kWh   │  │   gCO₂/kWh   │  │   gCO₂/kWh   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
│                                                                         │
│  ... (continues for all 28 regions)                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Individual Tile Anatomy

```
┌────────────────────────────────────┐
│ eu-north-1              0.7        │  ← Region code (left) + Intensity (right)
│ Stockholm, Sweden                  │  ← Location
│                                    │
│ ─────────────────────────────────  │  ← Separator line
│                                    │
│ ⚡ 98% renewable      gCO₂/kWh     │  ← Renewable % (left) + Unit (right)
└────────────────────────────────────┘
```

### Tile Dimensions:
- **Width**: 280px minimum (auto-fills available space)
- **Height**: ~140px
- **Padding**: 20px
- **Gap**: 1px (grey separator)

## Color Coding

### Intensity Values:
- **0.7** (Very Low) → Bright Green `#22c55e`
- **15.9** (Low) → Green `#16a34a`
- **95.3** (Moderate) → Grey `#404040`
- **227.0** (High) → Orange `#f97316`
- **510.8** (Very High) → Red `#ef4444`

### Visual Examples:

```
Very Low (≤50):
┌────────────────┐
│ eu-north-1     │
│ Stockholm      │
│            0.7 │ ← Bright green
│ ⚡ 98% renew   │
└────────────────┘

Low (≤150):
┌────────────────┐
│ us-west-2      │
│ Oregon, USA    │
│           15.9 │ ← Green
│ ⚡ 95% renew   │
└────────────────┘

Moderate (≤250):
┌────────────────┐
│ eu-south-1     │
│ Milan, Italy   │
│           95.3 │ ← Grey
│ ⚡ 70% renew   │
└────────────────┘

High (≤400):
┌────────────────┐
│ ap-northeast-2 │
│ Seoul, Korea   │
│          227.0 │ ← Orange
│ ⚡ 60% renew   │
└────────────────┘

Very High (>400):
┌────────────────┐
│ af-south-1     │
│ Cape Town, SA  │
│          510.8 │ ← Red
│ ⚡ 50% renew   │
└────────────────┘
```

## Responsive Behavior

### Desktop (>1024px):
```
┌─────┬─────┬─────┬─────┬─────┐
│  1  │  2  │  3  │  4  │  5  │  ← 5 columns
├─────┼─────┼─────┼─────┼─────┤
│  6  │  7  │  8  │  9  │ 10  │
└─────┴─────┴─────┴─────┴─────┘
```

### Tablet (640-1024px):
```
┌─────┬─────┬─────┐
│  1  │  2  │  3  │  ← 3 columns
├─────┼─────┼─────┤
│  4  │  5  │  6  │
└─────┴─────┴─────┘
```

### Mobile (<640px):
```
┌─────┐
│  1  │  ← 1 column
├─────┤
│  2  │
├─────┤
│  3  │
└─────┘
```

## Modal View (Click on Tile)

```
┌──────────────────────────────────────────────────┐
│  eu-north-1                                    × │
│  Stockholm, Sweden                               │
├──────────────────────────────────────────────────┤
│                                                  │
│  CURRENT CARBON INTENSITY                        │
│  ┌──────────────┬──────────────┐                │
│  │ Intensity    │ Index        │                │
│  │ 0.7          │ Very Low     │                │
│  └──────────────┴──────────────┘                │
│                                                  │
│  ✓ OPTIMAL REGION                                │
│  Best carbon intensity worldwide                 │
│                                                  │
│  OPTIMIZATION RECOMMENDATIONS                    │
│  ┌──────────────┬──────────────┐                │
│  │ Optimal      │ Savings      │                │
│  │ eu-north-1   │ Current      │                │
│  └──────────────┴──────────────┘                │
│                                                  │
│  REGION INFORMATION                              │
│  AWS Region:    eu-north-1                       │
│  Country:       SE                               │
│  Coordinates:   59.33°N, 18.06°E                 │
│  Data Source:   AWS Global Carbon Optimizer      │
│                                                  │
│  AWS RENEWABLE ENERGY & DATA CENTER EFFICIENCY   │
│  Grid Intensity:        30 gCO₂/kWh             │
│  AWS Renewable Energy:  98%                      │
│  Data Center Intensity: 0.7 gCO₂/kWh            │
│                                                  │
│  AWS data centers use renewable energy and       │
│  efficient infrastructure (PUE 1.135) to         │
│  significantly reduce carbon emissions.          │
│                                                  │
└──────────────────────────────────────────────────┘
```

## Navigation Bar

```
┌────────────────────────────────────────────────────────────┐
│  GreenQA                                                   │
│                                                            │
│  Dashboard  Europe  Worldwide  Forecast  Calculator  History
│             ──────  ─────────                              │
│                     ^ Active                               │
└────────────────────────────────────────────────────────────┘
```

## Typography

### Fonts:
- **Sans-serif**: Inter (body text, labels)
- **Monospace**: JetBrains Mono (region codes, numbers)

### Sizes:
- **Region code**: 15px, weight 600
- **Location**: 12px, weight 400
- **Intensity**: 32px, weight 300
- **Renewable %**: 12px, weight 400
- **Unit**: 11px, weight 400

## Spacing

```
Tile padding:     20px
Grid gap:         1px
Section margin:   48px
Header padding:   24px
Footer padding:   20px
```

## Accessibility

- ✅ High contrast ratios (WCAG AA compliant)
- ✅ Keyboard navigation support
- ✅ Screen reader friendly
- ✅ Touch-friendly tap targets (min 44x44px)
- ✅ Semantic HTML structure
- ✅ ARIA labels where needed

## Performance

- **Initial load**: <100ms
- **Render 28 tiles**: <50ms
- **Smooth scrolling**: 60fps
- **Modal open**: <16ms
- **Responsive resize**: Debounced 250ms

## Browser Support

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## Print Styles

When printing, the dashboard:
- Removes navigation
- Expands all sections
- Uses black text on white background
- Maintains grid layout
- Shows all 28 regions on separate pages if needed
