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
