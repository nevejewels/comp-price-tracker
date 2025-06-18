from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def accept_cookies(driver):
    try:
        cookie_accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        cookie_accept_button.click()
    except Exception:
        pass  # silent if cookie banner not found

def get_title(driver, logger):
    try:
        rightside_parent = driver.find_element(By.CLASS_NAME, "js-pdp-sidebar-inner")
        title_element = rightside_parent.find_element(By.CSS_SELECTOR, "h1.heading")
        title = title_element.text.strip()
        logger.info(f"Title extracted: {title}")
        return title
    except Exception as e:
        logger.error(f"Error extracting title: {e}")
        return None

def click_metal_option(driver, logger, metal_to_select):
    try:
        metal_elements = driver.find_elements(By.CSS_SELECTOR, "a.metal-around")
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
        style_options = driver.find_elements(By.CSS_SELECTOR, "a.center_stone_img")
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

def click_diamond_shape(driver, logger, shape_name):
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

def click_diamond_origin(driver, logger, origin_type):
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
