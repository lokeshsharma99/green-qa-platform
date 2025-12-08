"""
AWS Global Carbon Optimizer
Shows best regions and times to run workloads worldwide
"""

import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import requests

# Add parent directory to path for imports
sys.path.insert(0, '.')

try:
    from aws_datacenter_carbon import (
        calculate_aws_datacenter_carbon_intensity,
        AWS_RENEWABLE_ENERGY_PCT
    )
except ImportError:
    # Fallback if running standalone
    AWS_RENEWABLE_ENERGY_PCT = {}
    def calculate_aws_datacenter_carbon_intensity(region, intensity):
        return {'datacenter_intensity_gco2_kwh': intensity * 1.135}


# Complete AWS Region Information
AWS_REGIONS = {
    # US East
    'us-east-1': {
        'name': 'US East (N. Virginia)',
        'location': 'Virginia, USA',
        'country': 'US',
        'grid_zone': 'US-SERC-SRVC',
        'timezone': 'America/New_York',
        'lat': 38.13,
        'lon': -78.45,
        'renewable_pct': 0.90,
        'typical_grid_intensity': 420
    },
    'us-east-2': {
        'name': 'US East (Ohio)',
        'location': 'Ohio, USA',
        'country': 'US',
        'grid_zone': 'US-RFC-RFCW',
        'timezone': 'America/New_York',
        'lat': 40.42,
        'lon': -82.91,
        'renewable_pct': 0.85,
        'typical_grid_intensity': 550
    },
    
    # US West
    'us-west-1': {
        'name': 'US West (N. California)',
        'location': 'California, USA',
        'country': 'US',
        'grid_zone': 'US-CAL-CISO',
        'timezone': 'America/Los_Angeles',
        'lat': 37.35,
        'lon': -121.96,
        'renewable_pct': 0.92,
        'typical_grid_intensity': 280
    },
    'us-west-2': {
        'name': 'US West (Oregon)',
        'location': 'Oregon, USA',
        'country': 'US',
        'grid_zone': 'US-NW-PACW',
        'timezone': 'America/Los_Angeles',
        'lat': 45.87,
        'lon': -119.69,
        'renewable_pct': 0.95,
        'typical_grid_intensity': 280
    },
    
    # Europe
    'eu-west-1': {
        'name': 'Europe (Ireland)',
        'location': 'Dublin, Ireland',
        'country': 'IE',
        'grid_zone': 'IE',
        'timezone': 'Europe/Dublin',
        'lat': 53.35,
        'lon': -6.26,
        'renewable_pct': 0.85,
        'typical_grid_intensity': 300
    },
    'eu-west-2': {
        'name': 'Europe (London)',
        'location': 'London, UK',
        'country': 'GB',
        'grid_zone': 'GB',
        'timezone': 'Europe/London',
        'lat': 51.51,
        'lon': -0.13,
        'renewable_pct': 0.80,
        'typical_grid_intensity': 250
    },
    'eu-west-3': {
        'name': 'Europe (Paris)',
        'location': 'Paris, France',
        'country': 'FR',
        'grid_zone': 'FR',
        'timezone': 'Europe/Paris',
        'lat': 48.86,
        'lon': 2.35,
        'renewable_pct': 0.75,
        'typical_grid_intensity': 60
    },
    'eu-central-1': {
        'name': 'Europe (Frankfurt)',
        'location': 'Frankfurt, Germany',
        'country': 'DE',
        'grid_zone': 'DE',
        'timezone': 'Europe/Berlin',
        'lat': 50.11,
        'lon': 8.68,
        'renewable_pct': 0.75,
        'typical_grid_intensity': 380
    },
    'eu-central-2': {
        'name': 'Europe (Zurich)',
        'location': 'Zurich, Switzerland',
        'country': 'CH',
        'grid_zone': 'CH',
        'timezone': 'Europe/Zurich',
        'lat': 47.37,
        'lon': 8.54,
        'renewable_pct': 0.85,
        'typical_grid_intensity': 50
    },
    'eu-north-1': {
        'name': 'Europe (Stockholm)',
        'location': 'Stockholm, Sweden',
        'country': 'SE',
        'grid_zone': 'SE',
        'timezone': 'Europe/Stockholm',
        'lat': 59.33,
        'lon': 18.06,
        'renewable_pct': 0.98,
        'typical_grid_intensity': 30
    },
    'eu-south-1': {
        'name': 'Europe (Milan)',
        'location': 'Milan, Italy',
        'country': 'IT',
        'grid_zone': 'IT-NO',
        'timezone': 'Europe/Rome',
        'lat': 45.46,
        'lon': 9.19,
        'renewable_pct': 0.70,
        'typical_grid_intensity': 280
    },
    'eu-south-2': {
        'name': 'Europe (Spain)',
        'location': 'Aragon, Spain',
        'country': 'ES',
        'grid_zone': 'ES',
        'timezone': 'Europe/Madrid',
        'lat': 41.65,
        'lon': -0.88,
        'renewable_pct': 0.75,
        'typical_grid_intensity': 200
    },
    
    # Asia Pacific
    'ap-south-1': {
        'name': 'Asia Pacific (Mumbai)',
        'location': 'Mumbai, India',
        'country': 'IN',
        'grid_zone': 'IN-WE',
        'timezone': 'Asia/Kolkata',
        'lat': 19.08,
        'lon': 72.88,
        'renewable_pct': 0.55,
        'typical_grid_intensity': 650
    },
    'ap-northeast-1': {
        'name': 'Asia Pacific (Tokyo)',
        'location': 'Tokyo, Japan',
        'country': 'JP',
        'grid_zone': 'JP-TK',
        'timezone': 'Asia/Tokyo',
        'lat': 35.68,
        'lon': 139.69,
        'renewable_pct': 0.65,
        'typical_grid_intensity': 450
    },
    'ap-northeast-2': {
        'name': 'Asia Pacific (Seoul)',
        'location': 'Seoul, South Korea',
        'country': 'KR',
        'grid_zone': 'KR',
        'timezone': 'Asia/Seoul',
        'lat': 37.57,
        'lon': 126.98,
        'renewable_pct': 0.60,
        'typical_grid_intensity': 500
    },
    'ap-northeast-3': {
        'name': 'Asia Pacific (Osaka)',
        'location': 'Osaka, Japan',
        'country': 'JP',
        'grid_zone': 'JP-KN',
        'timezone': 'Asia/Tokyo',
        'lat': 34.69,
        'lon': 135.50,
        'renewable_pct': 0.65,
        'typical_grid_intensity': 450
    },
    'ap-southeast-1': {
        'name': 'Asia Pacific (Singapore)',
        'location': 'Singapore',
        'country': 'SG',
        'grid_zone': 'SG',
        'timezone': 'Asia/Singapore',
        'lat': 1.35,
        'lon': 103.82,
        'renewable_pct': 0.60,
        'typical_grid_intensity': 400
    },
    'ap-southeast-2': {
        'name': 'Asia Pacific (Sydney)',
        'location': 'Sydney, Australia',
        'country': 'AU',
        'grid_zone': 'AU-NSW',
        'timezone': 'Australia/Sydney',
        'lat': -33.87,
        'lon': 151.21,
        'renewable_pct': 0.70,
        'typical_grid_intensity': 550
    },
    'ap-southeast-3': {
        'name': 'Asia Pacific (Jakarta)',
        'location': 'Jakarta, Indonesia',
        'country': 'ID',
        'grid_zone': 'ID',
        'timezone': 'Asia/Jakarta',
        'lat': -6.21,
        'lon': 106.85,
        'renewable_pct': 0.45,
        'typical_grid_intensity': 700
    },
    'ap-southeast-4': {
        'name': 'Asia Pacific (Melbourne)',
        'location': 'Melbourne, Australia',
        'country': 'AU',
        'grid_zone': 'AU-VIC',
        'timezone': 'Australia/Melbourne',
        'lat': -37.81,
        'lon': 144.96,
        'renewable_pct': 0.70,
        'typical_grid_intensity': 550
    },
    'ap-east-1': {
        'name': 'Asia Pacific (Hong Kong)',
        'location': 'Hong Kong',
        'country': 'HK',
        'grid_zone': 'HK',
        'timezone': 'Asia/Hong_Kong',
        'lat': 22.32,
        'lon': 114.17,
        'renewable_pct': 0.50,
        'typical_grid_intensity': 600
    },
    
    # Canada
    'ca-central-1': {
        'name': 'Canada (Central)',
        'location': 'Montreal, Canada',
        'country': 'CA',
        'grid_zone': 'CA-QC',
        'timezone': 'America/Toronto',
        'lat': 45.50,
        'lon': -73.57,
        'renewable_pct': 0.90,
        'typical_grid_intensity': 20
    },
    'ca-west-1': {
        'name': 'Canada (Calgary)',
        'location': 'Calgary, Canada',
        'country': 'CA',
        'grid_zone': 'CA-AB',
        'timezone': 'America/Edmonton',
        'lat': 51.05,
        'lon': -114.07,
        'renewable_pct': 0.85,
        'typical_grid_intensity': 500
    },
    
    # South America
    'sa-east-1': {
        'name': 'South America (São Paulo)',
        'location': 'São Paulo, Brazil',
        'country': 'BR',
        'grid_zone': 'BR',
        'timezone': 'America/Sao_Paulo',
        'lat': -23.55,
        'lon': -46.63,
        'renewable_pct': 0.75,
        'typical_grid_intensity': 150
    },
    
    # Middle East
    'me-south-1': {
        'name': 'Middle East (Bahrain)',
        'location': 'Bahrain',
        'country': 'BH',
        'grid_zone': 'BH',
        'timezone': 'Asia/Bahrain',
        'lat': 26.07,
        'lon': 50.56,
        'renewable_pct': 0.40,
        'typical_grid_intensity': 600
    },
    'me-central-1': {
        'name': 'Middle East (UAE)',
        'location': 'UAE',
        'country': 'AE',
        'grid_zone': 'AE',
        'timezone': 'Asia/Dubai',
        'lat': 25.20,
        'lon': 55.27,
        'renewable_pct': 0.50,
        'typical_grid_intensity': 550
    },
    
    # Africa
    'af-south-1': {
        'name': 'Africa (Cape Town)',
        'location': 'Cape Town, South Africa',
        'country': 'ZA',
        'grid_zone': 'ZA',
        'timezone': 'Africa/Johannesburg',
        'lat': -33.92,
        'lon': 18.42,
        'renewable_pct': 0.50,
        'typical_grid_intensity': 900
    },
    
    # Israel
    'il-central-1': {
        'name': 'Israel (Tel Aviv)',
        'location': 'Tel Aviv, Israel',
        'country': 'IL',
        'grid_zone': 'IL',
        'timezone': 'Asia/Jerusalem',
        'lat': 32.09,
        'lon': 34.78,
        'renewable_pct': 0.55,
        'typical_grid_intensity': 550
    },
}


