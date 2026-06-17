import asyncio
import aiohttp
import re
import csv
import os
from bs4 import BeautifulSoup

SCRAPER_API_KEY = "349dca9f82b8f518fb41e0209841f426"
SEARCH_URL = os.environ.get("SEARCH_URL", "https://www.propertyfinder.ae/en/search?l=634&c=1&fu=0&ob=mr")

def scraper_url(target_url):
    return f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&render=true&country_code=ae"

async def fetch(session, url):
    async with session.get(scraper_url(url), timeout=aiohttp.ClientTimeout(total=60)) as resp:
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
print(f"Фрагмент: {html[200:600]}", flush=True)

soup = BeautifulSoup(html, "html.parser")

# Пробуем разные селекторы
links_plp = soup.select('a[href*="/en/plp/"]')
links_buy = soup.select('a[href*="/buy/"]')
print(f"Ссылки /plp/: {len(links_plp)}", flush=True)
print(f"Ссылки /buy/: {len(links_buy)}", flush=True)

links = list(dict.fromkeys([
    "https://www.propertyfinder.ae" + a["href"]
    for a in links_plp
    if a.get("href")
]))


            if not links:
                print("✅ Страницы закончились.", flush=True)
                break

            print(f"   Найдено {len(links)} листингов", flush=True)

            for i, link in enumerate(links):
                print(f"  [{i+1}/{len(links)}] {link}", flush=True)
                try:
                    html = await fetch(session, link)
                    soup = BeautifulSoup(html, "html.parser")

                    # Заголовок
                    title = ""
                    h1 = soup.find("h1")
                    if h1:
                        title = h1.get_text(strip=True)

                    # Цена
                    price = ""
                    for el in soup.find_all(string=re.compile(r"AED")):
                        price = el.strip()
                        break

                    # Reference и DLD Permit — ищем в тексте страницы
                    text = soup.get_text()

                    reference = ""
                    ref_match = re.search(r'Reference\s*[\n\r]*\s*(\d{8,})', text)
                    if ref_match:
                        reference = ref_match.group(1)

                    permit = ""
                    permit_match = re.search(r'DLD Permit Number\s*[\n\r]*\s*(\d{7,})', text)
                    if permit_match:
                        permit = permit_match.group(1)

                    results.append({
                        "url": link,
                        "title": title,
                        "price": price,
                        "reference": reference,
                        "permit": permit,
                    })

                    print(f"     ✓ {title[:40]} | {price} | Ref: {reference} | Permit: {permit}", flush=True)

                except Exception as e:
                    print(f"     ✗ Ошибка: {e}", flush=True)
                    results.append({"url": link, "error": str(e)})

                await asyncio.sleep(1)

            page_num += 1
            await asyncio.sleep(2)

    # Итог в логи
    print("\n========== РЕЗУЛЬТАТЫ ==========", flush=True)
    for r in results:
        print(f"🏠 {r.get('title','')[:40]}", flush=True)
        print(f"   💰 {r.get('price','')}", flush=True)
        print(f"   📋 Ref: {r.get('reference','')}", flush=True)
        print(f"   🔑 Permit: {r.get('permit','')}", flush=True)
        print(f"   🔗 {r.get('url','')}", flush=True)
        print(flush=True)

    print(f"✅ Всего: {len(results)} листингов", flush=True)
    return results

if __name__ == "__main__":
    print(f"🚀 Запуск. URL: {SEARCH_URL}", flush=True)
    asyncio.run(scrape_listings(SEARCH_URL))
