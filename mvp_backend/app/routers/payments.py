from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=schemas.PaymentRead, status_code=status.HTTP_201_CREATED)
def create_payment(payload: schemas.PaymentCreate, db: Session = Depends(get_db)):
    invoice = None
    if payload.invoice_id is not None:
        invoice = db.get(models.Invoice, payload.invoice_id)
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    payment = models.Payment(**payload.model_dump())
    db.add(payment)
    if invoice:
        current_paid = Decimal(str(invoice.amount_paid or 0))
        payment_amount = Decimal(str(payment.amount))
        invoice.amount_paid = current_paid + payment_amount
        invoice.amount_outstanding = Decimal(str(invoice.original_amount)) - invoice.amount_paid
        invoice.updated_at = datetime.utcnow()
        if invoice.amount_outstanding <= 0:
            invoice.status = "paid"
            invoice.amount_outstanding = 0
        db.add(invoice)
    db.commit()
    db.refresh(payment)
    return schemas.PaymentRead.model_validate(payment)


@router.get("", response_model=list[schemas.PaymentRead])
def list_payments(invoice_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(models.Payment)
    if invoice_id is not None:
        query = query.filter(models.Payment.invoice_id == invoice_id)
    payments = query.order_by(models.Payment.payment_date.desc()).all()
    return [schemas.PaymentRead.model_validate(payment) for payment in payments]


@router.patch("/{payment_id}", response_model=schemas.PaymentRead)
def update_payment(payment_id: int, payload: schemas.PaymentUpdate, db: Session = Depends(get_db)):
    payment = db.get(models.Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(payment, key, value)
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return schemas.PaymentRead.model_validate(payment)
