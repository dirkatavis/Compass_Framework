"""
Page Object Model for the Additional Information page in the complaint workflow.

This page appears after damage type and correction action have been entered,
showing a summary of the complaint before final submission.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver
    from selenium.webdriver.remote.webelement import WebElement


class AdditionalInformationPage:
    """
    Page Object for the Additional Information/Summary page.
    
    This page displays the complaint summary (Drivable status, damage type, etc.)
    and contains the final "Submit Complaint" button.
    
    Example HTML structure:
        <div class="fleet-operations-pwa__metadata-container__...">
            <div class="fleet-operations-pwa__metadata-row__...">
                <h1 class="bp6-heading">Drivable, Glass Damage</h1>
            </div>
            ...
            <button type="button" class="bp6-button bp6-intent-success ...">
                <span class="bp6-button-text">Submit Complaint</span>
            </button>
        </div>
    """
    
    # Locators - using contains() for CSS module classes with dynamic hashes
    SUMMARY_HEADING = (By.XPATH, "//h1[contains(text(), 'Drivable')]")
    MVA_DISPLAY = (By.XPATH, "//div[contains(@class, 'fleet-operations-pwa__mva__')]")
    SUBMIT_COMPLAINT_BUTTON = (By.XPATH, "//button[.//span[contains(text(), 'Submit Complaint')]]")
    ADDITIONAL_INFO_CHECKBOX = (By.XPATH, "//button[contains(@class, 'fleet-operations-pwa__checkbox-wrapper__')]")
    TAKE_PICTURE_BUTTON = (By.XPATH, "//button[contains(., 'Take picture')]")
    
    def __init__(self, driver: WebDriver, timeout: int = 30):
        """
        Initialize the Additional Information page object.
        
        Args:
            driver: Selenium WebDriver instance
            timeout: Default timeout for waits (seconds)
        """
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)
    
    def is_loaded(self) -> bool:
        """
        Check if the Additional Information page has loaded.
        
        Returns:
            True if the page summary heading is visible, False otherwise
        """
        try:
            self.wait.until(EC.presence_of_element_located(self.SUMMARY_HEADING))
            return True
        except TimeoutException:
            return False
    
    def get_summary_text(self) -> str:
        """
        Get the summary heading text (e.g., "Drivable, Glass Damage").
        
        Returns:
            The summary text, or empty string if not found
        """
        try:
            heading = self.driver.find_element(*self.SUMMARY_HEADING)
            return heading.text.strip()
        except Exception:
            return ""
    
    def get_mva(self) -> str:
        """
        Get the displayed MVA number.
        
        Returns:
            The MVA number shown on the page, or empty string if not found
        """
        try:
            mva_element = self.driver.find_element(*self.MVA_DISPLAY)
            return mva_element.text.strip()
        except Exception:
            return ""
    
    def is_submit_button_visible(self) -> bool:
        """
        Check if the Submit Complaint button is visible and clickable.
        
        Returns:
            True if button is present and clickable, False otherwise
        """
        try:
            button = self.wait.until(
                EC.element_to_be_clickable(self.SUBMIT_COMPLAINT_BUTTON)
            )
            return button is not None
        except TimeoutException:
            return False
    
    def click_submit_complaint(self) -> None:
        """
        Click the Submit Complaint button.
        
        Raises:
            TimeoutException: If button is not clickable within timeout period
        """
        button = self.wait.until(
            EC.element_to_be_clickable(self.SUBMIT_COMPLAINT_BUTTON)
        )
        button.click()
    
    def wait_for_page_to_close(self, timeout: int = 45) -> bool:
        """
        Wait for the Additional Information page/dialog to close after submission.
        
        Args:
            timeout: Maximum time to wait for closure (seconds)
        
        Returns:
            True if page closed successfully, False if timeout
        """
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, "div.bp6-dialog, div.bp6-overlay")
                )
            )
            return True
        except TimeoutException:
            return False
