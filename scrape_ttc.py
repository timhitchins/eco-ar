import os
import pickle
import time
from pathlib import Path
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional
from tqdm import tqdm
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from requests.exceptions import HTTPError, ConnectionError, Timeout

from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
from utils.logger import setup_logger
from utils.dataclass import IssuuItem, TTCContent
from utils.scraper import ScraperUtils
from utils.selenium_resource import SeleniumResource


class TTCScraper:
    """Scrapes periodicals and manages cached content."""

    def __init__(
        self,
        client: SeleniumResource = SeleniumResource(),
        utils: ScraperUtils = ScraperUtils(logger_name="Periodical Scraper"),
        pickle_dir: str = "./.run_cache",
    ):
        self._client = client
        self._utils = utils
        self._pickle_dir = Path(pickle_dir)
        self._pickle_dir.mkdir(parents=True, exist_ok=True)
        self._logger = setup_logger(logger_name="TTC Scraper")

    def _load_cached_content(self, pickle_name: str) -> Optional[List[TTCContent]]:
        pickle_path = self._pickle_dir / pickle_name
        if pickle_path.exists():
            with pickle_path.open("rb") as file:
                return pickle.load(file)
        return None

    def _dump_cached_content(self, content: List[TTCContent], pickle_name: str) -> None:
        pickle_path = self._pickle_dir / pickle_name
        with pickle_path.open("wb") as file:
            pickle.dump(content, file)

    def _get_periodical_content_by_page(self, page_url: str) -> List[TTCContent]:
        driver = self._client.driver
        try:
            driver.get(page_url)
            content_results = self._utils.wait_and_find_elements(
                driver, By.CLASS_NAME, "results_content")
            ttc_content = []

            for result in content_results:
                try:
                    category_labels = [
                        category.text for category in result.find_elements(By.CSS_SELECTOR, "h3 a[rel]")
                    ]
                    if "PERIODICALS" not in category_labels:
                        continue

                    title_element = result.find_element(By.TAG_NAME, "h1")
                    title_text = title_element.text if title_element else "Unknown Title"
                    links_with_images = result.find_elements(
                        By.CSS_SELECTOR, "a:has(img)")

                    ttc_issuus = [
                        IssuuItem(
                            issuu_name=urlparse(img.get_attribute(
                                "src")).path.split("/")[-1],
                            issuu_url=link.get_attribute("href"),
                            issuu_img_src=img.get_attribute("src"),
                        )
                        for link in links_with_images if (img := link.find_element(By.TAG_NAME, "img"))
                    ]

                    ttc_content.append(TTCContent(
                        ttc_content_title=title_text, ttc_items=ttc_issuus))
                except (StaleElementReferenceException, NoSuchElementException):
                    self._logger.warning(
                        "Element reference lost or missing during processing.")

            return ttc_content
        except Exception as e:
            self._logger.error(f"Failed to scrape {page_url}: {e}")
            self._client._cleanup_failed_attempt()
            return []
        finally:
            self._client.teardown_after_execution()

    def scrape_periodicals(self, root_url: str, pages: int, cache_file: str) -> List[TTCContent]:
        cached_content = self._load_cached_content(cache_file)
        if cached_content:
            return cached_content

        periodical_urls = [f"{root_url}{
            page_num}" for page_num in range(1, pages + 1)]
        all_content = []

        for url in tqdm(periodical_urls, desc="Scraping Periodicals"):
            page_content = self._get_periodical_content_by_page(url)
            all_content.extend(page_content)

        self._dump_cached_content(all_content, cache_file)
        return all_content


