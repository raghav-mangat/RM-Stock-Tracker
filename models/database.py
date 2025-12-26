from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, BigInteger, Text, Boolean, ForeignKey, Date, DateTime, UniqueConstraint
from sqlalchemy import Index as DBIndex
from flask_login import UserMixin
from flask import current_app
from enum import Enum
from werkzeug.security import generate_password_hash,check_password_hash
from typing import Optional
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from datetime import datetime, date, UTC
from time import time
from utils.datetime_utils import DATE_FORMAT

# Create a base class for SQLAlchemy
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# --- Enums ---

class SignupSource(str, Enum):
    EMAIL = "email"
    GOOGLE = "google"

class FolderAttribute(str, Enum):
    NAME = "name"
    DAY_CLOSE = "day_close"
    TODAYS_CHANGE_PERC = "todays_change_perc"
    DMA_200 = "dma_200"
    DMA_200_PERC_DIFF = "dma_200_perc_diff"
    DMA_50 = "dma_50"
    DMA_50_PERC_DIFF = "dma_50_perc_diff"
    DMA_30 = "dma_30"
    DMA_30_PERC_DIFF = "dma_30_perc_diff"
    LOW_52W = "low_52w"
    LOW_52W_PERC_DIFF = "low_52w_perc_diff"
    HIGH_52W = "high_52w"
    HIGH_52W_PERC_DIFF = "high_52w_perc_diff"

    @property
    def label(self):
        return {
            FolderAttribute.NAME: "Name",
            FolderAttribute.DAY_CLOSE: "Day Close",
            FolderAttribute.TODAYS_CHANGE_PERC: "Today's % Change",
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
            AlertAttribute.DMA_200_PERC_DIFF: None,
            AlertAttribute.DMA_50_PERC_DIFF: "percent",
            AlertAttribute.DMA_30_PERC_DIFF: "percent",
            AlertAttribute.HIGH_52W_PERC_DIFF: "percent",
            AlertAttribute.LOW_52W_PERC_DIFF: "percent",
        }[self]

class OrderBy(str, Enum):
    ASC = "asc"
    DESC = "desc"

# --- Models ---

class Stock(db.Model):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=True)

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
    volume: Mapped[int] = mapped_column(BigInteger, nullable=True)
    todays_change: Mapped[float] = mapped_column(nullable=True)
    todays_change_perc: Mapped[float] = mapped_column(nullable=True)

    # Daily Moving Averages
    dma_30: Mapped[float] = mapped_column(nullable=True)
    dma_30_perc_diff: Mapped[float] = mapped_column(nullable=True)
    dma_50: Mapped[float] = mapped_column(nullable=True)
    dma_50_perc_diff: Mapped[float] = mapped_column(nullable=True)
    dma_200: Mapped[float] = mapped_column(nullable=True)
    dma_200_perc_diff: Mapped[float] = mapped_column(nullable=True)

    # 52-Week High/Low
    high_52w: Mapped[float] = mapped_column(nullable=True)
    high_52w_perc_diff: Mapped[float] = mapped_column(nullable=True)
    low_52w: Mapped[float] = mapped_column(nullable=True)
    low_52w_perc_diff: Mapped[float] = mapped_column(nullable=True)

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
    week_data: Mapped[list["StockWeek"]] = relationship(
        back_populates="stock", cascade="all, delete-orphan"
    )

    # Adding Index for faster performance
    __table_args__ = (
        DBIndex("ix_stock_ticker", "ticker"),
    )

    # Returns a dict of all the stock attributes and their respective values
    def to_dict(self):
        def serialize(val):
            if isinstance(val, (datetime, date)):
                return val.strftime(DATE_FORMAT)
            return val

        stock_dict =  {
            column.name: serialize(getattr(self, column.name))
            for column in self.__table__.columns
        }

        return stock_dict


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

    # Adding Index for faster performance
    __table_args__ = (
        DBIndex("ix_indexholding_indexid_stockid", "index_id", "stock_id"),
    )


