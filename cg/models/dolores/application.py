import datetime
from typing import Any, Optional, List

from pydantic import BaseModel, validator

from cg.constants.sequencing import PreparationCategory, SequencingMethod


class ApplicationPrice(BaseModel):
    express: int
    clinical_trials: Optional[int]
    comment: Optional[str]
    priority: int
    research: int
    standard: int
    percent_invoicing_kth: float
    valid_from: datetime.date
    version: int


class Application(BaseModel):
    application_id: str
    application_price: List[ApplicationPrice]
    comment: Optional[str]
    description: str
    is_accredited: bool
    is_archived: bool
    min_sequencing_depth: int
    min_required_sample_concentration: int
    max_required_sample_concentration: int
    percent_reads_guaranteed: float
    sequencing_method: SequencingMethod = SequencingMethod.ILLUMINA
    preparation_category: PreparationCategory
    priority_processing: bool
    sample_concentration_unit: str
    sequencing_depth: int
    required_sample_concentration: Optional[str]
    target_sequence_reads: int
    turn_around_time: int
    expected_reads: Optional[int]

    @validator("required_sample_concentration", always=True)
    def set_required_sample_concentration(cls, value: str, values: dict[str, Any]) -> str:
        if isinstance(value, str):
            return value
        required_sample_concentration_terms: list = [
            values.get("min_required_sample_concentration"),
            "-",
            values.get("max_required_sample_concentration"),
            values.get("sample_concentration_unit"),
        ]
        return " ".join(map(str, required_sample_concentration_terms))

    @validator("expected_reads", always=True)
    def set_expected_reads(cls, _, values: dict[str, Any]) -> int:
        return int(
            values.get("target_sequence_reads") * values.get("percent_reads_guaranteed") / 100
        )
