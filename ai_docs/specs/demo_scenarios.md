# Demo Scenarios

Quick, reliable demo scenarios for the Irrigation Copilot API. All scenarios use fixed coordinates in Israel (Tel Aviv area).

## Scenario A: Farm Mode (Tomato, 5 Dunam)

**Description:** Compute irrigation plan for a 5 dunam tomato farm at mid-stage growth.

**PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/irrigation/plan" -Method POST -ContentType "application/json" -Body '{"lat": 32.0853, "lon": 34.7818, "mode": "farm", "crop_name": "tomato", "area_dunam": 5.0, "stage": "mid"}'
```

**curl:**
```bash
curl -X POST http://127.0.0.1:8000/irrigation/plan -H "Content-Type: application/json" -d '{"lat": 32.0853, "lon": 34.7818, "mode": "farm", "crop_name": "tomato", "area_dunam": 5.0, "stage": "mid"}'
```

**Expected:** Returns plan with `liters_per_day` (typically 2000-4000L), chosen forecast point, and diagnostics.

---

## Scenario B: Plant Mode (Herbs, 20cm Pot)

**Description:** Compute irrigation plan for herbs in a 20cm diameter pot.

**PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/irrigation/plan" -Method POST -ContentType "application/json" -Body '{"lat": 32.0853, "lon": 34.7818, "mode": "plant", "plant_profile": "herbs", "pot_diameter_cm": 20}'
```

**curl:**
```bash
curl -X POST http://127.0.0.1:8000/irrigation/plan -H "Content-Type: application/json" -d '{"lat": 32.0853, "lon": 34.7818, "mode": "plant", "plant_profile": "herbs", "pot_diameter_cm": 20}'
```

**Expected:** Returns plan with `ml_per_day` (typically 200-600ml), chosen forecast point, and diagnostics.

---

## Scenario C: Error Handling (Offline Cache Miss)

**Description:** Demonstrate error response when offline mode is enabled but no cached data exists.

**PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/irrigation/plan" -Method POST -ContentType "application/json" -Body '{"lat": 32.0853, "lon": 34.7818, "mode": "farm", "crop_name": "tomato", "area_dunam": 5.0, "offline": true}'
```

**curl:**
```bash
curl -X POST http://127.0.0.1:8000/irrigation/plan -H "Content-Type: application/json" -d '{"lat": 32.0853, "lon": 34.7818, "mode": "farm", "crop_name": "tomato", "area_dunam": 5.0, "offline": true}'
```

**Expected:** Returns HTTP 503 with error JSON:
```json
{
  "error": {
    "code": "OFFLINE_CACHE_MISS",
    "message": "No cached forecast data available for the requested date",
    "details": {}
  }
}
```

---

## Alternative Error: Unknown Crop

**Description:** Demonstrate validation error for unknown crop name.

**PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/irrigation/plan" -Method POST -ContentType "application/json" -Body '{"lat": 32.0853, "lon": 34.7818, "mode": "farm", "crop_name": "unknown_crop", "area_dunam": 5.0}'
```

**Expected:** Returns HTTP 400 with error JSON:
```json
{
  "error": {
    "code": "UNKNOWN_CROP",
    "message": "Unknown crop: unknown_crop",
    "details": {}
  }
}
```

