from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.post("", response_model=schemas.ContactRead, status_code=status.HTTP_201_CREATED)
def create_contact(contact: schemas.ContactCreate, db: Session = Depends(get_db)):
    if not db.get(models.Partner, contact.partner_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found")
    entity = models.Contact(**contact.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


@router.get("", response_model=list[schemas.ContactRead])
def list_contacts(partner_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(models.Contact)
    if partner_id is not None:
        query = query.filter(models.Contact.partner_id == partner_id)
    return query.order_by(models.Contact.created_at.desc()).all()


@router.patch("/{contact_id}", response_model=schemas.ContactRead)
def update_contact(contact_id: int, payload: schemas.ContactUpdate, db: Session = Depends(get_db)):
    contact = db.get(models.Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(contact, key, value)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = db.get(models.Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    db.delete(contact)
    db.commit()
    return None
