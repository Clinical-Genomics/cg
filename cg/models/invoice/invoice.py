from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

"""Module for modelling Invoices."""


class Contact(BaseModel):
    """Class for collection contact information used in the invoice."""

    name: str
    email: str
    customer_name: str
    reference: str
    address: str


class Application(BaseModel):
    """Class to collect Application information used in the invoice."""

    version: str
    tag: str
    discounted_price: int
    percent_kth: int


class InvoiceInfo(BaseModel):
    """Class to collect invoice information used in the invoice report."""

    name: str
    lims_id: Optional[str]
    id: str
    application_tag: str
    project: str
    date: str
    price: int
    priority: str
    price_kth: Optional[int]
    total_price: Optional[int]


class InvoiceReport(BaseModel):
    """Class that collects information used to create the invoice Excel sheet."""

    cost_center: str
    project_number: Optional[str]
    customer_id: str
    customer_name: str
    agreement: Optional[str]
    invoice_id: int
    contact: dict
    records: List[dict]
    pooled_samples: List
    record_type: str
