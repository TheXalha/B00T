from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
import os
import time

driver = None

def start_browser():
    global driver
    options = Options()
    options.add_argument("--start-maximized")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://futures.mexc.com/en-US/login")
    print("Selenium (Browser) başlatıldı, lütfen hesabınıza manuel giriş yapın.")

def stop_browser():
    global driver
    if driver:
        try:
            driver.quit()
            driver = None
            print("Browser kapatıldı.")
        except Exception as e:
            print(f"Browser kapatılırken hata: {e}")

def browser_handle_pair(pair):
    load_dotenv()
    global driver
    if not driver:
        print("Browser başlatılmamış!")
        return
        
    driver.get("https://www.mexc.com/futures/" + pair)
    time.sleep(10)
    try:
        element = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/section/div[3]/div[7]/section/div[1]/div[1]/span[1]')))
        element.click()

    except Exception as e:
        print(f"Tıklama hatası: {e}")
    time.sleep(5)
    try:
        element = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/section/div[3]/div[7]/section/div[2]/div[2]/div[1]/div/div/div[4]/div[1]/div/div[2]/div/div/input')))
        element.send_keys(Keys.BACKSPACE)
        element.send_keys(Keys.BACKSPACE)
        element.send_keys(os.getenv("ORDER_AMOUNT"))
    except Exception as e:
        print(f"Tıklama hatası: {e}")    

    time.sleep(5)

    try:
        element = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/section/div[3]/div[7]/section/div[2]/div[2]/div[1]/div/div/div[4]/div[4]/div[4]/div/div/label[2]/span[1]')))
                                                
        element.click()

    except Exception as e:
        print(f"Tıklama hatası: {e}")
    time.sleep(5)
    
    #js_code = """document.evaluate("/html/body/div[14]/div/div/ul/li[2]/span", document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click();"""

    #driver.execute_script(js_code)

    #time.sleep(5)


    try:
        element = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/section/div[3]/div[7]/section/div[2]/div[2]/div[1]/div/div/div[4]/div[4]/div[4]/section/div[2]/div/div/div[1]/div/div/div/input')))
        element.send_keys(os.getenv("TAKE_PROFIT"))
    except Exception as e:
        print(f"Tıklama hatası: {e}")   

    time.sleep(5)    

    try:
        element = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/section/div[3]/div[7]/section/div[2]/div[2]/div[1]/div/div/div[4]/div[4]/section/div/div[1]/button[2]/div/div')))
        element.click()

    except Exception as e:
        print(f"Tıklama hatası: {e}")