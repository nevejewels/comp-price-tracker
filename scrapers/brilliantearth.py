from scrapers.base_scraper import BaseScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from scrapers.brilliantearth_helper import (
    click_diamond_origin,
    click_style_option,
    click_metal_option,
    get_title,
    accept_cookies,
    click_diamond_shape
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

            diamond_shape = "Round"
            # diamond_shape = "Oval"
            # diamond_shape = "Emerald"
            # diamond_shape = "Cushion"
            # diamond_shape = "Elongated Cushion"
            # diamond_shape = "Radiant"
            # diamond_shape = "Princess"
            # diamond_shape = "Asscher"
            click_diamond_shape(self.driver, self.logger, diamond_shape)
            time.sleep(10)