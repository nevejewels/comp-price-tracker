from helpers.webdriver_manager import get_firefox_driver
from scrapers.brilliantearth import BrilliantearthScraper
from utils.logger import setup_logger  # Make sure this path is correct

def main():
    driver = get_firefox_driver(headless=False)
    logger = setup_logger("brilliant_scraper")

    try:
        scraper = BrilliantearthScraper(driver, logger)
        scraper.scrape()  # Now scrape is called correctly
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
