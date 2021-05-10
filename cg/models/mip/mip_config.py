"""Model MIP config"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import List
from typing_extensions import Literal


class AnalysisType(BaseModel):
    analysis_type: str
    sample_id: str


class MipBaseConfig(BaseModel):
    """This model is used when validating the mip analysis config"""

    analysis_type_: dict = Field(..., alias="analysis_type")
    family_id_: str = Field(None, alias="family_id")
    case_id: str = None
    config_path: str = Field(..., alias="config_file_analysis")
    deliverables_file_path: str = Field(..., alias="store_file")
    email: EmailStr
    is_dry_run: bool = Field(False, alias="dry_run_all")
    log_path: str = Field(..., alias="log_file")
    out_dir: str = Field(..., alias="outdata_dir")
    priority: Literal["low", "normal", "high"] = Field(..., alias="slurm_quality_of_service")
    samples: List[AnalysisType] = None
    sample_info_path: str = Field(..., alias="sample_info_file")

    @validator("case_id", always=True, pre=True)
    def set_case_id(cls, value, values: dict):
        """Set case_id. Family_id is used for older versions of MIP analysis"""
        return value or values.get("family_id_")

    @validator("samples", always=True, pre=True)
    def set_samples(cls, _, values: dict):
        """Set samples analysis type"""
        raw_samples: dict = values.get("analysis_type_")
        return [
            AnalysisType(sample_id=sample_id, analysis_type=analysis_type)
            for sample_id, analysis_type in raw_samples.items()
        ]


def parse_config(data: dict) -> MipBaseConfig:
    """Validate and parse MIP config file"""
    return MipBaseConfig(**data)
