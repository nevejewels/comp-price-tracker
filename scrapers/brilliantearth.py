import sys
import pandas as pd
from helpers.webdriver_manager import get_firefox_driver
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
    get_title_price,
    click_stone_shape,
    select_clarity,
    select_color,
    select_cut,
    set_carat_range,
    get_product_details
)
import time

import psycopg2
pg_conn = psycopg2.connect(
    host="178.79.182.27",
    database="briqpay",
    user="briqpay",
    password="briqpay111"
)
pg_conn.autocommit = True
pg_cursor = pg_conn.cursor()


class BrilliantearthScraper(BaseScraper):

    def scrape(self):
        print("Starting Brilliant Earth Scraper...")
        self.driver.quit()

        # urls = ['https://www.brilliantearth.com/en-gb/1.4mm-Provence-Solitaire-Ring-Gold-BE1776-4345169/',
        #         'https://www.77diamonds.com/engagement-rings/solitaire/round/white-gold?item=188']
        # urls = ['https://www.brilliantearth.com/en-gb/1.4mm-Provence-Solitaire-Ring-Gold-BE1776-4345169/']
        # urls = ['https://www.brilliantearth.com/en-gb/rings/cyorings/purchase_review/?did=47345275&sid=4345169']
        # urls = ['https://www.brilliantearth.com/en-gb/rings/cyorings/purchase_review/?sid=4345169&did=46944384']

        # df01 = pd.read_excel('files/common_price_inputfile.xlsx')
        # print(df01.shape)


        df_input = pd.read_excel('files/brilliantearth/Brilliantearth_input_data.xlsx')
        self.logger.info(f"Total input rows: {len(df_input)}")

        # match_columns = [
        #     "product_url",
        #     "metal",
        #     "stone_type",
        #     "stone_shape",
        #     "stone_carat",
        #     "color",
        #     "clarity",
        #     "cut"
        # ]

        # # Fetch only match_columns from MongoDB
        # existing_docs = list(collection.find({}, {col: 1 for col in match_columns}))

        # if not existing_docs:
        #     self.logger.info("No existing records found in MongoDB. Scraping all rows.")
        #     df_to_scrape = df_input.copy()
        # else:
        #     df_existing = pd.DataFrame(existing_docs)
        #     self.logger.info(f"Already crawled rows in DB: {len(df_existing)}")

        #     # Merge input with existing to find uncrawled ones
        #     df_merged = pd.merge(df_input, df_existing, on=match_columns, how='left', indicator=True)
        #     df_to_scrape = df_merged[df_merged['_merge'] == 'left_only'].drop(columns=['_merge'])

        # self.logger.info(f"Remaining rows to scrape: {len(df_to_scrape)}")


        # print(df_to_scrape.head())
        # print()

        for index, row in df_input.iterrows():
            print("\n")
            row_data = row.to_dict()
            print("row_data:", row_data)

            url = row_data.get('product_url')
            metal = row_data.get('metal')
            stone_type = row_data.get('stone_type')
            stone_shape = row_data.get('stone_shape')
            stone_carat = row_data.get('stone_carat')
            color = row_data.get('color')
            clarity = row_data.get('clarity')
            cut = row_data.get('cut')

            self.logger.info(f"Scraping URL: {url}")
            self.logger.info(f"Scraping Metal: {metal}")
            self.logger.info(f"Scraping Stone Type: {stone_type}")
            self.logger.info(f"Scraping Stone Shape: {stone_shape}")
            self.logger.info(f"Scraping Stone Carat: {stone_carat}")
            self.logger.info(f"Scraping Color: {color}")
            self.logger.info(f"Scraping Clarity: {clarity}")
            self.logger.info(f"Scraping Cut: {cut}")


        # for url in urls:
            driver = get_firefox_driver(headless=False)
            driver.get(url)
            time.sleep(3)

            # Accept cookies if the prompt appears
            accept_cookies(driver)
            time.sleep(4)

            # Get the title of the page

            # metal_val = "18K White Gold" # "18K Yellow Gold" "14K Rose Gold" "Platinum"
            metal_val = metal
            click_metal_option(driver, self.logger, metal_val)
            time.sleep(8)

            # style_name = "Classic" # "Hidden Halo"
            # click_style_option(driver, self.logger, style_name)

            # stone_type_val = "Natural" # "Lab Grown"
            stone_type_val = stone_type
            click_stonetype_diamond(driver, self.logger, stone_type_val)
            time.sleep(5)

            initial_title, metal_price = get_title_price(driver, self.logger)
            time.sleep(1)

            try:
                product_details = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[span[text()='Product Details']]"))
                )
                product_details.click()
                print("**** Clicked Product Details successfully.")
            except Exception as e:
                print(f"❌ Could not click Product Details: {e}")
            time.sleep(2)

            # product_detail = driver.find_element(By.ID, "headingOne")



            try:
                button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "add_cyoring"))
                )
                button.click()
                self.logger.info("Clicked 'CHOOSE THIS SETTING' button successfully.")
            except Exception as e:
                self.logger.error(f"Failed to click 'CHOOSE THIS SETTING' button: {e}")
            time.sleep(8)

            # stone_shape_value = "Round" # "Oval" "Emerald" "Cushion" "Elongated Cushion" "Radiant" "Princess" "Asscher"
            stone_shape_value = stone_shape
            click_stone_shape(driver, self.logger, stone_shape_value)
            time.sleep(2)

            stone_carat_value = stone_carat
            set_carat_range(driver, self.logger, stone_carat_value, stone_carat_value)
            time.sleep(2)

            # cut_values = "Fair" "Good" "Very Good" "Ideal" "Super Ideal"
            cut_values = cut
            select_cut(driver, self.logger, cut_values)
            time.sleep(2)


            color_val = color
            select_color(driver, self.logger, color_val)
            time.sleep(2)


            # clarity_val = "SI2" # "SI1" "VS2" "VS1" "VVS2" "VVS1" "IF" "FL"
            clarity_val = clarity
            select_clarity(driver, self.logger, clarity_val)
            time.sleep(2)

            result01 = click_first_select_diamond(driver, self.logger)
            if result01:
                time.sleep(10)
                product_details = get_product_details(driver, self.logger)
                initial_title = initial_title
                metal_price = metal_price
                additional_title = product_details['title']
                total_price = product_details['price']
                setting_title = product_details['setting_title']
                setting_price = product_details['setting_price']
                diamond_title = product_details['diamond_title']
                stone_price = product_details['diamond_price']

            else:
                initial_title = ""
                metal_price = ""
                additional_title = ""
                total_price = ""
                setting_title = ""
                setting_price = ""
                diamond_title = ""
                stone_price = ""
            print("initial_title:", initial_title)
            print("metal_price:", metal_price)
            print("additional_title:", additional_title)
            print("total_price:", total_price)
            print("setting_title:", setting_title)
            print("setting_price:", setting_price)
            print("diamond_title:", diamond_title)
            print("stone_price:", stone_price)

            row_data.update({
                "product_title": initial_title,
                "metal_price": metal_price,
                "stone_price": stone_price,
                "final_price": total_price,
                "updated_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "setting_title": setting_title,
                "setting_price": setting_price,
                "diamond_title": diamond_title,
                "updated_date_t": time.strftime("%Y-%m-%d"),
                "additional_title": additional_title
            })

            # # Insert into MongoDB
            # row_data.pop('_id', None)
            # for key, value in row_data.items():
            #     if pd.isna(value):
            #         row_data[key] = None
            # collection.insert_one(row_data)

            for key, value in row_data.items():
                if value in ["", "N/A"]:
                    row_data[key] = None

            print("row_data = ", row_data)

            insert_query = """
                INSERT INTO public.price_brilliantearth_scrape (
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


