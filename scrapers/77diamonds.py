import pandas as pd
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException
from pymongo import MongoClient

# === Setup ===
GECKODRIVER_PATH = r"C:\Users\komal.kumavat\Documents\77diamonds_data\geckodriver.exe"
EXCEL_FILE_PATH = r"C:\Users\komal.kumavat\Documents\77diamonds_data\77diamonds_output_file - 1.csv"

# === MongoDB Setup ===
client = MongoClient("mongodb://localhost:27017/")
db = client["77_diamonds"]
collection = db["15thJuly_data"]

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
        dropdown = Select(driver.find_element(By.CSS_SELECTOR, "select.headerCountriesDropdown"))
        dropdown.select_by_visible_text("United Kingdom")
        print("✅ Location changed to UK")
    except Exception as e:
        print("❌ Failed to change location:", e)

def select_metal(driver, metal):
    metal_mapping = {
        "18KT WG": "white-gold",
        "18KT YG": "yellow-gold",
        "18KT RG": "rose-gold",
        "18K White Gold": "white-gold",
        "18K Yellow Gold": "yellow-gold",
        "18K Rose Gold": "rose-gold",
        "Platinum": "platinum"
    }

    try:
        key = metal_mapping.get(metal.strip())
        if not key:
            print(f"❌ Invalid metal provided: {metal}")
            return

        selector = f"div[data-cy='metal-filter'] div[data-cy='{key}']"
        wait_and_click(driver, By.CSS_SELECTOR, selector)
        print(f"✅ Metal selected: {metal}")
    except Exception as e:
        print(f"❌ Failed to select metal: {metal} → {e}")
def handle_ring_selection_flow(driver):
    try:
        # Check if "Select this setting" button exists
        select_setting_btns = driver.find_elements(By.XPATH, "//button[normalize-space()='Select this setting']")
        if select_setting_btns:
            print("✅ 'Select this setting' button found.")
            wait_and_click(driver, By.XPATH, "//button[normalize-space()='Select this setting']")
            time.sleep(2)

            # After selecting the setting, click "Add diamond"
            wait_and_click(driver, By.CSS_SELECTOR, "button[data-cy='add-diamond-to-setting']")
            print("✅ Clicked 'Add diamond' after selecting setting.")
            return

        # If "Select this setting" is not found, check for "Add diamond"
        direct_add_buttons = driver.find_elements(By.XPATH, "//button[normalize-space()='Add diamond']")
        if direct_add_buttons:
            print("⚠️ 'Add diamond' button found directly — skipping 'Select this setting'.")
            wait_and_click(driver, By.XPATH, "//button[normalize-space()='Add diamond']")
            print("✅ Clicked 'Add diamond' directly.")
            return

        print("❌ Neither 'Select this setting' nor 'Add diamond' button found.")

    except Exception as e:
        print(f"❌ Error handling ring selection → {e}")


def select_stone_type(driver, stone_type):
    mapping = {
        "Natural Diamond": "natural",
        "Lab Diamond": "lab-grown",
        "Coloured": "coloured",
        "Gemstones": "gemstones"
    }
    try:
        value = mapping.get(stone_type.strip(), "natural")
        selector = f"div[data-cy='stoneType-filter'] div[data-cy='{value}']"

        # Wait until the element is present
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        element = driver.find_element(By.CSS_SELECTOR, selector)

        # Scroll into view before clicking
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.5)  # slight pause after scroll
        element.click()

        print(f"✅ Stone type selected: {stone_type}")
    except Exception as e:
        print(f"❌ Failed to select stone type: {stone_type} → {e}")

def select_shape(driver, shape):
    try:
        selector = f"div[data-cy='shapes-filter'] div[data-cy='{shape.lower()}']"
        shape_element = driver.find_element(By.CSS_SELECTOR, selector)
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'}); window.scrollBy(0, 200);", shape_element)
        time.sleep(2)
        wait_and_click(driver, By.CSS_SELECTOR, selector)
        print(f"✅ Shape selected: {shape}")
    except Exception as e:
        print(f"❌ Failed to select shape: {shape} → {e}")

