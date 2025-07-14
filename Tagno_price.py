import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from pymongo import MongoClient
import hashlib
import time
import re

# === MongoDB Setup ===
client = MongoClient("mongodb://localhost:27017/")
db = client["Diamond_data"]
collection = db["price_n_tagno_8thjuly"]
# === Load URLs ===
# with open(r"C:\Users\komal.kumavat\Documents\PDP_urls_data_fetching\scraped_urls.txt", "r", encoding="utf-8") as f:
with open(r"files\instock\scraped_urls.txt", "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip()]

# === Utility Functions ===
def clean(text):
    return ' '.join(text.replace('\xa0', ' ').replace('\n', ' ').split()).strip()

def extract_price(text):
    match = re.search(r"(£[\d,]+)", text)
    return {"price_raw": match.group(1)} if match else None

def parse_design_number(value):
    match = re.match(r"(\w+)\s+([\d.]+)ct\s+([\d.]+mm)\s+(\w+)", value)
    return {
        "Design Number": match.group(1),
        "Carat Weight": match.group(2),
        "Measurement": match.group(3),
        "Ring Size": match.group(4),
    } if match else {}

# === Main Extraction Logic ===
def extract_all_data(driver):
    extracted_data = {}
    try:
        elements = driver.find_elements(By.CSS_SELECTOR, ".prod_detail_rightBlock2")
    except:
        elements = []

    section_items = []
    for elem in elements:
        text = clean(elem.text)
        if not text:
            continue

        data = {}

        # === Extract price ===
        price_data = extract_price(text)
        if price_data:
            data.update(price_data)

        # === Extract details using regex ===
        patterns = [
            r"([A-Za-z \-/]+):\s*([^\n:£]+)",
            r"([A-Z][A-Za-z ]+):\s*([^\n:]+)",
            r"(\w+(?:\s+\w+)*):\s*([^\n:]+)",
        ]

        found_pairs = set()
        for pattern in patterns:
            for match in re.findall(pattern, text):
                key = clean(match[0])
                val = clean(match[1])
                if not key or not val or (key, val) in found_pairs:
                    continue
                found_pairs.add((key, val))

                if "VVS Colour" in key:
                    val_parts = val.split()
                    if len(val_parts) >= 2:
                        data["Clarity"] = "VVS"
                        colour = val_parts[0].replace("Tag", "").strip()
                        data["Colour"] = colour
                elif "Design Number" in key:
                    data.update(parse_design_number(val))
                else:
                    data[key] = val

        # Fallback line-by-line parsing
        if len(data) <= 1:
            for line in text.split('\n'):
                if ':' in line and len(line.strip()) > 3:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key = clean(parts[0])
                        val = clean(parts[1])
                        if "VVS Colour" in key:
                            val_parts = val.split()
                            if len(val_parts) >= 2:
                                data["Clarity"] = "VVS"
                                data["Colour"] = val_parts[0].replace("Tag", "").strip()
                        elif "Design Number" in key:
                            data.update(parse_design_number(val))
                        else:
                            data[key] = val

        if not data or (len(data) == 1 and "price_raw" in data):
            data["raw_text"] = text

        section_items.append(data)

    if section_items:
        extracted_data["Product Details"] = section_items

    # === Tag No ===
    try:
        tag_value_element = driver.find_element(By.XPATH,
            "//li[contains(@class, 'moreOptions') and .//div[contains(text(), 'Tag No:')]]//div[contains(@class, 'option_value')]")
        tag_text = clean(tag_value_element.text)
        extracted_data["Tag No"] = tag_text if tag_text else "NULL"
    except:
        extracted_data["Tag No"] = "NULL"

    # === Product Title ===
    try:
        title_selectors = [
            "h1", ".product-title", ".prod_detail_rightBlock2 h1",
            ".product-name", "[class*='title']", "[class*='product']"
        ]
        for selector in title_selectors:
            try:
                title_elem = driver.find_element(By.CSS_SELECTOR, selector)
                title_text = clean(title_elem.text)
                if title_text and len(title_text) > 5:
                    extracted_data["Product Title"] = title_text
                    break
            except:
                continue
    except:
        pass

    # === Product Code ===
    try:
        code_elem = driver.find_element(By.CSS_SELECTOR, ".prod_detail_rightBlock2 strong")
        code_text = clean(code_elem.text)
        if code_text:
            extracted_data["Product Code"] = code_text
    except:
        pass

    return extracted_data

# === Scraper Function ===
# === Scraper Function ===
def scrape_product_page(url):
    print(f"\n🔍 Scraping: {url}")
    
    # Configure Chrome options for headless mode
    options = uc.ChromeOptions()
    
    # Headless mode - runs in background without opening browser window
    options.add_argument("--headless")
    
    # Additional performance and stability options
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")  # Don't load images for faster scraping
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
    
    # Memory optimization
    options.add_argument("--memory-pressure-off")
    options.add_argument("--max_old_space_size=4096")
    
    # Match with your installed Chrome version (v137)
    chrome_version = 137
    driver = uc.Chrome(options=options, version_main=chrome_version)
    
    try:
        driver.get(url)
        time.sleep(6)
        
        data = extract_all_data(driver)
        data["product_url"] = url
        data["_id"] = hashlib.md5(url.encode()).hexdigest()
        data["scraped_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        collection.update_one(
            {"_id": data["_id"]},
            {"$set": data},
            upsert=True
        )
        print("✅ Stored in MongoDB")
        
    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
    finally:
        driver.quit()

# === Run for All URLs ===
print(f"🚀 Starting headless scraping of {len(urls)} URLs...")
for i, url in enumerate(urls, 1):
    print(f"Progress: {i}/{len(urls)}")
    scrape_product_page(url)
    
print("🎉 All URLs scraped successfully!")