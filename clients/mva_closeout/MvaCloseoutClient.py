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
import os
import sys
import time
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
    SeleniumPmActions,
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


def _pause_between_steps(logger: logging.Logger, step_delay: float, step_name: str) -> None:
    """Pause between workflow steps for easier visual debugging."""
    if step_delay > 0:
        logger.info(f"  [PAUSE] Waiting {step_delay:.1f}s after {step_name}...")
        time.sleep(step_delay)


def main():
    repo_root = Path(__file__).resolve().parents[2]
    client_dir = Path(__file__).resolve().parent

    local_sample = client_dir / 'mva_closeout_sample.csv'
    shared_sample = repo_root / 'data' / 'mva_closeout_sample.csv'
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
    parser.add_argument('--step-delay', type=float, default=None,
                        help='Pause (in seconds) between closeout steps (default: 0.5, overridable by INI or env)')
    parser.add_argument('--workitem-type', default='Glass',
                        help='Work item type to close (default: Glass)')

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

    # Determine step delay: priority is CLI > ENV > INI > default
    step_delay = args.step_delay
    if step_delay is None:
        step_delay_env = os.environ.get('COMPASS_STEP_DELAY')
        if step_delay_env is not None:
            try:
                step_delay = float(step_delay_env)
            except ValueError:
                step_delay = None
    if step_delay is None:
        try:
            step_delay_ini = config.get('timeouts.step_delay', None)
            if step_delay_ini is not None:
                step_delay = float(step_delay_ini)
        except Exception:
            step_delay = None
    if step_delay is None:
        step_delay = 0.5
    logger.info(f"Step delay between actions: {step_delay} seconds")
    target_type = (args.workitem_type or '').strip()
    logger.info(f"Target work item type: {target_type}")

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
        pm_actions = SeleniumPmActions(driver, step_delay=step_delay)
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
            current_step = "mark_processing"
            mva_item.mark_processing()

            try:
                logger.info("  [STEP 1] Entering MVA...")
                current_step = "enter_mva"
                entry_result = vehicle_actions.enter_mva(mva_item.mva, clear_existing=True)
                if entry_result.get('status') != 'success':
                    raise Exception(f"MVA entry failed: {entry_result.get('error', 'Unknown error')}")
                logger.info("  [STEP 1] ✓ MVA entered")
                _pause_between_steps(logger, step_delay, "STEP 1")

                logger.info("  [STEP 2] Waiting for property page...")
                current_step = "wait_for_property_page"
                if not vehicle_actions.wait_for_property_page_loaded(mva_item.mva):
                    raise Exception("Property page did not load")
                logger.info("  [STEP 2] ✓ Property page loaded")
                _pause_between_steps(logger, step_delay, "STEP 2")

                logger.info("  [STEP 3] Checking work items...")
                current_step = "check_workitems"
                tab_result = pm_actions.navigate_to_workitem_tab()
                if tab_result.get('status') != 'success':
                    raise Exception("Failed to navigate to WorkItem tab")

                workitems = pm_actions.get_existing_workitems()
                if not workitems:
                    raise Exception("No work items found")

                def _status_value(item):
                    return (item.get('status') or '').strip().lower()

                def _is_open(item):
                    return _status_value(item) == 'open'

                def _is_closed(item):
                    return _status_value(item) in ('closed', 'complete', 'completed')

                def _matches_target(item):
                    target = target_type.lower()
                    title = (item.get('type') or '').lower()
                    description = (item.get('description') or '').lower()
                    return target in title or target in description

                open_items = [item for item in workitems if _is_open(item)]
                closed_items = [item for item in workitems if _is_closed(item)]
                unknown_items = [item for item in workitems if not _is_open(item) and not _is_closed(item)]

                open_target_items = [item for item in open_items if _matches_target(item)]
                closed_target_items = [item for item in closed_items if _matches_target(item)]

                logger.info(
                    "  [STEP 3] Work items found - Open: %d, Closed: %d, Other: %d",
                    len(open_items),
                    len(closed_items),
                    len(unknown_items)
                )

                if not open_items:
                    logger.info("  [STEP 3] No open work items; skipping closeout")
                    mva_item.mark_completed({
                        'status_update_result': 'skipped',
                        'error': 'No open work items'
                    })
                    logger.info("  [STEP 7] ✓ MVA closeout skipped")
                    logger.info(f"  Progress: {collection.progress_percentage:.1f}%")
                    _pause_between_steps(logger, step_delay, "STEP 7")
                    continue

                if not open_target_items:
                    if closed_target_items:
                        logger.info(
                            "  [STEP 3] '%s' work items already closed; skipping closeout",
                            target_type
                        )
                    else:
                    logger.info(
                        "  [STEP 3] No open '%s' work items; skipping closeout",
                        target_type
                    )
                    mva_item.mark_completed({
                        'status_update_result': 'skipped',
                        'error': f"No open {target_type} work items"
                    })
                    logger.info("  [STEP 7] ✓ MVA closeout skipped")
                    logger.info(f"  Progress: {collection.progress_percentage:.1f}%")
                    _pause_between_steps(logger, step_delay, "STEP 7")
                    continue

                _pause_between_steps(logger, step_delay, "STEP 3")

                logger.info("  [STEP 4] Closing open work item...")
                current_step = "close_workitem"
                close_result = pm_actions.complete_open_workitem(mva_item.mva)
                if close_result.get('status') != 'ok':
                    raise Exception(f"Work item close failed: {close_result.get('reason', 'Unknown error')}")
                logger.info("  [STEP 4] ✓ Work item closed")
                _pause_between_steps(logger, step_delay, "STEP 4")

                logger.info("  [STEP 5] Updating vehicle status to Closed...")
                current_step = "set_vehicle_status"
                status_result = vehicle_actions.set_vehicle_status("Closed")
                if status_result.get('status') != 'success':
                    raise Exception(f"Status update failed: {status_result.get('error', 'Unknown error')}")
                logger.info("  [STEP 5] ✓ Status updated to Closed")
                _pause_between_steps(logger, step_delay, "STEP 5")

                logger.info("  [STEP 6] Saving vehicle record...")
                current_step = "save_vehicle"
                save_result = vehicle_actions.save_vehicle()
                if save_result.get('status') != 'success':
                    raise Exception(f"Save failed: {save_result.get('error', 'Unknown error')}")
                logger.info("  [STEP 6] ✓ Vehicle record saved")
                _pause_between_steps(logger, step_delay, "STEP 6")

                current_step = "mark_completed"
                mva_item.mark_completed({
                    'status_update_result': 'success',
                    'error': ''
                })

                logger.info("  [STEP 7] ✓ MVA closeout completed")
                logger.info(f"  Progress: {collection.progress_percentage:.1f}%")
                _pause_between_steps(logger, step_delay, "STEP 7")

            except Exception as e:
                logger.error(f"  ✗ Failed at step '{current_step}': {e}")
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