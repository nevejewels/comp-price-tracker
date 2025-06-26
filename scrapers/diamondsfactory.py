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
    stone_cut_select
)


from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/")
db = client["price_scraping"]
collection = db["diamondsfactory"]

class DiamondsFactoryScraper(BaseScraper):

    def scrape(self):
        self.driver.quit()

        df01 = pd.read_excel('files/common_price_inputfile.xlsx')
        print(df01.shape)

        for index, row in df01.iterrows():
            print("\n")
            url = row['Website URL_df']
            metal = row['Metal_df']
            stone_type = row['Stone Type_df']
            stone_shape = row['Stone Shape_df']
            stone_carat = row['Stone Carat_df']
            color = row['Color_df']
            clarity = row['Clarity_df']
            cut = row['Cut_df']

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
            time.sleep(8)

            stone_shape_select(driver, stone_shape)
            time.sleep(8)

            stone_carat_select(driver, stone_carat)
            time.sleep(8)

            stone_color_select(driver, color)
            time.sleep(8)

            stone_clarity_select(driver, clarity)
            time.sleep(8)

            stone_cut_select(driver, cut)
            time.sleep(8)

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.12);")
            time.sleep(2)  # Let elements load after scroll

            metal_price, diamond_price = metal_diamond_price(driver, self.logger)


            driver.quit()
