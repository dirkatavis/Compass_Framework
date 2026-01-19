"""
Glass Data Lookup - Compass Framework Client Script

Query Compass for VIN and Description for a list of MVAs.
Refactored from tightly-coupled GlassDataParser.py to use
protocol-first Compass Framework patterns.

Usage:
    python scripts/glass_data_lookup.py --input data/mva_list.csv --output results.csv
    python scripts/glass_data_lookup.py --mva 50227203 --output single_result.csv
    python scripts/glass_data_lookup.py --config my_config.ini

Expected failures (TDD):
    - ImportError: LoginFlow not found
    - ImportError: VehicleLookupFlow not found
    - ImportError: CSV utilities not found
    - AttributeError: Configuration missing credential methods
"""
import argparse
import sys
import os

# Add project root to path for imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Compass Framework imports (some will fail initially - this is expected!)
from compass_core import (
    StandardDriverManager,
    SeleniumNavigator,
    SeleniumVehicleDataActions,
    StandardLogger,
    IniConfiguration,
)

# These imports will FAIL initially - revealing gaps to implement
try:
    from compass_core import LoginFlow, SeleniumLoginFlow
    LOGIN_AVAILABLE = True
except ImportError as e:
    print(f"WARNING: LoginFlow not available: {e}")
    LOGIN_AVAILABLE = False

try:
    from compass_core import VehicleLookupFlow
    WORKFLOW_AVAILABLE = True
except ImportError as e:
    print(f"WARNING: VehicleLookupFlow not available: {e}")
    WORKFLOW_AVAILABLE = False

try:
    from compass_core import read_mva_list, write_results_csv
    CSV_UTILS_AVAILABLE = True
except ImportError as e:
    print(f"WARNING: CSV utilities not available: {e}")
    CSV_UTILS_AVAILABLE = False


