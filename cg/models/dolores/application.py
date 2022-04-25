from typing import Any, Optional

from pydantic import BaseModel, validator

from cg.constants.sequencing import PreparationCategory


class Application(BaseModel):
    application_id: str
    comment: Optional[str]
    description: str
    is_accredited: bool
    is_archived: bool
    min_sequencing_depth: int
    min_required_sample_concentration: int
    max_required_sample_concentration: int
    percent_reads_guaranteed: float
    percent_invoicing_kth: float
    preparation_category: PreparationCategory
    priority_processing: bool
    sample_concentration_unit: str
    sequencing_depth: int
    required_sample_concentration: Optional[str]
    target_sequence_reads: int
    turn_around_time: int

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
