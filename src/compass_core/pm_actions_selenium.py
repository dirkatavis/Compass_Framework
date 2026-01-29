"""
Selenium-backed implementation of PM flow actions.

Provides WebDriver-driven interactions for the PM workflow, following the
protocol-first design. This implementation is intended for environments where
Selenium is available; callers should treat all methods as best-effort and use
the returned status dictionaries for error handling.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
import time
import logging

try:
    from selenium.webdriver.remote.webdriver import WebDriver
except Exception:  # Fallback type when selenium typing is unavailable
    from typing import Any as WebDriver  # type: ignore

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from .pm_actions import PmActions


class SeleniumPmActions(PmActions):
    """
    Selenium-backed implementation of `PmActions`.

    Purpose:
      Drive PM-related UI flows via Selenium WebDriver using robust locators
      and defensive error handling.

    Example:
      driver = make_webdriver()
      actions = SeleniumPmActions(driver)
      status = actions.get_lighthouse_status("MVA123")

    Notes:
      The `mva` parameter in methods exists for protocol consistency and may be
      unused by this Selenium implementation, which relies on the active DOM.
    """

    def __init__(self, driver: WebDriver, timeout: int = 10, step_delay: float = 0.0):
        """Initialize Selenium-backed PM actions.

        Args:
            driver: Selenium WebDriver used to interact with the PM UI.
            timeout: Default wait timeout in seconds for Selenium operations.
            step_delay: Pause (in seconds) between actions for visual debugging.
        """
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)
        self.timeout = timeout
        self.step_delay = step_delay
        self._logger = logging.getLogger(__name__)
        # Track the driver's implicit wait value (assumes driver was configured before this instance)
        # Since Selenium doesn't provide a getter, we assume the standard configuration value
        # This will be the value we restore when temporarily disabling implicit wait
        self._implicit_wait_value = timeout

    def _find_pm_complaint_tiles(self) -> list:
        """Locate PM complaint tiles on the current page.

        Returns a list of tile elements; empty list if none found or an error
        occurs.
        """
        try:
            # Use single XPath to directly target PM tiles - more efficient than find-all-then-filter
            return self.driver.find_elements(
                By.XPATH, 
                "//div[contains(@class,'fleet-operations-pwa__complaintItem__') and (contains(., 'PM') or contains(., 'PM Hard Hold - PM'))]"
            )
        except Exception:
            return []

    def get_lighthouse_status(self, mva: str) -> Optional[str]:
        """Get the current Lighthouse status text for the specified vehicle.

        Args:
            mva: Vehicle identifier; accepted for interface consistency.

        Returns:
            Optional[str]: Trimmed Lighthouse status text, or None if not found
            or on error.
        """
        del mva  # protocol parameter retained but not used here
        try:
            status_el = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class, 'fleet-operations-pwa__vehicle-property__') and ./div[contains(., 'Lighthouse')]]//div[contains(@class, 'fleet-operations-pwa__vehicle-property-value__')]",
            )
            return status_el.text.strip()
        except NoSuchElementException:
            return None
        except Exception:
            return None

    def has_open_workitem(self, mva: str) -> bool:
        """Check whether there is an open PM Gas work item in view.

        Args:
            mva: Vehicle identifier; accepted for interface consistency.

        Returns:
            bool: True if an open PM Gas tile is present; False otherwise.
        """
        del mva
        try:
            tiles = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class, 'fleet-operations-pwa__scan-record__') and .//div[contains(@class, 'fleet-operations-pwa__scan-record-header-title-right__') and normalize-space()='Open'] and .//div[contains(@class, 'fleet-operations-pwa__scan-record-header-title__') and normalize-space()='PM Gas']]",
            )
            return len(tiles) > 0
        except Exception:
            return False

    def complete_open_workitem(self, mva: str) -> Dict[str, Any]:
        """Complete the currently open PM work item for a vehicle.

        Returns a structured result dict with status and optional reason.
        """
        del mva
        try:
            parent_card = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class, 'fleet-operations-pwa__scan-record__') and ./div[contains(@class, 'fleet-operations-pwa__scan-record-header__')] and ./div[contains(@class, 'fleet-operations-pwa__scan-record-row-2__') and contains(., 'PM')]]",
            )
            title_bar = parent_card.find_element(By.XPATH, "./div[contains(@class, 'fleet-operations-pwa__scan-record-header__')]")
            title_bar.click()

            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Mark Complete']"))).click()

            dialog_root = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.bp6-dialog")))
            textarea = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "textarea.bp6-text-area")))
            textarea.clear()
            textarea.send_keys("Done")

            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'bp6-dialog')]//button[normalize-space()='Complete Work Item']"))).click()

            self.wait.until(EC.invisibility_of_element(dialog_root))
            return {"status": "ok"}
        except TimeoutException as e:
            self._logger.warning(f"[TIMEOUT] complete_open_workitem: {e}")
            return {"status": "failed", "reason": f"timeout: {e}"}
        except Exception as e:
            self._logger.exception("Unexpected error in complete_open_workitem")
            return {"status": "failed", "reason": f"exception: {e}"}

    def has_pm_complaint(self, mva: str) -> bool:
        """Check whether the current vehicle has at least one PM complaint tile.

        Args:
            mva: Vehicle identifier; accepted for interface consistency.

        Returns:
            bool indicating presence of PM complaint tiles.
        """
        del mva
        try:
            pm_tiles = self._find_pm_complaint_tiles()
            return len(pm_tiles) > 0
        except Exception:
            return False

    def associate_pm_complaint(self, mva: str) -> Dict[str, Any]:
        """Associate the first PM-related complaint with a PM work item.

        Args:
            mva: Vehicle identifier; accepted for interface consistency.

        Returns:
            Result dict with status: ok | skipped_no_complaint | failed.
        """
        del mva
        try:
            pm_tiles = self._find_pm_complaint_tiles()
            if not pm_tiles:
                return {"status": "skipped_no_complaint"}
            pm_tiles[0].click()

            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Next']"))).click()

            try:
                self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Next']"))).click()
            except TimeoutException:
                # If the mileage/Next dialog never appears, we can safely continue the flow.
                pass

            # Attempt to select opcode "PM Gas" and advance the dialog if present.
            try:
                opcode_element = self.wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            "//*[self::button or self::span or self::div][contains(normalize-space(), 'PM Gas')]",
                        )
                    )
                )
                opcode_element.click()

                for label in ("Next", "Done", "Save", "Save & Continue"):
                    try:
                        self.wait.until(EC.element_to_be_clickable((By.XPATH, f"//button[normalize-space()='{label}']"))).click()
                        break
                    except TimeoutException:
                        continue
            except (TimeoutException, NoSuchElementException):
                # If the opcode selection UI is not present, proceed without failing.
                pass

            return {"status": "ok"}
        except TimeoutException as e:
            self._logger.warning(f"[TIMEOUT] associate_pm_complaint: {e}")
            return {"status": "failed", "reason": f"timeout: {e}"}
        except Exception as e:
            self._logger.exception("Unexpected error in associate_pm_complaint")
            return {"status": "failed", "reason": f"exception: {e}"}

    def navigate_back_home(self) -> None:
        """Navigate the browser back to the PM home screen.

        Best-effort helper to reset navigation state at the end of flows.
        """
        try:
            self.driver.back()
        except Exception:
            # Best-effort navigation; failures here are non-fatal and can be safely ignored.
            pass

    def _wait_for_toast_clear(self, timeout: int = 2) -> None:
        """Wait for any toast messages to disappear.
        
        Args:
            timeout: Maximum time to wait for toast to clear (seconds)
        """
        # Store current implicit wait value to restore later
        # Use tracked value since Selenium doesn't provide a getter for current implicit wait
        original_implicit_wait = self._implicit_wait_value
        try:
            # Temporarily disable implicit wait to avoid double-waiting
            self.driver.implicitly_wait(0)
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, "span.bp6-toast-message"))
            )
            self._logger.debug("[TOAST] Toast messages cleared")
        except TimeoutException:
            # No toast or already gone
            pass
        finally:
            # Restore original implicit wait value
            self.driver.implicitly_wait(original_implicit_wait)

    def navigate_to_workitem_tab(self) -> Dict[str, Any]:
        """
        Navigate to the WorkItem tab after entering an MVA.
        
        Returns:
            Dict with status: 'success' | 'failed' and optional error
        """
        # Look for Work Items tab using data-tab-id or text
        workitem_tab_xpath = "//div[@data-tab-id='workItems'] | //div[@role='tab' and contains(normalize-space(), 'Work Item')]"
        
        workitem_tab = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, workitem_tab_xpath))
        )
        workitem_tab.click()
        
        # Wait for tab panel to be visible
        self.wait.until(
            EC.visibility_of_element_located((By.ID, "bp6-tab-panel_undefined_workItems"))
        )
        
        # Wait for work item cards or "Add Work Item" button to be present
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((
                By.XPATH,
                "//div[contains(@class, 'fleet-operations-pwa__scan-record__')] | //button[contains(., 'Add Work Item')]"
            ))
        )
        
        return {"status": "success"}

    def get_existing_workitems(self) -> list:
        """
        Capture all existing workitem structures from the WorkItem tab.
        
        Returns:
            List of workitem dictionaries with 'type', 'status', 'description'
        """
        workitems = []
        try:
            # Find all workitem records - these use fleet-operations-pwa__scan-record class
            workitem_elements = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class, 'fleet-operations-pwa__scan-record__') and contains(@class, 'bp6-card')]"
            )
            
            for elem in workitem_elements:
                try:
                    # Extract workitem type/title from header-title class
                    title_elem = elem.find_element(
                        By.XPATH,
                        ".//div[contains(@class, 'fleet-operations-pwa__scan-record-header-title__')]"
                    )
                    workitem_type = title_elem.text.strip()
                    
                    # Extract status from header-title-right class
                    try:
                        status_elem = elem.find_element(
                            By.XPATH,
                            ".//div[contains(@class, 'fleet-operations-pwa__scan-record-header-title-right__')]"
                        )
                        status = status_elem.text.strip()
                    except NoSuchElementException:
                        status = "Unknown"
                    
                    # Extract description/details from row-2
                    try:
                        desc_elem = elem.find_element(
                            By.XPATH,
                            ".//div[contains(@class, 'fleet-operations-pwa__scan-record-row-2__')]"
                        )
                        description = desc_elem.text.strip()
                    except NoSuchElementException:
                        description = ""
                    
                    if workitem_type:
                        workitems.append({
                            "type": workitem_type,
                            "status": status,
                            "description": description
                        })
                        
                except Exception as exc:
                    self._logger.debug(f"[WORKITEMS] Failed to parse workitem element: {type(exc).__name__}: {exc}")
                    continue
            
            return workitems
            
        except Exception as exc:
            self._logger.debug(f"[WORKITEMS] Failed to read workitems: {type(exc).__name__}: {exc}")
            return []

    def _find_existing_complaints_in_dialog(self) -> list:
        """
        Find existing complaint tiles in the "Create Work Item" dialog.
        
        NOTE: This uses a placeholder locator. Update after HTML inspection.
        Based on legacy code pattern: fleet-operations-pwa__complaintItem__
        
        Returns:
            List of WebElement complaint tiles found in the dialog
        """
        try:
            # Placeholder locator - to be refined with actual HTML from dialog
            # Using pattern from legacy code: //div[contains(@class,'fleet-operations-pwa__complaintItem__')]
            tiles = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class, 'fleet-operations-pwa__complaintItem__')]"
            )
            self._logger.debug(f"[COMPLAINTS] Found {len(tiles)} complaint tile(s) in dialog")
            
            if self.step_delay > 0:
                time.sleep(self.step_delay)
            
            return tiles
            
        except Exception as exc:
            self._logger.debug(f"[COMPLAINTS] Failed to find complaint tiles: {type(exc).__name__}: {exc}")
            return []
    
    def _select_existing_complaint_by_damage_type(self, damage_type: str) -> Dict[str, Any]:
        """
        Search for and select an existing complaint matching the damage type.
        
        Args:
            damage_type: Type of damage to match (e.g., "Glass Damage", "PM", "Tires")
        
        Returns:
            Dict with:
                - status: 'success' (found and selected) | 'not_found' | 'error'
                - action: 'selected_existing' when status='success'
                - error: Error description when status='error'
        """
        try:
            tiles = self._find_existing_complaints_in_dialog()
            
            if not tiles:
                self._logger.info(f"[COMPLAINTS] No existing complaint tiles found")
                return {"status": "not_found"}
            
            # Search for matching damage type in tile text
            matching_tile = None
            for tile in tiles:
                tile_text = tile.text.strip()
                self._logger.debug(f"[COMPLAINTS] Checking tile text: {tile_text!r}")
                
                # Precise match: damage_type appears in tile text
                if damage_type in tile_text:
                    matching_tile = tile
                    self._logger.info(f"[COMPLAINTS] Found matching complaint: {tile_text!r}")
                    break
            
            if not matching_tile:
                self._logger.info(f"[COMPLAINTS] No complaint matching '{damage_type}' found")
                return {"status": "not_found"}
            
            # Click the matching tile
            try:
                matching_tile.click()
                self._logger.info(f"[COMPLAINTS] Clicked existing complaint tile")
                
                if self.step_delay > 0:
                    time.sleep(self.step_delay)
                
                # Click Next button to advance (wait for it to become enabled after tile selection)
                self._logger.info("[COMPLAINTS] Waiting for Next button to become enabled...")
                # Next button is disabled initially, becomes enabled after selecting complaint
                next_btn_xpath = "//button[normalize-space()='Next' and not(@disabled)]"
                next_btn = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, next_btn_xpath))
                )
                self._logger.info("[COMPLAINTS] Next button enabled, clicking now...")
                next_btn.click()
                self._logger.info("[COMPLAINTS] OK - Next button clicked")
                
                if self.step_delay > 0:
                    time.sleep(self.step_delay)
                
                return {"status": "success", "action": "selected_existing"}
                
            except Exception as click_exc:
                self._logger.error(f"[COMPLAINTS] Failed to click complaint tile or Next button: {type(click_exc).__name__}: {click_exc}")
                return {"status": "error", "error": f"tile_click_failed: {type(click_exc).__name__}"}
        
        except Exception as exc:
            self._logger.error(f"[COMPLAINTS] Exception in complaint selection: {type(exc).__name__}: {exc}")
            return {"status": "error", "error": f"selection_exception: {type(exc).__name__}"}

    def find_workitem(self, mva: str, damage_type: str, sub_damage_type: str, correction_action: str) -> Optional[Dict[str, Any]]:
        """
        Find an existing workitem matching the damage type.
        
        Checks existing workitems captured from WorkItem tab.
        Matches by damage type category (Glass, PM, Tires, Keys, etc).

        Args:
            mva: Vehicle identifier
            damage_type: Type of damage (e.g., "Glass", "PM", "Tires", "Keys")
            sub_damage_type: Sub-category of damage (e.g., "Windshield", "Side Window")
            correction_action: Correction action description (for logging)

        Returns:
            Optional[Dict]: Workitem details if found, or None
        """
        # Protocol parameters retained for interface consistency; unused here.
        _mva = mva
        _sub_damage_type = sub_damage_type
        _correction_action = correction_action
        
        try:
            existing = self.get_existing_workitems()
            
            # Match by damage type (case-insensitive, partial match)
            for item in existing:
                if damage_type.lower() in item['type'].lower():
                    return item
            
            return None
        except Exception:
            return None

    def create_workitem(self, mva: str, damage_type: str, sub_damage_type: str, correction_action: str) -> Dict[str, Any]:
        """
        Create a new workitem on the WorkItem tab.

        Args:
            mva: Vehicle identifier
            damage_type: Type of damage (e.g., "Glass", "PM", "Tires", "Keys")
            sub_damage_type: Sub-category of damage (e.g., "Windshield", "Side Window")
            correction_action: Correction action description

        Returns:
            Dict with status: 'success' | 'failed' and optional error/reason
        """
        del mva  # Protocol parameter
        
        try:
            # Step 1: Click "Add Work Item" button
            self._logger.info("[STEP1] Clicking Add Work Item button...")
            create_btn_xpath = "//button[contains(@class, 'fleet-operations-pwa__create-item-button__') and .//span[contains(text(), 'Add Work Item')]] | //button[normalize-space()='Add Work Item']"
            
            create_btn = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, create_btn_xpath))
            )
            create_btn.click()
            self._logger.info("[STEP1] Clicked Add Work Item button, verifying dialog opened...")
            if self.step_delay > 0:
                time.sleep(self.step_delay)
            
            # Step 2: Wait for "Create Work Item" page/dialog to load
            self._logger.info("[STEP2] Waiting for Add New Complaint button...")
            # Use class-based selector for reliability with dynamic hash suffix
            add_complaint_xpath = "//button[contains(@class, 'fleet-operations-pwa__nextButton__')]"
            try:
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, add_complaint_xpath))
                )
                self._logger.info("[STEP1-2] ✓ VERIFIED - Create Work Item dialog loaded with Add Complaint button")
            except TimeoutException:
                self._logger.error(f"[STEP2] FAILED - Add New Complaint button not found after 30s")
                self._logger.error(f"[STEP2] Locator: {add_complaint_xpath}")
                self._logger.error(f"[STEP2] Current URL: {self.driver.current_url}")
                self._logger.error(f"[STEP2] Page title: {self.driver.title}")
                # Check if any dialog appeared at all
                dialogs = self.driver.find_elements(By.CSS_SELECTOR, "div.bp6-dialog, div.bp6-overlay")
                self._logger.error(f"[STEP2] Dialogs on page: {len(dialogs)} found")
                raise
            if self.step_delay > 0:
                time.sleep(self.step_delay)
            
            # Step 3: Check for existing complaints matching the damage type
            self._logger.info(f"[STEP3] Checking for existing complaints matching '{damage_type}'...")
            complaint_result = self._select_existing_complaint_by_damage_type(damage_type)
            
            is_new_complaint = True  # Track whether we're creating new or reusing existing
            
            if complaint_result.get("status") == "success":
                # Existing complaint found and selected - skip form filling
                self._logger.info(f"[STEP3] OK - Reusing existing complaint, skipping form steps")
                is_new_complaint = False
                
            elif complaint_result.get("status") == "not_found":
                # No matching complaint - create new one
                self._logger.info("[STEP3] No matching complaint found - creating new complaint...")
                try:
                    add_complaint_btn = WebDriverWait(self.driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH, add_complaint_xpath))
                    )
                    add_complaint_btn.click()
                    self._logger.info("[STEP3] OK - Clicked Add New Complaint")
                    
                except TimeoutException:
                    self._logger.error(f"[STEP3] FAILED - Add New Complaint button not clickable after 30s")
                    self._logger.error(f"[STEP3] Locator: {add_complaint_xpath}")
                    self._logger.error(f"[STEP3] Current URL: {self.driver.current_url}")
                    # Check if button exists but is disabled
                    buttons = self.driver.find_elements(By.XPATH, add_complaint_xpath)
                    self._logger.error(f"[STEP3] Matching buttons found: {len(buttons)}")
                    if buttons:
                        self._logger.error(f"[STEP3] Button enabled: {buttons[0].is_enabled()}")
                        self._logger.error(f"[STEP3] Button displayed: {buttons[0].is_displayed()}")
                    raise
                if self.step_delay > 0:
                    time.sleep(self.step_delay)
                
            else:
                # Error occurred during complaint selection
                error_msg = complaint_result.get("error", "unknown_error")
                self._logger.error(f"[STEP3] Complaint selection failed: {error_msg}")
                return {
                    "status": "error",
                    "error": f"complaint_selection_failed: {error_msg}"
                }
            
            # Steps 4-8: Only execute if creating NEW complaint (skip if reusing existing)
            if is_new_complaint:
                # Step 4: Answer "Is vehicle drivable?" question
                self._logger.info("[STEP4] Waiting for 'Is vehicle drivable?' question...")
                drivable_xpath = "//button[contains(@class, 'fleet-operations-pwa__drivable-option-button__')][.//h1[text()='Yes']]"
                try:
                    drivable_yes_btn = WebDriverWait(self.driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH, drivable_xpath))
                    )
                    drivable_yes_btn.click()
                    self._logger.info("[STEP4] Clicked 'Yes' for drivable, waiting for damage type screen...")
                except TimeoutException:
                    self._logger.error(f"[STEP4] FAILED - Drivable 'Yes' button not found/clickable after 30s")
                    self._logger.error(f"[STEP4] Locator: {drivable_xpath}")
                    self._logger.error(f"[STEP4] Current URL: {self.driver.current_url}")
                    # Check for any drivable buttons
                    drivable_btns = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'fleet-operations-pwa__drivable-option-button__')]")
                    self._logger.error(f"[STEP4] Drivable buttons found: {len(drivable_btns)}")
                    for idx, btn in enumerate(drivable_btns[:3]):
                        self._logger.error(f"[STEP4] Button {idx}: text='{btn.text.strip()}', enabled={btn.is_enabled()}")
                    raise
                
                # Step 4.5: VERIFY damage type screen actually loaded after drivable click
                damage_button_xpath = f"//button[contains(@class, 'fleet-operations-pwa__damage-option-button__') and .//h1[text()='{damage_type}']]"
                try:
                    WebDriverWait(self.driver, 45).until(
                        EC.presence_of_element_located((By.XPATH, damage_button_xpath))
                    )
                    self._logger.info("[STEP4] ✓ VERIFIED - Damage type screen loaded after drivable selection")
                    
                except TimeoutException:
                    self._logger.error(f"[STEP4] FAILED - Damage type screen did not load after clicking drivable")
                    self._logger.error(f"[STEP4] Expected damage type button: {damage_button_xpath}")
                    self._logger.error(f"[STEP4] Current URL: {self.driver.current_url}")
                    # Check what screen we're actually on
                    damage_btns = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'fleet-operations-pwa__damage-option-button__')]")
                    self._logger.error(f"[STEP4] Damage option buttons found: {len(damage_btns)}")
                    for idx, btn in enumerate(damage_btns[:10]):
                        self._logger.error(f"[STEP4] Option {idx}: '{btn.text.strip()}'")
                    raise
                if self.step_delay > 0:
                    time.sleep(self.step_delay)
                
                # Step 5: Wait for damage type selection screen to appear
                self._logger.info("[STEP5] Damage type screen confirmed, selecting damage type...")
                damage_button_xpath = f"//button[contains(@class, 'fleet-operations-pwa__damage-option-button__') and .//h1[text()='{damage_type}']]"
                
                # Step 6: Select damage type/category - REQUIRED
                self._logger.info(f"[STEP6] Selecting damage type: {damage_type}...")
                
                try:
                    damage_selector = WebDriverWait(self.driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH, damage_button_xpath))
                    )
                    damage_selector.click()
                    self._logger.info(f"[STEP6] Clicked {damage_type}, waiting for sub-damage screen...")
                except TimeoutException:
                    self._logger.error(f"[STEP6] FAILED - Damage type '{damage_type}' button not clickable after 30s")
                    self._logger.error(f"[STEP6] Locator: {damage_button_xpath}")
                    self._logger.error(f"[STEP6] Current URL: {self.driver.current_url}")
                    # Check button state
                    buttons = self.driver.find_elements(By.XPATH, damage_button_xpath)
                    if buttons:
                        self._logger.error(f"[STEP6] Button found but enabled={buttons[0].is_enabled()}, displayed={buttons[0].is_displayed()}")
                    else:
                        self._logger.error(f"[STEP6] Button not found at all")
                    raise
                
                # Step 6.5: VERIFY sub-damage screen actually loaded
                sub_damage_button_xpath = f"//button[contains(@class, 'fleet-operations-pwa__damage-option-button__') and .//h1[text()='{sub_damage_type}']]"
                try:
                    WebDriverWait(self.driver, 45).until(
                        EC.presence_of_element_located((By.XPATH, sub_damage_button_xpath))
                    )
                    self._logger.info(f"[STEP6] ✓ VERIFIED - Sub-damage screen loaded after selecting {damage_type}")
                    
                except TimeoutException:
                    self._logger.error(f"[STEP6] FAILED - Sub-damage screen did not load after clicking {damage_type}")
                    self._logger.error(f"[STEP6] Expected sub-damage button: {sub_damage_button_xpath}")
                    self._logger.error(f"[STEP6] Current URL: {self.driver.current_url}")
                    # Check what options ARE available
                    sub_damage_btns = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'fleet-operations-pwa__damage-option-button__')]")
                    self._logger.error(f"[STEP6] Sub-damage option buttons found: {len(sub_damage_btns)}")
                    for idx, btn in enumerate(sub_damage_btns[:10]):
                        self._logger.error(f"[STEP6] Option {idx}: '{btn.text.strip()}'")
                    raise
                if self.step_delay > 0:
                    time.sleep(self.step_delay)
                
                # Step 7: Select sub-damage type - REQUIRED
                self._logger.info(f"[STEP7] Sub-damage screen confirmed, selecting: {sub_damage_type}...")
                sub_damage_button_xpath = f"//button[contains(@class, 'fleet-operations-pwa__damage-option-button__') and .//h1[text()='{sub_damage_type}']]"
                try:
                    sub_damage_selector = WebDriverWait(self.driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH, sub_damage_button_xpath))
                    )
                    sub_damage_selector.click()
                    self._logger.info(f"[STEP7] Clicked {sub_damage_type}, waiting for Additional Info page...")
                except TimeoutException:
                    self._logger.error(f"[STEP7] FAILED - Sub-damage type '{sub_damage_type}' button not found/clickable after 30s")
                    self._logger.error(f"[STEP7] Locator: {sub_damage_button_xpath}")
                    self._logger.error(f"[STEP7] Current URL: {self.driver.current_url}")
                    # Check what sub-damage types ARE available
                    sub_damage_btns = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'fleet-operations-pwa__damage-option-button__')]")
                    self._logger.error(f"[STEP7] Sub-damage option buttons found: {len(sub_damage_btns)}")
                    for idx, btn in enumerate(sub_damage_btns[:10]):
                        self._logger.error(f"[STEP7] Option {idx}: '{btn.text.strip()}'")
                    raise
                

                # Step 7.5: VERIFY Additional Info page actually loaded
                summary_xpath = "//h1[contains(text(), 'Drivable')]"
                try:
                    WebDriverWait(self.driver, 45).until(
                        EC.presence_of_element_located((By.XPATH, summary_xpath))
                    )
                    self._logger.info(f"[STEP7] ✓ VERIFIED - Additional Info page loaded after selecting {sub_damage_type}")
                except TimeoutException:
                    self._logger.error(f"[STEP7] FAILED - Additional Info page did not load after clicking {sub_damage_type}")
                    self._logger.error(f"[STEP7] Expected summary element: {summary_xpath}")
                    self._logger.error(f"[STEP7] Current URL: {self.driver.current_url}")
                    self._logger.error(f"[STEP7] Page title: {self.driver.title}")
                    # Check what IS on the page
                    h1_elements = self.driver.find_elements(By.TAG_NAME, "h1")
                    self._logger.error(f"[STEP7] H1 elements found: {len(h1_elements)}")
                    for idx, h1 in enumerate(h1_elements[:5]):
                        self._logger.error(f"[STEP7] H1 {idx}: '{h1.text.strip()}'")
                    raise
                if self.step_delay > 0:
                    time.sleep(self.step_delay)

                # Step 8: Click Submit on Additional Info page
                submit_xpath = "//button[.//span[contains(text(), 'Submit')]] | //button[.//p[contains(text(), 'Submit')]] | //button[normalize-space()='Submit']"
                try:
                    submit_btn = WebDriverWait(self.driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH, submit_xpath))
                    )
                    submit_btn.click()
                    self._logger.info("[STEP8] Clicked Submit on Additional Info page, waiting for Mileage page...")
                except TimeoutException:
                    self._logger.error("[STEP8] FAILED - Submit button not found/clickable on Additional Info page")
                    self._logger.error(f"[STEP8] Locator: {submit_xpath}")
                    self._logger.error(f"[STEP8] Current URL: {self.driver.current_url}")
                    raise
                if self.step_delay > 0:
                    time.sleep(self.step_delay)

            else:
                # Existing complaint was selected - form details are pre-filled
                self._logger.info("[STEPS4-7] Skipped - existing complaint selected, details pre-filled")
                self._logger.info("[STEPS8-9] Skipped - existing complaint flow goes directly to Mileage page")
                # Existing complaint flow skips Additional Info and Submit steps,
                # goes directly from complaint selection to Mileage page
                # Brief wait for SPA navigation after clicking Next on complaint
                if self.step_delay > 0:
                    time.sleep(self.step_delay)
                else:
                    time.sleep(0.5)
            
            # Step 10: Navigate Mileage page → Click Next
            self._logger.info("[STEP10] Waiting for Mileage page to load...")
            # Mileage page uses bp6-entity-title-title div, not H1
            mileage_heading_xpath = "//div[contains(@class, 'bp6-entity-title-title') and contains(text(), 'MILEAGE')]"
            try:
                WebDriverWait(self.driver, 45).until(
                    EC.presence_of_element_located((By.XPATH, mileage_heading_xpath))
                )
                self._logger.info("[STEP10] [OK] VERIFIED - Mileage page loaded")
            except TimeoutException:
                self._logger.error(f"[STEP10] FAILED - Mileage page did not load")
                self._logger.error(f"[STEP10] Expected heading: {mileage_heading_xpath}")
                self._logger.error(f"[STEP10] Current URL: {self.driver.current_url}")
                # Check for title elements
                title_elements = self.driver.find_elements(By.CLASS_NAME, "bp6-entity-title-title")
                self._logger.error(f"[STEP10] bp6-entity-title-title elements found: {[t.text.strip() for t in title_elements[:5]]}")
                raise
            
            # Click Next button on Mileage page
            self._logger.info("[STEP10] Clicking Next button on Mileage page...")
            # Next button has text in <p class="fleet-operations-pwa__submitText__...">Next</p>
            next_button_xpath = "//button[.//p[contains(text(), 'Next')]]" 
            try:
                next_btn = WebDriverWait(self.driver, 30).until(
                    EC.element_to_be_clickable((By.XPATH, next_button_xpath))
                )
                next_btn.click()
                self._logger.info("[STEP10] [OK] Clicked Next button")
            except TimeoutException:
                self._logger.error(f"[STEP10] FAILED - Next button not found on Mileage page")
                self._logger.error(f"[STEP10] Locator: {next_button_xpath}")
                # Check for any buttons with Next text
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                next_like = [b for b in all_buttons if 'next' in b.text.lower()]
                self._logger.error(f"[STEP10] Next-like buttons found: {[b.text.strip() for b in next_like[:5]]}")
                raise
            
            if self.step_delay > 0:
                time.sleep(self.step_delay)
            
            # Step 11: Navigate OpCodes page → Select Glass Repair/Replace
            self._logger.info("[STEP11] Waiting for OpCodes page to load...")
            # OpCodes page has no H1 heading, verify by checking for opCode items
            opcodes_items_xpath = "//div[contains(@class, 'opCodeItem')]"
            try:
                WebDriverWait(self.driver, 45).until(
                    EC.presence_of_element_located((By.XPATH, opcodes_items_xpath))
                )
                self._logger.info("[STEP11] [OK] VERIFIED - OpCodes page loaded")
            except TimeoutException:
                self._logger.error(f"[STEP11] FAILED - OpCodes page did not load after clicking Next")
                self._logger.error(f"[STEP11] Expected opCode items: {opcodes_items_xpath}")
                self._logger.error(f"[STEP11] Current URL: {self.driver.current_url}")
                # Check for any divs with opCode class
                opcode_divs = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'opCode')]")
                self._logger.error(f"[STEP11] OpCode divs found: {len(opcode_divs)}")
                raise
            
            # Click Glass Repair/Replace opCode item (it's a div, not a button)
            self._logger.info("[STEP11] Clicking Glass Repair/Replace opCode...")
            # OpCode items are divs with nested text div
            glass_opcode_xpath = "//div[contains(@class, 'opCodeItem') and .//div[contains(text(), 'Glass Repair/Replace')]]"
            try:
                glass_item = WebDriverWait(self.driver, 30).until(
                    EC.element_to_be_clickable((By.XPATH, glass_opcode_xpath))
                )
                glass_item.click()
                self._logger.info("[STEP11] [OK] Clicked Glass Repair/Replace")
            except TimeoutException:
                self._logger.error(f"[STEP11] FAILED - Glass Repair/Replace opCode not found")
                self._logger.error(f"[STEP11] Locator: {glass_opcode_xpath}")
                # Log available opCode items
                opcode_items = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'opCodeText')]")
                self._logger.error(f"[STEP11] Available opCodes: {[item.text.strip() for item in opcode_items[:10]]}")
                raise
            
            if self.step_delay > 0:
                time.sleep(self.step_delay)
            
            # Step 12: Click Create Work Item → Verify WorkItem page
            self._logger.info("[STEP12] Clicking Create Work Item button...")
            # Button text is in <p class="fleet-operations-pwa__submitText__...">Create Work Item</p>
            create_workitem_xpath = "//button[.//p[contains(text(), 'Create Work Item')]]"
            try:
                create_btn = WebDriverWait(self.driver, 30).until(
                    EC.element_to_be_clickable((By.XPATH, create_workitem_xpath))
                )
                create_btn.click()
                self._logger.info("[STEP12] [OK] Clicked Create Work Item")
            except TimeoutException:
                self._logger.error(f"[STEP12] FAILED - Create Work Item button not found")
                self._logger.error(f"[STEP12] Locator: {create_workitem_xpath}")
                # Check for any buttons with similar text
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                create_like = [b for b in all_buttons if 'create' in b.text.lower() or 'work' in b.text.lower()]
                self._logger.error(f"[STEP12] Create/Work buttons found: {[b.text.strip() for b in create_like[:5]]}")
                raise
            
            # Verify navigation to WorkItem page/tab
            self._logger.info("[STEP12] Waiting for WorkItem page to load...")
            workitem_heading_xpath = "//h1[contains(text(), 'Work Item') or contains(text(), 'WorkItem')]"
            try:
                WebDriverWait(self.driver, 45).until(
                    EC.presence_of_element_located((By.XPATH, workitem_heading_xpath))
                )
                self._logger.info("[STEP12] ✓ VERIFIED - WorkItem page loaded")
            except TimeoutException:
                self._logger.error(f"[STEP12] FAILED - WorkItem page did not load after Create Work Item")
                self._logger.error(f"[STEP12] Expected heading: {workitem_heading_xpath}")
                self._logger.error(f"[STEP12] Current URL: {self.driver.current_url}")
                raise
            
            if self.step_delay > 0:
                time.sleep(self.step_delay)
            
            # Step 13: Click Done → Verify Home page
            self._logger.info("[STEP13] Clicking Done button...")
            done_button_xpath = "//button[.//span[contains(text(), 'Done')]]"
            try:
                done_btn = WebDriverWait(self.driver, 30).until(
                    EC.element_to_be_clickable((By.XPATH, done_button_xpath))
                )
                done_btn.click()
                self._logger.info("[STEP13] ✓ Clicked Done button")
            except TimeoutException:
                self._logger.error(f"[STEP13] FAILED - Done button not found")
                self._logger.error(f"[STEP13] Locator: {done_button_xpath}")
                raise
            
            # Verify return to Home/Health page
            self._logger.info("[STEP13] Verifying return to Home page...")
            # Check URL contains 'health' (home page) and Add Work Item button is present
            try:
                WebDriverWait(self.driver, 45).until(
                    lambda d: 'health' in d.current_url.lower()
                )
                # Also verify Add Work Item button is present (confirms we're on main page)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Add Work Item')]"))
                )
                self._logger.info("[STEP13] ✓ VERIFIED - Returned to Home page, Add Work Item button present")
            except TimeoutException:
                self._logger.error(f"[STEP13] FAILED - Did not return to Home page")
                self._logger.error(f"[STEP13] Current URL: {self.driver.current_url}")
                raise
            
            # Success - all 13 steps completed
            complaint_action = "created_new" if is_new_complaint else "reused_existing"
            self._logger.info(f"[COMPLETE] ✓ Workitem created successfully - all 13 steps completed ({complaint_action})")
            
            return {
                "status": "success", 
                "damage_type": damage_type, 
                "action": correction_action,
                "complaint_action": complaint_action
            }
            
        except TimeoutException as e:
            self._logger.warning(f"[TIMEOUT] create_workitem: {e}")
            return {"status": "failed", "reason": f"timeout: {e}"}
        except Exception as e:
            self._logger.exception("Unexpected error in create_workitem")
            return {"status": "failed", "reason": f"exception: {e}"}