def get_uk_carbon_intensity():
    """Get real-time UK carbon intensity"""
    try:
        response = requests.get(
            'https://api.carbonintensity.org.uk/intensity',
            timeout=10
        )
        if response.ok:
            data = response.json()
            current = data['data'][0]
            return current['intensity']['actual'] or current['intensity']['forecast']
    except:
        pass
    return None


def calculate_region_carbon_intensity(region_code: str) -> Dict:
    """Calculate carbon intensity for a region"""
    region = AWS_REGIONS.get(region_code, {})
    
    # Try to get real-time data for UK
    if region.get('country') == 'GB':
        real_time = get_uk_carbon_intensity()
        if real_time:
            grid_intensity = real_time
        else:
            grid_intensity = region.get('typical_grid_intensity', 250)
    else:
        grid_intensity = region.get('typical_grid_intensity', 300)
    
    # Calculate AWS data center intensity
    result = calculate_aws_datacenter_carbon_intensity(region_code, grid_intensity)
    
    return {
        'region_code': region_code,
        'region_name': region.get('name', region_code),
        'location': region.get('location', 'Unknown'),
        'country': region.get('country', 'Unknown'),
        'grid_intensity': grid_intensity,
        'aws_renewable_pct': region.get('renewable_pct', 0.70),
        'datacenter_intensity': result.get('datacenter_intensity_gco2_kwh', grid_intensity * 1.135),
        'timezone': region.get('timezone', 'UTC'),
        'lat': region.get('lat', 0),
        'lon': region.get('lon', 0)
    }


