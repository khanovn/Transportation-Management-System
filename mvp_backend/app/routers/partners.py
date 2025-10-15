from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/partners", tags=["partners"])


@router.post("", response_model=schemas.PartnerRead, status_code=status.HTTP_201_CREATED)
def create_partner(partner: schemas.PartnerCreate, db: Session = Depends(get_db)):
    entity = models.Partner(**partner.model_dump())
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


@router.get("", response_model=list[schemas.PartnerRead])
def list_partners(db: Session = Depends(get_db)):
    partners = db.query(models.Partner).order_by(models.Partner.name).all()
    return partners


@router.get("/{partner_id}", response_model=schemas.PartnerRead)
def get_partner(partner_id: int, db: Session = Depends(get_db)):
    partner = db.get(models.Partner, partner_id)
    if not partner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found")
    return partner


@router.patch("/{partner_id}", response_model=schemas.PartnerRead)
def update_partner(partner_id: int, payload: schemas.PartnerUpdate, db: Session = Depends(get_db)):
    partner = db.get(models.Partner, partner_id)
    if not partner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(partner, key, value)
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner


@router.delete("/{partner_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_partner(partner_id: int, db: Session = Depends(get_db)):
    partner = db.get(models.Partner, partner_id)
    if not partner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found")
    db.delete(partner)
    db.commit()
    return None
