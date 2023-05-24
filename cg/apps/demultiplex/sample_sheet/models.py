import logging
from pydantic import BaseModel, Field
from typing import List

from cg.constants.constants import GenomeVersion
from cg.constants.demultiplexing import SampleSheetHeaderColumnNames

LOG = logging.getLogger(__name__)


class FlowCellSample(BaseModel):
    """This model is used when parsing/validating existing sample sheets."""

    flowcell_id: str = Field(..., alias=SampleSheetHeaderColumnNames.FLOW_CELL_ID.value)
    lane: int = Field(..., alias=SampleSheetHeaderColumnNames.LANE.value)
    sample_id: str
    sample_ref: str = Field(GenomeVersion.hg19.value, alias="SampleRef")
    index: str = Field(..., alias="index")
    index2: str = ""
    sample_name: str = Field(..., alias="SampleName")
    control: str = Field("N", alias="Control")
    recipe: str = Field("R1", alias="Recipe")
    operator: str = Field("script", alias="Operator")
    project: str = Field(..., alias="Project")

    class Config:
        allow_population_by_field_name = True


class FlowCellSampleBcl2Fastq(FlowCellSample):
    sample_id: str = Field(..., alias="SampleID")
    project: str = Field(..., alias="Project")


class FlowCellSampleDragen(FlowCellSample):
    sample_id: str = Field(..., alias="Sample_ID")
    project: str = Field(..., alias="Sample_Project")


class SampleSheet(BaseModel):
    samples: List[FlowCellSample]


class SampleSheetBcl2Fastq(SampleSheet):
    samples: List[FlowCellSampleBcl2Fastq]


class SampleSheetDragen(SampleSheet):
    samples: List[FlowCellSampleDragen]
