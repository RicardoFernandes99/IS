import random
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

IDEALISTA_URL = "https://www.idealista.pt/comprar-casas/viana-do-castelo-distrito/"

def get_houses():
    # Configuração do Chrome
    options = Options()
    # options.add_argument("--headless=new")  # headless mais estável
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(IDEALISTA_URL)

    # Espera aleatória inicial (simula tempo humano)
    time.sleep(random.uniform(6, 10))

    # Faz scroll até ao fim da página — força o carregamento dos anúncios
    for _ in range(3):
        driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
        time.sleep(random.uniform(2, 4))

    # Espera até que os artigos estejam no DOM
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
        )
    except:
        print("⚠️ Nenhum artigo encontrado — possivelmente bloqueado ou tempo limite atingido.")

    # Extrai o HTML final
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    houses = []
    for listing in soup.find_all("article"):
        title_tag = listing.find("a", class_="item-link")
        price_tag = listing.find("span", class_="item-price")
        location_tag = listing.find("span", class_="item-location")

        if title_tag and price_tag and location_tag:
            houses.append({
                "Title": title_tag.get_text(strip=True),
                "Price": price_tag.get_text(strip=True),
                "Location": location_tag.get_text(strip=True)
            })
    return houses


def main():
    houses = get_houses()
    df = pd.DataFrame(houses)

    if not df.empty:
        print(df.head())
        print(f"\n✅ Total houses found: {len(df)}")
        df.to_csv("idealista_houses.csv", index=False, encoding="utf-8-sig")
        print("💾 Dados guardados em idealista_houses.csv")
    else:
        print("⚠️ Nenhum resultado encontrado — o Idealista pode ter bloqueado temporariamente o acesso.")

if __name__ == "__main__":
    main()
