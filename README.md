# RM Stock Tracker

RM Stock Tracker is a production-grade web application for exploring
U.S. stocks, analyzing market data, and managing personalized watchlist
with alerts. The platform is designed with a strong focus on
performance, usability, scalability, and clean backend architecture.

> **Live Site:**
> [www.rmstocktracker.com](https://www.rmstocktracker.com)

---

## Overview

RM Stock Tracker provides a structured and efficient way to interact
with the U.S. stock market. It combines near real-time data updates,
interactive analytics, and a user-centric system for tracking stocks.

**The application emphasizes**:

- Performance-first backend design
- Clean and modular architecture
- Scalable data pipelines
- User-focused experience

---

## Core Features

### Market Exploration

- Search stocks by ticker symbol or company name
- Intelligent stock search bar showing relevant suggestions as users type,
  supporting keyboard navigation
- View top market movers including gainers, losers, and most traded
  stocks
- Trending stocks dashboard
- Live ticker tape showing a rotating set of stocks that refreshes
  throughout the day
- Explore major indices including S&P 500, Nasdaq 100, and Dow Jones, with access to
  constituents, key metrics, and sortable and filterable tables

### Stock Details and Charts

- Interactive charts with multiple timeframes
- AJAX-based updates without page reloads
- Technical indicators including 30, 50, and 200 day exponential
  moving averages (EMA)
- Today's performance, 52-week high/low, volume, 200-DMA, related companies,
  market capitalization and more

### Watchlist System

- Folder-based organization for tracking stocks
- Customizable data tables per folder
- Sorting and filtering across multiple attributes
- Support for the same stock in multiple folders

### Alerts System

- Condition-based alerts using minimum and maximum thresholds
- Support for absolute value based conditions for flexible comparisons
- Folder-level and stock-level alerts
- Dedicated alerts page with a breakdown of alert status by folder, including
  triggered stocks and stock-specific conditions
- Daily email summaries after market close

### User System

- Email and password authentication
- Google Sign-In using OAuth
- Profile and account settings management
- Secure session handling

### User Experience

- Light and dark mode support with seamless theme switching
- Clear and color-coded toast notifications for user actions and system feedback
- Fully responsive design optimized for both desktop and mobile devices
- Consistent and smooth experience across different screen sizes
- Optimized loading states and smooth transitions for better perceived performance

### Market Data Transparency

- Live market status displayed across the platform (open, closed, extended-hours)
- Data freshness indicators showing last updated timestamps in Eastern Time (ET)

---

## Performance and Architecture

### Precomputed Data Strategy

Heavy computations are handled through scheduled scripts rather than
during request handling.

### Dataset Versioning

The application uses a dataset versioning system to ensure:

- Atomic data updates
- No partial data exposure
- Safe rollback capability

### Optimized Search

- Dedicated search table
- Prefix-based queries
- Indexed columns for fast lookups
- No joins in search queries

### Redis Integration

Redis (Upstash) is used for:

- Email queueing
- Rate limiting
- Metrics tracking

### SEO Optimization

- Structured metadata and semantic HTML for better search engine visibility
- XML sitemap generation for improved indexing
- Integrated with Google Search Console for monitoring indexing, performance, and search visibility

### AJAX-Based Frontend

Dynamic updates across charts, dashboards, and watchlist improve
performance and user experience.

---

## Data Pipeline

### Market Data

- Powered by Massive.com API

### Index Holdings

- Sourced from Wikipedia
- Stored in JSON for caching and efficiency

### Update Strategy

- Data updates every 30 minutes during market hours
- Additional updates at market open and close
- Final update in the evening

---

## Admin and Monitoring

- Admin dashboard for system insights
- Metrics tracking for users, watchlist, and system activity
- Custom logging system for debugging and monitoring

---

## Tech Stack

- **Backend**: Python, Flask, SQLAlchemy 2.0, MySQL
- **Frontend**: HTML, CSS, JS, Jinja2, Bootstrap 5, Chart.js
- **Infrastructure**: PythonAnywhere, Redis (Upstash), Google Cloud (OAuth for authentication),
  custom domain and DNS configuration (Namecheap), custom email domain for transactional emails

---

## Project Structure

The project follows a modular architecture with separate components for
authentication, watchlist management, admin tools, data collection, and
scheduled jobs.

### Key directories:

- **auth**: authentication and user management
- **watchlist**: watchlist and alerts system
- **admin**: admin dashboard and metrics
- **data_collectors**: external data fetching
- **scheduled_scripts**: background jobs and pipelines
- **utils**: shared utilities and database queries
- **templates and static**: frontend components

---

## Disclaimer

Market data is provided for informational purposes only and may be
delayed. This application does not provide financial or investment
advice.

---

## License

This project is source-available and intended for viewing and
educational purposes only. See the [LICENSE](./LICENSE.md) for full
terms.

---

## Release Notes

See [Release Notes](./RELEASE_NOTES.md) for version history and
changelog.
