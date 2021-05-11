"""Model MIP sample info"""

import datetime

from pydantic import BaseModel, Field, validator


class MipBaseSampleinfo(BaseModel):
    """This model is used when validating the mip samplinfo file"""

    analysis_run_status_: str = Field(..., alias="analysisrunstatus")
    date: datetime.datetime = Field(..., alias="analysis_date")
    family_id_: str = Field(None, alias="family_id")
    case_id: str = None
    human_genome_build_: dict = Field(..., alias="human_genome_build")
    genome_build: str = None
    is_finished: bool = False
    program_: dict = None
    rank_model_version: str = None
    recipe_: dict = None
    sv_rank_model_version: str = None
    version: str = Field(..., alias="mip_version")

    @validator("case_id", always=True, pre=True)
    def set_case_id(cls, value, values: dict):
        """Set case_id. Family_id is used for older versions of MIP analysis"""
        return value or values.get("family_id_")

    @validator("genome_build", always=True, pre=True)
    def set_genome_build(cls, _, values: dict):
        """Set genome_build by combining source i.e. "hg"|"grch" and version"""
        raw_genome_build: dict = values.get("human_genome_build_")
        source = raw_genome_build.get("source")
        version = raw_genome_build.get("version")
        return f"{source}{version}"

    @validator("is_finished", always=True)
    def set_is_finished(cls, _, values: dict):
        """Set is_finished from analysisrunstatus_"""
        return values.get("analysis_run_status_") == "finished"

    @validator("rank_model_version", pre=True)
    def set_rank_model_version(cls, _, values: dict) -> str:
        """Set rank_model_version from genmod snv/indel analysis"""
        if "recipe_" in values:
            return values["recipe_"]["genmod"]["rank_model"]["version"]
        else:
            return values["program_"]["genmod"]["rank_model"]["version"]

    @validator("sv_rank_model_version", pre=True)
    def set_sv_rank_model_version(cls, _, values: dict) -> str:
        """Set rank_model_version from genmod SV analysis"""
        if "recipe_" in values:
            return values["recipe_"]["sv_genmod"]["sv_rank_model"]["version"]
        else:
            return values["program_"]["sv_genmod"]["sv_rank_model"]["version"]


def parse_sampleinfo(data: dict) -> MipBaseSampleinfo:
    """Parse MIP sample info file"""
    return MipBaseSampleinfo(**data)
