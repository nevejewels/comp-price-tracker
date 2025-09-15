from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

GECKODRIVER_PATH = r"C:\Users\komal.kumavat\Documents\77diamonds_data\geckodriver.exe"

def init_driver():
    service = Service(GECKODRIVER_PATH)
    options = webdriver.FirefoxOptions()
    options.add_argument("--start-maximized")
    return webdriver.Firefox(service=service, options=options)

def wait_and_click(driver, by, value, timeout=15):
    WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, value))).click()

def close_popup(driver):
    try:
        wait_and_click(driver, By.CSS_SELECTOR, "i.icon77.icon77-exit", 10)
        print("✅ Closed popup")
    except:
        print("❌ No popup or already closed")

def change_location_to_uk(driver):
    try:
        wait_and_click(driver, By.CLASS_NAME, "lblcode")
        time.sleep(10)
        dropdown = driver.find_element(By.CSS_SELECTOR, "select.headerCountriesDropdown")
        for option in dropdown.find_elements(By.TAG_NAME, "option"):
            if option.text.strip() == "United Kingdom":
                option.click()
                break
        print("✅ Location changed to UK")
    except Exception as e:
        print(f"❌ Failed to change location: {e}")

def select_first_diamond_and_add(driver):
    try:
        # Wait for the diamond image
        diamond_img = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tr.main-row img.diamondImage"))
        )
        # Scroll into view and click the image
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", diamond_img)
        diamond_img.click()
        print("✅ Clicked first diamond image.")

        # Wait for redirect and "Add to Ring" button to appear
        add_to_ring_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-cy='add-stone-to-selected-ring']"))
        )

        # Scroll to "Add to Ring" button and click
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_to_ring_btn)
        add_to_ring_btn.click()
        print("✅ 'Add to Ring' button clicked on ring page.")

    except Exception as e:
        print(f"❌ Failed during diamond selection or adding to ring → {e}")
def test_workflow():
    url = "https://www.77diamonds.com/engagement-rings/contour-solitaire-round-cut-diamond-18k-white-gold/p/794?step=item-diamond"
    driver = init_driver()
    try:
        driver.get(url)
        time.sleep(10)

        close_popup(driver)
        time.sleep(5)

        change_location_to_uk(driver)
        time.sleep(10)

        select_first_diamond_and_add(driver)
        time.sleep(5)

        

    except Exception as e:
        print(f"❌ Unexpected error during test: {e}")
    finally:
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    test_workflow()
