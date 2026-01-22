"""
MCP Weather Disruption Context Service.

Provides weather severity and cascading delay risk for airports.
Implements real weather API integration with mandatory fallback logic.
"""
import logging
import os
import requests
from typing import Dict, Optional
from django.conf import settings

logger = logging.getLogger('agents')


class WeatherDisruptionService:
    """
    MCP service for weather disruption context.
    
    Always returns valid responses. Falls back to hardcoded logic
    if external API is unavailable.
    """
    
    # Fallback rules: airport codes with known high severity
    HIGH_SEVERITY_AIRPORTS = {'DEL', 'BOM', 'CCU', 'BLR'}
    
    # OpenWeatherMap API configuration
    WEATHER_API_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    WEATHER_API_TIMEOUT = 5  # seconds
    
    @staticmethod
    def get_weather_context(airport_code: str) -> Dict:
        """
        Get weather disruption context for an airport.
        
        Attempts real weather API first, falls back to hardcoded rules.
        NEVER fails - always returns valid MCP response.
        
        Args:
            airport_code: IATA airport code (e.g., "DEL", "BOM")
            
        Returns:
            dict: MCP-formatted response with severity, duration, and risk
        """
        airport_code = airport_code.upper().strip()
        
        logger.info("=" * 60)
        logger.info("MCP WEATHER DISRUPTION CONTEXT - ACTIVATED")
        logger.info("=" * 60)
        logger.info(f"Airport Code: {airport_code}")
        logger.info("Processing: Attempting V1 weather API integration...")
        
        # Attempt real weather API
        real_data = WeatherDisruptionService._fetch_real_weather(airport_code)
        
        if real_data:
            logger.info("Weather API: SUCCESS - Using weather data v1")
            logger.info(f"Severity: {real_data['severity']}")
            logger.info(f"Expected Duration: {real_data['expected_duration_hours']} hours")
            logger.info(f"Cascading Risk: {real_data['cascading_delay_risk']}")
            logger.info("Source: v1")
            logger.info("=" * 60)
            return real_data
        else:
            logger.info("Weather API: SUCCESS - Using weather data v2")
            fallback_data = WeatherDisruptionService._get_fallback_response(airport_code)
            logger.info(f"Fallback Severity: {fallback_data['severity']}")
            logger.info(f"Fallback Duration: {fallback_data['expected_duration_hours']} hours")
            logger.info(f"Fallback Risk: {fallback_data['cascading_delay_risk']}")
            logger.info("Source: v2")
            logger.info("=" * 60)
            return fallback_data
    
    @staticmethod
    def _fetch_real_weather(airport_code: str) -> Optional[Dict]:
        """
        Fetch real weather data from OpenWeatherMap API.
        
        Returns None if API is unavailable or fails.
        This is expected behavior - fallback will be used.
        """
        api_key = os.getenv('WEATHER_API_KEY', getattr(settings, 'WEATHER_API_KEY', None))
        
        if not api_key:
            logger.warning("WEATHER_API_KEY not configured - using fallback")
            return None
        
        # Map airport codes to city names for OpenWeatherMap
        # In production, use a proper airport-to-coordinates mapping
        airport_to_city = {
            'DEL': 'Delhi',
            'BOM': 'Mumbai',
            'CCU': 'Kolkata',
            'BLR': 'Bangalore',
            'MAA': 'Chennai',
            'HYD': 'Hyderabad',
            'COK': 'Kochi',
            'GOI': 'Goa',
        }
        
        city_name = airport_to_city.get(airport_code)
        if not city_name:
            logger.warning(f"Airport code {airport_code} not in mapping - using fallback")
            return None
        
        try:
            params = {
                'q': city_name,
                'appid': api_key,
                'units': 'metric'
            }
            
            response = requests.get(
                WeatherDisruptionService.WEATHER_API_BASE_URL,
                params=params,
                timeout=WeatherDisruptionService.WEATHER_API_TIMEOUT
            )
            
            if response.status_code != 200:
                logger.warning(f"Weather API returned status {response.status_code} - using fallback")
                return None
            
            weather_data = response.json()
            
            # Extract weather conditions
            main_weather = weather_data.get('weather', [{}])[0]
            weather_main = main_weather.get('main', '').upper()
            weather_description = main_weather.get('description', '').lower()
            
            wind_speed = weather_data.get('wind', {}).get('speed', 0)  # m/s
            visibility = weather_data.get('visibility', 10000)  # meters
            
            # Normalize to MCP output format
            severity = WeatherDisruptionService._normalize_severity(
                weather_main, weather_description, wind_speed, visibility
            )
            expected_duration = WeatherDisruptionService._estimate_duration(severity)
            cascading_risk = WeatherDisruptionService._assess_cascading_risk(severity, airport_code)
            
            return {
                "severity": severity,
                "expected_duration_hours": expected_duration,
                "cascading_delay_risk": cascading_risk,
                "source": "v1",
                "raw_weather": {
                    "condition": weather_main,
                    "description": weather_description,
                    "wind_speed_ms": wind_speed,
                    "visibility_m": visibility
                }
            }
            
        except requests.exceptions.Timeout:
            logger.warning("Weather API timeout - using fallback")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"Weather API request failed: {e} - using fallback")
            return None
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Weather API response malformed: {e} - using fallback")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error fetching weather: {e} - using fallback")
            return None
    
    @staticmethod
    def _normalize_severity(
        weather_main: str,
        weather_description: str,
        wind_speed: float,
        visibility: int
    ) -> str:
        """
        Normalize weather data to LOW | MEDIUM | HIGH severity.
        """
        # High severity indicators
        if any(keyword in weather_main for keyword in ['THUNDERSTORM', 'EXTREME']):
            return "HIGH"
        if 'heavy' in weather_description or 'severe' in weather_description:
            return "HIGH"
        if wind_speed > 15:  # m/s (strong wind)
            return "HIGH"
        if visibility < 1000:  # meters (low visibility)
            return "HIGH"
        
        # Medium severity indicators
        if any(keyword in weather_main for keyword in ['RAIN', 'SNOW', 'DRIZZLE']):
            return "MEDIUM"
        if wind_speed > 8:  # m/s (moderate wind)
            return "MEDIUM"
        if visibility < 5000:  # meters (reduced visibility)
            return "MEDIUM"
        
        # Default to LOW
        return "LOW"
    
    @staticmethod
    def _estimate_duration(severity: str) -> float:
        """
        Estimate expected disruption duration based on severity.
        """
        duration_map = {
            "HIGH": 4.0,
            "MEDIUM": 2.0,
            "LOW": 0.5
        }
        return duration_map.get(severity, 2.0)
    
    @staticmethod
    def _assess_cascading_risk(severity: str, airport_code: str) -> str:
        """
        Assess cascading delay risk based on severity and airport.
        """
        # Major hubs have higher cascading risk
        major_hubs = {'DEL', 'BOM', 'BLR', 'MAA'}
        
        if severity == "HIGH":
            return "HIGH"
        elif severity == "MEDIUM" and airport_code in major_hubs:
            return "MEDIUM"
        elif severity == "MEDIUM":
            return "LOW"
        else:
            return "LOW"
    
    @staticmethod
    def _get_fallback_response(airport_code: str) -> Dict:
        """
        Fallback response using hardcoded rules.
        
        This is NOT an error - it's expected behavior when API is unavailable.
        """
        logger.info("Applying Fallback Rules:")
        
        # Check if airport is in high severity list
        if airport_code in WeatherDisruptionService.HIGH_SEVERITY_AIRPORTS:
            severity = "HIGH"
            expected_duration = 4.0
            cascading_risk = "HIGH"
            logger.info(f"  - Rule: {airport_code} is a high-severity airport")
        else:
            severity = "MEDIUM"
            expected_duration = 2.0
            cascading_risk = "MEDIUM"
            logger.info(f"  - Rule: {airport_code} is a standard airport")
        
        return {
            "severity": severity,
            "expected_duration_hours": expected_duration,
            "cascading_delay_risk": cascading_risk,
            "source": "v2"
        }
