from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

def get_firefox_driver(headless=False):
    options = Options()
    options.headless = headless  # Use True for headless mode

    # Block images directly using set_preference on options
    options.set_preference("permissions.default.image", 2)

    service = Service("/usr/local/bin/geckodriver")

    driver = webdriver.Firefox(service=service, options=options)
    driver.implicitly_wait(10)
    return driver

# def get_firefox_driver(headless=False):

#     options = Options()
#     options.headless = False  # Set to True for headless mode
#     options.binary_location = r"C:\Program Files\Mozilla Firefox\firefox.exe"

#     profile = webdriver.FirefoxProfile()
#     profile.set_preference("permissions.default.image", 2)  # Block all images
#     options.profile = profile
#     service = Service(r"C:\geckodriver\geckodriver.exe")

#     driver = webdriver.Firefox(service=service, options=options)

#     driver.implicitly_wait(10)
#     return driver