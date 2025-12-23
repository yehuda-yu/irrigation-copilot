# Data Sources

## MVP: MoAG Farmers Forecast
- Endpoint: TBD (existing adapter pattern)
- Data: Daily evaporation, min/max temps
- Normalization: Parse into ForecastPoint model
- Caching: SQLite cache for daily pulls

## Future: IMS Official Station API
- Endpoint: TBD
- Data: Official ET0, station metadata
- Use case: Higher accuracy, official data

## Data Model
All sources normalize to `ForecastPoint`:
- date, lat, lon, evap_mm, temp_min, temp_max, name, area

