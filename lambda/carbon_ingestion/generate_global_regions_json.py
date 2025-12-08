"""
Generate global regions JSON for dashboard
"""
import json
from aws_global_carbon_optimizer import get_all_regions_carbon_intensity

def generate_json():
    """Generate JSON file with all global regions data"""
    print("Fetching global regions data...")
    regions = get_all_regions_carbon_intensity()
    
    # Format for dashboard
    formatted_regions = []
    for region in regions:
        formatted_regions.append({
            'region_code': region['region_code'],
            'region_name': region['region_name'],
            'location': region['location'],
            'country': region['country'],
            'grid_intensity': region['grid_intensity'],
            'datacenter_intensity': round(region['datacenter_intensity'], 1),
            'aws_renewable_pct': region['aws_renewable_pct'],
            'timezone': region['timezone'],
            'lat': region['lat'],
            'lon': region['lon']
        })
    
    # Save to JSON file
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, '..', '..', 'dashboard', 'public', 'global-regions.json')
    with open(output_file, 'w') as f:
        json.dump({
            'regions': formatted_regions,
            'total': len(formatted_regions),
            'generated_at': '2025-12-07T18:51:02Z'
        }, f, indent=2)
    
    print(f"✅ Generated {len(formatted_regions)} regions")
    print(f"📁 Saved to: {output_file}")
    
    # Print summary
    best = min(formatted_regions, key=lambda x: x['datacenter_intensity'])
    worst = max(formatted_regions, key=lambda x: x['datacenter_intensity'])
    
    print(f"\n📊 Summary:")
    print(f"   Best:  {best['region_code']} - {best['datacenter_intensity']} gCO2/kWh")
    print(f"   Worst: {worst['region_code']} - {worst['datacenter_intensity']} gCO2/kWh")

if __name__ == '__main__':
    generate_json()
