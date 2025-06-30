from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
import time

def metal_select(driver, metal_val):
    try:
        if metal_val == "18K White Gold":
            metal_id = "img_GL_18K_W"
        elif metal_val == "18K Yellow Gold":
            metal_id = "img_GL_18K_Y"
        elif metal_val == "18K Rose Gold":
            metal_id = "img_GL_18K_R"
        elif metal_val == "Platinum":
            metal_id = "img_PL_950_W"
        # driver.find_element(By.ID, metal_id).click()
        metal1 = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, metal_id))
        )
        metal1.click()
        print(f"Clicked on metal = {metal_val}")
    except Exception as e:
        print(f"Error selecting metal: {e}")

def stone_type_select(driver, stone_type):
    try:
        # Wait for the entire stone type dropdown block to be present
        stone_type_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "stone_type"))
        )

        # Get all li items
        stone_type_options = stone_type_container.find_elements(By.CSS_SELECTOR, "li.stone_typeCls")

        for option in stone_type_options:
            label = option.get_attribute("namer")  # or use .text if more reliable
            if label and label.strip().lower() == stone_type.strip().lower():
                option.click()
                print(f"{stone_type} selected!")
                return

        print(f"Stone type '{stone_type}' not found.")
        
    except Exception as err:
        print(f"Stone type selection failed: {err}")

def stone_shape_select(driver, stone_shape):
    try:
        # Wait for the stone shape container to be present
        shape_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "stone_shape"))
        )

        # Find all shape option elements
        shape_options = shape_container.find_elements(By.CSS_SELECTOR, "li.stone_shapeCls")

        # Iterate and match shape
        for option in shape_options:
            label = option.get_attribute("namer")
            if label and label.strip().lower() == stone_shape.strip().lower():
                option.click()
                print(f"Stone shape '{stone_shape}' selected!")
                return

        print(f"Stone shape '{stone_shape}' not found among available options.")

    except Exception as e:
        print(f"Stone shape selection failed: {e}")

def stone_carat_select(driver, stone_carat):
    try:
        # Format input to two decimal places (e.g., 0.5 -> '0.50')
        formatted_input = "{:.2f}".format(float(stone_carat))

        # Wait for the carat container
        carat_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "stone_carat"))
        )

        # Find all carat option elements
        carat_options = carat_container.find_elements(By.CSS_SELECTOR, "li.stone_caratCls")

        for option in carat_options:
            label = option.get_attribute("namer")
            if label and label.strip() == formatted_input:
                option.click()
                print(f"Stone carat '{formatted_input}' selected!")
                return

        print(f"Stone carat '{formatted_input}' not found among options.")

    except Exception as e:
        print(f"Stone carat selection failed: {e}")


def stone_color_select(driver, stone_color):
    try:
        # Normalize input (e.g. 'f' → 'F')
        target_color = str(stone_color).strip().upper()

        # Wait for the color container
        color_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "stone_color"))
        )

        # Find all color options
        color_options = color_container.find_elements(By.CSS_SELECTOR, "li.stone_colorCls")

        for option in color_options:
            label = option.get_attribute("namer")
            is_disabled = "disabledopt" in option.get_attribute("class")

            if label and label.strip().upper() == target_color:
                if is_disabled:
                    print(f"Stone color '{target_color}' is disabled/unavailable.")
                    return
                option.click()
                print(f"Stone color '{target_color}' selected!")
                return

        print(f"Stone color '{target_color}' not found among options.")

    except Exception as e:
        print(f"Stone color selection failed: {e}")

def stone_clarity_select(driver, clarity_value):
    try:
        # Normalize clarity input (e.g., 'vs2' → 'VS2')
        clarity_target = str(clarity_value).strip().upper()

        # Wait for the clarity container to be present
        clarity_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "stone_clarity"))
        )

        # Get all clarity option elements
        clarity_options = clarity_container.find_elements(By.CSS_SELECTOR, "li.stone_clarityCls")

        for option in clarity_options:
            label = option.get_attribute("namer")
            is_disabled = "disabledopt" in option.get_attribute("class")

            if label and label.strip().upper() == clarity_target:
                if is_disabled:
                    print(f"Stone clarity '{clarity_target}' is disabled/unavailable.")
                    return
                option.click()
                print(f"Stone clarity '{clarity_target}' selected!")
                return

        print(f"Stone clarity '{clarity_target}' not found among options.")

    except Exception as e:
        print(f"Stone clarity selection failed: {e}")

