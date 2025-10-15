from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, future=True
)
TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)

Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def setup_module(_):
    app.dependency_overrides[get_db] = override_get_db


def teardown_module(_):
    app.dependency_overrides.clear()


client = TestClient(app)


def test_invoice_lifecycle():
    partner_payload = {
        "name": "Acme Logistics",
        "credit_rating": "A",
        "payment_terms_days": 30,
    }
    response = client.post("/partners", json=partner_payload)
    assert response.status_code == 201
    partner_id = response.json()["id"]

    invoice_payload = {
        "partner_id": partner_id,
        "debtor_name": "Globex",
        "debtor_email_available": True,
        "invoice_number": "INV-1001",
        "issue_date": date.today().isoformat(),
        "due_date": (date.today() + timedelta(days=10)).isoformat(),
        "original_amount": "1500.00",
    }
    response = client.post("/invoices", json=invoice_payload)
    assert response.status_code == 201
    invoice = response.json()
    assert invoice["amount_outstanding"] == "1500.00"
    invoice_id = invoice["id"]

    payment_payload = {
        "invoice_id": invoice_id,
        "payment_date": date.today().isoformat(),
        "amount": "500.00",
    }
    response = client.post("/payments", json=payment_payload)
    assert response.status_code == 201

    response = client.get(f"/invoices/{invoice_id}")
    assert response.status_code == 200
    invoice_after_payment = response.json()
    assert invoice_after_payment["amount_outstanding"] == "1000.00"

    dashboard = client.get("/dashboard/aging").json()
    assert dashboard["total_outstanding"] == "1000"
