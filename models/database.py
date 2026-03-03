from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import (String, Integer, Float, Numeric, BigInteger, Text, Boolean, ForeignKey,
                        Date, DateTime, UniqueConstraint, TypeDecorator, CheckConstraint)
from sqlalchemy import Index as DBIndex
from sqlalchemy import Enum as SQLEnum
from flask_login import UserMixin
from flask import current_app
from enum import Enum
from werkzeug.security import generate_password_hash,check_password_hash
from typing import Optional
from decimal import Decimal
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from datetime import datetime, date
from time import time
from utils.datetime_utils import get_current_utc, format_dt_et, format_date, convert_to_utc_tz_aware
from utils.constants import MAX_USERNAME_LEN, MAX_NAME_LEN, MAX_FOLDER_NAME_LEN

"""
Notes:

- Initializing unique=True or having UniqueConstraint for attributes automatically 
    adds an index in MySQL.
- Composite indexes must still be explicitly defined using Index().
- Store the timestamps using BigInt.
- Using Numeric data type instead of Float for better accuracy.
- The order of folder attributes and folder/item alerts shown depends on the
    order of things initialized in the respective enums below.
"""

"""
Timezone Policy:

- All datetime fields in the database are stored in UTC.
- MySQL does not store timezone metadata.
- All datetimes retrieved from the database must be treated as UTC.
- Conversion to ET happens only at the presentation layer.
"""

# Create a base class for SQLAlchemy
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# --- Constants ---

NUMERIC_PRECISION = 20
DECIMAL_PRECISION = 4

TICKER_LEN = 16
STOCK_NAME_LEN = 500
STOCK_INFO_LEN = 255

INDEX_NAME_LEN = 500

USER_INFO_LEN = 255

# --- Enums ---

class SignupSource(str, Enum):
    EMAIL = "email"
    GOOGLE = "google"

class FolderAttribute(str, Enum):
    NAME = "name"
    DAY_CLOSE = "day_close"
    TODAYS_CHANGE_PERC = "todays_change_perc"
    VOLUME = "volume"
    DMA_200 = "dma_200"
    DMA_200_PERC_DIFF = "dma_200_perc_diff"
    DMA_50 = "dma_50"
    DMA_50_PERC_DIFF = "dma_50_perc_diff"
    DMA_30 = "dma_30"
    DMA_30_PERC_DIFF = "dma_30_perc_diff"
    HIGH_52W = "high_52w"
    HIGH_52W_PERC_DIFF = "high_52w_perc_diff"
    LOW_52W = "low_52w"
    LOW_52W_PERC_DIFF = "low_52w_perc_diff"

    @property
    def label(self):
        return {
            FolderAttribute.NAME: "Name",
            FolderAttribute.DAY_CLOSE: "Day Close",
            FolderAttribute.TODAYS_CHANGE_PERC: "Today's % Change",
            FolderAttribute.VOLUME: "Volume",
            FolderAttribute.DMA_200: "200-DMA",
            FolderAttribute.DMA_200_PERC_DIFF: "200-DMA % Diff",
            FolderAttribute.DMA_50: "50-DMA",
            FolderAttribute.DMA_50_PERC_DIFF: "50-DMA % Diff",
            FolderAttribute.DMA_30: "30-DMA",
            FolderAttribute.DMA_30_PERC_DIFF: "30-DMA % Diff",
            FolderAttribute.HIGH_52W: "52w-High",
            FolderAttribute.HIGH_52W_PERC_DIFF: "52w-High % Diff",
            FolderAttribute.LOW_52W: "52w-Low",
            FolderAttribute.LOW_52W_PERC_DIFF: "52w-Low % Diff",
        }[self]

    @property
    def type(self):
        return {
            FolderAttribute.NAME: None,
            FolderAttribute.DAY_CLOSE: "currency",
            FolderAttribute.TODAYS_CHANGE_PERC: None,
            FolderAttribute.VOLUME: None,
            FolderAttribute.DMA_200: "currency",
            FolderAttribute.DMA_200_PERC_DIFF: None,
            FolderAttribute.DMA_50: "currency",
            FolderAttribute.DMA_50_PERC_DIFF: "percent",
            FolderAttribute.DMA_30: "currency",
            FolderAttribute.DMA_30_PERC_DIFF: "percent",
            FolderAttribute.HIGH_52W: "currency",
            FolderAttribute.HIGH_52W_PERC_DIFF: "percent",
            FolderAttribute.LOW_52W: "currency",
            FolderAttribute.LOW_52W_PERC_DIFF: "percent",
        }[self]

