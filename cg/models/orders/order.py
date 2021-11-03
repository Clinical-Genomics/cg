from typing import Optional

from pydantic import BaseModel, constr, conlist

from cg.models.orders.sample_base import OrderSample
from cg.store import models


class OrderIn(BaseModel):
    name: constr(min_length=2, max_length=models.Sample.order.property.columns[0].type.length)
    comment: Optional[str]
    customer: constr(
        min_length=1, max_length=models.Customer.internal_id.property.columns[0].type.length
    )
    samples: conlist(OrderSample, min_items=1)
