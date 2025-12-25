# Irrigation Coefficients Data

This directory contains FAO-56 stage-based crop coefficient (Kc) data files.

## File Format

Each crop has a JSON file with:
- `crop_name`: Standard crop identifier
- `coefficients`: Stage-based Kc values (initial, mid, end)
- `metadata`: Source information (FAO-56) and notes

## Coefficient Structure

```json
{
  "crop_name": "tomato",
  "coefficients": {
    "type": "stage",
    "basis": "ET0 Penman-Monteith",
    "kc_initial": 0.6,
    "kc_mid": 1.15,
    "kc_end": 0.9
  },
  "metadata": {
    "source": {
      "title": "FAO-56 Table 12",
      "url": "https://www.fao.org/4/x0490e/x0490e0b.htm",
      "table": "Table 12"
    }
  }
}
```

## Source

All coefficients are from **FAO-56 Irrigation and Drainage Paper No. 56, Chapter 6, Table 12**:
- Basis: ET0 Penman-Monteith reference evapotranspiration
- Format: Stage-based (initial, mid-season, end-season)
- URL: https://www.fao.org/4/x0490e/x0490e0b.htm

## Adding New Crops

1. Create a JSON file following the format above
2. Use FAO-56 Table 12 values
3. Document source in metadata