class AlertAttribute(str, Enum):
    DAY_CLOSE = "day_close"
    TODAYS_CHANGE_PERC = "todays_change_perc"
    VOLUME = "volume"
    DMA_200_PERC_DIFF = "dma_200_perc_diff"
    DMA_50_PERC_DIFF = "dma_50_perc_diff"
    DMA_30_PERC_DIFF = "dma_30_perc_diff"
    HIGH_52W_PERC_DIFF = "high_52w_perc_diff"
    LOW_52W_PERC_DIFF = "low_52w_perc_diff"

    @property
    def label(self):
        return {
            AlertAttribute.DAY_CLOSE: "Day Close",
            AlertAttribute.TODAYS_CHANGE_PERC: "Today's Percentage Change",
            AlertAttribute.VOLUME: "Volume",
            AlertAttribute.DMA_200_PERC_DIFF: "200-DMA Percentage Difference",
            AlertAttribute.DMA_50_PERC_DIFF: "50-DMA Percentage Difference",
            AlertAttribute.DMA_30_PERC_DIFF: "30-DMA Percentage Difference",
            AlertAttribute.HIGH_52W_PERC_DIFF: "52w-High Percentage Difference",
            AlertAttribute.LOW_52W_PERC_DIFF: "52w-Low Percentage Difference",
        }[self]

    @property
    def type(self):
        return {
            AlertAttribute.DAY_CLOSE: "currency",
            AlertAttribute.TODAYS_CHANGE_PERC: None,
            AlertAttribute.VOLUME: None,
            AlertAttribute.DMA_200_PERC_DIFF: None,
            AlertAttribute.DMA_50_PERC_DIFF: "percent",
            AlertAttribute.DMA_30_PERC_DIFF: "percent",
            AlertAttribute.HIGH_52W_PERC_DIFF: "percent",
            AlertAttribute.LOW_52W_PERC_DIFF: "percent",
        }[self]

class OrderBy(str, Enum):
    ASC = "asc"
    DESC = "desc"

# --- Custom SQLAlchemy Data Types ---

class UTCDateTime(TypeDecorator):
    impl = DateTime
    cache_ok = True

    def process_result_value(self, value, dialect):
        if value is not None:
            return convert_to_utc_tz_aware(value)
        return value

# --- Custom SQLAlchemy Mixins ---

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=get_current_utc
    )

    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=get_current_utc,
        onupdate=get_current_utc
    )

# --- Models ---

