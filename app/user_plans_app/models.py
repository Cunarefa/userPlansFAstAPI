from datetime import date
from decimal import Decimal
from typing import List

from sqlalchemy import ForeignKey, String, Numeric, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    login: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    registration_date: Mapped[date]

    credits: Mapped[list["Credit"]] = relationship("Credit", back_populates="user")


class Credit(Base):
    __tablename__ = "credits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    issuance_date: Mapped[date] = mapped_column(nullable=False)
    return_date: Mapped[date] = mapped_column(nullable=False)
    actual_return_date: Mapped[date | None] = mapped_column(nullable=True)
    body: Mapped[int] = mapped_column(nullable=False)
    percent: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="credits")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="credit")


class Dictionary(Base):
    __tablename__ = "dictionary"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    plans: Mapped[List["Plan"]] = relationship("Plan", back_populates="category")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="type")


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    period: Mapped[date] = mapped_column(nullable=False)
    sum: Mapped[int] = mapped_column(nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("dictionary.id"), nullable=False)

    category: Mapped["Dictionary"] = relationship("Dictionary",back_populates="plans")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sum: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    payment_date: Mapped[date] = mapped_column(nullable=False)
    credit_id: Mapped[int] = mapped_column(ForeignKey("credits.id"), nullable=False)
    type_id: Mapped[int] = mapped_column(ForeignKey("dictionary.id"), nullable=False)

    credit: Mapped["Credit"] = relationship("Credit", back_populates="payments")
    type: Mapped["Dictionary"] = relationship("Dictionary", back_populates="payments")
