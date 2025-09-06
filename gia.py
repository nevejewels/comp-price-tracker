from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
# Firefox options
options = Options()
# Uncomment below to run in headless mode
# options.headless = True

# Initialize Firefox driver
driver = webdriver.Firefox(options=options)

try:
    # Open the GIA report page
    report_url = "https://www.gia.edu/report-check?locale=en_US&reportno=2357144346"
    driver.get(report_url)
    time.sleep(2)  # Wait for the page to load  
    driver.execute_script("document.body.style.zoom='40%'")


    # Wait for iframe that contains the cookie banner
    iframe = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe"))
    )
    driver.switch_to.frame(iframe)
    print("🔎 Switched to cookie consent iframe")

    # Now wait for and click the Accept All button
    accept_button = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "a.acceptAllButtonLower"))
    )
    accept_button.click()
    print("✅ Clicked 'Accept All' button")

    # Switch back to main page
    driver.switch_to.default_content()

    # Wait until the page content loads
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    print("Page title:", driver.title)


    time.sleep(2)  # Give some time for the modal to appear
    # Wait for and click the "Close" button
    close_button = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.ID, "gwt-debug-close_id"))
    )
    close_button.click()
    print("✅ Clicked 'Close' button")

    # Verify modal disappears
    WebDriverWait(driver, 10).until_not(
        EC.presence_of_element_located((By.ID, "gwt-debug-close_id"))
    )
    print("🎉 Cookie settings modal closed")





finally:
    driver.quit()
