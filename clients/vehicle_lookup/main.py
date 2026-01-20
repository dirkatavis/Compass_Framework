#!/usr/bin/env python3
"""
Vehicle Lookup Client - Glass Info Retrieval

Reads MVAs from CSV, retrieves vehicle properties (MVA, VIN, Description),
and writes results to GlassInfo.csv.

Usage:
    python main.py --input mva_list.csv --config ../webdriver.ini.local
"""
import argparse
import logging
import sys
from pathlib import Path

# Add framework to path (editable install alternative)
framework_path = Path(__file__).parent.parent.parent / 'src'
if framework_path.exists():
    sys.path.insert(0, str(framework_path))

from compass_core import (
    StandardDriverManager,
    SeleniumNavigator,
    SmartLoginFlow,
    SeleniumLoginFlow,
    SeleniumVehicleDataActions,
    IniConfiguration,
    MvaCollection,
    read_mva_list,
    write_results_csv
)


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure logging for the client script."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('vehicle_lookup.log')
        ]
    )
    return logging.getLogger('vehicle_lookup_client')


def main():
    parser = argparse.ArgumentParser(description='Retrieve glass info for MVA list')
    parser.add_argument('--input', '-i', 
                       default='../../data/sample_mva_list.csv',
                       help='Input CSV file with MVA list')
    parser.add_argument('--output', '-o',
                       default='GlassInfo.csv',
                       help='Output CSV file for results')
    parser.add_argument('--config', '-c',
                       default='../../webdriver.ini.local',
                       help='Configuration file with credentials')
    parser.add_argument('--headless', action='store_true',
                       help='Run browser in headless mode')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    logger = setup_logging(args.verbose)
    
    logger.info("="*60)
    logger.info("Vehicle Lookup Client - Glass Info Retrieval")
    logger.info("="*60)
    
    # Load configuration
    logger.info(f"Loading configuration from: {args.config}")
    config = IniConfiguration()
    config_data = config.load(args.config)
    
    if not config.validate():
        logger.error("Configuration validation failed")
        return 1
    
    # Clear output file from previous session
    output_path = Path(args.output)
    if output_path.exists():
        logger.info(f"Clearing previous output file: {args.output}")
        output_path.unlink()
    
    # Read MVA list
    logger.info(f"Reading MVA list from: {args.input}")
    mva_list = read_mva_list(args.input)
    logger.info(f"Found {len(mva_list)} MVAs to process")
    
    # Create collection for state tracking
    collection = MvaCollection.from_list(mva_list)
    
    # Initialize driver and components
    driver_manager = StandardDriverManager()
    driver = None
    
    try:
        logger.info("Initializing browser...")
        driver = driver_manager.get_or_create_driver(
            headless=args.headless,
            incognito=True
        )
        
        navigator = SeleniumNavigator(driver)
        vehicle_actions = SeleniumVehicleDataActions(driver, logger=logger)
        
        # Login
        logger.info("Performing authentication...")
        
        # Create login flows
        base_login = SeleniumLoginFlow(driver, navigator, logger)
        login_flow = SmartLoginFlow(driver, navigator, base_login, logger)
        
        # Authenticate with credentials
        app_url = config_data['app'].get('app_url', config_data['app'].get('base_url', ''))
        login_result = login_flow.authenticate(
            username=config_data['credentials']['username'],
            password=config_data['credentials']['password'],
            url=app_url,
            login_id=config_data['credentials'].get('login_id', config_data['credentials'].get('wwid', '')),
            timeout=60
        )
        
        if login_result['status'] != 'success':
            logger.error(f"Login failed: {login_result.get('error', 'Unknown error')}")
            return 1
        
        logger.info("✓ Authentication successful")
        
        # Process each MVA
        logger.info(f"\nProcessing {len(collection)} MVAs...")
        properties_to_get = ['MVA', 'VIN', 'Desc']
        
        for idx, mva_item in enumerate(collection, start=1):
            logger.info(f"\n[{idx}/{len(collection)}] Processing MVA: {mva_item.mva}")
            mva_item.mark_processing()
            
            try:
                # Enter MVA
                logger.debug(f"  Entering MVA...")
                entry_result = vehicle_actions.enter_mva(mva_item.mva, clear_existing=True)
                
                if entry_result['status'] != 'success':
                    raise Exception(f"MVA entry failed: {entry_result.get('error')}")
                
                # Verify echo
                logger.debug(f"  Verifying MVA echo...")
                if not vehicle_actions.verify_mva_echo(mva_item.mva):
                    raise Exception("MVA echo verification failed")
                
                # Wait for property page
                logger.debug(f"  Waiting for property page...")
                if not vehicle_actions.wait_for_property_page_loaded(mva_item.mva, timeout=15):
                    raise Exception("Property page did not load")
                
                # Retrieve properties
                logger.info(f"  Retrieving properties: {', '.join(properties_to_get)}")
                retrieved = {}
                for prop_name in properties_to_get:
                    value = vehicle_actions.get_vehicle_property(prop_name, timeout=5)
                    retrieved[prop_name] = value if value else 'N/A'
                    logger.info(f"    {prop_name}: {value if value else 'N/A'}")
                
                logger.info(f"  Summary - MVA: {retrieved['MVA']}, VIN: {retrieved['VIN']}, Desc: {retrieved['Desc']}")
                
                # Mark completed (normalize keys to lowercase for CSV export)
                mva_item.mark_completed({
                    'vin': retrieved.get('VIN', 'N/A'),
                    'desc': retrieved.get('Desc', 'N/A')
                })
                logger.info(f"  Progress: {collection.progress_percentage:.1f}%")
                
            except Exception as e:
                logger.error(f"  ✗ Failed: {e}")
                mva_item.mark_failed({'error': str(e)})
        
        # Write results
        logger.info(f"\nWriting results to: {args.output}")
        output_path = Path(args.output)
        results = collection.to_results_list()
        write_results_csv(results, str(output_path))
        
        logger.info("="*60)
        logger.info("Summary:")
        logger.info(f"  Total MVAs: {len(collection)}")
        logger.info(f"  Completed: {collection.completed_count}")
        logger.info(f"  Failed: {collection.failed_count}")
        logger.info(f"  Success Rate: {collection.progress_percentage:.1f}%")
        logger.info(f"  Output: {output_path.absolute()}")
        logger.info("="*60)
        
        return 0 if collection.failed_count == 0 else 1
        
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        return 1
        
    finally:
        if driver:
            logger.info("Closing browser...")
            driver_manager.quit_driver()


if __name__ == '__main__':
    sys.exit(main())
