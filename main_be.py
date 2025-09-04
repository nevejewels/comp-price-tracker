from helpers.webdriver_manager import get_firefox_driver
from scrapers.brilliantearth import BrilliantearthScraper
from scrapers.diamondsfactory import DiamondsFactoryScraper
from utils.logger import setup_logger
import time
import pandas as pd
from helpers.email_service import send_error_email, send_completion_email
import datetime
from utils.db import pg_cursor


def bemain():
    driver = None
    total_items = 0
    logger = setup_logger(name="brilliantearth_scraper", file_name="brilliantearth")
    logger.info("Brilliantearth scraping job started.")
    
    start_time = time.time()
    total_scraped = 0
    total_failed = 0

    try:
        driver = get_firefox_driver(headless=False)
        scraper = BrilliantearthScraper(driver, logger)

        # Load input data
        logger.info("Loading input file: Brilliantearth_input_data.xlsx")
        df_input = pd.read_excel('files/brilliantearth/Brilliantearth_input_data2.xlsx')
        
        total_items = len(df_input)
        logger.info(f"Total input items: {total_items}")
        
        try:
            # Start scraping
            logger.info("Starting scrape...")
            scraped, failed = scraper.scrape()
            logger.info(f"Scraping completed. Success: {scraped}, Failed: {failed}")
            total_scraped += scraped
            total_failed += failed
        except Exception as e:
            logger.error(f"Scraping failed: {e}", exc_info=True)
            send_error_email("Brilliantearth", e)
            total_failed = total_items  # Assume all failed

    except Exception as e:
        logger.error(f"Initialization failed: {e}", exc_info=True)
        send_error_email("Brilliantearth", e)
        total_failed = total_items

    finally:
        if driver:
            driver.quit()

        execution_time = str(datetime.timedelta(seconds=time.time() - start_time))
        total_input_count = total_items

        today_str = datetime.datetime.today().strftime('%Y-%m-%d')
        pg_cursor.execute("""
            SELECT COUNT(*) 
            FROM public.stg_price_brilliantearth_scrape 
            WHERE updated_date_t = %s
        """, (today_str,))
        total_scraped_count = pg_cursor.fetchone()[0]
        pg_cursor.close()

        logger.info(f"Execution time: {execution_time}")
        logger.info(f"Scraped count in DB: {total_scraped_count}")

        send_completion_email("Brilliantearth", total_scraped, total_failed, execution_time, total_input_count, total_scraped_count)
        logger.info("Brilliantearth scraping job finished.\n")


if __name__ == "__main__":
    bemain()
