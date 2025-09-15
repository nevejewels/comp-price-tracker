import json
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException

# -----------------------------
# Custom Firefox driver builder
# -----------------------------
def get_firefox_driver(headless=False):
    options = Options()
    options.headless = headless
    options.binary_location = r"C:\Program Files\Mozilla Firefox\firefox.exe"

    profile = webdriver.FirefoxProfile()
    profile.set_preference("permissions.default.image", 2)  # Disable images
    options.profile = profile

    service = Service(r"C:\geckodriver\geckodriver.exe")
    driver = webdriver.Firefox(service=service, options=options)
    driver.implicitly_wait(10)
    return driver

# -----------------------------
# Scraper config
# -----------------------------
URL = "https://www.austenblake.com/design/white-gold-round-diamond-engagement-ring-clrn34901"
DEFAULT_TIMEOUT = 20

@dataclass
class OptionLocator:
    field: str
    code: Optional[str] = None
    id_: Optional[str] = None
    text: Optional[str] = None

# -----------------------------
# Helper functions
# -----------------------------
def wait(driver, by, value, timeout=DEFAULT_TIMEOUT):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))

def visible(driver, by, value, timeout=DEFAULT_TIMEOUT):
    return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((by, value)))

def clickable(driver, by, value, timeout=DEFAULT_TIMEOUT):
    return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, value)))

def scroll_into_view(driver, el):
    driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'center'});", el)

def js_click(driver, el):
    driver.execute_script("arguments[0].click();", el)

def safe_click(driver, el):
    try:
        scroll_into_view(driver, el)
        el.click()
    except (ElementClickInterceptedException, StaleElementReferenceException):
        js_click(driver, el)

def click_if_present(driver, by, value) -> bool:
    try:
        el = WebDriverWait(driver, 3).until(EC.presence_of_element_located((by, value)))
        safe_click(driver, el)
        return True
    except TimeoutException:
        return False

# -----------------------------
# Page interaction steps
# -----------------------------
def accept_cookies(driver):
    click_if_present(driver, By.ID, "onetrust-accept-btn-handler")

def close_claim_container(driver):
    try:
        path_css = 'path[d="M6 6L14 14M6 14L14 6L6 14Z"]'
        path_el = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, path_css)))
        js_click(driver, path_el)
    except TimeoutException:
        pass

def select_li_option(driver, locator: OptionLocator):
    css = f'li[custom_field="{locator.field}"][code="{locator.code}"]'
    try:
        el = WebDriverWait(driver, 6).until(EC.presence_of_element_located((By.CSS_SELECTOR, css)))
        safe_click(driver, el)
    except TimeoutException:
        pass

def select_ring_size_M(driver):
    try:
        toggle = driver.find_element(By.CSS_SELECTOR, ".btn.dropdown-toggle.selectpicker")
        safe_click(driver, toggle)
        m_item = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//span[@class="text" and normalize-space()="M"]'))
        )
        safe_click(driver, m_item)
    except Exception:
        pass

def click_add_to_bag(driver):
    try:
        el = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.add_to_bag"))
        )
        safe_click(driver, el)
    except TimeoutException:
        raise RuntimeError("Could not click Add to bag")

def wait_for_cart_page(driver):
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "checkout-cart")))

def parse_cart_json(driver) -> Dict[str, Any]:
    try:
        cart_div = visible(driver, By.ID, "checkout-cart", timeout=15)
        data_attr = cart_div.get_attribute("data-ga-cart-data")
        if data_attr:
            return json.loads(data_attr)
    except Exception:
        pass
    return {}

# -----------------------------
# Main runner
# -----------------------------
def main():
    driver = get_firefox_driver(headless=False)  # switch to True if you want headless
    try:
        driver.get(URL)

        accept_cookies(driver)
        close_claim_container(driver)

        # PDP selections
        select_li_option(driver, OptionLocator(field="metal_purity", code="GL_18K_W"))
        select_ring_size_M(driver)
        select_li_option(driver, OptionLocator(field="stone_type", code="DI"))
        select_li_option(driver, OptionLocator(field="stone_shape", code="RND"))
        select_li_option(driver, OptionLocator(field="stone_carat", code="50"))
        select_li_option(driver, OptionLocator(field="stone_clarity", code="VVS1"))
        select_li_option(driver, OptionLocator(field="stone_color", code="F"))
        select_li_option(driver, OptionLocator(field="stone_cut", code="EX"))  # Excellent

        click_add_to_bag(driver)
        wait_for_cart_page(driver)

        cart_data = parse_cart_json(driver)
        print(json.dumps(cart_data, indent=2))

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
