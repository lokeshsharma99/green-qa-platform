"""
Green QA Platform - Enhanced Carbon Data Ingestion Lambda v2.0

INTEGRATIONS FROM WORKSPACE:
- carbontracker: Real energy measurement patterns
- Carbon-Aware-Computing: Free European forecast data (CC0)
- grid-intensity-go: Multi-provider patterns (Ember, WattTime, ElectricityMaps)
- GSF SCI formula with embodied carbon
- Cloud Carbon Footprint methodology

Data Sources:
- UK Carbon Intensity API (free, no auth) - eu-west-2
- Carbon-Aware-Computing forecasts (free, no auth) - Europe
- WattTime API (token) - US regions
- ElectricityMaps API (token) - Global
- Ember static data (embedded) - Global fallback
- EPA eGRID2020 / EEA factors - Regional fallback
"""

import boto3
import json
import os
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import base64

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ============================================================================
# CONFIGURATION
# ============================================================================

TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'green_qa_carbon_intensity')

# Cloud Carbon Footprint PUE Values
# Source: https://www.cloudcarbonfootprint.org/docs/methodology/#power-usage-effectiveness-pue
# AWS Sustainability Report: https://sustainability.aboutamazon.com/2024-amazon-sustainability-report-aws-summary.pdf
CLOUD_PUE = {
    'aws': 1.15,     # AWS average PUE (2024 Sustainability Report)
    'gcp': 1.1,      # GCP average PUE
    'azure': 1.185   # Azure average PUE
}

# Energy coefficients (Watts per vCPU)
# Source: https://github.com/cloud-carbon-footprint/cloud-carbon-footprint/blob/trunk/packages/aws/src/lib/AWSInstanceTypes.ts
# SPECpower benchmarks: https://www.spec.org/power_ssj2008/
VCPU_TDP_WATTS = {
    'default': 10.0,      # Intel Xeon Scalable (most common in AWS)
    'graviton': 7.0,      # AWS Graviton2 (ARM-based, more efficient)
    'amd_epyc': 8.5,      # AMD EPYC processors
    'intel_xeon': 10.0,   # Intel Xeon baseline
    'gpu_v100': 300.0,    # NVIDIA V100 GPU
    'gpu_a100': 400.0     # NVIDIA A100 GPU
}

# Memory coefficient (kWh per GB-hour)
# Source: https://www.cloudcarbonfootprint.org/docs/methodology/#memory
# Based on: https://github.com/etsy/cloud-jewels (Etsy's Cloud Jewels research)
# Calculation: 1 GB RAM uses ~0.392 Watts continuously
MEMORY_COEFFICIENT_KWH_PER_GB = 0.000392

# Embodied emissions per vCPU-hour (gCO2)
# Sources:
# - Teads Engineering: https://medium.com/teads-engineering/building-an-aws-ec2-carbon-emissions-dataset-3f0fd76c98ac
# - Dell Server LCA: https://i.dell.com/sites/csdocuments/CorpComm_Docs/en/carbon-footprint-poweredge-r740.pdf
# - CCF Methodology: https://www.cloudcarbonfootprint.org/docs/methodology/#embodied-emissions
# Calculation: Server manufacturing (~1000 kg CO2) / lifespan (4 years) / vCPUs (40)
EMBODIED_EMISSIONS_G_PER_VCPU_HOUR = {
    'aws': 2.5,           # AWS standard instances
    'aws_graviton': 1.8,  # AWS Graviton (more efficient manufacturing)
    'gcp': 2.3,           # GCP instances
    'azure': 2.6          # Azure instances
}

# EPA eGRID2020 NERC Region Emission Factors (gCO2/kWh)
EPA_EGRID_FACTORS = {
    'NPCC': 230, 'RFCE': 390, 'RFCM': 550, 'RFCW': 520,
    'SERC': 420, 'FRCC': 400, 'TRE': 380, 'WECC': 280, 'MRO': 500, 'SPP': 400
}

# EEA Emission Factors for Europe (gCO2/kWh)
EEA_FACTORS = {
    'DE': 380, 'FR': 60, 'GB': 250, 'IE': 300, 'SE': 30,
    'FI': 100, 'NL': 350, 'ES': 200, 'IT': 280, 'PL': 600,
    'AT': 120, 'CH': 50, 'BE': 170, 'DK': 150, 'NO': 20
}

