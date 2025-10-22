import random
import time
import pandas as pd
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re

IDEALISTA_BASE_URL = "https://www.idealista.pt/comprar-casas/viana-do-castelo-distrito/"
MAX_PAGES = 5  

def get_page_url(page_number):
    if page_number == 1:
        return IDEALISTA_BASE_URL
    else:
        return f"{IDEALISTA_BASE_URL}pagina-{page_number}"

def get_houses(max_pages=MAX_PAGES):

    options = uc.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("window-size=1920,1080")
    
    driver = uc.Chrome(options=options, version_main=140)  
    
    all_houses = []
    cookies_accepted = False
    
    try:
        for page in range(1, max_pages + 1):
            current_url = get_page_url(page)
            
            driver.get(current_url)
            
            time.sleep(random.uniform(5, 8))
            
            if not cookies_accepted:
                try:
                    cookie_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
                    )
                    print(" Found cookie consent popup, accepting...")
                    cookie_button.click()
                    time.sleep(random.uniform(2, 3))
                    cookies_accepted = True
                except Exception:
                    print(" No cookie consent popup found or already accepted")
                    cookies_accepted = True
            
            total_height = driver.execute_script("return document.body.scrollHeight")
            viewport_height = driver.execute_script("return window.innerHeight")
            scroll_points = range(0, total_height, viewport_height//2)
            
            for point in scroll_points:
                driver.execute_script(f"window.scrollTo(0, {point});")
                time.sleep(random.uniform(1, 2))  
            
            driver.execute_script(f"window.scrollTo(0, {total_height//2});")
            time.sleep(random.uniform(1, 2))
            
            if check_for_captcha(driver):
                time.sleep(5)
            
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
                )
            except Exception as e:
                print(f" Error waiting for articles: {e}")
                continue  
            
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            if "Não foram encontrados resultados" in soup.text:
                print(f" No results")
                break
            
            houses_on_page = []
            for listing in soup.find_all("article"):
                title_tag = listing.find("a", class_="item-link")
                price_tag = listing.find("span", class_="item-price")
                
                detail_elements = listing.find_all("span", class_="item-detail")
                details_text = ""
                area_text = ""

                if detail_elements and len(detail_elements) > 0:
                    details_text = detail_elements[0].get_text(strip=True) if detail_elements[0] else ""
                    
                if detail_elements and len(detail_elements) > 1:
                    area_text = detail_elements[1].get_text(strip=True) if detail_elements[1] else ""

                area_text = re.search(r'(\d+)', area_text).group(1) if area_text and re.search(r'(\d+)', area_text) else ""
                print(f"Details: {details_text}, Area: {area_text}")
                
                img_tag = listing.find("img")
                img_url = img_tag.get('src', '') if img_tag else ''
                
                
                if title_tag and price_tag:

                    title_text = title_tag.get_text(strip=True)
                    
                    property_parts = title_text.split(',', 1)  
                    property_type = property_parts[0].strip()
                    location = property_parts[1].strip() if len(property_parts) > 1 else "No location"
                    
                    houses_on_page.append({
                        "Title": property_type,  
                        "Price": price_tag.get_text(strip=True),
                        "Location": location,  
                        "tX": details_text,
                        "Area m2": area_text,
                        "ImageURL": img_url,
                    })
            
            all_houses.extend(houses_on_page)
            
            if page < max_pages:
                wait_time = random.uniform(5, 15)  
                time.sleep(wait_time)
        return all_houses
        
    except Exception as e:
        print(f" Error: {e}")
        return []
    
    finally:
        driver.quit()


def check_for_captcha(driver):
    """Check if a captcha is present on the page"""
    captcha_indicators = [
        "captcha", "robot", "verification", "verify", "human",
        "Are you a robot?", "Please verify"
    ]
    
    page_source = driver.page_source.lower()
    for indicator in captcha_indicators:
        if indicator.lower() in page_source:
            return True
    
    try:
        captcha_elements = driver.find_elements(By.XPATH, 
            "//*[contains(text(), 'captcha') or contains(@id, 'captcha') or contains(@class, 'captcha')]")
        if captcha_elements:
            return True
    except:
        pass
        
    return False

def main():
    max_attempts = 3
    attempt = 1
    
    while attempt <= max_attempts:
        print(f"Attempt {attempt} of {max_attempts}")
        houses = get_houses(max_pages=MAX_PAGES)
        
        if houses:
            df = pd.DataFrame(houses)
            
                    
            filename = f"idealista_houses.csv"
            df.to_csv(filename, index=False, encoding="utf-8-sig")
            break
        else:
            if attempt < max_attempts:
                wait_time = random.uniform(30, 60)
                time.sleep(wait_time)
            attempt += 1
    

if __name__ == "__main__":
    main()