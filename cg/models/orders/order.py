from typing import List, Optional

from pydantic import BaseModel


class OrderIn(BaseModel):
    name: str
    comment: Optional[str]
    customer: str
    samples: List[dict]
