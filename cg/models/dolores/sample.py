from typing import Optional, Union, List, Any

from datetime import datetime

from pydantic import BaseModel, validator

from cg.constants.priority import Priority, PriorityChoices
from cg.models.dolores.sequencing import Sequencing


class Sample(BaseModel):
    created_at: Optional[datetime]
    comment: Optional[str]
    customer: str
    customer_sample_id: str
    lims_sample_id: str
    invoice_id: int
    order_id: int
    priority: Union[Priority, PriorityChoices]
    sample_id: str
    sequencing: List[Sequencing]
    subject_id: str
    total_nr_sequencing_reads: Optional[int]

    @validator("priority", always=True)
    def convert_priority(cls, value: Union[Priority, PriorityChoices]) -> Priority:
        if isinstance(value, str):
            return Priority[value]
        return value

    @validator("total_nr_sequencing_reads", always=True)
    def set_total_nr_sequencing_reads(cls, _, values: dict[str, Any]) -> int:
        sequencings: List[Sequencing] = values.get("sequencing")
        total_nr_sequencing_reads: int = 0
        for sequencing in sequencings:
            total_nr_sequencing_reads += sequencing.sequence_reads
        return total_nr_sequencing_reads