def stone_cut_select(driver, cut_value):
    try:
        # Normalize input (e.g., 'very good' → 'Very Good')
        target_cut = str(cut_value).strip().title()

        # Wait until the cut container is loaded
        cut_container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "stone_cut"))
        )

        # Find all cut grade options
        cut_options = cut_container.find_elements(By.CSS_SELECTOR, "li.stone_cutCls")

        for option in cut_options:
            label = option.get_attribute("namer")
            is_disabled = "disabledopt" in option.get_attribute("class")

            if label and label.strip().lower() == target_cut.lower():
                if is_disabled:
                    print(f"Cut grade '{target_cut}' is disabled/unavailable.")
                    return
                option.click()
                print(f"Cut grade '{target_cut}' selected!")
                return

        print(f"Cut grade '{target_cut}' not found among options.")

    except Exception as e:
        print(f"Cut grade selection failed: {e}")

def get_title(driver, logger):
    try:
        title_element = driver.find_element(By.CSS_SELECTOR, "div.product-name h1.prod_title")
        title = title_element.text.strip()
        logger.info("Product Title: %s", title)
        return title
    except Exception as e:
        logger.error("Error: %s", e)
        return None

def get_price(driver, logger):
    try:
        strike_price = driver.find_element(By.CSS_SELECTOR, "span.black-strike-price").text.strip()
    except:
        strike_price = "N/A"
    try:
        final_price = driver.find_element(By.CSS_SELECTOR, "span.final_price").get_attribute("content")
        final_price = f"£{final_price.strip()}" if final_price else "N/A"
    except:
        final_price = "N/A"
    try:
        rrp_price = driver.find_element(By.CSS_SELECTOR, "span.rrp.linethrough").text.strip()
    except:
        rrp_price = "N/A"
    try:
        you_save = driver.find_element(By.CSS_SELECTOR, "span.save").text.strip()
    except:
        you_save = "N/A"
    return strike_price, final_price, rrp_price, you_save

def metal_diamond_price(driver):
    # Wait until the parent container is present
    try:
        parent = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "setting-diamond-options"))
        )

        # Get the setting price
        setting_price_element = parent.find_element(By.ID, "metalPrice")
        setting_price = setting_price_element.text.strip().replace("£", "")

        # Get the diamond price
        diamond_price_element = parent.find_element(By.ID, "stonePrice")
        diamond_price = diamond_price_element.text.strip().replace("£", "")

        print("Setting Price:", setting_price)
        print("Diamond Price:", diamond_price)
        return setting_price, diamond_price
    except:
        return None, None

def time_taken_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Time taken for {func.__name__}: {elapsed_time:.2f} seconds")
        return result
    return wrapper

@time_taken_decorator
def extract_all_product_details(driver):
    details = {}
    try:
        parent = driver.find_element(By.CLASS_NAME, "detailCol1")
        print("Parent element found:", parent)
        
        # Get all <p> elements inside it
        ps = parent.find_elements(By.TAG_NAME, "p")

        for p in ps:
            text = p.text.strip()
            if ":" in text:
                key, val = text.split(":", 1)
                key = key.strip().rstrip(":")
                val = val.strip()
                if key and val:
                    details[key] = val
            else:
                # for <b>Setting Height:</b><span><span>5.2 mm</span></span> pattern
                try:
                    b = p.find_element(By.TAG_NAME, "b")
                    span = p.find_element(By.TAG_NAME, "span")
                    key = b.text.strip().rstrip(":")
                    val = span.text.strip()
                    if key and val:
                        details[key] = val
                except:
                    continue
    except Exception as e:
        print(f"❌ Error in detailCol1 extraction: {e}")
    
    return {"product_details": details}

