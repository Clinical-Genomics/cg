from pydantic import Field

from cg.models.orders.sample_base import NAME_PATTERN, SexEnum, StatusEnum
from cg.services.orders.validation.models.sample import Sample


class NalloSample(Sample):
    father: str | None = Field(None, pattern=NAME_PATTERN)
    mother: str | None = Field(None, pattern=NAME_PATTERN)
    phenotype_groups: list[str] | None = None
    phenotype_terms: list[str] | None = None
    require_qc_ok: bool = False
    sex: SexEnum
    source: str
    status: StatusEnum
    subject_id: str = Field(pattern=NAME_PATTERN, max_length=128)
