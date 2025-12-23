"""
Fetch forecast data script.

Calls data adapter to fetch forecast for given location and prints summary.
Useful for testing data adapters and debugging forecast retrieval.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data.moag_client import MoAGClient
from app.data.moag_parser import parse_forecast_response


def main():
    """Fetch and display forecast summary."""
    # TODO: Parse command-line arguments (lat, lon)
    # TODO: Initialize MoAG client
    # TODO: Fetch forecast
    # TODO: Parse response
    # TODO: Print summary
    print("Forecast fetch script - TODO: Implement")


if __name__ == "__main__":
    main()

