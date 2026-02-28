# MVA Closeout Client

Sets vehicle status to Closed for a batch of MVAs from CSV.

## Self-Contained Structure

This client follows the same structure as other clients:
- ✅ Script: `MvaCloseoutClient.py`
- ✅ Sample Data: `mva_closeout_sample.csv`
- ✅ Config (optional): `webdriver.ini.local`
- ✅ Output: `MvaCloseout_results.csv`
- ✅ Logs: `mva_closeout.log`

## Usage

```powershell
cd clients/mva_closeout
python MvaCloseoutClient.py
```

### Options

```powershell
python MvaCloseoutClient.py --input my_mvas.csv --output my_results.csv --config ../../webdriver.ini.local --headless --verbose
```

### Target a Specific Work Item Type

```powershell
python MvaCloseoutClient.py --workitem-type Glass
```

### Slow Down Step Execution

```powershell
python MvaCloseoutClient.py --step-delay 2.0
```

You can also set `COMPASS_STEP_DELAY` or `timeouts.step_delay` in `webdriver.ini.local`.

## Input CSV Format

One MVA per line (same format as vehicle lookup):

```csv
mva
50227203
12345678
98765432
```

## Output CSV Format

```csv
mva,status_update_result,error
50227203,success,
12345678,failed,Status update failed
```

## Config Resolution

The client loads config in this order:
1. `./webdriver.ini.local`
2. `../../webdriver.ini.local`
