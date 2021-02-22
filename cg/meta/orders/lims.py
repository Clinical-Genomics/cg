import logging
from datetime import datetime
from typing import List, Optional

from cg.apps.lims import LimsAPI
from pydantic import BaseModel, validator
from typing_extensions import Literal

LOG = logging.getLogger(__name__)
SEX_MAP = {"male": "M", "female": "F"}


class Udf(BaseModel):
    application: str
    capture_kit: Optional[str]
    comment: Optional[str]
    concentration: Optional[str]
    concentration_sample: Optional[str]
    customer: str
    data_analysis: Optional[str]
    data_delivery: Optional[str]
    elution_buffer: Optional[str]
    extraction_method: Optional[str]
    family_name: str = "NA"
    formalin_fixation_time: Optional[str]
    index: Optional[str]
    index_number: Optional[str]
    organism: Optional[str]
    organism_other: Optional[str]
    pool: Optional[str]
    post_formalin_fixation_time: Optional[str]
    priority: str = "standard"
    quantity: Optional[str]
    reference_genome: Optional[str]
    require_qcok: bool = False
    rml_plate_name: Optional[str]
    sex: Literal["M", "F", "unknown"] = "unknown"
    source: str = "NA"
    tissue_block_size: Optional[str]
    tumour: bool = False
    tumour_purity: Optional[str]
    volume: Optional[str]
    well_position_rml: Optional[str]
    verified_organism: Optional[str]

    @validator("sex")
    def validate_sex(cls, value: str):
        return SEX_MAP.get(value, "unknown")


class LimsSample(BaseModel):
    name: str
    container: str = "Tube"
    container_name: Optional[str]
    well_position: Optional[str]
    index_sequence: Optional[str]
    udfs: Optional[Udf]


class LimsProjectData(BaseModel):
    id: str
    name: str
    date: Optional[datetime]


def to_lims(customer: str, samples: List[dict]) -> List[LimsSample]:
    """Convert order input to lims interface input."""
    samples_lims = []
    for sample in samples:
        LOG.debug(f"{sample['name']}: prepare LIMS input")
        sample["customer"] = customer
        lims_sample: LimsSample = LimsSample.parse_obj(sample)
        udf: Udf = Udf.parse_obj(sample)
        lims_sample.udfs = udf
        samples_lims.append(lims_sample)
    return samples_lims


def process_lims(lims_api: LimsAPI, data: dict, samples: List[dict]):
    """Process samples to add them to LIMS."""
    samples_lims: List[LimsSample] = to_lims(data["customer"], samples)
    project_name = data["ticket"] or data["name"]
    # Create new lims project
    project_data = lims_api.submit_project(
        project_name, [lims_sample.dict() for lims_sample in samples_lims]
    )
    lims_map = lims_api.get_samples(projectlimsid=project_data["id"], map_ids=True)
    return project_data, lims_map
