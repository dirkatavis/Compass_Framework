# Vin2Mva

Simple client to look up MVA values from a list of VINs.

## Run

From repo root:

```bash
python clients/vin_to_mva/Vin2Mva.py --input clients/vin_to_mva/vins_sample.csv --config webdriver.ini.local
```

## Options

- `-i, --input` Input CSV file with VIN list (default: `clients/vin_to_mva/vins_sample.csv`)
- `-o, --output` Output CSV file (default: `clients/vin_to_mva/Vin2Mva_results.csv`)
- `-c, --config` INI config file with credentials and app URL (default: `webdriver.ini.local`)
- `--headless` Run browser in headless mode
- `-v, --verbose` Enable verbose logging
- `-t, --timeout` Timeout in seconds for vehicle data display (default: `20`)

## Input format

Single-column CSV with header `VIN`, for example:

```csv
VIN
1GNSCNKD3MR250256
1V2WR2CA4SC525787
```

## Output format

CSV with two columns:

```csv
vin,mva
```

Output file is overwritten on each run.
