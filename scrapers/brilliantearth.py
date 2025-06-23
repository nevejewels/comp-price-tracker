import sys
import pandas as pd
from scrapers.base_scraper import BaseScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from scrapers.brilliantearth_helper import (
    accept_cookies,
    click_stonetype_diamond,
    click_first_select_diamond,
    click_style_option,
    click_metal_option,
    get_title,
    click_stone_shape,
    select_clarity,
    select_color,
    select_cut,
    set_carat_range,
    get_product_details
)
import time

class BrilliantearthScraper(BaseScraper):

    def scrape(self):

        # urls = ['https://www.brilliantearth.com/en-gb/1.4mm-Provence-Solitaire-Ring-Gold-BE1776-4345169/',
        #         'https://www.77diamonds.com/engagement-rings/solitaire/round/white-gold?item=188']
        # urls = ['https://www.brilliantearth.com/en-gb/1.4mm-Provence-Solitaire-Ring-Gold-BE1776-4345169/']
        # urls = ['https://www.brilliantearth.com/en-gb/rings/cyorings/purchase_review/?did=47345275&sid=4345169']
        # urls = ['https://www.brilliantearth.com/en-gb/rings/cyorings/purchase_review/?sid=4345169&did=46944384']

        df01 = pd.read_excel('files/brilliantearth_price_inputfile.xlsx')
        print(df01.head())

        for index, row in df01.iterrows():
            url = row['Website URL']
            metal = row['Metal']
            stone_type = row['Stone Type']
            stone_shape = row['Stone Shape']


            self.logger.info(f"Scraping URL: {url}")
            self.logger.info(f"Scraping Metal: {metal}")
            self.logger.info(f"Scraping Stone Type: {stone_type}")

        # for url in urls:
            self.driver.get(url)

            # Accept cookies if the prompt appears
            accept_cookies(self.driver)
            time.sleep(4)

            # Get the title of the page
            title = get_title(self.driver, self.logger)

            # metal_val = "18K White Gold" # "18K Yellow Gold" "14K Rose Gold" "Platinum"
            metal_val = metal
            click_metal_option(self.driver, self.logger, metal_val)

            # style_name = "Classic" # "Hidden Halo"
            # click_style_option(self.driver, self.logger, style_name)

            # stone_type_val = "Natural" # "Lab Grown"
            stone_type_val = stone_type
            click_stonetype_diamond(self.driver, self.logger, stone_type_val)
            time.sleep(2.5)

            try:
                button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "add_cyoring"))
                )
                button.click()
                self.logger.info("Clicked 'CHOOSE THIS SETTING' button successfully.")
            except Exception as e:
                self.logger.error(f"Failed to click 'CHOOSE THIS SETTING' button: {e}")

            # stone_shape_value = "Round" # "Oval" "Emerald" "Cushion" "Elongated Cushion" "Radiant" "Princess" "Asscher"
            stone_shape_value = stone_shape
            click_stone_shape(self.driver, self.logger, stone_shape_value)
            time.sleep(15)

            sys.exit()

            # time.sleep(5)
            # set_carat_range(self.driver, self.logger, "1.0", "1.0")
            # print("Set carat range to 1.0 - 1.0")
            # time.sleep(10)

            # time.sleep(10)
            # # cut_values = "Fair"
            # # cut_values = "Good"
            # # cut_values = "Very Good"
            # # cut_values = "Ideal"
            # cut_values = "Super Ideal"
            # select_cut(self.driver, self.logger, cut_values)
            # time.sleep(10)


            # time.sleep(10)
            # color_val = "E"
            # select_color(self.driver, self.logger, color_val)
            # time.sleep(10)

            # time.sleep(4)
            # clarity_val = "SI2"
            # clarity_val = "SI1"
            # clarity_val = "VS2"
            # clarity_val = "VS1"
            # clarity_val = "VVS2"
            # clarity_val = "VVS1"
            # clarity_val = "IF"
            # clarity_val = "FL"
            # select_clarity(self.driver, self.logger, clarity_val)
            # time.sleep(5)

            # time.sleep(2)
            # click_first_select_diamond(self.driver, self.logger)
            # time.sleep(5)

            time.sleep(3)

            product_details = get_product_details(self.driver, self.logger)
            title = product_details['title']
            price = product_details['price']
            setting_title = product_details['setting_title']
            setting_price = product_details['setting_price']
            diamond_title = product_details['diamond_title']
            diamond_price = product_details['diamond_price']