def get_all_regions_carbon_intensity() -> List[Dict]:
    """Get carbon intensity for all AWS regions"""
    results = []
    
    for region_code in AWS_REGIONS.keys():
        try:
            result = calculate_region_carbon_intensity(region_code)
            results.append(result)
        except Exception as e:
            print(f"Error calculating {region_code}: {e}")
    
    return results


def get_best_regions(limit: int = 10) -> List[Dict]:
    """Get best regions sorted by carbon intensity"""
    all_regions = get_all_regions_carbon_intensity()
    sorted_regions = sorted(all_regions, key=lambda x: x['datacenter_intensity'])
    return sorted_regions[:limit]


def get_worst_regions(limit: int = 10) -> List[Dict]:
    """Get worst regions sorted by carbon intensity"""
    all_regions = get_all_regions_carbon_intensity()
    sorted_regions = sorted(all_regions, key=lambda x: x['datacenter_intensity'], reverse=True)
    return sorted_regions[:limit]


def get_european_regions() -> List[Dict]:
    """Get all European regions sorted by carbon intensity"""
    all_regions = get_all_regions_carbon_intensity()
    european = [r for r in all_regions if r['region_code'].startswith('eu-')]
    return sorted(european, key=lambda x: x['datacenter_intensity'])


def compare_regions_by_continent() -> Dict:
    """Compare regions grouped by continent"""
    all_regions = get_all_regions_carbon_intensity()
    
    continents = {
        'North America': [],
        'Europe': [],
        'Asia Pacific': [],
        'South America': [],
        'Middle East': [],
        'Africa': []
    }
    
    for region in all_regions:
        code = region['region_code']
        if code.startswith('us-') or code.startswith('ca-'):
            continents['North America'].append(region)
        elif code.startswith('eu-'):
            continents['Europe'].append(region)
        elif code.startswith('ap-'):
            continents['Asia Pacific'].append(region)
        elif code.startswith('sa-'):
            continents['South America'].append(region)
        elif code.startswith('me-'):
            continents['Middle East'].append(region)
        elif code.startswith('af-') or code.startswith('il-'):
            continents['Africa'].append(region)
    
    # Sort each continent by carbon intensity
    for continent in continents:
        continents[continent] = sorted(
            continents[continent],
            key=lambda x: x['datacenter_intensity']
        )
    
    return continents


