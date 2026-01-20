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

try:
    from .pm_actions import PmActions
except Exception:
    # Fallback protocol definition to allow import when pm_actions is not present
    from typing import Protocol, runtime_checkable

    @runtime_checkable
    class PmActions(Protocol):
        def get_lighthouse_status(self, mva: str) -> Optional[str]: ...
        def has_open_workitem(self, mva: str) -> bool: ...
        def complete_open_workitem(self, mva: str) -> Dict[str, Any]: ...
        def has_pm_complaint(self, mva: str) -> bool: ...
        def associate_pm_complaint(self, mva: str) -> Dict[str, Any]: ...
        def navigate_back_home(self) -> None: ...
        def find_workitem(self, mva: str, damage_type: str, correction_action: str) -> Optional[Dict[str, Any]]: ...
        def create_workitem(self, mva: str, damage_type: str, correction_action: str) -> Dict[str, Any]: ...


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

    def _find_pm_complaint_tiles(self) -> list:
        """Locate PM complaint tiles on the current page.

        Returns a list of tile elements; empty list if none found or an error
        occurs.
        """
        try:
            tiles = self.driver.find_elements(By.XPATH, "//div[contains(@class,'fleet-operations-pwa__complaintItem__')]")
            return [t for t in tiles if any(label in t.text for label in ["PM", "PM Hard Hold - PM"])]
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
        except TimeoutException:
            return {"status": "failed", "reason": "timeout"}
        except Exception as e:
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
        except TimeoutException:
            return {"status": "failed", "reason": "timeout"}
        except Exception as e:
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
                        
                except Exception:
                    continue
            
            return workitems
            
        except Exception:
            return []

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
        del mva  # Protocol parameter
        del sub_damage_type  # Not used in matching currently
        del correction_action  # Not used in matching, only damage type
        
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
            # Wait for any toast messages to disappear first
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, "span.bp6-toast-message"))
                )
                self._logger.debug("[PREP] Waited for toast messages to disappear")
            except TimeoutException:
                # No toast or already gone, that's fine
                pass
            
            # Step 1: Click "Add Work Item" button
            self._logger.info("[STEP1] Clicking Add Work Item button...")
            create_btn_xpath = "//button[contains(@class, 'fleet-operations-pwa__create-item-button__') and .//span[contains(text(), 'Add Work Item')]] | //button[normalize-space()='Add Work Item']"
            
            create_btn = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, create_btn_xpath))
            )
            create_btn.click()
            self._logger.info("[STEP1] OK - Clicked Add Work Item")
            if self.step_delay > 0:
                time.sleep(self.step_delay)
            
            # Step 2: Wait for "Create Work Item" page/dialog to load
            self._logger.info("[STEP2] Waiting for Add New Complaint button...")
            # Use class-based selector for reliability with dynamic hash suffix
            add_complaint_xpath = "//button[contains(@class, 'fleet-operations-pwa__nextButton__')]"
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, add_complaint_xpath))
            )
            self._logger.info("[STEP2] OK - Create Work Item page loaded")
            if self.step_delay > 0:
                time.sleep(self.step_delay)
            
            # Step 3: Check for existing open complaints that match the damage type
            # TODO: Implement logic to select existing complaint if match found
            # For now, always click "Add New Complaint"
            
            self._logger.info("[STEP3] Clicking Add New Complaint button...")
            add_complaint_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, add_complaint_xpath))
            )
            add_complaint_btn.click()
            self._logger.info("[STEP3] OK - Clicked Add New Complaint")
            if self.step_delay > 0:
                time.sleep(self.step_delay)
            
            # Step 4: Answer "Is vehicle drivable?" question
            self._logger.info("[STEP4] Waiting for 'Is vehicle drivable?' question...")
            drivable_yes_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'fleet-operations-pwa__drivable-option-button__')][.//h1[text()='Yes']]"))
            )
            drivable_yes_btn.click()
            self._logger.info("[STEP4] OK - Selected 'Yes' for drivable")
            if self.step_delay > 0:
                time.sleep(self.step_delay)
            
            # Step 5: Wait for damage type selection screen to appear
            self._logger.info("[STEP5] Waiting for damage type buttons...")
            damage_button_xpath = f"//button[contains(@class, 'fleet-operations-pwa__damage-option-button__') and .//h1[text()='{damage_type}']]"
            
            # Wait for the damage type button to be present
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, damage_button_xpath))
            )
            self._logger.info("[STEP5] OK - Damage type buttons visible")
            if self.step_delay > 0:
                time.sleep(self.step_delay)
            
            # Step 6: Select damage type/category - REQUIRED
            self._logger.info(f"[STEP6] Selecting damage type: {damage_type}...")
            
            damage_selector = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, damage_button_xpath))
            )
            damage_selector.click()
            self._logger.info(f"[STEP6] OK - Selected {damage_type}")
            if self.step_delay > 0:
                time.sleep(self.step_delay)
            
            # Step 7: Select sub-damage type - REQUIRED
            self._logger.info(f"[STEP7] Selecting sub-damage type: {sub_damage_type}...")
            sub_damage_button_xpath = f"//button[contains(@class, 'fleet-operations-pwa__damage-option-button__') and .//h1[text()='{sub_damage_type}']]"            
            sub_damage_selector = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, sub_damage_button_xpath))
            )
            sub_damage_selector.click()
            self._logger.info(f"[STEP7] OK - Selected {sub_damage_type}")
            if self.step_delay > 0:
                time.sleep(self.step_delay)
            
            # Step 8: Enter correction action in textarea - REQUIRED
            self._logger.info("[STEP8] Entering correction action...")
            action_field = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "textarea.bp6-text-area"))
            )
            action_field.clear()
            action_field.send_keys(correction_action)
            self._logger.info("[STEP8] OK - Entered correction action")
            if self.step_delay > 0:
                time.sleep(self.step_delay)
            
            # Step 9: Click Complete/Submit button - REQUIRED
            self._logger.info("[STEP9] Clicking Complete/Submit button...")
            complete_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Complete') or contains(text(), 'Submit') or contains(text(), 'Next')]"))
            )
            complete_btn.click()
            self._logger.info("[STEP9] OK - Clicked Complete/Submit")
            if self.step_delay > 0:
                time.sleep(self.step_delay)
            
            # Step 10: Wait for form to close
            self._logger.info("[STEP10] Waiting for form to close...")
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.bp6-dialog, div.bp6-overlay"))
                )
            except TimeoutException:
                pass  # Form might already be closed
            self._logger.info("[STEP10] OK - Form closed, workitem created!")
            
            return {"status": "success", "damage_type": damage_type, "action": correction_action}
            
        except TimeoutException as e:
            self._logger.error(f"[TIMEOUT] {str(e)}")
            return {"status": "failed", "reason": f"timeout: {str(e)}"}
        except Exception as e:
            self._logger.error(f"[EXCEPTION] {str(e)}")
            return {"status": "failed", "reason": f"exception: {str(e)}"}
