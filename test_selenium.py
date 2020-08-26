from selenium import webdriver
import os

option = webdriver.ChromeOptions()
option.binary_location = os.getenv('GOOGLE_CHROME_BIN')
option.add_argument("--headless")
option.add_argument('--disable-gpu')
option.add_argument('--no-sandbox')

driver = webdriver.Chrome(executable_path=os.getenv('CHROME_EXECUTABLE_PATH'), options=option)
driver.get('https://emploisfp-psjobs.cfp-psc.gc.ca/psrs-srfp/applicant/page2440?fromMenu=true&toggleLanguage=en')
print(driver.page_source)
