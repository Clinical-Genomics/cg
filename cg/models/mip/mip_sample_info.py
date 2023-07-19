"""Model MIP sample info"""
from typing import Optional

import datetime

from pydantic import BaseModel, Field, field_validator


class MipBaseSampleInfo(BaseModel):
    """This model is used when validating the mip sample info file"""

    family_id_: Optional[str] = Field(None, alias="family_id")
    case_id: Optional[str] = None
    human_genome_build_: dict = Field(..., alias="human_genome_build")
    genome_build: str = None
    program_: dict = Field(None, alias="program")
    recipe_: dict = Field(None, alias="recipe")
    rank_model_version: str = None
    sv_rank_model_version: str = None
    analysis_run_status_: str = Field(..., alias="analysisrunstatus")
    date: datetime.datetime = Field(..., alias="analysis_date")
    is_finished: bool = False
    mip_version: str = None

    @field_validator("case_id", mode="before")
    def set_case_id(cls, value, values: dict) -> str:
        """Set case_id. Family_id is used for older versions of MIP analysis"""
        return value or values.get("family_id_")

    @field_validator("genome_build", mode="before")
    def set_genome_build(cls, _, values: dict) -> str:
        """Set genome_build by combining source i.e. "hg"|"grch" and version"""
        raw_genome_build: dict = values.get("human_genome_build_")
        source = raw_genome_build.get("source")
        version = raw_genome_build.get("version")
        return f"{source}{version}"

    @field_validator("is_finished")
    def set_is_finished(cls, _, values: dict) -> bool:
        """Set is_finished from analysisrunstatus_"""
        return values.get("analysis_run_status_") == "finished"

    @field_validator("rank_model_version")
    def set_rank_model_version(cls, _, values: dict) -> str:
        """Set rank_model_version from genmod snv/indel analysis"""
        if "recipe_" in values:
            if "genmod" in values["recipe_"]:
                return values["recipe_"]["genmod"]["rank_model"]["version"]
        else:
            if "genmod" in values["program_"]:
                return values["program_"]["genmod"]["rank_model"]["version"]

    @field_validator("sv_rank_model_version")
    def set_sv_rank_model_version(cls, _, values: dict) -> str:
        """Set rank_model_version from genmod SV analysis"""
        if "recipe_" in values:
            if "genmod" in values["recipe_"]:
                return values["recipe_"]["sv_genmod"]["sv_rank_model"]["version"]
        else:
            if "genmod" in values["program_"]:
                return values["program_"]["sv_genmod"]["sv_rank_model"]["version"]
