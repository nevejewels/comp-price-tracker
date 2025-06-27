import sys
import pandas as pd
from helpers.webdriver_manager import get_firefox_driver
from scrapers.base_scraper import BaseScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from scrapers.diamondsfactory_helper import (
    metal_diamond_price,
    metal_select,
    stone_type_select,
    stone_shape_select,
    stone_carat_select,
    stone_color_select,
    stone_clarity_select,
    stone_cut_select,
    get_title,
    get_price,
    extract_all_product_details
)

from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/")
db = client["price_scraping"]
collection = db["diamondsfactory"]

class DiamondsFactoryScraper(BaseScraper):

    def scrape(self):
        self.driver.quit()

        df_input = pd.read_excel('files/diamondsfactory_input.xlsx')
        self.logger.info(f"Total input rows: {len(df_input)}")

        match_columns = [
            "product_url",
            "metal",
            "stone_type",
            "stone_shape",
            "stone_carat",
            "color",
            "clarity",
            "cut"
        ]

        existing_docs = list(collection.find({}, {col: 1 for col in match_columns}))
        if not existing_docs:
            self.logger.info("No existing records found in MongoDB. Scraping all rows.")
            df_to_scrape = df_input.copy()
        else:
            df_existing = pd.DataFrame(existing_docs)
            self.logger.info(f"Already crawled rows in DB: {len(df_existing)}")

            # Merge input with existing to find uncrawled ones
            df_merged = pd.merge(df_input, df_existing, on=match_columns, how='left', indicator=True)
            df_to_scrape = df_merged[df_merged['_merge'] == 'left_only'].drop(columns=['_merge'])

        self.logger.info(f"Remaining rows to scrape: {len(df_to_scrape)}")

        for index, row in df_to_scrape.iterrows():
            print("\n")
            url = row['product_url']
            metal = row['metal']
            stone_type = row['stone_type']
            stone_shape = row['stone_shape']
            stone_carat = row['stone_carat']
            color = row['color']
            clarity = row['clarity']
            cut = row['cut']

            self.logger.info(f"Scraping URL: {url}")
            self.logger.info(f"Scraping Metal: {metal}")
            self.logger.info(f"Scraping Stone Type: {stone_type}")
            self.logger.info(f"Scraping Stone Shape: {stone_shape}")
            self.logger.info(f"Scraping Stone Carat: {stone_carat}")
            self.logger.info(f"Scraping Color: {color}")
            self.logger.info(f"Scraping Clarity: {clarity}")
            self.logger.info(f"Scraping Cut: {cut}")

            driver = get_firefox_driver(headless=False)
            
            driver.get(url)
            time.sleep(2)
            driver.execute_script("document.body.style.zoom='40%'")
            time.sleep(5)

            try:
                accept_cookies_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
                )
                accept_cookies_button.click()
                print("Cookies accepted.")
            except Exception:
                print(f"No cookies popup")
            time.sleep(2)

            metal_val = metal.strip()
            metal_select(driver, metal_val)
            time.sleep(8)

            stone_type_select(driver, stone_type)
            time.sleep(5)

            stone_shape_select(driver, stone_shape)
            time.sleep(5)

            stone_carat_select(driver, stone_carat)
            time.sleep(5)

            stone_color_select(driver, color)
            time.sleep(5)

            stone_clarity_select(driver, clarity)
            time.sleep(5)

            stone_cut_select(driver, cut)
            time.sleep(5)

            detail_json = extract_all_product_details(driver)
            print(f"Detail JSON: {detail_json}")
            time.sleep(1)

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.13);")
            time.sleep(2)  # Let elements load after scroll

            title = get_title(driver, self.logger)
            print(f"Title: {title}")

            strike_price, final_price, rrp_price, you_save = get_price(driver, self.logger)
            print(f"Strike Price: {strike_price}, Final Price: {final_price}, RRP Price: {rrp_price}, You Save: {you_save}")
            
            metal_price, diamond_price = metal_diamond_price(driver)
            print(f"Metal Price: {metal_price}, Diamond Price: {diamond_price}")

            row_data = row.to_dict()
            row_data.update({
                "product_title": title,
                "metal_price": metal_price,
                "stone_price": diamond_price,
                "final_price": final_price,
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "strike_price": strike_price,
                "rrp_price": rrp_price,
                "you_save": you_save,
                "detail_json": detail_json
            })

            row_data.pop('_id', None)
            collection.insert_one(row_data)
            self.logger.info(f"Inserted data into MongoDB for URL: {url}")

            driver.quit()