# Ember Climate Annual Data (gCO2/kWh) - from grid-intensity-go
EMBER_DATA = {
    'SE': 30, 'NO': 20, 'FR': 60, 'CH': 50, 'FI': 100, 'AT': 120,
    'DK': 150, 'BE': 170, 'ES': 200, 'GB': 250, 'IT': 280, 'IE': 300,
    'NL': 350, 'DE': 380, 'PL': 600, 'US': 380, 'JP': 450, 'AU': 550,
    'IN': 650, 'CN': 550, 'SG': 400
}

# Carbon-Aware-Computing Free Forecast URLs (CC0 licensed)
CARBON_AWARE_COMPUTING_FORECASTS = {
    'de': 'https://carbonawarecomputing.blob.core.windows.net/forecasts/de.json',
    'fr': 'https://carbonawarecomputing.blob.core.windows.net/forecasts/fr.json',
    'at': 'https://carbonawarecomputing.blob.core.windows.net/forecasts/at.json',
    'ch': 'https://carbonawarecomputing.blob.core.windows.net/forecasts/ch.json',
    'uk': 'https://carbonawarecomputing.blob.core.windows.net/forecasts/uk.json',
}

# AWS Region Configuration
AWS_REGION_CONFIG = {
    'eu-west-2': {
        'country': 'GB', 'grid_zone': 'GB',
        'source_priority': ['uk_carbon_intensity', 'carbon_aware_computing', 'eea', 'ember'],
        'provider': 'aws'
    },
    'eu-north-1': {
        'country': 'SE', 'grid_zone': 'SE',
        'source_priority': ['electricitymaps', 'eea', 'ember'],
        'provider': 'aws'
    },
    'eu-west-1': {
        'country': 'IE', 'grid_zone': 'IE',
        'source_priority': ['electricitymaps', 'eea', 'ember'],
        'provider': 'aws'
    },
    'eu-west-3': {
        'country': 'FR', 'grid_zone': 'FR',
        'source_priority': ['carbon_aware_computing', 'electricitymaps', 'eea', 'ember'],
        'provider': 'aws'
    },
    'eu-central-1': {
        'country': 'DE', 'grid_zone': 'DE',
        'source_priority': ['carbon_aware_computing', 'electricitymaps', 'eea', 'ember'],
        'provider': 'aws'
    },
    'eu-south-1': {
        'country': 'IT', 'grid_zone': 'IT-NO',
        'source_priority': ['electricitymaps', 'eea', 'ember'],
        'provider': 'aws'
    },
    'eu-south-2': {
        'country': 'ES', 'grid_zone': 'ES',
        'source_priority': ['electricitymaps', 'eea', 'ember'],
        'provider': 'aws'
    },
    'eu-central-2': {
        'country': 'CH', 'grid_zone': 'CH',
        'source_priority': ['carbon_aware_computing', 'electricitymaps', 'eea', 'ember'],
        'provider': 'aws'
    },
    'us-east-1': {
        'country': 'US', 'grid_zone': 'US-SERC-SRVC', 'nerc': 'SERC',
        'watttime_ba': 'PJM',
        'source_priority': ['watttime', 'epa_egrid', 'ember'],
        'provider': 'aws'
    },
    'us-east-2': {
        'country': 'US', 'grid_zone': 'US-RFC-RFCW', 'nerc': 'RFCW',
        'watttime_ba': 'MISO',
        'source_priority': ['watttime', 'epa_egrid', 'ember'],
        'provider': 'aws'
    },
    'us-west-1': {
        'country': 'US', 'grid_zone': 'US-CAL-CISO', 'nerc': 'WECC',
        'watttime_ba': 'CAISO_NORTH',
        'source_priority': ['watttime', 'epa_egrid', 'ember'],
        'provider': 'aws'
    },
    'us-west-2': {
        'country': 'US', 'grid_zone': 'US-NW-PACW', 'nerc': 'WECC',
        'watttime_ba': 'PACW',
        'source_priority': ['watttime', 'epa_egrid', 'ember'],
        'provider': 'aws'
    },
    'ap-northeast-1': {
        'country': 'JP', 'grid_zone': 'JP-TK',
        'source_priority': ['electricitymaps', 'ember'],
        'provider': 'aws'
    },
    'ap-southeast-1': {
        'country': 'SG', 'grid_zone': 'SG',
        'source_priority': ['electricitymaps', 'ember'],
        'provider': 'aws'
    },
    'ap-southeast-2': {
        'country': 'AU', 'grid_zone': 'AU-NSW',
        'source_priority': ['electricitymaps', 'ember'],
        'provider': 'aws'
    }
}


