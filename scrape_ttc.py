from urllib3.util.retry import Retry
from requests.exceptions import RequestException, HTTPError, ConnectionError, Timeout
from requests.adapters import HTTPAdapter
from utils.dataclass import (
    IssuuItem,
    TTCContent,
)
from utils.scraper import ScraperUtils
from utils.selenium_resource import SeleniumResource
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    StaleElementReferenceException,
    NoSuchElementException,
)
from urllib.parse import urlparse
import logging
from typing import List, Optional
from itertools import chain
import os
import pickle
from tqdm import tqdm
import time
import requests
import multiprocessing


class TTCScraper:
    def __init__(
        self,
        client=SeleniumResource(),
        utils=ScraperUtils(logger_name="Periodical Scraper"),
        pickle_dir: str = "./.run_cache"
    ):
        self._client = client
        self._client.setup_for_execution()
        self._utils = utils
        self._pickle_dir = pickle_dir

    def _load_periodical_page_content(
        self,
        pickle_name: str = "periodicals.pkl"
    ) -> List[TTCContent] | None:
        pickle_path = f"{self._pickle_dir}./{pickle_name}"
        if os.path.exists(pickle_path):
            with open(pickle_path, "rb") as file:
                periodicals = pickle.load(file)
                return periodicals
        else:
            return None

    def _dump_periodical_page_content(
        self,
        pickle_name: str = "periodicals.pkl"
    ) -> str:
        pickle_path = f"{self._pickle_dir}./{pickle_name}"
        with open(pickle_path, "wb") as file:
            pickle.dump(self._periodicals, file)
        return pickle_path

    def _get_periodical_content_by_page(
        self,
        page_url: str
    ) -> List[TTCContent] | None:
        try:
            driver = self._client.driver
            # Navigate to tag page

            driver.get(page_url)

            # Get content results
            content_results = self._utils.wait_and_find_elements(
                driver,
                By.CLASS_NAME,
                "results_content"
            )

            ttc_content = []
            for result in content_results:
                try:
                    # Get the Category type. Include only periodicals.

                    category_labels = [category.text for category in result.find_elements(
                        By.CSS_SELECTOR,
                        "h3 a[rel]"
                    )]

                    if "PERIODICALS" not in category_labels:
                        continue

                    # Get title from the current result element
                    result_title = result.find_element(By.TAG_NAME, "h1")
                    if not result_title:
                        self._utils.logger.warning(
                            "No title found for content result")
                        continue

                    title_text = result_title.text
                    self._utils.logger.info(
                        f"Found title for result {title_text}")

                    # Get links with images
                    links_with_images = result.find_elements(
                        By.CSS_SELECTOR,
                        "a:has(img)",
                    )
                    if not links_with_images:
                        self._utils.logger.warning("No links with images")
                        continue

                    ttc_issuus = []
                    for link_img in links_with_images:
                        issuu_href = self._utils.get_attribute_safely(
                            link_img, "href")
                        parsed_issuu_href = urlparse(issuu_href)
                        issuu_url = f"{
                            parsed_issuu_href.scheme}://{parsed_issuu_href.netloc}{parsed_issuu_href.path}"

                        img_element = link_img.find_element(
                            By.TAG_NAME,
                            "img",
                        )
                        if not img_element:
                            continue

                        issuu_img_src = self._utils.get_attribute_safely(
                            img_element, "src")
                        if not issuu_href or not issuu_img_src:
                            continue

                        issu_name = urlparse(issuu_img_src).path.strip(
                            "/").split("/")[-1]
                        issuu_item = IssuuItem(
                            issuu_name=issu_name,
                            issuu_url=issuu_url,
                            issuu_img_src=issuu_img_src
                        )
                        ttc_issuus.append(issuu_item)

                    ttc_content_result = TTCContent(
                        ttc_content_title=result_title.text,
                        ttc_items=ttc_issuus.copy()
                    )
                    ttc_content.append(ttc_content_result)

                except StaleElementReferenceException:
                    continue
                except NoSuchElementException:
                    logging.warning("Missing h1 tag in result.")
                    continue
                except StaleElementReferenceException:
                    logging.warning(
                        "Result became stale, skipping")
                    continue
            return ttc_content
        except Exception as e:
            self._utils.logger.error(f"An error occurred: {str(e)}")
            return None
        finally:
            self._client.teardown_after_execution()

    def scrape_ttc_periodicals(
        self,
        root_page_url: str = "https://thetalonconspiracy.com/category/periodicals/page/",
        pages: int = 10,
    ) -> List[TTCContent] | None:
        try:

            loaded_periodicals = self._load_periodical_page_content()

            if not loaded_periodicals:

                periodical_urls = [f"{root_page_url}{
                    page_num}" for page_num in range(1, pages+1)]

                self._periocical_url: List[str] = periodical_urls

                periodical_content = [self._get_periodical_content_by_page(
                    url) for url in periodical_urls]

                periodicals: List[TTCContent] = list(chain(*periodical_content)  # type: ignore[arg-type]
                                                     )
                self._periodicals = periodicals
                self._dump_periodical_page_content()
            else:
                self._periodicals = loaded_periodicals
            return self._periodicals
        except Exception as e:
            self._utils.logger.error(f"TTC periodical scrape failed: {e}")
            raise

