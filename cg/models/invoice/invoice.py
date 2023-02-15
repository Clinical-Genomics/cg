from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class Contact(BaseModel):
    name: str
    email: str
    customer_name: str
    reference: str
    address: str


class Application(BaseModel):
    version: str
    tag: str
    discounted_price: int
    percent_kth: int


class InvoiceInfo(BaseModel):
    name: str
    lims_id: str
    id: str
    application_tag: str
    project: str
    date: Optional[datetime]
    price: int
    priority: str
    price_kth: Optional[int]
    total_price: Optional[int]


class InvoiceReport(BaseModel):
    cost_center: str
    project_number: str
    customer_id: str
    customer_name: str
    agreement: str
    invoice_id: int
    contact: dict
    records: List[dict]
    pooled_samples: List
    record_type: str