class StockMaster(db.Model):
    __tablename__ = "stocks_master"

    id: Mapped[int] = mapped_column(primary_key=True)

    # All tickers data
    ticker: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=True)
    type: Mapped[str] = mapped_column(String(100), nullable=True)
    primary_exchange: Mapped[str] = mapped_column(String(10), nullable=True)

    # Full Market Snapshot Data
    last_updated: Mapped[DateTime] = db.Column(db.DateTime(timezone=True), nullable=True)
    day_close: Mapped[float] = mapped_column(nullable=True)
    day_open: Mapped[float] = mapped_column(nullable=True)
    day_high: Mapped[float] = mapped_column(nullable=True)
    day_low: Mapped[float] = mapped_column(nullable=True)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=True)
    todays_change: Mapped[float] = mapped_column(nullable=True)
    todays_change_perc: Mapped[float] = mapped_column(nullable=True)

    # Backref from watchlist items
    watchlist_items: Mapped[list["WatchlistItem"]] = relationship("WatchlistItem", back_populates="stock")

    # Adding Index for faster performance
    __table_args__ = (
        DBIndex("ix_stock_master_ticker", "ticker"),
        DBIndex("ix_stock_master_name", "name"),
    )

    # Returns a list of all the attributes in the table except for the excluded ones
    def attribute_list(self):
        exclude = ["id"]

        attributes = [
            column.name
            for column in self.__table__.columns
            if column.name not in exclude
        ]
        return attributes


class StockMinute(db.Model):
    __tablename__ = "stock_minute_data"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[DateTime] = db.Column(db.DateTime(timezone=True), nullable=False)
    close_price: Mapped[float] = mapped_column(nullable=True)
    ema_30: Mapped[float] = mapped_column(nullable=True)
    ema_50: Mapped[float] = mapped_column(nullable=True)
    ema_200: Mapped[float] = mapped_column(nullable=True)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=True)

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
    volume: Mapped[int] = mapped_column(BigInteger, nullable=True)

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
    volume: Mapped[int] = mapped_column(BigInteger, nullable=True)

    stock: Mapped["Stock"] = relationship(back_populates="day_data")

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_stockday_stockid_date"),
        # Adding Index for faster performance
        DBIndex("ix_stockday_stockid_date", "stock_id", "date"),
    )


