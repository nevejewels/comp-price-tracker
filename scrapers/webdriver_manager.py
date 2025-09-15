from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

def get_firefox_driver(headless=False):
    options = Options()
    options.headless = headless  # Set True for silent mode (not recommended for debugging)

    # Path to Firefox (optional if already in PATH)
    options.binary_location = r"C:\Program Files\Mozilla Firefox\firefox.exe"

    # Create Firefox profile with preferences
    profile = webdriver.FirefoxProfile()
    profile.set_preference("permissions.default.image", 2)  # Block image loading
    profile.set_preference("dom.webdriver.enabled", False)
    profile.set_preference("useAutomationExtension", False)
    profile.set_preference("general.useragent.override", 
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

    options.profile = profile

    # Path to geckodriver
    service = Service(executable_path=r"C:\Users\komal.kumavat\Documents\77diamonds_data\geckodriver.exe")
    
    # Initialize driver
    driver = webdriver.Firefox(service=service, options=options)

    # Set maximum page load timeout (in seconds)
    driver.set_page_load_timeout(60)

    # Implicit wait for all elements
    driver.implicitly_wait(10)

    return driver