# ============================================================================
# API CLIENTS
# ============================================================================

class UKCarbonIntensityAPI:
    """UK Carbon Intensity API - FREE, NO AUTH. Source: carbonintensity.org.uk"""
    BASE_URL = 'https://api.carbonintensity.org.uk'
    
    @staticmethod
    def get_current_intensity() -> Optional[Dict]:
        try:
            req = Request(f'{UKCarbonIntensityAPI.BASE_URL}/intensity',
                         headers={'Accept': 'application/json'})
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                current = data['data'][0]
            return {
                'intensity': current['intensity']['actual'] or current['intensity']['forecast'],
                'index': current['intensity']['index'],
                'from': current['from'], 'to': current['to']
            }
        except Exception as e:
            logger.error(f"UK Carbon API error: {e}")
            return None
    
    @staticmethod
    def get_forecast_48h() -> Optional[List[Dict]]:
        try:
            now = datetime.utcnow().strftime('%Y-%m-%dT%H:%MZ')
            req = Request(f'{UKCarbonIntensityAPI.BASE_URL}/intensity/{now}/fw48h',
                         headers={'Accept': 'application/json'})
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
            return [{'from': f['from'], 'to': f['to'],
                    'intensity': f['intensity']['forecast'],
                    'index': f['intensity']['index']} for f in data['data'][:96]]
        except Exception as e:
            logger.error(f"UK Carbon forecast error: {e}")
            return None
    
    @staticmethod
    def get_generation_mix() -> Optional[List[Dict]]:
        try:
            req = Request(f'{UKCarbonIntensityAPI.BASE_URL}/generation',
                         headers={'Accept': 'application/json'})
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
            return data['data']['generationmix']
        except Exception as e:
            logger.error(f"UK Generation mix error: {e}")
            return None


class CarbonAwareComputingAPI:
    """Carbon-Aware-Computing forecasts - FREE, NO AUTH, CC0 licensed."""
    
    @staticmethod
    def get_forecast(country_code: str) -> Optional[List[Dict]]:
        url = CARBON_AWARE_COMPUTING_FORECASTS.get(country_code.lower())
        if not url:
            return None
        try:
            req = Request(url, headers={'Accept': 'application/json'})
            with urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode())
            # Format matches Carbon Aware SDK
            optimal_points = data.get('optimalDataPoints', [])
            return [{'timestamp': p.get('timestamp'), 'intensity': p.get('value'),
                    'location': p.get('location')} for p in optimal_points[:48]]
        except Exception as e:
            logger.error(f"Carbon-Aware-Computing error for {country_code}: {e}")
            return None


class WattTimeAPI:
    """WattTime API for US marginal emissions. Requires auth."""
    BASE_URL = 'https://api.watttime.org'
    
    def __init__(self):
        self.username = os.environ.get('WATTTIME_USER')
        self.password = os.environ.get('WATTTIME_PASSWORD')
        self._token = None
        self._token_expiry = None
    
    def _get_token(self) -> Optional[str]:
        if self._token and self._token_expiry and datetime.utcnow() < self._token_expiry:
            return self._token
        if not self.username or not self.password:
            return None
        try:
            auth = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
            req = Request(f'{self.BASE_URL}/login', headers={'Authorization': f'Basic {auth}'})
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                self._token = data['token']
                self._token_expiry = datetime.utcnow() + timedelta(minutes=25)
                return self._token
        except Exception as e:
            logger.error(f"WattTime auth error: {e}")
            return None
    
    def get_current_index(self, ba: str) -> Optional[Dict]:
        token = self._get_token()
        if not token:
            return None
        try:
            req = Request(f'{self.BASE_URL}/v3/signal-index?ba={ba}',
                         headers={'Authorization': f'Bearer {token}'})
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
            moer = data.get('value', 0)
            intensity_g_kwh = moer * 453.592 / 1000
            return {'intensity': round(intensity_g_kwh, 1), 'percent': data.get('percent'),
                   'ba': ba, 'validUntil': data.get('validUntil')}
        except Exception as e:
            logger.error(f"WattTime index error: {e}")
            return None


