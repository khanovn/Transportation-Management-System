from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Iterable

from . import models


def calculate_invoice_age(invoice: models.Invoice, today: date | None = None) -> int:
    today = today or date.today()
    return (today - invoice.issue_date).days


def calculate_days_past_due(invoice: models.Invoice, today: date | None = None) -> int:
    today = today or date.today()
    return max((today - invoice.due_date).days, 0)


def is_overdue(invoice: models.Invoice, today: date | None = None) -> bool:
    return calculate_days_past_due(invoice, today) > 0 and invoice.amount_outstanding > 0


def determine_aging_bucket(days_past_due: int) -> str:
    if days_past_due <= 0:
        return "current"
    if days_past_due <= 30:
        return "1-30"
    if days_past_due <= 60:
        return "31-60"
    if days_past_due <= 90:
        return "61-90"
    return "90+"


def sum_decimal(values: Iterable[Decimal | float | int]) -> Decimal:
    total = Decimal("0")
    for value in values:
        total += Decimal(str(value))
    return total
