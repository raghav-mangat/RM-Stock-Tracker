from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Text, ForeignKey, Date

# Create a base class for SQLAlchemy
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# --- Models ---

class Stock(db.Model):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

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
    last_updated = db.Column(db.DateTime(timezone=True), nullable=True)
    last_close: Mapped[float] = mapped_column(nullable=True)
    last_open: Mapped[float] = mapped_column(nullable=True)
    day_high: Mapped[float] = mapped_column(nullable=True)
    day_low: Mapped[float] = mapped_column(nullable=True)
    volume: Mapped[float] = mapped_column(nullable=True)
    todays_change: Mapped[float] = mapped_column(nullable=True)
    todays_change_perc: Mapped[float] = mapped_column(nullable=True)

    # Moving Averages
    dma_50: Mapped[float] = mapped_column(nullable=True)
    dma_200: Mapped[float] = mapped_column(nullable=True)
    dma_200_perc_diff: Mapped[float] = mapped_column(nullable=True)

    # 52 Week High/Low
    high_52w: Mapped[float] = mapped_column(nullable=True)
    low_52w: Mapped[float] = mapped_column(nullable=True)

    # Related Companies (comma-separated string)
    related_companies: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationships
    index_holdings: Mapped[list["IndexHolding"]] = relationship(back_populates="stock")


class Index(db.Model):
    __tablename__ = "indexes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    last_updated = db.Column(db.DateTime(timezone=True), nullable=True)

    holdings: Mapped[list["IndexHolding"]] = relationship(back_populates="index")


class IndexHolding(db.Model):
    __tablename__ = "index_holdings"

    id: Mapped[int] = mapped_column(primary_key=True)
    index_id: Mapped[int] = mapped_column(ForeignKey("indexes.id"), nullable=False)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), nullable=False)
    weight: Mapped[float] = mapped_column(nullable=True)

    index: Mapped[Index] = relationship(back_populates="holdings")
    stock: Mapped[Stock] = relationship(back_populates="index_holdings")


class StockMaster(db.Model):
    __tablename__ = "stocks_master"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=True)
    primary_exchange: Mapped[str] = mapped_column(String(10), nullable=False)
