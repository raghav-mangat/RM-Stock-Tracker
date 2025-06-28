# Release Notes — v2.1.0
**Release Date:** June 22, 2025

> **Live Site:** [raghavmangat.pythonanywhere.com](https://raghavmangat.pythonanywhere.com/)

## Overview

This release builds on the solid foundation of v2.0.0 by polishing the interface, improving user experience, expanding functionality, refactoring the codebase, and enhancing reliability and structure.

---

## What’s New

### User Experience Improvements

- **Error Handling:**
  - Added custom **404** and **500** error pages.
  - 500 page includes a **Refresh** button alongside "Go Home".

- **Professional Layout & Consistency:**
  - Improved layout consistency across all pages.
  - Footer and navbar redesigned and fixed to bottom and top of screen respectively.
  - Footer now includes social links (GitHub, LinkedIn, Instagram).

- **Homepage Redesign:**
  - **Stocks** and **Indexes** sections shown **side-by-side** in responsive Bootstrap cards.
  - Improved homepage description for professionalism and clarity.

- **Accessibility & SEO:**
  - Improved HTML semantics and metadata.
  - Better formatting and description for screen readers and search engines.

### New Functional Features

- **Last Updated Times:**
  - For each **stock**, the last updated timestamp from Polygon is stored and displayed.
  - For each **index**, the ET timestamp at which the DB was populated is stored and shown.

- **DMA % Difference Popover:**
  - Added a helpful Bootstrap **popover** to explain the 200-DMA % difference.
  - Includes a color legend for quick understanding.
  - Popover is globalized and reused via a **Jinja macro**.

### Data Integrity Handling

- Added a new script to fetch **market status** at 12 p.m. ET and store it in a JSON file.
- The **DB population script** checks this market status before running at 4 p.m. and 8 p.m. ET to ensure accurate data (i.e., avoids populating with all-zero snapshot values when market is closed).

### Code Refactoring & Project Structure

- **Filter & Error Handling Utilities:**
  - Moved all template filters and error handlers to a new `utils/` package.
  - This keeps `app.py` clean and modular.

- **Macro Templates:**
  - Created a `macros/` folder in `templates/`.
  - Centralized the DMA % popover for reuse in both show_stock and show_index.

- **Stock Data Collection Refactor:**
  - Changed stock data script to return a **Stock model object** instead of JSON.
  - Created a centralized attribute list to avoid hardcoding values.

- **Improved Number Formatting:**
  - All large numbers (market cap, volume, etc.) now use proper comma-separated formatting for readability.

---

## Summary

Version `v2.1.0` brings a highly polished experience for users and developers. It introduces reliability checks for data accuracy, better error handling, improved UX, and a cleaner codebase.

**Next Steps:** The foundation is now ready for future features like historical charts, user login, and custom watchlists.

**Full Changelog:** https://github.com/RaghavMangat2000/RM-Stock-Tracker/compare/v2.0.0...v2.1.0


------------------------------------------------------------------------------------------------------------


# Release Notes — v2.0.0
**Release Date:** June 19, 2025

> **Live Site:** [raghavmangat.pythonanywhere.com](https://raghavmangat.pythonanywhere.com/)

## Overview

This release introduces a full **database-powered** version of RM Stock Tracker. It replaces the older JSON-based system with a dynamic and scalable backend using **Flask, SQLAlchemy, and SQLite**. You can now search and view real-time stock data and explore the composition of major stock market indexes.

---

## What’s New

### Home Page Navigation

- Choose between the two main options:
  - **Stocks**: Search for any stock in the U.S. market.
  - **Indexes**: Browse a list of 6 major indexes.

### Stock Search & Detail View

- Search for any stock using its ticker symbol or company name.
- See a detailed view with:
  - Ticker and company name
  - Day closing price
  - 200-day moving average (200-DMA)
  - % difference from the 200-DMA
  - Other market data (open, high, low, volume, etc.)

### Index Listings & Holdings View

- View a list of 6 major indexes:
  - S&P 500, Nasdaq 100, Dow Jones, Magnificent Seven, ARKK, Berkshire Hathaway
- Clicking an index shows all its holdings:
  - Company Name, Ticker, Weight in index
  - Day Close, 200-DMA, % Difference
- Sort the list in ascending or descending order of:
  - Weight, Day Close, 200-DMA , or % Difference
- Click a stock in the list to see more details about that stock.

### 200-DMA % Difference Coloring

The % difference between the day close and 200-day moving average is color-coded for quick insight:

- **Dark Green**: >= +10%
- **Green**: Between +2% and +10%
- **Yellow**: Between -2% and +2%
- **Red**: Between -2% and -10%
- **Dark Red**: <= -10%

---

## Technical Improvements

- Integrated **SQLAlchemy** and a full database schema:
  - `Stock`, `StockMaster`, `Index`, and `IndexHolding` tables.
- All data is now dynamically fetched and cached in the database.
- A **data population script** scrapes data from [SlickCharts](https://www.slickcharts.com) and pulls detailed stock data using the Polygon.io API.
- Automatically creates the `instance/` folder and database file if missing.
- Responsive Bootstrap layout with a **dummy navbar and footer** for structure.

---

## Summary

Version `v2.0.0` transforms the RM Stock Tracker into a scalable, real-time web app with search, detailed views, and index analysis. It's a strong foundation for adding features like charts, watchlists, and login functionality in the future.

**Full Changelog**: https://github.com/RaghavMangat2000/RM-Stock-Tracker/compare/v1.2.0...v2.0.0