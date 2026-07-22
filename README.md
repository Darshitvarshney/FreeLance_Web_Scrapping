# 🚀 Google Maps Business Data Scraper

A high-performance **Google Maps Business Data Scraper** built with **Python**, **Playwright**, and **asyncio** for collecting business information at scale.

The scraper automates Google Maps searches for a given business category (e.g., Hair Salons) across multiple cities and states, extracts business details, visits business websites to collect email addresses, and exports the results into well-structured Excel files.

The project includes a production-ready scraper with resume support, progress tracking, concurrent scraping, and Excel merging utilities, making it suitable for large-scale lead generation and business intelligence.

---

# ✨ Features

* 🔍 Automated Google Maps scraping
* 🌎 State-wise and city-wise business search
* ⚡ Asynchronous scraping using Playwright
* 📧 Email extraction from business websites
* 📞 Phone number extraction
* 🌐 Website URL extraction
* 📍 Latitude & Longitude extraction
* 📄 Excel export with separate sheets
* 🔄 Resume scraping after interruption
* 📊 Batch processing
* 🚀 Concurrent scraping for improved performance
* 🧹 Duplicate removal utility

---

# 🛠 Tech Stack

| Technology          | Purpose                   |
| ------------------- | ------------------------- |
| Python              | Programming Language      |
| Playwright          | Browser Automation        |
| asyncio             | Concurrent Task Execution |
| aiohttp             | Async HTTP Requests       |
| pandas              | Excel & Data Processing   |
| openpyxl            | Excel File Handling       |
| Regular Expressions | Email Extraction          |
| JSON                | Progress Tracking         |

---

# 📂 Project Structure

```text
FreeLance_Web_Scrapping/

├── main.py
│   ├── Standard asynchronous scraper
│   ├── Google Maps scraping
│   ├── Website email extraction
│   └── Excel generation
│
├── main2.py
│   ├── Production scraper
│   ├── Resume support
│   ├── Progress tracking
│   ├── Batch processing
│   ├── Concurrent scraping
│   ├── Resource blocking
│   └── Faster execution
│
├── combine.py
│   ├── Merge generated Excel files
│   └── Remove duplicate businesses
│
├── USA_Cities_2025_New.xlsx
│
└── README.md
```

---

# ⚙️ How It Works

## Step 1 — Load Cities

The scraper loads city and state information from:

```
USA_Cities_2025_New.xlsx
```

---

## Step 2 — Generate Search Query

A search query is generated dynamically.

Example:

```
Hair Salon in Phoenix, Arizona
```

The business category can easily be changed to scrape different industries such as:

* Restaurants
* Dentists
* Hotels
* Car Dealers
* Electricians
* Lawyers
* Used Car Dealers

---

## Step 3 — Search Google Maps

Playwright launches Chromium and opens Google Maps.

The scraper searches for the generated query.

---

## Step 4 — Scroll Search Results

Google Maps loads businesses dynamically.

The scraper automatically scrolls through the result feed until all businesses are loaded.

---

## Step 5 — Visit Business Listings

Each business page is opened individually.

The scraper extracts:

* Business Name
* Address
* Phone Number
* Website
* Google Maps URL
* Latitude
* Longitude

---

## Step 6 — Crawl Business Website

If a business website is available, the scraper downloads the homepage using **aiohttp**.

Email addresses are extracted using regular expressions while filtering out placeholder and invalid emails.

---

## Step 7 — Store Results

Business records are stored in memory and periodically written to Excel.

Each state is exported as a separate workbook with individual worksheets for every city.

---

## Step 8 — Resume Support (main2.py)

The production scraper stores progress in:

```
scraping_progress.json
```

If the scraper stops unexpectedly, it resumes from the last processed city without starting over.

---

## Step 9 — Merge Excel Files

After scraping, `combine.py` merges all generated Excel files into a single dataset and removes duplicate businesses using the Google Maps URL as the unique identifier.

---

# 📊 Extracted Fields

Each business record contains:

* Business Name
* Address
* Phone Number
* Website
* Email Address
* Google Maps URL
* Latitude
* Longitude

---

# 🚀 Scraper Versions

## main.py

The initial asynchronous scraper focused on reliable data extraction.

### Features

* Async Google Maps scraping
* Website crawling
* Email extraction
* Excel export
* City-wise processing

---

## main2.py

The optimized production version with several performance improvements.

### Improvements

* Progress tracking
* Resume support
* Batch processing
* Concurrent city scraping
* Concurrent business scraping
* Resource blocking (images, fonts, CSS, media)
* Faster execution
* Better memory management

---

# ▶️ Installation

Clone the repository:

```bash
git clone https://github.com/Darshitvarshney/FreeLance_Web_Scrapping.git
```

Navigate to the project:

```bash
cd FreeLance_Web_Scrapping
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Install Playwright browser:

```bash
playwright install
```

---

# ▶️ Running the Project

Run the standard scraper:

```bash
python main.py
```

Run the optimized production scraper:

```bash
python main2.py
```

Merge Excel files:

```bash
python combine.py
```

---

# 📈 Workflow Diagram

```text
USA_Cities_2025_New.xlsx
            │
            ▼
     Load City & State
            │
            ▼
 Generate Search Query
            │
            ▼
     Google Maps Search
            │
            ▼
 Scroll Through Results
            │
            ▼
 Collect Business Links
            │
            ▼
 Visit Business Pages
            │
            ▼
Extract Business Details
            │
            ▼
 Visit Business Website
            │
            ▼
 Extract Email Address
            │
            ▼
  Save Excel per State
            │
            ▼
 Merge Excel Files
            │
            ▼
 Remove Duplicates
            │
            ▼
    Final Lead Dataset
```

---

# 💼 Use Cases

* Lead Generation
* Market Research
* Sales Prospecting
* Business Directory Creation
* Competitor Analysis
* Location Intelligence
* Data Collection for Freelance Projects

---

# 🔮 Future Enhancements

* Proxy Rotation
* CAPTCHA Handling
* Multi-country Support
* CSV & Database Export
* Docker Support
* Scheduler Integration
* Automatic Category Selection
* Contact Page Crawling
* Parallel Browser Instances

---

# 👨‍💻 Author

**Darshit Varshney**

* GitHub: https://github.com/Darshitvarshney
* LinkedIn: https://www.linkedin.com/in/darshit-varshney-422002390

---

# 📜 License

This project is intended for educational and research purposes. Please ensure that your use complies with Google's Terms of Service and applicable laws regarding web scraping.

---

# ⭐ Support

If you found this project useful, consider giving it a ⭐ on GitHub. Your support helps improve the project and encourages future development.
