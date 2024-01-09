from pydantic.v1 import BaseModel, validator
from typing_extensions import Literal

from cg.constants import Priority

SEX_MAP = {"male": "M", "female": "F"}


class Udf(BaseModel):
    application: str
    capture_kit: str | None
    collection_date: str | None
    comment: str | None
    concentration: str | None
    concentration_sample: str | None
    concentration_ng_ul: str | None
    customer: str
    control: str | None
    data_analysis: str | None
    data_delivery: str | None
    elution_buffer: str | None
    extraction_method: str | None
    family_name: str | None = "NA"
    formalin_fixation_time: str | None
    index: str | None
    index_number: str | None
    lab_code: str | None
    organism: str | None
    organism_other: str | None
    original_lab: str | None
    original_lab_address: str | None
    pool: str | None
    post_formalin_fixation_time: str | None
    pre_processing_method: str | None
    primer: str | None
    priority: str = Priority.standard.name
    quantity: str | None
    reference_genome: str | None
    region: str | None
    region_code: str | None
    require_qc_ok: bool = False
    rml_plate_name: str | None
    selection_criteria: str | None
    sex: Literal["M", "F", "unknown"] = "unknown"
    skip_reception_control: bool | None = None
    source: str = "NA"
    tissue_block_size: str | None
    tumour: bool | None = False
    tumour_purity: str | None
    volume: str | None
    well_position_rml: str | None
    verified_organism: bool | None

    @validator("sex", pre=True)
    def validate_sex(cls, value: str):
        return SEX_MAP.get(value, "unknown")


class LimsSample(BaseModel):
    name: str
    container: str = "Tube"
    container_name: str | None
    well_position: str | None
    index_sequence: str | None
    udfs: Udf | None

    @classmethod
    def parse_obj(cls, obj: dict):
        parsed_obj: LimsSample = super().parse_obj(obj)
        udf: Udf = Udf.parse_obj(obj)
        parsed_obj.udfs = udf
        return parsed_obj
