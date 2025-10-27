from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas, utils
from ..database import get_db

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("", response_model=schemas.InvoiceRead, status_code=status.HTTP_201_CREATED)
def create_invoice(payload: schemas.InvoiceCreate, db: Session = Depends(get_db)):
    partner = db.get(models.Partner, payload.partner_id)
    if not partner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found")
    entity = models.Invoice(**payload.model_dump())
    entity.amount_outstanding = entity.original_amount
    entity.last_status_update_at = datetime.utcnow()
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return _to_invoice_read(entity)


@router.get("", response_model=list[schemas.InvoiceRead])
def list_invoices(
    db: Session = Depends(get_db),
    partner_id: int | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    overdue_only: bool = False,
    priority: str | None = None,
    search: str | None = None,
):
    query = db.query(models.Invoice).options(joinedload(models.Invoice.partner))
    if partner_id:
        query = query.filter(models.Invoice.partner_id == partner_id)
    if status_filter:
        query = query.filter(models.Invoice.status == status_filter)
    if overdue_only:
        today = date.today()
        query = query.filter(models.Invoice.due_date < today, models.Invoice.amount_outstanding > 0)
    if priority:
        query = query.filter(models.Invoice.priority_level == priority)
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(func.lower(models.Invoice.invoice_number).like(like))
    invoices = query.order_by(models.Invoice.due_date.asc()).all()
    return [_to_invoice_read(invoice) for invoice in invoices]


@router.get("/{invoice_id}", response_model=schemas.InvoiceWithRelations)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = (
        db.query(models.Invoice)
        .options(joinedload(models.Invoice.partner).joinedload(models.Partner.contacts), joinedload(models.Invoice.notes))
        .filter(models.Invoice.id == invoice_id)
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    invoice_read = _to_invoice_read(invoice)
    partner_read = schemas.PartnerRead.model_validate(invoice.partner)
    contacts = [schemas.ContactRead.model_validate(contact) for contact in invoice.partner.contacts]
    invoice_read_dict = invoice_read.model_dump()
    invoice_read_dict.update({"partner": partner_read, "contacts": contacts})
    return schemas.InvoiceWithRelations(**invoice_read_dict)


@router.patch("/{invoice_id}", response_model=schemas.InvoiceRead)
def update_invoice(invoice_id: int, payload: schemas.InvoiceUpdate, db: Session = Depends(get_db)):
    invoice = db.get(models.Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(invoice, key, value)
    invoice.updated_at = datetime.utcnow()
    if "status" in update_data:
        invoice.last_status_update_at = datetime.utcnow()
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return _to_invoice_read(invoice)


@router.post("/{invoice_id}/notes", response_model=schemas.InvoiceNoteRead, status_code=status.HTTP_201_CREATED)
def add_note(invoice_id: int, payload: schemas.InvoiceNoteCreate, db: Session = Depends(get_db)):
    invoice = db.get(models.Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    note = models.InvoiceNote(invoice_id=invoice_id, body=payload.body, author=payload.author)
    db.add(note)
    db.commit()
    db.refresh(note)
    return schemas.InvoiceNoteRead.model_validate(note)


@router.post("/{invoice_id}/manual-action", response_model=schemas.InvoiceRead)
def trigger_manual_action(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.get(models.Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    invoice.manual_action_required = True
    invoice.last_manual_action_at = datetime.utcnow()
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return _to_invoice_read(invoice)


def _to_invoice_read(invoice: models.Invoice) -> schemas.InvoiceRead:
    age = utils.calculate_invoice_age(invoice)
    past_due = utils.calculate_days_past_due(invoice)
    overdue_flag = utils.is_overdue(invoice)
    return schemas.InvoiceRead(
        id=invoice.id,
        partner_id=invoice.partner_id,
        debtor_name=invoice.debtor_name,
        debtor_email_available=invoice.debtor_email_available,
        debtor_credit_rating=invoice.debtor_credit_rating,
        invoice_number=invoice.invoice_number,
        po_reference=invoice.po_reference,
        issue_date=invoice.issue_date,
        due_date=invoice.due_date,
        original_amount=Decimal(str(invoice.original_amount)),
        amount_paid=Decimal(str(invoice.amount_paid)),
        amount_outstanding=Decimal(str(invoice.amount_outstanding)),
        currency=invoice.currency,
        status=invoice.status,
        current_status_note=invoice.current_status_note,
        priority_level=invoice.priority_level,
        manual_action_required=invoice.manual_action_required,
        source=invoice.source,
        factoring_batch_id=invoice.factoring_batch_id,
        invoice_age_days=age,
        days_past_due=past_due,
        is_overdue=overdue_flag,
        created_at=invoice.created_at,
        updated_at=invoice.updated_at,
    )
