from typing import List, Optional

from cg.models.orders.sample_base import OrderSample
from pydantic import BaseModel


# Class for holding information about cases in order
class OrderCase(BaseModel):
    cohorts: Optional[List[str]]
    name: str
    panels: Optional[List[str]]
    priority: str
    samples: List[OrderSample]
    synopsis: Optional[str]


class OrderPool(BaseModel):
    name: str
    data_analysis: str
    data_delivery: Optional[str]
    application: str
    samples: List[OrderSample]


# This is for validating in data
class Orderform(BaseModel):
    comment: Optional[str] = None
    delivery_type: str
    project_type: str
    customer: str
    name: str
    data_analysis: Optional[str] = None
    data_delivery: Optional[str] = None
    ticket: Optional[int] = None
    samples: List[OrderSample]
    cases: Optional[List[OrderCase]] = None