class ElectricityMapsAPI:
    """ElectricityMaps API for global carbon intensity. Requires token."""
    BASE_URL = 'https://api.electricitymap.org/v3'
    
    def __init__(self):
        self.token = os.environ.get('ELECTRICITY_MAPS_TOKEN')
    
    def get_current_intensity(self, zone: str) -> Optional[Dict]:
        if not self.token:
            return None
        try:
            req = Request(f'{self.BASE_URL}/carbon-intensity/latest?zone={zone}',
                         headers={'auth-token': self.token})
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
            return {'intensity': data.get('carbonIntensity'), 'datetime': data.get('datetime'),
                   'zone': zone, 'isEstimated': data.get('isEstimated', False)}
        except Exception as e:
            logger.error(f"ElectricityMaps error for {zone}: {e}")
            return None


# ============================================================================
# CARBON CALCULATIONS (GSF SCI + CCF Methodology)
# ============================================================================

def calculate_embodied_carbon(vcpu_count: int, duration_hours: float, provider: str = 'aws') -> float:
    """Calculate embodied carbon using CCF methodology."""
    rate = EMBODIED_EMISSIONS_G_PER_VCPU_HOUR.get(provider, 2.5)
    return vcpu_count * duration_hours * rate


def calculate_sci(energy_kwh: float, carbon_intensity: float,
                  embodied_carbon_g: float = 0, functional_unit: float = 1) -> Tuple[float, Dict]:
    """
    Calculate Software Carbon Intensity using GSF formula.
    SCI = ((E × I) + M) / R
    """
    operational = energy_kwh * carbon_intensity
    total = operational + embodied_carbon_g
    sci = total / functional_unit if functional_unit > 0 else total
    
    return sci, {
        'energy_kwh': round(energy_kwh, 6),
        'carbon_intensity_gco2_kwh': round(carbon_intensity, 1),
        'operational_emissions_g': round(operational, 4),
        'embodied_emissions_g': round(embodied_carbon_g, 4),
        'total_emissions_g': round(total, 4),
        'functional_unit': functional_unit,
        'sci_gco2_per_unit': round(sci, 4)
    }


def calculate_test_carbon_footprint(duration_seconds: float, vcpu_count: int = 2,
                                    memory_gb: float = 4.0, carbon_intensity: float = 300,
                                    provider: str = 'aws', instance_type: str = 'default') -> Dict:
    """Calculate carbon footprint for test execution using CCF methodology."""
    duration_hours = duration_seconds / 3600
    pue = CLOUD_PUE.get(provider, 1.15)
    
    # Compute energy
    vcpu_tdp = VCPU_TDP_WATTS.get(instance_type, VCPU_TDP_WATTS['default'])
    compute_kwh = (vcpu_count * vcpu_tdp * duration_hours) / 1000
    
    # Memory energy
    memory_kwh = memory_gb * duration_hours * MEMORY_COEFFICIENT_KWH_PER_GB
    
    # Total with PUE
    total_energy_kwh = (compute_kwh + memory_kwh) * pue
    
    # Embodied carbon (now included!)
    embodied_g = calculate_embodied_carbon(vcpu_count, duration_hours, provider)
    
    # Calculate SCI
    sci, breakdown = calculate_sci(
        energy_kwh=total_energy_kwh,
        carbon_intensity=carbon_intensity,
        embodied_carbon_g=embodied_g,
        functional_unit=1
    )
    
    return {
        'duration_seconds': duration_seconds,
        'vcpu_count': vcpu_count,
        'memory_gb': memory_gb,
        'provider': provider,
        'pue': pue,
        'compute_energy_kwh': round(compute_kwh, 6),
        'memory_energy_kwh': round(memory_kwh, 6),
        'total_energy_kwh': round(total_energy_kwh, 6),
        'embodied_carbon_g': round(embodied_g, 4),
        'carbon_intensity_gco2_kwh': carbon_intensity,
        'carbon_emissions_g': round(breakdown['total_emissions_g'], 4),
        'carbon_emissions_kg': round(breakdown['total_emissions_g'] / 1000, 6),
        'sci': sci,
        'breakdown': breakdown
    }


# ============================================================================
# MULTI-SOURCE DATA FETCHING
# ============================================================================

