"""
Populates the ticker_tape_stocks_cache table with a curated and randomized
set of stocks for the scrolling ticker tape.

Note:
This could be implemented using Redis for faster reads and automatic TTLs.
However, due to Redis command-based pricing (Upstash),
we intentionally use MySQL as a cost-effective cache.
"""

import os
import sys

# Make sure that the project root is in Python's path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models.database import db, Stock, Index, IndexHolding, StockMaster, TickerTapeStockCache
import random
from sqlalchemy import delete
from utils.db_queries.all_stocks import get_trending_stocks

def main():
    app.logger.info(
        f"Starting script",
        extra={"log_type": "scheduled_script", "action": "update_ticker_tape_stocks_cache"}
    )

    try:
        with app.app_context():
            try:
                with db.session.begin():
                    # Clear existing ticker tape entries
                    db.session.execute(delete(TickerTapeStockCache))
                    db.session.flush()

                    ticker_tape_stocks = []

                    # Get all stocks in Nasdaq 100 Index in descending order of weight
                    nasdaq100_stocks = [
                        row.id for row in (
                            db.session.query(StockMaster.id)
                            .join(Stock, Stock.stock_master_id == StockMaster.id)
                            .join(IndexHolding, IndexHolding.stock_id == Stock.id)
                            .join(Index, Index.id == IndexHolding.index_id)
                            .filter(
                                Index.slug == "nasdaq100",
                                StockMaster.name.isnot(None),
                                StockMaster.day_close.isnot(None),
                                StockMaster.todays_change.isnot(None),
                                StockMaster.todays_change_perc.isnot(None),
                                StockMaster.volume.isnot(None),
                            )
                            .order_by(IndexHolding.weight.desc())
                            .all()
                        )
                    ]

                    # Choose the stock list
                    stock_list = nasdaq100_stocks
                    if not stock_list:
                        trending_stocks = get_trending_stocks()
                        stock_list = [row.id for row in trending_stocks]

                    # Get all stocks from StockMaster Table
                    all_stocks = [
                        row.id for row in (
                            db.session.query(StockMaster.id)
                            .filter(
                                StockMaster.name.isnot(None),
                                StockMaster.day_close.isnot(None),
                                StockMaster.todays_change.isnot(None),
                                StockMaster.todays_change_perc.isnot(None),
                                StockMaster.volume.isnot(None),
                            )
                            .all()
                        )
                    ]

                    if stock_list:
                        # Get top 10 stocks
                        ticker_tape_stocks.extend(stock_list[:10])

                        # Add 20 random stocks from remaining stocks
                        remaining = stock_list[10:]
                        if remaining:
                            ticker_tape_stocks.extend(
                                random.sample(remaining, min(20, len(remaining)))
                            )

                    # Add 20 random stocks from all stocks in StockMaster Table
                    remaining_pool = [s for s in all_stocks if s not in stock_list]
                    ticker_tape_stocks.extend(random.sample(remaining_pool, min(20, len(remaining_pool))))

                    if not ticker_tape_stocks:
                        raise RuntimeError("Ticker tape cache would be empty")

                    # Shuffle the selected 50 ticker tape stocks
                    random.shuffle(ticker_tape_stocks)

                    # Store the ticker tape stocks in the database
                    for stock_master_id in ticker_tape_stocks:
                        db.session.add(
                            TickerTapeStockCache(stock_master_id=stock_master_id)
                        )

                    # Changes automatically committed

            except Exception as e:
                print(f"Error: {e}")
                db.session.rollback()
                raise

            app.logger.info(
                f"Completed script",
                extra={"log_type": "scheduled_script", "action": "update_ticker_tape_stocks_cache"}
            )

    except Exception as e:
        app.logger.exception(
            f"Script failed",
            extra={"log_type": "scheduled_script", "action": "update_ticker_tape_stocks_cache", "reason": str(e)}
        )
        sys.exit(1)


if __name__ == "__main__":
    main()