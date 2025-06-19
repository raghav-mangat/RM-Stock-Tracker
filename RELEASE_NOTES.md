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
  - Last closing price
  - 200-day moving average (200-DMA)
  - % difference from the 200-DMA
  - Other market data (open, high, low, volume, etc.)

### Index Listings & Holdings View

- View a list of 6 major indexes:
  - S&P 500, Nasdaq 100, Dow Jones, Magnificent Seven, ARKK, Berkshire Hathaway
- Clicking an index shows all its holdings:
  - Company Name, Ticker, Weight in index
  - Last Close, 200-DMA, % Difference
- Sort the list in ascending or descending order of:
  - Weight, Last Close, 200-DMA , or % Difference
- Click a stock in the list to see more details about that stock.

### 200-DMA % Difference Coloring

The % difference between the last close and 200-day moving average is color-coded for quick insight:

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

**Full Changelog**: https://github.com/RaghavMangat2000/Stocks-Web-App/compare/v1.2.0...v2.0.0