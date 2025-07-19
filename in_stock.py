import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient
import hashlib
import time
import re
import os
import pandas as pd

# =========================
# Scraper Function
# =========================
def scrape_product_urls(url):
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.version_main = 135

    driver = uc.Chrome(options=options)
    driver.get(url)
    time.sleep(60)  # Allow time for JS to render

    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        ).click()
        print("Cookie banner accepted.")
    except:
        print("No cookie banner found.")

    # ✅ Extract total product count from class="product-count"
    try:
        count_text = driver.find_element(By.CLASS_NAME, "product-count").text
        total_products = int(re.search(r'\d+', count_text).group())
        print(f"Target product count: {total_products}")
    except Exception as e:
        print("Failed to get product count:", e)
        driver.quit()
        exit()

    # ✅ Scroll and collect URLs
    product_urls = set()
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Get product links
        products = driver.find_elements(By.CLASS_NAME, "product-section-block")
        for product in products:
            try:
                a_tag = product.find_element(By.TAG_NAME, "a")
                href = a_tag.get_attribute("href")
                if href:
                    product_urls.add(href)
            except:
                continue

        print(f"Collected {len(product_urls)} / {total_products}")
        if len(product_urls) >= total_products:
            break

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    driver.quit()
    return list(product_urls)


# =========================
# Main Execution
# =========================
# urls = [
#     "https://www.diamondsfactory.co.uk/available-now/instock-rings?instock=1&page=1&limit=5000",
#     "https://www.diamondsfactory.co.uk/available-now/instock-earrings?instock=1&page=1&limit=5000",
#     "https://www.diamondsfactory.co.uk/available-now/instock-pendants?instock=1&page=1&limit=5000",
#     "https://www.diamondsfactory.co.uk/available-now/instock-bracelets?instock=1&page=1&limit=5000",
#     "https://www.diamondsfactory.co.uk/available-now/instock-gift-sets?instock=1&page=1&limit=5000",
# ]
urls = [
    "https://www.diamondsfactory.co.uk/available-now?instock=1&page=1&limit=5000"
]

all_scraped_data = []
for url in urls:
    print("\n📡 Fetching for:", url)
    scraped_urls = scrape_product_urls(url)
    all_scraped_data.extend([{"source_url": url, "product_url": u} for u in scraped_urls])
    print(f"✅ Completed for: {url}")

# =========================
# Save to CSV
# =========================
df = pd.DataFrame(all_scraped_data)
df.to_csv(r"files\instock\instock_urls.csv", index=False, encoding="utf-8")
print("\n📁 Data saved to csv")
