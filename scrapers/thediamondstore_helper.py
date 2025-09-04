from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
import time
import re


def cookie_consent(driver):
    try:
        # Wait until the Accept button is clickable and click it
        accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Accept']"))
        )
        accept_button.click()
        print("✅ Cookie consent accepted.")
    except Exception as e:
        print(f"❌ Could not click accept button: {e}")

def metal_click_view_button(driver, metal_name):
    """
    Clicks the VIEW button for the given metal type.
    :param driver: Selenium WebDriver instance
    :param metal_name: e.g., "18K Yellow Gold" or "Platinum"
    """
    # try:
    #     # Wait until the element with the given metal name is visible
    #     metal_element = WebDriverWait(driver, 10).until(
    #         EC.presence_of_element_located((By.XPATH, f"//dt/span[normalize-space(text())='{metal_name}']"))
    #     )
    #     print(f"Found metal element: {metal_element.text}")

    #     # Find the VIEW button in the same row as the metal
    #     view_button = metal_element.find_element(By.XPATH, "./ancestor::dl//a[contains(text(),'VIEW')]")
        
    #     # Click the button
    #     # view_button.click()
    #     driver.execute_script("arguments[0].click();", view_button)
    #     print(f"Clicked VIEW for: {metal_name}")

    # except Exception as e:
    #     print(f"Could not click VIEW for '{metal_name}': {e}")

    # try:
    #     # Find all metals on the page
    #     metals = driver.find_elements(By.XPATH, "//dt/span")
    #     available_metals = [m.text.strip() for m in metals]

    #     if metal_name not in available_metals:
    #         print(f"VIEW button not found for '{metal_name}' (Available metals: {available_metals})")
    #         return  # stop here, don't click anything

    #     # Wait for the specific metal element
    #     metal_element = WebDriverWait(driver, 10).until(
    #         EC.presence_of_element_located(
    #             (By.XPATH, f"//dt/span[normalize-space(text())='{metal_name}']")
    #         )
    #     )

    #     # Find VIEW button in the same row
    #     view_button = metal_element.find_element(
    #         By.XPATH, "./ancestor::dl//a[contains(text(),'VIEW')]"
    #     )

    #     # Click using JS (more reliable than .click())
    #     driver.execute_script("arguments[0].click();", view_button)
    #     print(f"Clicked VIEW for: {metal_name}")

    # except Exception as e:
    #     print(f"Could not click VIEW for '{metal_name}': {e}")


    # Locate the SETTING section
    setting_section = WebDriverWait(driver, 10).until(EC.presence_of_element_located((
        By.XPATH, "//div[contains(@class,'choices__section')][.//h5[normalize-space(text())='SETTING']]"
    )))

    # Find all products inside this section
    products = setting_section.find_elements(By.XPATH, ".//dl[contains(@class,'choices__product')]")

    # Loop through each product row and match metal name
    for product in products:
        name = product.find_element(By.XPATH, ".//dt/span").text.strip()
        if name.lower() == metal_name.lower():
            view_button = product.find_element(By.XPATH, ".//a[contains(text(),'VIEW')]")
            view_button.click()
            print(f"✅ Clicked VIEW for {metal_name}")
            return True

    print(f"❌ Metal '{metal_name}' not found in SETTING section.")
    return False


def click_view_by_section(driver, section_name, option_name, timeout=10):
    """
    Clicks the VIEW button for a given option inside a specified section (e.g., SETTING, CLARITY).
    
    :param driver: Selenium WebDriver instance
    :param section_name: Section title (e.g., "SETTING", "CLARITY")
    :param option_name: The option value to match (e.g., "18K White Gold", "G/VS1")
    :param timeout: Max wait time in seconds
    """
    wait = WebDriverWait(driver, timeout)

    # Step 1: Find the section by its heading
    section = wait.until(EC.presence_of_element_located((
        By.XPATH, f"//div[contains(@class,'choices__section')][.//h5[normalize-space(text())='{section_name}']]"
    )))
    # print("section = ", section)
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", section)

    # Step 2: Get all product rows inside this section
    products = section.find_elements(By.XPATH, ".//dl[contains(@class,'choices__product')]")
    print("products = ", len(products))

    # Step 3: Loop through rows and find matching option
    for product in products:
        # print("product = ", product)
        name = product.find_element(By.XPATH, ".//dt/span").text.strip()
        print("name = ", name)
        if name.lower() == option_name.lower():
            view_button = product.find_element(By.XPATH, ".//a[contains(text(),'VIEW')]")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", view_button)
            time.sleep(1)
            view_button.click()
            # time.sleep(1)
            # view_button.click()
            print(f"✅ Clicked VIEW for '{option_name}' in section '{section_name}'")
            return True

    print(f"❌ Option '{option_name}' not found in section '{section_name}'")
    return False

def diamond_choices_button(driver):
    diamond_choices_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[normalize-space()='DIAMOND CHOICES']"))
    )
    print("diamond_choices_btn = ", diamond_choices_btn)
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", diamond_choices_btn)
    time.sleep(3)
    diamond_choices_btn.click()
    print("diamond_choices_btn clicked ")
    print("clicked diamond choices")
    time.sleep(2)

def diamond_choices_button1(driver):
    diamond_choices_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//div[normalize-space()='DIAMOND CHOICES']"))
    )
    print("diamond_choices_btn = ", diamond_choices_btn)
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", diamond_choices_btn)
    time.sleep(3)
    diamond_choices_btn.click()
    print("clicked 1st time")
    time.sleep(3)
    diamond_choices_btn.click()
    print("clicked 2nd time")
    time.sleep(2)