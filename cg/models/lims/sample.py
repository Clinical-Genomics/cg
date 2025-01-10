from pydantic import BaseModel, field_validator
from pydantic_core.core_schema import ValidationInfo
from typing_extensions import Literal

from cg.constants import Priority

SEX_MAP = {"male": "M", "female": "F"}


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
    formalin_fixation_time: float | None = None
    index: str | None = None
    index_number: str | None = None
    lab_code: str | None = None
    organism: str | None = None
    organism_other: str | None = None
    original_lab: str | None = None
    original_lab_address: str | None = None
    pool: str | None = None
    post_formalin_fixation_time: float | None = None
    pre_processing_method: str | None = None
    primer: str | None = None
    priority: str = Priority.standard.name
    quantity: float | None = None
    reference_genome: str | None = None
    region: str | None = None
    region_code: str | None = None
    require_qc_ok: bool = False
    rml_plate_name: str | None = None
    selection_criteria: str | None = None
    sex: Literal["M", "F", "unknown"] = "unknown"
    skip_reception_control: bool | None = None
    source: str = "NA"
    tissue_block_size: str | None = None
    tumour: bool | None = False
    tumour_purity: float | None = None
    verified_organism: bool | None = None
    volume: str | None = None
    well_position_rml: str | None = None

    @field_validator("sex", mode="before")
    @classmethod
    def validate_sex(cls, value: str):
        return SEX_MAP.get(value, "unknown")


class LimsSample(BaseModel):
    container: str = "Tube"
    container_name: str | None = None
    index_sequence: str | None = None
    name: str
    udfs: Udf | None = None
    well_position: str | None = None

    @field_validator("well_position", mode="before")
    def reset_well_positions_for_tubes(cls, value: str, info: ValidationInfo):
        return None if info.data.get("container") == "Tube" else value

    @classmethod
    def parse_obj(cls, obj: dict):
        lims_sample: LimsSample = super().model_validate(obj)
        udf: Udf = Udf.model_validate(obj)
        lims_sample.udfs = udf
        return lims_sample
