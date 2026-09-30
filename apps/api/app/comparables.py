"""RET-030 comparable inputs and deterministic, unadjusted unit-rate analysis."""

import csv
import hashlib
import io
import json
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import Comparable


def _nonblank(value: str) -> str:
    result = value.strip()
    if not result:
        raise ValueError("value must not be blank")
    return result


class ComparableFacts(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transaction_date: date
    reported_price: Decimal = Field(gt=0)
    currency_code: str = Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    property_type: str = Field(min_length=1, max_length=200)
    area_value: Decimal = Field(gt=0)
    area_unit: str = Field(min_length=1, max_length=80)
    location_label: str = Field(min_length=1, max_length=300)
    project_name: str | None = Field(default=None, max_length=300)
    developer_name: str | None = Field(default=None, max_length=300)

    @field_validator("property_type", "area_unit", "location_label")
    @classmethod
    def required_text(cls, value: str) -> str:
        return _nonblank(value)

    @field_validator("project_name", "developer_name")
    @classmethod
    def optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class ComparableCreate(ComparableFacts):
    model_config = ConfigDict(extra="forbid")

    evidence_id: UUID


class ComparableRecord(ComparableCreate):
    id: UUID
    deal_id: UUID
    price_per_area: Decimal


class CsvComparableImport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    csv_content: str = Field(min_length=1, max_length=2_000_000)
    source_name: str = Field(min_length=1, max_length=300)
    source_type: str = Field(min_length=1, max_length=100)
    source_reference: str | None = None
    rights_status: str = Field(min_length=1, max_length=100)
    rights_notes: str | None = None

    @field_validator("source_name", "source_type", "rights_status")
    @classmethod
    def source_text(cls, value: str) -> str:
        return _nonblank(value)


class ValuationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    currency_code: str = Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    as_of: date


class ValuationRecord(BaseModel):
    valuation_method: str
    currency_code: str
    area_unit: str
    as_of: date
    comparable_count: int
    comparable_ids: list[UUID]
    unit_rate_low: Decimal
    unit_rate_central: Decimal
    unit_rate_high: Decimal
    valuation_low: Decimal
    valuation_central: Decimal
    valuation_high: Decimal
    dispersion_ratio: Decimal
    excluded_future_count: int
    excluded_rights_count: int


CSV_REQUIRED_COLUMNS = {
    "transaction_date",
    "reported_price",
    "currency_code",
    "property_type",
    "area_value",
    "area_unit",
    "location_label",
}
CSV_OPTIONAL_COLUMNS = {"project_name", "developer_name"}


def parse_comparable_csv(content: str) -> list[tuple[ComparableFacts, dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(content, newline=""))
    fieldnames = reader.fieldnames or []
    if len(fieldnames) != len(set(fieldnames)):
        raise ValueError("CSV column names must be unique")
    headers = set(fieldnames)
    if not CSV_REQUIRED_COLUMNS <= headers or headers - CSV_REQUIRED_COLUMNS - CSV_OPTIONAL_COLUMNS:
        missing = sorted(CSV_REQUIRED_COLUMNS - headers)
        unexpected = sorted(headers - CSV_REQUIRED_COLUMNS - CSV_OPTIONAL_COLUMNS)
        raise ValueError(f"CSV columns invalid; missing={missing}, unexpected={unexpected}")
    rows: list[tuple[ComparableFacts, dict[str, str]]] = []
    for row_number, row in enumerate(reader, start=2):
        if None in row or not any((value or "").strip() for value in row.values()):
            raise ValueError(f"CSV row {row_number} is malformed or blank")
        raw = {key: value or "" for key, value in row.items() if key is not None}
        try:
            facts = ComparableFacts.model_validate(raw)
        except Exception as error:
            raise ValueError(
                f"CSV row {row_number} has invalid or missing field values; source values suppressed"
            ) from error
        rows.append((facts, raw))
    if not rows:
        raise ValueError("CSV must contain at least one comparable row")
    return rows


def comparable_fingerprint(facts: ComparableFacts) -> str:
    canonical = {
        "transaction_date": facts.transaction_date.isoformat(),
        "reported_price": format(facts.reported_price.normalize(), "f"),
        "currency_code": facts.currency_code,
        "property_type": facts.property_type.casefold(),
        "area_value": format(facts.area_value.normalize(), "f"),
        "area_unit": facts.area_unit.casefold(),
        "location_label": facts.location_label.casefold(),
        "project_name": (facts.project_name or "").casefold(),
        "developer_name": (facts.developer_name or "").casefold(),
    }
    serialized = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def price_per_area(reported_price: Decimal, area_value: Decimal) -> Decimal:
    return (reported_price / area_value).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


USABLE_RIGHTS_STATUSES = {"synthetic", "authorized", "licensed", "customer_provided"}


def usable_rights(rights_status: str) -> bool:
    return rights_status.strip().casefold() in USABLE_RIGHTS_STATUSES


def calculate_indicative_valuation(
    *,
    property_area: Decimal,
    property_area_unit: str,
    property_type: str,
    location_label: str,
    currency_code: str,
    as_of: date,
    comparable_rows: list[tuple[Comparable, str]],
) -> ValuationRecord:
    """Use exact-match comparable facts and an unadjusted median unit rate.

    No area conversion, FX conversion, location inference, or quality weighting
    occurs. The same (currency, area unit, type, and location) must be supplied.
    """
    matches = []
    future_count = 0
    rights_count = 0
    for comparable, rights_status in comparable_rows:
        if not usable_rights(rights_status):
            rights_count += 1
            continue
        if comparable.transaction_date > as_of:
            future_count += 1
            continue
        if (
            comparable.currency_code != currency_code
            or comparable.area_unit.casefold() != property_area_unit.casefold()
            or comparable.property_type.casefold() != property_type.casefold()
            or comparable.location_label.casefold() != location_label.casefold()
        ):
            continue
        matches.append((comparable.id, price_per_area(comparable.reported_price, comparable.area_value)))

    if not matches:
        raise ValueError("No eligible exact-match comparables are available for this property.")
    rates = sorted(rate for _, rate in matches)
    count = len(rates)
    if count % 2:
        central_rate = rates[count // 2]
    else:
        central_rate = ((rates[count // 2 - 1] + rates[count // 2]) / Decimal(2)).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
    low_rate, high_rate = rates[0], rates[-1]
    factor = property_area
    low_value = (low_rate * factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    central_value = (central_rate * factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    high_value = (high_rate * factor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    dispersion = (
        ((high_rate - low_rate) / central_rate).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        if central_rate
        else Decimal(0)
    )
    return ValuationRecord(
        valuation_method="unadjusted exact-match median unit rate; observed min/max range",
        currency_code=currency_code,
        area_unit=property_area_unit,
        as_of=as_of,
        comparable_count=count,
        comparable_ids=[comparable_id for comparable_id, _ in matches],
        unit_rate_low=low_rate,
        unit_rate_central=central_rate,
        unit_rate_high=high_rate,
        valuation_low=low_value,
        valuation_central=central_value,
        valuation_high=high_value,
        dispersion_ratio=dispersion,
        excluded_future_count=future_count,
        excluded_rights_count=rights_count,
    )
