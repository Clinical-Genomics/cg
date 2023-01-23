from typing import Optional, Union, List, Any

from datetime import datetime

from pydantic import BaseModel, validator

from cg.constants.experiment_design import Control, Container
from cg.constants.priority import Priority, PriorityChoices
from cg.models.dolores.event import EventComment
from cg.models.dolores.sequencing import Sequencing


class ExperimentDesign(BaseModel):
    container: Optional[Container]
    container_name: Optional[str]
    container_position: Optional[str]
    control: Optional[Control]
    downsampled_to_nr_sequence_reads: Optional[int]
    time_point: Optional[str]
    series: Optional[str]


class Sample(BaseModel):
    created_at: Optional[datetime]
    comments: Optional[List[EventComment]]
    customer: str
    customer_sample_id: str
    experiment_design: Optional[ExperimentDesign]
    lims_sample_id: str
    invoice: bool = True
    invoice_id: Optional[int]
    order_id: int
    priority: Union[Priority, PriorityChoices]
    received_at: Optional[datetime]
    sample_id: str
    sequencing: Optional[List[Sequencing]]
    subject_id: str
    ticket_ids: Optional[List[int]]
    total_nr_sequencing_reads: Optional[int]
    pass_sequencing_qc: bool = False

    @validator("priority", always=True)
    def convert_priority(cls, value: Union[Priority, PriorityChoices]) -> Priority:
        if isinstance(value, str):
            return Priority[value]
        return value

    @validator("total_nr_sequencing_reads", always=True)
    def set_total_nr_sequencing_reads(cls, _, values: dict[str, Any]) -> int:
        total_nr_sequencing_reads: int = 0
        if not values.get("sequencing"):
            return total_nr_sequencing_reads
        sequencings: List[Sequencing] = values.get("sequencing")
        for sequencing in sequencings:
            total_nr_sequencing_reads += sequencing.sequence_reads
        return total_nr_sequencing_reads


class SampleCancer(Sample):
    is_tumour: bool
    loqusdb_id: Optional[str]
    loqusdb_name: Optional[str]


class SampleRareDisease(Sample):
    loqusdb_id: Optional[str]
    loqusdb_name: Optional[str]
