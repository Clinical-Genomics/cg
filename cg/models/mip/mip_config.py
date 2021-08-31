"""Model MIP config"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import List

from cg.constants.priority import SlurmQos


class AnalysisType(BaseModel):
    analysis_type: str
    sample_id: str


class MipBaseConfig(BaseModel):
    """This model is used when validating the mip analysis config"""

    family_id_: str = Field(None, alias="family_id")
    case_id: str = None
    analysis_type_: dict = Field(..., alias="analysis_type")
    samples: List[AnalysisType] = None
    config_path: str = Field(..., alias="config_file_analysis")
    deliverables_file_path: str = Field(..., alias="store_file")
    email: EmailStr
    is_dry_run: bool = Field(False, alias="dry_run_all")
    log_path: str = Field(..., alias="log_file")
    out_dir: str = Field(..., alias="outdata_dir")
    priority: SlurmQos = Field(..., alias="slurm_quality_of_service")
    sample_info_path: str = Field(..., alias="sample_info_file")
    sample_ids: List[str]

    @validator("case_id", always=True, pre=True)
    def set_case_id(cls, value, values: dict) -> str:
        """Set case_id. Family_id is used for older versions of MIP analysis"""
        return value or values.get("family_id_")

    @validator("samples", always=True, pre=True)
    def set_samples(cls, _, values: dict) -> List[AnalysisType]:
        """Set samples analysis type"""
        raw_samples: dict = values.get("analysis_type_")
        return [
            AnalysisType(sample_id=sample_id, analysis_type=analysis_type)
            for sample_id, analysis_type in raw_samples.items()
        ]
