# RM Stock Tracker

A lightweight and professional web app to search U.S. stocks and explore major market indexes using live financial data — built with Python, Flask, SQLAlchemy, and Bootstrap.

> **Live Site**: [raghavmangat.pythonanywhere.com](https://raghavmangat.pythonanywhere.com)

---

##  Features

-  **Search Stocks** by ticker symbol or company name
-  View detailed stock information:
   - Open, high, low, close, volume
   - 200-day moving average (DMA)
   - % Difference between last close and 200-DMA
   - 50-DMA, 52w High/Low
   - Company description, related companies, and more
-  **Explore Indexes**:
   - S&P 500, Nasdaq 100, Dow Jones, Magnificent Seven, ARKK Innovation, Berkshire Hathaway
-  For each index, see:
   - Ticker, company name, weight, last close, 200-DMA, % difference between last close and 200-DMA
   - Sort by weight, last close, 200-DMA, or % difference
-  Click on any stock to view full details
-  Color-coded % difference between last close and 200-DMA for fast visual insights:
   - **Dark Green**: ≥ +10%
   - **Green**: +2% to +10%
   - **Yellow**: -2% to +2%
   - **Red**: -2% to -10%
   - **Dark Red**: ≤ -10%
- Last updated times shown for each stock and index in Eastern Time
- User-friendly 404 and 500 error pages with refresh and navigation options
- Clean, responsive UI with Bootstrap and custom styling

---

## Tech Stack

- **Backend**: Python, Flask, SQLAlchemy
- **Frontend**: HTML, CSS, JS, Jinja2, Bootstrap 5
- **Database**: SQLite (dev), MySQL (prod)
- **APIs**: Polygon.io, SlickCharts

---

## Project Structure

```
├── data_collectors/        # Scripts to collect stock and index data
├── db_populate_scripts/    # Scripts to populate the database
├── models/                 # SQLAlchemy database models
├── static/                 # Static JS and CSS files
├── templates/              # Jinja2 HTML templates
│   └── macros/             # Reusable HTML macros (e.g., popovers)
├── utils/                  # Jinja filters and error handlers
└── app.py                  # Flask application entry point
```

---

## Getting Started

To run the app locally:

1. **Clone the repo**
2. **Set up a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate     # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file** in the root directory:

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