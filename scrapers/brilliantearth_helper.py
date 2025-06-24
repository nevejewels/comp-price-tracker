from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
import time
import re


def accept_cookies(driver):
    try:
        cookie_accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        cookie_accept_button.click()
    except Exception:
        pass  # silent if cookie banner not found

def get_title_price(driver, logger):
    try:
        # rightside_parent = driver.find_element(By.CLASS_NAME, "js-pdp-sidebar-inner")
        rightside_parent = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "js-pdp-sidebar-inner"))
        )
        title_element = rightside_parent.find_element(By.CSS_SELECTOR, "h1.heading")
        title = title_element.text.strip()
        logger.info(f"Title extracted: {title}")

        price_element = rightside_parent.find_element(
            By.CSS_SELECTOR, "span[ge-data-converted-full-price]"
        )
        raw_price = price_element.text.strip()
        price = re.sub(r"[^\d.]", "", raw_price)
        logger.info(f"Price extracted: {price}")

        return title, price
    except Exception as e:
        logger.error(f"Error extracting title: {e}")
        return None

def click_metal_option(driver, logger, metal_to_select):
    try:
        # metal_elements = driver.find_elements(By.CSS_SELECTOR, "a.metal-around")
        metal_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.metal-around"))
        )
        for metal in metal_elements:
            try:
                span = metal.find_element(By.CSS_SELECTOR, "span.tm-sr-only")
                metal_name = span.text.strip()
                if metal_name == metal_to_select:
                    logger.info(f"Clicking on metal: {metal_name}")
                    metal.click()
                    return
            except Exception as e:
                logger.warning(f"Could not read a metal name: {e}")
        logger.warning(f"Metal '{metal_to_select}' not found on page.")
    except Exception as e:
        logger.error(f"Error selecting metal: {e}")

def click_style_option(driver, logger, style_name):
    try:
        # style_options = driver.find_elements(By.CSS_SELECTOR, "a.center_stone_img")
        style_options = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.center_stone_img"))
        )
        logger.info(f"Found {len(style_options)} style options.")
        for option in style_options:
            name = option.get_attribute("data-name").strip()
            logger.info(f"Checking style option: {name}")
            if name.lower() == style_name.lower():
                logger.info(f"Clicking style: {name}")
                option.click()
                return
        logger.warning(f"Style '{style_name}' not found.")
    except Exception as e:
        logger.error(f"Error clicking style option: {e}")

def click_stone_shape(driver, logger, shape_name):
    try:
        shape_list = driver.find_elements(By.CSS_SELECTOR, 'ul#js_shape > li')
        logger.info(f"Found {len(shape_list)} shape options.")

        for li in shape_list:
            data_shape = li.get_attribute("data-shape").strip()
            logger.info(f"Checking shape: {data_shape}")
            
            if data_shape.lower() == shape_name.lower():
                link = li.find_element(By.CSS_SELECTOR, "a.custom-control-a")
                link.click()
                logger.info(f"✅ Clicked on diamond shape: {data_shape}")
                return
        logger.warning(f"❌ Diamond shape '{shape_name}' not found.")
    except Exception as e:
        logger.error(f"❌ Error clicking diamond shape '{shape_name}': {e}")

def click_stonetype_diamond(driver, logger, origin_type):
    origin_type = origin_type.strip().lower()
    
    try:
        if origin_type == "natural":
            driver.find_element(By.ID, "natural_option").click()
            logger.info("✅ Clicked on 'Natural' diamond origin.")
        elif origin_type in ["lab", "lab grown"]:
            driver.find_element(By.ID, "lab_option").click()
            logger.info("✅ Clicked on 'Lab Grown' diamond origin.")
        else:
            logger.warning(f"❌ Unknown diamond origin: {origin_type}")
    except Exception as e:
        logger.error(f"❌ Error clicking diamond origin '{origin_type}': {e}")

def set_carat_range(driver, logger, min_value="1.0", max_value="1.0"):
    try:
        max_input = driver.find_element(By.ID, "max_carat")
        print(f"Max input: {max_input}")
        max_input.send_keys(Keys.CONTROL + "a")
        max_input.send_keys(Keys.DELETE)
        time.sleep(1) 
        max_input.send_keys(str(max_value))
        max_input.send_keys(Keys.ENTER)

        min_input = driver.find_element(By.ID, "min_carat")
        print(f"Min input: {min_input}")
        min_input.send_keys(Keys.CONTROL + "a")
        min_input.send_keys(Keys.DELETE)
        time.sleep(1) 
        min_input.send_keys(str(min_value))
        min_input.send_keys(Keys.ENTER)

        logger.info(f"✅ Carat range set: Min = {min_value}, Max = {max_value}")
    except Exception as e:
        logger.error(f"❌ Failed to set carat range: {e}")


