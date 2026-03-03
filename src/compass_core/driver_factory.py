"""
Driver Factory for Compass Framework.
Provides self-healing Edge WebDriver management with version mismatch detection and auto-update.
"""

import os
import sys
import logging
import subprocess
import time
import zipfile
import io
from typing import Optional, Dict, Any, Tuple
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.common.exceptions import SessionNotCreatedException, WebDriverException

# Try to import webdriver-manager for Approach A
try:
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
    HAS_WEBDRIVER_MANAGER = True
except ImportError:
    HAS_WEBDRIVER_MANAGER = False

# Import internal version checking (if available)
try:
    from .browser_version_checker import BrowserVersionChecker
except ImportError:
    # Fallback/Mock for standalone or when imported from outside compass_core
    BrowserVersionChecker = None

class DriverFactory:
    """
    Architect's Solution for robust, self-healing Edge WebDriver management.
    Handles version mismatches, process locking, and automatic recovery.
    """
    
    def __init__(self, driver_path: Optional[str] = None, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.driver_path = driver_path or self._get_default_driver_path()
        self.checker = BrowserVersionChecker() if BrowserVersionChecker else None
        
    def _get_default_driver_path(self) -> str:
        """Determines the standard location for msedgedriver.exe."""
        # Check current directory or drivers.local/
        if os.path.exists("msedgedriver.exe"):
            return os.path.abspath("msedgedriver.exe")
        
        # Try finding relative to this file if in compass_core
        base_dir = os.path.dirname(os.path.abspath(__file__))
        local_drivers = os.path.join(os.path.dirname(base_dir), "drivers.local", "msedgedriver.exe")
        if os.path.exists(local_drivers):
            return local_drivers
            
        return os.path.abspath("msedgedriver.exe")

    def kill_locked_drivers(self):
        """Terminates any running msedgedriver.exe processes to prevent file locks."""
        self.logger.info("[DRIVER_FACTORY] Task: Terminating locked msedgedriver.exe processes...")
        try:
            if sys.platform == "win32":
                # Find and kill msedgedriver.exe
                subprocess.run(["taskkill", "/F", "/IM", "msedgedriver.exe", "/T"], 
                               capture_output=True, check=False)
                # Give OS a moment to release handles
                time.sleep(1)
        except Exception as e:
            self.logger.warning(f"[DRIVER_FACTORY] Error killing driver processes: {e}")

    def update_driver_approach_a(self) -> str:
        """Approach A: Use webdriver-manager for a clean, low-maintenance setup."""
        self.logger.info("[DRIVER_FACTORY] Updating via Approach A (webdriver-manager)...")
        self.kill_locked_drivers()
        manager = EdgeChromiumDriverManager()
        new_path = manager.install()
        self.logger.info(f"[DRIVER_FACTORY] Approach A Success: {new_path}")
        return new_path

    def update_driver_approach_b(self) -> str:
        """Approach B: Custom/Air-Gapped fallback using direct downloads from Microsoft."""
        self.logger.info("[DRIVER_FACTORY] Updating via Approach B (Manual Scrape/Download)...")
        import urllib.request
        import json
        
        # 1. Detect Browser Version
        browser_v = "unknown"
        if self.checker:
            browser_v = self.checker.get_edge_version()
        
        if browser_v == "unknown":
            raise RuntimeError("Cannot detect Edge browser version for manual download.")
            
        self.logger.info(f"[DRIVER_FACTORY] Target Version: {browser_v}")
        
        # 2. Kill locks
        self.kill_locked_drivers()
        
        # 3. Construct Download URL (Microsoft pattern)
        # Usually: https://msedgedriver.azureedge.net/{version}/edgedriver_win64.zip
        url = f"https://msedgedriver.azureedge.net/{browser_v}/edgedriver_win64.zip"
        
        try:
            self.logger.info(f"[DRIVER_FACTORY] Downloading from {url}...")
            with urllib.request.urlopen(url) as response:
                content = response.read()
                
            # 4. Extract
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                # Find msedgedriver.exe in zip
                for file_name in z.namelist():
                    if file_name.lower() == "msedgedriver.exe":
                        # Write to self.driver_path
                        with open(self.driver_path, "wb") as f:
                            f.write(z.read(file_name))
                        self.logger.info(f"[DRIVER_FACTORY] Approach B Success: {self.driver_path}")
                        return self.driver_path
        except Exception as e:
            self.logger.error(f"[DRIVER_FACTORY] Approach B Failed: {e}")
            raise

        raise RuntimeError("msedgedriver.exe not found in downloaded zip.")

    def get_driver(self, options: Optional[EdgeOptions] = None, max_retries: int = 2) -> webdriver.Edge:
        """
        Main entry point. Attempts to create driver, catches version errors, 
        self-heals, and re-attempts.
        """
        report = {"attempts": 0, "status": "Pending", "browser_version": "N/A", "driver_version": "N/A"}
        
        if self.checker:
            report["browser_version"] = self.checker.get_edge_version()
            report["driver_version"] = self.checker.get_driver_version(self.driver_path)

        for attempt in range(1, max_retries + 1):
            report["attempts"] = attempt
            try:
                self.logger.info(f"[DRIVER_FACTORY] Initialization Attempt {attempt}...")
                service = Service(executable_path=self.driver_path)
                driver = webdriver.Edge(service=service, options=options)
                
                # If we get here, success!
                report["status"] = "Success"
                self._print_summary_table(report)
                return driver
                
            except (SessionNotCreatedException, WebDriverException) as e:
                err_msg = str(e)
                is_version_mismatch = "This version of Microsoft Edge WebDriver only supports" in err_msg or \
                                    "session not created: This version of" in err_msg
                
                if is_version_mismatch and attempt < max_retries:
                    self.logger.warning("[DRIVER_FACTORY] Version mismatch detected! Self-healing initiated...")
                    
                    try:
                        if HAS_WEBDRIVER_MANAGER:
                            self.driver_path = self.update_driver_approach_a()
                        else:
                            self.driver_path = self.update_driver_approach_b()
                        
                        # Update report metadata after download
                        if self.checker:
                            report["driver_version"] = self.checker.get_driver_version(self.driver_path)
                            
                        continue # Re-attempt loop
                    except Exception as fatal:
                        self.logger.error(f"[DRIVER_FACTORY] Auto-update failed: {fatal}")
                        break
                else:
                    self.logger.error(f"[DRIVER_FACTORY] Unrecoverable WebDriver error: {e}")
                    report["status"] = f"Failed: {type(e).__name__}"
                    raise RuntimeError(f"Unrecoverable WebDriver error: {e}")
        
        self._print_summary_table(report)
        raise RuntimeError(f"Failed to initialize Edge WebDriver after {max_retries} attempts.")

    def _print_summary_table(self, report: Dict[str, Any]):
        """Prints a concise summary table as requested."""
        table = [
            "\n" + "="*50,
            " EDGE WEBDRIVER INITIALIZATION SUMMARY ",
            "-"*50,
            f" Current Browser Version : {report['browser_version']}",
            f" Target Driver Version  : {report['driver_version']}",
            f" Total Attempts         : {report['attempts']}",
            f" Final Status           : {report['status'].upper()}",
            "="*50 + "\n"
        ]
        print("\n".join(table))

def architect_note():
    """Architect's Note on Approach selection."""
    note = """
### Senior Architect's Note: WebDriver Maintenance

*   **Recommendation: Approach A (webdriver-manager)**
    Approach A is the preferred solution for production environments. It leverages a mature, community-maintained 
    library that handles not only Edge but Chrome, Firefox, and IE. It abstracts away the brittle URL 
    scraping logic and supports custom cache directories, which is vital for CI/CD pipelines.

*   **When to use Approach B (Manual):**
    Use this only in highly restricted, air-gapped, or "locked-down" corporate environments where 
    third-party PyPI packages are audited/prohibited, but direct traffic to *.azureedge.net (Microsoft) 
    is permitted.

*   **Resiliency Design:**
    The `DriverFactory` implements a 'Trap-Fix-Retry' pattern. By catching `SessionNotCreatedException`, 
    we isolate version issues from environmental issues. Process management (`taskkill`) is critical on 
    Windows where open handles prevent binary replacement.
    """
    print(note)

if __name__ == "__main__":
    # Self-test/Demo
    logging.basicConfig(level=logging.INFO)
    factory = DriverFactory()
    try:
        # options = EdgeOptions()
        # options.add_argument("--headless")
        # d = factory.get_driver(options=options)
        # d.quit()
        architect_note()
    except Exception as e:
        print(f"Demo failed: {e}")
