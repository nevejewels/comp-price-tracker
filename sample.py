from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
import time

# Optional: set Firefox to run headless
options = Options()
options.binary_location = r"C:\Program Files\Mozilla Firefox\firefox.exe"

# options.add_argument("--headless")  # Uncomment to run in background

# Path to geckodriver (make sure it's installed and in PATH or provide full path)
service = Service(r"C:\geckodriver\geckodriver.exe")

# Initialize Firefox driver
driver = webdriver.Firefox(service=service, options=options)

try:
    # Open a webpage
    driver.get("https://www.python.org")

    # Wait a bit for page load (not always needed but safe)
    time.sleep(2)

    # Get and print the title
    print("Page Title:", driver.title)

finally:
    # Close the browser
    driver.quit()
