import logging
from pydantic import BaseModel, Field
from typing import List

LOG = logging.getLogger(__name__)


class NovaSeqSample(BaseModel):
    """This model is used when parsing/validating existing sample sheets."""

    flow_cell: str = Field(..., alias="FCID")
    lane: int = Field(..., alias="Lane")
    sample_id: str = Field(..., alias="SampleID")
    reference: str = Field(..., alias="SampleRef")
    index: str = Field(..., alias="index")
    sample_name: str = Field(..., alias="SampleName")
    control: str = Field(..., alias="Control")
    recipe: str = Field(..., alias="Recipe")
    operator: str = Field(..., alias="Operator")
    project: str = Field(..., alias="Project")
    second_index: str = Field(..., alias="index2")


class SampleBcl2Fastq(NovaSeqSample):
    sample_id: str = Field(..., alias="SampleID")
    project: str = Field(..., alias="Project")


class SampleDragen(NovaSeqSample):
    sample_id: str = Field(..., alias="Sample_ID")
    project: str = Field(..., alias="Sample_Project")


class SampleSheet(BaseModel):
    type: str
    samples: List[NovaSeqSample]


class SampleSheetBcl2Fastq(SampleSheet):
    samples: List[SampleBcl2Fastq]


class SampleSheetDragen(SampleSheet):
    samples: List[SampleDragen]
