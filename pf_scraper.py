import asyncio
from playwright.async_api import async_playwright
import csv
import re

async def scrape_listings(search_url: str):
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        page_num = 1

        while True:
            url = search_url + f"&page={page_num}"
            print(f"\n📄 Страница {page_num}: {url}")
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)

            # Собираем ссылки на листинги
            links = await page.eval_on_selector_all(
                'a[href*="/en/plp/"]',
                "els => [...new Set(els.map(el => el.href))]"
            )

            if not links:
                print("✅ Листинги закончились.")
                break

            print(f"   Найдено {len(links)} листингов")

            for i, link in enumerate(links):
                print(f"  [{i+1}/{len(links)}] {link}")
                try:
                    await page.goto(link, wait_until="networkidle", timeout=30000)
                    await asyncio.sleep(1.5)

                    # Заголовок
                    title = ""
                    try:
                        title = await page.locator("h1").first.inner_text(timeout=5000)
                    except:
                        pass

                    # Цена
                    price = ""
                    try:
                        price = await page.locator('[data-testid="price"]').first.inner_text(timeout=5000)
                    except:
                        try:
                            price = await page.locator('span:has-text("AED")').first.inner_text(timeout=3000)
                        except:
                            pass

                    # DLD Permit Number
                    permit = ""
                    try:
                        content = await page.content()
                        match = re.search(r'Permit[^0-9]*(\d{7,})', content)
                        if match:
                            permit = match.group(1)
                    except:
                        pass

                    # Reference number
                    reference = ""
                    try:
                        content = await page.content()
                        match = re.search(r'Reference[^0-9]*(\d{5,})', content)
                        if match:
                            reference = match.group(1)
                    except:
                        pass

                    results.append({
                        "url": link,
                        "title": title.strip(),
                        "price": price.strip(),
                        "permit": permit.strip(),
                        "reference": reference.strip(),
                    })

                    print(f"     ✓ {title[:40]} | {price} | Permit: {permit} | Ref: {reference}")

                except Exception as e:
                    print(f"     ✗ Ошибка: {e}")
                    results.append({"url": link, "error": str(e)})

            page_num += 1
            await asyncio.sleep(2)

        await browser.close()

    # Сохраняем CSV
    if results:
        with open("listings.csv", "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["url", "title", "price", "permit", "reference"])
            writer.writeheader()
            for r in results:
                writer.writerow({k: r.get(k, "") for k in ["url", "title", "price", "permit", "reference"]})
        print(f"\n✅ Сохранено {len(results)} листингов → listings.csv")

    return results


if __name__ == "__main__":
    url = input("Вставь ссылку на поиск PF: ").strip()
    asyncio.run(scrape_listings(url))
