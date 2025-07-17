import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import os

output_file = open("files/instock/scraped_urls.txt", "a", encoding="utf-8")

# Launch undetected Chrome
def get(url):
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.version_main = 135
    driver = uc.Chrome(options=options)
    driver.get(url)
    time.sleep(20)  # Allow time for JS to render

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

    # ✅ Save to file
    for url in product_urls:
        output_file.write(url + "\n")

    driver.quit()

    # ✅ Output
    print(f"\nTotal URLs scraped: {len(product_urls)}")
    for url in product_urls:
        print(url)













urls = [
    "https://www.diamondsfactory.co.uk/available-now/instock-rings?instock=1&page=1&limit=5000",
    "https://www.diamondsfactory.co.uk/available-now/instock-earrings?instock=1&page=1&limit=5000",
    "https://www.diamondsfactory.co.uk/available-now/instock-pendants?instock=1&page=1&limit=5000",
    "https://www.diamondsfactory.co.uk/available-now/instock-bracelets?instock=1&page=1&limit=5000",
    "https://www.diamondsfactory.co.uk/available-now/instock-gift-sets?instock=1&page=1&limit=5000",
]

# Loop through each URL
for item in urls:
    print("Fetching for this url:", item)
    get(item)
    print("Completed for this url:", item)

# Close the file
output_file.close()










# ✅ Ensure directory exists
output_dir = r"C:\Users\rahul.gupta\Documents\pycodes\aa"
os.makedirs(output_dir, exist_ok=True)

# Launch undetected Chrome
def get(url, output_filename):
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.version_main = 135
    driver = uc.Chrome(options=options)
    driver.get(url)
    time.sleep(20)  # Allow time for JS to render

    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        ).click()
        print("Cookie banner accepted.")
    except:
        print("No cookie banner found.")

    # ✅ Extract total product count
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
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

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

    # ✅ Save to file in target directory
    output_path = os.path.join(output_dir, output_filename)
    with open(output_path, "w", encoding="utf-8") as f:
        for url in product_urls:
            f.write(url + "\n")

    print(f"\nTotal URLs scraped: {len(product_urls)} — Saved to {output_path}")
    for url in product_urls:
        print(url)

# URL to filename mapping
urls_with_filenames = {
    "https://www.diamondsfactory.co.uk/available-now/instock-rings?instock=1&page=1&limit=5000": "instock-rings.txt",
    "https://www.diamondsfactory.co.uk/available-now/instock-earrings?instock=1&page=1&limit=5000": "instock-earrings.txt",
    "https://www.diamondsfactory.co.uk/available-now/instock-pendants?instock=1&page=1&limit=5000": "instock-pendants.txt",
    "https://www.diamondsfactory.co.uk/available-now/instock-bracelets?instock=1&page=1&limit=5000": "instock-bracelets.txt",
    "https://www.diamondsfactory.co.uk/available-now/instock-gift-sets?instock=1&page=1&limit=5000": "instock-gift-sets.txt",
}

# Run scraping
for url, filename in urls_with_filenames.items():
    print("Fetching for this url:", url)
    get(url, filename)
    print("Completed for this url:", url)
