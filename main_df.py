from helpers.webdriver_manager import get_firefox_driver
from scrapers.brilliantearth import BrilliantearthScraper
from scrapers.diamondsfactory import DiamondsFactoryScraper
from utils.logger import setup_logger  # Make sure this path is correct
import time
import pandas as pd
from helpers.email_service import send_error_email, send_completion_email
import datetime
from utils.db import pg_cursor

def bemain():
    driver = get_firefox_driver(headless=False)
    logger = setup_logger("brilliant_scraper")

    try:
        scraper = BrilliantearthScraper(driver, logger)
        scraper.scrape()  # Now scrape is called correctly
    finally:
        driver.quit()

def dfmain():
    driver = None
    logger = setup_logger("diamonds_factory_scraper")
    start_time = time.time()
    total_scraped = 0
    total_failed = 0

    try:
        driver = get_firefox_driver(headless=False)
        scraper = DiamondsFactoryScraper(driver, logger)
        
        # Get the input data to know total count
        df_input = pd.read_excel('files/diamondsfactory/diamondsfactory_input.xlsx')
        total_items = len(df_input)
        
        try:
            # Modified scrape method should return success/failure counts
            scraped, failed = scraper.scrape()
            total_scraped += scraped
            total_failed += failed
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            send_error_email("DiamondsFactory", e)
            total_failed = total_items  # Assume all failed if we couldn't even start
            
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        send_error_email("DiamondsFactory", e)
        total_failed = total_items  # Assume all failed if we couldn't even start
    finally:
        if driver:
            driver.quit()
        
        # Calculate execution time
        execution_time = str(datetime.timedelta(seconds=time.time() - start_time))

        total_input_count = len(df_input)
        today_str = datetime.datetime.today().strftime('%Y-%m-%d')
        pg_cursor.execute("""
            SELECT COUNT(*) 
            FROM public.stg_price_df_scrape 
            WHERE updated_date_t = %s
        """, (today_str,))

        total_scraped_count = pg_cursor.fetchone()[0]

        pg_cursor.close()

        # Send completion email
        send_completion_email("DiamondsFactory", total_scraped, total_failed, execution_time, total_input_count, total_scraped_count)


if __name__ == "__main__":
    # bemain()
    dfmain()
