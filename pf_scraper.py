import asyncio
import re
import os
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

USERNAME = "brd-customer-hl_2311d537-zone-scraping_browser"
PASSWORD = "a2tnpm1d8j9u"
WS_URL = f"wss://{USERNAME}:{PASSWORD}@brd.superproxy.io:9222"
SEARCH_URL = os.environ.get("SEARCH_URL", "https://www.propertyfinder.ae/en/search?l=634&c=1&fu=0&ob=mr")

async def scrape():
    async with async_playwright() as pw:
        print("🔌 Подключаемся к Bright Data браузеру...", flush=True)
        browser = await pw.chromium.connect_over_cdp(WS_URL)
        page = await browser.new_page()

        url = SEARCH_URL + "&page=1"
        print(f"📄 Открываем: {url}", flush=True)
        await page.goto(url, timeout=60000)
        await page.wait_for_load_state("networkidle")

        html = await page.content()
        print(f"HTML длина: {len(html)}", flush=True)

        soup = BeautifulSoup(html, "html.parser")
        links = list(dict.fromkeys([
            "https://www.propertyfinder.ae" + a["href"]
            for a in soup.select('a[href*="/en/plp/"]')
            if a.get("href")
        ]))
        print(f"Найдено ссылок: {len(links)}", flush=True)

        if not links:
            print("❌ Ссылки не найдены", flush=True)
            await browser.close()
            return

        # Только первый листинг
        link = links[0]
        print(f"🔗 {link}", flush=True)
        await page.goto(link, timeout=60000)
        await page.wait_for_load_state("networkidle")

        html = await page.content()
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

        await browser.close()

if __name__ == "__main__":
    print("🚀 Тест — 1 листинг через Bright Data Browser", flush=True)
    asyncio.run(scrape())
