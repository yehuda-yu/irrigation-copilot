"""
Fetch forecast data script.

Calls data adapter to fetch forecast for given date and prints summary.
Useful for testing data adapters and debugging forecast retrieval.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data import OfflineModeError, get_forecast_points
from app.data.moag_client import MoAGClientError
from app.data.station_matching import (
    InvalidCoordinatesError,
    get_nearest_points,
    haversine_km,
    pick_nearest_point,
)


def main() -> int:
    """
    Fetch and display forecast summary.

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = argparse.ArgumentParser(description="Fetch forecast data from MoAG API")
    parser.add_argument(
        "--date",
        type=str,
        default=datetime.now().date().isoformat(),
        help="Forecast date in YYYY-MM-DD format (default: today)",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Enable offline mode (use cache only, no network fetch)",
    )
    parser.add_argument(
        "--lat",
        type=float,
        default=None,
        help="User latitude (optional, for nearest point selection)",
    )
    parser.add_argument(
        "--lon",
        type=float,
        default=None,
        help="User longitude (optional, for nearest point selection)",
    )
    args = parser.parse_args()

    try:
        mode_str = "offline" if args.offline else "online"
        print(f"Fetching forecast for date: {args.date} (mode: {mode_str})")
        points = get_forecast_points(date_str=args.date, offline_mode=args.offline)

        if not points:
            print("ERROR: No forecast points returned")
            return 1

        # Calculate statistics
        evap_values = [p.evap_mm for p in points]
        min_evap = min(evap_values)
        max_evap = max(evap_values)

        # Print summary
        print("\nForecast Summary:")
        print(f"  Total points: {len(points)}")
        print(f"  Evap range: {min_evap:.2f} - {max_evap:.2f} mm")

        # If lat/lon provided, select nearest point
        if args.lat is not None and args.lon is not None:
            try:
                nearest = pick_nearest_point(args.lat, args.lon, points)
                nearest_distance = haversine_km(args.lat, args.lon, nearest.lat, nearest.lon)

                print(f"\nNearest Point Selection (user location: {args.lat:.4f}, {args.lon:.4f}):")
                print(f"  Name: {nearest.name or 'N/A'}")
                print(f"  Area: {nearest.geographic_area or 'N/A'}")
                print(f"  Location: ({nearest.lat:.4f}, {nearest.lon:.4f})")
                print(f"  Distance: {nearest_distance:.2f} km")
                print(f"  Date: {nearest.date}")
                print(f"  Evap: {nearest.evap_mm:.2f} mm")
                print(f"  Temp: {nearest.temp_min or 'N/A'}°C - {nearest.temp_max or 'N/A'}°C")

                # Show top 3 nearest
                top3 = get_nearest_points(args.lat, args.lon, points, k=3)
                print("\nTop 3 Nearest Points:")
                for i, (point, dist) in enumerate(top3, 1):
                    area_str = point.geographic_area or "N/A"
                    name_str = point.name or "N/A"
                    print(f"  {i}. {name_str} ({area_str}) - {dist:.2f} km")
            except (ValueError, InvalidCoordinatesError) as e:
                if isinstance(e, InvalidCoordinatesError):
                    print(f"WARNING: Nearest point selection failed: {e}", file=sys.stderr)
                    skipped_msg = (
                        f"  Diagnostics: {e.skipped_count}/{e.total_points} points "
                        "skipped due to invalid coordinates"
                    )
                    print(skipped_msg, file=sys.stderr)
                else:
                    print(f"WARNING: Nearest point selection failed: {e}", file=sys.stderr)
        else:
            print("\nSample points (first 3):")
            for i, point in enumerate(points[:3], 1):
                print(f"\n  Point {i}:")
                print(f"    Name: {point.name or 'N/A'}")
                print(f"    Area: {point.geographic_area or 'N/A'}")
                print(f"    Location: ({point.lat:.4f}, {point.lon:.4f})")
                print(f"    Date: {point.date}")
                print(f"    Evap: {point.evap_mm:.2f} mm")
                print(f"    Temp: {point.temp_min or 'N/A'}°C - {point.temp_max or 'N/A'}°C")

        return 0

    except ValueError as e:
        print(f"ERROR: Invalid input: {e}", file=sys.stderr)
        return 1
    except OfflineModeError as e:
        print(f"ERROR: Offline mode: {e}", file=sys.stderr)
        print(
            "  Hint: Run once online to populate cache, or disable offline mode.",
            file=sys.stderr,
        )
        return 1
    except MoAGClientError as e:
        print(f"ERROR: MoAG API error: {e}", file=sys.stderr)
        if e.status_code:
            print(f"  HTTP Status: {e.status_code}", file=sys.stderr)
        if e.response_snippet:
            print(f"  Response snippet: {e.response_snippet[:200]}...", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
