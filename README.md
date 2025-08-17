# RM Stock Tracker

An informative and user-friendly web app to explore U.S. stocks and major market indices using real-time financial data. Built with Python, Flask, SQLAlchemy, Bootstrap, Chart.js and the Polygon.io API.

> **Live Site:** [www.rmstocktracker.com](https://www.rmstocktracker.com)

---

## Features

- **Search Stocks** by ticker symbol or company name
- View detailed stock information:
  - Day open, high, low, close, and volume
  - Today's price change and % change with up/down arrow
  - 30-day, 50-day and 200-day moving averages (DMA)
  - % Difference from 200-DMA (color-coded)
  - 52-week high and low
  - Market cap (with readable formatting)
  - Company overview and related companies
- **Interactive Stock Charts**
  - Choose from multiple timeframes: 1D, 1W, 1M, 3M, 6M, YTD, 1Y, 3Y, 5Y
  - Smooth transitions using AJAX without page reloads
  - Custom legends, hover info, and responsive design for mobile
  - Loading indicators and missing-data overlays for a better experience
- **Summary Section with Charts**
  - Visualize stock performance with neat, professional, and color-coded summary charts
  - Responsive summary cards with key highlights
- **Top Market Movers**
  - View top gainers, losers, and most traded stocks
  - Switch between overall market, S&P 500, Nasdaq 100, and Dow Jones
- **Explore Indices**
  - S&P 500, Nasdaq 100, Dow Jones, Magnificent Seven, ARKK Innovation, Berkshire Hathaway
  - View top holdings with metrics like weight, day close, DMA values, % difference, and more
  - Sort by weight, company name, DMA %, or today's price change
- Color-coded 200-DMA % Difference:
  - **Dark Green**: ≥ +10%
  - **Green**: +2% to +10%
  - **Yellow**: -2% to +2%
  - **Red**: -2% to -10%
  - **Dark Red**: ≤ -10%
- Animated ticker tape showing popular and some random stocks
- Stock search bar showing relevant suggestions with easy keyboard navigation
- Loading spinner overlay when navigating pages or charts that take longer time to load
- Data last updated time shown in Eastern Time
- Responsive design with Bootstrap 5
- Clean UI, consistent layout, and helpful error messages

---

## Tech Stack

- **Backend**: Python, Flask, SQLAlchemy  
- **Frontend**: HTML, CSS, JS, Jinja2, Bootstrap 5, Chart.js  
- **Database**: SQLite (dev), MySQL (prod)  
- **APIs**: Polygon.io, SlickCharts

---

## Project Structure

```
├── app.py                  # Flask application entry point
├── data_collectors/        # Scripts to fetch stock, index, and market data
├── db_populate_scripts/    # Scripts to update and populate database
├── models/                 # SQLAlchemy ORM models
├── static/                 # Static files (CSS, JS, favicon, etc.)
│   ├── assets/
│   ├── js/
│   └── styles/
├── templates/              # Jinja2 HTML templates
│   └── macros/             # Reusable Jinja components
└── utils/                  # Helpers for datetime, filters, etc.
    └── db_queries/         # Scripts to run database queries
```

---

## Getting Started

1. **Clone the repository**

2. **Set up a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate     # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file** in the root directory

   ```env
   IS_RELEASE="0"
   DATABASE_URI=your_sqlite_db_uri
   POLYGON_API_KEY=your_polygon_api_key
   ```

5. **Run the app**

   ```bash
   flask run
   ```

---

## License

This project is licensed under the Creative Commons Attribution 4.0 International License.  
See the [LICENSE](./LICENSE.md) file for details.

---

## Release Notes

See [Release Notes](./RELEASE_NOTES.md) for version history and changelog.