def manual_implementation(args):
    """
    Fallback: Manual implementation showing step-by-step usage
    of available protocols. This demonstrates the target workflow
    that VehicleLookupFlow should automate.
    """
    logger = StandardLogger("glass_data_lookup")
    logger.info("=" * 60)
    logger.info("Glass Data Lookup - Manual Mode (Workflow not available)")
    logger.info("=" * 60)
    
    # Load configuration
    config = IniConfiguration()
    config_file = args.config or "webdriver.ini.local"
    
    try:
        config.load(config_file)
        logger.info(f"Loaded configuration from: {config_file}")
    except Exception as e:
        logger.warning(f"Could not load config file: {e}")
    
    # Get credentials (will fail if config doesn't support them)
    try:
        username = config.get('credentials.username') or os.getenv('COMPASS_USERNAME')
        password = config.get('credentials.password') or os.getenv('COMPASS_PASSWORD')
        login_id = config.get('credentials.login_id') or os.getenv('COMPASS_LOGIN_ID')
    except Exception as e:
        logger.error(f"❌ Credentials not configured: {e}")
        logger.info("Expected: credentials.username, credentials.password, credentials.login_id in INI")
        logger.info("Or set: COMPASS_USERNAME, COMPASS_PASSWORD, COMPASS_LOGIN_ID env vars")
        return 1
    
    if not all([username, password, login_id]):
        logger.error("❌ Missing credentials (username/password/login_id)")
        return 1
    
    # Initialize driver and protocols
    driver_manager = StandardDriverManager()
    driver = driver_manager.get_or_create_driver(
        incognito=args.incognito,
        headless=args.headless
    )
    logger.info(f"✓ Driver initialized (incognito={args.incognito}, headless={args.headless})")
    
    navigator = SeleniumNavigator(driver, logger)
    vehicle_actions = SeleniumVehicleDataActions(driver, logger)
    
    # STEP 1: Login (manual - LoginFlow not available)
    logger.info("=" * 60)
    logger.info("STEP 1: Login to Compass")
    logger.info("=" * 60)
    
    try:
        # Navigate to login URL
        login_url = config.get('app.login_url', 'https://login.microsoftonline.com/')
        navigator.navigate_to(login_url, verify=False)
        logger.info(f"✓ Navigated to: {login_url}")
        
        # TODO: Implement login steps here
        # This shows what SeleniumLoginFlow should automate
        logger.warning("⚠️  Manual login required - LoginFlow not implemented")
        logger.info("Expected: SeleniumLoginFlow would handle SSO automation")
        
        # For now, pause for manual login
        input("\nPlease login manually, then press ENTER to continue...")
        
    except Exception as e:
        logger.error(f"❌ Login failed: {e}")
        driver_manager.quit_driver()
        return 1
    
    # STEP 2: Read MVA list
    logger.info("=" * 60)
    logger.info("STEP 2: Read MVA list")
    logger.info("=" * 60)
    
    if args.mva:
        # Single MVA from command line
        mva_list = [args.mva]
        logger.info(f"✓ Single MVA: {args.mva}")
    else:
        # Read from CSV (manual - CSV utils not available)
        if not CSV_UTILS_AVAILABLE:
            logger.error("❌ CSV utilities not available - cannot read input file")
            logger.info("Expected: compass_core.read_mva_list() function")
            driver_manager.quit_driver()
            return 1
        
        try:
            mva_list = read_mva_list(args.input)
            logger.info(f"✓ Read {len(mva_list)} MVAs from: {args.input}")
        except Exception as e:
            logger.error(f"❌ Failed to read MVA list: {e}")
            driver_manager.quit_driver()
            return 1
    
    # STEP 3: Process MVAs
    logger.info("=" * 60)
    logger.info(f"STEP 3: Process {len(mva_list)} MVAs")
    logger.info("=" * 60)
    
    results = []
    
    for idx, mva in enumerate(mva_list, 1):
        logger.info(f"[{idx}/{len(mva_list)}] Processing MVA: {mva}")
        
        try:
            # Enter MVA
            enter_result = vehicle_actions.enter_mva(mva, timeout=10)
            if enter_result.get("status") != "success":
                logger.warning(f"  ⚠️  Failed to enter MVA: {enter_result.get('error')}")
                results.append({"mva": mva, "vin": "N/A", "desc": "N/A", "error": enter_result.get('error')})
                continue
            
            # Verify echo
            echo_result = vehicle_actions.verify_mva_echo(mva, timeout=5)
            if echo_result.get("status") != "success":
                logger.warning(f"  ⚠️  MVA echo verification failed: {echo_result.get('error')}")
            
            # Get VIN
            vin_result = vehicle_actions.wait_for_property_loaded("VIN", timeout=12)
            vin = vin_result.get("value", "N/A") if vin_result.get("status") == "success" else "N/A"
            
            # Get Desc
            desc_result = vehicle_actions.wait_for_property_loaded("Desc", timeout=12)
            desc = desc_result.get("value", "N/A") if desc_result.get("status") == "success" else "N/A"
            
            logger.info(f"  ✓ VIN: {vin}, Desc: {desc}")
            results.append({"mva": mva, "vin": vin, "desc": desc, "error": None})
            
        except Exception as e:
            logger.error(f"  ❌ Error processing MVA {mva}: {e}")
            results.append({"mva": mva, "vin": "N/A", "desc": "N/A", "error": str(e)})
    
    # STEP 4: Write results
    logger.info("=" * 60)
    logger.info("STEP 4: Write results")
    logger.info("=" * 60)
    
    output_path = os.path.abspath(args.output)
    
    if CSV_UTILS_AVAILABLE:
        try:
            write_results_csv(results, output_path)
            logger.info(f"✓ Results written to: {output_path}")
        except Exception as e:
            logger.error(f"❌ Failed to write results: {e}")
    else:
        # Manual CSV writing
        import csv
        try:
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["mva", "vin", "desc", "error"])
                writer.writeheader()
                writer.writerows(results)
            logger.info(f"✓ Results written to: {output_path}")
        except Exception as e:
            logger.error(f"❌ Failed to write results: {e}")
    
    # Cleanup
    driver_manager.quit_driver()
    logger.info("=" * 60)
    logger.info("✓ Glass Data Lookup completed")
    logger.info("=" * 60)
    
    return 0


