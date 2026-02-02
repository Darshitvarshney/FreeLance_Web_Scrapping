import time, random
import re
import aiohttp
from urllib.parse import unquote
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os
import pandas as pd
import json

# ---------------- CONFIG ----------------
SEM = asyncio.Semaphore(3)  # Increased concurrent cities
BIZ_SEM = asyncio.Semaphore(3)  # Increased concurrent businesses

BASE_URL = "https://www.google.com/maps/search/"
TARGET_STATE_CODE = "AZ" 
BATCH_SIZE = 25
START_FROM_INDEX = 0

OUTPUT_DIR = "state_city_excels"
PROGRESS_FILE = "scraping_progress.json"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------- PROGRESS TRACKING ----------------
def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {"last_completed_index": -1, "state_code": None}

def save_progress(state_code, last_index):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({
            "last_completed_index": last_index,
            "state_code": state_code,
            "timestamp": datetime.now().isoformat()
        }, f)

# ---------------- DATA IMPORT ----------------
cities_df = pd.read_excel("USA_Cities_2025_New.xlsx")

# ---------------- REGEX ----------------
EMAIL_REGEX = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
PHONE_REGEX = r"\+?\d[\d\s().-]{8,}\d"

DUMMY_EMAILS = {
    "user@domain.com", "hi@mystore.com", "your@email.com",
    "example@example.com", "info@mysite.com", "info@example.com",
    "hello@locmaps.com", "filler@godaddy.com", "contact@mysite.com",
    "name@example.com", "impallari@gmail.com", "someone@example.com",
    "info@indiantypefoundry.com", "team@latofonts.com",
    "hello@usmapsz.xyz", "support@glossgenius.com",
    "icon@2x.webp", "email@email.com"
}

# ---------------- RESOURCE BLOCKING ----------------
async def block_resources(route):
    if route.request.resource_type in {"image", "media", "font", "stylesheet"}:
        await route.abort()
    else:
        await route.continue_()

# ---------------- EMAIL EXTRACTION ----------------
async def extract_email_fast(url, session):
    try:
        async with session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=3),  # Reduced timeout
            headers={"User-Agent": "Mozilla/5.0"}
        ) as resp:
            if resp.status != 200:
                return "NA"

            html = await resp.text()

            # mailto first
            mailtos = re.findall(r"mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", html, re.I)
            if mailtos:
                return mailtos[0]

            # visible emails
            emails = EMAIL_REGEX.findall(html)
            if emails:
                def clean_email(e: str) -> str:
                    e = e.lower().replace("mailto:", "")
                    return re.sub(r"[^\w@.+-]", "", e)

                cleaned = [clean_email(e) for e in emails]

                if any(e in DUMMY_EMAILS for e in cleaned):
                    return "NA"
                
                em = emails[0].lower()
                local_part = em.split("@")[0]

                IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".svg")
                if em.endswith(IMAGE_EXTS):
                    return "NA"

                digit_ratio = sum(c.isdigit() for c in local_part) / len(local_part)
                if digit_ratio > 0.5:
                    return "NA"
                
                return emails[0]
    except:
        pass
    return "NA"

# ---------------- HELPER FUNCTIONS ----------------
def extract_name_from_url(url):
    try:
        part = url.split("/place/")[1].split("/")[0]
        return unquote(part).replace("+", " ").strip()
    except:
        return "NA"

async def extract_address_fallback(page):
    try:
        panel = await page.query_selector("div[role='main']")
        if not panel:
            return "NA"
        text = await panel.inner_text()
        for line in text.split("\n"):
            if "," in line and any(x in line for x in ["Street", "St", "Ave", "Road", "Rd", "Blvd", "Drive"]):
                return line.strip()
    except:
        pass
    return "NA"

def extract_lat_lng_from_url(url):
    try:
        match = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", url)
        if match:
            return match.group(1), match.group(2)
    except:
        pass
    return "NA", "NA"

async def scroll_results_feed(page, max_attempts=25):  # Reduced from 40
    feed = await page.query_selector("div[role='feed']")
    if not feed:
        return

    previous_height = 0
    same_height_count = 0

    for _ in range(max_attempts):
        await page.evaluate("(feed) => feed.scrollBy(0, feed.scrollHeight * 2)", feed)
        await asyncio.sleep(random.uniform(0.8, 1.5))  # Faster scrolling

        current_height = await page.evaluate("(feed) => feed.scrollHeight", feed)

        if current_height == previous_height:
            same_height_count += 1
        else:
            same_height_count = 0

        if same_height_count >= 2:
            break

        previous_height = current_height

# ---------------- BUSINESS SCRAPER ----------------
async def safe_goto(page, url):
    try:
        await page.goto(url, timeout=30000, wait_until="domcontentloaded")  # Reduced timeout
        await page.wait_for_timeout(1000)  # Reduced wait
        return True
    except:
        return False

async def scrape_business_details(page, session, url):
    if not await safe_goto(page, url):
        return None

    try:
        await page.wait_for_selector('button[data-item-id*="address"]', timeout=1500)  # Reduced
    except:
        pass

    name_el = await page.query_selector("h1")
    name = await name_el.inner_text() if name_el else extract_name_from_url(url)

    address = phone = website = "NA"

    address_el = await page.query_selector('button[data-item-id*="address"]')
    if address_el:
        address = (await address_el.inner_text()).strip()

    if address == "NA":
        address = await extract_address_fallback(page)

    phone_el = await page.query_selector('button[data-item-id*="phone"]')
    if phone_el:
        phones = re.findall(PHONE_REGEX, await phone_el.inner_text())
        if phones:
            phone = phones[0]

    website_el = await page.query_selector('a[data-item-id*="authority"]')
    if website_el:
        website = await website_el.get_attribute("href")

    email = "NA"
    if website != "NA":
        email = await extract_email_fast(website, session)

    lat, lng = extract_lat_lng_from_url(url)

    return [name, address, phone, website, email, url, lat, lng]

