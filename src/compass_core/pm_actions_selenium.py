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
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException

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

    def _safe_click(self, element: Any, scroll: bool = True):
        """Perform a safe click by scrolling into center view first.
        
        This overrides viewport scaling issues where elements near the edge 
        are incorrectly calculated during hit-testing if not centered.
        """
        if scroll:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", 
                element
            )
            time.sleep(0.3)
        
        element.click()

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
            self._safe_click(title_bar)

            self._safe_click(self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Mark Complete']"))))

            dialog_root = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.bp6-dialog")))
            textarea = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "textarea.bp6-text-area")))
            textarea.clear()
            textarea.send_keys("Done")

            self._safe_click(self.wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'bp6-dialog')]//button[normalize-space()='Complete Work Item']"))))

            self.wait.until(EC.invisibility_of_element(dialog_root))
            return {"status": "ok"}
        except TimeoutException as e:
            self._logger.warning(f"[TIMEOUT] complete_open_workitem: Timed out waiting for element")
            return {"status": "failed", "reason": "timeout"}
        except Exception as e:
            self._logger.error(f"[ERROR] complete_open_workitem failed: {str(e).split('Stacktrace:')[0].strip()}")
            return {"status": "failed", "reason": f"exception: {type(e).__name__}"}

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
            self._safe_click(pm_tiles[0])

            self._safe_click(self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Next']"))))

            try:
                self._safe_click(self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Next']"))))
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
                self._safe_click(opcode_element)

                for label in ("Next", "Done", "Save", "Save & Continue"):
                    try:
                        self._safe_click(self.wait.until(EC.element_to_be_clickable((By.XPATH, f"//button[normalize-space()='{label}']"))))
                        break
                    except TimeoutException:
                        continue
            except (TimeoutException, NoSuchElementException):
                # If the opcode selection UI is not present, proceed without failing.
                pass

            return {"status": "ok"}
        except TimeoutException as e:
            self._logger.warning(f"[TIMEOUT] associate_pm_complaint: Timed out during association")
            return {"status": "failed", "reason": "timeout"}
        except Exception as e:
            self._logger.error(f"[ERROR] associate_pm_complaint failed: {str(e).split('Stacktrace:')[0].strip()}")
            return {"status": "failed", "reason": f"exception: {type(e).__name__}"}

    def navigate_back_home(self) -> None:
        """Navigate the browser back to the PM home screen (Health tab).

        Uses direct URL navigation instead of driver.back() for maximum reliability
        after complex SPA flows like work item creation.
        """
        try:
            # Detect current environment from URL
            current_url = self.driver.current_url
            if "/workspace/fleet-operations-pwa/" in current_url:
                # Construct clean Health tab URL
                base_url = current_url.split("/workspace/fleet-operations-pwa/")[0]
                health_url = f"{base_url}/workspace/fleet-operations-pwa/health"
                
                if current_url != health_url:
                    self._logger.info(f"[NAV] Returning to Dashboard via URL: {health_url}")
                    self.driver.get(health_url)
                    
                    # Wait for stability
                    WebDriverWait(self.driver, 10).until(
                        lambda d: "health" in d.current_url.lower()
                    )
                    time.sleep(0.5)
            else:
                # Fallback to back() if outside PWA context
                self.driver.back()
        except Exception as e:
            self._logger.warning(f"[NAV] Best-effort navigation failed: {str(e)}")
            # Last resort - try one back() if URL logic failed
            try:
                self.driver.back()
            except:
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
        
        self._safe_click(workitem_tab)
        
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
                self._safe_click(matching_tile)
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
                self._safe_click(next_btn)
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
            # Step 0: Dashboard Audit (Requirement Step 1)
            self._logger.info(f"[STEP0] Performing Dashboard Audit for '{damage_type}'...")
            
            # Look for "Open" cards specifically (red status)
            open_cards_xpath = "//div[contains(@class, 'fleet-operations-pwa__status-red')]//ancestor::div[contains(@class, 'fleet-operations-pwa__scan-record__')]"
            
            # Briefly check if any open cards exist that match the damage type
            try:
                # Use a short wait for the audit
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_all_elements_located((By.XPATH, open_cards_xpath))
                )
                open_cards = self.driver.find_elements(By.XPATH, open_cards_xpath)
                self._logger.info(f"[STEP0] Found {len(open_cards)} total 'Open' cards. Checking for '{damage_type}' match...")
                
                for card in open_cards:
                    card_text = card.text
                    if damage_type.lower() in card_text.lower():
                        self._logger.info(f"[STEP0] [SKIP] Found matching 'Open' card for '{damage_type}': {card_text.strip().splitlines()[0]}")
                        return {
                            "status": "success", 
                            "message": "skipped_duplicate",
                            "damage_type": damage_type,
                            "reason": "existing_open_workitem"
                        }
                self._logger.info(f"[STEP0] No 'Open' cards match '{damage_type}'. Proceeding to creation.")
            except TimeoutException:
                self._logger.info(f"[STEP0] No 'Open' cards found on dashboard. Proceeding to creation.")

            # Step 1: Click "Add Work Item" button
            self._logger.info("[STEP1] Clicking Add Work Item button...")
            create_btn_xpath = "//button[contains(@class, 'fleet-operations-pwa__create-item-button__') and .//span[contains(text(), 'Add Work Item')]] | //button[normalize-space()='Add Work Item']"
            
            create_btn = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, create_btn_xpath))
            )
            self._safe_click(create_btn)
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
                    self._safe_click(add_complaint_btn)
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
                # Step 4: Answer "Is vehicle drivable?" question (Requirement Step 3)
                self._logger.info("[STEP4] Wizard: Selecting Drivable 'Yes' (Checkmark icon)...")
                # Updated XPath to favor binary icon-based selection with text fallback
                drivable_xpath = "//button[.//span[contains(@class, 'bp6-icon-tick-circle')] or .//h1[text()='Yes']]"
                try:
                    drivable_yes_btn = WebDriverWait(self.driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH, drivable_xpath))
                    )
                    self._safe_click(drivable_yes_btn)
                    self._logger.info("[STEP4] ✓ Selected 'Yes' for drivable")
                except TimeoutException:
                    self._logger.error(f"[STEP4] FAILED - Drivable 'Yes' button not found: {drivable_xpath}")
                    raise
                
                # Step 5: Wizard: Category/Damage Type Selection (Requirement Step 4)
                # Requirements state: select icon matching intent (Oil Can / Cracked Window)
                self._logger.info(f"[STEP5] Wizard: Selecting category icon for '{damage_type}'...")
                
                # Map damage types to specific icon names (Blueprints 6 icons usually)
                category_map = {
                    "PM": "//button[.//span[contains(@class, 'bp6-icon-oil-can')] or .//h1[contains(text(), 'PM')]]",
                    "Glass Damage": "//button[.//span[contains(@class, 'bp6-icon-cracked-window')] or .//h1[contains(text(), 'Glass')]]",
                    "Tires": "//button[.//span[contains(@class, 'bp6-icon-inner-tires')] or .//h1[contains(text(), 'Tire')]]"
                }
                
                # Default to text-based if not in map
                category_xpath = category_map.get(damage_type, f"//button[.//h1[text()='{damage_type}']]")
                
                try:
                    category_btn = WebDriverWait(self.driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH, category_xpath))
                    )
                    self._safe_click(category_btn)
                    self._logger.info(f"[STEP5] ✓ Selected category: {damage_type}")
                except TimeoutException:
                    self._logger.error(f"[STEP5] FAILED - Category icon/button not found for '{damage_type}': {category_xpath}")
                    raise

                # Step 6: Wizard: Sub-Category Selection (Requirement Step 5)
                self._logger.info(f"[STEP6] Wizard: Selecting sub-category '{sub_damage_type}'...")
                sub_category_xpath = f"//button[.//h1[text()='{sub_damage_type}']] | //button[contains(@class, 'damage-option-button') and contains(., '{sub_damage_type}')]"
                try:
                    sub_btn = WebDriverWait(self.driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH, sub_category_xpath))
                    )
                    self._safe_click(sub_btn)
                    self._logger.info(f"[STEP6] ✓ Selected sub-category: {sub_damage_type}")
                except TimeoutException:
                    self._logger.error(f"[STEP6] FAILED - Sub-category button not found for '{sub_damage_type}': {sub_category_xpath}")
                    raise

                # Step 7: Wizard: Submit Complaint (Confirmation Handshake)
                self._logger.info("[STEP7] Wizard: Clicking Submit Complaint...")
                submit_complaint_xpath = "//button[.//span[contains(text(), 'Submit')] or .//p[contains(text(), 'Submit')]]"
                try:
                    submit_btn = WebDriverWait(self.driver, 30).until(
                        EC.element_to_be_clickable((By.XPATH, submit_complaint_xpath))
                    )
                    self._safe_click(submit_btn)
                    self._logger.info("[STEP7] ✓ Clicked Submit Complaint")
                except TimeoutException:
                    self._logger.error(f"[STEP7] FAILED - Submit Complaint button not found: {submit_complaint_xpath}")
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
            
            # Step 10: Navigate Mileage page → Click Next (Requirement Step 6)
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
                self._safe_click(next_btn)
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
                self._safe_click(glass_item)
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
            
            # Step 12: Click Create Work Item → Verify Confirmation screen (Requirement Step 12/13)
            self._logger.info("[STEP12] Clicking Create Work Item button...")
            # Button text is in <p class="fleet-operations-pwa__submitText__...">Create Work Item</p>
            create_workitem_xpath = "//button[.//p[contains(text(), 'Create Work Item')]]"
            try:
                create_btn = WebDriverWait(self.driver, 30).until(
                    EC.element_to_be_clickable((By.XPATH, create_workitem_xpath))
                )
                self._safe_click(create_btn)
                self._logger.info("[STEP12] ✓ Clicked Create Work Item")
            except TimeoutException:
                self._logger.error(f"[STEP12] FAILED - Create Work Item button not found")
                self._logger.error(f"[STEP12] Locator: {create_workitem_xpath}")
                # Check for any buttons with similar text
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                create_like = [b for b in all_buttons if 'create' in b.text.lower() or 'work' in b.text.lower()]
                self._logger.error(f"[STEP12] Create/Work buttons found: {[b.text.strip() for b in create_like[:5]]}")
                return {'status': 'failure', 'error': 'create_button_missing'}

            # Step 13: Done Button Handshake (Requirement Step 13)
            # This is the final step: wait for the "Done" confirmation button
            self._logger.info("[STEP13] Handshake: Waiting for 'Done' confirmation button...")
            done_button_xpath = "//button[.//p[contains(@class, 'finalDialogeText') and text()='Done']]"
            start_wait = time.time()
            try:
                # Use strict waiter to detect UI pop
                done_waiter = WebDriverWait(self.driver, 45, poll_frequency=0.2)
                
                # Check for physical presence and clickability
                done_btn = done_waiter.until(
                    EC.element_to_be_clickable((By.XPATH, done_button_xpath))
                )
                self._logger.info(f"[STEP13] ✓ Handshake complete in {time.time() - start_wait:.2f}s")
                
                # Center and Click
                self._safe_click(done_btn)
                self._logger.info("[STEP13] ✓ Clicked Done button, returning to Home page")

                # Verify return to Home/Health page (Requirement Step 13)
                self._logger.info("[STEP13] Verifying return to Dashboard...")
                WebDriverWait(self.driver, 45).until(
                    lambda d: 'health' in d.current_url.lower() and "createWorkItem" not in d.current_url
                )
                self._logger.info(f"[STEP13] ✓ VERIFIED - Returned to Dashboard (URL: {self.driver.current_url})")
                
                # Success - all steps completed
                complaint_action = "created_new" if is_new_complaint else "reused_existing"
                return {
                    "status": "success", 
                    "damage_type": damage_type, 
                    "action": correction_action,
                    "complaint_action": complaint_action
                }

            except Exception as e:
                self._logger.error(f"[STEP13] FAILED at {time.time() - start_wait:.2f}s: {str(e).split('Stacktrace:')[0]}")
                self._logger.error(f"[STEP13] Current URL: {self.driver.current_url}")
                # List all visible buttons to see what's actually there
                all_btns = self.driver.find_elements(By.TAG_NAME, "button")
                visible_texts = [b.text.strip() for b in all_btns if b.is_displayed()]
                self._logger.error(f"[STEP13] All visible buttons: {visible_texts}")
                return {'status': 'failure', 'error': 'confirmation_timeout'}

        except TimeoutException as e:
            self._logger.warning(f"[TIMEOUT] create_workitem: Execution timed out at step progress {self.driver.current_url}")
            return {"status": "failed", "reason": "timeout"}
        except Exception as e:
            self._logger.error(f"[ERROR] create_workitem failed: {str(e).split('Stacktrace:')[0].strip()}")
            return {"status": "failed", "reason": f"exception: {type(e).__name__}"}
