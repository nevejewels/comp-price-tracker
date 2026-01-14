import os
import re
import time
import json
import random
import threading
import concurrent.futures
from datetime import datetime

import pandas as pd
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, StaleElementReferenceException, ElementClickInterceptedException,
    NoSuchElementException, WebDriverException
)

# ====================== USER CONFIG ======================
INPUT_CSV = r"C:\Users\komal.kumavat\Downloads\A&B_InputFile - Sheet1.csv"
OUTPUT_CSV = r"C:\Users\komal.kumavat\Downloads\output_results_5thOCT.csv"
SCREENSHOTS_DIR = r"C:\Users\komal.kumavat\Downloads\screenshots"

# Concurrency & politeness
MAX_WORKERS = 2               # <-- two threads
JITTER_MIN, JITTER_MAX = 0.15, 0.45 # tiny random sleep around actions

# Retry & nav tuning
UNLIMITED_RETRY = True
MAX_ATTEMPTS_PER_URL = 8            # used only if UNLIMITED_RETRY = False
PAGE_LOAD_TIMEOUT = 45              # seconds
NAV_RESTART_EVERY = 3               # restart driver after these many nav fails
BASE_BACKOFF = 1.0                  # seconds
MAX_BACKOFF = 20.0                  # seconds

# =========================================================

# Globals for thread-safe writing
write_lock = threading.Lock()

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

ensure_dir(SCREENSHOTS_DIR)

def rando(min_s=JITTER_MIN, max_s=JITTER_MAX):
    time.sleep(random.uniform(min_s, max_s))

def now_ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def backoff_sleep(attempt, base=BASE_BACKOFF, cap=MAX_BACKOFF):
    delay = min(cap, base * (2 ** max(0, attempt-1)))
    time.sleep(delay)

def append_result_row(row_dict):
    """Thread-safe append to CSV."""
    with write_lock:
        mode = 'a' if os.path.exists(OUTPUT_CSV) else 'w'
        header = not os.path.exists(OUTPUT_CSV)
        try:
            pd.DataFrame([row_dict]).to_csv(
                OUTPUT_CSV, index=False, encoding="utf-8-sig",
                mode=mode, header=header
            )
        except Exception as e:
            print(f"❌ Error appending result row: {e}")

def load_resume_set(output_csv):
    done = set()
    if os.path.exists(output_csv):
        try:
            prev = pd.read_csv(output_csv)
            if 'product_url' in prev.columns and 'status' in prev.columns:
                done = set(prev.loc[prev['status'] == 'success', 'product_url'].astype(str))
                print(f"🔁 Resume mode: {len(done)} URLs already done (skipping).")
        except Exception as e:
            print(f"⚠️ Could not read existing OUTPUT_CSV for resume: {e}")
    return done

# ---------------------- Driver Builder ----------------------
def build_driver():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")  # uncomment for headless
    options.add_argument("--window-size=1920,1080")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    d = webdriver.Chrome(options=options)
    d.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    try:
        d.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    except Exception:
        pass
    return d

