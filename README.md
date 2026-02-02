# FreeLance_Web_Scrapping

# 📊 Google Maps Business Data Scraper

## Project Overview

This project is a high-performance web scraping solution designed to extract structured business data from **Google Maps** at a city and state level.
It automates the collection of business information such as:

* Business Name
* Address
* Phone Number
* Website
* Email (if available)
* Google Maps URL
* Latitude & Longitude

The scraper is optimized for **scalability**, **accuracy**, and **export-ready datasets** (Excel format).

---

## ⚙️ Technology Stack

* Python 3.9+
* Playwright (browser automation)
* aiohttp (async HTTP requests)
* asyncio (concurrency management)
* pandas (data processing)
* openpyxl (Excel export)

---

## 📁 Project Structure

```
project/
│
├── main.py         # Version 1 – Deep extraction (slow but very thorough)
├── main_final.py   # Version 2 – Optimized high-speed scraper
├── combine.py      # Utility script to merge multiple Excel outputs
├── USA_Cities_2025_New.xlsx
```

---

## 🚀 main.py (Version 1 – Deep Extraction Engine)

**Purpose:**
Designed for **maximum data completeness**.

**Characteristics:**

* Sequential scraping logic
* Performs deeper page interaction
* Uses higher wait times for element detection
* Safer for dynamic pages
* Best suited for:

  * Small datasets
  * High-value leads
  * When accuracy is prioritized over speed

**Advantages:**

* More stable
* Higher chance of capturing missing fields
* Minimal risk of partial data

**Limitation:**

* Slower execution due to conservative timeouts and reduced concurrency

---

## ⚡ main_final.py (Version 2 – High-Speed Production Scraper)

**Purpose:**
Built for **large-scale data collection** with performance optimization.

**Enhancements:**

* Parallel city scraping using asyncio
* Parallel business scraping using semaphores
* Resource blocking (images, fonts, media, CSS)
* Reduced timeouts
* Batched Excel exports
* Resume support using progress file

**Advantages:**

* 3–5x faster than Version 1
* Suitable for:

  * State-level scraping
  * Large datasets
  * Commercial lead generation
* Automatically saves progress
* Handles crashes and restarts gracefully

**Trade-off:**

* Slightly less aggressive extraction than Version 1
* Optimized for **speed + sufficient data coverage**

---

## 📤 Output Format

Each run generates Excel files where:

* Each city is stored as a separate sheet
* Columns:

  ```
  Name | Address | Phone | Website | Email | Google Maps URL | Latitude | Longitude
  ```
* Files are timestamped for traceability

---

## 🧩 combine.py (Data Merger)

This script:

* Combines multiple state or batch Excel files
* Removes duplicates using Google Maps URL
* Produces a single consolidated workbook

Used after scraping is complete for final dataset delivery.

---

## ▶️ How to Run

### Install dependencies:

```bash
pip install playwright aiohttp pandas openpyxl
playwright install
```

### Run Version 1 (Deep Mode):

```bash
python main.py
```

### Run Version 2 (Fast Mode):

```bash
python main_final.py
```

### Merge Output Files:

```bash
python combine.py
```

---

## 📌 Use Case

* Lead generation
* Market research
* Business intelligence
* Location-based analytics
* Freelance data delivery

---

## 🧠 Development Philosophy

This project was developed in **two stages**:

1. **main.py** – Accuracy-first prototype
2. **main_final.py** – Speed-optimized production build

This ensures both:

* Data integrity
* Operational efficiency

---

## 📄 License & Usage

This codebase is provided as part of a freelance project and is intended for controlled, ethical, and compliant web scraping.



