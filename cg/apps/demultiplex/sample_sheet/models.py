import logging
from pydantic.v1 import BaseModel, Extra, Field
from typing import List

from cg.constants.constants import GenomeVersion
from cg.constants.demultiplexing import SampleSheetNovaSeq6000Sections, SampleSheetNovaSeqXSections

LOG = logging.getLogger(__name__)


class FlowCellSample(BaseModel):
    """Base class for flow cell samples."""

    lane: int
    sample_id: str
    index: str
    index2: str = ""

    class Config:
        allow_population_by_field_name = True
        extra = Extra.ignore


class FlowCellSampleNovaSeq6000(FlowCellSample):
    """Base class for NovaSeq6000 flow cell samples."""

    flowcell_id: str = Field("", alias=SampleSheetNovaSeq6000Sections.Data.FLOW_CELL_ID.value)
    lane: int = Field(..., alias=SampleSheetNovaSeq6000Sections.Data.LANE.value)
    sample_ref: str = Field(
        GenomeVersion.hg19.value, alias=SampleSheetNovaSeq6000Sections.Data.SAMPLE_REFERENCE.value
    )
    index: str = Field(..., alias=SampleSheetNovaSeq6000Sections.Data.INDEX_1.value)
    index2: str = Field("", alias=SampleSheetNovaSeq6000Sections.Data.INDEX_2.value)
    sample_name: str = Field(..., alias=SampleSheetNovaSeq6000Sections.Data.SAMPLE_NAME.value)
    control: str = Field("N", alias=SampleSheetNovaSeq6000Sections.Data.CONTROL.value)
    recipe: str = Field("R1", alias=SampleSheetNovaSeq6000Sections.Data.RECIPE.value)
    operator: str = Field("script", alias=SampleSheetNovaSeq6000Sections.Data.OPERATOR.value)


class FlowCellSampleNovaSeqX(FlowCellSample):
    """Class that represents a NovaSeqX flow cell sample."""

    lane: int = Field(..., alias=SampleSheetNovaSeqXSections.Data.LANE.value)
    sample_id: str = Field(..., alias=SampleSheetNovaSeqXSections.Data.SAMPLE_INTERNAL_ID.value)
    index: str = Field(..., alias=SampleSheetNovaSeqXSections.Data.INDEX_1.value)
    index2: str = Field("", alias=SampleSheetNovaSeqXSections.Data.INDEX_2.value)
    adapter_read_1: str = Field("", alias=SampleSheetNovaSeqXSections.Data.ADAPTER_READ_1.value)
    adapter_read_2: str = Field("", alias=SampleSheetNovaSeqXSections.Data.ADAPTER_READ_2.value)
    barcode_mismatches_1: int = Field(
        1, alias=SampleSheetNovaSeqXSections.Data.BARCODE_MISMATCHES_1.value
    )
    barcode_mismatches_2: int = Field(
        1, alias=SampleSheetNovaSeqXSections.Data.BARCODE_MISMATCHES_2.value
    )


class FlowCellSampleNovaSeq6000Bcl2Fastq(FlowCellSampleNovaSeq6000):
    """Class that represents a NovaSeq6000 Bcl2fastq flow cell sample."""

    sample_id: str = Field(
        ..., alias=SampleSheetNovaSeq6000Sections.Data.SAMPLE_INTERNAL_ID_BCL2FASTQ.value
    )
    project: str = Field(
        ..., alias=SampleSheetNovaSeq6000Sections.Data.SAMPLE_PROJECT_BCL2FASTQ.value
    )


class FlowCellSampleNovaSeq6000Dragen(FlowCellSampleNovaSeq6000):
    """Class that represents a NovaSeq6000 Dragen flow cell sample."""

    sample_id: str = Field(
        ..., alias=SampleSheetNovaSeq6000Sections.Data.SAMPLE_INTERNAL_ID_BCLCONVERT.value
    )
    project: str = Field(
        ..., alias=SampleSheetNovaSeq6000Sections.Data.SAMPLE_PROJECT_BCLCONVERT.value
    )


class SampleSheet(BaseModel):
    samples: List[FlowCellSample]


class SampleSheetBcl2Fastq(SampleSheet):
    samples: List[FlowCellSampleNovaSeq6000Bcl2Fastq]


class SampleSheetDragen(SampleSheet):
    samples: List[FlowCellSampleNovaSeq6000Dragen]
