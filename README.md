# RM Stock Tracker

A lightweight web app to search U.S. stocks and explore major market indexes with live financial data, built using Python, Flask, SQLAlchemy, and Bootstrap.

> Live Site: [raghavmangat.pythonanywhere.com](https://raghavmangat.pythonanywhere.com)

---

## Features

- **Search Stocks** by ticker or company name
- View detailed info:
  - Last closing price
  - 200-day moving average (200-DMA)
  - % Difference from 200-DMA
  - Open, high, low, volume, etc.
- **Explore Indexes** like:
  - S&P 500, Nasdaq 100, Dow Jones, Magnificent Seven, ARKK, Berkshire Hathaway
- See each index’s holdings:
  - Ticker, company name, weight, last close, 200-DMA, % difference
- Sort holdings by:
  - Weight, last close, 200-DMA, or % difference
- Click on the stock name of a holding to view detailed info
- Color-coded % difference for fast visual analysis
  - **Dark Green**: >= +10%
  - **Green**: Between +2% and +10%
  - **Yellow**: Between -2% and +2%
  - **Red**: Between -2% and -10%
  - **Dark Red**: <= -10%
---

## Tech Stack

- **Backend**: Python, Flask, SQLAlchemy
- **Frontend**: HTML, CSS, Bootstrap
- **Database**: SQLite (dev) / MySQL (prod)
- **APIs**: Polygon.io, SlickCharts

---

## Getting Started

To run this project locally:

1. **Clone the repository**
2. **Create a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file** in the project root with the following variables:

   ```env
   IS_RELEASE="0"
   DATABASE_URI=your_sqlite_database_uri_here
   POLYGON_API_KEY=your_polygon_api_key_here
   ```

5. **Run the app**

   ```bash
   flask run
   ```

---

## License

This project is licensed under the Creative Commons Attribution 4.0 International License.  
See the [LICENSE](./LICENSE.md) file for details.
