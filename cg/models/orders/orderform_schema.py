from typing import Optional

from pydantic import BaseModel

from cg.models.orders.sample_base import OrderSample


# Class for holding information about cases in order
class OrderCase(BaseModel):
    cohorts: Optional[list[str]]
    name: str
    panels: Optional[list[str]]
    priority: str
    samples: list[OrderSample]
    synopsis: Optional[str]


class OrderPool(BaseModel):
    name: str
    data_analysis: str
    data_delivery: Optional[str]
    application: str
    samples: list[OrderSample]


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
    samples: list[OrderSample]
    cases: Optional[list[OrderCase]] = None
