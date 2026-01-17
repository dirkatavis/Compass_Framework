"""
Selenium-backed implementation of PM flow actions.

Provides WebDriver-driven interactions for the PM workflow, following the
protocol-first design. This implementation is intended for environments where
Selenium is available; callers should treat all methods as best-effort and use
the returned status dictionaries for error handling.
"""
from __future__ import annotations
from typing import Dict, Any, Optional

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

    def __init__(self, driver: WebDriver, timeout: int = 10):
        """Initialize Selenium-backed PM actions.

        Args:
            driver: Selenium WebDriver used to interact with the PM UI.
            timeout: Default wait timeout in seconds for Selenium operations.
        """
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)
        self.timeout = timeout

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