class StockWeek(db.Model):
    __tablename__ = "stock_week_data"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[DateTime] = db.Column(db.DateTime(timezone=True), nullable=False)
    close_price: Mapped[float] = mapped_column(nullable=True)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=True)

    stock: Mapped["Stock"] = relationship(back_populates="week_data")

    __table_args__ = (
        UniqueConstraint("stock_id", "date", name="uq_stockweek_stockid_date"),
        # Adding Index for faster performance
        DBIndex("ix_stockweek_stockid_date", "stock_id", "date"),
    )


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    google_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)

    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Timestamps
    created_at: Mapped[DateTime] = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    last_login_at: Mapped[DateTime] = db.Column(
        db.DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    last_email_sent_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Session validation
    security_timestamp: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=lambda: int(time())
    )

    # User preferences
    email_alerts_on: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # For analytics
    signup_source: Mapped["SignupSource"] = mapped_column("SignupSource", nullable=False)

    @property
    def password(self):
        raise AttributeError("Password is not readable")

    @password.setter
    def password(self, raw_password):
        self.password_hash = generate_password_hash(
            raw_password,
            method='pbkdf2:sha256',
            salt_length=8
        )

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

    __table_args__ = (
        DBIndex("ix_user_email", "email"),
        DBIndex("ix_user_username", "username")
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
                algorithms=["HS256"]
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

    def __repr__(self) -> str:
        return (f"<User id={self.id} email={self.email} username={self.username} "
                f"first_name={self.first_name} last_name={self.last_name}>")


class WatchlistFolder(db.Model):
    __tablename__ = "wl_folders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    sort_by_attribute: Mapped["FolderAttribute"] = mapped_column("FolderAttribute", nullable=True)
    sort_by_order: Mapped["OrderBy"] = mapped_column("OrderBy", nullable=True)

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
    folder_alerts: Mapped[list["WatchlistFolderAlert"]] = relationship(
        "WatchlistFolderAlert",
        back_populates="folder",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    __table_args__ = (
        # Make folder names unique per user: (user_id, name) must be unique
        UniqueConstraint("user_id", "name", name="uq_wl_folder_user_name"),
        DBIndex("ix_wl_folders_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return (f"<WatchlistFolder id={self.id} user_id={self.user_id} name={self.name} order={self.order} "
                f"sort_by_attribute={self.sort_by_attribute} sort_by_order={self.sort_by_order}>")


class WatchlistItem(db.Model):
    __tablename__ = "wl_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    folder_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("wl_folders.id", ondelete="CASCADE"),
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
    item_alerts: Mapped[list["WatchlistItemAlert"]] = relationship(
        "WatchlistItemAlert",
        back_populates="item",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        # prevent duplicate (same stock in same folder)
        UniqueConstraint("folder_id", "stock_id", name="uq_wl_items_folder_stock"),
        DBIndex("ix_wl_items_folder_id", "folder_id"),
        DBIndex("ix_wl_items_stock_id", "stock_id"),
    )

    def __repr__(self) -> str:
        return f"<WatchlistItem id={self.id} folder_id={self.folder_id} stock_id={self.stock_id}>"


class WatchlistFolderAttribute(db.Model):
    __tablename__ = "wl_folder_attributes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attribute: Mapped["FolderAttribute"] = mapped_column(db.Enum(FolderAttribute), nullable=False)

    # Values for filters
    min_value: Mapped[float] = mapped_column(nullable=True)
    max_value: Mapped[float] = mapped_column(nullable=True)

    folder_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("wl_folders.id", ondelete="CASCADE"),
        nullable=False
    )

    # Relationships
    folder: Mapped["WatchlistFolder"] = relationship("WatchlistFolder", back_populates="folder_attributes")

    __table_args__ = (
        UniqueConstraint("folder_id", "attribute", name="uq_folder_attribute"),
    )

    def __repr__(self) -> str:
        return (f"<WatchlistFolderAttribute id={self.id} folder_id={self.folder_id} attribute={self.attribute} "
                f"min_value={self.min_value} max_value={self.max_value}>")


class WatchlistAlert(db.Model):
    __tablename__ = "wl_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    attribute: Mapped["AlertAttribute"] = mapped_column(db.Enum(AlertAttribute), nullable=False)
    min_value: Mapped[float] = mapped_column(nullable=True)
    max_value: Mapped[float] = mapped_column(nullable=True)

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="watchlist_alerts")

    # Folders for this Alert
    alert_folders: Mapped[list["WatchlistFolderAlert"]] = relationship(
        "WatchlistFolderAlert",
        back_populates="alert",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # Items for this Alert
    alert_items: Mapped[list["WatchlistItemAlert"]] = relationship(
        "WatchlistItemAlert",
        back_populates="alert",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        DBIndex("ix_wl_alerts_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return (f"<WatchlistAlert id={self.id} user_id={self.user_id} attribute={self.attribute} "
                f"min_value={self.min_value} max_value={self.max_value}>")


class WatchlistFolderAlert(db.Model):
    __tablename__ = "wl_folder_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    folder_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("wl_folders.id", ondelete="CASCADE"),
        nullable=False
    )
    alert_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("wl_alerts.id", ondelete="CASCADE"),
        nullable=False
    )

    # Relationships
    folder: Mapped["WatchlistFolder"] = relationship("WatchlistFolder", back_populates="folder_alerts")
    alert: Mapped["WatchlistAlert"] = relationship("WatchlistAlert", back_populates="alert_folders")

    __table_args__ = (
        UniqueConstraint("folder_id", "alert_id", name="uq_folder_alert"),
    )

    def __repr__(self) -> str:
        return f"<WatchlistFolderAlert id={self.id} folder_id={self.folder_id} alert_id={self.alert_id}>"


class WatchlistItemAlert(db.Model):
    __tablename__ = "wl_item_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("wl_items.id", ondelete="CASCADE"),
        nullable=False
    )
    alert_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("wl_alerts.id", ondelete="CASCADE"),
        nullable=False
    )

    # Relationships
    item: Mapped["WatchlistItem"] = relationship("WatchlistItem", back_populates="item_alerts")
    alert: Mapped["WatchlistAlert"] = relationship("WatchlistAlert", back_populates="alert_items")

    __table_args__ = (
        UniqueConstraint("item_id", "alert_id", name="uq_item_alert"),
    )

    def __repr__(self) -> str:
        return f"<WatchlistItemAlert id={self.id} item_id={self.item_id} alert_id={self.alert_id}>"