from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time

# def select_cut(driver, logger, cut_level):
#     cut_map = {
#         "Fair": 0,
#         "Good": 1,
#         "Very Good": 2,
#         "Ideal": 3,
#         "Super Ideal": 4
#     }

#     cut_level = cut_level.strip().title()
#     if cut_level not in cut_map:
#         logger.error(f"❌ Invalid cut level '{cut_level}'. Valid options: {list(cut_map.keys())}")
#         return

#     try:
#         handle_parent = driver.find_element(By.ID, "Cut")
#         handles = handle_parent.find_elements(By.CLASS_NAME, "noUi-handle")

#         if len(handles) != 2:
#             logger.error("❌ Could not find both slider handles.")
#             return

#         min_handle = handles[0]
#         max_handle = handles[1]

#         slider = driver.find_element(By.ID, "js_cut_slider")
#         slider_width = slider.size['width']
#         step_width = slider_width / (len(cut_map))

#         actions = ActionChains(driver)

#         target_x = int(cut_map[cut_level] * step_width)
#         print(f"Target X position for cut level '{cut_level}': {target_x}")

#         # # Move min handle to 0 (safe left reset)
#         # actions.click_and_hold(min_handle).move_by_offset(-step_width * 5, 0).release().perform()
#         # time.sleep(0.3)

#         # Move max handle to far right (safe right reset)
#         actions.click_and_hold(max_handle).move_by_offset(step_width * 5, 0).release().perform()
#         time.sleep(0.3)

#         # Now move both to target_x
#         actions.click_and_hold(min_handle).move_by_offset(target_x, 0).release().perform()
#         time.sleep(0.3)

#         actions.click_and_hold(max_handle).move_by_offset(target_x - slider_width, 0).release().perform()

#         logger.info(f"✅ Selected cut level: {cut_level}")
#     except Exception as e:
#         logger.error(f"❌ Failed to select cut level '{cut_level}': {e}")

def select_cut(driver, logger, cut_level):
    cut_map = {
        "Fair": 0,
        "Good": 1,
        "Very Good": 2,
        "Ideal": 3,
        "Super Ideal": 4
    }

    cut_level = cut_level.strip().title()
    if cut_level not in cut_map:
        logger.error(f"❌ Invalid cut level '{cut_level}'. Valid options: {list(cut_map.keys())}")
        return

    try:
        # Scroll into view
        slider = driver.find_element(By.ID, "js_cut_slider")
        driver.execute_script("arguments[0].scrollIntoView(true);", slider)

        # Set both handles to the same index (for single cut selection)
        js_script = f"""
            let slider = document.getElementById('js_cut_slider').noUiSlider;
            if (slider) {{
                slider.set([{cut_map[cut_level]}, {cut_map[cut_level]}]);
            }}
        """
        driver.execute_script(js_script)

        logger.info(f"✅ Cut level '{cut_level}' set successfully via JS.")
    except Exception as e:
        logger.error(f"❌ Failed to set cut level '{cut_level}' via JS: {e}")


def select_color(driver, logger, color_value):
    color_map = {
        "J": 0,
        "I": 1,
        "H": 2,
        "G": 3,
        "F": 4,
        "E": 5,
        "D": 6
    }

    color_value = color_value.strip().upper()
    if color_value not in color_map:
        logger.error(f"❌ Invalid color '{color_value}'. Valid options: {list(color_map.keys())}")
        return

    try:
        # Scroll to slider
        slider = driver.find_element(By.ID, "js_color_slider")
        driver.execute_script("arguments[0].scrollIntoView(true);", slider)

        # Set both handles to the same index to isolate selection
        js_script = f"""
            let slider = document.getElementById('js_color_slider').noUiSlider;
            if (slider) {{
                slider.set([{color_map[color_value]}, {color_map[color_value]}]);
            }}
        """
        driver.execute_script(js_script)

        logger.info(f"✅ Color '{color_value}' set successfully via JS.")
    except Exception as e:
        logger.error(f"❌ Failed to set color '{color_value}' via JS: {e}")


