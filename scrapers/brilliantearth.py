from scrapers.base_scraper import BaseScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from scrapers.brilliantearth_helper import (
    click_diamond_origin,
    click_first_select_diamond,
    click_style_option,
    click_metal_option,
    get_title,
    accept_cookies,
    click_diamond_shape,
    select_clarity,
    select_color,
    select_cut,
    set_carat_range
)
import time

class BrilliantearthScraper(BaseScraper):

    def scrape(self):

        # urls = ['https://www.brilliantearth.com/en-gb/1.4mm-Provence-Solitaire-Ring-Gold-BE1776-4345169/',
        #         'https://www.77diamonds.com/engagement-rings/solitaire/round/white-gold?item=188']
        urls = ['https://www.brilliantearth.com/en-gb/1.4mm-Provence-Solitaire-Ring-Gold-BE1776-4345169/']
        # urls = ['https://www.brilliantearth.com/en-gb/rings/cyorings/purchase_review/?sid=4345169&did=46944384']

        for url in urls:
            self.logger.info(f"Scraping: {url}")
            self.driver.get(url)
            time.sleep(2)

            # Accept cookies if the prompt appears
            accept_cookies(self.driver)

            # # Get the title of the page
            # title = get_title(self.driver, self.logger)

            # metal_to_select = "18K White Gold"
            # # metal_to_select = "18K Yellow Gold"
            # # metal_to_select = "14K Rose Gold"
            # # metal_to_select = "Platinum"
            # click_metal_option(self.driver, self.logger, metal_to_select)

            # style_name = "Classic"
            # # style_name = "Hidden Halo"
            # click_style_option(self.driver, self.logger, style_name)

            # time.sleep(10)

            # # stone_type_val = "Natural"
            # stone_type_val = "Lab Grown"
            # click_diamond_origin(self.driver, self.logger, stone_type_val)


            try:
                button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "add_cyoring"))
                )
                button.click()
                self.logger.info("Clicked 'CHOOSE THIS SETTING' button successfully.")
            except Exception as e:
                self.logger.error(f"Failed to click 'CHOOSE THIS SETTING' button: {e}")
            time.sleep(5)

            # diamond_shape = "Round"
            # diamond_shape = "Oval"
            # diamond_shape = "Emerald"
            # diamond_shape = "Cushion"
            # diamond_shape = "Elongated Cushion"
            # diamond_shape = "Radiant"
            # diamond_shape = "Princess"
            # diamond_shape = "Asscher"
            # click_diamond_shape(self.driver, self.logger, diamond_shape)
            # time.sleep(10)

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

            time.sleep(6)
            clarity_val = "SI2"
            # clarity_val = "SI1"
            # clarity_val = "VS2"
            # clarity_val = "VS1"
            # clarity_val = "VVS2"
            # clarity_val = "VVS1"
            # clarity_val = "IF"
            # clarity_val = "FL"
            select_clarity(self.driver, self.logger, clarity_val)
            time.sleep(5)

            click_first_select_diamond(self.driver, self.logger)
            time.sleep(15)