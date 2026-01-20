"""
Selenium implementation of VehicleDataActions protocol.

This implementation uses WebDriver to interact with Compass vehicle property pages.
Currently includes inline POM logic; will be extracted to separate POMs in future PRs.
"""
from typing import Dict, Any, Optional, List
import time
import logging

try:
    from selenium.webdriver.remote.webdriver import WebDriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
except ImportError:
    # Selenium not available - module cannot be used
    from typing import Any as WebDriver  # type: ignore
    Keys = None  # type: ignore
    
from .vehicle_data_actions import VehicleDataActions

# WebDriver wait configuration
DEFAULT_WAIT_TIMEOUT = 10  # seconds
DEFAULT_POLL_FREQUENCY = 0.5  # seconds
FIELD_READY_TIMEOUT = 5  # seconds - for field readiness checks
FIELD_READY_POLL = 0.25  # seconds - faster polling for field checks


class SeleniumVehicleDataActions(VehicleDataActions):
    """Selenium-backed implementation of VehicleDataActions.
    
    This implementation interacts with Compass UI to retrieve vehicle properties.
    
    Note: POM logic is currently inline; will be extracted to:
      - VehiclePropertiesPage (property extraction)
      - MVAInputPage (MVA entry)
    in subsequent PRs after architecture approval.
    
    Example:
        driver = get_driver()
        logger = StandardLogger("vehicle_actions")
        actions = SeleniumVehicleDataActions(driver, logger)
        actions.enter_mva("50227203")
        vin = actions.get_vehicle_property("VIN")
    """
    
    def __init__(self, driver: WebDriver, logger: logging.Logger = None, timeout: int = 10):
        """Initialize Selenium vehicle data actions.
        
        Args:
            driver: Selenium WebDriver instance
            logger: Optional logger instance
            timeout: Default timeout for wait operations (seconds)
        """
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, DEFAULT_WAIT_TIMEOUT, poll_frequency=DEFAULT_POLL_FREQUENCY)
        self._logger = logger or logging.getLogger(__name__)
    
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
                            self._logger.debug(f"[MVA_INPUT] Found input field using {by}={selector}")
                            return elem
                except Exception as e:
                    self._logger.debug(f"[MVA_INPUT] Selector {by}={selector} failed: {e}")
                    continue
            
            self._logger.warning("[MVA_INPUT] No MVA input field found with any known selector")
            return None
        except Exception as e:
            self._logger.error(f"[MVA_INPUT] Error finding input field: {e}")
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
                input_field.send_keys(Keys.CONTROL + 'a')
                input_field.send_keys(Keys.DELETE)
                input_field.clear()
                time.sleep(0.2)
            
            # Wait for field to be empty (up to 3 seconds)
            for i in range(15):
                if input_field.get_attribute("value") == "":
                    self._logger.debug(f"[MVA_INPUT] Field cleared after {i * 0.2:.1f}s")
                    return True
                time.sleep(0.2)
            
            self._logger.warning("[MVA_INPUT] Field not empty after clearing attempts")
            return False
        except Exception as e:
            self._logger.error(f"[MVA_INPUT] Error clearing input field: {e}")
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
            # Multiple XPath strategies to find property value
            xpaths = [
                # Strategy 1: Exact class match with sibling selector
                f"//div[contains(@class, 'vehicle-property-name') and normalize-space()='{label}']/following-sibling::div[contains(@class, 'vehicle-property-value')]",
                # Strategy 2: Parent container approach
                f"//div[div[contains(@class, 'vehicle-property-name') and normalize-space()='{label}']]/div[contains(@class,'vehicle-property-value')]",
                # Strategy 3: Generic fallback
                f"//div[div[normalize-space()='{label}']]/div[contains(@class,'value')]"
            ]
            
            elem = None
            for xpath in xpaths:
                try:
                    elem = WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((By.XPATH, xpath))
                    )
                    if elem:
                        break
                except (TimeoutException, NoSuchElementException):
                    continue
            
            if not elem:
                self._logger.warning(f"[PROPERTY] Property '{label}' element not found after trying all strategies")
                return None
            
            value = elem.text.strip() if elem else None
            if value:
                self._logger.debug(f"[PROPERTY] Found {label}={value}")
            else:
                self._logger.warning(f"[PROPERTY] Element found for {label} but value is empty")
            return value if value else None
        except Exception as e:
            self._logger.error(f"[PROPERTY] Error getting property '{label}': {e}")
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
            if elem:
                self._logger.debug(f"[MVA_ECHO] Found MVA '{mva}' echoed in UI")
                return True
            return False
        except TimeoutException:
            self._logger.debug(f"[MVA_ECHO] MVA '{mva}' not found in UI (timeout={timeout}s)")
            return False
        except NoSuchElementException:
            self._logger.debug(f"[MVA_ECHO] MVA '{mva}' element not found")
            return False
        except Exception as e:
            self._logger.error(f"[MVA_ECHO] Error checking MVA echo for '{mva}': {e}")
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
                WebDriverWait(self.driver, FIELD_READY_TIMEOUT, poll_frequency=FIELD_READY_POLL).until(
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
                    self._logger.warning(f"[MVA] Field not fully cleared before entering MVA '{mva}'")
            
            # Enter MVA
            input_field.send_keys(mva)
            self._logger.info(f"[MVA] Entered MVA: {mva}")
            
            return {
                'status': 'success',
                'mva': mva
            }
            
        except Exception as e:
            self._logger.error(f"[MVA] Failed to enter MVA '{mva}': {e}")
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
            self._logger.debug(f"[PROPERTY] Property '{label}' loaded successfully")
            return True
        except TimeoutException:
            self._logger.warning(f"[PROPERTY] Timeout waiting for property '{label}' to load (timeout={timeout}s)")
            return False
        except Exception as e:
            self._logger.error(f"[PROPERTY] Error waiting for property '{label}': {e}")
            return False
    
    def wait_for_property_page_loaded(self, expected_mva: str, timeout: int = 15) -> bool:
        """
        Wait for property page to load by detecting MVA in property section.
        
        This method waits for the vehicle property page to fully load by checking
        if the expected MVA appears in the property details section. This is the
        most reliable indicator that the page has finished loading after entering
        an MVA (which auto-submits after 8 digits).
        
        Args:
            expected_mva: The MVA value to search for in the property section
            timeout: Maximum wait time in seconds (default: 15)
            
        Returns:
            True if property section loaded with expected MVA visible, False on timeout
            
        Example:
            >>> vehicle_actions.enter_mva("50227203")
            >>> if vehicle_actions.wait_for_property_page_loaded("50227203", timeout=15):
            ...     vin = vehicle_actions.get_vehicle_property("VIN")
        """
        if not expected_mva:
            self._logger.warning("[PROPERTY_PAGE] Empty MVA provided")
            return False
        
        # Use last 8 digits for matching
        mva_to_find = expected_mva[-8:] if len(expected_mva) >= 8 else expected_mva
        
        self._logger.info(f"[PROPERTY_PAGE] Waiting for property page with MVA: {mva_to_find}")
        
        def mva_in_properties(driver):
            """Check if MVA appears in property section with exact match."""
            try:
                # Look for MVA text in the property section
                # Try multiple selectors that might contain the MVA
                selectors = [
                    f"//*[contains(text(), '{mva_to_find}')]",  # Any element containing MVA
                    f"//div[contains(@class, 'property')]//text()[contains(., '{mva_to_find}')]",
                    f"//*[@id='mva' or @name='mva']//following-sibling::*[contains(text(), '{mva_to_find}')]"
                ]
                
                for selector in selectors:
                    try:
                        element = driver.find_element(By.XPATH, selector)
                        if element and element.is_displayed():
                            # Verify the element text exactly matches our MVA (or contains it as a word)
                            element_text = element.text.strip()
                            # Check if MVA appears as exact match or word boundary
                            if element_text == mva_to_find or f" {mva_to_find} " in f" {element_text} ":
                                self._logger.debug(f"[PROPERTY_PAGE] Found MVA '{mva_to_find}' in element text: '{element_text[:50]}'")
                                return True
                    except NoSuchElementException:
                        continue
                        
                return False
                
            except Exception as e:
                self._logger.debug(f"[PROPERTY_PAGE] Error checking for MVA: {e}")
                return False
        
        try:
            WebDriverWait(self.driver, timeout, poll_frequency=DEFAULT_POLL_FREQUENCY).until(mva_in_properties)
            self._logger.info(f"[PROPERTY_PAGE] Property page loaded successfully with MVA: {mva_to_find}")
            return True
            
        except TimeoutException:
            self._logger.warning(f"[PROPERTY_PAGE] Timeout waiting for property page with MVA: {mva_to_find} (timeout={timeout}s)")
            return False
            
        except Exception as e:
            self._logger.error(f"[PROPERTY_PAGE] Error waiting for property page: {e}")
            return False
