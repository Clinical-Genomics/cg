"""Model MIP config"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from pydantic_core.core_schema import ValidationInfo

from cg.constants.priority import SlurmQos


class AnalysisType(BaseModel):
    analysis_type: str
    sample_id: str


class MipBaseConfig(BaseModel):
    """This model is used when validating the mip analysis config"""

    family_id_: str | None = Field(None, alias="family_id")
    case_id: str = None
    analysis_type_: dict = Field(dict, alias="analysis_type")
    samples: list[AnalysisType] = None
    config_path: str = Field(str, alias="config_file_analysis")
    deliverables_file_path: str = Field(str, alias="store_file")
    email: EmailStr
    is_dry_run: bool = Field(False, alias="dry_run_all")
    log_path: str = Field(str, alias="log_file")
    out_dir: str = Field(str, alias="outdata_dir")
    priority: SlurmQos = Field(SlurmQos, alias="slurm_quality_of_service")
    sample_info_path: str = Field(str, alias="sample_info_file")
    sample_ids: list[str]

    @field_validator("case_id", mode="before")
    @classmethod
    def set_case_id(cls,  info: ValidationInfo, value:str) -> str:
        """Set case_id. Family_id is used for older versions of MIP analysis"""
        return value or info.data.get("family_id_")

    @field_validator("samples", mode="before")
    @classmethod
    def set_samples(cls, _,  info: ValidationInfo) -> list[AnalysisType]:
        """Set samples analysis type"""
        raw_samples: dict = info.data.get("analysis_type_")
        return [
            AnalysisType(sample_id=sample_id, analysis_type=analysis_type)
            for sample_id, analysis_type in raw_samples.items()
        ]