def select_carat_range(driver, min_carat, max_carat):
    try:
        min_carat = "{:.2f}".format(float(min_carat))
        max_carat = "{:.2f}".format(float(max_carat))

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "select[data-cy='select-min']"))
        )

        Select(driver.find_element(By.CSS_SELECTOR, "select[data-cy='select-min']")).select_by_value(str(min_carat))
        Select(driver.find_element(By.CSS_SELECTOR, "select[data-cy='select-max']")).select_by_value(str(max_carat))
        print(f"✅ Carat range set → Min: {min_carat} | Max: {max_carat}")
    except Exception as e:
        print(f"❌ Failed to set carat range → {e}")


def select_color(driver, color_value):
    color_order = ["L", "K", "J", "I", "H", "G", "F", "E", "D"]
    color_value = color_value.strip().upper()

    if color_value not in color_order:
        print(f"❌ Invalid color '{color_value}'")
        return

    index = color_order.index(color_value)
    total_colors = len(color_order)

    try:
        # Step 1: Locate the colour modal specifically
        modal = driver.find_element(By.CSS_SELECTOR, '[data-cy="colour-modal"]')

        # Step 2: Inside modal, get the slider track and slider dots
        slider = modal.find_element(By.CSS_SELECTOR, '[data-cy="colors"] .vue-slider-rail')
        dots = modal.find_elements(By.CSS_SELECTOR, '[data-cy="colors"] .vue-slider-dot')

        if len(dots) != 2:
            print("❌ Expected 2 slider handles, found:", len(dots))
            return

        # Step 3: Get the size of the slider to calculate move offset
        slider_width = slider.size['width']
        step_width = slider_width / (total_colors - 1)

        left_dot = dots[0]
        right_dot = dots[1]

        # Step 4: Use ActionChains to move both slider handles
        actions = ActionChains(driver)

        # Move left handle to the target color
        actions.click_and_hold(left_dot).move_by_offset(step_width * index, 0).release().perform()
        time.sleep(0.5)

        # Move right handle to the same target color
        actions.click_and_hold(right_dot).move_by_offset(-step_width * (total_colors - 1 - index), 0).release().perform()
        time.sleep(0.5)

        print(f"✅ Color '{color_value}' selected.")
    
    except Exception as e:
        print(f"❌ Error selecting color '{color_value}': {e}")
def select_clarity(driver, clarity_value):

    clarity_order = ["SI2", "SI1", "VS2", "VS1", "VVS2", "VVS1", "IF", "FL"]
    clarity_value = clarity_value.strip().upper()

    if clarity_value not in clarity_order:
        print(f"❌ Invalid clarity '{clarity_value}'")
        return

    index = clarity_order.index(clarity_value)
    total_clarity_levels = len(clarity_order)

    try:
        # Locate the specific clarity slider section
        clarity_section = driver.find_element(By.CSS_SELECTOR, '[data-cy="clarity"]')

        # Get the slider track and dots inside clarity section
        slider = clarity_section.find_element(By.CSS_SELECTOR, '.vue-slider-rail')
        dots = clarity_section.find_elements(By.CSS_SELECTOR, '.vue-slider-dot')

        if len(dots) != 2:
            print("❌ Expected 2 clarity slider handles, found:", len(dots))
            return

        slider_width = slider.size['width']
        step_width = slider_width / (total_clarity_levels - 1)

        left_dot = dots[0]
        right_dot = dots[1]

        actions = ActionChains(driver)

        # Move left handle to desired clarity
        actions.click_and_hold(left_dot).move_by_offset(step_width * index, 0).release().perform()
        time.sleep(0.5)

        # Move right handle to same clarity
        actions.click_and_hold(right_dot).move_by_offset(-step_width * (total_clarity_levels - 1 - index), 0).release().perform()
        time.sleep(0.5)

        print(f"✅ Clarity '{clarity_value}' selected.")

    except Exception as e:
        print(f"❌ Error selecting clarity '{clarity_value}': {e}")