def print_region_table(regions: List[Dict], title: str):
    """Print formatted table of regions"""
    print(f"\n{'='*100}")
    print(f" {title}")
    print(f"{'='*100}")
    print(f"{'Rank':<6}{'Region':<25}{'Location':<25}{'Grid':<12}{'AWS DC':<12}{'Renewable':<12}{'Savings'}")
    print(f"{'-'*100}")
    
    for i, region in enumerate(regions, 1):
        grid = region['grid_intensity']
        dc = region['datacenter_intensity']
        renewable = region['aws_renewable_pct'] * 100
        savings = ((grid * 1.135 - dc) / (grid * 1.135)) * 100
        
        print(f"{i:<6}{region['region_code']:<25}{region['location']:<25}"
              f"{grid:<12.0f}{dc:<12.1f}{renewable:<12.0f}%{savings:>6.1f}%")


def print_continent_comparison(continents: Dict):
    """Print comparison by continent"""
    print(f"\n{'='*100}")
    print(f" Best Regions by Continent")
    print(f"{'='*100}")
    
    for continent, regions in continents.items():
        if not regions:
            continue
        
        print(f"\n{continent}:")
        print(f"{'  Rank':<8}{'Region':<25}{'Location':<25}{'AWS DC Intensity':<20}")
        print(f"  {'-'*95}")
        
        for i, region in enumerate(regions[:5], 1):  # Top 5 per continent
            print(f"  {i:<6}{region['region_code']:<25}{region['location']:<25}"
                  f"{region['datacenter_intensity']:<20.1f} gCO2/kWh")


def print_european_detailed():
    """Print detailed European comparison"""
    european = get_european_regions()
    
    print(f"\n{'='*100}")
    print(f" European Regions - Detailed Analysis")
    print(f"{'='*100}")
    print(f"{'Region':<20}{'Location':<20}{'Grid':<12}{'Renewable':<12}{'AWS DC':<12}{'Best Time (UTC)'}")
    print(f"{'-'*100}")
    
    for region in european:
        # Best time is typically during day when solar is high (10:00-16:00 UTC)
        best_time = "10:00-16:00"
        
        print(f"{region['region_code']:<20}{region['location']:<20}"
              f"{region['grid_intensity']:<12.0f}{region['aws_renewable_pct']*100:<12.0f}%"
              f"{region['datacenter_intensity']:<12.1f}{best_time}")


def generate_recommendations() -> Dict:
    """Generate recommendations for workload placement"""
    all_regions = get_all_regions_carbon_intensity()
    best = min(all_regions, key=lambda x: x['datacenter_intensity'])
    worst = max(all_regions, key=lambda x: x['datacenter_intensity'])
    
    # Calculate potential savings
    savings_gco2 = worst['datacenter_intensity'] - best['datacenter_intensity']
    savings_pct = (savings_gco2 / worst['datacenter_intensity']) * 100
    
    return {
        'best_region': best,
        'worst_region': worst,
        'potential_savings_gco2_kwh': savings_gco2,
        'potential_savings_percent': savings_pct,
        'recommendation': f"Run workloads in {best['region_code']} instead of {worst['region_code']} "
                         f"to save {savings_gco2:.1f} gCO2/kWh ({savings_pct:.1f}% reduction)"
    }


