import datetime
from datetime import timedelta
import sys
import pandas as pd
from helpers.email_service import send_error_email
from helpers.webdriver_manager import get_firefox_driver
from scrapers.base_scraper import BaseScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from helpers.common_helper import (
    parse_numeric
)
from scrapers.diamondsfactory_helper import (
    get_full_product_description,
    metal_diamond_price,
    metal_select,
    stone_type_select,
    stone_shape_select,
    stone_carat_select,
    stone_color_select,
    stone_clarity_select,
    stone_cut_select,
    get_title,
    get_price,
    extract_all_product_details
)
from utils.db import pg_cursor

class DiamondsFactoryScraper(BaseScraper):

    def scrape(self):
        total_scraped = 0
        total_failed = 0

        try:
            self.driver.quit()

            df_input = pd.read_excel('files/diamondsfactory/diamondsfactory_input_final.xlsx')
            self.logger.info(f"Total input rows: {len(df_input)}")

            today_str = datetime.datetime.today().strftime('%Y-%m-%d')
            # today_str1 = datetime.datetime.today()
            # three_days_ago = today_str1 - datetime.timedelta(days=1)
            # today_str = three_days_ago.strftime('%Y-%m-%d')
            print("🗓️ Today's date for scraping: ", today_str)

            pg_cursor.execute("""
                SELECT product_url, category, sub_category, collection_no, metal, stone_type, stone_shape, stone_carat, color, clarity, cut
                FROM public.stg_price_df_scrape
                WHERE updated_date_t = %s
            """, (today_str,))
            rows = pg_cursor.fetchall()
            print(f"🛑 Total rows already scraped today: {len(rows)}")

            # 5. Convert DB result to DataFrame
            columns = ["product_url", "category", "sub_category", "collection_no", "metal", "stone_type", "stone_shape", "stone_carat", "color", "clarity", "cut"]
            df_scraped = pd.DataFrame(rows, columns=columns)
            print(f"🛑 Already scraped rows today: {len(df_scraped)}")

            # 6. Merge to find remaining rows
            df_merged = pd.merge(df_input, df_scraped, on=columns, how='left', indicator=True)
            df_remaining = df_merged[df_merged['_merge'] == 'left_only'].drop(columns=['_merge'])
            print(f"✅ Remaining rows to scrape: {len(df_remaining)}")


            for index, row in df_remaining.iterrows():
                try:
                    print("\n")
                    url = row['product_url']
                    metal = row['metal']
                    stone_type = row['stone_type']
                    stone_shape = row['stone_shape']
                    stone_carat = row['stone_carat']
                    color = row['color']
                    clarity = row['clarity']
                    cut = row['cut']

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
                    time.sleep(5)

                    stone_shape_select(driver, stone_shape)
                    time.sleep(5)

                    stone_carat_select(driver, stone_carat)
                    time.sleep(5)

                    stone_color_select(driver, color)
                    time.sleep(5)

                    stone_clarity_select(driver, clarity)
                    time.sleep(5)

                    stone_cut_select(driver, cut)
                    time.sleep(5)

                    # detail_json = extract_all_product_details(driver)
                    # print(f"Detail JSON: {detail_json}")
                    # time.sleep(1)

                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.13);")
                    time.sleep(2)  # Let elements load after scroll

                    title = get_title(driver, self.logger)
                    print(f"Title: {title}")

                    strike_price, final_price, rrp_price, you_save = get_price(driver, self.logger)
                    print(f"Strike Price: {strike_price}, Final Price: {final_price}, RRP Price: {rrp_price}, You Save: {you_save}")
                    
                    metal_price, diamond_price = metal_diamond_price(driver)
                    print(f"Metal Price: {metal_price}, Diamond Price: {diamond_price}")

                    full_product_description = get_full_product_description(driver)
                    print("📝 Full Product Description:\n", full_product_description)

                    updated_date = time.strftime("%Y-%m-%d %H:%M:%S")
                    # now = datetime.datetime.now()
                    # three_days_ago = now - datetime.timedelta(days=1)
                    # updated_date = three_days_ago.strftime("%Y-%m-%d %H:%M:%S")
                    print(f"Updated Date: {updated_date}")

                    row_data = row.to_dict()
                    row_data.update({
                        "product_title": title,
                        "metal_price": metal_price,
                        "stone_price": diamond_price,
                        "final_price": strike_price,
                        "product_description": full_product_description,
                        "updated_date": updated_date,
                        "promotion_price": final_price,
                        "rrp_price": rrp_price,
                        "you_save": you_save,
                        "updated_date_t": today_str
                        # "detail_json": detail_json
                    })

                    row_data["metal_price"] = parse_numeric(row_data.get("metal_price"))
                    row_data["stone_price"] = parse_numeric(row_data.get("stone_price"))
                    row_data["final_price"] = parse_numeric(row_data.get("final_price"))
                    row_data["promotion_price"] = parse_numeric(row_data.get("promotion_price"))
                    row_data["rrp_price"] = parse_numeric(row_data.get("rrp_price"))
                    row_data["you_save"] = parse_numeric(row_data.get("you_save"))

                    for key, value in row_data.items():
                        if value in ["", "N/A"] or pd.isna(value):
                            row_data[key] = None

                    print("row_data = ", row_data)

                    insert_query = """
                        INSERT INTO public.stg_price_df_scrape (
                            website, product_url, category, sub_category, collection_no, variant_no,
                            metal, stone_type, stone_shape, stone_carat, color, clarity, cut,
                            product_title, metal_price, stone_price, final_price, updated_date,
                            setting_title, setting_price, diamond_title, product_description,
                            additional_attributes, metal_price_e, stone_price_e, final_price_e,
                            updated_date_t, metal_t, stone_type_t, stone_shape_t,
                            clarity_t, cut_t, promotion_price, rrp_price, you_save
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s, %s, 
                            %s, %s, %s, %s, 
                            %s, %s, %s, %s, %s)
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
                        row_data.get("stone_shape"),
                        row_data.get("stone_carat"),
                        row_data.get("color"),
                        row_data.get("clarity"),
                        row_data.get("cut"),
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
                        row_data.get("metal_price_e"),
                        row_data.get("stone_price_e"),
                        row_data.get("final_price_e"),
                        row_data.get("updated_date_t"),
                        row_data.get("metal_t"),
                        row_data.get("stone_type_t"),
                        row_data.get("stone_shape_t"),
                        row_data.get("clarity_t"),
                        row_data.get("cut_t"),
                        row_data.get("promotion_price"),
                        row_data.get("rrp_price"),
                        row_data.get("you_save")
                    ]

                    pg_cursor.execute(insert_query, values)

                    self.logger.info(f"Inserted data into PostgreSQL for URL: {url}")
                    self.logger.info(f"Scraping completed for URL: {url}")

                    driver.quit()
                    total_scraped += 1

                except Exception as e:
                    self.logger.error(f"Failed to scrape {url}: {e}")
                    send_error_email("DiamondsFactory", e, url, row_data)
                    total_failed += 1
            return total_scraped, total_failed


        except Exception as e:
            self.logger.error(f"Fatal error in scrape method: {e}")
            send_error_email("DiamondsFactory", e)
            return 0, len(df_input)  # Assume all failed if we hit this
