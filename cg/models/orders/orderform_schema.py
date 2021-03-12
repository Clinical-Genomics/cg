from typing import List, Optional

from pydantic import BaseModel

from cg.models.orders.sample_base import OrderSample


# Class for holding information about cases in order
class OrderCase(BaseModel):
    name: str
    samples: List[OrderSample]
    require_qcok: bool = False
    priority: str
    panels: Optional[List[str]]


class OrderPool(BaseModel):
    name: str
    data_analysis: str
    data_delivery: Optional[str]
    application: str
    samples: List[OrderSample]


# This is for validating in data
class Orderform(BaseModel):
    comment: Optional[str]
    delivery_type: str
    project_type: str
    customer: str
    name: str
    data_analysis: Optional[str]
    data_delivery: Optional[str]
    ticket: Optional[int]
    samples: List[OrderSample]
    cases: Optional[List[OrderCase]]
