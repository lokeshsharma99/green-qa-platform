"""
Green QA Platform - Weather-based Clean Grid Predictor

Uses Open-Meteo API (FREE, NO AUTH) to predict renewable energy generation
and identify optimal low-carbon windows for test scheduling.

Open-Meteo API: https://open-meteo.com/en/docs
- Solar radiation (shortwave_radiation, direct_radiation)
- Wind speed at 10m and 100m (wind_speed_10m, wind_speed_100m)
- Cloud cover (cloudcover)
- 16-day hourly forecasts

Renewable Energy Correlation:
- High solar radiation + low cloud cover = high solar generation
- Wind speed 10-25 m/s = optimal wind generation
- Combined score predicts clean grid periods
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.request import urlopen, Request
from urllib.error import URLError
from dataclasses import dataclass
from enum import Enum

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# ============================================
# AWS Europe Data Center Coordinates
# ============================================

AWS_EUROPE_COORDS = {
    'eu-north-1': {
        'name': 'Stockholm',
        'country': 'SE',
        'lat': 59.3293,
        'lon': 18.0686,
        'renewable_mix': 0.65,  # ~65% renewable (hydro, wind)
        'timezone': 'Europe/Stockholm'
    },
    'eu-west-3': {
        'name': 'Paris',
        'country': 'FR',
        'lat': 48.8566,
        'lon': 2.3522,
        'renewable_mix': 0.25,  # ~25% renewable (nuclear is low-carbon but not renewable)
        'timezone': 'Europe/Paris'
    },
    'eu-west-2': {
        'name': 'London',
        'country': 'GB',
        'lat': 51.5074,
        'lon': -0.1278,
        'renewable_mix': 0.45,  # ~45% renewable (wind growing)
        'timezone': 'Europe/London'
    },
    'eu-west-1': {
        'name': 'Dublin',
        'country': 'IE',
        'lat': 53.3498,
        'lon': -6.2603,
        'renewable_mix': 0.40,  # ~40% renewable (strong wind)
        'timezone': 'Europe/Dublin'
    },
    'eu-central-1': {
        'name': 'Frankfurt',
        'country': 'DE',
        'lat': 50.1109,
        'lon': 8.6821,
        'renewable_mix': 0.50,  # ~50% renewable (solar + wind)
        'timezone': 'Europe/Berlin'
    },
    'eu-south-1': {
        'name': 'Milan',
        'country': 'IT',
        'lat': 45.4642,
        'lon': 9.1900,
        'renewable_mix': 0.40,  # ~40% renewable (hydro + solar)
        'timezone': 'Europe/Rome'
    },
    'eu-south-2': {
        'name': 'Aragon',
        'country': 'ES',
        'lat': 41.6488,
        'lon': -0.8891,
        'renewable_mix': 0.50,  # ~50% renewable (solar + wind)
        'timezone': 'Europe/Madrid'
    },
    'eu-central-2': {
        'name': 'Zurich',
        'country': 'CH',
        'lat': 47.3769,
        'lon': 8.5417,
        'renewable_mix': 0.75,  # ~75% renewable (hydro)
        'timezone': 'Europe/Zurich'
    }
}

# ============================================
# Renewable Energy Thresholds
# ============================================

# Wind speed thresholds (m/s)
WIND_THRESHOLDS = {
    'cut_in': 3.0,      # Minimum for turbines to start
    'optimal_low': 10.0,  # Optimal range start
    'optimal_high': 25.0, # Optimal range end
    'cut_out': 30.0     # Turbines shut down
}

# Solar radiation thresholds (W/m²)
SOLAR_THRESHOLDS = {
    'low': 100,         # Minimal generation
    'moderate': 300,    # Moderate generation
    'high': 600,        # High generation
    'excellent': 800    # Excellent generation
}

# Cloud cover thresholds (%)
CLOUD_THRESHOLDS = {
    'clear': 20,        # Clear sky
    'partly': 50,       # Partly cloudy
    'cloudy': 80        # Overcast
}


# ============================================
# Data Classes
# ============================================

class RenewableScore(Enum):
    """Renewable energy generation score."""
    EXCELLENT = "excellent"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    POOR = "poor"


@dataclass
class WeatherForecast:
    """Hourly weather forecast data."""
    time: str
    temperature: float
    cloud_cover: float
    wind_speed_10m: float
    wind_speed_100m: float  # Hub height for wind turbines
    solar_radiation: float   # W/m²
    direct_radiation: float  # W/m² (direct = better for solar panels)
    is_day: bool


@dataclass
class RenewablePrediction:
    """Predicted renewable energy generation for a time slot."""
    time: str
    solar_score: float       # 0-1 scale
    wind_score: float        # 0-1 scale
    combined_score: float    # 0-1 scale weighted by regional mix
    renewable_level: RenewableScore
    predicted_intensity: float  # Estimated gCO2/kWh
    recommendation: str


# ============================================
# Open-Meteo API Client
# ============================================

class OpenMeteoAPI:
    """
    Open-Meteo Weather API client.
    FREE, NO AUTH REQUIRED.
    https://open-meteo.com/en/docs
    """
    BASE_URL = 'https://api.open-meteo.com/v1/forecast'
    
    @staticmethod
    def get_renewable_forecast(
        lat: float,
        lon: float,
        days: int = 7,
        timezone: str = 'UTC'
    ) -> Optional[List[Dict]]:
        """
        Get weather forecast relevant to renewable energy generation.
        
        Args:
            lat: Latitude
            lon: Longitude
            days: Forecast days (1-16)
            timezone: Timezone for local time
        
        Returns:
            List of hourly forecast data
        """
        params = [
            f"latitude={lat}",
            f"longitude={lon}",
            f"forecast_days={min(days, 16)}",
            f"timezone={timezone}",
            "hourly=temperature_2m,cloudcover,windspeed_10m,windspeed_100m,"
            "shortwave_radiation,direct_radiation,is_day"
        ]
        
        url = f"{OpenMeteoAPI.BASE_URL}?{'&'.join(params)}"
        
        try:
            req = Request(url, headers={'Accept': 'application/json'})
            with urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode())
            
            hourly = data.get('hourly', {})
            times = hourly.get('time', [])
            
            forecasts = []
            for i, time in enumerate(times):
                forecasts.append({
                    'time': time,
                    'temperature': hourly.get('temperature_2m', [None])[i],
                    'cloud_cover': hourly.get('cloudcover', [0])[i] or 0,
                    'wind_speed_10m': hourly.get('windspeed_10m', [0])[i] or 0,
                    'wind_speed_100m': hourly.get('windspeed_100m', [0])[i] or 0,
                    'solar_radiation': hourly.get('shortwave_radiation', [0])[i] or 0,
                    'direct_radiation': hourly.get('direct_radiation', [0])[i] or 0,
                    'is_day': hourly.get('is_day', [0])[i] == 1
                })
            
            logger.info(f"Open-Meteo: Retrieved {len(forecasts)} hours for {lat},{lon}")
            return forecasts
        
        except Exception as e:
            logger.error(f"Open-Meteo API error: {e}")
            return None


# ============================================
# Renewable Energy Scoring
# ============================================

def calculate_solar_score(
    solar_radiation: float,
    cloud_cover: float,
    is_day: bool
) -> float:
    """
    Calculate solar generation score (0-1).
    
    Formula considers:
    - Direct solar radiation (W/m²)
    - Cloud cover reduction
    - Day/night factor
    """
    if not is_day or solar_radiation < 10:
        return 0.0
    
    # Base score from radiation
    if solar_radiation >= SOLAR_THRESHOLDS['excellent']:
        base_score = 1.0
    elif solar_radiation >= SOLAR_THRESHOLDS['high']:
        base_score = 0.8
    elif solar_radiation >= SOLAR_THRESHOLDS['moderate']:
        base_score = 0.5
    elif solar_radiation >= SOLAR_THRESHOLDS['low']:
        base_score = 0.3
    else:
        base_score = 0.1
    
    # Cloud cover penalty (exponential reduction)
    cloud_factor = 1.0 - (cloud_cover / 100) ** 0.8
    
    return round(min(1.0, base_score * cloud_factor), 3)


def calculate_wind_score(
    wind_speed_10m: float,
    wind_speed_100m: float
) -> float:
    """
    Calculate wind generation score (0-1).
    
    Uses wind speed at 100m (typical hub height).
    Optimal range: 10-25 m/s
    """
    # Use 100m wind if available, otherwise 10m with adjustment
    wind = wind_speed_100m if wind_speed_100m > 0 else wind_speed_10m * 1.3
    
    if wind < WIND_THRESHOLDS['cut_in']:
        return 0.0
    elif wind >= WIND_THRESHOLDS['cut_out']:
        return 0.0  # Turbines shut down at high speeds
    elif WIND_THRESHOLDS['optimal_low'] <= wind <= WIND_THRESHOLDS['optimal_high']:
        return 1.0  # Optimal range
    elif wind < WIND_THRESHOLDS['optimal_low']:
        # Linear increase from cut-in to optimal
        return (wind - WIND_THRESHOLDS['cut_in']) / (WIND_THRESHOLDS['optimal_low'] - WIND_THRESHOLDS['cut_in'])
    else:
        # Linear decrease from optimal to cut-out
        return (WIND_THRESHOLDS['cut_out'] - wind) / (WIND_THRESHOLDS['cut_out'] - WIND_THRESHOLDS['optimal_high'])


def calculate_combined_score(
    solar_score: float,
    wind_score: float,
    renewable_mix: float
) -> Tuple[float, RenewableScore]:
    """
    Calculate combined renewable score weighted by regional generation mix.
    
    Args:
        solar_score: Solar generation score (0-1)
        wind_score: Wind generation score (0-1)
        renewable_mix: Regional renewable percentage (0-1)
    
    Returns:
        Tuple of (combined_score, RenewableScore level)
    """
    # Weight: 50/50 for solar/wind (simplified)
    combined = (solar_score * 0.5 + wind_score * 0.5) * renewable_mix
    
    # Determine level
    if combined >= 0.7:
        level = RenewableScore.EXCELLENT
    elif combined >= 0.5:
        level = RenewableScore.HIGH
    elif combined >= 0.3:
        level = RenewableScore.MODERATE
    elif combined >= 0.1:
        level = RenewableScore.LOW
    else:
        level = RenewableScore.POOR
    
    return round(combined, 3), level


def predict_carbon_intensity(
    base_intensity: float,
    combined_score: float
) -> float:
    """
    Predict carbon intensity based on renewable generation.
    
    Higher renewable score = lower carbon intensity.
    
    Formula:
    predicted = base * (1 - (score * reduction_factor))
    """
    max_reduction = 0.5  # Max 50% reduction from base
    reduction = combined_score * max_reduction
    
    return round(base_intensity * (1 - reduction), 1)


# ============================================
# Main Prediction Functions
# ============================================

def get_renewable_predictions(
    region: str,
    days: int = 7
) -> Optional[List[RenewablePrediction]]:
    """
    Get renewable energy predictions for an AWS region.
    
    Args:
        region: AWS region code (e.g., 'eu-west-2')
        days: Forecast days (1-16)
    
    Returns:
        List of hourly predictions
    """
    if region not in AWS_EUROPE_COORDS:
        logger.warning(f"Unknown region: {region}")
        return None
    
    config = AWS_EUROPE_COORDS[region]
    
    # Get weather forecast
    forecast = OpenMeteoAPI.get_renewable_forecast(
        lat=config['lat'],
        lon=config['lon'],
        days=days,
        timezone=config['timezone']
    )
    
    if not forecast:
        return None
    
    # Base intensity for region (gCO2/kWh)
    BASE_INTENSITIES = {
        'eu-north-1': 30,   # Sweden - very low base
        'eu-west-3': 60,    # France - nuclear
        'eu-west-2': 250,   # UK - mixed
        'eu-west-1': 300,   # Ireland - gas + wind
        'eu-central-1': 380, # Germany - coal + renewables
        'eu-south-1': 280,  # Italy - mixed
        'eu-south-2': 200,  # Spain - renewables growing
        'eu-central-2': 50  # Switzerland - hydro
    }
    
    base_intensity = BASE_INTENSITIES.get(region, 300)
    
    predictions = []
    for hour in forecast:
        solar_score = calculate_solar_score(
            hour['solar_radiation'],
            hour['cloud_cover'],
            hour['is_day']
        )
        
        wind_score = calculate_wind_score(
            hour['wind_speed_10m'],
            hour['wind_speed_100m']
        )
        
        combined, level = calculate_combined_score(
            solar_score,
            wind_score,
            config['renewable_mix']
        )
        
        predicted_intensity = predict_carbon_intensity(base_intensity, combined)
        
        # Generate recommendation
        if level == RenewableScore.EXCELLENT:
            rec = "🟢 Excellent - Run now!"
        elif level == RenewableScore.HIGH:
            rec = "🟢 High renewables - Good time"
        elif level == RenewableScore.MODERATE:
            rec = "🟡 Moderate - Acceptable"
        elif level == RenewableScore.LOW:
            rec = "🟠 Low renewables - Consider deferring"
        else:
            rec = "🔴 Poor - Defer if possible"
        
        predictions.append(RenewablePrediction(
            time=hour['time'],
            solar_score=solar_score,
            wind_score=wind_score,
            combined_score=combined,
            renewable_level=level,
            predicted_intensity=predicted_intensity,
            recommendation=rec
        ))
    
    return predictions


def find_optimal_windows(
    predictions: List[RenewablePrediction],
    window_hours: int = 2,
    max_results: int = 5
) -> List[Dict]:
    """
    Find optimal execution windows based on renewable predictions.
    
    Args:
        predictions: List of hourly predictions
        window_hours: Required contiguous hours
        max_results: Maximum windows to return
    
    Returns:
        List of optimal windows sorted by combined score
    """
    windows = []
    
    for i in range(len(predictions) - window_hours + 1):
        window = predictions[i:i + window_hours]
        
        avg_score = sum(p.combined_score for p in window) / len(window)
        avg_intensity = sum(p.predicted_intensity for p in window) / len(window)
        min_level = min(p.renewable_level.value for p in window)
        
        windows.append({
            'start_time': window[0].time,
            'end_time': window[-1].time,
            'avg_combined_score': round(avg_score, 3),
            'avg_predicted_intensity': round(avg_intensity, 1),
            'min_level': min_level,
            'hours': window_hours
        })
    
    # Sort by highest score
    windows.sort(key=lambda w: w['avg_combined_score'], reverse=True)
    
    return windows[:max_results]


def get_best_scheduling_recommendation(
    region: str,
    duration_hours: int = 2,
    max_defer_days: int = 3
) -> Dict:
    """
    Get the best scheduling recommendation for a workload.
    
    Args:
        region: AWS region
        duration_hours: Required execution duration
        max_defer_days: Maximum days to look ahead
    
    Returns:
        Recommendation with optimal windows
    """
    predictions = get_renewable_predictions(region, days=max_defer_days)
    
    if not predictions:
        return {
            'error': 'Could not get weather forecast',
            'fallback': 'Run immediately'
        }
    
    optimal_windows = find_optimal_windows(
        predictions,
        window_hours=duration_hours,
        max_results=5
    )
    
    # Current conditions
    current = predictions[0] if predictions else None
    
    # Best window
    best = optimal_windows[0] if optimal_windows else None
    
    # Determine overall recommendation
    if current and current.renewable_level in [RenewableScore.EXCELLENT, RenewableScore.HIGH]:
        recommendation = "RUN_NOW"
        reason = f"Current conditions are {current.renewable_level.value}"
    elif best and best['avg_combined_score'] > 0.5:
        recommendation = "DEFER"
        reason = f"Better window at {best['start_time']} (score: {best['avg_combined_score']})"
    else:
        recommendation = "RUN_NOW"
        reason = "No significantly better window found"
    
    return {
        'region': region,
        'recommendation': recommendation,
        'reason': reason,
        'current_conditions': {
            'time': current.time if current else None,
            'renewable_level': current.renewable_level.value if current else None,
            'predicted_intensity': current.predicted_intensity if current else None,
            'solar_score': current.solar_score if current else None,
            'wind_score': current.wind_score if current else None
        },
        'optimal_windows': optimal_windows,
        'forecast_days': max_defer_days,
        'generated_at': datetime.utcnow().isoformat()
    }


# ============================================
# Lambda Handler
# ============================================

def lambda_handler(event: Dict, context) -> Dict:
    """
    Lambda handler for weather-based predictions.
    
    Actions:
        - get_forecast: Get renewable predictions for a region
        - find_windows: Find optimal execution windows
        - recommend: Get scheduling recommendation
    """
    action = event.get('action', 'recommend')
    region = event.get('region', 'eu-west-2')
    
    try:
        if action == 'get_forecast':
            days = event.get('days', 3)
            predictions = get_renewable_predictions(region, days)
            
            if not predictions:
                return {'statusCode': 500, 'body': json.dumps({'error': 'Failed to get forecast'})}
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'region': region,
                    'predictions': [
                        {
                            'time': p.time,
                            'solar_score': p.solar_score,
                            'wind_score': p.wind_score,
                            'combined_score': p.combined_score,
                            'level': p.renewable_level.value,
                            'predicted_intensity': p.predicted_intensity,
                            'recommendation': p.recommendation
                        }
                        for p in predictions
                    ]
                })
            }
        
        elif action == 'find_windows':
            days = event.get('days', 3)
            duration = event.get('duration_hours', 2)
            
            predictions = get_renewable_predictions(region, days)
            if not predictions:
                return {'statusCode': 500, 'body': json.dumps({'error': 'Failed to get forecast'})}
            
            windows = find_optimal_windows(predictions, duration)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'region': region,
                    'duration_hours': duration,
                    'optimal_windows': windows
                })
            }
        
        elif action == 'recommend':
            duration = event.get('duration_hours', 2)
            max_days = event.get('max_defer_days', 3)
            
            recommendation = get_best_scheduling_recommendation(
                region, duration, max_days
            )
            
            return {
                'statusCode': 200,
                'body': json.dumps(recommendation)
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


# ============================================
# Local Testing
# ============================================

if __name__ == '__main__':
    print("=== Weather-based Clean Grid Predictor ===\n")
    
    # Test for London (eu-west-2)
    print("1. Testing Open-Meteo API for London...")
    forecast = OpenMeteoAPI.get_renewable_forecast(51.5074, -0.1278, days=2)
    if forecast:
        print(f"   Received {len(forecast)} hours of forecast")
        print(f"   First hour: {forecast[0]}")
    
    # Test predictions
    print("\n2. Testing renewable predictions for eu-west-2...")
    predictions = get_renewable_predictions('eu-west-2', days=2)
    if predictions:
        print(f"   Generated {len(predictions)} predictions")
        for p in predictions[:6]:
            print(f"   {p.time}: Solar={p.solar_score:.2f}, Wind={p.wind_score:.2f}, "
                  f"Combined={p.combined_score:.2f}, Level={p.renewable_level.value}")
    
    # Test optimal windows
    print("\n3. Finding optimal windows...")
    if predictions:
        windows = find_optimal_windows(predictions, window_hours=2)
        for i, w in enumerate(windows[:3], 1):
            print(f"   #{i}: {w['start_time']} to {w['end_time']} "
                  f"(score: {w['avg_combined_score']}, intensity: {w['avg_predicted_intensity']})")
    
    # Test recommendation
    print("\n4. Getting scheduling recommendation...")
    rec = get_best_scheduling_recommendation('eu-west-2', duration_hours=2)
    print(f"   Recommendation: {rec['recommendation']}")
    print(f"   Reason: {rec['reason']}")
    
    print("\n=== Tests Complete ===")
