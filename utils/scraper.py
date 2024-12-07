#  regular imports
from .logger import setup_logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
)
from typing import List, Optional, Any
import time


class WebScraper:
    def __init__(self, max_retries: int = 3, timeout: int = 10):
        self.max_retries = max_retries
        self.timeout = timeout
        self.logger = setup_logging()

    def wait_and_find_element(
            self,
            driver,
            by: By,
            value: str,
            timeout: Optional[int] = None,
    ) -> Optional[Any]:
        """Safely wait for and find an element with retries."""
        timeout = timeout or self.timeout
        for attempt in range(self.max_retries):
            try:
                return WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
            except StaleElementReferenceException:
                if attempt == self.max_retries - 1:
                    self.logger.error("")
                time.sleep(1)
            except TimeoutException:
                self.logger.error(
                    f"Timeout waiting for element {by}={value}")
                return None
        return None

    def wait_and_find_elements(
        self,
        driver,
        by: By,
        value: str,
        timeout: Optional[int] = None,
    ) -> List[Any]:
        """Safely wait for and find elements with retries."""
        timeout = timeout or self.timeout
        for attempt in range(self.max_retries):
            try:
                elements = WebDriverWait(driver, timeout).until(
                    EC.presence_of_all_elements_located((by, value))
                )
                return elements
            except StaleElementReferenceException:
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(1)
            except TimeoutException:
                self.logger.warning(
                    f"Timeout waiting for elements {by}={value}")
                return []
        return []

    def get_attribute_safely(
        self,
        element,
        attribute: str
    ) -> Optional[str]:
        """Safely get an attribute from an element with retries."""
        for attempt in range(self.max_retries):
            try:
                return element.get_attribute(attribute)
            except StaleElementReferenceException:
                if attempt == self.max_retries - 1:
                    return None
                time.sleep(1)
        return None

    def click_download_button(
        self,
        driver,
        timeout: Optional[int] = None,
        wait_time: int = 5
    ) -> bool:
        """
        Click the download button with data-tooltip="Download" and wait for download to complete.

        Args:
            driver: Selenium WebDriver instance
            timeout: Optional timeout override (uses instance timeout if not specified)
            wait_time: Time to wait after clicking for download to complete (default: 5 seconds)

        Returns:
            bool: True if download button was found and clicked successfully, False otherwise
        """
        try:
            # Find download button using data-tooltip attribute
            download_button = self.wait_and_find_element(
                driver,
                By.CSS_SELECTOR,  # type: ignore[arg-type]
                '[data-tooltip="Download"]',
                timeout
            )

            if not download_button:
                self.logger.warning("Download button not found")
                return False

            # Check if button is clickable
            if not download_button.is_enabled():
                self.logger.warning("Download button is not enabled")
                return False

            # Scroll button into view to ensure it's clickable
            driver.execute_script(
                "arguments[0].scrollIntoView(true);", download_button)
            time.sleep(1)  # Brief pause after scrolling

            # Click the download button
            download_button.click()
            self.logger.info("Download button clicked successfully")

            # Wait for specified time to allow download to complete
            time.sleep(wait_time)

            return True

        except Exception as e:
            self.logger.error(f"Error during download: {str(e)}")
            return False
