from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Text, ForeignKey, Date, DateTime, UniqueConstraint
from sqlalchemy import Index as DBIndex

# Create a base class for SQLAlchemy
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# --- Models ---

class Stock(db.Model):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=True)

    # Company Info
    description: Mapped[str] = mapped_column(Text, nullable=True)
    homepage_url: Mapped[str] = mapped_column(Text, nullable=True)
    list_date: Mapped[Date] = mapped_column(db.Date, nullable=True)
    industry: Mapped[str] = mapped_column(String(100), nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=True)
    total_employees: Mapped[int] = mapped_column(nullable=True)
    market_cap: Mapped[float] = mapped_column(nullable=True)

    # Branding
    icon_url: Mapped[str] = mapped_column(Text, nullable=True)

    # Snapshot Data
    last_updated: Mapped[DateTime] = db.Column(db.DateTime(timezone=True), nullable=True)
    day_close: Mapped[float] = mapped_column(nullable=True)
    day_open: Mapped[float] = mapped_column(nullable=True)
    day_high: Mapped[float] = mapped_column(nullable=True)
    day_low: Mapped[float] = mapped_column(nullable=True)
    volume: Mapped[int] = mapped_column(nullable=True)
    todays_change: Mapped[float] = mapped_column(nullable=True)
    todays_change_perc: Mapped[float] = mapped_column(nullable=True)

    # Moving Averages
    dma_30: Mapped[float] = mapped_column(nullable=True)
    dma_50: Mapped[float] = mapped_column(nullable=True)
    dma_200: Mapped[float] = mapped_column(nullable=True)
    dma_200_perc_diff: Mapped[float] = mapped_column(nullable=True)

    # 52 Week High/Low
    high_52w: Mapped[float] = mapped_column(nullable=True)
    low_52w: Mapped[float] = mapped_column(nullable=True)

    # Related Companies (comma-separated string)
    related_companies: Mapped[str] = mapped_column(Text, nullable=True)

    # Index Relationship
    index_holdings: Mapped[list["IndexHolding"]] = relationship(back_populates="stock")

    # Chart Data Relationships
    minute_data: Mapped[list["StockMinute"]] = relationship(
        back_populates="stock", cascade="all, delete-orphan"
    )
    hour_data: Mapped[list["StockHour"]] = relationship(
        back_populates="stock", cascade="all, delete-orphan"
    )
    day_data: Mapped[list["StockDay"]] = relationship(
        back_populates="stock", cascade="all, delete-orphan"
    )

    # Adding Index for faster performance
    __table_args__ = (
        DBIndex("ix_stock_ticker", "ticker"),
    )

class Index(db.Model):
    __tablename__ = "indices"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    url: Mapped[str] = mapped_column(String(255), nullable=True)
    last_updated: Mapped[DateTime] = db.Column(db.DateTime(timezone=True), nullable=True)

    holdings: Mapped[list["IndexHolding"]] = relationship(back_populates="index")


class IndexHolding(db.Model):
    __tablename__ = "index_holdings"

    id: Mapped[int] = mapped_column(primary_key=True)
    index_id: Mapped[int] = mapped_column(ForeignKey("indices.id"), nullable=False)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), nullable=False)
    weight: Mapped[float] = mapped_column(nullable=True)

    index: Mapped[Index] = relationship(back_populates="holdings")
    stock: Mapped[Stock] = relationship(back_populates="index_holdings")


class StockMaster(db.Model):
    __tablename__ = "stocks_master"

    id: Mapped[int] = mapped_column(primary_key=True)

    # All tickers data
    ticker: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=True)
    type: Mapped[str] = mapped_column(String(100), nullable=True)
    primary_exchange: Mapped[str] = mapped_column(String(10), nullable=True)

    # Full Market Snapshot Data
    last_updated: Mapped[DateTime] = db.Column(db.DateTime(timezone=True), nullable=True)
    day_close: Mapped[float] = mapped_column(nullable=True)
    day_open: Mapped[float] = mapped_column(nullable=True)
    day_high: Mapped[float] = mapped_column(nullable=True)
    day_low: Mapped[float] = mapped_column(nullable=True)
    volume: Mapped[int] = mapped_column(nullable=True)
    todays_change: Mapped[float] = mapped_column(nullable=True)
    todays_change_perc: Mapped[float] = mapped_column(nullable=True)

    # Adding Index for faster performance
    __table_args__ = (
        DBIndex("ix_stock_master_ticker", "ticker"),
        DBIndex("ix_stock_master_name", "name"),
    )


class StockMinute(db.Model):
    __tablename__ = "stock_minute_data"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[DateTime] = db.Column(db.DateTime(timezone=True), nullable=False)
    close_price: Mapped[float] = mapped_column(nullable=True)
    ema_30: Mapped[float] = mapped_column(nullable=True)
    ema_50: Mapped[float] = mapped_column(nullable=True)
    ema_200: Mapped[float] = mapped_column(nullable=True)
    volume: Mapped[int] = mapped_column(nullable=True)

    stock: Mapped["Stock"] = relationship(back_populates="minute_data")

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_stockminute_stockid_date"),
        # Adding Index for faster performance
        DBIndex("ix_stockminute_stockid_date", "stock_id", "date"),
    )


class StockHour(db.Model):
    __tablename__ = "stock_hour_data"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[DateTime] = db.Column(db.DateTime(timezone=True), nullable=False)
    close_price: Mapped[float] = mapped_column(nullable=True)
    ema_30: Mapped[float] = mapped_column(nullable=True)
    ema_50: Mapped[float] = mapped_column(nullable=True)
    ema_200: Mapped[float] = mapped_column(nullable=True)
    volume: Mapped[int] = mapped_column(nullable=True)

    stock: Mapped["Stock"] = relationship(back_populates="hour_data")

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_stockhour_stockid_date"),
        # Adding Index for faster performance
        DBIndex("ix_stockhour_stockid_date", "stock_id", "date"),
    )


class StockDay(db.Model):
    __tablename__ = "stock_day_data"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[DateTime] = db.Column(db.DateTime(timezone=True), nullable=False)
    close_price: Mapped[float] = mapped_column(nullable=True)
    ema_30: Mapped[float] = mapped_column(nullable=True)
    ema_50: Mapped[float] = mapped_column(nullable=True)
    ema_200: Mapped[float] = mapped_column(nullable=True)
    volume: Mapped[int] = mapped_column(nullable=True)

    stock: Mapped["Stock"] = relationship(back_populates="day_data")

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_stockday_stockid_date"),
        # Adding Index for faster performance
        DBIndex("ix_stockday_stockid_date", "stock_id", "date"),
    )
