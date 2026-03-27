#!/usr/bin/env python3
"""
Vin2Mva Client - Vehicle MVA Retrieval via VIN

Reads VINs from CSV, retrieves corresponding MVAs from Compass,
and writes results to Vin2Mva_results.csv.

Usage:
    python Vin2Mva.py --input vins_sample.csv --config ../../webdriver.ini.local
"""
import argparse
import logging
import sys
import os
from pathlib import Path

# Add framework to path (editable install alternative)
framework_path = Path(__file__).resolve().parents[2] / "src"
if framework_path.exists():
    sys.path.insert(0, str(framework_path))

try:
    from compass_core import (
        CompassRunner,
        Vin2MvaFlow,
        StandardDriverManager,
        SeleniumNavigator,
        SmartLoginFlow,
        SeleniumLoginFlow,
        SeleniumVehicleDataActions,
        IniConfiguration,
        StandardLogger,
        StandardLoggerFactory
    )
except ImportError as e:
    print(f"Error: Framework not found or missing dependencies: {e}")
    sys.exit(1)


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure logging for the client script."""
    # Place log file in same directory as script
    script_dir = Path(__file__).parent
    log_file = script_dir / "vin2mva_diag.log"
    level = logging.DEBUG if verbose else logging.INFO
    
    # Use framework logger factory for consistency
    factory = StandardLoggerFactory()
    logger = factory.create_logger("vin2mva_client", {"level": level})
    
    # Add file handler for diagnostics
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    
    # StandardLogger wraps a standard logging.Logger instance
    if hasattr(logger, "_logger"):
        logger._logger.addHandler(file_handler)
    
    return logger


def main():
    # Resolve paths
    repo_root = Path(__file__).resolve().parents[2]
    client_dir = Path(__file__).resolve().parent
    
    # Default paths
    default_input = client_dir / "vins_sample.csv"
    default_output = client_dir / "Vin2Mva_results.csv"
    
    # Look for config in client dir first, then repo root
    local_config = client_dir / "webdriver.ini.local"
    shared_config = repo_root / "webdriver.ini.local"
    default_config = local_config if local_config.exists() else shared_config
    
    parser = argparse.ArgumentParser(description="Retrieve MVAs for VIN list")
    parser.add_argument("--input", "-i", 
                       default=str(default_input),
                       help="Input CSV file with VIN list")
    parser.add_argument("--output", "-o",
                       default=str(default_output),
                       help="Output CSV file for results")
    parser.add_argument("--config", "-c",
                       default=str(default_config),
                       help="Configuration file with credentials")
    parser.add_argument("--headless", action="store_true",
                       help="Run browser in headless mode")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    parser.add_argument("--timeout", "-t", type=int, default=20,
                       help="Timeout in seconds for vehicle data display (default: 20)")
    
    args = parser.parse_args()
    logger = setup_logging(args.verbose)
    
    logger.info("="*60)
    logger.info("Vin2Mva Client - Vehicle MVA Retrieval")
    logger.info("="*60)
    
    # Initialize Configuration
    config = IniConfiguration()
    if not os.path.exists(args.config):
        logger.error(f"Configuration file not found: {args.config}")
        logger.info("Please create webdriver.ini.local from webdriver.ini template")
        return 1
        
    config.load(args.config)
    if not config.validate():
        logger.error("Configuration validation failed - check credentials and URLs")
        return 1
    
    # Setup Driver Manager
    driver_manager = StandardDriverManager()
    
    # Setup Navigator
    # The protocol method name is get_or_create_driver
    driver = driver_manager.get_or_create_driver()
    navigator = SeleniumNavigator(driver)
    
    # Setup Login Flow
    login_flow = SmartLoginFlow(
        driver=driver,
        navigator=navigator,
        login_flow=SeleniumLoginFlow(driver=driver, navigator=navigator, logger=logger),
        logger=logger
    )
    
    # Setup Vehicle Data Actions
    vehicle_actions = SeleniumVehicleDataActions(
        driver=driver,
        logger=logger
    )
    
    # Initialize Workflow
    workflow = Vin2MvaFlow(
        driver_manager=driver_manager,
        navigator=navigator,
        login_flow=login_flow,
        vehicle_actions=vehicle_actions,
        logger=logger
    )
    
    # Execution parameters
    params = {
        "username": config.get("credentials.username"),
        "password": config.get("credentials.password"),
        "login_id": config.get("credentials.login_id"),
        "app_url": config.get("app.app_url"),
        "input_file": args.input,
        "output_file": args.output,
        "timeout": args.timeout
    }
    
    # Run Workflow
    try:
        result = workflow.run(params)
        
        status = result.get("status")
        if status == "success":
            logger.info("SUCCESS: " + str(result.get("summary")))
            logger.info("Results saved to: " + str(args.output))
            return 0
        else:
            logger.error("FAILURE: " + str(result.get("error")))
            return 1
            
    except KeyboardInterrupt:
        logger.warning("Workflow interrupted by user")
        return 130
    except Exception as e:
        logger.critical("Unhandled exception: " + str(e))
        import traceback
        logger.critical(traceback.format_exc())
        return 1
    finally:
        # Cleanup
        driver_manager.quit_driver()


if __name__ == "__main__":
    sys.exit(main())
