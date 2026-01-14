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
import psycopg2

# === Setup ===
GECKODRIVER_PATH = r"C:\Users\komal.kumavat\Documents\77diamonds_data\geckodriver.exe"
EXCEL_FILE_PATH = r"C:\Users\komal.kumavat\Documents\77diamonds_data\77diamonds_input-file(script).xlsx"

# === PostgreSQL Setup ===
DB_CONFIG = {
    'host': 'localhost',
    'database': 'scrapping',
    'port':5432,
    'user': 'postgres',
    'password': 'root'
}

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

def handle_ring_selection_flow(driver):
    try:
        select_setting_btns = driver.find_elements(By.XPATH, "//button[normalize-space()='Select this setting']")
        if select_setting_btns:
            print("✅ 'Select this setting' button found.")
            wait_and_click(driver, By.XPATH, "//button[normalize-space()='Select this setting']")
            time.sleep(2)
            wait_and_click(driver, By.CSS_SELECTOR, "button[data-cy='add-diamond-to-setting']")
            print("✅ Clicked 'Add diamond' after selecting setting.")
            return
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
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        element = driver.find_element(By.CSS_SELECTOR, selector)
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.5)
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
        modal = driver.find_element(By.CSS_SELECTOR, '[data-cy="colour-modal"]')
        slider = modal.find_element(By.CSS_SELECTOR, '[data-cy="colors"] .vue-slider-rail')
        dots = modal.find_elements(By.CSS_SELECTOR, '[data-cy="colors"] .vue-slider-dot')
        if len(dots) != 2:
            print("❌ Expected 2 slider handles, found:", len(dots))
            return
        slider_width = slider.size['width']
        step_width = slider_width / (total_colors - 1)
        left_dot = dots[0]
        right_dot = dots[1]
        actions = ActionChains(driver)
        actions.click_and_hold(left_dot).move_by_offset(step_width * index, 0).release().perform()
        time.sleep(0.5)
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
        clarity_section = driver.find_element(By.CSS_SELECTOR, '[data-cy="clarity"]')
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
        actions.click_and_hold(left_dot).move_by_offset(step_width * index, 0).release().perform()
        time.sleep(0.5)
        actions.click_and_hold(right_dot).move_by_offset(-step_width * (total_clarity_levels - 1 - index), 0).release().perform()
        time.sleep(0.5)
        print(f"✅ Clarity '{clarity_value}' selected.")
    except Exception as e:
        print(f"❌ Error selecting clarity '{clarity_value}': {e}")

def select_cut(driver, cut_value):
    cut_order = ["GOOD", "VERY GOOD", "EXCELLENT", "CUPID'S IDEAL"]
    cut_value = cut_value.strip().upper()
    if cut_value not in cut_order:
        print(f"❌ Invalid cut value '{cut_value}'")
        return
    index = cut_order.index(cut_value)
    total_cuts = len(cut_order)
    try:
        cut_section = driver.find_element(By.CSS_SELECTOR, '[data-cy="cut"]')
        slider = cut_section.find_element(By.CSS_SELECTOR, '.vue-slider-rail')
        dots = cut_section.find_elements(By.CSS_SELECTOR, '.vue-slider-dot')
        if len(dots) != 2:
            print("❌ Expected 2 cut slider handles, found:", len(dots))
            return
        slider_width = slider.size['width']
        step_width = slider_width / (total_cuts - 1)
        left_dot = dots[0]
        right_dot = dots[1]
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
        diamond_img = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tr.main-row img.diamondImage"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", diamond_img)
        diamond_img.click()
        print("✅ Clicked first diamond image.")
        add_to_ring_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-cy='add-stone-to-selected-ring']"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_to_ring_btn)
        add_to_ring_btn.click()
        print("✅ 'Add to Ring' button clicked on ring page.")
    except Exception as e:
        print(f"❌ Failed during diamond selection or adding to ring → {e}")