def workflow_implementation(args):
    """
    Ideal implementation using VehicleLookupFlow workflow.
    This shows the target API - simple, protocol-first, clean.
    
    This will FAIL initially - that's the point (TDD)!
    """
    logger = StandardLogger("glass_data_lookup")
    logger.info("=" * 60)
    logger.info("Glass Data Lookup - Workflow Mode")
    logger.info("=" * 60)
    
    # Load configuration
    config = IniConfiguration()
    config_file = args.config or "webdriver.ini.local"
    
    try:
        config.load(config_file)
        logger.info(f"Loaded configuration from: {config_file}")
    except Exception as e:
        logger.warning(f"Could not load config file: {e}")
    
    # Initialize workflow
    workflow = VehicleLookupFlow()
    
    # Prepare workflow parameters
    params = {
        "input_file": args.input if not args.mva else None,
        "mva_list": [args.mva] if args.mva else None,
        "output_file": args.output,
        "username": config.get('credentials.username') or os.getenv('COMPASS_USERNAME'),
        "password": config.get('credentials.password') or os.getenv('COMPASS_PASSWORD'),
        "login_id": config.get('credentials.login_id') or os.getenv('COMPASS_LOGIN_ID'),
        "login_url": config.get('app.login_url', 'https://login.microsoftonline.com/'),
        "incognito": args.incognito,
        "headless": args.headless,
    }
    
    # Run workflow
    logger.info("Starting VehicleLookupFlow...")
    result = workflow.run(params)
    
    if result.get("status") == "success":
        logger.info(f"✓ Workflow completed: {result.get('summary')}")
        return 0
    else:
        logger.error(f"❌ Workflow failed: {result.get('error')}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Query Compass for vehicle data using MVA lookups",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process MVA list from CSV
  python scripts/glass_data_lookup.py --input data/mva_list.csv --output results.csv
  
  # Single MVA lookup
  python scripts/glass_data_lookup.py --mva 50227203 --output single_result.csv
  
  # With custom config
  python scripts/glass_data_lookup.py --config my_config.ini --input data/mvas.csv
  
  # Headless mode
  python scripts/glass_data_lookup.py --mva 50227203 --headless --output result.csv
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--input', '-i', help='Input CSV file with MVA list')
    input_group.add_argument('--mva', '-m', help='Single MVA to lookup')
    
    # Output options
    parser.add_argument('--output', '-o', default='glass_results.csv',
                        help='Output CSV file (default: glass_results.csv)')
    
    # Configuration
    parser.add_argument('--config', '-c', help='Configuration file (default: webdriver.ini.local)')
    
    # Browser options
    parser.add_argument('--incognito', action='store_true', help='Run in incognito/private mode')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    
    # Mode selection
    parser.add_argument('--force-manual', action='store_true',
                        help='Force manual mode even if workflow available')
    
    args = parser.parse_args()
    
    # Display framework status
    print("\n" + "=" * 60)
    print("Compass Framework - Glass Data Lookup")
    print("=" * 60)
    print(f"LoginFlow available:     {'YES' if LOGIN_AVAILABLE else 'NO (will use manual login)'}")
    print(f"VehicleLookupFlow:       {'YES' if WORKFLOW_AVAILABLE else 'NO (will use manual steps)'}")
    print(f"CSV utilities:           {'YES' if CSV_UTILS_AVAILABLE else 'NO (will use fallback)'}")
    print("=" * 60 + "\n")
    
    # Choose implementation mode
    if WORKFLOW_AVAILABLE and not args.force_manual:
        return workflow_implementation(args)
    else:
        if not args.force_manual:
            print("WARNING: Workflow not available - falling back to manual implementation")
        return manual_implementation(args)


if __name__ == "__main__":
    sys.exit(main())
