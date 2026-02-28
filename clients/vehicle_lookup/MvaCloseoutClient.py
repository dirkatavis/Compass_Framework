#!/usr/bin/env python3
"""
MVA Closeout Client

Reads MVAs from CSV, updates each vehicle status to Closed,
and writes results to MvaCloseout_results.csv.

Usage:
    python MvaCloseoutClient.py --input mva_list.csv --config ../webdriver.ini.local
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
    script_dir = Path(__file__).parent
    log_file = script_dir / 'mva_closeout.log'
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )
    return logging.getLogger('mva_closeout_client')


def main():
    repo_root = Path(__file__).resolve().parents[2]
    client_dir = Path(__file__).resolve().parent

    local_sample = client_dir / 'vehicle_lookup_sample.csv'
    shared_sample = repo_root / 'data' / 'vehicle_lookup_sample.csv'
    default_input = local_sample if local_sample.exists() else shared_sample

    default_output = client_dir / 'MvaCloseout_results.csv'

    local_config = client_dir / 'webdriver.ini.local'
    shared_config = repo_root / 'webdriver.ini.local'
    default_config = local_config if local_config.exists() else shared_config

    parser = argparse.ArgumentParser(description='Close out vehicles for MVA list')
    parser.add_argument('--input', '-i',
                        default=str(default_input),
                        help='Input CSV file with MVA list')
    parser.add_argument('--output', '-o',
                        default=str(default_output),
                        help='Output CSV file for results')
    parser.add_argument('--config', '-c',
                        default=str(default_config),
                        help='Configuration file with credentials')
    parser.add_argument('--headless', action='store_true',
                        help='Run browser in headless mode')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')

    args = parser.parse_args()
    logger = setup_logging(args.verbose)

    logger.info("=" * 60)
    logger.info("MVA Closeout Client")
    logger.info("=" * 60)

    logger.info(f"Loading configuration from: {args.config}")
    config = IniConfiguration()
    config_data = config.load(args.config)

    if not config.validate():
        logger.error("Configuration validation failed")
        return 1

    output_path = Path(args.output)
    if output_path.exists():
        logger.info(f"Clearing previous output file: {args.output}")
        output_path.unlink()

    logger.info(f"Reading MVA list from: {args.input}")
    mva_list = read_mva_list(args.input)
    logger.info(f"Found {len(mva_list)} MVAs to process")

    collection = MvaCollection.from_list(mva_list)

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

        logger.info("Performing authentication...")

        base_login = SeleniumLoginFlow(driver, navigator, logger)
        login_flow = SmartLoginFlow(driver, navigator, base_login, logger)

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

        logger.info(f"\nProcessing {len(collection)} MVAs...")

        for idx, mva_item in enumerate(collection, start=1):
            logger.info(f"\n[{idx}/{len(collection)}] Processing MVA: {mva_item.mva}")
            mva_item.mark_processing()

            try:
                logger.debug("  Entering MVA...")
                entry_result = vehicle_actions.enter_mva(mva_item.mva, clear_existing=True)
                if entry_result.get('status') != 'success':
                    raise Exception(f"MVA entry failed: {entry_result.get('error', 'Unknown error')}")

                logger.debug("  Waiting for property page...")
                if not vehicle_actions.wait_for_property_page_loaded(mva_item.mva):
                    raise Exception("Property page did not load")

                logger.info("  Updating vehicle status to Closed...")
                status_result = vehicle_actions.set_vehicle_status("Closed")
                if status_result.get('status') != 'success':
                    raise Exception(f"Status update failed: {status_result.get('error', 'Unknown error')}")

                logger.debug("  Saving vehicle record...")
                save_result = vehicle_actions.save_vehicle()
                if save_result.get('status') != 'success':
                    raise Exception(f"Save failed: {save_result.get('error', 'Unknown error')}")

                mva_item.mark_completed({
                    'status_update_result': 'success',
                    'error': ''
                })

                logger.info("  ✓ Status updated to Closed")
                logger.info(f"  Progress: {collection.progress_percentage:.1f}%")

            except Exception as e:
                logger.error(f"  ✗ Failed: {e}")
                mva_item.mark_failed(str(e))

        logger.info(f"\nWriting results to: {args.output}")
        output_path = Path(args.output)

        results = []
        for item in collection:
            if item.is_completed:
                result = item.result or {}
                results.append({
                    'mva': item.mva,
                    'status_update_result': result.get('status_update_result', 'success'),
                    'error': result.get('error', '')
                })
            elif item.is_failed:
                results.append({
                    'mva': item.mva,
                    'status_update_result': 'failed',
                    'error': item.error or 'Unknown error'
                })
            else:
                results.append({
                    'mva': item.mva,
                    'status_update_result': 'failed',
                    'error': 'MVA was not processed'
                })

        write_results_csv(results, str(output_path))

        logger.info("=" * 60)
        logger.info("Summary:")
        logger.info(f"  Total MVAs: {len(collection)}")
        logger.info(f"  Completed: {collection.completed_count}")
        logger.info(f"  Failed: {collection.failed_count}")
        logger.info(f"  Success Rate: {collection.progress_percentage:.1f}%")
        logger.info(f"  Output: {output_path.absolute()}")
        logger.info("=" * 60)

        return 0 if collection.failed_count == 0 else 1

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1

    finally:
        if driver:
            logger.info("Closing browser...")
            driver_manager.quit_driver()


if __name__ == '__main__':
    sys.exit(main())