def download_issuu(
    issuu_item: IssuuItem,
    issuudownload_url: str = "https://issuudownload.com/",
    issuu_pdfs_dir: str = "/app/issuu_pdfs_dev/",
) -> IssuuItem:
    """Download PDF content from Issuu using Selenium and requests.

    Args:
        issuu_item (IssuuItem): The Issuu item containing URL and metadata.
        issuudownload_url (str): The URL of the Issuu downloader.
        issuu_pdfs_dir (str): Directory to save downloaded PDFs.
        worker (Optional[int]): Identifier for multiprocessing workers.

    Returns:
        IssuuItem: Updated IssuuItem with download link and filepath.
    """
    utils = ScraperUtils(logger_name="Issuu Download")
    client = SeleniumResource()
    session = None
    logger = setup_logger(logger_name="Download Issuu")

    try:
        if not issuu_item.issuu_download_link and not issuu_item.issuu_filepath:
            # Setup Selenium client and navigate to the Issuu downloader page.
            client.setup_for_execution()
            driver = client.driver
            driver.get(issuudownload_url)

            # Locate and fill the input field with the Issuu URL.
            input_field = utils.wait_and_find_element(
                driver,
                By.CSS_SELECTOR,
                '#DocumentUrl',
                timeout=50
            )
            if not input_field:
                raise ValueError(
                    "Input field not found on Issuu downloader page.")
            input_field.clear()
            input_field.send_keys(issuu_item.issuu_url)

            # Locate and click the submit button.
            submit_button = utils.wait_and_find_element(
                driver,
                By.CSS_SELECTOR,
                'button.btn.btn-primary'
            )
            if not submit_button:
                raise ValueError("Submit button not found.")
            submit_button.click()
            time.sleep(15)

            # Locate and click the "Save All" button.
            save_all_button = utils.wait_and_find_element(
                driver,
                By.ID,
                'btPdfDownload',
                timeout=15,
            )
            if not save_all_button:
                logger.error("Save All button not found.")
                raise ValueError("Save All button not found.")
            save_all_button.click()
            time.sleep(30)

            # Retrieve the download link.
            download_button = utils.wait_and_find_element(
                driver,
                By.CSS_SELECTOR,
                'a.btn.btn-outline-success',
                timeout=30,
            )
            if not download_button:
                logger.error("Download button not found.")
                raise ValueError("Download button not found.")
            download_link = download_button.get_attribute('href')
            if not download_link:
                logger.error("Download link is empty.")
                raise ValueError("Download link is empty.")

            issuu_item.issuu_download_link = download_link
            logger.info(f"Download link obtained: {download_link}")

            # Download the file using the Requests library.
            session = requests.Session()
            retries = Retry(
                total=5,
                backoff_factor=0.5,
                status_forcelist=[500, 502, 503, 504],
                allowed_methods=["GET"]
            )
            session.mount("http://", HTTPAdapter(max_retries=retries))
            session.mount("https://", HTTPAdapter(max_retries=retries))

            if not os.path.exists(issuu_pdfs_dir):
                os.makedirs(issuu_pdfs_dir)

            response = session.get(download_link, timeout=10)
            response.raise_for_status()

            # Generate file name and save the file.
            filename = os.path.basename(
                urlparse(issuu_item.issuu_url).path) + ".pdf"
            filepath = os.path.join(issuu_pdfs_dir, filename)
            with open(filepath, 'wb') as file:
                file.write(response.content)

            issuu_item.issuu_filepath = filepath
            logger.info(f"File saved successfully at: {filepath}")

    except (HTTPError, ConnectionError, Timeout) as e:
        logger.error(f"Failed to download PDF: {e}")
        client._cleanup_failed_attempt()

        raise Exception(
            f"Download failed for {issuu_item.issuu_url}. Reason: {e}"
        )

    except Exception as e:
        logger.error(f"Unexpected error during Issuu download: {e}")
        client._cleanup_failed_attempt()
        raise

    finally:
        # Cleanup Selenium client.
        try:
            client.teardown_after_execution()
            # Close the session.
            if session:
                session.close()

        except Exception as quit_error:
            logger.warning(f"Failed to quit WebDriver: {quit_error}")
        return issuu_item


def download_issuu_pdfs(issuu_items: List[IssuuItem], max_workers: int = 8) -> List[IssuuItem]:
    logger = setup_logger(logger_name="Dowload Issuu PDFs")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(download_issuu, item): item for item in issuu_items}
        results = []

        for future in tqdm(as_completed(futures), total=len(issuu_items), desc="Downloading PDFs"):
            try:
                results.append(future.result())
            except Exception as e:
                logger.error(f"Error downloading an item: {e}")
        return results


if __name__ == "__main__":
    scraper = TTCScraper()
    root_url = "https://thetalonconspiracy.com/category/periodicals/page/"
    cache_file = "periodicals.pkl"
    pages_to_scrape = 10

    periodicals = scraper.scrape_periodicals(
        root_url, pages_to_scrape, cache_file
    )

    content_with_pdfs: List[TTCContent] = []
    for content in periodicals:
        content.ttc_items = download_issuu_pdfs(content.ttc_items)
        content_with_pdfs.append(content)

    scraper._dump_cached_content(
        content_with_pdfs, "ttc_content_with_pdfs.pkl")