# ---------------------- Per-Thread Scraper ----------------------
class Scraper:
    def __init__(self, thread_name="T"):
        self.thread_name = thread_name
        self.driver = build_driver()
        self.wait = WebDriverWait(self.driver, 20)
        self.actions = ActionChains(self.driver)

    def restart_driver(self):
        try:
            self.driver.quit()
        except Exception:
            pass
        time.sleep(1.0)
        self.driver = build_driver()
        self.wait = WebDriverWait(self.driver, 20)
        self.actions = ActionChains(self.driver)

    # ---- helpers (bound to this driver) ----
    def sleep_safely(self, seconds=0.7):
        time.sleep(seconds)

    def scroll_into_view_center(self, el, offset_y=-120):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", el)
            self.driver.execute_script("window.scrollBy(0, arguments[0]);", offset_y)
            rando()
        except Exception:
            pass

    def js_click(self, el):
        self.driver.execute_script("arguments[0].click();", el)

    def safe_click(self, locator, by=By.XPATH, timeout=12, center=True, retries=2, allow_js_fallback=True):
        last_err = None
        for _ in range(retries + 1):
            try:
                el = WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located((by, locator)))
                if center:
                    self.scroll_into_view_center(el)
                el = WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable((by, locator)))
                try:
                    el.click()
                except (ElementClickInterceptedException, StaleElementReferenceException):
                    if allow_js_fallback:
                        try:
                            self.js_click(el)
                            return True
                        except Exception:
                            try:
                                self.actions.move_to_element(el).click().perform()
                                return True
                            except Exception:
                                pass
                return True
            except Exception as e:
                last_err = e
                rando(0.4, 0.9)
        return False

    def robust_click(self, el, max_retries=3):
        for _ in range(max_retries):
            try:
                self.scroll_into_view_center(el)
                rando()
                el.click()
                return True
            except Exception:
                try:
                    self.js_click(el)
                    return True
                except Exception:
                    try:
                        self.actions.move_to_element(el).click().perform()
                        return True
                    except Exception:
                        pass
            rando(0.3, 0.7)
        return False

    def take_screenshot(self, filename_prefix, idx, attempt=None):
        try:
            ts = now_ts()
            attempt_part = f"_try{attempt:02d}" if attempt is not None else ""
            filename = f"{filename_prefix}_{self.thread_name}_{idx+1:03d}{attempt_part}_{ts}.png"
            path = os.path.join(SCREENSHOTS_DIR, filename)
            self.driver.execute_script("window.scrollTo(0, 0);")
            rando(0.3, 0.6)
            self.driver.save_screenshot(path)
            print(f"📸 [{self.thread_name}] Screenshot saved: {filename}")
            return filename
        except Exception as e:
            print(f"❌ [{self.thread_name}] Screenshot failed: {e}")
            return None

    # ---- navigation robustness ----
    def wait_for_dom_ready(self, timeout=25):
        end = time.time() + timeout
        last_error = None
        while time.time() < end:
            try:
                ready = self.driver.execute_script("return document.readyState")
                body_len = self.driver.execute_script(
                    "return document.body && document.body.innerText ? document.body.innerText.length : 0")
                if ready == "complete" and body_len and int(body_len) > 50:
                    return True
            except WebDriverException as e:
                last_error = e
            time.sleep(0.3)
        if last_error:
            raise last_error
        return False

    def page_has_product_signals(self):
        try:
            candidates = [
                (By.XPATH, "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'add to cart') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'add to bag')]"),
                (By.CSS_SELECTOR, ".panel"),
                (By.XPATH, "//span[contains(@class,'caret') or self::span[@class='caret']]"),
            ]
            for by, sel in candidates:
                elems = self.driver.find_elements(by, sel)
                if any(e.is_displayed() for e in elems):
                    return True
        except Exception:
            pass
        return False

    def open_url_with_retries(self, url, idx):
        attempt = 0
        fails_since_restart = 0
        while True:
            attempt += 1
            try:
                print(f"🌐 [{self.thread_name}] Navigating (attempt {attempt}): {url}")
                try:
                    self.driver.get(url)
                except TimeoutException:
                    print(f"⏱️ [{self.thread_name}] Page load timed out, stopping load and checking DOM…")
                    try: self.driver.execute_script("window.stop();")
                    except Exception: pass

                if not self.wait_for_dom_ready(timeout=25):
                    raise TimeoutException("DOM not ready after navigation")

                time.sleep(0.8)  # settle
                if not self.page_has_product_signals():
                    raise TimeoutException("Product signals not found")

                print(f"✅ [{self.thread_name}] Nav ok")
                return True, attempt, None

            except Exception as e:
                print(f"⚠️ [{self.thread_name}] Nav attempt {attempt} failed: {e}")
                self.take_screenshot("nav_fail", idx, attempt=attempt)
                fails_since_restart += 1

                if fails_since_restart >= NAV_RESTART_EVERY:
                    print(f"🔄 [{self.thread_name}] Restarting browser to clear state…")
                    self.restart_driver()
                    fails_since_restart = 0

                backoff_sleep(attempt)

                if not UNLIMITED_RETRY and attempt >= MAX_ATTEMPTS_PER_URL:
                    return False, attempt, e

    # ---- site interactions (ported) ----
    def accept_cookies(self):
        selectors = [
            "//button[@id='onetrust-accept-btn-handler']",
            "//button[contains(@class, 'accept-cookies')]",
            "//button[contains(@class, 'cookie-accept')]",
            "//button[contains(text(), 'Accept')]",
            "//button[contains(text(), 'OK')]",
            "#cookie-accept",
            ".cookie-accept",
            "[data-cookie-accept]"
        ]
        for selector in selectors:
            try:
                by_type = By.XPATH if selector.startswith("//") or selector.startswith("(") else By.CSS_SELECTOR
                element = WebDriverWait(self.driver, 4).until(EC.element_to_be_clickable((by_type, selector)))
                element.click()
                rando()
                return True
            except Exception:
                continue
        return False

    def open_ring_size_dropdown(self):
        opened = self.safe_click("//span[contains(@class,'caret') or self::span[@class='caret']]", timeout=8)
        rando()
        return opened

    def close_ring_size_dropdown(self):
        try:
            self.actions.send_keys(Keys.ESCAPE).perform()
            rando(0.1, 0.2)
            return True
        except Exception:
            return False

    def choose_ring_size_M(self):
        if not self.open_ring_size_dropdown():
            return None
        option_xpath = "//a[.//span[normalize-space()='M']]"
        try:
            el = self.wait.until(EC.visibility_of_element_located((By.XPATH, option_xpath)))
            self.scroll_into_view_center(el)
            rando(0.08, 0.2)
            try:
                el.click()
            except (ElementClickInterceptedException, StaleElementReferenceException):
                self.js_click(el)
            rando(0.08, 0.2)
        except TimeoutException:
            self.close_ring_size_dropdown()
            return None
        self.close_ring_size_dropdown()
        rando(0.08, 0.2)
        return "M"

    def choose_generic_option(self, field, value, exact=False):
        if not value or str(value).strip() == "":
            return None
        needle = str(value).strip()
        if field == "stone_carat":
            try:
                needle = f"{float(needle):.2f}"
            except Exception:
                needle = needle
            xpath = f"//li[@custom_field='stone_carat' and @namer='{needle}']"
        else:
            nlow = needle.lower()
            if exact:
                xpath = f"//li[@custom_field='{field}' and translate(@namer,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')='{nlow}']"
            else:
                xpath = f"//li[@custom_field='{field}' and contains(translate(@namer,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{nlow}')]"
        if self.safe_click(xpath):
            rando(0.1, 0.25)
            return needle
        return None

    def scroll_product_page_deep(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        rando(0.15, 0.3)
        self.driver.execute_script("window.scrollTo(0, 0);")
        rando(0.1, 0.2)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
        rando(0.1, 0.2)

    # ---------------------- NEW: PDP price scraping ----------------------
    def _collect_price_texts(self, elements):
        """Return ordered unique list of currency-like strings from elements' text."""
        prices = []
        seen = set()
        # currency tokens like £1,234.56 / $1,234 / €1.234,56 etc. (keep simple UK/US/EU patterns)
        price_re = re.compile(r"(?:£|\$|€)\s?\d[\d,\.]*")
        for el in elements:
            try:
                txt = (el.text or el.get_attribute("innerText") or "").strip().replace("\xa0", " ")
                for match in price_re.findall(txt):
                    m = match.strip()
                    if m and m not in seen:
                        seen.add(m)
                        prices.append(m)
            except Exception:
                continue
        return prices

    def _first_text(self, css_list):
        for sel in css_list:
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, sel)
                tx = (el.text or el.get_attribute("innerText") or "").strip().replace("\xa0", " ")
                if tx:
                    return tx
            except Exception:
                continue
        return ""

    def scrape_pdp_prices(self):
        """
        Extract prices visible on the Product Detail Page before adding to bag.
        Returns keys:
            - pdp_current_price
            - pdp_strike_price
            - pdp_offer_text
            - pdp_price_candidates
        """
        data = {}
        try:
            # Give dynamic price a moment to settle
            for _ in range(6):
                # Broad net: anything with id/class containing 'price'
                price_elems = self.driver.find_elements(
                    By.XPATH,
                    "//*[contains(translate(@class,'PRICE','price'),'price') or contains(translate(@id,'PRICE','price'),'price')]"
                )
                prices = self._collect_price_texts(price_elems)
                if prices:
                    break
                time.sleep(0.4)

            # Specific selectors we know often exist
            strike = self._first_text([".strike-price", ".old-price", ".was-price", ".rrp"])
            offer  = self._first_text([".offer-text", ".promo", ".badge-offer", ".savings"])

            # Prefer very specific 'metalPrice' if present for current price
            curr_specific = self._first_text(["#metalPrice", "[id*='metalPrice']", ".price.cartPrice"])
            pdp_current = ""
            if curr_specific:
                # From that block, pull first currency token
                m = re.search(r"(?:£|\$|€)\s?\d[\d,\.]*", curr_specific)
                if m:
                    pdp_current = m.group(0).strip()

            if not pdp_current and prices:
                # Heuristic: last price on page is often the live price near CTA
                pdp_current = prices[-1]

            data["pdp_current_price"] = pdp_current
            if strike:
                m = re.search(r"(?:£|\$|€)\s?\d[\d,\.]*", strike)
                if m:
                    data["pdp_strike_price"] = m.group(0).strip()
            if offer:
                data["pdp_offer_text"] = offer
            if prices:
                data["pdp_price_candidates"] = " | ".join(prices)
        except Exception as e:
            data["pdp_price_error"] = str(e)
        return data

    # ---------------------- Description & details ----------------------
    def scrape_complete_description(self):
        out = {}
        try:
            panels = []
            for _ in range(10):
                panels = self.driver.find_elements(By.CSS_SELECTOR, ".panel")
                found = False
                for panel in panels:
                    if "You have selected" in panel.get_attribute("innerText"):
                        found = True
                        break
                if found:
                    break
                self.sleep_safely(0.6)

            target_panel = None
            for panel in panels:
                if "You have selected" in panel.get_attribute("innerText"):
                    target_panel = panel
                    break

            if not target_panel:
                print(f"⚠️ [{self.thread_name}] No product description panel found")
                out["description_full"] = ""
                return out

            html = target_panel.get_attribute("innerHTML")
            soup = BeautifulSoup(html, "html.parser")

            full_desc = []
            for p in soup.find_all("p"):
                full_desc.append(" ".join(p.stripped_strings))
            h2 = soup.find("h2", {"class": "product_varaint_main"})
            if h2:
                full_desc.append(" ".join(h2.stripped_strings))

            desc_line = " ".join(full_desc)
            desc_line = re.sub(r"\s+", " ", desc_line).replace('\xa0', ' ').strip()
            out["description_full"] = desc_line

            print(f"✅ [{self.thread_name}] Description extracted ({len(desc_line)} chars)")
        except Exception as e:
            print(f"❌ [{self.thread_name}] Error in description extraction: {e}")
            out["description_full"] = ""
        return out

    def scrape_ring_and_diamond_details(self):
        out = {}
        try:
            details_btn = self.driver.find_element(
                By.XPATH, "//button[contains(@class,'accordion') and contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'ring') and contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'diamond')]"
            )
            self.scroll_into_view_center(details_btn)
            rando(0.15, 0.3)
            if "active" not in details_btn.get_attribute("class"):
                self.robust_click(details_btn)
                rando(0.15, 0.3)
            panel = None
            siblings = details_btn.find_elements(By.XPATH, "following-sibling::*")
            for sib in siblings:
                if "panel" in sib.get_attribute("class"):
                    panel = sib
                    break
            if not panel:
                panels = self.driver.find_elements(By.CSS_SELECTOR, ".product-details-section .panel, .panel")
                for p in panels:
                    if p.is_displayed() and p.find_elements(By.CSS_SELECTOR, ".pro-details-sec"):
                        panel = p
                        break
            if not panel:
                return out
            details_section = None
            try:
                details_section = panel.find_element(By.CSS_SELECTOR, ".pro-details-sec")
            except Exception:
                cand = panel.find_elements(By.CSS_SELECTOR, ".pro-details-sec")
                if cand:
                    details_section = cand[0]
            if not details_section:
                return out
            self.scroll_into_view_center(details_section)
            rando(0.1, 0.2)
            out["ring_diamond_details_html"] = details_section.get_attribute("innerHTML")
            out["ring_diamond_details_text"] = details_section.text.strip().replace('\n', ' ').replace('\r', ' ')
        except Exception as e:
            out["ring_diamond_extraction_error"] = str(e)
        return out

    # ---------------------- NEW: Cart price scraping ----------------------
    def scrape_cart_details(self):
        """
        Works on both dedicated cart page and side drawer.
        Returns keys including:
          - cart_currency, cart_value, coupon_code
          - item_* fields (from data-ga-cart-data)
          - summary_* lines (Subtotal, VAT, Coupon, Total)
          - cart_prices_found (visible prices fallback)
        """
        data = {}

        # Try the analytics payload
        try:
            json_str = self.driver.execute_script(
                "var el = document.querySelector('#checkout-cart');"
                "return el ? el.getAttribute('data-ga-cart-data') : null;"
            )
            if json_str:
                j = json.loads(json_str)
                data["cart_currency"] = j.get("currency", "")
                data["cart_value"] = j.get("value", "")
                data["coupon_code"] = j.get("coupon", "")
                items = j.get("items", [])
                if items:
                    itm = items[0]
                    data.update({
                        "item_id": itm.get("item_id", ""),
                        "item_name": itm.get("item_name", ""),
                        "item_brand": itm.get("item_brand", ""),
                        "item_category": itm.get("item_category", ""),
                        "item_variant": itm.get("item_variant", ""),
                        "cart_item_price": itm.get("price", ""),
                        "cart_item_qty": itm.get("quantity", ""),
                        "cart_id": itm.get("cart_id", ""),
                        "metal_purity_cart": itm.get("metal_purity", ""),
                        "ring_size_cart": itm.get("ring_size", ""),
                        "stone_type_cart": itm.get("stone_type", ""),
                        "stone_carat_cart": itm.get("stone_carat", ""),
                        "stone_clarity_cart": itm.get("stone_clarity", ""),
                        "stone_color_cart": itm.get("stone_color", ""),
                        "stone_cut_cart": itm.get("stone_cut", ""),
                        "stone_certificate_cart": itm.get("stone_certificate", ""),
                        "band_width_cart": itm.get("band_width", ""),
                        "stone_shape_cart": itm.get("stone_shape", ""),
                    })
        except Exception:
            # silently ignore if the attribute or json is missing/bad
            pass

        # Visible cart text (fallbacks)
        try:
            sel = ".cartPrice, .checkout_option.prodetailhed, .price, .cart-total, .summary_total, #total, .strike-price"
            found = self.driver.find_elements(By.CSS_SELECTOR, sel)
            prices = []
            for el in found:
                tx = (el.text or "").strip().replace('\n', ' ').replace('\xa0', ' ')
                if tx and any(c.isdigit() for c in tx):
                    prices.append(tx)
            if prices:
                data["cart_prices_found"] = " | ".join(prices)
        except Exception:
            pass

        # Totals table (Subtotal / VAT / Coupon / Total)
        try:
            rows = self.driver.find_elements(By.XPATH, "//table[contains(@class,'table-price')]//tr")
            for r in rows:
                left = ""
                right = ""
                try:
                    left = r.find_element(By.CSS_SELECTOR, ".pull-left").text.strip()
                except Exception:
                    try:
                        left = r.find_elements(By.TAG_NAME, "td")[0].text.strip()
                    except Exception:
                        pass
                try:
                    right = r.find_element(By.CSS_SELECTOR, ".pull-right").text.strip()
                except Exception:
                    try:
                        tds = r.find_elements(By.TAG_NAME, "td")
                        right = tds[-1].text.strip() if tds else ""
                    except Exception:
                        pass
                if left:
                    key = left.lower().strip().replace(" ", "_").replace(":", "")
                    data[f"summary_{key}"] = right
        except Exception:
            pass

        # Sticky total (if available)
        try:
            el = self.driver.find_element(By.CSS_SELECTOR, ".sticky-total-price .sticky-amount")
            data["sticky_total"] = el.text.strip()
        except Exception:
            pass

        return data

    # ---------------------- Add to cart ----------------------
    def add_to_cart_and_screenshot(self, idx, attempt):
        cart_data = {}
        cart_screenshot = None
        try:
            add_button = None
            selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add to cart')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add to bag')]",
                "//input[@type='submit' and contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add to cart')]",
                "//input[@type='submit' and contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add to bag')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add to cart')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add to bag')]",
                "//button[@id='add-to-cart']",
                "//button[@id='add-to-bag']",
                "//button[contains(@class, 'add-to-cart')]",
                "//button[contains(@class, 'add-to-bag')]",
                ".add-to-cart",
                ".add-to-bag",
                "#add-to-cart",
                "#add-to-bag"
            ]
            for selector in selectors:
                try:
                    by_type = By.XPATH if selector.startswith("//") or selector.startswith("(") else By.CSS_SELECTOR
                    add_button = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((by_type, selector)))
                    break
                except TimeoutException:
                    continue
            if not add_button:
                cart_data["add_to_cart_status"] = "button_not_found"
                return cart_data, None
            self.scroll_into_view_center(add_button)
            rando(0.2, 0.4)
            try:
                add_button.click()
            except (ElementClickInterceptedException, StaleElementReferenceException):
                try:
                    self.js_click(add_button)
                except Exception:
                    try:
                        self.actions.move_to_element(add_button).click().perform()
                    except Exception as e:
                        cart_data["add_to_cart_status"] = "click_failed"
                        cart_data["add_to_cart_error"] = str(e)
                        return cart_data, None

            # Give time for modal or cart page
            self.sleep_safely(1.8)

            # If a minicart showed up, great; else try to click to the cart page
            try:
                minicart = self.driver.find_elements(By.CSS_SELECTOR, ".minicart, .cart-modal, #cart-modal")
                if not any(el.is_displayed() for el in minicart):
                    # Try cart icon / link if present
                    for sel in ["a[href*='cart']", "a[href*='bag']", ".cart-link", ".bag-link", "#cart-link", "#bag-link"]:
                        try:
                            el = self.driver.find_element(By.CSS_SELECTOR, sel)
                            if el.is_displayed():
                                self.scroll_into_view_center(el)
                                self.robust_click(el)
                                break
                        except Exception:
                            continue
                    self.sleep_safely(1.0)
            except Exception:
                pass

            cart_data["add_to_cart_status"] = "success"
            cart_data["cart_url"] = self.driver.current_url
            cart_screenshot = self.take_screenshot("cart_page", idx, attempt=attempt)
        except Exception as e:
            cart_data["add_to_cart_status"] = "error"
            cart_data["add_to_cart_error"] = str(e)
        return cart_data, cart_screenshot

    # ------------------ one product end-to-end ------------------
        # ------------------ one product end-to-end ------------------
    def process_product(self, idx, row):
        url = str(row["product_url"]).strip()
        attempt = 0

        while True:
            attempt += 1
            status = "success"
            error_reason = ""
            desc_data = {}
            ring_diamond_data = {}
            cart_data = {}
            pdp_price_data = {}
            cart_price_data = {}
            screenshot_filename = None
            cart_screenshot_filename = None
            selected_metal = None
            selected_size = None
            selected_stone_type = None
            selected_shape = None
            selected_carat = None
            selected_clarity = None
            selected_color = None
            selected_cut = None

            try:
                ok, _, nav_err = self.open_url_with_retries(url, idx)
                if not ok:
                    raise nav_err or Exception("Navigation failed without explicit error")

                try: 
                    self.accept_cookies()
                except: 
                    pass

                # Selections (non-fatal)
                try: selected_metal = self.choose_generic_option("metal_purity", row.get("metal", ""), exact=False); rando()
                except Exception as e: print(f"[{self.thread_name}] Metal selection error: {e}")
                try: selected_size = self.choose_ring_size_M(); rando()
                except Exception as e: print(f"[{self.thread_name}] Ring size selection error: {e}")
                try: selected_stone_type = self.choose_generic_option("stone_type", row.get("stone_type", ""), exact=True); rando()
                except Exception as e: print(f"[{self.thread_name}] Stone type selection error: {e}")
                try: selected_shape = self.choose_generic_option("stone_shape", row.get("stone_shape", ""), exact=False); rando()
                except Exception as e: print(f"[{self.thread_name}] Shape selection error: {e}")
                try: selected_carat = self.choose_generic_option("stone_carat", row.get("stone_carat", ""), exact=True); rando()
                except Exception as e: print(f"[{self.thread_name}] Carat selection error: {e}")
                try: selected_clarity = self.choose_generic_option("stone_clarity", row.get("clarity", ""), exact=False); rando()
                except Exception as e: print(f"[{self.thread_name}] Clarity selection error: {e}")
                try: selected_color = self.choose_generic_option("stone_color", row.get("color", ""), exact=False); rando()
                except Exception as e: print(f"[{self.thread_name}] Color selection error: {e}")
                try: selected_cut = self.choose_generic_option("stone_cut", row.get("cut", ""), exact=False); rando()
                except Exception as e: print(f"[{self.thread_name}] Cut selection error: {e}")

                self.scroll_product_page_deep()
                self.sleep_safely(0.4)

                # Prices BEFORE add to cart
                pdp_price_data = self.scrape_pdp_prices()

                screenshot_filename = self.take_screenshot("product_page", idx, attempt=attempt)
                desc_data = self.scrape_complete_description(); rando(0.05, 0.15)
                ring_diamond_data = self.scrape_ring_and_diamond_details(); rando(0.05, 0.15)

                # Add to cart and collect cart details
                cart_data, cart_screenshot_filename = self.add_to_cart_and_screenshot(idx, attempt)
                cart_price_data = self.scrape_cart_details()

                print(f"✅ [{self.thread_name}] Done product {idx+1} (attempt {attempt})")

            except KeyboardInterrupt:
                print(f"🛑 [{self.thread_name}] Stopped by user.")
                raise
            except Exception as e:
                status = "error"
                error_reason = f"General error: {e}"
                print(f"❌ [{self.thread_name}] Error product {idx+1} attempt {attempt}: {e}")
                try: 
                    screenshot_filename = self.take_screenshot("error_page", idx, attempt=attempt)
                except: 
                    pass

            # ======================= FINAL SCHEMA =======================
            row_out = {
                "website": row.get("website", ""),
                "product_url": url,
                "category": row.get("category", ""),
                "sub_category": row.get("subcategory", ""),
                "collection_no": row.get("collection_no", ""),
                "variant_no": row.get("variant_no", ""),
                "metal": selected_metal or "",
                "stone_type": selected_stone_type or "",
                "stone_shape": selected_shape or "",
                "stone_carat": selected_carat or "",
                "color": selected_color or "",
                "clarity": selected_clarity or "",
                "cut": selected_cut or "",

                "product_title": desc_data.get("description_full", ""),
                "metal_price": pdp_price_data.get("pdp_current_price", ""),
                "stone_price": "",  # not parsed separately
                "updated_date": datetime.now().strftime("%Y-%m-%d"),

                "setting_title": ring_diamond_data.get("ring_diamond_details_text", ""),
                "setting_price": "",
                "diamond_title": "",

                "product_description": desc_data.get("description_full", ""),
                "additional_attributes": json.dumps(ring_diamond_data),

                "metal_price_e": cart_price_data.get("cart_item_price", ""),
                "stone_price_e": "",
                "final_price_e": cart_price_data.get("summary_total", ""),
                "updated_date_t": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "metal_t": cart_price_data.get("metal_purity_cart", ""),
                "stone_type_t": cart_price_data.get("stone_type_cart", ""),
                "stone_shape_t": cart_price_data.get("stone_shape_cart", ""),
                "clarity_t": cart_price_data.get("stone_clarity_cart", ""),
                "cut_t": cart_price_data.get("stone_cut_cart", ""),

                "promotion_price": cart_price_data.get("cart_prices_found", ""),
                "rrp_price": pdp_price_data.get("pdp_strike_price", ""),
                "you_save": pdp_price_data.get("pdp_offer_text", ""),
                "final_price": cart_price_data.get("sticky_total", cart_price_data.get("summary_total", "")),

                "product_url1": url
            }
            # =============================================================

            # Persist this attempt
            append_result_row(row_out)

            if status == "success":
                return row_out  # success

            # else retry
            if UNLIMITED_RETRY:
                print(f"🔁 [{self.thread_name}] Retrying URL until success…")
                backoff_sleep(attempt)
                continue
            else:
                if attempt >= MAX_ATTEMPTS_PER_URL:
                    print(f"⛔ [{self.thread_name}] Max attempts reached, giving up this URL.")
                    return row_out
                backoff_sleep(attempt)


    def close(self):
        try:
            self.driver.quit()
        except Exception:
            pass

