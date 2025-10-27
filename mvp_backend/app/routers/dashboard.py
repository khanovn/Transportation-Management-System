from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas, utils
from ..database import get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/aging", response_model=schemas.DashboardMetrics)
def get_aging_summary(db: Session = Depends(get_db)):
    invoices = db.query(models.Invoice).all()
    total_outstanding = Decimal("0")
    total_past_due = Decimal("0")
    overdue_count = 0
    buckets: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))

    debtors: dict[str, dict[str, Decimal | str]] = {}

    for invoice in invoices:
        outstanding = Decimal(str(invoice.amount_outstanding))
        total_outstanding += outstanding
        past_due_days = utils.calculate_days_past_due(invoice)
        bucket = utils.determine_aging_bucket(past_due_days)
        buckets[bucket] += outstanding
        if past_due_days > 0 and outstanding > 0:
            overdue_count += 1
            total_past_due += outstanding
        key = invoice.debtor_name.lower()
        debtor_entry = debtors.setdefault(
            key,
            {
                "debtor_name": invoice.debtor_name,
                "debtor_email": invoice.partner.contacts[0].email if invoice.partner.contacts else None,
                "total_due": Decimal("0"),
                "invoice_numbers": [],
            },
        )
        debtor_entry["total_due"] = debtor_entry.get("total_due", Decimal("0")) + outstanding
        debtor_entry["invoice_numbers"].append(invoice.invoice_number)

    top_debtors = sorted(
        debtors.values(),
        key=lambda item: item["total_due"],
        reverse=True,
    )[:5]

    return schemas.DashboardMetrics(
        total_outstanding=total_outstanding,
        total_past_due=total_past_due,
        invoices_count=len(invoices),
        overdue_count=overdue_count,
        by_bucket={bucket: value for bucket, value in buckets.items()},
        top_debtors=[
            {
                "debtor_name": debtor["debtor_name"],
                "debtor_email": debtor.get("debtor_email"),
                "total_due": debtor["total_due"],
            }
            for debtor in top_debtors
        ],
    )
