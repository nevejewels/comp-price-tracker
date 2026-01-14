import os
import csv
import time
import random
import warnings
from datetime import datetime

import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from db_insert import insert_scraped_data
from parser import normalize_records

# =====================================================
# CONFIG
# =====================================================
uc.Chrome.__del__ = lambda self: None

INPUT_CSV = r"C:\Users\komal.kumavat\Documents\diamond_heaven_simulated_output\diamond_heaven_data_input.csv"

OUTPUT_DIR = "diamondheaven_competitor_products"
LOG_FILE = os.path.join(OUTPUT_DIR, "scraper_log.txt")
FAIL_CSV = os.path.join(OUTPUT_DIR, "failed_rows.csv")

PAGE_TIMEOUT = 120
MAX_RETRIES = 3

DB_CONFIG = {
    "dbname": "competitor_products",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5432,
}

SOURCE_WEBSITE = "diamond-heaven.co.uk"

warnings.filterwarnings("ignore")

def log(msg):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def log_fail(row, reason):
    exists = os.path.exists(FAIL_CSV)
    with open(FAIL_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()) + ["error"])
        if not exists:
            writer.writeheader()
        row["error"] = reason
        writer.writerow(row)

def start_driver():
    opts = uc.ChromeOptions()
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--window-size=1920,1080")
    driver = uc.Chrome(options=opts, version_main=141)
    driver.set_page_load_timeout(PAGE_TIMEOUT)
    return driver

def accept_cookies(driver):
    try:
        WebDriverWait(driver, 6).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Accept')]"))
        ).click()
        time.sleep(0.5)
    except:
        pass

def select_shape(driver, shape):
    block = driver.find_element(By.CLASS_NAME, "pdstone_shape")
    block.find_element(By.CSS_SELECTOR, f"li[data-hint='{shape}']").click()
    time.sleep(0.5)


def set_carat(driver, carat_label):
    slider = driver.find_element(By.ID, "labgrownnonfeedcaratSlider")
    pip = slider.find_element(
        By.XPATH, f".//span[contains(@class,'ui-slider-label') and text()='{carat_label}']"
    )
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", pip)
    pip.click()
    time.sleep(1)


def select_clarity(driver, clarity):
    ul = driver.find_element(By.ID, "labgrownnonfeedclarityRadio")
    label = ul.find_element(By.CSS_SELECTOR, f"input[value='{clarity}'] + label")
    label.click()
    time.sleep(0.5)


def select_cut(driver, cut):
    ul = driver.find_element(By.ID, "labgrownnonfeedcutRadio")
    label = ul.find_element(By.CSS_SELECTOR, f"input[value='{cut}'] + label")
    label.click()
    time.sleep(0.5)


def extract_summary(driver):
    summary = {}
    block = driver.find_element(By.CSS_SELECTOR, ".summary-block")
    for p in block.find_elements(By.TAG_NAME, "p"):
        try:
            key = p.find_element(By.TAG_NAME, "span").text.replace(":", "").lower()
            val = p.text.replace(p.find_element(By.TAG_NAME, "span").text, "").strip()
            summary[key] = val
        except:
            continue
    return summary


def extract_price(driver):
    out = {}
    block = driver.find_element(By.ID, "price-block")

    def safe(sel):
        try:
            return block.find_element(By.CSS_SELECTOR, sel).text.strip()
        except:
            return None

    out["list_price"] = safe(".special_price")

    raw = block.text
    if "inc VAT" in raw:
        out["final_price_inc_vat"] = raw.split("inc VAT")[0].split("£")[-1].strip()

    try:
        out["high_street_price"] = block.find_element(
            By.XPATH, ".//p[contains(text(),'High Street Price')]"
        ).text.split(":")[-1].strip()
    except:
        pass

    try:
        out["you_save"] = block.find_element(By.CLASS_NAME, "you-save").text.split(":")[-1].strip()
    except:
        pass

    out["finance_pm"] = safe(".v12_montly_pay_cart")

    return out


def process_row(driver, row):
    driver.get(row["product_url"])
    time.sleep(2)
    accept_cookies(driver)

    select_shape(driver, row["shape"])
    set_carat(driver, row["carat"])
    select_clarity(driver, row["clarity"])
    select_cut(driver, row["cut"])

    summary = extract_summary(driver)
    price = extract_price(driver)

    record = {
        **row,
        **summary,
        **price,
        "updated_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    }

    normalized = normalize_records([record], source_website=SOURCE_WEBSITE)
    insert_scraped_data(normalized, SOURCE_WEBSITE, DB_CONFIG)

#main
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df = pd.read_csv(INPUT_CSV)

    driver = start_driver()

    try:
        for idx, row in df.iterrows():
            payload = row.to_dict()
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    log(f"▶ Row {idx+1} | Attempt {attempt}")
                    process_row(driver, payload)
                    break
                except Exception as e:
                    log(f"⚠️ Retry {attempt} failed: {e}")
                    if attempt == MAX_RETRIES:
                        log_fail(payload, str(e))
    finally:
        driver.quit()

    log("✅ Diamond Heaven scrape completed")

if __name__ == "__main__":
    main()
