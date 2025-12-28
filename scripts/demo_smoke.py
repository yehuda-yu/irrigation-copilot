"""
Quick smoke test for the Irrigation Copilot API.

Assumes the API server is running at http://127.0.0.1:8000.
Exits with non-zero code if the request fails.
"""

import sys

try:
    import requests
except ImportError:
    print("ERROR: requests library not found. Install with: uv sync")
    sys.exit(1)

API_URL = "http://127.0.0.1:8000/irrigation/plan"

# Test request: tomato farm, 5 dunam, mid stage
TEST_REQUEST = {
    "lat": 32.0853,
    "lon": 34.7818,
    "mode": "farm",
    "crop_name": "tomato",
    "area_dunam": 5.0,
    "stage": "mid",
}

def main():
    """Run smoke test against deterministic endpoint."""
    # First check if server is running
    try:
        health_check = requests.get("http://127.0.0.1:8000/health", timeout=2)
        if health_check.status_code != 200:
            print("WARNING: Health endpoint returned non-200 status")
    except requests.exceptions.ConnectionError:
        print("ERROR: Server is not running!")
        print("\nTo start the server, run in a separate terminal:")
        print("  uv run uvicorn app.api.main:app --reload")
        print("\nThen run this script again.")
        sys.exit(1)

    # Now test the irrigation endpoint
    try:
        response = requests.post(API_URL, json=TEST_REQUEST, timeout=10)

        if response.status_code != 200:
            print(f"ERROR: API returned status {response.status_code}")
            print(f"Response: {response.text}")
            if response.status_code == 404:
                print("\nTroubleshooting:")
                print("1. Make sure the server is running the latest code")
                print("2. Check that routes are registered: http://127.0.0.1:8000/docs")
                print("3. Try restarting the server")
            sys.exit(1)

        data = response.json()

        # Print key fields
        plan = data.get("plan", {})
        print("[OK] API smoke test passed")
        print(f"  Date used: {data.get('date_used', 'N/A')}")
        print(f"  Evaporation: {data.get('evap_mm_used', 'N/A')} mm")

        if "liters_per_day" in plan:
            print(f"  Irrigation: {plan['liters_per_day']:.1f} L/day")
        elif "ml_per_day" in plan:
            print(f"  Irrigation: {plan['ml_per_day']:.1f} ml/day")

        chosen = data.get("chosen_point", {})
        if chosen:
            name = chosen.get('name', 'N/A')
            dist = chosen.get('distance_km', 'N/A')
            print(f"  Forecast point: {name} ({dist:.1f} km away)")

    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to API server.")
        print(f"Make sure the server is running at {API_URL}")
        print("\nTo start the server, run in a separate terminal:")
        print("  uv run uvicorn app.api.main:app --reload")
        print("\nThen run this script again.")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("ERROR: Request timed out")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

