#!/usr/bin/env python3
"""
Create Missing WorkItems Client

Reads workitem specifications from CSV (MVA, DamageType, CorrectionAction),
finds existing workitems or creates new ones as needed.

Usage:
    python CreateMissingWorkItems.py --input workitems.csv --config ../../webdriver.ini.local
"""
import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add framework to path (editable install alternative)
framework_path = Path(__file__).parent.parent.parent / 'src'
if framework_path.exists():
    sys.path.insert(0, str(framework_path))

from compass_core import (
    StandardDriverManager,
    SeleniumNavigator,
    SmartLoginFlow,
    SeleniumLoginFlow,
    SeleniumPmActions,
    SeleniumVehicleDataActions,
    IniConfiguration,
    read_workitem_list
)


def setup_logging(verbose: bool = False) -> logging.Logger:
    """
    Configure logging for the client script.
    
    Recreates log file each session.
    """
    log_file = 'CreateMissingWorkItems.log'
    level = logging.DEBUG if verbose else logging.INFO
    
    # Remove existing handlers to recreate log
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Recreate log file (delete if exists)
    log_path = Path(log_file)
    if log_path.exists():
        log_path.unlink()
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, mode='w')  # 'w' mode recreates file
        ]
    )
    return logging.getLogger('create_missing_workitems')


def main():
    parser = argparse.ArgumentParser(description='Create or find workitems from CSV list')
    parser.add_argument('--input', '-i',
                       default='../../data/sample_workitems.csv',
                       help='Input CSV file with workitem specifications')
    parser.add_argument('--config', '-c',
                       default='../../webdriver.ini.local',
                       help='Configuration file with credentials')
    parser.add_argument('--headless', action='store_true',
                       help='Run browser in headless mode')
    parser.add_argument('--incognito', action='store_true', default=True,
                       help='Run browser in incognito/private mode (default: True)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--step-delay', type=float, default=0.0,
                       help='Pause (in seconds) between actions for visual debugging (default: 0)')
    
    args = parser.parse_args()
    logger = setup_logging(args.verbose)
    
    logger.info("="*60)
    logger.info("Create Missing WorkItems Client")
    logger.info(f"Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)
    
    # Load configuration
    logger.info(f"Loading configuration from: {args.config}")
    config = IniConfiguration()
    config_data = config.load(args.config)
    
    if not config.validate():
        logger.error("Configuration validation failed")
        return 1
    
    # Read workitem list
    logger.info(f"Reading workitem list from: {args.input}")
    try:
        workitems = read_workitem_list(args.input)
        logger.info(f"Found {len(workitems)} workitems to process")
    except Exception as e:
        logger.error(f"Failed to read workitem list: {e}")
        return 1
    
    # Initialize driver and components
    driver_manager = StandardDriverManager()
    driver = None
    
    # Track results
    results = {
        'found': [],
        'created': [],
        'failed': []
    }
    
    try:
        logger.info("Initializing browser...")
        driver = driver_manager.get_or_create_driver(
            headless=args.headless,
            incognito=args.incognito
        )
        
        navigator = SeleniumNavigator(driver)
        pm_actions = SeleniumPmActions(driver, step_delay=args.step_delay)
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
        
        # Process each workitem
        logger.info(f"\nProcessing {len(workitems)} workitems...")
        
        for idx, item in enumerate(workitems, start=1):
            mva = item['mva']
            damage_type = item['damage_type']
            sub_damage_type = item['sub_damage_type']
            correction_action = item['correction_action']
            
            logger.info(f"\n[{idx}/{len(workitems)}] Processing MVA: {mva}")
            logger.info(f"  Damage Type: {damage_type}")
            logger.info(f"  Sub-Damage Type: {sub_damage_type}")
            logger.info(f"  Correction: {correction_action}")
            
            try:
                # Navigate to vehicle
                logger.debug(f"  Entering MVA...")
                entry_result = vehicle_actions.enter_mva(mva, clear_existing=True)
                
                if entry_result['status'] != 'success':
                    raise Exception(f"MVA entry failed: {entry_result.get('error')}")
                
                # Wait for property page to load (MVA property field)
                logger.debug(f"  Waiting for property page...")
                if not vehicle_actions.wait_for_property_page_loaded(mva):
                    raise Exception("Property page did not load")
                
                # Navigate to WorkItem tab
                logger.debug(f"  Navigating to WorkItem tab...")
                tab_result = pm_actions.navigate_to_workitem_tab()
                
                if tab_result['status'] != 'success':
                    raise Exception(f"Failed to navigate to WorkItem tab: {tab_result.get('reason')}")
                
                # Capture existing workitems
                logger.debug(f"  Capturing existing workitems...")
                existing_items = pm_actions.get_existing_workitems()
                
                if existing_items:
                    logger.debug(f"  Found {len(existing_items)} existing workitems:")
                    for wi in existing_items:
                        logger.debug(f"    - {wi['type']} ({wi['status']})")
                else:
                    logger.debug(f"  No existing workitems found")
                
                # Check if workitem matching damage type exists
                logger.debug(f"  Checking for existing '{damage_type}' workitem...")
                existing = pm_actions.find_workitem(mva, damage_type, sub_damage_type, correction_action)
                
                if existing:
                    logger.info(f"  ✓ '{damage_type}' workitem already exists (Status: {existing.get('status', 'Unknown')})")
                    results['found'].append({
                        'mva': mva,
                        'damage_type': damage_type,
                        'action': correction_action,
                        'status': existing.get('status', 'Unknown')
                    })
                else:
                    # Create new workitem
                    logger.info(f"  → Creating new '{damage_type}' workitem...")
                    create_result = pm_actions.create_workitem(mva, damage_type, sub_damage_type, correction_action)
                    
                    if create_result['status'] == 'success':
                        logger.info(f"  ✓ Workitem created successfully")
                        results['created'].append({
                            'mva': mva,
                            'damage_type': damage_type,
                            'action': correction_action
                        })
                    else:
                        raise Exception(f"Creation failed: {create_result.get('reason', 'Unknown')}")
                
                # Navigate back for next item
                pm_actions.navigate_back_home()
                
            except Exception as e:
                logger.error(f"  ✗ Error processing {mva}: {e}")
                results['failed'].append({
                    'mva': mva,
                    'damage_type': damage_type,
                    'action': correction_action,
                    'error': str(e)
                })
                # Try to recover
                try:
                    pm_actions.navigate_back_home()
                except Exception:
                    pass
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("SUMMARY")
        logger.info("="*60)
        logger.info(f"Total Processed: {len(workitems)}")
        logger.info(f"  Found Existing: {len(results['found'])}")
        logger.info(f"  Created New:    {len(results['created'])}")
        logger.info(f"  Failed:         {len(results['failed'])}")
        
        if results['failed']:
            logger.warning("\nFailed Items:")
            for item in results['failed']:
                logger.warning(f"  - {item['mva']}: {item['error']}")
        
        logger.info("="*60)
        logger.info(f"Session completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return 0 if not results['failed'] else 1
        
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        return 1
        
    finally:
        if driver:
            logger.info("\nClosing browser...")
            try:
                driver_manager.quit_driver()
            except Exception as e:
                logger.warning(f"Error closing driver: {e}")


if __name__ == '__main__':
    sys.exit(main())
