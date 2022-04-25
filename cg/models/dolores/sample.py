from typing import Optional, Union, List

from datetime import datetime

from pydantic import BaseModel, validator

from cg.constants.priority import Priority, PriorityChoices
from cg.models.dolores.sequencing import Sequencing


class Sample(BaseModel):
    created_at: Optional[datetime]
    customer: str
    customer_sample_id: str
    lims_sample_id: str
    invoice_id: int
    order_id: int
    priority: Union[Priority, PriorityChoices]
    sample_id: str
    sequencing: List[Sequencing]
    subject_id: str

    @validator("priority", always=True)
    def validate_priority(cls, value: Union[Priority, PriorityChoices]) -> Priority:
        if isinstance(value, str):
            return Priority[value]
        return value