def extract_diamond_details_on_diamond_page(driver):
    data = {}
    try:
        accordion = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.accordion.diamond-accordion"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", accordion)
        time.sleep(2)
        header = accordion.find_element(By.XPATH, ".//h3[contains(text(), 'Diamond Details')]")
        icon_class = header.find_element(By.TAG_NAME, "i").get_attribute("class")
        if icon_class and "chevron-down" in icon_class:
            header.click()
            time.sleep(1)
        details_container = accordion.find_element(By.CSS_SELECTOR, "div.accordion-diamond-details")
        details = details_container.find_elements(By.CLASS_NAME, "diamond-detail")
        for detail in details:
            try:
                prop = detail.find_element(By.CLASS_NAME, "property").text.strip().rstrip(":")
                value = detail.find_element(By.CLASS_NAME, "value").text.strip()
                data[prop] = value
            except Exception:
                continue
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
        product_details = driver.find_element(By.CSS_SELECTOR, "div.product-details")
        driver.execute_script("arguments[0].scrollIntoView(true);", product_details)
        time.sleep(3)
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
        element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", element)
        time.sleep(1)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
        try:
            element.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", element)
        print(f"✅ Metal selected: {metal}")
    except TimeoutException:
        print(f"❌ Metal option not found for: {metal}")
    except Exception as e:
        print(f"❌ Failed to select metal '{metal}': {e}")
        try:
            product_name = driver.find_element(By.CSS_SELECTOR, "h1.item-title").text.strip()
            print(f"✅ Metal selected: {metal}")
            print(f"🛍️  Product Name: {product_name}")
        except Exception:
            pass

