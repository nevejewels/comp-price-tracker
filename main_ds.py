from helpers.webdriver_manager import get_firefox_driver
from scrapers.thediamondstore import TheDiamondStoreScraper
from utils.logger import setup_logger  # Make sure this path is correct
import time
import pandas as pd
from helpers.email_service import send_error_email, send_completion_email
import datetime
from utils.db import pg_cursor

def dsmain():
    driver = get_firefox_driver(headless=False)
    logger = setup_logger(name="thediamondstore_scraper", file_name="thediamondstore")

    try:
        scraper = TheDiamondStoreScraper(driver, logger)
        scraper.scrape()  # Now scrape is called correctly
    finally:
        driver.quit()


if __name__ == "__main__":
    dsmain()
