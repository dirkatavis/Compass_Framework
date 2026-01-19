"""
Selenium implementation of VehicleDataActions protocol.

This implementation uses WebDriver to interact with Compass vehicle property pages.
Currently includes inline POM logic; will be extracted to separate POMs in future PRs.
"""
from typing import Dict, Any, Optional, List
import time

try:
    from selenium.webdriver.remote.webdriver import WebDriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    import selenium.webdriver.common.keys as Keys
except ImportError:
    # Fallback when selenium not available
    from typing import Any as WebDriver  # type: ignore
    
from .vehicle_data_actions import VehicleDataActions


class SeleniumVehicleDataActions(VehicleDataActions):
    """Selenium-backed implementation of VehicleDataActions.
    
    This implementation interacts with Compass UI to retrieve vehicle properties.
    
    Note: POM logic is currently inline; will be extracted to:
      - VehiclePropertiesPage (property extraction)
      - MVAInputPage (MVA entry)
    in subsequent PRs after architecture approval.
    
    Example:
        driver = get_driver()
        actions = SeleniumVehicleDataActions(driver)
        actions.enter_mva("50227203")
        vin = actions.get_vehicle_property("VIN")
    """
    
    def __init__(self, driver: WebDriver, timeout: int = 10):
        """Initialize Selenium vehicle data actions.
        
        Args:
            driver: Selenium WebDriver instance
            timeout: Default timeout for wait operations
        """
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)
    
    # ====================
    # MVA INPUT METHODS (TODO: Extract to MVAInputPage POM)
    # ====================
    
    def _find_mva_input(self) -> Optional[Any]:
        """Find the MVA input field on the current page.
        
        TODO: Extract to MVAInputPage.find_input()
        
        Returns:
            WebElement for the input field, or None if not found
        """
        try:
            # Try common input field patterns for Compass
            selectors = [
                (By.CSS_SELECTOR, "input[type='search']"),
                (By.CSS_SELECTOR, "input[placeholder*='MVA']"),
                (By.CSS_SELECTOR, "input[placeholder*='Search']"),
                (By.XPATH, "//input[@type='search' or @type='text']"),
            ]
            
            for by, selector in selectors:
                try:
                    elements = self.driver.find_elements(by, selector)
                    # Return first visible and enabled element
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            return elem
                except Exception:
                    continue
            
            return None
        except Exception:
            return None
    
    def _clear_input_field(self, input_field: Any) -> bool:
        """Aggressively clear an input field.
        
        TODO: Extract to MVAInputPage.clear_field()
        
        Args:
            input_field: WebElement of the input field
            
        Returns:
            True if cleared successfully, False otherwise
        """
        try:
            # Multiple clearing strategies for robustness
            for _ in range(3):
                input_field.send_keys(Keys.Keys.CONTROL + 'a')
                input_field.send_keys(Keys.Keys.DELETE)
                input_field.clear()
                time.sleep(0.2)
            
            # Wait for field to be empty (up to 3 seconds)
            for _ in range(15):
                if input_field.get_attribute("value") == "":
                    return True
                time.sleep(0.2)
            
            return False
        except Exception:
            return False
    
    # ====================
    # VEHICLE PROPERTY METHODS (TODO: Extract to VehiclePropertiesPage POM)
    # ====================
    
    def _get_property_by_label(self, label: str, timeout: int = 5) -> Optional[str]:
        """Get vehicle property value by label.
        
        TODO: Extract to VehiclePropertiesPage.get_property_by_label()
        
        Args:
            label: Property label (e.g., 'VIN', 'Desc')
            timeout: Wait timeout
            
        Returns:
            Property value or None
        """
        try:
            # XPath to find value div next to label div
            xpath = (
                f"//div[div[normalize-space()='{label}']]/div[contains(@class,'vehicle-property-value')]"
            )
            elem = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            value = elem.text.strip() if elem else None
            return value if value else None
        except (TimeoutException, NoSuchElementException):
            return None
    
    def _find_mva_echo(self, mva: str, timeout: int = 1) -> bool:
        """Check if MVA is echoed in the UI.
        
        TODO: Extract to VehiclePropertiesPage.verify_mva_echo()
        
        Args:
            mva: MVA to look for (typically last 8 digits)
            timeout: Wait timeout
            
        Returns:
            True if found, False otherwise
        """
        try:
            # Look for MVA in common display areas
            xpath = f"//*[contains(text(), '{mva}')]"
            elem = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return elem is not None
        except (TimeoutException, NoSuchElementException):
            return False
    
    # ====================
    # PROTOCOL IMPLEMENTATION
    # ====================
    
    def enter_mva(self, mva: str, clear_existing: bool = True) -> Dict[str, Any]:
        """Enter an MVA into the Compass search/input field.
        
        Implements VehicleDataActions.enter_mva()
        """
        try:
            input_field = self._find_mva_input()
            
            if not input_field:
                # Wait and retry
                time.sleep(0.5)
                input_field = self._find_mva_input()
            
            if not input_field:
                return {
                    'status': 'error',
                    'error': 'Could not find MVA input field',
                    'mva': mva
                }
            
            # Wait for field to be ready
            try:
                WebDriverWait(self.driver, 5, poll_frequency=0.25).until(
                    lambda d: input_field.is_enabled() and input_field.is_displayed()
                )
            except TimeoutException:
                return {
                    'status': 'error',
                    'error': 'Input field not ready',
                    'mva': mva
                }
            
            # Clear if requested
            if clear_existing:
                if not self._clear_input_field(input_field):
                    # Log warning but continue
                    pass
            
            # Enter MVA
            input_field.send_keys(mva)
            
            return {
                'status': 'ok',
                'mva': mva
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to enter MVA: {str(e)}',
                'mva': mva
            }
    
    def get_vehicle_property(self, label: str, timeout: int = 10) -> Optional[str]:
        """Get a vehicle property value by its display label.
        
        Implements VehicleDataActions.get_vehicle_property()
        """
        return self._get_property_by_label(label, timeout)
    
    def get_vehicle_properties(self, labels: List[str], timeout: int = 10) -> Dict[str, str]:
        """Get multiple vehicle properties in a single call.
        
        Implements VehicleDataActions.get_vehicle_properties()
        """
        properties = {}
        for label in labels:
            value = self._get_property_by_label(label, timeout)
            properties[label] = value if value else 'N/A'
        return properties
    
    def verify_mva_echo(self, mva: str, timeout: int = 5) -> bool:
        """Verify that the UI has echoed the entered MVA.
        
        Implements VehicleDataActions.verify_mva_echo()
        """
        # Use last 8 digits for matching
        last8 = mva[-8:] if len(mva) >= 8 else mva
        return self._find_mva_echo(last8, timeout)
    
    def wait_for_property_loaded(self, label: str, timeout: int = 10) -> bool:
        """Wait for a specific property to be loaded and visible.
        
        Implements VehicleDataActions.wait_for_property_loaded()
        """
        def non_empty_value(driver):
            val = self._get_property_by_label(label, timeout=1)
            return val if val and val != "N/A" else False
        
        try:
            WebDriverWait(self.driver, timeout, poll_frequency=0.5).until(non_empty_value)
            return True
        except TimeoutException:
            return False
