from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class ContactBase(BaseModel):
    name: str
    role: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_primary: bool = False
    validated_at: Optional[datetime] = None


class ContactCreate(ContactBase):
    partner_id: int


class ContactUpdate(ContactBase):
    pass


class ContactRead(ContactBase):
    id: int
    partner_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PartnerBase(BaseModel):
    name: str
    credit_rating: Optional[str] = Field(default=None, max_length=1)
    default_currency: str = "USD"
    payment_terms_days: int = 30
    average_days_to_pay: Optional[int] = None
    notes: Optional[str] = None
    status: str = "active"


class PartnerCreate(PartnerBase):
    pass


class PartnerUpdate(PartnerBase):
    pass


class PartnerRead(PartnerBase):
    id: int
    created_at: datetime
    updated_at: datetime
    contacts: list[ContactRead] = []

    class Config:
        from_attributes = True


class InvoiceBase(BaseModel):
    partner_id: int
    debtor_name: str
    debtor_email_available: bool = False
    debtor_credit_rating: Optional[str] = None
    invoice_number: str
    po_reference: Optional[str] = None
    issue_date: date
    due_date: date
    original_amount: Decimal
    currency: str = "USD"
    status: str = "open"
    current_status_note: Optional[str] = None
    priority_level: str = "normal"
    manual_action_required: bool = False
    source: str = "direct"
    factoring_batch_id: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceUpdate(BaseModel):
    debtor_name: Optional[str] = None
    debtor_email_available: Optional[bool] = None
    debtor_credit_rating: Optional[str] = None
    po_reference: Optional[str] = None
    issue_date: Optional[date] = None
    due_date: Optional[date] = None
    original_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    current_status_note: Optional[str] = None
    priority_level: Optional[str] = None
    manual_action_required: Optional[bool] = None
    source: Optional[str] = None
    factoring_batch_id: Optional[str] = None


class InvoiceRead(InvoiceBase):
    id: int
    amount_paid: Decimal
    amount_outstanding: Decimal
    invoice_age_days: int
    days_past_due: int
    is_overdue: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvoiceWithRelations(InvoiceRead):
    partner: PartnerRead
    contacts: list[ContactRead] = []


class InvoiceNoteCreate(BaseModel):
    invoice_id: int
    body: str
    author: Optional[str] = None


class InvoiceNoteRead(BaseModel):
    id: int
    invoice_id: int
    body: str
    author: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentBase(BaseModel):
    invoice_id: Optional[int] = None
    partner_id: Optional[int] = None
    payment_date: date
    amount: Decimal
    currency: str = "USD"
    reference: Optional[str] = None
    source: str = "factoring"
    status: str = "pending"


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    invoice_id: Optional[int] = None
    status: Optional[str] = None


class PaymentRead(PaymentBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardMetrics(BaseModel):
    total_outstanding: Decimal
    total_past_due: Decimal
    invoices_count: int
    overdue_count: int
    by_bucket: dict[str, Decimal]
    top_debtors: list[dict[str, str | Decimal]]


class EmailPreview(BaseModel):
    debtor_name: str
    debtor_email: Optional[str]
    invoice_numbers: list[str]
    total_due: Decimal
    subject: str
    body: str


class EmailQueueCreate(BaseModel):
    debtor_name: str
    debtor_email: Optional[EmailStr]
    subject: str
    body: str
    scheduled_for: datetime


class EmailQueueRead(EmailQueueCreate):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
