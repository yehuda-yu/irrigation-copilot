"""
MoAG (Ministry of Agriculture) forecast API client.

Fetches daily evaporation and temperature forecasts from MoAG farmers forecast endpoint.
Handles HTTP requests, timeouts, and retries.
"""


class MoAGClient:
    """
    Client for MoAG forecast API.
    
    Handles authentication, request formatting, and error handling.
    """

    def __init__(self, base_url: str | None = None, timeout: int = 30):
        """
        Initialize MoAG client.
        
        Args:
            base_url: API base URL (optional, uses default if not provided)
            timeout: Request timeout in seconds
        """
        # TODO: Implement client initialization
        pass

    def fetch_forecast(self, lat: float, lon: float) -> dict:
        """
        Fetch forecast data for given coordinates.
        
        Args:
            lat: Latitude
            lon: Longitude
        
        Returns:
            Raw API response dictionary
        
        Raises:
            RequestException: On network or API errors
        """
        # TODO: Implement API request with retries/timeouts
        pass

