from utils.selenium_resource import SeleniumResource, TimeoutException


def test_selenium_resource():
    # Create and initialize the Selenium resource
    selenium = SeleniumResource(max_retries=3, connect_timeout=30)
    try:
        selenium.setup_for_execution()
        # Use the driver...
        selenium.driver.get("https://example.com")
    except TimeoutException as e:
        print(f"Failed to initialize Selenium: {e}")
    finally:
        selenium.teardown_after_execution()


# try:
#     ttc_url = "https://thetalonconspiracy.com/"

#     client = SeleniumResource()
#     client.setup_for_execution()
#     href_list = []
#     # Navigate to the webpage
#     client.driver.get(ttc_url)

#     # Wait for the sidebar to be present
#     sidebar = WebDriverWait(client.driver, 10).until(
#         EC.presence_of_element_located((By.ID, "sidebarleft"))
#     )

#     # Find all anchor tags within list items in the sidebar
#     # Using XPath to find all <a> tags that are descendants of <li> elements
#     sidebar_tag_links = sidebar.find_elements(
#         By.XPATH,
#         # This finds all <a> tags with href attributes within <li> elements
#         ".//li//a[@href]"
#     )

#     # Extract href attributes
#     ttc_tags = []
#     for link in sidebar_tag_links:
#         client.driver.implicitly_wait(5)
#         tag_url = link.get_attribute('href')
#         parsed_url = urlparse(tag_url).path
#         tag_name = parsed_url.strip("/").split("/")[-1]

#         client.driver.get(tag_url)
#         content_results = WebDriverWait(client.driver, 10).until(
#             EC.presence_of_all_elements_located(
#                 (By.CLASS_NAME, "results_content"))
#         )

#         ttc_content = []
#         for result in content_results:
#             result_title = result.find_element(By.TAG_NAME, "h1")
#             links_with_images = result.find_elements(
#                 By.CSS_SELECTOR, "a:has(img)")

#             ttc_issuus = []
#             for link_img in links_with_images:
#                 issuu_href = link_img.get_attribute("href")
#                 issuu_img_src = link_img.find_element(
#                     By.TAG_NAME, "img").get_attribute("src")
#                 issu_name = urlparse(issuu_img_src).path.strip(
#                     "/").split("/")[-1]
#                 issuu_item = IssuuItem(
#                     issuu_name=issu_name,
#                     issuu_url=issuu_href,
#                     issuu_img_src=issuu_img_src
#                 )
#                 ttc_issuus.append(issuu_item)
#             ttc_content_result = TTCContent(
#                 ttc_content_title=result_title.text,
#                 ttc_items=ttc_issuus.copy(),
#             )
#             ttc_issuus.clear()
#             ttc_content.append(ttc_content_result)
#         ttc_tag = TTCTag(
#             ttc_tag_name=tag_name,
#             ttc_tag_url=tag_url,
#             ttc_tag_content=ttc_content.copy(),
#         )
#         ttc_content.clear()
#         ttc_tags.append(ttc_tag)
#         client.driver.back()
#         sidebar = WebDriverWait(client.driver, timeout=10).until(
#             EC.presence_of_element_located((By.ID, "sidebarleft"))
#         )
#     ttc_tags.clear()

# except Exception as e:
#     print(f"An error occurred: {e}")
# finally:
#     client.teardown_after_execution()