def create_table_if_not_exists():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        # Use more appropriate datatypes for numeric fields
        create_table_query = """
        CREATE TABLE IF NOT EXISTS stg_price_77diamonds_scrape_new (
            id SERIAL PRIMARY KEY,
            website TEXT,
            product_url TEXT,
            category TEXT,
            sub_category TEXT,
            collection_no TEXT,
            variant_no TEXT,
            metal TEXT,
            stone_type TEXT,
            stone_shape TEXT,
            stone_carat NUMERIC,
            color TEXT,
            clarity TEXT,
            cut TEXT,
            product_title TEXT,
            metal_price NUMERIC,
            stone_price NUMERIC,
            final_price NUMERIC,
            updated_date TIMESTAMP,
            setting_title TEXT,
            setting_price NUMERIC,
            diamond_title TEXT,
            product_description TEXT,
            additional_attributes TEXT,
            metal_t TEXT,
            stone_type_t TEXT,
            stone_shape_t TEXT,
            clarity_t TEXT,
            cut_t TEXT,
            metal_price_e NUMERIC,
            stone_price_e NUMERIC,
            final_price_e NUMERIC,
            updated_date_t TIMESTAMP,
            additional_title TEXT,
            final_title TEXT
        );
        """
        cur.execute(create_table_query)
        conn.commit()
        print("✅ Table created or already exists")
    except Exception as e:
        print(f"❌ Error creating table: {e}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

def _to_numeric(val):
    try:
        if val is None or val == "":
            return None
        return float(str(val).replace(",", "").replace("£", "").strip())
    except Exception:
        return None

def _to_timestamp(val):
    try:
        if not val:
            return None
        return datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None

def save_to_postgresql(data):
    print(data)
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        insert_query = """
        INSERT INTO stg_price_77diamonds_scrape (
            website, product_url, category, sub_category, collection_no, variant_no,
            metal, stone_type, stone_shape, stone_carat, color, clarity, cut,
            product_title, metal_price, stone_price, final_price, updated_date,
            setting_title, setting_price, diamond_title, product_description,
            additional_attributes, metal_t, stone_type_t, stone_shape_t, clarity_t,
            cut_t, metal_price_e, stone_price_e, final_price_e, updated_date_t,
            additional_title, final_title
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        # Prepare data tuple in correct order and convert types
        data_tuple = (
            data.get('website', ''),
            data.get('product_url', ''),
            data.get('category', ''),
            data.get('sub_category', ''),
            data.get('collection_no', ''),
            data.get('variant_no', ''),
            data.get('metal', ''),
            data.get('stone_type', ''),
            data.get('stone_shape', ''),
            _to_numeric(data.get('stone_carat', None)),
            data.get('color', ''),
            data.get('clarity', ''),
            data.get('cut', ''),
            data.get('product_title', ''),
            _to_numeric(data.get('metal_price', None)),
            _to_numeric(data.get('stone_price', None)),
            _to_numeric(data.get('final_price', None)),
            _to_timestamp(data.get('updated_date', '')),
            data.get('setting_title', ''),
            _to_numeric(data.get('setting_price', None)),
            data.get('diamond_title', ''),
            data.get('product_description', ''),
            data.get('additional_attributes', ''),
            data.get('metal_t', ''),
            data.get('stone_type_t', ''),
            data.get('stone_shape_t', ''),
            data.get('clarity_t', ''),
            data.get('cut_t', ''),
            _to_numeric(data.get('metal_price_e', None)),
            _to_numeric(data.get('stone_price_e', None)),
            _to_numeric(data.get('final_price_e', None)),
            _to_timestamp(data.get('updated_date_t', '')),
            data.get('additional_title', ''),
            data.get('final_title', '')
        )
        cur.execute(insert_query, data_tuple)
        conn.commit()
        print("✅ Data inserted into PostgreSQL")
    except Exception as e:
        print("❌ Error saving to PostgreSQL: {}".format(e))
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

def process_row(row, idx):
    # Extract and sanitize input
    print(row,'row')
    metal = row.get("metal", "")
    stone_type = row.get("stone_type", "")
    shape = row.get("stone_shape", "")
    carat = row.get("stone_carat", "")
    color = row.get("color", "")
    clarity = row.get("clarity", "")
    cut = row.get("cut", "")
    url = str(row.get("product_url", "")).split("&step=item-diamond")[0]

    print(f"\n===== Processing Row {idx + 1} =====")
    print(f"🌐 Navigating to: {url}")

    driver = init_driver()
    try:
        driver.get(url)
        time.sleep(10)
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
        base_info = extract_ring_and_diamond_info(driver)
        additional_info = extract_additional_ring_diamond_info(driver)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        scraped_data = {
            "website": "77diamonds.com",
            "product_url": url,
            "category":row.get("category", ""),
            "sub_category":row.get("sub_category", ""),
            "collection_no":row.get("collection_no", ""),
            "variant_no": "",
            "metal": metal,
            "stone_type": stone_type,
            "stone_shape": shape,
            "stone_carat": carat,
            "color": color,
            "clarity": clarity,
            "cut": cut,
            "product_title": base_info.get("setting_name", ""),
            "metal_price": base_info.get("setting_price", ""),
            "stone_price": base_info.get("diamond_price", ""),
            "final_price": base_info.get("total_price", ""),
            "updated_date": now_str,
            "setting_title": base_info.get("setting_name", ""),
            "setting_price": base_info.get("setting_price", ""),
            "diamond_title": f"{base_info.get('carat', '')}ct {base_info.get('color', '')} {base_info.get('clarity', '')}",
            "product_description": "",
            "additional_attributes": str(additional_info),
            "metal_t": "",
            "stone_type_t": "",
            "stone_shape_t": "",
            "clarity_t": "",
            "cut_t": "",
            "metal_price_e": "",
            "stone_price_e": "",
            "final_price_e": "",
            "updated_date_t": now_str,
            "additional_title": "",
            "final_title": ""
        }
        save_to_postgresql(scraped_data)
    except Exception as e:
        print(f"❌ Error processing row {idx + 1} → {e}")
    finally:
        driver.quit()

def main():
    create_table_if_not_exists()
    df = pd.read_csv(EXCEL_FILE_PATH)
    for idx, row in df.iterrows():
        process_row(row, idx)

if __name__ == "__main__":
    main()
