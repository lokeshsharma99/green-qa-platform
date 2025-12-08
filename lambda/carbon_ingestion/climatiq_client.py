"""
Climatiq API Client for ZeroCarb Platform

Provides comprehensive carbon calculation capabilities using Climatiq's API:
- Cloud computing validation
- Scope 3 procurement emissions
- AI-powered autopilot calculations
- Emission factor search
- Intermodal freight emissions

API Documentation: https://www.climatiq.io/docs
"""

import os
import logging
import requests
from typing import Dict, List, Optional, Union
from datetime import datetime
from functools import lru_cache

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Configuration
CLIMATIQ_API_KEY = os.environ.get('CLIMATIQ_API_KEY', 'QQP3JPFPK11TF0ADEAMD9XECG0')
CLIMATIQ_BASE_URL = 'https://api.climatiq.io'
CLIMATIQ_PREVIEW_URL = 'https://preview.api.climatiq.io'
DATA_VERSION = '^21'  # Use latest v21 data

# Request timeout
TIMEOUT = 30


class ClimatiqClient:
    """Client for Climatiq API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or CLIMATIQ_API_KEY
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def _request(self, method: str, url: str, **kwargs) -> Dict:
        """Make HTTP request with error handling"""
        try:
            kwargs['timeout'] = kwargs.get('timeout', TIMEOUT)
            kwargs['headers'] = self.headers
            
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"Climatiq API HTTP error: {e}")
            logger.error(f"Response: {e.response.text if e.response else 'No response'}")
            raise
        except requests.exceptions.Timeout:
            logger.error(f"Climatiq API timeout after {TIMEOUT}s")
            raise
        except Exception as e:
            logger.error(f"Climatiq API error: {e}")
            raise
    
    # ========================================================================
    # CLOUD COMPUTING
    # ========================================================================
    
    def cloud_compute_instance(
        self,
        provider: str,
        region: str,
        instance: str,
        duration: float,
        duration_unit: str = 'hour',
        vcpu_utilization: float = 0.5,
        year: int = None
    ) -> Dict:
        """
        Calculate cloud instance emissions
        
        Args:
            provider: 'aws', 'azure', 'gcp'
            region: Cloud provider region
            instance: Instance type (e.g., 't2.micro')
            duration: How long instance runs
            duration_unit: 'hour', 'day', 'year'
            vcpu_utilization: CPU utilization 0-1
            year: Year of usage
        
        Returns:
            {
                'co2e': float,  # kg CO2e
                'co2e_unit': 'kg',
                'co2e_calculation_method': 'ar5',
                'emission_factor': {...},
                'constituent_gases': {...}
            }
        """
        url = f"{CLIMATIQ_BASE_URL}/compute/v1/{provider}/instance"
        
        payload = {
            'region': region,
            'instance': instance,
            'duration': duration,
            'duration_unit': duration_unit,
            'average_vcpu_utilization': vcpu_utilization
        }
        
        if year:
            payload['year'] = year
        
        return self._request('POST', url, json=payload)
    
    def cloud_compute_cpu(
        self,
        provider: str,
        region: str,
        cpu_count: int,
        duration: float,
        duration_unit: str = 'hour',
        cpu_load: float = 0.5
    ) -> Dict:
        """Calculate CPU electricity emissions"""
        url = f"{CLIMATIQ_BASE_URL}/compute/v1/{provider}/cpu"
        
        payload = {
            'region': region,
            'cpu_count': cpu_count,
            'duration': duration,
            'duration_unit': duration_unit,
            'cpu_load': cpu_load
        }
        
        return self._request('POST', url, json=payload)
    
    def cloud_compute_memory(
        self,
        provider: str,
        region: str,
        data: float,
        data_unit: str = 'GB',
        duration: float = 1,
        duration_unit: str = 'hour'
    ) -> Dict:
        """Calculate memory availability emissions"""
        url = f"{CLIMATIQ_BASE_URL}/compute/v1/{provider}/memory"
        
        payload = {
            'region': region,
            'data': data,
            'data_unit': data_unit,
            'duration': duration,
            'duration_unit': duration_unit
        }
        
        return self._request('POST', url, json=payload)
    
    # ========================================================================
    # PROCUREMENT (Scope 3.1)
    # ========================================================================
    
    def procurement_spend(
        self,
        classification_code: str,
        classification_type: str,
        spend_year: int,
        spend_region: str,
        money: float,
        money_unit: str = 'usd',
        tax_margin: float = None,
        trade_margin: float = None,
        transport_margin: float = None
    ) -> Dict:
        """
        Calculate Scope 3.1 emissions from spending
        
        Args:
            classification_code: Industry code (e.g., '62' for IT services)
            classification_type: 'nace2', 'isic4', 'naics2017', 'mcc', 'unspsc'
            spend_year: Year of expenditure
            spend_region: UN/LOCODE (e.g., 'US', 'GB')
            money: Amount spent
            money_unit: Currency code (e.g., 'usd', 'eur', 'gbp')
            tax_margin: Optional tax margin override
            trade_margin: Optional trade margin override
            transport_margin: Optional transport margin override
        
        Returns:
            {
                'estimate': {
                    'co2e': float,  # kg CO2e
                    'co2e_unit': 'kg',
                    'emission_factor': {...}
                },
                'calculation_details': {
                    'tax_margin': float,
                    'trade_margin': float,
                    'transport_margin': float,
                    'inflation_applied': float
                }
            }
        """
        url = f"{CLIMATIQ_BASE_URL}/procurement/v1/spend"
        
        payload = {
            'activity': {
                'classification_code': classification_code,
                'classification_type': classification_type
            },
            'spend_year': spend_year,
            'spend_region': spend_region,
            'money': money,
            'money_unit': money_unit
        }
        
        if tax_margin is not None:
            payload['tax_margin'] = tax_margin
        if trade_margin is not None:
            payload['trade_margin'] = trade_margin
        if transport_margin is not None:
            payload['transport_margin'] = transport_margin
        
        return self._request('POST', url, json=payload)
    
    def procurement_spend_batch(self, requests_list: List[Dict]) -> List[Dict]:
        """Batch procurement calculations (max 100)"""
        url = f"{CLIMATIQ_BASE_URL}/procurement/v1/spend/batch"
        
        if len(requests_list) > 100:
            raise ValueError("Maximum 100 requests per batch")
        
        return self._request('POST', url, json=requests_list)
    
    # ========================================================================
    # AUTOPILOT (AI-Powered)
    # ========================================================================
    
    def autopilot_suggest(
        self,
        text: str,
        model: str = 'general',
        unit_type: List[str] = None,
        year: int = None,
        region: str = None,
        region_fallback: bool = False,
        max_suggestions: int = 10
    ) -> Dict:
        """
        AI-powered emission factor suggestions
        
        Args:
            text: Natural language activity description
            model: 'general' (default)
            unit_type: Filter by unit types
            year: Activity year
            region: UN/LOCODE
            region_fallback: Accept less specific regions
            max_suggestions: Max results (1-20)
        
        Returns:
            {
                'results': [
                    {
                        'suggestion_id': str,
                        'emission_factor': {...},
                        'suggestion_details': {
                            'label': 'accept' or 'review'
                        }
                    }
                ],
                'model': str,
                'model_version': str
            }
        """
        url = f"{CLIMATIQ_PREVIEW_URL}/autopilot/v1-preview4/suggest"
        
        payload = {
            'text': text,
            'model': model,
            'max_suggestions': max_suggestions
        }
        
        if unit_type:
            payload['unit_type'] = unit_type
        if year:
            payload['year'] = year
        if region:
            payload['region'] = region
            payload['region_fallback'] = region_fallback
        
        return self._request('POST', url, json=payload)
    
    def autopilot_estimate(
        self,
        suggestion_id: str,
        parameters: Dict
    ) -> Dict:
        """
        Calculate emissions using autopilot suggestion
        
        Args:
            suggestion_id: ID from autopilot_suggest
            parameters: Activity parameters (e.g., {'energy': 100, 'energy_unit': 'kWh'})
        
        Returns:
            Standard estimation response
        """
        url = f"{CLIMATIQ_PREVIEW_URL}/autopilot/v1-preview4/suggest/estimate"
        
        payload = {
            'suggestion_id': suggestion_id,
            'parameters': parameters
        }
        
        return self._request('POST', url, json=payload)
    
    def autopilot_one_shot(
        self,
        text: str,
        parameters: Dict,
        model: str = 'general',
        year: int = None,
        region: str = None,
        region_fallback: bool = False
    ) -> Dict:
        """
        One-shot AI-powered estimation (suggest + estimate in one call)
        
        Args:
            text: Natural language activity description
            parameters: Activity parameters
            model: 'general'
            year: Activity year
            region: UN/LOCODE
            region_fallback: Accept fallback regions
        
        Returns:
            Standard estimation response with AI metadata
        """
        url = f"{CLIMATIQ_PREVIEW_URL}/autopilot/v1-preview4/estimate"
        
        payload = {
            'text': text,
            'parameters': parameters,
            'model': model
        }
        
        if year:
            payload['year'] = year
        if region:
            payload['region'] = region
            payload['region_fallback'] = region_fallback
        
        return self._request('POST', url, json=payload)
    
    # ========================================================================
    # SEARCH & ESTIMATE
    # ========================================================================
    
    @lru_cache(maxsize=100)
    def search_emission_factors(
        self,
        query: str = None,
        activity_id: str = None,
        category: str = None,
        sector: str = None,
        region: str = None,
        year: int = None,
        unit_type: str = None,
        source: str = None,
        page: int = 1,
        results_per_page: int = 20
    ) -> Dict:
        """
        Search emission factors
        
        Args:
            query: Free-text search
            activity_id: Filter by activity ID
            category: Filter by category
            sector: Filter by sector
            region: Filter by region (UN/LOCODE)
            year: Filter by year
            unit_type: Filter by unit type
            source: Filter by data source
            page: Page number
            results_per_page: Results per page (max 500)
        
        Returns:
            {
                'current_page': int,
                'last_page': int,
                'total_results': int,
                'results': [
                    {
                        'id': str,
                        'activity_id': str,
                        'name': str,
                        'category': str,
                        'factor': float,
                        'unit': str,
                        'source': str,
                        'year': int,
                        'region': str,
                        'region_name': str,
                        'data_quality_flags': []
                    }
                ]
            }
        """
        url = f"{CLIMATIQ_BASE_URL}/data/v1/search"
        
        params = {
            'data_version': DATA_VERSION,
            'page': page,
            'results_per_page': min(results_per_page, 500)
        }
        
        if query:
            params['query'] = query
        if activity_id:
            params['activity_id'] = activity_id
        if category:
            params['category'] = category
        if sector:
            params['sector'] = sector
        if region:
            params['region'] = region
        if year:
            params['year'] = year
        if unit_type:
            params['unit_type'] = unit_type
        if source:
            params['source'] = source
        
        return self._request('GET', url, params=params)
    
    def estimate(
        self,
        emission_factor: Dict,
        parameters: Dict
    ) -> Dict:
        """
        Calculate emissions using emission factor
        
        Args:
            emission_factor: {'activity_id': str, 'data_version': str} or {'id': str}
            parameters: Activity parameters (varies by unit type)
        
        Returns:
            {
                'co2e': float,  # kg CO2e
                'co2e_unit': 'kg',
                'co2e_calculation_method': str,
                'emission_factor': {...},
                'constituent_gases': {...},
                'activity_data': {...}
            }
        """
        url = f"{CLIMATIQ_BASE_URL}/data/v1/estimate"
        
        payload = {
            'emission_factor': emission_factor,
            'parameters': parameters
        }
        
        return self._request('POST', url, json=payload)
    
    def estimate_batch(self, requests_list: List[Dict]) -> List[Dict]:
        """Batch estimate (max 100)"""
        url = f"{CLIMATIQ_BASE_URL}/data/v1/estimate/batch"
        
        if len(requests_list) > 100:
            raise ValueError("Maximum 100 requests per batch")
        
        return self._request('POST', url, json=requests_list)
    
    # ========================================================================
    # INTERMODAL FREIGHT
    # ========================================================================
    
    def freight_intermodal(
        self,
        route: List[Dict],
        cargo_weight: float,
        cargo_weight_unit: str = 't'
    ) -> Dict:
        """
        Calculate intermodal freight emissions
        
        Args:
            route: List of locations and legs
            cargo_weight: Weight of cargo
            cargo_weight_unit: 't' (tonnes) or 'kg'
        
        Returns:
            {
                'co2e': float,  # kg CO2e
                'hub_equipment_co2e': float,
                'vehicle_operation_co2e': float,
                'vehicle_energy_provision_co2e': float,
                'distance_km': float,
                'route': [...]  # Detailed route
            }
        """
        url = f"{CLIMATIQ_BASE_URL}/freight/v3/intermodal"
        
        payload = {
            'route': route,
            'cargo': {
                'weight': cargo_weight,
                'weight_unit': cargo_weight_unit
            }
        }
        
        return self._request('POST', url, json=payload)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def validate_cloud_calculation(
    our_result: Dict,
    provider: str,
    region: str,
    instance: str,
    duration_hours: float,
    vcpu_util: float = 0.5
) -> Dict:
    """
    Compare our calculation with Climatiq's
    
    Args:
        our_result: Our calculation result
        provider: 'aws', 'azure', 'gcp'
        region: Cloud region
        instance: Instance type
        duration_hours: Duration in hours
        vcpu_util: CPU utilization
    
    Returns:
        {
            'our_calculation': {...},
            'climatiq_calculation': {...},
            'difference_kg': float,
            'difference_percent': float,
            'recommendation': 'use_ours' | 'use_climatiq' | 'review'
        }
    """
    try:
        client = ClimatiqClient()
        
        climatiq_result = client.cloud_compute_instance(
            provider=provider,
            region=region,
            instance=instance,
            duration=duration_hours,
            duration_unit='hour',
            vcpu_utilization=vcpu_util
        )
        
        our_co2e_kg = our_result.get('carbon_emissions_g', 0) / 1000
        climatiq_co2e_kg = climatiq_result.get('co2e', 0)
        
        difference_kg = abs(our_co2e_kg - climatiq_co2e_kg)
        difference_percent = (difference_kg / our_co2e_kg * 100) if our_co2e_kg > 0 else 0
        
        # Recommendation logic
        if difference_percent < 10:
            recommendation = 'use_ours'  # Close enough, use our real-time data
        elif difference_percent < 25:
            recommendation = 'use_climatiq'  # Moderate difference, use industry standard
        else:
            recommendation = 'review'  # Large difference, needs investigation
        
        return {
            'our_calculation': {
                'co2e_kg': our_co2e_kg,
                'method': 'ZeroCarb (TEADS + CCF)',
                'source': 'Real-time grid data'
            },
            'climatiq_calculation': {
                'co2e_kg': climatiq_co2e_kg,
                'method': climatiq_result.get('co2e_calculation_method'),
                'source': climatiq_result.get('emission_factor', {}).get('source')
            },
            'difference_kg': difference_kg,
            'difference_percent': round(difference_percent, 2),
            'recommendation': recommendation,
            'notices': climatiq_result.get('notices', [])
        }
    
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return {
            'error': str(e),
            'recommendation': 'use_ours'  # Fallback to our calculation
        }


def calculate_scope3_procurement(
    cloud_spend_usd: float,
    year: int = None,
    region: str = 'US'
) -> Dict:
    """
    Calculate Scope 3.1 emissions from cloud spending
    
    Args:
        cloud_spend_usd: Monthly or annual cloud spending
        year: Year of spending
        region: Spending region
    
    Returns:
        {
            'scope3_emissions_kg': float,
            'calculation_method': str,
            'source': str,
            'breakdown': {...}
        }
    """
    try:
        client = ClimatiqClient()
        
        year = year or datetime.now().year
        
        result = client.procurement_spend(
            classification_code='62',  # IT services (NACE2)
            classification_type='nace2',
            spend_year=year,
            spend_region=region,
            money=cloud_spend_usd,
            money_unit='usd'
        )
        
        return {
            'scope3_emissions_kg': result['estimate']['co2e'],
            'calculation_method': result['estimate']['co2e_calculation_method'],
            'source': result['estimate']['emission_factor']['source'],
            'breakdown': result['calculation_details'],
            'notices': result.get('notices', [])
        }
    
    except Exception as e:
        logger.error(f"Scope 3 calculation error: {e}")
        return {
            'error': str(e),
            'scope3_emissions_kg': 0
        }


def ai_estimate(user_query: str, parameters: Dict) -> Dict:
    """
    AI-powered emission calculation
    
    Args:
        user_query: Natural language description
        parameters: Activity parameters
    
    Returns:
        {
            'co2e_kg': float,
            'confidence': 'accept' | 'review',
            'emission_factor': {...},
            'notices': [...]
        }
    """
    try:
        client = ClimatiqClient()
        
        result = client.autopilot_one_shot(
            text=user_query,
            parameters=parameters,
            region_fallback=True
        )
        
        return {
            'co2e_kg': result.get('co2e', 0),
            'confidence': result.get('suggestion_details', {}).get('label', 'review'),
            'emission_factor': result.get('emission_factor', {}),
            'notices': result.get('notices', []),
            'model_version': result.get('model_version')
        }
    
    except Exception as e:
        logger.error(f"AI estimate error: {e}")
        return {
            'error': str(e),
            'co2e_kg': 0,
            'confidence': 'error'
        }


# ============================================================================
# TESTING
# ============================================================================

if __name__ == '__main__':
    print("=== Climatiq API Client Test ===\n")
    
    client = ClimatiqClient()
    
    # Test 1: Cloud Computing
    print("1. Testing Cloud Computing...")
    try:
        result = client.cloud_compute_instance(
            provider='aws',
            region='eu-west-2',
            instance='t2.micro',
            duration=1,
            duration_unit='hour',
            vcpu_utilization=0.5
        )
        print(f"   ✅ AWS t2.micro (1h): {result['co2e']} kg CO2e")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Procurement
    print("\n2. Testing Procurement (Scope 3.1)...")
    try:
        result = client.procurement_spend(
            classification_code='62',
            classification_type='nace2',
            spend_year=2024,
            spend_region='US',
            money=10000,
            money_unit='usd'
        )
        print(f"   ✅ $10k IT services: {result['estimate']['co2e']} kg CO2e")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Search
    print("\n3. Testing Emission Factor Search...")
    try:
        result = client.search_emission_factors(
            query='electricity UK',
            region='GB',
            results_per_page=3
        )
        print(f"   ✅ Found {result['total_results']} factors")
        for factor in result['results'][:3]:
            print(f"      - {factor['name']}: {factor['factor']} {factor['unit']}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Autopilot
    print("\n4. Testing Autopilot AI...")
    try:
        result = client.autopilot_one_shot(
            text='Running 100 integration tests on AWS',
            parameters={
                'number': 100,
                'time': 30,
                'time_unit': 'min'
            }
        )
        print(f"   ✅ AI estimate: {result['co2e']} kg CO2e")
        print(f"      Confidence: {result.get('suggestion_details', {}).get('label', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n=== Tests Complete ===")