def select_clarity(driver, logger, clarity_value):
    clarity_map = {
        "SI2": 0,
        "SI1": 1,
        "VS2": 2,
        "VS1": 3,
        "VVS2": 4,
        "VVS1": 5,
        "IF": 6,
        "FL": 7
    }

    clarity_value = clarity_value.strip().upper()
    if clarity_value not in clarity_map:
        logger.error(f"❌ Invalid clarity level '{clarity_value}'. Valid options: {list(clarity_map.keys())}")
        return

    try:
        # Scroll to Clarity slider
        slider = driver.find_element(By.ID, "js_clarity_slider")
        driver.execute_script("arguments[0].scrollIntoView(true);", slider)

        # Set both slider handles to select only the chosen clarity
        js_script = f"""
            let slider = document.getElementById('js_clarity_slider').noUiSlider;
            if (slider) {{
                slider.set([{clarity_map[clarity_value]}, {clarity_map[clarity_value]}]);
            }}
        """
        driver.execute_script(js_script)

        logger.info(f"✅ Clarity '{clarity_value}' set successfully via JS.")
    except Exception as e:
        logger.error(f"❌ Failed to set clarity '{clarity_value}' via JS: {e}")


# def click_first_select_diamond(driver, logger):
#     try:
#         # Wait until the diamond product grid is present
#         WebDriverWait(driver, 10).until(
#             EC.presence_of_element_located((By.ID, "diamonds_search_gallery"))
#         )

#         # Find all diamond products
#         products = driver.find_elements(By.CSS_SELECTOR, "#diamonds_search_gallery .per-product")

#         if not products:
#             logger.error("❌ No diamond products found.")
#             return

#         first_product = products[0]

#         # Within the first product, find the "Select Diamond" button
#         select_button = first_product.find_element(By.CSS_SELECTOR, ".js-select-diamond-cta")
#         # driver.execute_script("arguments[0].scrollIntoView(true);", select_button)
#         select_button.click()

#         logger.info("✅ Clicked on the 'Select Diamond' button of the first product.")

#     except Exception as e:
#         logger.error(f"❌ Failed to click on the first 'Select Diamond' button: {e}")

def click_first_select_diamond(driver, logger):

    first_button = driver.find_elements(By.XPATH, "//a[contains(text(), 'Select Diamond')]")[0]
    time.sleep(5)
    first_button.click()
    logger.info("✅ Clicked on the first 'Select Diamond' button.")

    # try:
    #     # Find all <a> tags
    #     anchor_tags = driver.find_elements(By.TAG_NAME, "a")
    #     print(f"Found {len(anchor_tags)} anchor tags on the page.")

    #     # Filter to anchors with exact text "Select Diamond"
    #     select_links = [a for a in anchor_tags if a.text.strip() == "Select Diamond"]
    #     print(f"Found {len(select_links)} 'Select Diamond' links.")

    #     if not select_links:
    #         logger.error("❌ No 'Select Diamond' links found on the page.")
    #         return

    #     # Scroll to and click the first one
    #     driver.execute_script("arguments[0].scrollIntoView(true);", select_links[0])
    #     time.sleep(1)
    #     print("done scrolling to the first 'Select Diamond' link.")
    #     select_links[0].click()

    #     logger.info("✅ Clicked on the first 'Select Diamond' link.")
    # except Exception as e:
    #     logger.error(f"❌ Failed to click 'Select Diamond': {e}")

def get_product_details(driver, logger):
    try:
        title = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//h1"))).text.strip()
    except:
        title = None
    try:
        price_raw = driver.find_element(By.XPATH, "(//span[@pdpprice and @ge-data-converted-full-price])[1]").text.strip()
        price = re.sub(r"[^\d.]", "", price_raw)
    except:
        price = None
    try:
        setting_title = driver.find_element(By.CLASS_NAME, "setting_h1").text.strip().replace('\n', ' ')
    except:
        setting_title = None
    try:
        setting_price_raw = driver.find_element(By.ID, "setting-price").text.strip()
        setting_price = re.sub(r"[^\d.]", "", setting_price_raw)
    except:
        setting_price = None
    try:
        diamond_title = driver.find_element(By.ID, "diamond_name").text.strip()
    except:
        diamond_title = None
    try:
        diamond_price_raw = driver.find_element(By.XPATH, "//div[@id='diamond_name']/../../span").text.strip()
        diamond_price = re.sub(r"[^\d.]", "", diamond_price_raw)
    except:
        diamond_price = None
    logger.info(f"Title: {title}")
    logger.info(f"Price: {price}")
    logger.info(f"Setting Title: {setting_title}")
    logger.info(f"Setting Price: {setting_price}")
    logger.info(f"Diamond Title: {diamond_title}")
    logger.info(f"Diamond Price: {diamond_price}")
    return {
        "title": title,
        "price": price,
        "setting_title": setting_title,
        "setting_price": setting_price,
        "diamond_title": diamond_title,
        "diamond_price": diamond_price
    }