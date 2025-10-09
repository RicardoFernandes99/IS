import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from io import StringIO

IDEALISTA_URL = "https://www.idealista.pt/comprar-casas/viana-do-castelo-distrito/"

session = requests.Session()
session.headers.update({
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "accept-language": "en-US;en;q=0.9",
    "accept-encoding": "gzip, deflate, br",
    })

DELAY = 1  

def get_houses():
    resp = session.get(IDEALISTA_URL)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    houses = []
    for listing in soup.find_all("article", class_="item"):
        title = listing.find("a", class_="item-link").get_text(strip=True)
        price = listing.find("span", class_="item-price").get_text(strip=True)
        location = listing.find("span", class_="item-location").get_text(strip=True)
        houses.append({"Title": title, "Price": price, "Location": location})
    return houses

def main():
    houses = get_houses()
    df = pd.DataFrame(houses)
    for house in houses:
        print(house)
    print(f"Total houses found: {len(houses)}")    
    print(df)

if __name__ == "__main__":
    main()