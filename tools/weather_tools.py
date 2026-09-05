"""
Weather Tool for Project Anima.

Provides schema definition and execution handler for the get_weather tool,
which fetches real-time weather information for a specified location.
"""

import logging
from typing import Any, Dict, List
import requests

logger = logging.getLogger("anima.tools.weather")

GET_WEATHER_SCHEMA: Dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": (
            "Fetch real-time weather information for a specific location. "
            "Use this tool when the user asks about weather, temperature, or climate conditions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City or location name (e.g., 'Jakarta', 'Surabaya', 'Tokyo').",
                }
            },
            "required": ["location"],
        },
    },
}

WEATHER_TOOLS: List[Dict[str, Any]] = [GET_WEATHER_SCHEMA]

DEFAULT_TIMEOUT: int = 10


def execute_get_weather(location: str) -> str:
    """
    Fetch current weather condition, temperature, and humidity for a given location using wttr.in.

    Args:
        location (str): Name of the city or location.

    Returns:
        str: Formatted weather status string or an error message.
    """
    if not location or not isinstance(location, str):
        logger.warning("Invalid or empty location provided to get_weather.")
        return "Error: Location must be a valid non-empty string."

    clean_location = location.strip()
    url = f"https://wttr.in/{clean_location}?format=j1"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        logger.info(f"Fetching weather information for location: {clean_location}")
        response = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()

        data = response.json()
        current_condition = data["current_condition"][0]

        temp_c = current_condition.get("temp_C", "N/A")
        feels_like_c = current_condition.get("FeelsLikeC", "N/A")
        weather_desc = current_condition.get("weatherDesc", [{}])[0].get("value", "Unknown")
        humidity = current_condition.get("humidity", "N/A")
        wind_speed_kmh = current_condition.get("windspeedKmph", "N/A")

        result = (
            f"Weather in {clean_location.title()}:\n"
            f"- Condition: {weather_desc}\n"
            f"- Temperature: {temp_c}°C (Feels like: {feels_like_c}°C)\n"
            f"- Humidity: {humidity}%\n"
            f"- Wind Speed: {wind_speed_kmh} km/h"
        )

        logger.info(f"Successfully retrieved weather data for {clean_location}.")
        return result

    except requests.exceptions.Timeout:
        logger.error(f"Timeout occurred while fetching weather for {clean_location}")
        return f"Error: Request timed out while trying to fetch weather for {clean_location}."
    except requests.exceptions.RequestException as exc:
        logger.error(f"HTTP request error fetching weather for {clean_location}: {exc}")
        return f"Error: Unable to retrieve weather data for {clean_location}."
    except (KeyError, IndexError, ValueError) as exc:
        logger.error(f"Error parsing weather JSON payload for {clean_location}: {exc}")
        return f"Error: Failed to parse weather data for {clean_location}."
    except Exception as exc:
        logger.error(f"Unexpected error in get_weather for {clean_location}: {exc}")
        return f"Error: An unexpected error occurred while fetching weather info."