class StockMaster(TimestampMixin, db.Model):
    __tablename__ = "stocks_master"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # All tickers data
    ticker: Mapped[str] = mapped_column(String(TICKER_LEN), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(STOCK_NAME_LEN), index=True, nullable=False)
    primary_exchange: Mapped[str] = mapped_column(String(STOCK_INFO_LEN), nullable=False)

    stock_type_id: Mapped[int] = mapped_column(
        ForeignKey("stock_type_meta.id"),
        nullable=False,
        index=True
    )

    stock_type: Mapped["StockTypeMeta"] = relationship(
        "StockTypeMeta",
        lazy="joined"
    )

    # Full Market Snapshot Data
    last_updated: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    day_close: Mapped[Decimal] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=False)
    day_open: Mapped[Decimal] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=False)
    day_high: Mapped[Decimal] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=False)
    day_low: Mapped[Decimal] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    vwap: Mapped[Decimal] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=False)
    todays_change: Mapped[Decimal] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=False)
    todays_change_perc: Mapped[Decimal] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=False)
    prev_o: Mapped[Decimal] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=False)
    prev_h: Mapped[Decimal] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=False)
    prev_l: Mapped[Decimal] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=False)
    prev_c: Mapped[Decimal] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=False)
    prev_v: Mapped[int] = mapped_column(BigInteger, nullable=False)
    prev_vwap: Mapped[Decimal] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=False)

    # Flag to check if the data is valid
    is_data_valid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )

    # Stock Relationship
    stock: Mapped[Optional["Stock"]] = relationship(
        "Stock",
        back_populates="stock_master",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # Backref from watchlist items
    watchlist_items: Mapped[list["WatchlistItem"]] = relationship(
        "WatchlistItem",
        back_populates="stock",
        passive_deletes=True
    )

    # Adding Index for faster performance
    __table_args__ = (
        DBIndex("ix_stock_master_ticker_name", "ticker", "name"),
    )

    # Returns a list of all the attributes in the table except for the excluded ones
    def attribute_list(self):
        exclude = ["id", "created_at", "updated_at"]

        attributes = [
            column.name
            for column in self.__table__.columns
            if column.name not in exclude
        ]
        return attributes

    # Returns a dict of all the stock master attributes and their respective values
    def to_dict(self):
        def serialize(val):
            if isinstance(val, datetime):
                return format_dt_et(val)
            if isinstance(val, date):
                return format_date(val)
            return val

        stock_master_dict = {
            column.name: serialize(getattr(self, column.name))
            for column in self.__table__.columns
        }

        return stock_master_dict

    def __repr__(self) -> str:
        return (f"<StockMaster id={self.id} ticker={self.ticker} name={self.name} "
                f"day_close={self.day_close}>")


class Stock(TimestampMixin, db.Model):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Company Info
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    homepage_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    list_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(STOCK_INFO_LEN), nullable=True)
    total_employees: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    market_cap: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)

    # Branding
    icon_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Daily Moving Averages
    dma_30: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)
    dma_30_perc_diff: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)
    dma_50: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)
    dma_50_perc_diff: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)
    dma_200: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)
    dma_200_perc_diff: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)

    # 52-Week High/Low
    high_52w: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)
    high_52w_perc_diff: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)
    low_52w: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)
    low_52w_perc_diff: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)

    # Related Companies (comma-separated string)
    related_companies: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Stock Master Relationship
    stock_master_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("stocks_master.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    stock_master: Mapped["StockMaster"] = relationship(
        "StockMaster",
        back_populates="stock",
        uselist=False
    )

    # Index Relationship
    index_holdings: Mapped[list["IndexHolding"]] = relationship(
        back_populates="stock",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # Chart Data Relationships
    minute_data: Mapped[list["StockMinute"]] = relationship(
        back_populates="stock", cascade="all, delete-orphan", passive_deletes=True
    )
    hour_data: Mapped[list["StockHour"]] = relationship(
        back_populates="stock", cascade="all, delete-orphan", passive_deletes=True
    )
    day_data: Mapped[list["StockDay"]] = relationship(
        back_populates="stock", cascade="all, delete-orphan", passive_deletes=True
    )
    week_data: Mapped[list["StockWeek"]] = relationship(
        back_populates="stock", cascade="all, delete-orphan", passive_deletes=True
    )

    # Returns a dict of all the stock attributes and their respective values
    def to_dict(self):
        def serialize(val):
            if isinstance(val, datetime):
                return format_dt_et(val)
            if isinstance(val, date):
                return format_date(val)
            return val

        stock_dict = dict()
        if self.stock_master:
            stock_dict.update(self.stock_master.to_dict())

        stock_dict.update({
            column.name: serialize(getattr(self, column.name))
            for column in self.__table__.columns
        })

        return stock_dict

    def __repr__(self) -> str:
        return f"<Stock id={self.id} stock_master_id={self.stock_master_id}>"


class StockTypeMeta(TimestampMixin, db.Model):
    __tablename__ = "stock_type_meta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Polygon / Massive API canonical identifier
    code: Mapped[str] = mapped_column(
        String(STOCK_INFO_LEN),
        unique=True,
        nullable=False,
    )

    # Human-readable label
    description: Mapped[str] = mapped_column(
        String(STOCK_INFO_LEN),
        nullable=False
    )

    # Active flag in case Polygon / Massive API deprecates types
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<StockTypeMeta id={self.id } code={self.code} description={self.description}>"


class StockMinute(db.Model):
    __tablename__ = "stock_minute_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    date: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    close_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)
    ema_30: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)
    ema_50: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)
    ema_200: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="CASCADE"),
        nullable=False
    )
    stock: Mapped["Stock"] = relationship(back_populates="minute_data")

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_stockminute_stockid_date"),
    )


class StockHour(db.Model):
    __tablename__ = "stock_hour_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    date: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    close_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)
    ema_30: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)
    ema_50: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)
    ema_200: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="CASCADE"),
        nullable=False
    )
    stock: Mapped["Stock"] = relationship(back_populates="hour_data")

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_stockhour_stockid_date"),
    )


