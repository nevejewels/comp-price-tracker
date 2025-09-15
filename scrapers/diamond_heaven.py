import time
import pandas as pd
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DiamondHeavenScraper:
    def __init__(self, gecko_path, input_csv_path):
        self.gecko_path = gecko_path
        self.input_csv_path = input_csv_path
        self.driver = None
        self.wait = None
    
    def setup_driver(self):
        """Initialize the Firefox driver with options"""
        try:
            options = Options()
            options.add_argument("--start-maximized")
            # Add additional options for stability
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.set_preference("dom.webdriver.enabled", False)
            options.set_preference('useAutomationExtension', False)
            
            self.driver = webdriver.Firefox(
                service=FirefoxService(self.gecko_path), 
                options=options
            )
            self.wait = WebDriverWait(self.driver, 15)
            logger.info("Firefox driver initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize driver: {e}")
            return False
    
    def load_page(self, url="https://www.diamond-heaven.co.uk/build-your-ring/by-stone/diamond"):
        """Load the target page"""
        try:
            self.driver.get(url)
            # Wait for page to load completely
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)  # Additional buffer for dynamic content
            logger.info("Page loaded successfully")
            return True
        except TimeoutException:
            logger.error("Page load timeout")
            return False
        except Exception as e:
            logger.error(f"Error loading page: {e}")
            return False
    
    def scroll_into_view(self, element):
        """Scroll element into view smoothly"""
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", 
                element
            )
            time.sleep(1)
        except Exception as e:
            logger.warning(f"Scroll failed: {e}")
    
    def click_label_by_for_attr(self, for_attr, description=""):
        """Click label by for attribute with error handling and scrolling"""
        try:
            # First try to find the element
            label = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"label[for='{for_attr}']"))
            )
            
            # Scroll the element into view with more buffer
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", 
                label
            )
            time.sleep(2)  # Wait for scroll to complete
            
            # Wait for it to be clickable after scrolling
            clickable_label = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, f"label[for='{for_attr}']"))
            )
            
            # Try clicking with JavaScript if regular click fails
            try:
                clickable_label.click()
            except Exception:
                logger.warning(f"Regular click failed for {for_attr}, trying JavaScript click")
                self.driver.execute_script("arguments[0].click();", clickable_label)
            
            time.sleep(1)
            logger.info(f"Clicked {description}: {for_attr}")
            return True
            
        except TimeoutException:
            logger.error(f"Timeout waiting for element: {for_attr}")
            return False
        except Exception as e:
            logger.error(f"Error clicking {for_attr}: {e}")
            return False
    
    def get_correct_value_orders(self):
        """Get the correct value orders based on your reference pattern"""
        return {
            'carat': [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.5, 2.0, 2.5, 3.0],
            'color': ['D', 'E', 'F', 'G', 'H', 'I', 'J', 'K'],
            'clarity': ['FL', 'IF', 'VVS1', 'VVS2', 'VS1', 'VS2', 'SI1', 'SI2'],
            'cut': ['GOOD', 'VERY GOOD', 'EXCELLENT']  # Matching your reference exactly
        }
    
    def normalize_carat_value(self, value):
        """Normalize carat value to float"""
        try:
            # Convert to float and handle common formatting issues
            if isinstance(value, str):
                value = value.strip()
                # Handle cases like "0.50", "1.00", etc.
                return float(value)
            return float(value)
        except:
            logger.error(f"Could not normalize carat value: {value}")
            return None
    
    def set_slider_reference_style(self, slider_index, value, slider_type):
        """Set slider using the exact reference pattern from your previous script"""
        try:
            # Get value orders - matching your reference exactly
            value_orders = {
                'carat': [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.5, 2.0, 2.5, 3.0],
                'color': ['D', 'E', 'F', 'G', 'H', 'I', 'J', 'K'],
                'clarity': ['FL', 'IF', 'VVS1', 'VVS2', 'VS1', 'VS2', 'SI1', 'SI2'],
                'cut': ['GOOD', 'VERY GOOD', 'EXCELLENT']  # Matching your reference order
            }
            
            order = value_orders.get(slider_type, [])
            if not order:
                logger.error(f"❌ No order defined for {slider_type}")
                return False
            
            # Normalize value based on type
            if slider_type == 'carat':
                normalized_value = self.normalize_carat_value(value)
                if normalized_value is None or normalized_value not in order:
                    logger.error(f"❌ Invalid carat value '{value}'")
                    return False
                target_index = order.index(normalized_value)
            else:
                value_str = str(value).strip().upper()
                if value_str not in order:
                    logger.error(f"❌ Invalid {slider_type} value '{value_str}'")
                    return False
                target_index = order.index(value_str)
            
            total_values = len(order)
            
            # Find the slider group
            slider_groups = self.driver.find_elements(By.CSS_SELECTOR, ".ui-slider")
            if slider_index >= len(slider_groups):
                logger.error(f"❌ Slider index {slider_index} not found")
                return False
            
            target_slider = slider_groups[slider_index]
            self.scroll_into_view(target_slider)
            
            # Find the handles (dots) - following your reference pattern
            handles = target_slider.find_elements(By.CSS_SELECTOR, ".ui-slider-handle")
            if len(handles) != 2:
                logger.error(f"❌ Expected 2 slider handles, found: {len(handles)}")
                return False
            
            # Get slider dimensions - following your reference
            slider_width = target_slider.size['width']
            step_width = slider_width / (total_values - 1)
            
            left_handle = handles[0]
            right_handle = handles[1]
            
            # Use ActionChains exactly like your reference
            actions = ActionChains(self.driver)
            
            # Move left handle to target position (following your reference pattern)
            actions.click_and_hold(left_handle).move_by_offset(int(step_width * target_index), 0).release().perform()
            time.sleep(0.5)
            
            # Move right handle to target position (following your reference pattern)
            actions.click_and_hold(right_handle).move_by_offset(-int(step_width * (total_values - 1 - target_index)), 0).release().perform()
            time.sleep(0.5)
            
            logger.info(f"✅ {slider_type.title()} '{value}' selected using reference method.")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error selecting {slider_type} '{value}' with reference method: {e}")
            return False
    
    def extract_percentage_from_style(self, style_attr):
        """Extract percentage value from style attribute like 'left: 28.5714%;'"""
        try:
            import re
            if not style_attr:
                return 0.0
            match = re.search(r'left:\s*([0-9.]+)%', style_attr)
            if match:
                return float(match.group(1))
            return 0.0
        except:
            return 0.0
        """Verify that the slider was set to the expected value"""
        try:
            slider_groups = self.driver.find_elements(By.CSS_SELECTOR, ".ui-slider")
            if slider_index >= len(slider_groups):
                return False
            
            target_slider = slider_groups[slider_index]
            handles = target_slider.find_elements(By.CSS_SELECTOR, ".ui-slider-handle")
            
            if len(handles) >= 2:
                # Check if both handles are at approximately the same position
                left_style = handles[0].get_attribute('style')
                right_style = handles[1].get_attribute('style')
                
                left_pos = self.extract_percentage_from_style(left_style)
                right_pos = self.extract_percentage_from_style(right_style)
                
                # For single value selection, handles should be close together
                position_diff = abs(left_pos - right_pos)
                
                logger.info(f"Slider {slider_type} positions - Left: {left_pos}%, Right: {right_pos}%, Diff: {position_diff}%")
                
                # Consider it successful if handles are within 5% of each other
                return position_diff <= 5.0
            
            return False
            
        except Exception as e:
            logger.warning(f"Could not verify slider value: {e}")
            return False
    
    def extract_percentage_from_style(self, style_attr):
        """Extract percentage value from style attribute like 'left: 28.5714%;'"""
        try:
            import re
            if not style_attr:
                return 0.0
            match = re.search(r'left:\s*([0-9.]+)%', style_attr)
            if match:
                return float(match.group(1))
            return 0.0
        except:
            return 0.0
    
    def set_slider_with_verification(self, slider_index, value, slider_type, max_attempts=3):
        """Set slider with verification and retry logic using reference method"""
        for attempt in range(max_attempts):
            logger.info(f"Setting {slider_type} slider to {value} (attempt {attempt + 1}/{max_attempts})")
            
            if self.set_slider_reference_style(slider_index, value, slider_type):
                # Verify the setting
                time.sleep(1)  # Allow time for UI to update
                
                if self.verify_slider_value(slider_index, value, slider_type):
                    logger.info(f"✅ {slider_type} slider successfully set and verified")
                    return True
                else:
                    logger.warning(f"⚠️ {slider_type} slider set but verification failed")
                    # Continue to retry
            
            if attempt < max_attempts - 1:
                logger.info(f"Retrying {slider_type} slider...")
                time.sleep(2)
        
        logger.error(f"❌ Failed to set {slider_type} slider after {max_attempts} attempts")
        return False
    
    def process_row(self, row, row_index):
        """Process a single row from the CSV"""
        logger.info(f"Processing row {row_index + 1}...")
        
        try:
            # Stone type selection
            stone_type = row['stone_type'].strip().lower()
            if stone_type == 'natural':
                success = self.click_label_by_for_attr("naturalDiamond", "Natural Diamond")
            else:
                success = self.click_label_by_for_attr("labgrownDiamond", "Lab Grown Diamond")
            
            if not success:
                return False
            
            time.sleep(2)
            
            # Shape selection (assuming round)
            if not self.click_label_by_for_attr("naturalshapeRound", "Round Shape"):
                return False
            
            time.sleep(2)
            
            # Set sliders with improved method and verification
            slider_settings = [
                (0, row['stone_carat'], 'carat'),
                (1, row['color'], 'color'),
                (2, row['clarity'], 'clarity'),
                (3, row['cut'], 'cut')
            ]
            
            for slider_index, value, slider_type in slider_settings:
                if not self.set_slider_with_verification(slider_index, value, slider_type):
                    logger.error(f"Failed to set {slider_type} slider for value {value}")
                    return False
                time.sleep(1)  # Small delay between sliders
            
            logger.info(f"✅ Row {row_index + 1} processed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing row {row_index + 1}: {e}")
            return False
    
    def run(self, process_all_rows=False):
        """Main execution method"""
        try:
            # Read input CSV
            try:
                df = pd.read_csv(self.input_csv_path)
                logger.info(f"Loaded CSV with {len(df)} rows")
            except Exception as e:
                logger.error(f"Error reading CSV: {e}")
                return
            
            # Setup driver
            if not self.setup_driver():
                return
            
            # Load page
            if not self.load_page():
                return
            
            # Process rows
            successful_rows = 0
            total_rows = len(df) if process_all_rows else 1
            
            for index, row in df.iterrows():
                logger.info(f"\n{'='*50}")
                logger.info(f"Processing row {index + 1}: Carat={row['stone_carat']}, Color={row['color']}, Clarity={row['clarity']}, Cut={row['cut']}")
                logger.info(f"{'='*50}")
                
                if self.process_row(row, index):
                    successful_rows += 1
                else:
                    logger.error(f"❌ Failed to process row {index + 1}")
                
                # Break after first row unless processing all
                if not process_all_rows:
                    break
                
                # Add delay between rows
                if index < len(df) - 1:
                    time.sleep(5)
            
            logger.info(f"\n🎯 Processing complete: {successful_rows}/{total_rows} rows successful")
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                time.sleep(5)  # Final wait
                self.driver.quit()
                logger.info("Driver closed successfully")
            except Exception as e:
                logger.error(f"Error closing driver: {e}")

# Usage
if __name__ == "__main__":
    # Configuration
    GECKO_PATH = r"C:\Users\komal.kumavat\Diamond-data\data\geckodriver.exe"
    INPUT_CSV = r"C:\Users\komal.kumavat\Downloads\Diamond_heaven-input_file.csv"
    
    # Create and run scraper
    scraper = DiamondHeavenScraper(GECKO_PATH, INPUT_CSV)
    
    # Set to True to process all rows, False to process only first row
    scraper.run(process_all_rows=False)