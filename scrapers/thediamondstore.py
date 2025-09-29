import datetime
from datetime import timedelta
import re
import sys
import pandas as pd
from helpers.webdriver_manager import get_firefox_driver
from scrapers.base_scraper import BaseScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from helpers.email_service import send_error_email, send_completion_email
from scrapers.thediamondstore_helper import (
    cookie_consent,
    metal_click_view_button,
    click_view_by_section,
    diamond_choices_button,
    diamond_choices_button1,
    cross_button1,
    cross_button2,
    chatbot_button
)
import time

import psycopg2

from utils import logger
pg_conn = psycopg2.connect(
    host="178.79.182.27",
    database="briqpay",
    user="briqpay",
    password="briqpay111"
)
pg_conn.autocommit = True
pg_cursor = pg_conn.cursor()


class TheDiamondStoreScraper(BaseScraper):

    def scrape(self):
        total_scraped = 0
        total_failed = 0

        try:
            self.logger.info("Starting thediamondstore Scraper...")
            self.driver.quit()

            # urls = ['https://www.thediamondstore.co.uk/products/natalia-lab-diamond-engagement-side-stone-ring-18kw-gold-150ct-f-vs1']

            df_input = pd.read_excel('files/thediamondstore/thediamondstore_input.xlsx')
            self.logger.info(f"Total input rows: {len(df_input)}")

            today_str = datetime.datetime.today().strftime('%Y-%m-%d')
            # today_str1 = datetime.datetime.today()
            # three_days_ago = today_str1 - datetime.timedelta(days=200)
            # today_str = three_days_ago.strftime('%Y-%m-%d')
            self.logger.info("Today's date for scraping: %s", today_str)

            pg_cursor.execute("""
                SELECT product_url, category, sub_category, collection_no, metal, stone_type, stone_shape, stone_carat, color, clarity, cut
                FROM public.stg_price_thediamondstore_scrape
                WHERE updated_date_t = %s
            """, (today_str,))
            rows = pg_cursor.fetchall()
            self.logger.info("Total scraped rows: %d", len(rows))

            # 5. Convert DB result to DataFrame
            columns = ["product_url", "category", "sub_category", "collection_no", "metal", "stone_type", "stone_shape", "stone_carat", "color", "clarity", "cut"]
            df_scraped = pd.DataFrame(rows, columns=columns)

            for col in ["stone_carat"]:  # add more if needed
                df_input[col] = pd.to_numeric(df_input[col], errors="coerce")
                df_scraped[col] = pd.to_numeric(df_scraped[col], errors="coerce")

            # 6. Merge to find remaining rows
            df_merged = pd.merge(df_input, df_scraped, on=columns, how='left', indicator=True)
            df_remaining = df_merged[df_merged['_merge'] == 'left_only'].drop(columns=['_merge'])
            print(f"✅ Remaining rows to scrape: {len(df_remaining)}")

            for index, row in df_remaining.iterrows():

                print("\n")
                row_data = row.to_dict()
                print("row_data:", row_data)

                url = row_data.get('product_url')
                metal = row_data.get('metal')
                stone_type = row_data.get('stone_type')
                # stone_shape = row_data.get('stone_shape')
                # stone_carat = row_data.get('stone_carat')
                # color = row_data.get('color')
                # clarity = row_data.get('clarity')
                # cut = row_data.get('cut')

                self.logger.info(f"Scraping URL: {url}")
                self.logger.info(f"Scraping Metal: {metal}")
                self.logger.info(f"Scraping Stone Type: {stone_type}")
                # self.logger.info(f"Scraping Stone Shape: {stone_shape}")
                # self.logger.info(f"Scraping Stone Carat: {stone_carat}")
                # self.logger.info(f"Scraping Color: {color}")
                # self.logger.info(f"Scraping Clarity: {clarity}")
                # self.logger.info(f"Scraping Cut: {cut}")


                driver = get_firefox_driver(headless=False)
                driver.get(url)
                time.sleep(3)
                driver.execute_script("document.body.style.zoom='60%'")
                time.sleep(3)

                # driver.execute_script("document.body.style.zoom='80%'")
                # time.sleep(25)
                for i in range(30):
                    time.sleep(1)
                    print(i+1)
                print("Page loaded")

                # Accept cookie consent
                cookie_consent(driver)

                cross_button1(driver)

                cross_button2(driver)

                cross_button1(driver)

                chatbot_button(driver)



                # title = driver.find_element(By.CLASS_NAME, 'product-page-info__title').text
                # print(f"Title: {title}")

                # price = driver.find_element(By.CLASS_NAME, 'product-page-info__price').text
                # print(f"Price: {price}")

                diamond_choices_button(driver)

                # stone_type = 'Natural'
                # stone_type = 'Lab'
                # if stone_type == 'Natural':
                #     diamond_choice = driver.find_element(By.XPATH, "//div[normalize-space()='MINED']")
                # else:
                #     diamond_choice = driver.find_element(By.XPATH, "//div[contains(normalize-space(), 'SUSTAINABLE LAB')]")
                # diamond_choice.click()
                # print(f"Clicked diamond choice: {stone_type}")
                # time.sleep(5)

                if stone_type == 'Natural':
                    xpath = "//div[normalize-space()='MINED']"
                else:
                    xpath = "//div[contains(normalize-space(), 'SUSTAINABLE LAB')]"
                diamond_choice = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                # Scroll into view before clicking
                # driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", diamond_choice)
                diamond_choice.click()
                print(f"Clicked diamond choice: {stone_type}")
                time.sleep(5)


                # metal = '18K Yellow Gold'
                # metal = '18K White Gold'
                # metal = 'Platinum'
                # metal_click_view_button(driver, metal)
                # time.sleep(2)
                # click_view_by_section(driver, "SETTING", metal)
                # print("comple1")
                # time.sleep(5)
                success = click_view_by_section(driver, "SETTING", metal)
                if not success:
                    print(f"❌ Skipping {url} because metal '{metal}' not found.")
                    driver.quit()
                    continue   # Skip saving & go to next row

                print("✅ Metal selection successful")
                time.sleep(5)


                # print("strted")
                # diamond_choices_button1(driver)
                # time.sleep(10)
                # # clarity = 'F/VS1'
                # clarity = 'G/VS1'
                # # clarity = 'G/SI2'
                # # clarity = 'G/VS2'
                # click_view_by_section(driver, "CLARITY", clarity)
                # time.sleep(4)

                title = driver.find_element(By.CLASS_NAME, 'product-page-info__title').text
                print(f"Title: {title}")

                # price = driver.find_element(By.CLASS_NAME, 'product-page-info__price').text
                # print(f"Price: {price}")

                # ---- Extract Price ----
                # The main price is inside: <span class="price price--sale">
                price_element = driver.find_element(By.CSS_SELECTOR, "span.price.price--sale span:nth-of-type(2)")
                price_raw = price_element.text.strip()

                # ---- Extract RRP Price ----
                # The RRP is inside a <span> with text-decoration: line-through
                rrp_element = driver.find_element(By.CSS_SELECTOR, "span.price.price--sale span[style*='line-through']")
                rrp_price_raw = rrp_element.text.strip()

                print("price:", price_raw)
                print("rrp_price:", rrp_price_raw)

                try:
                    price = re.sub(r"[^\d.]", "", price_raw)
                except:
                    price = price_raw

                try:
                    rrp_price = re.sub(r"[^\d.]", "", rrp_price_raw)
                except:
                    rrp_price = rrp_price_raw

                print("price:", price)
                print("rrp_price:", rrp_price)



                updated_date = time.strftime("%Y-%m-%d %H:%M:%S")
                # now = datetime.datetime.now()
                # three_days_ago = now - datetime.timedelta(days=200)
                # updated_date = three_days_ago.strftime("%Y-%m-%d %H:%M:%S")
                print(f"Updated Date: {updated_date}")

                row_data.update({
                    "product_title": title,
                    "metal_price": price,
                    "final_price": rrp_price,
                    "updated_date": updated_date,
                    "updated_date_t": today_str,
                })

                for key, value in row_data.items():
                    if value in ["", "N/A"] or pd.isna(value):
                        row_data[key] = None

                self.logger.info("row_data = %s", row_data)

                insert_query = """
                    INSERT INTO public.stg_price_thediamondstore_scrape (
                        website, product_url, category, sub_category, collection_no, variant_no,
                        metal, stone_type, stone_shape, stone_carat, color, clarity, cut,
                        product_title, metal_price, stone_price, final_price, updated_date,
                        setting_title, setting_price, diamond_title, product_description,
                        additional_attributes, metal_t, stone_type_t, stone_shape_t,
                        clarity_t, cut_t, metal_price_e, stone_price_e, final_price_e,
                        updated_date_t, additional_title
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

                values = [
                    row_data.get("website"),
                    row_data.get("product_url"),
                    row_data.get("category"),
                    row_data.get("sub_category"),
                    row_data.get("collection_no"),
                    row_data.get("variant_no"),
                    row_data.get("metal"),
                    row_data.get("stone_type"),
                    # row_data.get("stone_shape"),
                    # row_data.get("stone_carat"),
                    # row_data.get("color"),
                    # row_data.get("clarity"),
                    # row_data.get("cut"),
                    row_data.get("product_title"),
                    row_data.get("metal_price"),
                    row_data.get("stone_price"),
                    row_data.get("final_price"),
                    row_data.get("updated_date"),
                    row_data.get("setting_title"),
                    row_data.get("setting_price"),
                    row_data.get("diamond_title"),
                    row_data.get("product_description"),
                    row_data.get("additional_attributes"),
                    row_data.get("metal_t"),
                    row_data.get("stone_type_t"),
                    row_data.get("stone_shape_t"),
                    row_data.get("clarity_t"),
                    row_data.get("cut_t"),
                    row_data.get("metal_price_e"),
                    row_data.get("stone_price_e"),
                    row_data.get("final_price_e"),
                    row_data.get("updated_date_t"),
                    row_data.get("additional_title")
                ]

                pg_cursor.execute(insert_query, values)


                self.logger.info(f"Inserted data into PostgreSQL for URL: {url}")
                self.logger.info(f"Scraping completed for URL: {url}")

                driver.quit()

                time.sleep(10)
        except Exception as e:
            print("Error occurred while scraping:", e)


# <button type="button" style="min-width: 150px;" class=" pKrqgcVNmqUx8tgLuy22 FGuZn6Hqld825JDQ3Obf bxUFNq8u5loIAs30Tnxm cc-btn cc-allow isense-cc-btn isense-cc-allow isense-cc-submit-consent" aria-label="Accept">Accept</button>
