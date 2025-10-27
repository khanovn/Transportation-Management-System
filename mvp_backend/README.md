# Invoice Receivables MVP Backend

This FastAPI service implements the minimal viable product for the invoice payment tracking and receivables management platform described in `docs/invoice-ar-spec.md`.

## Features

- Partners and contacts management with validation
- Invoice lifecycle tracking including automated aging metadata
- Payment ingestion with automatic balance reconciliation
- Factoring report CSV import that auto-matches payments to invoices
- Aging dashboard metrics and top debtor summaries
- Email campaign preview and lightweight queuing for weekly follow-ups
- Minimal REST API surface with OpenAPI schema generated automatically by FastAPI

## Getting Started

Create a virtual environment and install dependencies:

```bash
cd mvp_backend
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

Run the API locally:

```bash
uvicorn app.main:app --reload
```

The service uses a SQLite database stored at `invoice_ar.db` in the project root. FastAPI will generate the tables automatically on startup.

### Running Tests

```bash
pytest
```

## API Overview

Key endpoints include:

- `POST /partners` create partners
- `POST /contacts` manage debtor contacts
- `POST /invoices` create invoices (auto-calculates outstanding balance)
- `POST /payments` register payments and update invoice status
- `GET /dashboard/aging` view KPI metrics
- `GET /emails/weekly-campaign` preview batched reminder emails
- `POST /import/factoring-report` ingest CSV statements from the factoring provider

Refer to the auto-generated OpenAPI docs at `/docs` for the full contract.
