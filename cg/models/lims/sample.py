from typing import Optional

from pydantic.v1 import BaseModel, validator
from typing_extensions import Literal

from cg.constants import Priority

SEX_MAP = {"male": "M", "female": "F"}


class Udf(BaseModel):
    application: str
    capture_kit: Optional[str]
    collection_date: Optional[str]
    comment: Optional[str]
    concentration: Optional[str]
    concentration_sample: Optional[str]
    customer: str
    control: Optional[str]
    data_analysis: Optional[str]
    data_delivery: Optional[str]
    elution_buffer: Optional[str]
    extraction_method: Optional[str]
    family_name: str = "NA"
    formalin_fixation_time: Optional[str]
    index: Optional[str]
    index_number: Optional[str]
    lab_code: Optional[str]
    organism: Optional[str]
    organism_other: Optional[str]
    original_lab: Optional[str]
    original_lab_address: Optional[str]
    pool: Optional[str]
    post_formalin_fixation_time: Optional[str]
    pre_processing_method: Optional[str]
    primer: Optional[str]
    priority: str = Priority.standard.name
    quantity: Optional[str]
    reference_genome: Optional[str]
    region: Optional[str]
    region_code: Optional[str]
    require_qc_ok: bool = False
    rml_plate_name: Optional[str]
    selection_criteria: Optional[str]
    sex: Literal["M", "F", "unknown"] = "unknown"
    skip_reception_control: Optional[bool] = None
    source: str = "NA"
    tissue_block_size: Optional[str]
    tumour: Optional[bool] = False
    tumour_purity: Optional[str]
    volume: Optional[str]
    well_position_rml: Optional[str]
    verified_organism: Optional[bool]

    @validator("sex", pre=True)
    def validate_sex(cls, value: str):
        return SEX_MAP.get(value, "unknown")


class LimsSample(BaseModel):
    name: str
    container: str = "Tube"
    container_name: Optional[str]
    well_position: Optional[str]
    index_sequence: Optional[str]
    udfs: Optional[Udf]

    @classmethod
    def parse_obj(cls, obj: dict):
        parsed_obj: LimsSample = super().parse_obj(obj)
        udf: Udf = Udf.parse_obj(obj)
        parsed_obj.udfs = udf
        return parsed_obj
