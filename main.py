
import time
import re
import aiohttp
from urllib.parse import unquote
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import os


SEM = asyncio.Semaphore(3)  # max 3 cities at once

# ---------------- CONFIG ----------------
BASE_URL = "https://www.google.com/maps/search/"

# ---------- ------ IMPORT CITIES DATA ----------------
import pandas as pd

cities_df = pd.read_excel("USA_Cities_2025_New.xlsx")


#---------------- SEARCH TERMS ----------------

def build_search_terms(city, state_name):
    return [
        f"Hair Salon in {city}, {state_name}"
    ]

# ---------------- REGEX ----------------

EMAIL_REGEX = re.compile(
    r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"
)
PHONE_REGEX = r"\+?\d[\d\s().-]{8,}\d"

# ---------------- HELPERS ----------------
DUMMY_EMAILS = {
                    "user@domain.com",
                    "hi@mystore.com",
                    "your@email.com",
                    "example@example.com",
                    "info@mysite.com",
                    "info@example.com",
                    "hello@locmaps.com",
                    "filler@godaddy.com",
                    "contact@mysite.com",
                    "name@example.com",
                    "impallari@gmail.com",
                    "someone@example.com",
                    "info@indiantypefoundry.com",
                    "team@latofonts.com",
                    "hello@usmapsz.xyz",
                    "support@glossgenius.com",
                    "icon@2x.webp",
                    "email@email.com"
                }
async def extract_email_fast(url, session):
    try:
        async with session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=4),
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        ) as resp:
            if resp.status != 200:
                return "NA"

            html = await resp.text()

            # 1️⃣ mailto first (most reliable)
            mailtos = re.findall(r"mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", html, re.I)
            if mailtos:
                return mailtos[0]

            # 2️⃣ visible emails
            emails = EMAIL_REGEX.findall(html)
            if emails:
                
                def clean_email(e: str) -> str:
                    e = e.lower().replace("mailto:", "")
                    return re.sub(r"[^\w@.+-]", "", e)

                # normalize all once
                cleaned = [clean_email(e) for e in emails]

                # fastest correct check
                if any(e in DUMMY_EMAILS for e in cleaned):
                    return "NA"
                em = emails[0].lower()
                local_part = em.split("@")[0]

                IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".svg")

                if emails[0].lower().endswith(IMAGE_EXTS):
                    return "NA"
                # reject usernames that are mostly digits/hex
                digit_ratio = sum(c.isdigit() for c in local_part) / len(local_part)
                if digit_ratio > 0.5:
                    return "NA"
                
                return emails[0]

    except:
        pass

    return "NA"

async def warm_up_maps(browser):
    page = await browser.new_page()
    await page.goto("https://www.google.com/maps", timeout=60000)
    await page.wait_for_timeout(8000)

    # Simulate human interaction
    await page.mouse.move(300, 300)
    await page.mouse.wheel(0, 1200)
    await page.wait_for_timeout(3000)

    await page.close()

def extract_name_from_url(url):
    try:
        part = url.split("/place/")[1].split("/")[0]
        return unquote(part).replace("+", " ").strip()
    except:
        return "NA"

# def extract_phone_fallback(page):
#     try:
#         text = page.inner_text("body")
#         phones = re.findall(PHONE_REGEX, text)
#         if phones:
#             return phones[0]
#     except:
#         pass
#     return "NA"

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

async def scroll_results_feed(page, pause_time=2, max_attempts=60):
    feed = await page.query_selector("div[role='feed']")
    if not feed:
        return

    previous_height = 0
    same_height_count = 0

    for _ in range(max_attempts):
        await page.evaluate(
            "(feed) => feed.scrollBy(0, feed.scrollHeight * 2)",
            feed
        )
        await asyncio.sleep(pause_time)

        current_height = await page.evaluate(
            "(feed) => feed.scrollHeight",
            feed
        )

        if current_height == previous_height:
            same_height_count += 1
        else:
            same_height_count = 0

        if same_height_count >= 2:
            break

        previous_height = current_height

def safe_text(el):
    try:
        return el.inner_text().strip() if el else "NA"
    except:
        return "NA"

