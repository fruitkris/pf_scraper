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
        return await resp.text()

async def scrape_listings(search_url):
    results = []
    async with aiohttp.ClientSession() as session:
        page_num = 1
        while True:
            url = search_url + f"&page={page_num}"
            print(f"\n📄 Страница {page_num}", flush=True)
            html = await fetch(session, url)
            print(f"HTML длина: {len(html)}", flush=True)
            print(f"Фрагмент: {html[:300]}", flush=True)
            soup = BeautifulSoup(html, "html.parser")
            links = list(dict.fromkeys([
                "https://www.propertyfinder.ae" + a["href"]
                for a in soup.select('a[href*="/en/plp/"]')
                if a.get("href")
            ]))
            if not links:
                print("✅ Листинги закончились.", flush=True)
                break
            print(f"Найдено {len(links)} листингов", flush=True)
            for i, link in enumerate(links):
                print(f"[{i+1}/{len(links)}] {link}", flush=True)
                try:
                    html = await fetch(session, link)
                    soup = BeautifulSoup(html, "html.parser")
                    title = soup.find("h1").get_text(strip=True) if soup.find("h1") else ""
                    price = ""
                    for el in soup.find_all(string=re.compile(r"AED")):
                        price = el.strip()
                        break
                    text = soup.get_text()
                    reference = ""
                    ref_match = re.search(r'Reference\s*[\n\r]*\s*(\d{8,})', text)
                    if ref_match:
                        reference = ref_match.group(1)
                    permit = ""
                    permit_match = re.search(r'DLD Permit Number\s*[\n\r]*\s*(\d{7,})', text)
                    if permit_match:
                        permit = permit_match.group(1)
                    results.append({"url": link, "title": title, "price": price, "reference": reference, "permit": permit})
                    print(f"✓ {title[:40]} | {price} | Ref: {reference} | Permit: {permit}", flush=True)
                except Exception as e:
                    print(f"✗ Ошибка: {e}", flush=True)
                await asyncio.sleep(1)
            page_num += 1
            await asyncio.sleep(2)
    print("\n========== РЕЗУЛЬТАТЫ ==========", flush=True)
    for r in results:
        print(f"🏠 {r.get('title','')[:40]} | 💰 {r.get('price','')} | 📋 {r.get('reference','')} | 🔑 {r.get('permit','')} | 🔗 {r.get('url','')}", flush=True)
    print(f"\n✅ Всего: {len(results)} листингов", flush=True)

if __name__ == "__main__":
    print(f"🚀 Запуск. URL: {SEARCH_URL}", flush=True)
    asyncio.run(scrape_listings(SEARCH_URL))
