from pydantic import BaseModel

from cg.models.orders.sample_base import OrderSample


# Class for holding information about cases in order
class OrderCase(BaseModel):
    cohorts: list[str] | None
    name: str
    panels: list[str] | None
    priority: str
    samples: list[OrderSample]
    synopsis: str | None


class OrderPool(BaseModel):
    name: str
    data_analysis: str
    data_delivery: str | None
    application: str
    samples: list[OrderSample]


# This is for validating in data
class Orderform(BaseModel):
    comment: str | None = None
    delivery_type: str
    project_type: str
    customer: str
    name: str
    data_analysis: str | None = None
    data_delivery: str | None = None
    ticket: int | None = None
    samples: list[OrderSample]
    cases: list[OrderCase] | None = None