def extract_lat_lng_from_url(url):
    try:
        match = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", url)
        if match:
            return match.group(1), match.group(2)
    except:
        pass
    return "NA", "NA"

# ---------------- BUSINESS SCRAPER ----------------
async def safe_goto(page, url):
    try:
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        return True
    except:
        return False

async def scrape_business_details(page, session, url):

    if not await safe_goto(page, url):
        return None
    address_el = await page.query_selector('button[data-item-id*="address"]')

    if not address_el:
        # Only wait if really missing
        try:
            await page.wait_for_selector(
                'button[data-item-id*="address"]',
                timeout=2500
            )
        except:
            pass
    name_el = await page.query_selector("h1")
    name = await name_el.inner_text() if name_el else extract_name_from_url(url)

    address = phone = website = "NA"

    # address_el = await page.query_selector('button[data-item-id*="address"]')
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

# ---------------- LOCATION FILTER ----------------

# from math import radians, cos, sin, asin, sqrt

# def haversine(lat1, lon1, lat2, lon2):
#     R = 6371  # km
#     lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

#     dlat = lat2 - lat1
#     dlon = lon2 - lon1

#     a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
#     return 2 * R * asin(sqrt(a))

# def is_within_city_radius(lat, lng, city_lat, city_lng, radius_km=20):
#     try:
#         lat = float(lat)
#         lng = float(lng)
#     except:
#         return False

#     return haversine(lat, lng, city_lat, city_lng) <= radius_km

# ---------------- EXPORT ----------------

OUTPUT_DIR = "state_city_excels"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def export_state_excel(state_code, state_name, city_results):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = f"{state_code}_{state_name.replace(' ', '_')}_{timestamp}.xlsx"
    print(file_path)
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        for city, data in city_results.items():
            if not data:
                continue

            df = pd.DataFrame(
                data,
                columns=[
    "Name", "Address", "Phone", "Website", "Email",
    "Google Maps URL", "Latitude", "Longitude"
]

            )

            sheet_name = city[:31]  # Excel sheet name limit
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"[✓] Created {file_path}")

# ---------------- MAIN ----------------

async def scrape_city(browser, session, city, state, city_lat, city_lng):

    async with SEM:
        context = await browser.new_context()
        page = await context.new_page()

        all_links = set()
        results = []

        search_url = BASE_URL + f"Hair Salon in {city}, {state},USA".replace(" ", "+")
        print(f"[+] Searching: {city}")

        await page.goto(search_url, timeout=60000)
        await page.wait_for_timeout(5000)

        await scroll_results_feed(page)

        links = await page.query_selector_all("a[href*='/maps/place']")
        for link in links:
            href = await link.get_attribute("href")
            if href:
                all_links.add(href)

        # total = len(all_links)


        for url in (all_links):
            # print(f"[TEST {idx}/{total}] Scraping business")
            data = await scrape_business_details(page, session, url)

            if not data:
                continue

            # lat, lng = data[-2], data[-1]
            # if is_within_city_radius(lat, lng, city_lat, city_lng):
            results.append(data)

        await context.close()
        return city, results


TARGET_STATE_CODE = "UT"   


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        async with aiohttp.ClientSession() as session:
            # 🔥 Warm-up
            await warm_up_maps(browser)


            # ✅ FILTER CITIES BY STATE CODE
            state_df = cities_df[cities_df["State Code"] == TARGET_STATE_CODE]

            # (optional) limit cities for testing
            # state_df = state_df.head(2)

            state_name = state_df["State"].iloc[0]
            # print(f"\n=== STATE: {state_name} ===")

            tasks = []

            for (_, row) in (state_df.iterrows()):

                tasks.append(
                    scrape_city(
                        browser,
                        session,
                        row["City"],
                        state_name,
                        row["Latitude"],
                        row["Longitude"]
                    )
                )

            results = await asyncio.gather(*tasks)

            city_results = {city: data for city, data in results if data}

            export_state_excel(TARGET_STATE_CODE, state_name, city_results)

            await browser.close()


if __name__ == "__main__":
    start_time = time.perf_counter()
    asyncio.run(main())
    end_time = time.perf_counter()

    elapsed = end_time - start_time
    print(f"\n⏱ Total execution time: {elapsed:.2f} seconds")
