from scrapers.base_scraper import BaseScraper
from selenium.webdriver.common.by import By
import time

class BrilliantearthScraper(BaseScraper):
    
    def scrape(self):

        # urls = ['https://www.brilliantearth.com/en-gb/1.4mm-Provence-Solitaire-Ring-Gold-BE1776-4345169/',
        #         'https://www.77diamonds.com/engagement-rings/solitaire/round/white-gold?item=188']
        urls = ['https://www.brilliantearth.com/en-gb/1.4mm-Provence-Solitaire-Ring-Gold-BE1776-4345169/']


        for url in urls:
            self.logger.info(f"Scraping: {url}")
            self.driver.get(url)
            time.sleep(2)

            try:
                title_element = self.driver.find_element(By.CSS_SELECTOR, "h1.heading")
                title = title_element.text.strip()
                self.logger.info(f"✅ Title extracted: {title}")
            except Exception as e:
                self.logger.error(f"❌ Error extracting title: {e}")

            time.sleep(10)
