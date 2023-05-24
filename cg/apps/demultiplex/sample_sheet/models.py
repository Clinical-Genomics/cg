import logging
from pydantic import BaseModel, Field
from typing import List

from cg.constants.demultiplexing import SampleSheetHeaderColumnNames

LOG = logging.getLogger(__name__)


class NovaSeqSample(BaseModel):
    """This model is used when parsing/validating existing sample sheets."""

    flow_cell: str = Field(..., alias=SampleSheetHeaderColumnNames.FLOW_CELL_ID.value)
    lane: int = Field(..., alias=SampleSheetHeaderColumnNames.LANE.value)
    sample_id: str = Field(..., alias="SampleID")
    sample_ref: str = Field(..., alias="SampleRef")
    index: str = Field(..., alias="index")
    index2: str = ""
    sample_name: str = Field(..., alias="SampleName")
    control: str = Field("N", alias="Control")
    recipe: str = Field("R1", alias="Recipe")
    operator: str = Field(..., alias="Operator")
    project: str = Field(..., alias="Project")
    second_index: str = Field("script", alias="index2")

    class Config:
        allow_population_by_field_name = True


class SampleBcl2Fastq(NovaSeqSample):
    sample_id: str = Field(..., alias="SampleID")
    project: str = Field(..., alias="Project")


class SampleDragen(NovaSeqSample):
    sample_id: str = Field(..., alias="Sample_ID")
    project: str = Field(..., alias="Sample_Project")


class SampleSheet(BaseModel):
    samples: List[NovaSeqSample]


class SampleSheetBcl2Fastq(SampleSheet):
    samples: List[SampleBcl2Fastq]


class SampleSheetDragen(SampleSheet):
    samples: List[SampleDragen]
