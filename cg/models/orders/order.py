from typing import Optional

from pydantic import BaseModel, constr, conlist

from cg.store import models


class OrderIn(BaseModel):
    name: constr(min_length=2, max_length=models.Sample.order.property.columns[0].type.length)
    comment: Optional[str]
    customer: constr(min_length=7, max_length=7)
    samples: conlist(dict, min_items=1)
