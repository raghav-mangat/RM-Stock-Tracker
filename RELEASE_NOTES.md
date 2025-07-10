# Release Notes - v2.3.0
**Release Date:** July 10, 2025

> **Live Site:** [www.rmstocktracker.com](https://www.rmstocktracker.com)

## Overview

Version 2.3.0 brings many new features and refinements. The website now offers better insights into stock performance, a cleaner UI, more top stock data, and improved backend structure. It’s faster, easier to use, and more helpful for exploring U.S. markets. This is the first version being released since I have transferred ownership of the project repo from my test account "RaghavMangat2000" to my main account "raghav-mangat".

---

## What’s New

### Top Market Movers Section (New!)
- Added a new section showing **Top Gainers**, **Top Losers**, and **Most Traded Stocks**
- Organized using vertical tabs to switch between overall market, S&P 500, Nasdaq 100, and Dow Jones
- Each tab shows horizontal subtabs for the 3 categories

### Ticker Tape Animation
- Added a dynamic ticker tape to the stocks page
- Shows 50 stocks: Popular and some random tickers
- Color-coded with smooth animation

### Index Improvements
- "Today's Change" column added to the index stock table
- Table can now be sorted by this new column
- Added **52-week High** and **52-week Low** columns for more context

### Stock Details Improvements
- Display "Today's Change" and arrow icon (up/down)
- Market cap and volume values are now human-friendly (e.g., 2.4B)
- Better coloring for values based on percentage

### Code Improvements
- Created multiple reusable **Jinja macros** for cards, tables, arrows, and filters
- Added a shared macro for all page Hero sections
- Refactored stock and index table coloring logic for consistency
- Improved search bar with better suggestions and scrollable dropdown with keyboard navigation

### Backend Changes
- Refactored data collector and DB population logic into packages
- Improved error handling, and missing or incorrect data detection
- Better organization of top stocks and populate data utilities

### UI & UX Polishing
- Updated written content across the website to be simpler and easier to understand
- Improved visual layout and border styles
- Added a **favicon** and app icons for browser tabs and mobile

---

## Summary

Version `v2.3.0` upgrades the user experience with new stock insights, better visuals, and cleaner backend structure. The app is now even more useful and easier to explore.

**Full Changelog:** https://github.com/raghav-mangat/RM-Stock-Tracker/compare/v2.2.0...v2.3.0


------------------------------------------------------------------------------------------------------------


# Release Notes - v2.2.0
**Release Date:** June 29, 2025

> **Live Site:** [www.rmstocktracker.com](https://www.rmstocktracker.com)

## Overview

Version 2.2.0 builds on v2.1.0 with numerous user-facing improvements, better filter and sort logic, UI enhancements, backend refactoring, and a move to a custom domain. It emphasizes usability, performance, and maintainability, while polishing the design and interactivity.

---

## What’s New

### UI & Navigation Enhancements

- **Breadcrumbs and Back Button**:
  - Breadcrumb navigation and back buttons added across the site (except the home page) for better page context and smoother navigation.

- **Stock Details Enhancements**:
  - Ticker symbol and company name now included in the stock details table.
  - DMA % Difference popover now works on hover in addition to click.

- **Indexes Table Improvements**:
  - The table on the index page can now be sorted by **company name**.
  - Clean visual layout and spacing added to the **All Indexes** page for improved responsiveness and clarity.

### Filtering and Display Logic

- **200-DMA % Diff Filter**:
  - Index tables can now be filtered by color-coded **200-DMA % Difference** buckets (dark green, green, yellow, red, dark red).
  - Table still supports sorting by multiple columns while filters are active.

- **Last Updated Time in Eastern Time (ET)**:
  - Displaying the last updated time of the data in Eastern Time (ET) across the website.

- **Null Value Display Logic**:
  - If **all filters are selected**, rows with null % difference values are also shown.
  - If **any subset** of filters is selected, null rows are excluded.

- **Cleaner Templates with Jinja Filters**:
  - New modular Jinja filters for formatting float and integer values improve readability and adhere to DRY principles.

- **Handling Missing Data**:
  - Improved checks throughout stock details page to show **"N/A"** where data is unavailable.
  - Special styling added for missing 200-DMA % difference data.

### Backend and Reliability

- **MySQL Reliability**:
  - SQLAlchemy connection pool settings tuned to reduce 500 errors and ensure reliable MySQL connections.

- **Refactored Scripts**:
  - Data collection and DB population scripts refactored and documented for clarity.
  - Unnecessary API calls eliminated by tracking already updated tickers.
  - Reverted to a previous reliable method of fetching DMA values from Polygon.

- **Organized JavaScript**:
  - Created a new `base.js` to centralize common scripts used across templates.

- **URL & Route Clean-up**:
  - Simplified and improved route naming for clarity and consistency.
  - Active links now persist in the navbar when viewing specific stock/index pages.

### Hosting & Domain

- **Custom Domain Launched**:
  - Project now hosted at [www.rmstocktracker.com](https://www.rmstocktracker.com), no longer under the PythonAnywhere subdomain.

---

## Summary

Version `v2.2.0` adds major polish and practical upgrades. It greatly improves index interactivity with filters, improves backend robustness, and completes the move to a professional custom domain. The codebase is now well-positioned for user authentication, dashboards, and future analytics.

**Full Changelog:** https://github.com/raghav-mangat/RM-Stock-Tracker/compare/v2.1.0...v2.2.0


------------------------------------------------------------------------------------------------------------


# Release Notes - v2.1.0
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

**Full Changelog:** https://github.com/raghav-mangat/RM-Stock-Tracker/compare/v2.0.0...v2.1.0


------------------------------------------------------------------------------------------------------------


# Release Notes - v2.0.0
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

**Full Changelog**: https://github.com/raghav-mangat/RM-Stock-Tracker/compare/v1.2.0...v2.0.0