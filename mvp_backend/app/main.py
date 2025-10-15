from __future__ import annotations

from fastapi import FastAPI

from .database import Base, engine
from .routers import contacts, dashboard, emails, imports, invoices, partners, payments

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Invoice Receivables MVP", version="0.1.0")

app.include_router(partners.router)
app.include_router(contacts.router)
app.include_router(invoices.router)
app.include_router(payments.router)
app.include_router(dashboard.router)
app.include_router(emails.router)
app.include_router(imports.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
