from __future__ import annotations

import csv
from datetime import datetime
from decimal import Decimal
from io import StringIO

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db

router = APIRouter(prefix="/import", tags=["import"])


@router.post("/factoring-report", status_code=status.HTTP_202_ACCEPTED)
def ingest_factoring_report(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(StringIO(content))
    imported_count = 0
    for row in reader:
        invoice_number = row.get("invoice_number")
        if not invoice_number:
            continue
        invoice = db.query(models.Invoice).filter(models.Invoice.invoice_number == invoice_number).first()
        if not invoice:
            continue
        amount_raw = row.get("amount_paid", "0")
        amount_paid = Decimal(amount_raw)
        payment_date_raw = row.get("payment_date")
        if not payment_date_raw:
            continue
        payment_date = datetime.strptime(payment_date_raw, "%Y-%m-%d").date()
        payment = models.Payment(
            invoice_id=invoice.id,
            partner_id=invoice.partner_id,
            payment_date=payment_date,
            amount=amount_paid,
            currency=row.get("currency", invoice.currency),
            reference=row.get("reference"),
            source="factoring",
            status="applied",
        )
        invoice.amount_paid = Decimal(str(invoice.amount_paid or 0)) + amount_paid
        invoice.amount_outstanding = Decimal(str(invoice.original_amount)) - invoice.amount_paid
        if invoice.amount_outstanding <= 0:
            invoice.status = "paid"
            invoice.amount_outstanding = 0
        invoice.updated_at = datetime.utcnow()
        db.add(payment)
        db.add(invoice)
        imported_count += 1
    db.commit()
    return {"imported_payments": imported_count}