async def scrape_one_business(context, session, url):
    async with BIZ_SEM:
        page = await context.new_page()
        try:
            return await scrape_business_details(page, session, url)
        finally:
            await page.close()

# ---------------- CITY SCRAPER ----------------
async def scrape_city(browser, session, city, state, city_lat, city_lng):
    async with SEM:
        context = await browser.new_context(
            locale="en-US",
            timezone_id="America/New_York"
        )
        # Block resources at context level for better performance
        await context.route("**/*", block_resources)
        page = await context.new_page()

        all_links = set()
        results = []

        search_url = BASE_URL + f"Hair Salon in {city}, {state}, USA".replace(" ", "+")
        print(f"[+] {city}")

        try:
            await page.goto(search_url, timeout=45000)  # Reduced
            await page.wait_for_timeout(3000)  # Reduced
            await scroll_results_feed(page)

            links = await page.query_selector_all("a[href*='/maps/place']")
            for link in links:
                href = await link.get_attribute("href")
                if href:
                    all_links.add(href)

            tasks = [scrape_one_business(context, session, url) for url in all_links]
            biz_results = await asyncio.gather(*tasks, return_exceptions=True)  # Don't fail on errors

            for data in biz_results:
                if data and not isinstance(data, Exception):
                    results.append(data)

        except Exception as e:
            print(f"[!] {city} failed: {str(e)[:50]}")
        finally:
            await context.close()

        return city, results

# ---------------- EXPORT ----------------
def export_batch_to_excel(state_code, state_name, city_results, batch_num=None):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    batch_suffix = f"_batch{batch_num}" if batch_num else ""
    file_path = os.path.join(
        OUTPUT_DIR,
        f"{state_code}_{state_name.replace(' ', '_')}{batch_suffix}_{timestamp}.xlsx"
    )

    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        for city, data in city_results.items():
            if not data:
                continue

            df = pd.DataFrame(
                data,
                columns=["Name", "Address", "Phone", "Website", "Email",
                        "Google Maps URL", "Latitude", "Longitude"]
            )

            sheet_name = city[:31]
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"[✓] Batch {batch_num} saved")
    return file_path

# ---------------- MAIN ----------------
async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--disable-extensions"
            ]
        )

        # Increased connector limit for more concurrent connections
        connector = aiohttp.TCPConnector(limit=50, limit_per_host=10)
        async with aiohttp.ClientSession(connector=connector) as session:
            state_df = cities_df[cities_df["State Code"] == TARGET_STATE_CODE].reset_index(drop=True)
            state_name = state_df["State"].iloc[0]
            
            total_cities = len(state_df)
            print(f"\n{'='*60}")
            print(f"STATE: {state_name} ({TARGET_STATE_CODE})")
            print(f"Cities: {total_cities} | Batch: {BATCH_SIZE} | Start: {START_FROM_INDEX}")
            print(f"{'='*60}\n")

            batch_num = (START_FROM_INDEX // BATCH_SIZE) + 1
            
            # Process all cities with periodic batch saves
            pending = set()
            results_queue = []

            city_iter = state_df.iloc[START_FROM_INDEX:].iterrows()

            # Prime the pool with up to SEM limit
            for _ in range(SEM._value):
                try:
                    _, row = next(city_iter)
                except StopIteration:
                    break

                task = asyncio.create_task(
                    scrape_city(
                        browser, session,
                        row["City"], state_name,
                        row["Latitude"], row["Longitude"]
                    )
                )
                pending.add(task)

            completed = 0
            all_city_data = {}

            while pending:
                done, pending = await asyncio.wait(
                    pending, return_when=asyncio.FIRST_COMPLETED
                )

                for task in done:
                    result = await task
                    if result and not isinstance(result, Exception):
                        city, data = result
                        all_city_data[city] = data
                        completed += 1

                        # ---- SAVE BATCH (unchanged logic) ----
                        if completed % BATCH_SIZE == 0:
                            print(f"\n[💾] Saving batch {batch_num}")
                            batch_cities = list(all_city_data.keys())[-BATCH_SIZE:]
                            batch_data = {c: all_city_data[c] for c in batch_cities}

                            export_batch_to_excel(
                                TARGET_STATE_CODE, state_name, batch_data, batch_num
                            )
                            save_progress(TARGET_STATE_CODE, START_FROM_INDEX + completed - 1)

                            for c in batch_cities:
                                del all_city_data[c]

                            import gc
                            gc.collect()
                            batch_num += 1

                    # ---- Schedule NEXT city immediately ----
                    try:
                        _, row = next(city_iter)
                        new_task = asyncio.create_task(
                            scrape_city(
                                browser, session,
                                row["City"], state_name,
                                row["Latitude"], row["Longitude"]
                            )
                        )
                        pending.add(new_task)
                    except StopIteration:
                        pass

            
            # Save remaining cities
            if all_city_data:
                print(f"\n[💾] Saving final batch {batch_num} ({len(all_city_data)} cities)")
                export_batch_to_excel(TARGET_STATE_CODE, state_name, all_city_data, batch_num)
                save_progress(TARGET_STATE_CODE, START_FROM_INDEX + completed - 1)

            await browser.close()
            print(f"\n{'='*60}")
            print(f"[✓] COMPLETE!")
            print(f"{'='*60}\n")

if __name__ == "__main__":
    start_time = time.perf_counter()
    asyncio.run(main())
    elapsed = time.perf_counter() - start_time
    
    print(f"\n⏱ Total: {elapsed:.2f}s ({elapsed/60:.2f}m)")