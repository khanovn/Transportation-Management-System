from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/emails", tags=["emails"])


@router.get("/weekly-campaign", response_model=list[schemas.EmailPreview])
def preview_weekly_campaign(db: Session = Depends(get_db)):
    cutoff_date = datetime.utcnow().date() - timedelta(days=30)
    invoices = (
        db.query(models.Invoice)
        .filter(
            or_(
                models.Invoice.last_status_update_at == None,  # noqa: E711
                models.Invoice.last_status_update_at < cutoff_date,
            )
        )
        .filter(models.Invoice.amount_outstanding > 0)
        .all()
    )
    grouped: dict[str, dict[str, object]] = defaultdict(lambda: {"invoice_numbers": [], "total_due": Decimal("0")})
    for invoice in invoices:
        debtor_key = invoice.debtor_name.lower()
        item = grouped[debtor_key]
        item["debtor_name"] = invoice.debtor_name
        contact_email = invoice.partner.contacts[0].email if invoice.partner.contacts else None
        item["debtor_email"] = contact_email
        item["invoice_numbers"].append(invoice.invoice_number)
        item["total_due"] = item.get("total_due", Decimal("0")) + Decimal(str(invoice.amount_outstanding))
    previews = []
    for group in grouped.values():
        invoice_numbers = group["invoice_numbers"]
        subject = f"Friendly reminder: {len(invoice_numbers)} open invoice(s)"
        body = "\n".join(
            [
                f"Dear {group.get('debtor_name')},",
                "",
                "We are following up on the outstanding invoices listed below:",
                *[f"- {number}" for number in invoice_numbers],
                "",
                "Please let us know if you need any assistance.",
                "",
                "Best regards,",
                "Receivables Team",
            ]
        )
        previews.append(
            schemas.EmailPreview(
                debtor_name=group.get("debtor_name"),
                debtor_email=group.get("debtor_email"),
                invoice_numbers=invoice_numbers,
                total_due=group.get("total_due"),
                subject=subject,
                body=body,
            )
        )
    return previews


@router.post("/queue", response_model=schemas.EmailQueueRead, status_code=status.HTTP_201_CREATED)
def queue_email(item: schemas.EmailQueueCreate, db: Session = Depends(get_db)):
    entity = models.EmailQueueItem(**item.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return schemas.EmailQueueRead.model_validate(entity)


@router.get("/queue", response_model=list[schemas.EmailQueueRead])
def list_queue(db: Session = Depends(get_db)):
    items = db.query(models.EmailQueueItem).order_by(models.EmailQueueItem.scheduled_for.asc()).all()
    return [schemas.EmailQueueRead.model_validate(item) for item in items]
