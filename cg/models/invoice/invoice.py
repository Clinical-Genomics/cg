"""Module for defining invoice models."""
from pydantic import BaseModel
from typing import List, Optional, Any
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

    version: str
    tag: str
    discounted_price: int
    percent_kth: int


class InvoiceInfo(BaseModel):
    """Class to collect invoice information used in the invoice report."""

    name: str
    id: str
    lims_id: Optional[str] = None
    application_tag: str
    project: str
    date: Optional[Any] = None
    price: int
    priority: PriorityTerms
    price_kth: Optional[int] = None
    total_price: Optional[int] = None


class InvoiceReport(BaseModel):
    """Class that collects information used to create the invoice Excel sheet."""

    cost_center: str
    project_number: Optional[str] = None
    customer_id: str
    customer_name: str
    agreement: Optional[str] = None
    invoice_id: int
    contact: dict
    records: List
    pooled_samples: Optional[Any] = None
    record_type: RecordType
