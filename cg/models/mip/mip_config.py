"""Model MIP config"""

from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, ValidationInfo, field_validator

from cg.constants.priority import SlurmQos


class AnalysisType(BaseModel):
    analysis_type: str
    sample_id: str


class MipBaseConfig(BaseModel):
    """This model is used when validating the mip analysis config"""

    family_id_: str | None = Field(None, alias="family_id")
    case_id: Annotated[str | None, Field(validate_default=True)] = None
    analysis_type_: dict = Field(dict, alias="analysis_type")
    samples: Annotated[list[AnalysisType] | None, Field(validate_default=True)] = None
    config_path: str = Field(str, alias="config_file_analysis")
    deliverables_file_path: str = Field(str, alias="store_file")
    email: EmailStr
    is_dry_run: bool = Field(False, alias="dry_run_all")
    log_path: str = Field(str, alias="log_file")
    out_dir: str = Field(str, alias="outdata_dir")
    priority: SlurmQos = Field(SlurmQos, alias="slurm_quality_of_service")
    sample_info_path: str = Field(str, alias="sample_info_file")
    sample_ids: list[str]

    @field_validator("case_id")
    @classmethod
    def set_case_id(cls, value: str, info: ValidationInfo) -> str:
        """Set case id. Family id is used for older versions of MIP analysis"""
        return value or info.data.get("family_id_")

    @field_validator(
        "samples",
    )
    @classmethod
    def set_samples(cls, _, info: ValidationInfo) -> list[AnalysisType]:
        """Set samples analysis type"""
        raw_samples: dict = info.data.get("analysis_type_")
        return [
            AnalysisType(sample_id=sample_id, analysis_type=analysis_type)
            for sample_id, analysis_type in raw_samples.items()
        ]
