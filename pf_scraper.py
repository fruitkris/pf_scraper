import urllib.request
try:
    urllib.request.urlopen('https://api.brightdata.com', timeout=5)
    print("✅ Сеть работает", flush=True)
except Exception as e:
    print(f"❌ Сеть не работает: {e}", flush=True)


import asyncio
import aiohttp
import re
import os
from bs4 import BeautifulSoup

BD_API_KEY = os.environ.get("BD_API_KEY", "2577d2d3-25f9-46f6-9d4d-98a56b172178")
ZONE = "scraping_browser"
SEARCH_URL = os.environ.get("SEARCH_URL", "https://www.propertyfinder.ae/en/search?l=634&c=1&fu=0&ob=mr")

async def fetch(session, url):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BD_API_KEY}"
    }
    payload = {
    "zone": "scraping_browser",
    "url": url,
    "format": "raw"
}
    async with session.post(
        "https://api.brightdata.com/request",
        headers=headers,
        json=payload,
        timeout=aiohttp.ClientTimeout(total=120)
    ) as resp:
        print(f"Status: {resp.status}", flush=True)
        return await resp.text()

async def scrape():
    async with aiohttp.ClientSession() as session:
        url = SEARCH_URL + "&page=1"
        print(f"📄 Запрос: {url}", flush=True)
        html = await fetch(session, url)
        print(f"HTML длина: {len(html)}", flush=True)
        print(f"Фрагмент: {html[:500]}", flush=True)

        soup = BeautifulSoup(html, "html.parser")
        links = list(dict.fromkeys([
            "https://www.propertyfinder.ae" + a["href"]
            for a in soup.select('a[href*="/en/plp/"]')
            if a.get("href")
        ]))
        print(f"Найдено ссылок: {len(links)}", flush=True)

        if not links:
            print("❌ Ссылок не найдено", flush=True)
            return

        link = links[0]
        print(f"🔗 {link}", flush=True)
        html = await fetch(session, link)
        soup = BeautifulSoup(html, "html.parser")
        title = soup.find("h1").get_text(strip=True) if soup.find("h1") else ""
        price = ""
        for el in soup.find_all(string=re.compile(r"AED")):
            price = el.strip()
            break
        text = soup.get_text()
        ref_match = re.search(r'Reference\s*[\n\r]*\s*(\d{8,})', text)
        reference = ref_match.group(1) if ref_match else ""
        permit_match = re.search(r'DLD Permit Number\s*[\n\r]*\s*(\d{7,})', text)
        permit = permit_match.group(1) if permit_match else ""

        print(f"\n✅ РЕЗУЛЬТАТ:", flush=True)
        print(f"🏠 {title}", flush=True)
        print(f"💰 {price}", flush=True)
        print(f"📋 Ref: {reference}", flush=True)
        print(f"🔑 Permit: {permit}", flush=True)
        print(f"🔗 {link}", flush=True)

if __name__ == "__main__":
    print("🚀 Тест — 1 листинг", flush=True)
    asyncio.run(scrape())
