import logging
from pydantic import BaseModel, Field
from typing import List

LOG = logging.getLogger(__name__)


class ModelError(Exception):

    """
    Base exception for the package.
    """

    def __init__(self, message: str):
        super(ModelError, self).__init__()
        self.message = message


class SampleSheetError(ModelError):
    """Raised when something is wrong with the order form."""


class BaseSample(BaseModel):
    """This model is used when creating sample sheets."""

    flow_cell: str
    lane: int
    sample_id: str
    reference: str
    index: str
    second_index: str = None
    sample_name: str
    control: str
    recipe: str
    operator: str
    project: str


class Sample(BaseModel):
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


class NovaSeqSample(Sample):
    """This model is used when parsing/validating existing novaseq sample sheets."""

    second_index: str = Field(..., alias="index2")


class NovaSeqSampleBcl2Fastq(NovaSeqSample):
    sample_id: str = Field(..., alias="SampleID")
    project: str = Field(..., alias="Project")


class NovaSeqSampleDragen(NovaSeqSample):
    sample_id: str = Field(..., alias="Sample_ID")
    project: str = Field(..., alias="Sample_Project")


class SampleSheet(BaseModel):
    type: str
    samples: List[Sample]


class SampleSheetBcl2Fastq(SampleSheet):
    samples: List[NovaSeqSampleBcl2Fastq]


class SampleSheetDragen(SampleSheet):
    samples: List[NovaSeqSampleDragen]