def select_cut(driver, cut_value):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.action_chains import ActionChains
    import time

    cut_order = ["GOOD", "VERY GOOD", "EXCELLENT", "CUPID'S IDEAL"]
    cut_value = cut_value.strip().upper()

    if cut_value not in cut_order:
        print(f"❌ Invalid cut value '{cut_value}'")
        return

    index = cut_order.index(cut_value)
    total_cuts = len(cut_order)

    try:
        # Step 1: Locate the unique cut slider section
        cut_section = driver.find_element(By.CSS_SELECTOR, '[data-cy="cut"]')

        # Step 2: Get the slider rail and dots within this section
        slider = cut_section.find_element(By.CSS_SELECTOR, '.vue-slider-rail')
        dots = cut_section.find_elements(By.CSS_SELECTOR, '.vue-slider-dot')

        if len(dots) != 2:
            print("❌ Expected 2 cut slider handles, found:", len(dots))
            return

        slider_width = slider.size['width']
        step_width = slider_width / (total_cuts - 1)

        left_dot = dots[0]
        right_dot = dots[1]

        # Step 3: Move handles using ActionChains
        actions = ActionChains(driver)

        actions.click_and_hold(left_dot).move_by_offset(step_width * index, 0).release().perform()
        time.sleep(0.5)
        actions.click_and_hold(right_dot).move_by_offset(-step_width * (total_cuts - 1 - index), 0).release().perform()
        time.sleep(0.5)

        print(f"✅ Cut '{cut_value}' selected.")

    except Exception as e:
        print(f"❌ Error selecting cut '{cut_value}': {e}")


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
        
 
def extract_diamond_details_on_diamond_page(driver):
    data = {}

    try:
        # Wait for and scroll to the Diamond Details accordion
        accordion = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.accordion.diamond-accordion"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", accordion)
        time.sleep(2)

        # Ensure the section is expanded
        header = accordion.find_element(By.XPATH, ".//h3[contains(text(), 'Diamond Details')]")
        if "chevron-down" in header.find_element(By.TAG_NAME, "i").get_attribute("class"):
            header.click()
            time.sleep(1)

        # Get all diamond-detail rows
        details_container = accordion.find_element(By.CSS_SELECTOR, "div.accordion-diamond-details")
        details = details_container.find_elements(By.CLASS_NAME, "diamond-detail")

        for detail in details:
            try:
                prop = detail.find_element(By.CLASS_NAME, "property").text.strip().rstrip(":")
                value = detail.find_element(By.CLASS_NAME, "value").text.strip()
                data[prop] = value
            except Exception:
                continue  # Ignore any malformed rows

        print("✅ Diamond details extracted:")
        for k, v in data.items():
            print(f"{k}: {v}")

    except Exception as e:
        print(f"❌ Failed to extract diamond details: {e}")

    return data

