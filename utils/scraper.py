from .logger import setup_logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
)
from typing import List, Optional, Any
import time


class ScraperUtils:
    def __init__(
            self,
            max_retries: int = 3,
            timeout: int = 10,
            logger_name: str = "Scraper Utilities"
    ):
        self.max_retries = max_retries
        self.timeout = timeout
        self.logger = setup_logger(
            logger_name=logger_name
        )

    def wait_and_find_element(
            self,
            driver,
            by: By | str,
            value: str,
            timeout: Optional[int] = None
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
        by: By | str,
        value: str,
        timeout: Optional[int] = None
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