def main():
    """Main function to display all analysis"""
    print("\n" + "="*100)
    print(" AWS Global Carbon Optimizer - Worldwide Analysis")
    print("="*100)
    print(f" Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("="*100)
    
    # 1. Best regions worldwide
    best_regions = get_best_regions(10)
    print_region_table(best_regions, "🌟 Top 10 Best AWS Regions (Lowest Carbon Intensity)")
    
    # 2. Worst regions worldwide
    worst_regions = get_worst_regions(10)
    print_region_table(worst_regions, "⚠️  Top 10 Worst AWS Regions (Highest Carbon Intensity)")
    
    # 3. European regions detailed
    print_european_detailed()
    
    # 4. Comparison by continent
    continents = compare_regions_by_continent()
    print_continent_comparison(continents)
    
    # 5. Recommendations
    recommendations = generate_recommendations()
    print(f"\n{'='*100}")
    print(f" 💡 Recommendations")
    print(f"{'='*100}")
    print(f"\nBest Region Worldwide:")
    print(f"  {recommendations['best_region']['region_code']} - {recommendations['best_region']['location']}")
    print(f"  Carbon Intensity: {recommendations['best_region']['datacenter_intensity']:.1f} gCO2/kWh")
    print(f"  AWS Renewable: {recommendations['best_region']['aws_renewable_pct']*100:.0f}%")
    
    print(f"\nWorst Region Worldwide:")
    print(f"  {recommendations['worst_region']['region_code']} - {recommendations['worst_region']['location']}")
    print(f"  Carbon Intensity: {recommendations['worst_region']['datacenter_intensity']:.1f} gCO2/kWh")
    print(f"  AWS Renewable: {recommendations['worst_region']['aws_renewable_pct']*100:.0f}%")
    
    print(f"\nPotential Savings:")
    print(f"  {recommendations['potential_savings_gco2_kwh']:.1f} gCO2/kWh ({recommendations['potential_savings_percent']:.1f}% reduction)")
    print(f"\n  {recommendations['recommendation']}")
    
    # 6. Best times to run (general guidance)
    print(f"\n{'='*100}")
    print(f" ⏰ Best Times to Run Workloads (General Guidance)")
    print(f"{'='*100}")
    print("""
For regions with high solar penetration (California, Spain, Australia):
  - Best: 10:00-16:00 local time (solar peak)
  - Avoid: 18:00-22:00 local time (evening peak, fossil fuels)

For regions with high wind (Ireland, Denmark, Scotland):
  - Best: Variable, check real-time data
  - Generally better: Night and early morning (wind patterns)

For regions with hydro/nuclear (Sweden, France, Canada):
  - Good: All times (stable clean energy)
  - Best: Still during off-peak hours (less grid stress)

For regions with coal/gas (India, South Africa, Indonesia):
  - Best: Midday (some solar)
  - Avoid: Evening peak (highest fossil fuel use)
""")
    
    print(f"{'='*100}")
    print(f" 📊 Summary Statistics")
    print(f"{'='*100}")
    
    all_regions = get_all_regions_carbon_intensity()
    avg_intensity = sum(r['datacenter_intensity'] for r in all_regions) / len(all_regions)
    avg_renewable = sum(r['aws_renewable_pct'] for r in all_regions) / len(all_regions)
    
    print(f"\nTotal AWS Regions Analyzed: {len(all_regions)}")
    print(f"Average AWS Data Center Intensity: {avg_intensity:.1f} gCO2/kWh")
    print(f"Average AWS Renewable Energy: {avg_renewable*100:.1f}%")
    print(f"\nBest Region: {best_regions[0]['region_code']} ({best_regions[0]['datacenter_intensity']:.1f} gCO2/kWh)")
    print(f"Worst Region: {worst_regions[0]['region_code']} ({worst_regions[0]['datacenter_intensity']:.1f} gCO2/kWh)")
    print(f"Range: {worst_regions[0]['datacenter_intensity'] - best_regions[0]['datacenter_intensity']:.1f} gCO2/kWh")
    
    print(f"\n{'='*100}\n")


if __name__ == '__main__':
    main()