def extract_ring_and_diamond_info(driver):
    try:
        container = driver.find_element(By.CSS_SELECTOR, "div.item-details")
        driver.execute_script("arguments[0].scrollIntoView(true);", container)
        time.sleep(2)

        # === RING / SETTING DETAILS ===
        try:
            setting_name = container.find_element(By.CSS_SELECTOR, '[data-cy="setting"] h4').text.strip()
        except NoSuchElementException:
            setting_name = ""

        try:
            metal = container.find_element(By.CSS_SELECTOR, '[data-cy="setting"] p').text.strip()
        except NoSuchElementException:
            metal = ""

        try:
            setting_final_price = container.find_element(By.CSS_SELECTOR, '[data-cy="setting"] .itemPrice span:last-child').text.strip()
        except NoSuchElementException:
            setting_final_price = ""

        try:
            setting_original_price = container.find_element(By.CSS_SELECTOR, '[data-cy="setting"] .itemPrice span.product-discount').text.strip()
        except NoSuchElementException:
            setting_original_price = ""

        # === DIAMOND DETAILS ===
        try:
            diamond_block = container.find_element(By.CSS_SELECTOR, '[data-cy="diamond"]')

            diamond_code = diamond_block.get_attribute("data-cy-code") or ""
            carat = diamond_block.get_attribute("data-cy-carat") or ""
            shape = diamond_block.get_attribute("data-cy-shape") or ""
            color = diamond_block.get_attribute("data-cy-colour") or ""
            clarity = diamond_block.get_attribute("data-cy-clarity") or ""
            cut = diamond_block.get_attribute("data-cy-cut") or ""

            try:
                cut_text = diamond_block.find_element(By.XPATH, ".//span[contains(text(),'Cut:')]").text.split(":")[-1].strip()
            except:
                cut_text = ""

            try:
                color_text = diamond_block.find_element(By.XPATH, ".//span[contains(text(),'Colour:')]").text.split(":")[-1].strip()
            except:
                color_text = ""

            try:
                clarity_text = diamond_block.find_element(By.XPATH, ".//span[contains(text(),'Clarity:')]").text.split(":")[-1].strip()
            except:
                clarity_text = ""

            try:
                diamond_price = diamond_block.find_element(By.CSS_SELECTOR, '.itemPrice div').text.strip()
            except:
                diamond_price = ""

        except NoSuchElementException:
            diamond_code = carat = shape = color = clarity = cut = ""
            cut_text = clarity_text = color_text = diamond_price = ""

        # === TOTAL PRICING ===
        try:
            total_price = container.find_element(By.CSS_SELECTOR, ".item-total h3 span._float-right").text.strip()
        except NoSuchElementException:
            total_price = ""

        try:
            vat = container.find_element(By.XPATH, "//h4[contains(text(), 'VAT')]/span").text.strip()
        except NoSuchElementException:
            vat = ""

        try:
            subtotal = container.find_element(By.XPATH, "//h4[contains(text(), 'Subtotal')]/span").text.strip()
        except NoSuchElementException:
            subtotal = ""

        # === DEBUG OUTPUT ===
        print("🔹 Setting:", setting_name)
        print("🔹 Metal:", metal)
        print("🔹 Setting Price:", setting_final_price)
        print("🔹 Original Setting Price:", setting_original_price)
        print("🔹 Diamond Code:", diamond_code)
        print("🔹 Carat:", carat)
        print("🔹 Color:", color_text)
        print("🔹 Clarity:", clarity_text)
        print("🔹 Cut:", cut_text)
        print("🔹 Diamond Price:", diamond_price)
        print("🔹 Subtotal:", subtotal)
        print("🔹 VAT:", vat)
        print("🔹 Total Price:", total_price)

        return {
            "setting_name": setting_name,
            "metal": metal,
            "setting_price": setting_final_price,
            "setting_original_price": setting_original_price,
            "diamond_code": diamond_code,
            "carat": carat,
            "color": color_text,
            "clarity": clarity_text,
            "cut": cut_text,
            "diamond_price": diamond_price,
            "subtotal": subtotal,
            "vat": vat,
            "total_price": total_price
        }

    except Exception as e:
        print(f"❌ Failed to extract product/diamond info: {e}")
        return {}
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