def get_carbon_intensity_multi_source(region: str) -> Dict:
    """Get carbon intensity using multiple sources with fallback chain."""
    if region not in AWS_REGION_CONFIG:
        logger.warning(f"Unknown region: {region}")
        return {'intensity': 450, 'source': 'fallback', 'forecast': [], 'region': region}
    
    config = AWS_REGION_CONFIG[region]
    country = config.get('country', '')
    
    for source in config['source_priority']:
        result = None
        
        if source == 'uk_carbon_intensity':
            current = UKCarbonIntensityAPI.get_current_intensity()
            if current:
                forecast = UKCarbonIntensityAPI.get_forecast_48h() or []
                mix = UKCarbonIntensityAPI.get_generation_mix()
                result = {
                    'intensity': current['intensity'],
                    'index': current['index'],
                    'source': 'uk_carbon_intensity',
                    'source_name': 'UK National Grid ESO',
                    'is_realtime': True,
                    'forecast': forecast,
                    'generation_mix': mix
                }
        
        elif source == 'carbon_aware_computing':
            forecast = CarbonAwareComputingAPI.get_forecast(country.lower())
            if forecast and len(forecast) > 0:
                # Use first optimal point as current
                result = {
                    'intensity': forecast[0].get('intensity', EEA_FACTORS.get(country, 300)),
                    'source': 'carbon_aware_computing',
                    'source_name': 'Carbon-Aware-Computing (Fraunhofer ISE)',
                    'is_realtime': True,
                    'forecast': forecast
                }
        
        elif source == 'watttime':
            wt = WattTimeAPI()
            ba = config.get('watttime_ba')
            if ba:
                current = wt.get_current_index(ba)
                if current:
                    result = {
                        'intensity': current['intensity'],
                        'percent': current.get('percent'),
                        'source': 'watttime',
                        'source_name': 'WattTime',
                        'is_realtime': True,
                        'forecast': []
                    }
        
        elif source == 'electricitymaps':
            em = ElectricityMapsAPI()
            zone = config.get('grid_zone')
            if zone:
                current = em.get_current_intensity(zone)
                if current and current.get('intensity'):
                    result = {
                        'intensity': current['intensity'],
                        'source': 'electricitymaps',
                        'source_name': 'ElectricityMaps',
                        'is_realtime': True,
                        'forecast': []
                    }
        
        elif source == 'epa_egrid':
            nerc = config.get('nerc')
            if nerc and nerc in EPA_EGRID_FACTORS:
                result = {
                    'intensity': EPA_EGRID_FACTORS[nerc],
                    'source': 'epa_egrid',
                    'source_name': 'EPA eGRID2020',
                    'is_realtime': False,
                    'nerc_region': nerc,
                    'forecast': []
                }
        
        elif source == 'eea':
            if country in EEA_FACTORS:
                result = {
                    'intensity': EEA_FACTORS[country],
                    'source': 'eea',
                    'source_name': 'European Environment Agency',
                    'is_realtime': False,
                    'forecast': []
                }
        
        elif source == 'ember':
            if country in EMBER_DATA:
                result = {
                    'intensity': EMBER_DATA[country],
                    'source': 'ember',
                    'source_name': 'Ember Climate (Annual)',
                    'is_realtime': False,
                    'forecast': []
                }
        
        if result:
            result['region'] = region
            result['country'] = country
            result['grid_zone'] = config.get('grid_zone')
            return result
    
    # Final fallback
    return {
        'region': region,
        'country': country,
        'intensity': EMBER_DATA.get(country, 450),
        'source': 'fallback',
        'source_name': 'Static Fallback',
        'is_realtime': False,
        'forecast': []
    }


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def store_carbon_data(region: str, data: Dict) -> None:
    """Store carbon intensity data in DynamoDB."""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(TABLE_NAME)
    
    timestamp = int(datetime.utcnow().timestamp())
    ttl = int((datetime.utcnow() + timedelta(hours=48)).timestamp())
    
    item = {
        'region_id': region,
        'timestamp': timestamp,
        'carbon_intensity': Decimal(str(data['intensity'])),
        'source': data.get('source', 'unknown'),
        'source_name': data.get('source_name', ''),
        'is_realtime': data.get('is_realtime', False),
        'country': data.get('country'),
        'grid_zone': data.get('grid_zone'),
        'ttl': ttl
    }
    
    if data.get('index'):
        item['index'] = data['index']
    if data.get('generation_mix'):
        item['generation_mix'] = data['generation_mix']
    if data.get('forecast'):
        item['forecast'] = json.dumps(data['forecast'][:48])
    
    table.put_item(Item=item)
    logger.info(f"Stored: {region} = {data['intensity']} gCO2/kWh ({data['source']})")


def get_all_regions_summary() -> List[Dict]:
    """Get carbon intensity for all configured regions, sorted by intensity."""
    results = []
    for region in AWS_REGION_CONFIG.keys():
        data = get_carbon_intensity_multi_source(region)
        results.append({
            'region': region,
            'intensity': data['intensity'],
            'source': data['source'],
            'source_name': data.get('source_name', ''),
            'is_realtime': data.get('is_realtime', False),
            'country': AWS_REGION_CONFIG[region].get('country')
        })
    results.sort(key=lambda x: x['intensity'])
    return results


