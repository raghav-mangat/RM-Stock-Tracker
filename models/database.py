from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey

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
    last_close: Mapped[float] = mapped_column(nullable=True)
    dma_200: Mapped[float] = mapped_column(nullable=True)
    perc_diff: Mapped[float] = mapped_column(nullable=True)

    index_holdings: Mapped[list["IndexHolding"]] = relationship(back_populates="stock")


class Index(db.Model):
    __tablename__ = "indexes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    url: Mapped[str] = mapped_column(String(100), nullable=False)

    holdings: Mapped[list["IndexHolding"]] = relationship(back_populates="index")


class IndexHolding(db.Model):
    __tablename__ = "index_holdings"

    id: Mapped[int] = mapped_column(primary_key=True)
    index_id: Mapped[int] = mapped_column(ForeignKey("indexes.id"), nullable=False)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), nullable=False)
    weight: Mapped[float] = mapped_column(nullable=True)

    index: Mapped[Index] = relationship(back_populates="holdings")
    stock: Mapped[Stock] = relationship(back_populates="index_holdings")