def extract_additional_ring_diamond_info(driver):
    try:
        # Step 1: Scroll into view
        product_details = driver.find_element(By.CSS_SELECTOR, "div.product-details")
        driver.execute_script("arguments[0].scrollIntoView(true);", product_details)
        time.sleep(3)

        # Step 2: Expand accordion if it's collapsed
        try:
            accordion_header = driver.find_element(By.CSS_SELECTOR, ".accordion-item.-opened .accordion-item-label")
            driver.execute_script("arguments[0].scrollIntoView(true);", accordion_header)
            time.sleep(1)
        except:
            print("⚠️ Could not locate accordion header to expand.")

        result = {
            "Setting Style": "",
            "Band Width": "",
            "Claws": "",
            "WedFit": "",
            "Diamond Type": "",
            "Diamond Shape": "",
            "Diamond Code": "",
            "Diamond Carat": "",
            "Diamond Colour": "",
            "Diamond Clarity": ""
        }

        # Step 3: Extract all list items in the product-details section
        ul_items = driver.find_elements(By.CSS_SELECTOR, "div.product-details li")

        for li in ul_items:
            text = li.text.strip()
            if text.lower().startswith("setting:"):
                result["Setting Style"] = text.split(":", 1)[-1].strip()
            elif text.lower().startswith("band width:"):
                result["Band Width"] = text.split(":", 1)[-1].strip()
            elif text.lower().startswith("claws:"):
                result["Claws"] = text.split(":", 1)[-1].strip()
            elif text.lower().startswith("wedfit:"):
                result["WedFit"] = text.split(":", 1)[-1].strip()
            elif text.lower().startswith("type"):
                result["Diamond Type"] = text.split(":", 1)[-1].strip()
            elif text.lower().startswith("shape"):
                result["Diamond Shape"] = text.split(":", 1)[-1].strip()
            elif text.lower().startswith("code"):
                result["Diamond Code"] = text.split(":", 1)[-1].strip()
            elif text.lower().startswith("carat"):
                result["Diamond Carat"] = text.split(":", 1)[-1].strip()
            elif text.lower().startswith("colour") or text.lower().startswith("color"):
                result["Diamond Colour"] = text.split(":", 1)[-1].strip()
            elif text.lower().startswith("clarity"):
                result["Diamond Clarity"] = text.split(":", 1)[-1].strip()

        print("🔎 Extracted from Product Details Accordion:")
        for key, val in result.items():
            print(f"🔸 {key}: {val}")

        return result

    except NoSuchElementException as e:
        print(f"❌ Product details section not found: {e}")
        return {}
    except Exception as e:
        print(f"❌ Unexpected error while extracting product details: {e}")
        return {}

# --- Modified metal selection function to extract product name as well ---
def select_metal(driver, metal):
    metal_mapping = {
        "18KT WG": "white-gold",
        "18KT YG": "yellow-gold",
        "18KT RG": "rose-gold",
        "Platinum": "platinum"
    }

    try:
        key = metal_mapping.get(metal.strip())
        if not key:
            print(f"❌ Invalid metal provided: {metal}")
            return

        selector = f"div[data-cy='metal-filter'] div[data-cy='{key}']"

        # Wait for the element to be present
        element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )

        # Scroll the element into view using JavaScript (more reliable)
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", element)
        time.sleep(1)

        # Ensure it's clickable
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))

        try:
            element.click()
        except ElementClickInterceptedException:
            # Try clicking via JavaScript as fallback
            driver.execute_script("arguments[0].click();", element)

        print(f"✅ Metal selected: {metal}")

    except TimeoutException:
        print(f"❌ Metal option not found for: {metal}")
    except Exception as e:
        print(f"❌ Failed to select metal '{metal}': {e}")
        # === Extract product name after selecting metal ===
        product_name = driver.find_element(By.CSS_SELECTOR, "h1.item-title").text.strip()
        print(f"✅ Metal selected: {metal}")
        print(f"🛍️  Product Name: {product_name}")

    except Exception as e:
        print(f"❌ Failed to select metal: {metal} → {e}")

