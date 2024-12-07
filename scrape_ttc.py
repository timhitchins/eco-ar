from utils.dataclass import (
    IssuuItem,
    TTCContent,
)
from utils.scraper import WebScraper
from utils.selenium_resource import SeleniumResource
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    StaleElementReferenceException,
    NoSuchElementException,
)
from urllib.parse import urlparse
import logging
from typing import Iterable
from itertools import chain
import os
import pickle
import time


def get_periodical_content_by_page(
    page_url: str,
    client=SeleniumResource(),
    scraper=WebScraper(),
) -> Iterable[TTCContent] | None:
    try:

        client.setup_for_execution()
        driver = client.driver
        # Navigate to tag page

        driver.get(page_url)

        # Get content results
        content_results = scraper.wait_and_find_elements(
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
                    scraper.logger.warning(
                        "No title found for content result")
                    continue

                title_text = result_title.text
                scraper.logger.info(f"Found title for result {title_text}")

                # Get links with images
                links_with_images = result.find_elements(
                    By.CSS_SELECTOR,
                    "a:has(img)",
                )
                if not links_with_images:
                    scraper.logger.warning("No links with images")
                    continue

                ttc_issuus = []
                for link_img in links_with_images:
                    issuu_href = scraper.get_attribute_safely(
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

                    issuu_img_src = scraper.get_attribute_safely(
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
        scraper.logger.error(f"An error occurred: {str(e)}")
        return None
    finally:
        client.teardown_after_execution()


def scrape_ttc_periodicals(
    root_page_url: str = "https://thetalonconspiracy.com/category/periodicals/page/",
    pages: int = 10,
) -> Iterable[TTCContent] | None:
    try:
        periodical_urls = [f"{root_page_url}{
            page_num}" for page_num in range(1, pages+1)]

        periodical_content = [get_periodical_content_by_page(
            url) for url in periodical_urls]

        periodicals = chain(*periodical_content)  # type: ignore[arg-type]
        return list(periodicals)
    except Exception as e:
        # TODO: Add logging or convert scraper def to class
        print(e)
        return None


def download_issuu(

    issuu_url: str,
    issuudownload_url: str = "https://issuudownload.com/",
    client=SeleniumResource(),
    scraper=WebScraper(),
):
    client.setup_for_execution()
    driver = client.driver
    # Navigate to tag page

    driver.get(issuudownload_url)
    input = scraper.wait_and_find_element(
        driver,
        By.CSS_SELECTOR,
        '#DocumentUrl'
    )

    input.clear()
    input.send_keys(issuu_url)

    submit_button = scraper.wait_and_find_element(
        driver,
        By.CSS_SELECTOR,
        'button.btn.btn-primary'
    )

    submit_button.click()
    time.sleep(5)

    save_all_button = scraper.wait_and_find_element(
        driver,
        By.ID,
        'btPdfDownload'
    )

    save_all_button.click()
    time.sleep(5)

    download_button = scraper.wait_and_find_element(
        driver,
        By.CSS_SELECTOR,
        'a.btn.btn-outline-success'
    )

    download_link = download_button.get_attribute('href')

    return download_link

    ###################
if __name__ == "__main__":
    pickle_file = "./periodicals.pkl"
    if os.path.exists(pickle_file):
        with open(pickle_file, "rb") as file:
            periodicals = pickle.load(file)

    else:
        periodicals = scrape_ttc_periodicals()
        with open(pickle_file, 'wb') as file:  # type: ignore[assignment]
            pickle.dump(periodicals, file)

        # download issuus
    download_issuu(
        issuu_url=periodicals[0].ttc_items[0].issuu_url
    )
