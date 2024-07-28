from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_validator
from typing_extensions import Literal

from cg.constants import Priority

SEX_MAP = {"male": "M", "female": "F"}


class LimsProject(BaseModel):
    id: str
    name: str
    date: datetime | None = None


class Udf(BaseModel):
    application: str
    capture_kit: str | None = None
    collection_date: str | None = None
    comment: str | None = None
    concentration: float | None = None
    concentration_ng_ul: str | None = None
    concentration_sample: float | None = None
    control: str | None = None
    customer: str
    data_analysis: str | None = None
    data_delivery: str | None = None
    elution_buffer: str | None = None
    extraction_method: str | None = None
    family_name: str | None = "NA"
    formalin_fixation_time: int | None = None
    index: str | None = None
    index_number: str | None = None
    lab_code: str | None = None
    organism: str | None = None
    organism_other: str | None = None
    original_lab: str | None = None
    original_lab_address: str | None = None
    pool: str | None = None
    post_formalin_fixation_time: int | None = None
    pre_processing_method: str | None = None
    primer: str | None = None
    priority: str = Priority.standard.name
    quantity: int | None = None
    reference_genome: str | None = None
    region: str | None = None
    region_code: str | None = None
    require_qc_ok: bool = False
    rml_plate_name: str | None = None
    selection_criteria: str | None = None
    sex: Annotated[str, Field(validate_default=True)] = "unknown"
    skip_reception_control: bool | None = None
    source: str = "NA"
    tissue_block_size: str | None = None
    tumour: bool | None = False
    tumour_purity: int | None = None
    verified_organism: bool | None = None
    volume: str | None = None
    well_position_rml: str | None = None

    @field_validator("sex", mode="before")
    @classmethod
    def set_udf_sex(cls, sex: Literal["male", "female", "unknown"]) -> str:
        return SEX_MAP.get(sex, "unknown")


class LimsSample(BaseModel):
    application: str | None = None
    application_version: str | None = None
    case: str | None = None
    comment: str | None = None
    concentration_ng_ul: str | None = None
    container: str = "Tube"
    container_name: str | None = None
    customer: str | None = None
    father: str | None = None
    id: str | None = None
    index_sequence: str | None = None
    mother: str | None = None
    name: str
    panels: list[str] | None = None
    passed_initial_qc: str | None = None
    priority: str | None = None
    project: LimsProject | None = None
    received: str | None = None
    sex: str | None = None
    source: str | None = None
    status: str | None = None
    udfs: Udf | None = None
    well_position: str | None = None

    @classmethod
    def parse_obj(cls, sample_raw: dict):
        lims_sample: LimsSample = super().model_validate(sample_raw)
        lims_sample.udfs = Udf.model_validate(sample_raw)
        return lims_sample