# ---------------------- Thread wrapper ----------------------
def threaded_worker(task):
    """task: (idx, row_dict)"""
    idx, row = task
    thread_name = threading.current_thread().name
    scraper = Scraper(thread_name=thread_name)
    try:
        return scraper.process_product(idx, row)
    finally:
        scraper.close()

# ============================ MAIN ============================
def main():
    # Load input
    df = pd.read_csv(INPUT_CSV)
    # Ensure column exists
    if "product_url" not in df.columns:
        raise ValueError("INPUT_CSV must contain a 'product_url' column.")

    # Resume: skip URLs already success
    done_urls = load_resume_set(OUTPUT_CSV)

    # Build tasks list (skip already successful)
    tasks = [(idx, row) for idx, row in df.iterrows() if str(row["product_url"]).strip() not in done_urls]
    total = len(tasks)
    print(f"🚀 Starting with {total} pending URLs (of {len(df)} total). Threads: {MAX_WORKERS}")

    if total == 0:
        print("✅ Nothing to do. All URLs already scraped successfully.")
        return

    # Thread pool of 2 workers (polite)
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="T") as executor:
        future_to_idx = {executor.submit(threaded_worker, t): t[0] for t in tasks}
        completed = 0
        for future in concurrent.futures.as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                _ = future.result()  # already appended row inside
                completed += 1
                print(f"📊 Progress: {completed}/{total} finished")
            except KeyboardInterrupt:
                print("🛑 Interrupted. Exiting…")
                break
            except Exception as e:
                print(f"❌ Worker error on index {idx}: {e}")

    print(f"\n📂 Progress saved to {OUTPUT_CSV}")
    print(f"📸 Screenshots in {SCREENSHOTS_DIR}")
    print("🏁 Done.")

if __name__ == "__main__":
    main()
