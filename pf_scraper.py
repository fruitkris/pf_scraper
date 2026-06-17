import asyncio
import aiohttp
import re
import os
from bs4 import BeautifulSoup

BD_API_KEY = "2577d2d3-25f9-46f6-9d4d-98a56b172178"
SEARCH_URL = os.environ.get("SEARCH_URL", "https://www.propertyfinder.ae/en/search?l=634&c=1&fu=0&ob=mr")

async def fetch(session, url):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BD_API_KEY}"
    }
    payload = {
        "zone": "unblocker",
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

async def scrape_listings(search_url):
    async with aiohttp.ClientSession() as session:
        # Только первая страница
        url = search_url + "&page=1"
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
            print("❌ Ссылки не найдены", flush=True)
            return

        # Только первый листинг
        link = links[0]
        print(f"🔗 Первый листинг: {link}", flush=True)
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
    print(f"🚀 Тест — 1 листинг", flush=True)
    asyncio.run(scrape_listings(SEARCH_URL))
