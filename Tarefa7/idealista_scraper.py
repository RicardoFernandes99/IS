import random
import time
import pandas as pd
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

IDEALISTA_BASE_URL = "https://www.idealista.pt/comprar-casas/viana-do-castelo-distrito/"
MAX_PAGES = 5  # Maximum number of pages to scrape

def get_page_url(page_number):
    """Generate URL for specific page"""
    if page_number == 1:
        return IDEALISTA_BASE_URL
    else:
        return f"{IDEALISTA_BASE_URL}pagina-{page_number}"

def get_houses(max_pages=MAX_PAGES):
    # Configure undetected-chromedriver (more effective at bypassing detection)
    options = uc.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("window-size=1920,1080")
    
    # Using undetected_chromedriver with version matching parameter
    # This tells undetected_chromedriver to use your current Chrome version
    driver = uc.Chrome(options=options, version_main=140)  # Specify your Chrome version 140
    
    all_houses = []
    cookies_accepted = False
    
    try:
        for page in range(1, max_pages + 1):
            current_url = get_page_url(page)
            print(f"🌐 Navigating to page {page}/{max_pages}: {current_url}")
            
            # Open in a real browser window
            driver.get(current_url)
            
            # Wait like a human would
            time.sleep(random.uniform(5, 8))
            
            # Handle cookie consent popup if it appears (only on the first page)
            if not cookies_accepted:
                try:
                    cookie_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
                    )
                    print("🍪 Found cookie consent popup, accepting...")
                    cookie_button.click()
                    time.sleep(random.uniform(2, 3))
                    cookies_accepted = True
                except Exception:
                    print("🍪 No cookie consent popup found or already accepted")
                    cookies_accepted = True
            
            # Scroll down gradually like a human
            total_height = driver.execute_script("return document.body.scrollHeight")
            viewport_height = driver.execute_script("return window.innerHeight")
            scroll_points = range(0, total_height, viewport_height//2)
            
            for point in scroll_points:
                driver.execute_script(f"window.scrollTo(0, {point});")
                time.sleep(random.uniform(1, 2))  # Random delay between scrolls
            
            # Scroll back up a bit (like a human would)
            driver.execute_script(f"window.scrollTo(0, {total_height//2});")
            time.sleep(random.uniform(1, 2))
            
            # Check for captcha
            if check_for_captcha(driver):
                print("⚠️ CAPTCHA detected! Please solve it manually...")
                # Give user time to solve the captcha manually
                print("You have 60 seconds to solve the CAPTCHA...")
                time.sleep(60)
            
            # Wait until articles appear
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
                )
            except Exception as e:
                print(f"⚠️ Error waiting for articles: {e}")
                continue  # Skip this page if no articles found
            
            # Extract HTML after everything has loaded
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            # Check if we're on a "no results" page or if we've reached the last page
            if "Não foram encontrados resultados" in soup.text or "No se han encontrado resultados" in soup.text:
                print(f"🔍 No more results found on page {page}. Stopping.")
                break
            
            # Extract houses from this page
            houses_on_page = []
            for listing in soup.find_all("article"):
                title_tag = listing.find("a", class_="item-link")
                price_tag = listing.find("span", class_="item-price")
                location_tag = listing.find("span", class_="item-location")
                
                # Try to find size and rooms
                details = listing.find("span", class_="item-detail")
                details_text = details.get_text(strip=True) if details else ""
                
                # Try to get image URL
                img_tag = listing.find("img")
                img_url = img_tag.get('src', '') if img_tag else ''
                
                if title_tag and price_tag:
                    houses_on_page.append({
                        "Title": title_tag.get_text(strip=True),
                        "Price": price_tag.get_text(strip=True),
                        "Location": location_tag.get_text(strip=True) if location_tag else "",
                        "Details": details_text,
                        "ImageURL": img_url,
                        "Page": page  # Track which page this listing came from
                    })
            
            print(f"✓ Found {len(houses_on_page)} listings on page {page}")
            all_houses.extend(houses_on_page)
            
            # Wait between pages to avoid triggering anti-scraping measures
            if page < max_pages:
                wait_time = random.uniform(15, 25)  # Longer wait between pages
                print(f"⏱️ Waiting {wait_time:.1f} seconds before going to the next page...")
                time.sleep(wait_time)
        return all_houses
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []
    
    finally:
        # Always close the browser
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
    
    # Check for specific elements that might indicate a captcha
    try:
        captcha_elements = driver.find_elements(By.XPATH, 
            "//*[contains(text(), 'captcha') or contains(@id, 'captcha') or contains(@class, 'captcha')]")
        if captcha_elements:
            return True
    except:
        pass
        
    return False

def main():
    print("🔍 Starting to scrape Idealista (up to 5 pages)...")
    max_attempts = 3
    attempt = 1
    
    while attempt <= max_attempts:
        print(f"Attempt {attempt} of {max_attempts}")
        houses = get_houses(max_pages=MAX_PAGES)
        
        if houses:
            df = pd.DataFrame(houses)
            
            # Group by page to show statistics
            pages_stats = df.groupby('Page').size().to_dict()
            print("\n📊 Listings per page:")
            for page, count in pages_stats.items():
                print(f"  • Page {page}: {count} listings")
                
            print("\n🏡 First few listings:")
            print(df[['Title', 'Price', 'Location']].head())
            
            print(f"\n✅ Total houses found: {len(df)} from {len(pages_stats)} pages")
            
            # Save with timestamp to avoid overwriting
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"idealista_houses_{timestamp}.csv"
            df.to_csv(filename, index=False, encoding="utf-8-sig")
            print(f"💾 Dados guardados em {filename}")
            break
        else:
            print(f"⚠️ Attempt {attempt}: Nenhum resultado encontrado")
            if attempt < max_attempts:
                wait_time = random.uniform(30, 60)
                print(f"Waiting {wait_time:.1f} seconds before trying again...")
                time.sleep(wait_time)
            attempt += 1
    
    if attempt > max_attempts:
        print("❌ All attempts failed. O Idealista pode ter bloqueado temporariamente o acesso.")


if __name__ == "__main__":
    main()