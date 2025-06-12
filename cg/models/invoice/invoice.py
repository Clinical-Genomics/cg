"""Module for defining invoice models."""

from typing import Any

from pydantic import BaseModel

from cg.constants.priority import PriorityTerms
from cg.constants.sequencing import RecordType


class InvoiceContact(BaseModel):
    """Class for collection contact information used in the invoice."""

    name: str
    email: str
    customer_name: str
    reference: str
    address: str


class InvoiceApplication(BaseModel):
    """Class to collect Application information used in the invoice."""

    version: int
    tag: str
    discounted_price: int
    percent_kth: int


class InvoiceInfo(BaseModel):
    """Class to collect invoice information used in the invoice report."""

    name: str
    id: int
    lims_id: str | None = None
    application_tag: str
    project: str
    date: Any | None = None
    price: int
    priority: PriorityTerms
    price_kth: int | None = None
    total_price: int | None = None


class InvoiceReport(BaseModel):
    """Class that collects information used to create the invoice Excel sheet."""

    cost_center: str
    project_number: str | None = None
    customer_id: str
    customer_name: str
    agreement: str | None = None
    invoice_id: int
    contact: dict
    records: list
    pooled_samples: Any | None = None
    record_type: RecordType
