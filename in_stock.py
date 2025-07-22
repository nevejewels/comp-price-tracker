import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import time
import re
import hashlib
import pandas as pd
import psycopg2

# =========================
# PostgreSQL Setup
# =========================
pg_conn = psycopg2.connect(
    host="178.79.182.27",
    database="briqpay",
    user="briqpay",
    password="briqpay111"
)
pg_conn.autocommit = True
pg_cursor = pg_conn.cursor()

# =========================
# Utility Functions
# =========================
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


# =========================
# Scrape Product URLs
# =========================
def scrape_product_urls(url):
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.version_main = 135

    driver = uc.Chrome(options=options)
    driver.get(url)
    time.sleep(45)

    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        ).click()
    except:
        pass

    product_urls = set()
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        products = driver.find_elements(By.CLASS_NAME, "product-section-block")
        for product in products:
            try:
                href = product.find_element(By.TAG_NAME, "a").get_attribute("href")
                if href:
                    product_urls.add(href)
            except:
                continue

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    driver.quit()
    return list(product_urls)

# =========================
# Extract Product Data
# =========================
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
        price_data = extract_price(text)
        if price_data:
            data.update(price_data)

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
                if (key, val) in found_pairs: continue
                found_pairs.add((key, val))

                if "VVS Colour" in key:
                    parts = val.split()
                    if len(parts) >= 2:
                        data["Clarity"] = "VVS"
                        data["Colour"] = parts[0].replace("Tag", "").strip()
                elif "Design Number" in key:
                    data.update(parse_design_number(val))
                else:
                    data[key] = val

        if not data or (len(data) == 1 and "price_raw" in data):
            data["raw_text"] = text

        section_items.append(data)

    if section_items:
        extracted_data["Product Details"] = section_items

    try:
        tag_elem = driver.find_element(By.XPATH,
            "//li[contains(@class, 'moreOptions') and .//div[contains(text(), 'Tag No:')]]//div[contains(@class, 'option_value')]")
        extracted_data["Tag No"] = clean(tag_elem.text)
    except:
        extracted_data["Tag No"] = "NULL"

    try:
        for selector in ["h1", ".product-title", ".prod_detail_rightBlock2 h1"]:
            try:
                title = driver.find_element(By.CSS_SELECTOR, selector).text
                if title and len(title) > 5:
                    extracted_data["Product Title"] = clean(title)
                    break
            except:
                continue
    except:
        pass

    try:
        code_elem = driver.find_element(By.CSS_SELECTOR, ".prod_detail_rightBlock2 strong")
        code_text = clean(code_elem.text)
        if code_text:
            extracted_data["Product Code"] = code_text
    except:
        pass

    return extracted_data

# =========================
# Scrape Single Product Page
# =========================
def scrape_product_page(url):
    print(f"\n🔍 Scraping: {url}")
    options = uc.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.version_main = 137

    driver = uc.Chrome(options=options)
    try:
        driver.get(url)
        time.sleep(6)

        data = extract_all_data(driver)
        data["product_url"] = url
        data["_id"] = hashlib.md5(url.encode()).hexdigest()
        data["scraped_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

        tag_no = data.get("Tag No", "NULL")
        price = ""
        if "Product Details" in data:
            for item in data["Product Details"]:
                if "price_raw" in item:
                    price = item["price_raw"].replace(" ", "")
                    break

        pg_cursor.execute("""
            INSERT INTO instock_scrape_data (tag_no, price, scraped_at, product_url)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
        """, (tag_no, price, data["scraped_at"], url))

        print("✅ Stored in PostgreSQL & scraped_at = ", data["scraped_at"])
    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
    finally:
        driver.quit()

# =========================
# Main
# =========================
if __name__ == "__main__":
    listing_urls = [
        "https://www.diamondsfactory.co.uk/available-now?instock=1&page=1&limit=5000"
    ]

    all_urls = []
    for url in listing_urls:
        print(f"\n📡 Fetching product URLs from: {url}")
        product_urls = scrape_product_urls(url)
        print(f"✅ Collected {len(product_urls)} product URLs")
        all_urls.extend(product_urls)

    # Save URLs with today's date
    today_str = datetime.today().strftime("%Y-%m-%d")
    csv_filename = f"files/instock/instock_urls_{today_str}.csv"
    df = pd.DataFrame([{"product_url": u} for u in all_urls])
    df.to_csv(csv_filename, index=False)
    print(f"📁 URLs saved to: {csv_filename}")


    # Get already scraped URLs from DB
    # pg_cursor.execute("SELECT product_url FROM instock_scrape_data;")
    pg_cursor.execute("""
        SELECT product_url 
        FROM instock_scrape_data 
        WHERE DATE(scraped_at) = CURRENT_DATE;
    """)
    scraped_urls = set(row[0] for row in pg_cursor.fetchall())

    remaining_urls = [url for url in all_urls if url not in scraped_urls]
    print(f"\n🔁 Remaining to scrape: {len(remaining_urls)}")

    print(f"\n🚀 Starting scraping of {len(remaining_urls)} product pages...")
    for i, product_url in enumerate(remaining_urls, 1):
        print(f"Progress: {i}/{len(remaining_urls)}")
        scrape_product_page(product_url)

    print("\n🎉 All done!")