def save_to_mongodb(row_data, extracted_data, status="success", error_message=""):
    """
    Save all extracted data to MongoDB with timestamp
    """
    try:
        # Create comprehensive document with all data
        document = {
            # Original row data
            "serial_number": row_data.get("SN", ""),
            "original_url": row_data.get("Website URL", ""),
            "input_metal": row_data.get("Metal", ""),
            "input_stone_type": row_data.get("Stone Type", ""),
            "input_stone_shape": row_data.get("Stone Shape", ""),
            "input_stone_carat": row_data.get("Stone Carat", ""),
            "input_color": row_data.get("Color", ""),
            "input_clarity": row_data.get("Clarity", ""),
            "input_cut": row_data.get("Cut", ""),
            
            # Extracted product information
            "product_name": extracted_data.get("product_name", ""),
            
            # Ring/Setting information
            "setting_name": extracted_data.get("ring_diamond_info", {}).get("setting_name", ""),
            "setting_metal": extracted_data.get("ring_diamond_info", {}).get("metal", ""),
            "setting_price": extracted_data.get("ring_diamond_info", {}).get("setting_price", ""),
            "setting_original_price": extracted_data.get("ring_diamond_info", {}).get("setting_original_price", ""),
            
            # Diamond information from main extraction
            "diamond_code": extracted_data.get("ring_diamond_info", {}).get("diamond_code", ""),
            "diamond_carat": extracted_data.get("ring_diamond_info", {}).get("carat", ""),
            "diamond_color": extracted_data.get("ring_diamond_info", {}).get("color", ""),
            "diamond_clarity": extracted_data.get("ring_diamond_info", {}).get("clarity", ""),
            "diamond_cut": extracted_data.get("ring_diamond_info", {}).get("cut", ""),
            "diamond_price": extracted_data.get("ring_diamond_info", {}).get("diamond_price", ""),
            
            # Pricing information
            "subtotal": extracted_data.get("ring_diamond_info", {}).get("subtotal", ""),
            "vat": extracted_data.get("ring_diamond_info", {}).get("vat", ""),
            "total_price": extracted_data.get("ring_diamond_info", {}).get("total_price", ""),
            
            # Additional ring details
            "setting_style": extracted_data.get("additional_info", {}).get("Setting Style", ""),
            "band_width": extracted_data.get("additional_info", {}).get("Band Width", ""),
            "claws": extracted_data.get("additional_info", {}).get("Claws", ""),
            "wedfit": extracted_data.get("additional_info", {}).get("WedFit", ""),
            
            # Additional diamond details from accordion
            "diamond_details": extracted_data.get("diamond_details", {}),
            
            # Metadata
            "scraping_status": status,
            "error_message": error_message,
            "scraped_at": datetime.now(),
            "scraped_timestamp": datetime.now().isoformat(),
            "date_scraped": datetime.now().strftime("%Y-%m-%d"),
            "time_scraped": datetime.now().strftime("%H:%M:%S")
        }
        
        # Insert into MongoDB
        result = collection.insert_one(document)
        print(f"✅ Data saved to MongoDB with ID: {result.inserted_id}")
        
        return result.inserted_id
        
    except Exception as e:
        print(f"❌ Failed to save data to MongoDB: {e}")
        return None
    
def process_row(row, idx):
    # Extract and sanitize input
    metal = row["metal"]
    stone_type = row["stone_type"]
    shape = row["stone_shape"]
    carat = str(row["stone_carat"])
    color = row["color"]
    clarity = row["clarity"]
    cut = row["cut"]
    url = row["product_url"].split("&step=item-diamond")[0]

    print(f"\n===== Processing Row {idx + 1} =====")
    print(f"🌐 Navigating to: {url}")

    driver = init_driver()
    try:
        driver.get(url)
        time.sleep(10)

        # === Interaction Steps ===
        close_popup(driver)
        time.sleep(10)

        change_location_to_uk(driver)
        time.sleep(10)

        select_metal(driver, metal)
        time.sleep(10)
        handle_ring_selection_flow(driver)
        time.sleep(10)
        select_stone_type(driver, stone_type)
        time.sleep(10)
        select_shape(driver, shape)
        time.sleep(10)
        select_carat_range(driver, carat, carat)
        time.sleep(10)
        select_color(driver, color)
        time.sleep(10)
        select_clarity(driver, clarity)
        time.sleep(10)
        select_cut(driver, cut)
        time.sleep(10)
        select_first_diamond_and_add(driver)
        time.sleep(10)

        # === Data Extraction ===
        base_info = extract_ring_and_diamond_info(driver)
        additional_info = extract_additional_ring_diamond_info(driver)
        # diamond_page_info = extract_diamond_details_on_diamond_page(driver)

        # Merge all data
        scraped_data = {
        "metal": metal,
        "stone_type": stone_type,
        "shape": shape,
        "carat": carat,
        "color": color,
        "clarity": clarity,
        "cut": cut,
        "product_url": url,
        "ring_diamond_info": base_info,
        "additional_info": additional_info,
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

        # Insert to MongoDB
        collection.insert_one(scraped_data)
        print("✅ Data inserted into MongoDB")

    except Exception as e:
        print(f"❌ Error processing row {idx + 1} → {e}")
    finally:
        driver.quit()


# === Main Function ===
def main():
    df = pd.read_csv(EXCEL_FILE_PATH)
    for idx, row in df.iterrows():
        process_row(row, idx)


if __name__ == "__main__":
    main()
