from __future__ import annotations

from datetime import datetime, date
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Partner(Base):
    __tablename__ = "partners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    credit_rating: Mapped[Optional[str]] = mapped_column(String(1), nullable=True)
    default_currency: Mapped[str] = mapped_column(String(3), default="USD")
    payment_terms_days: Mapped[int] = mapped_column(Integer, default=30)
    average_days_to_pay: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contacts: Mapped[list[Contact]] = relationship("Contact", back_populates="partner", cascade="all, delete-orphan")  # type: ignore[name-defined]
    invoices: Mapped[list[Invoice]] = relationship("Invoice", back_populates="partner", cascade="all, delete-orphan")  # type: ignore[name-defined]


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    partner_id: Mapped[int] = mapped_column(ForeignKey("partners.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    partner: Mapped[Partner] = relationship("Partner", back_populates="contacts")


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    partner_id: Mapped[int] = mapped_column(ForeignKey("partners.id", ondelete="RESTRICT"), nullable=False)
    debtor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    debtor_email_available: Mapped[bool] = mapped_column(Boolean, default=False)
    debtor_credit_rating: Mapped[Optional[str]] = mapped_column(String(1))
    invoice_number: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    po_reference: Mapped[Optional[str]] = mapped_column(String(120))
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    original_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    amount_paid: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    amount_outstanding: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[str] = mapped_column(String(32), default="open")
    current_status_note: Mapped[Optional[str]] = mapped_column(Text)
    last_status_update_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    priority_level: Mapped[str] = mapped_column(String(16), default="normal")
    manual_action_required: Mapped[bool] = mapped_column(Boolean, default=False)
    last_manual_action_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    source: Mapped[str] = mapped_column(String(16), default="direct")
    factoring_batch_id: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    partner: Mapped[Partner] = relationship("Partner", back_populates="invoices")
    notes: Mapped[list[InvoiceNote]] = relationship("InvoiceNote", back_populates="invoice", cascade="all, delete-orphan")  # type: ignore[name-defined]
    payments: Mapped[list[Payment]] = relationship("Payment", back_populates="invoice")  # type: ignore[name-defined]


class InvoiceNote(Base):
    __tablename__ = "invoice_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    invoice: Mapped[Invoice] = relationship("Invoice", back_populates="notes")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_id: Mapped[Optional[int]] = mapped_column(ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True)
    partner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("partners.id", ondelete="SET NULL"), nullable=True)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    reference: Mapped[Optional[str]] = mapped_column(String(120))
    source: Mapped[str] = mapped_column(String(32), default="factoring")
    status: Mapped[str] = mapped_column(String(16), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    invoice: Mapped[Optional[Invoice]] = relationship("Invoice", back_populates="payments")
    partner: Mapped[Optional[Partner]] = relationship("Partner")


class EmailQueueItem(Base):
    __tablename__ = "email_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    debtor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    debtor_email: Mapped[Optional[str]] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
