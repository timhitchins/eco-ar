# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.webdriver import WebDriver
# from selenium.webdriver.chrome.service import Service
# from selenium.common.exceptions import TimeoutException, WebDriverException
# import tempfile
# import shutil
# import time
# from typing import Optional
# import logging


# class SeleniumResource:
#     def __init__(self, max_retries: int = 3, connect_timeout: int = 30):
#         self._driver: Optional[WebDriver] = None
#         self._download_dir_path: Optional[str] = None
#         self._max_retries = max_retries
#         self._connect_timeout = connect_timeout
#         self._logger = logging.getLogger(__name__)

#     def setup_for_execution(self) -> None:
#         """
#         Sets up the Chrome WebDriver with retries on failure.
#         Raises TimeoutException if all retries fail.
#         """
#         attempts = 0
#         last_exception = None

#         while attempts < self._max_retries:
#             try:
#                 self._download_dir_path = tempfile.mkdtemp()

#                 # Create and configure the Chrome service
#                 service = Service(
#                     executable_path="/usr/local/bin/chromedriver")
#                 service.start()

#                 # Create and configure Chrome options
#                 options = self._set_chrome_options(self._download_dir_path)

#                 # Initialize the WebDriver with timeout
#                 self._driver = webdriver.Chrome(
#                     service=service,
#                     options=options
#                 )

#                 # Set page load timeout
#                 self._driver.set_page_load_timeout(self._connect_timeout)

#                 # Test the connection
#                 self._driver.get('about:blank')

#                 return  # Success - exit the retry loop

#             except (TimeoutException, WebDriverException) as e:
#                 last_exception = e
#                 attempts += 1
#                 self._logger.warning(f"Attempt {attempts} failed: {str(e)}")

#                 # Clean up failed attempt
#                 self._cleanup_failed_attempt()

#                 if attempts < self._max_retries:
#                     # Wait before retrying
#                     time.sleep(2 ** attempts)  # Exponential backoff

#         # If we get here, all attempts failed
#         raise TimeoutException(
#             f"Failed to initialize Chrome WebDriver after {
#                 self._max_retries} attempts. "
#             f"Last error: {str(last_exception)}"
#         )

#     def _cleanup_failed_attempt(self) -> None:
#         """Clean up resources after a failed attempt."""
#         if self._driver:
#             try:
#                 self._driver.quit()
#             except Exception as e:
#                 self._logger.warning(f"Error cleaning up WebDriver: {str(e)}")
#             self._driver = None

#         if self._download_dir_path:
#             try:
#                 shutil.rmtree(self._download_dir_path)
#             except Exception as e:
#                 self._logger.warning(
#                     f"Error cleaning up download directory: {str(e)}")
#             self._download_dir_path = None

#     def teardown_after_execution(self) -> None:
#         """Safely tears down the Selenium WebDriver and cleans up resources."""
#         if self._driver:
#             try:
#                 self._driver.quit()
#             except Exception as e:
#                 self._logger.warning(f"Error quitting WebDriver: {str(e)}")
#             self._driver = None

#         if self._download_dir_path:
#             try:
#                 shutil.rmtree(self._download_dir_path)
#             except Exception as e:
#                 self._logger.warning(
#                     f"Error removing download directory: {str(e)}")
#             self._download_dir_path = None

#     def _set_chrome_options(self, download_dir: str) -> Options:
#         """Sets Chrome options with improved stability settings."""
#         chrome_options = Options()

#         # Basic options for headless operation
#         chrome_options.add_argument("--no-sandbox")
#         chrome_options.add_argument("--headless")
#         chrome_options.add_argument("--disable-dev-shm-usage")

#         # Additional stability options
#         chrome_options.add_argument("--disable-gpu")
#         chrome_options.add_argument("--disable-software-rasterizer")
#         chrome_options.add_argument("--disable-extensions")
#         chrome_options.add_argument("--disable-features=NetworkService")
#         chrome_options.add_argument("--window-size=1920,1080")
#         chrome_options.add_argument("--disable-browser-side-navigation")

#         # Configure preferences
#         chrome_prefs = {
#             "profile.default_content_settings": {"images": 2},
#             "download.default_directory": download_dir,
#             "download.prompt_for_download": False,
#             "download.directory_upgrade": True,
#             "safebrowsing.enabled": True
#         }
#         chrome_options.experimental_options["prefs"] = chrome_prefs

#         return chrome_options

#     @property
#     def driver(self) -> WebDriver:
#         """Returns the WebDriver instance."""
#         if not self._driver:
#             raise RuntimeError(
#                 "WebDriver not initialized. Call setup_for_execution() first.")
#         return self._driver

#     @property
#     def download_dir_path(self) -> str:
#         """Returns the download directory path."""
#         if not self._download_dir_path:
#             raise RuntimeError(
#                 "Download directory not initialized. Call setup_for_execution() first.")
#         return self._download_dir_path