# ============================================================================
# LAMBDA HANDLER
# ============================================================================

def lambda_handler(event: Dict, context) -> Dict:
    """
    Main Lambda handler.
    
    Actions:
        - refresh: Refresh all regions
        - get_current: Get intensity for one region
        - get_optimal: Get lowest-carbon regions
        - calculate: Calculate carbon for workload
        - get_all: Get all regions data
    """
    action = event.get('action', 'refresh')
    
    try:
        if action == 'refresh':
            results = {}
            for region in AWS_REGION_CONFIG.keys():
                try:
                    data = get_carbon_intensity_multi_source(region)
                    store_carbon_data(region, data)
                    results[region] = {
                        'intensity': data['intensity'],
                        'source': data['source'],
                        'is_realtime': data.get('is_realtime', False)
                    }
                except Exception as e:
                    logger.error(f"Error processing {region}: {e}")
                    results[region] = {'error': str(e)}
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'message': 'Carbon data refreshed',
                    'timestamp': datetime.utcnow().isoformat(),
                    'regions_updated': len([r for r in results.values() if 'error' not in r]),
                    'results': results
                })
            }
        
        elif action == 'get_current':
            region = event.get('region', 'eu-west-2')
            data = get_carbon_intensity_multi_source(region)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'region': region,
                    'carbon_intensity': data['intensity'],
                    'source': data['source'],
                    'source_name': data.get('source_name', ''),
                    'is_realtime': data.get('is_realtime', False),
                    'index': data.get('index'),
                    'forecast': data.get('forecast', [])[:24],
                    'generation_mix': data.get('generation_mix'),
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        elif action == 'get_optimal':
            limit = event.get('limit', 5)
            summary = get_all_regions_summary()[:limit]
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'optimal_regions': summary,
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        elif action == 'get_all':
            summary = get_all_regions_summary()
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'regions': summary,
                    'total_regions': len(summary),
                    'realtime_count': len([r for r in summary if r.get('is_realtime')]),
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        
        elif action == 'calculate':
            region = event.get('region', 'eu-west-2')
            duration = event.get('duration_seconds', 3600)
            vcpu = event.get('vcpu_count', 2)
            memory = event.get('memory_gb', 4.0)
            
            data = get_carbon_intensity_multi_source(region)
            result = calculate_test_carbon_footprint(
                duration_seconds=duration,
                vcpu_count=vcpu,
                memory_gb=memory,
                carbon_intensity=data['intensity'],
                provider='aws'
            )
            result['region'] = region
            result['source'] = data['source']
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(result)
            }
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Unknown action: {action}'})
            }
    
    except Exception as e:
        logger.error(f"Handler error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


if __name__ == '__main__':
    print("=== Enhanced Carbon Ingestion Lambda v2.0 ===\n")
    
    print("1. Testing UK Carbon Intensity API...")
    uk_data = UKCarbonIntensityAPI.get_current_intensity()
    if uk_data:
        print(f"   UK: {uk_data['intensity']} gCO2/kWh ({uk_data['index']})")
    
    print("\n2. Testing Carbon-Aware-Computing forecasts...")
    for country in ['de', 'fr', 'uk']:
        forecast = CarbonAwareComputingAPI.get_forecast(country)
        if forecast:
            print(f"   {country.upper()}: {len(forecast)} forecast points")
    
    print("\n3. Testing multi-source for regions...")
    for region in ['eu-west-2', 'eu-north-1', 'eu-central-1', 'us-east-1']:
        data = get_carbon_intensity_multi_source(region)
        rt = "🟢" if data.get('is_realtime') else "🟡"
        print(f"   {rt} {region}: {data['intensity']} gCO2/kWh ({data['source']})")
    
    print("\n4. Testing carbon calculation with embodied carbon...")
    footprint = calculate_test_carbon_footprint(
        duration_seconds=3600, vcpu_count=4, memory_gb=8.0, carbon_intensity=250
    )
    print(f"   Energy: {footprint['total_energy_kwh']} kWh")
    print(f"   Embodied: {footprint['embodied_carbon_g']} gCO2")
    print(f"   Total: {footprint['carbon_emissions_g']} gCO2")
    
    print("\n=== Tests complete ===")