class StockDay(db.Model):
    __tablename__ = "stock_day_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    date: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    close_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)
    ema_30: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)
    ema_50: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)
    ema_200: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="CASCADE"),
        nullable=False
    )
    stock: Mapped["Stock"] = relationship(back_populates="day_data")

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_stockday_stockid_date"),
    )


class StockWeek(db.Model):
    __tablename__ = "stock_week_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    date: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    close_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="CASCADE"),
        nullable=False
    )
    stock: Mapped["Stock"] = relationship(back_populates="week_data")

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_stockweek_stockid_date"),
    )


class Index(TimestampMixin, db.Model):
    __tablename__ = "indices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    slug: Mapped[str] = mapped_column(String(INDEX_NAME_LEN), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(INDEX_NAME_LEN), unique=True, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    holdings: Mapped[list["IndexHolding"]] = relationship(
        back_populates="index",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"<Index id={self.id } slug={self.slug} name={self.name}>"


class IndexHolding(TimestampMixin, db.Model):
    __tablename__ = "index_holdings"

    # Composite Primary Key (index_id, stock_id)
    index_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("indices.id", ondelete="CASCADE"),
        primary_key=True
    )
    stock_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("stocks.id", ondelete="CASCADE"),
        primary_key=True
    )
    weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)

    index: Mapped["Index"] = relationship(back_populates="holdings")
    stock: Mapped["Stock"] = relationship(back_populates="index_holdings")


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    email: Mapped[str] = mapped_column(String(USER_INFO_LEN), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(MAX_USERNAME_LEN), unique=True, nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(MAX_NAME_LEN), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(MAX_NAME_LEN), nullable=True)

    password_hash: Mapped[Optional[str]] = mapped_column(String(USER_INFO_LEN), nullable=True)
    google_id: Mapped[Optional[str]] = mapped_column(String(USER_INFO_LEN), unique=True, nullable=True)

    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Timestamps
    last_login_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=get_current_utc
    )

    # Roles
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Session validation
    security_timestamp: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=lambda: int(time())
    )

    # User preferences
    email_alerts_on: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # For analytics
    signup_source: Mapped["SignupSource"] = mapped_column(
        SQLEnum(SignupSource, name="signup_source_enum"),
        nullable=False
    )

    @property
    def password(self):
        raise AttributeError("Password is not readable")

    @password.setter
    def password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def remove_password(self):
        self.password_hash = None

    def verify_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    # One user -> many watchlist folders
    watchlist_folders: Mapped[list["WatchlistFolder"]] = relationship(
        "WatchlistFolder",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # One user -> many watchlist alerts
    watchlist_alerts: Mapped[list["WatchlistAlert"]] = relationship(
        "WatchlistAlert",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def get_token(self, token_type, expires_in=86400):
        """
        Create a JWT. Default expiry 86400 seconds (24 hours)
        """
        now = int(time())
        payload = {
            "sub": str(self.id),
            "type": token_type,
            "stamp": self.security_timestamp,
            "iat": now,
            "exp": now + int(expires_in),
        }
        return jwt.encode(
            payload=payload,
            key=current_app.config["SECRET_KEY"],
            algorithm="HS256"
        )

    @staticmethod
    def verify_token(token, token_type):
        """
        Verify token and check if it is of the expected type.
        Returns user instance or None.
        """
        result = None
        try:
            payload = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"],
                options={"require": ["exp", "iat", "sub"]}
            )
        except ExpiredSignatureError:
            # Token expired
            return result
        except InvalidTokenError:
            # Invalid token
            return result

        if payload.get("type") != token_type:
            # Invalid token type
            return result

        user_id = payload.get("sub")
        if not user_id:
            # Invalid user
            return result

        user = db.session.execute(db.select(User).where(User.id == int(user_id))).scalar()
        if not user:
            return result

        if payload.get("stamp") != user.security_timestamp:
            return result

        return user

    __table_args__ = (
        # Enforce password_hash OR google_id
        CheckConstraint(
            "(password_hash IS NOT NULL OR google_id IS NOT NULL)",
            name="ck_user_password_hash_or_google_id",
        ),
    )

    def __repr__(self) -> str:
        return (f"<User id={self.id} email={self.email} username={self.username} "
                f"first_name={self.first_name} last_name={self.last_name}>")


class WatchlistFolder(TimestampMixin, db.Model):
    __tablename__ = "watchlist_folders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(MAX_FOLDER_NAME_LEN), nullable=False)
    folder_order: Mapped[int] = mapped_column(Integer, nullable=False)
    sort_by_attribute: Mapped[Optional["FolderAttribute"]] = mapped_column(
        SQLEnum(FolderAttribute, name="folder_attribute_enum"),
        nullable=True
    )
    sort_by_order: Mapped[Optional["OrderBy"]] = mapped_column(
        SQLEnum(OrderBy, name="order_by_enum"),
        nullable=True
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationship back to user
    user: Mapped["User"] = relationship("User", back_populates="watchlist_folders")

    # Items inside this folder
    items: Mapped[list["WatchlistItem"]] = relationship(
        "WatchlistItem",
        back_populates="folder",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # Attributes for this folder
    folder_attributes: Mapped[list["WatchlistFolderAttribute"]] = relationship(
        "WatchlistFolderAttribute",
        back_populates="folder",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # Alerts for this folder
    alerts: Mapped[list["WatchlistAlert"]] = relationship(
        "WatchlistAlert",
        back_populates="folder",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        # Make folder names unique per user: (user_id, name) must be unique
        UniqueConstraint("user_id", "name", name="uq_watchlist_folder_name_user"),
        # Make folder order unique per user: (user_id, folder_order) must be unique
        UniqueConstraint("user_id", "folder_order", name="uq_watchlist_folder_order_user"),

        # folder_order >= 1
        CheckConstraint(
            "folder_order >= 1",
            name="ck_watchlist_folder_order_ge_1",
        ),

        DBIndex("ix_watchlist_folders_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return (f"<WatchlistFolder id={self.id} user_id={self.user_id} folder_order={self.folder_order} "
                f"name={self.name} sort_by_attribute={self.sort_by_attribute} "
                f"sort_by_order={self.sort_by_order}>")


class WatchlistItem(TimestampMixin, db.Model):
    __tablename__ = "watchlist_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    item_order: Mapped[int] = mapped_column(Integer, nullable=False)

    folder_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("watchlist_folders.id", ondelete="CASCADE"),
        nullable=False,
    )
    stock_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("stocks_master.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    folder: Mapped["WatchlistFolder"] = relationship("WatchlistFolder", back_populates="items")
    stock: Mapped["StockMaster"] = relationship("StockMaster", back_populates="watchlist_items")

    # Alerts for this item
    alerts: Mapped[list["WatchlistAlert"]] = relationship(
        "WatchlistAlert",
        back_populates="item",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        # Prevent duplicate (same stock in same folder)
        UniqueConstraint("folder_id", "stock_id", name="uq_watchlist_item_folder_stock"),
        # Make item order unique per folder: (folder_id, item_order) must be unique
        UniqueConstraint("folder_id", "item_order", name="uq_watchlist_item_order_folder"),

        # item_order >= 1
        CheckConstraint(
            "item_order >= 1",
            name="ck_watchlist_item_order_ge_1",
        ),

        DBIndex("ix_watchlist_items_folder_id", "folder_id"),
        DBIndex("ix_watchlist_items_stock_id", "stock_id"),
    )

    def __repr__(self) -> str:
        return (f"<WatchlistItem id={self.id} folder_id={self.folder_id} stock_id={self.stock_id} "
                f"item_order={self.item_order}>")


class WatchlistFolderAttribute(TimestampMixin, db.Model):
    __tablename__ = "watchlist_folder_attributes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    attribute: Mapped["FolderAttribute"] = mapped_column(
        SQLEnum(FolderAttribute, name="folder_attribute_enum"),
        nullable=False
    )

    # Values for filters
    use_abs: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    min_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)
    max_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True)

    folder_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("watchlist_folders.id", ondelete="CASCADE"),
        nullable=False
    )

    # Relationships
    folder: Mapped["WatchlistFolder"] = relationship("WatchlistFolder", back_populates="folder_attributes")

    __table_args__ = (
        # Cannot have duplicate attributes in a folder
        UniqueConstraint("folder_id", "attribute", name="uq_watchlist_folder_attribute"),

        # min_value <= max_value
        CheckConstraint(
            "(min_value IS NULL OR max_value IS NULL OR min_value <= max_value)",
            name="ck_watchlist_folder_attribute_min_le_max",
        ),
    )

    def __repr__(self) -> str:
        return (f"<WatchlistFolderAttribute id={self.id} folder_id={self.folder_id} attribute={self.attribute} "
                f"min_value={self.min_value} max_value={self.max_value} use_abs={self.use_abs}>")


class WatchlistAlert(TimestampMixin, db.Model):
    __tablename__ = "watchlist_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    attribute: Mapped["AlertAttribute"] = mapped_column(
        SQLEnum(AlertAttribute, name="alert_attribute_enum"),
        nullable=False
    )
    use_abs: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    min_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True
    )
    max_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(NUMERIC_PRECISION, DECIMAL_PRECISION), nullable=True
    )

    # Ownership
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # EXACTLY ONE of these must be non-null
    folder_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("watchlist_folders.id", ondelete="CASCADE"),
        nullable=True,
    )
    item_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("watchlist_items.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="watchlist_alerts")
    folder: Mapped[Optional["WatchlistFolder"]] = relationship(
        "WatchlistFolder", back_populates="alerts"
    )
    item: Mapped[Optional["WatchlistItem"]] = relationship(
        "WatchlistItem", back_populates="alerts"
    )

    __table_args__ = (
        # Each folder/item can have only one alert for a given attribute
        UniqueConstraint("folder_id", "attribute", name="uq_watchlist_alert_folder_attribute"),
        UniqueConstraint("item_id", "attribute", name="uq_watchlist_alert_item_attribute"),

        # Enforce folder XOR item
        CheckConstraint(
            "(folder_id IS NOT NULL AND item_id IS NULL) OR "
            "(folder_id IS NULL AND item_id IS NOT NULL)",
            name="ck_watchlist_alert_folder_xor_item",
        ),
        # min_value <= max_value
        CheckConstraint(
            "(min_value IS NULL OR max_value IS NULL OR min_value <= max_value)",
            name="ck_watchlist_alert_min_le_max",
        ),

        DBIndex("ix_watchlist_alerts_user_id", "user_id"),
        DBIndex("ix_watchlist_alerts_folder_id", "folder_id"),
        DBIndex("ix_watchlist_alerts_item_id", "item_id"),
    )

    def __repr__(self) -> str:
        target = f"folder_id={self.folder_id}" if self.folder_id else f"item_id={self.item_id}"
        return (
            f"<WatchlistAlert id={self.id} user_id={self.user_id} "
            f"attribute={self.attribute} {target}>"
        )


class DailyAppStatus(TimestampMixin, db.Model):
    __tablename__ = "daily_app_status"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Identity
    date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)

    # Core Usage Metrics
    emails_enqueued: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    massive_api_calls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    google_oauth_callbacks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    emails_sent_success: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    emails_sent_failure: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    email_send_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    email_send_permanent_failure: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # App Health Metrics
    request_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    static_request_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    responses_5xx: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    slow_requests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    uncaught_exceptions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    avg_latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_static_latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    redis_flush_success: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    redis_flush_failure: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Growth & Engagement (Total)
    total_users: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active_users: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    google_users: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    email_users: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    verified_users: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    password_users: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    google_id_users: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    password_and_google_id_users: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    email_alerts_users: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Growth & Engagement (24 hours)
    logged_in_users_24h: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_users_24h: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deleted_users_24h: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Watchlist Status
    num_watchlist_folders: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    num_watchlist_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    num_watchlist_alerts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    num_stock_watchlist_items: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    num_stock_master: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    num_stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Market Status
    market_open: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Upstash Redis Data
    redis_data_collected_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=get_current_utc
    )
    redis_total_commands: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    redis_total_reads: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    redis_total_writes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    redis_used_memory_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    redis_max_memory_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    redis_keys_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    redis_expired_keys: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    redis_evicted_keys: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # MySQL Database Data
    mysql_data_collected_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        default=get_current_utc
    )
    mysql_total_db_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    mysql_data_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    mysql_index_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    mysql_table_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return (f"<DailyAppStatus id={self.id} date={self.date} request_count={self.request_count} "
                f"avg_latency_ms={self.avg_latency_ms} total_users={self.total_users}>")


class TickerTapeStockCache(TimestampMixin, db.Model):
    __tablename__ = "ticker_tape_stocks_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # FK - StockMaster
    stock_master_id: Mapped[int] = mapped_column(
        ForeignKey("stocks_master.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    # Relationship
    stock_master: Mapped["StockMaster"] = relationship(
        "StockMaster",
        lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<TickerTapeStockCache id={self.id} stock_master_id={self.stock_master_id}>"
