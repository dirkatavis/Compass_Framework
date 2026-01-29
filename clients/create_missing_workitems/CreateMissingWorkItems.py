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
import time
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
    # Place log file in same directory as script
    script_dir = Path(__file__).parent
    log_file = script_dir / 'CreateMissingWorkItems.log'
    level = logging.DEBUG if verbose else logging.INFO
    
    # Remove existing handlers to recreate log
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Recreate log file (delete if exists)
    if log_file.exists():
        log_file.unlink()
    
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

    repo_root = Path(__file__).resolve().parents[2]
    client_dir = Path(__file__).resolve().parent
    
    # Look for sample CSV in client dir first, then shared data dir
    local_sample = client_dir / 'create_missing_workitems_sample.csv'
    shared_sample = repo_root / 'data' / 'create_missing_workitems_sample.csv'
    default_input = local_sample if local_sample.exists() else shared_sample
    
    # Look for config in client dir first, then repo root
    local_config = client_dir / 'webdriver.ini.local'
    shared_config = repo_root / 'webdriver.ini.local'
    default_config = local_config if local_config.exists() else shared_config

    parser.add_argument('--input', '-i',
                       default=str(default_input),
                       help='Input CSV file with workitem specifications')
    parser.add_argument('--config', '-c',
                       default=str(default_config),
                       help='Configuration file with credentials')
    parser.add_argument('--headless', action='store_true',
                       help='Run browser in headless mode')
    parser.add_argument('--incognito', action='store_true', default=True,
                       help='Run browser in incognito/private mode (default: True - forces fresh login)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--step-delay', type=float, default=0.0,
                       help='Pause (in seconds) between actions for visual debugging (default: 0)')
    parser.add_argument('--max-retries', type=int, default=2,
                       help='Max retries with page refresh when property page times out (default: 2)')
    parser.add_argument('--property-timeout', type=int, default=120,
                       help='Timeout in seconds for property page to load (default: 120, increase for slow app performance)')
    parser.add_argument('--debug-pause', action='store_true',
                       help='Pause 30 seconds on failures before closing browser (for debugging, not recommended in CI)')
    
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
            
            retry_count = 0
            success = False
            
            while retry_count <= args.max_retries and not success:
                try:
                    if retry_count > 0:
                        logger.warning(f"  Retry {retry_count}/{args.max_retries}: Refreshing page and trying again...")
                        driver.refresh()
                        time.sleep(3)  # Wait for refresh
                    
                    # Navigate to vehicle (this loads property page on Health tab)
                    logger.debug(f"  Entering MVA on Health tab...")
                    entry_result = vehicle_actions.enter_mva(mva, clear_existing=True)
                    
                    if entry_result['status'] != 'success':
                        raise Exception(f"MVA entry failed: {entry_result.get('error')}")
                    
                    # Wait for property page to load (MVA property field)
                    logger.debug(f"  Waiting for property page (timeout={args.property_timeout}s)...")
                    if not vehicle_actions.wait_for_property_page_loaded(mva, timeout=args.property_timeout):
                        raise Exception("Property page did not load")
                    
                    success = True  # Property page loaded successfully
                    
                except Exception as e:
                    if "Property page did not load" in str(e) and retry_count < args.max_retries:
                        retry_count += 1
                        logger.warning(f"  Property page timeout - will retry ({retry_count}/{args.max_retries})")
                        continue  # Retry the loop
                    else:
                        # Either not a property page error, or we're out of retries
                        raise
            
            if not success:
                raise Exception("Property page failed to load after all retries")
            
            try:
                # NOW switch to WorkItem tab (vehicle already loaded)
                logger.debug(f"  Switching to WorkItem tab...")
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
                    logger.info(f"  [EXISTS] '{damage_type}' workitem already exists (Status: {existing.get('status', 'Unknown')})")
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
                        logger.info(f"  [OK] Workitem created successfully")
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
                logger.error(f"  [FAILED] Error processing {mva}: {e}")
                results['failed'].append({
                    'mva': mva,
                    'damage_type': damage_type,
                    'action': correction_action,
                    'error': str(e)
                })
                # Try to recover
                try:
                    pm_actions.navigate_back_home()
                except Exception as nav_err:
                    logger.warning(f"  Failed to navigate back home during recovery: {nav_err}")
        
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
        
        # If there were failures, optionally pause before closing browser for debugging
        if results['failed'] and args.debug_pause:
            logger.warning("\n[DEBUG] Failures detected - pausing 30 seconds before closing browser...")
            logger.warning("[DEBUG] Check browser window to see current page state")
            time.sleep(30)
        elif results['failed']:
            logger.info("\n[INFO] Failures detected. Use --debug-pause to keep browser open for inspection.")
        
        return 0 if not results['failed'] else 1
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        if args.debug_pause:
            logger.warning("\n[DEBUG] Exception occurred - pausing 30 seconds before closing browser...")
            logger.warning("[DEBUG] Check browser window to see current page state")
            time.sleep(30)
        else:
            logger.info("\n[INFO] Exception occurred. Use --debug-pause to keep browser open for inspection.")
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
