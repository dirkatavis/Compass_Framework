#!/usr/bin/env python3
"""
Vehicle Lookup Client Script - Compass Framework

Demonstrates complete GlassDataParser.py functionality using Compass Framework.
Replaces legacy script with protocol-based, testable implementation.

Usage:
    python scripts/vehicle_lookup_client.py --input data/mva.csv --output results.csv
    python scripts/vehicle_lookup_client.py --mva 50227203,12345678 --output results.csv
"""
import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from compass_core import (
    StandardDriverManager,
    SeleniumNavigator,
    SeleniumLoginFlow,
    SmartLoginFlow,
    SeleniumVehicleDataActions,
    VehicleLookupFlow,
    IniConfiguration,
    StandardLogger
)


def main():
    """Main entry point for vehicle lookup client."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Batch MVA lookup using Compass Framework'
    )
    parser.add_argument(
        '--input',
        help='Path to input CSV file with MVA list'
    )
    parser.add_argument(
        '--mva',
        help='Comma-separated list of MVAs (alternative to --input)'
    )
    parser.add_argument(
        '--output',
        required=True,
        help='Path to output CSV file for results'
    )
    parser.add_argument(
        '--config',
        default='webdriver.ini.local',
        help='Configuration file (default: webdriver.ini.local)'
    )
    parser.add_argument(
        '--incognito',
        action='store_true',
        help='Use incognito mode (forces fresh login)'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode'
    )
    parser.add_argument(
        '--properties',
        default='VIN,Desc',
        help='Comma-separated list of properties to retrieve (default: VIN,Desc)'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=12,
        help='Timeout in seconds for property loading (default: 12)'
    )
    
    args = parser.parse_args()
    
    # Validate input source
    if not args.input and not args.mva:
        parser.error('Either --input or --mva must be provided')
    
    if args.input and args.mva:
        parser.error('Cannot use both --input and --mva')
    
    # Initialize logger
    logger = StandardLogger("vehicle_lookup_client")
    logger.info("=" * 80)
    logger.info("Vehicle Lookup Client - Compass Framework")
    logger.info("=" * 80)
    
    # Load configuration
    config = IniConfiguration()
    try:
        config.load(args.config)
        logger.info(f"Loaded configuration from: {args.config}")
    except FileNotFoundError:
        logger.warning(f"Config file not found: {args.config}, trying fallback...")
        try:
            config.load('webdriver.ini')
            logger.info("Loaded fallback configuration: webdriver.ini")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return 1
    
    # Get credentials from config or environment
    username = config.get('credentials.username') or os.getenv('COMPASS_USERNAME')
    password = config.get('credentials.password') or os.getenv('COMPASS_PASSWORD')
    login_id = config.get('credentials.login_id') or os.getenv('COMPASS_LOGIN_ID')
    app_url = config.get('app.app_url')
    
    # Validate required credentials
    if not all([username, password, app_url]):
        logger.error("Missing required credentials (username, password, app_url)")
        logger.error("Set in config file or environment variables:")
        logger.error("  COMPASS_USERNAME, COMPASS_PASSWORD, COMPASS_LOGIN_ID (optional)")
        return 1
    
    # Parse properties list
    properties = [p.strip() for p in args.properties.split(',')]
    
    # Build parameters for workflow
    params = {
        'username': username,
        'password': password,
        'app_url': app_url,
        'login_id': login_id,
        'output_file': args.output,
        'properties': properties,
        'timeout': args.timeout
    }
    
    # Add MVA source (input file or direct list)
    if args.input:
        if not os.path.exists(args.input):
            logger.error(f"Input file not found: {args.input}")
            return 1
        params['input_file'] = args.input
        logger.info(f"Input source: CSV file ({args.input})")
    else:
        mva_list = [m.strip() for m in args.mva.split(',')]
        params['mva_list'] = mva_list
        logger.info(f"Input source: Direct MVA list ({len(mva_list)} MVAs)")
    
    logger.info(f"Output file: {args.output}")
    logger.info(f"Properties: {', '.join(properties)}")
    logger.info(f"Incognito mode: {args.incognito}")
    logger.info(f"Headless mode: {args.headless}")
    
    # Initialize Compass Framework components
    logger.info("-" * 80)
    logger.info("Initializing Compass Framework...")
    
    try:
        # Create driver manager
        driver_manager = StandardDriverManager()
        
        # Create driver with options
        driver = driver_manager.get_or_create_driver(
            incognito=args.incognito,
            headless=args.headless
        )
        logger.info("✓ WebDriver initialized")
        
        # Create navigator
        navigator = SeleniumNavigator(driver)
        logger.info("✓ Navigator initialized")
        
        # Create login flows (base + smart)
        base_login_flow = SeleniumLoginFlow(driver, navigator, logger)
        smart_login_flow = SmartLoginFlow(driver, navigator, base_login_flow, logger)
        logger.info("✓ Login flows initialized (SmartLoginFlow active)")
        
        # Create vehicle data actions
        vehicle_actions = SeleniumVehicleDataActions(driver, logger)
        logger.info("✓ Vehicle data actions initialized")
        
        # Create workflow
        workflow = VehicleLookupFlow(
            driver_manager=driver_manager,
            navigator=navigator,
            login_flow=smart_login_flow,
            vehicle_actions=vehicle_actions,
            logger=logger
        )
        logger.info("✓ VehicleLookupFlow initialized")
        
        # Execute workflow
        logger.info("-" * 80)
        logger.info("Executing workflow...")
        logger.info("-" * 80)
        
        result = workflow.run(params)
        
        # Report results
        logger.info("=" * 80)
        if result['status'] == 'success':
            logger.info("✓ Workflow completed successfully")
            logger.info(f"  Total MVAs: {result['results_count']}")
            logger.info(f"  Successful: {result['success_count']}")
            logger.info(f"  Failed: {result['results_count'] - result['success_count']}")
            logger.info(f"  Output: {result['output_file']}")
            logger.info("=" * 80)
            return 0
        else:
            logger.error("✗ Workflow failed")
            logger.error(f"  Error: {result.get('error', 'Unknown error')}")
            logger.error("=" * 80)
            return 1
            
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1
    finally:
        # Cleanup
        try:
            if 'driver_manager' in locals():
                driver_manager.quit_driver()
                logger.info("✓ WebDriver cleaned up")
        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")


if __name__ == '__main__':
    sys.exit(main())