# Generic functions Issuu Items


def download_issuu(
    issuu_item: IssuuItem,
    issuudownload_url: str = "https://issuudownload.com/",
    issuu_pdfs_dir: str = "/app/issuu_pdfs/",
    worker: Optional[int] = None
) -> IssuuItem:
    try:
        if not issuu_item.issuu_download_link and not issuu_item.issuu_filepath:
            utils = ScraperUtils(
                logger_name=f"Issuu Downloads for worker: {worker}")
            client = SeleniumResource()
            client.setup_for_execution()

            client.driver.get(issuudownload_url)

            # Find and input the URL
            input_field = utils.wait_and_find_element(
                client.driver,
                By.CSS_SELECTOR,
                '#DocumentUrl',
                timeout=50,
            )
            if not input_field:
                raise ValueError("Input field not found")

            input_field.clear()
            input_field.send_keys(issuu_item.issuu_url)

            # Click the submit button
            submit_button = utils.wait_and_find_element(
                client.driver,
                By.CSS_SELECTOR,
                'button.btn.btn-primary'
            )
            if not submit_button:
                raise ValueError("Submit button not found")
            submit_button.click()
            time.sleep(5)

            # Click the save all button
            save_all_button = utils.wait_and_find_element(
                client.driver,
                By.ID,
                'btPdfDownload'
            )
            if not save_all_button:
                raise ValueError("Save All button not found")
            save_all_button.click()
            time.sleep(5)

            # Get the download link
            download_button = utils.wait_and_find_element(
                client.driver,
                By.CSS_SELECTOR,
                'a.btn.btn-outline-success'
            )
            if not download_button:
                raise ValueError("Download button not found")

            download_link = download_button.get_attribute('href')
            if not download_link:
                raise ValueError("Download link is empty")

            # Save the download link to the item
            utils.logger.info(f"Download link obtained: {download_link}")
            # update IssuuItem dataclass
            issuu_item.issuu_download_link = download_link

            session = requests.Session()
            retries = Retry(
                total=5,
                backoff_factor=.05,
                # Retry on server errors
                status_forcelist=[500, 502, 503, 504],
                allowed_methods=["GET"],  # Retry only GET requests
            )
            session.mount("http://", HTTPAdapter(max_retries=retries))
            session.mount("https://", HTTPAdapter(max_retries=retries))

            try:

                if not os.path.exists(issuu_pdfs_dir):
                    os.makedirs(issuu_pdfs_dir)

                # Perform the GET request
                response = session.get(download_link, timeout=10)
                response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)

                # Extract the filename
                filename = os.path.basename(
                    urlparse(issuu_item.issuu_url).path)
                filename = f"{filename}.pdf"
                filepath = os.path.join(issuu_pdfs_dir, filename)

                # Save the file
                with open(filepath, 'wb') as file:
                    file.write(response.content)

                # Update the IssuuItem dataclass
                issuu_item.issuu_filepath = filepath
                return issuu_item

            except (HTTPError, ConnectionError, Timeout) as e:
                raise Exception(f"Failed to download PDF from: {
                                download_link} due to: {e}")
            except RequestException as e:
                raise Exception(
                    f"An unexpected error occurred while downloading PDF: {e}")
            finally:
                if session:
                    session.close()
        else:
            return issuu_item
    except Exception as e:
        if client:
            client._cleanup_failed_attempt()
        utils.logger.error(f"Error processing {issuu_item.issuu_url}: {e}")
        return issuu_item  # Return the item even if failed
    finally:
        if client and client.driver:
            try:
                client.driver.quit()
            except Exception as quit_error:
                utils.logger.warning(
                    f"Failed to quit WebDriver: {quit_error}")
        client.teardown_after_execution()


def download_issuu_pdfs(issuu_items: List[IssuuItem]) -> List[IssuuItem]:
    max_processes = 8
    num_processes = min(multiprocessing.cpu_count(), max_processes)
    pool = multiprocessing.Pool(processes=num_processes)

    processed_items = []
    with tqdm(total=len(issuu_items), desc="Downloading PDFs") as pbar:
        results = []

        for idx, item in enumerate(issuu_items):
            result = pool.apply_async(
                download_issuu, args=(item, "https://issuudownload.com/", "/app/issuu_pdfs", idx))
            results.append(result)

        for result in results:
            try:
                processed_item = result.get()  # Get the result from the async process
                processed_items.append(processed_item)
            except Exception as e:
                print(f"Error processing item: {e}")
            pbar.update(1)

    # Close the pool
    pool.close()
    pool.join()

    return processed_items  # Return the list of processed items


    ###################
if __name__ == "__main__":

    scraper = TTCScraper()
    periodicals = scraper.scrape_ttc_periodicals()

    if periodicals:
        updated_ttc_content: List[TTCContent] = []
        for content in periodicals:
            updated_issuus = download_issuu_pdfs(content.ttc_items)
            content.ttc_items = updated_issuus
            updated_ttc_content.append(content)
        scraper._periodicals = updated_ttc_content
        scraper._dump_periodical_page_content(pickle_name="ttc_content.pkl")
