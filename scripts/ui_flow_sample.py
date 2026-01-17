"""
UI Flow Sample: Launch Edge, navigate to login, authenticate, and enter MVA.

This script demonstrates a minimal end-to-end flow using the framework:
 - Uses `StandardDriverManager` to launch Edge WebDriver
 - Navigates to a login URL with `SeleniumNavigator`
 - Logs in via the `MicrosoftLoginPage` POM
 - Optionally enters an MVA into a page field provided via locator

Prerequisites:
 - Edge WebDriver installed and version-compatible
 - Configure driver path in `webdriver.ini.local` → `[webdriver] edge_path = drivers.local/msedgedriver.exe`
 - Set credentials via CLI args or environment variables

Usage:
    python scripts/ui_flow_sample.py --url https://login.microsoftonline.com/ \
        --username you@example.com --password **** \
        --mva MVA123 --mva-locator xpath=//input[@name='search']
"""
from __future__ import annotations
import os
import sys
import argparse
from typing import Tuple, Optional
import time

from compass_core import StandardDriverManager, SeleniumNavigator, StandardLogger

# Ensure repo root is on sys.path for importing test POMs
import pathlib as _pl
_repo_root = str(_pl.Path(__file__).resolve().parents[1])
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from tests.e2e.pages.login_page import MicrosoftLoginPage


def parse_locator(spec: Optional[str]) -> Optional[Tuple[str, str]]:
    """Parse a locator spec like `css=.selector` or `xpath=//div` into a tuple.

    Returns (By.<TYPE>, value) where TYPE is 'css selector' or 'xpath'.
    """
    if not spec:
        return None
    if spec.startswith("css="):
        return ("css selector", spec[4:])
    if spec.startswith("xpath="):
        return ("xpath", spec[6:])
    return None


def main():
    ap = argparse.ArgumentParser(description="UI flow sample: login and enter MVA")
    ap.add_argument("--url", default="https://login.microsoftonline.com/", help="Login page URL")
    ap.add_argument("--username", default=os.getenv("UI_SAMPLE_USERNAME", ""), help="Login username/email")
    ap.add_argument("--password", default=os.getenv("UI_SAMPLE_PASSWORD", ""), help="Login password")
    ap.add_argument("--mva", default=os.getenv("UI_SAMPLE_MVA", ""), help="MVA to enter after login")
    ap.add_argument("--mva-locator", default=os.getenv("UI_SAMPLE_MVA_LOCATOR", ""), help="Locator for MVA input (css=... | xpath=...)")
    ap.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    ap.add_argument("--incognito", action="store_true", help="Run browser in InPrivate/incognito mode")
    args = ap.parse_args()

    logger = StandardLogger("ui_flow_sample")

    # Launch driver
    try:
        dm = StandardDriverManager()
        driver = dm.get_or_create_driver(headless=args.headless, incognito=args.incognito)
    except Exception as e:
        logger.error(f"Failed to launch driver: {e}")
        sys.exit(2)

    try:
        # Navigate to login URL
        navigator = SeleniumNavigator(driver)
        # Navigate without strict verification to allow redirects
        nav_res = navigator.navigate_to(args.url, label="App", verify=False)
        # Verify on domain only to tolerate SSO/multipass redirects
        try:
            from urllib.parse import urlparse
            parsed = urlparse(args.url)
            base = f"{parsed.scheme}://{parsed.netloc}"
        except Exception:
            base = args.url
        verify_res = navigator.verify_page(url=base)
        if verify_res.get("status") != "success":
            logger.error(f"Navigation failed: {nav_res}")
            sys.exit(3)

        # Perform login only if we detect Microsoft login page
        login_page = MicrosoftLoginPage(driver, timeout=15)
        if login_page.is_login_page():
            if not args.username:
                logger.warning("Detected Microsoft login page but no username provided; skipping login.")
            else:
                login_res = login_page.login(args.username, args.password or None)
                if not login_res.get("success"):
                    logger.error(f"Login failed: {login_res}")
                    # Continue flow to allow inspection of page state even after login failure
                else:
                    logger.info("Login succeeded.")
        else:
            logger.info("Not a Microsoft login page; skipping login step.")

        # Optionally enter MVA
        if args.mva and args.mva_locator:
            loc = parse_locator(args.mva_locator)
            if not loc:
                logger.warning("Invalid MVA locator format; expected css=... or xpath=...")
            else:
                try:
                    from selenium.webdriver.support.ui import WebDriverWait
                    from selenium.webdriver.support import expected_conditions as EC
                    wait = WebDriverWait(driver, 10)
                    el = wait.until(EC.element_to_be_clickable(loc))
                    el.clear()
                    el.send_keys(args.mva)
                    logger.info(f"Entered MVA: {args.mva}")
                except Exception as e:
                    logger.warning(f"Failed to enter MVA: {e}")

        logger.info("UI flow sample completed.")
    finally:
        try:
            # Pause to allow manual inspection before closing the browser
            time.sleep(30)
            dm.quit_driver()
        except Exception:
            pass


if __name__ == "__main__":
    main()
