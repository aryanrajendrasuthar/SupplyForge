import csv
import io
import json
from decimal import Decimal, InvalidOperation

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import PricingTier, Sku
from app.schemas import BulkImportResult, BulkImportRowResult, SkuCreate


def parse_bulk_import(filename: str, raw: bytes, db: Session) -> BulkImportResult:
    rows = _rows_from_json(raw) if filename.lower().endswith(".json") else _rows_from_csv(raw)

    created = updated = failed = 0
    row_results: list[BulkImportRowResult] = []

    for index, row in enumerate(rows, start=1):
        try:
            payload = SkuCreate.model_validate(row)
        except ValidationError as exc:
            failed += 1
            row_results.append(BulkImportRowResult(row=index, status="failed", error=str(exc)))
            continue

        try:
            existing = db.execute(select(Sku).where(Sku.sku == payload.sku)).scalar_one_or_none()
            if existing is None:
                db.add(_build_sku(payload))
                status = "created"
            else:
                _apply_update(existing, payload, db)
                status = "updated"
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            failed += 1
            row_results.append(
                BulkImportRowResult(row=index, sku=payload.sku, status="failed", error=str(exc.orig))
            )
            continue

        if status == "created":
            created += 1
        else:
            updated += 1
        row_results.append(BulkImportRowResult(row=index, sku=payload.sku, status=status))

    return BulkImportResult(created=created, updated=updated, failed=failed, rows=row_results)


def _build_sku(payload: SkuCreate) -> Sku:
    return Sku(
        sku=payload.sku,
        name=payload.name,
        description=payload.description,
        category=payload.category,
        compliance_certs=payload.compliance_certs,
        pricing_tiers=[
            PricingTier(min_quantity=t.min_quantity, unit_price=t.unit_price) for t in payload.pricing_tiers
        ],
    )


def _apply_update(sku: Sku, payload: SkuCreate, db: Session) -> None:
    sku.name = payload.name
    sku.description = payload.description
    sku.category = payload.category
    sku.compliance_certs = payload.compliance_certs
    if payload.pricing_tiers:
        # Flush the deletes before inserting the replacements — see the same
        # comment in app/routes.py::update_sku for why this ordering matters.
        sku.pricing_tiers.clear()
        db.flush()
        sku.pricing_tiers.extend(
            PricingTier(min_quantity=t.min_quantity, unit_price=t.unit_price) for t in payload.pricing_tiers
        )


def _rows_from_json(raw: bytes) -> list[dict]:
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, list):
        raise ValueError("JSON bulk import must be a list of SKU objects")
    return data


def _rows_from_csv(raw: bytes) -> list[dict]:
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8")))
    rows = []
    for row in reader:
        certs = [c.strip() for c in (row.get("compliance_certs") or "").split(";") if c.strip()]
        pricing_tiers: list[dict] = []
        unit_price = (row.get("unit_price") or "").strip()
        if unit_price:
            try:
                pricing_tiers = [{"min_quantity": 1, "unit_price": Decimal(unit_price)}]
            except InvalidOperation:
                pricing_tiers = [{"min_quantity": 1, "unit_price": unit_price}]  # let pydantic reject it
        rows.append(
            {
                "sku": (row.get("sku") or "").strip(),
                "name": (row.get("name") or "").strip(),
                "description": row.get("description") or None,
                "category": (row.get("category") or "").strip(),
                "compliance_certs": certs,
                "pricing_tiers": pricing_tiers,
            }
        )
    return rows
