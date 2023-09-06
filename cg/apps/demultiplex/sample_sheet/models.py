import logging
from pydantic import ConfigDict, BaseModel, Extra, Field
from typing import List

from cg.constants.constants import GenomeVersion
from cg.constants.demultiplexing import SampleSheetNovaSeq6000Sections, SampleSheetV2Sections

LOG = logging.getLogger(__name__)


class FlowCellSample(BaseModel):
    """Base class for flow cell samples."""

    lane: int
    sample_id: str
    index: str
    index2: str = ""
    model_config = ConfigDict(populate_by_name=True, extra=Extra.ignore)


class FlowCellSampleBcl2Fastq(FlowCellSample):
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

    sample_id: str = Field(
        ..., alias=SampleSheetNovaSeq6000Sections.Data.SAMPLE_INTERNAL_ID_BCL2FASTQ.value
    )
    project: str = Field(
        ..., alias=SampleSheetNovaSeq6000Sections.Data.SAMPLE_PROJECT_BCL2FASTQ.value
    )


class FlowCellSampleBCLConvert(FlowCellSample):
    """Class that represents a NovaSeqX flow cell sample."""

    lane: int = Field(..., alias=SampleSheetV2Sections.Data.LANE.value)
    sample_id: str = Field(..., alias=SampleSheetV2Sections.Data.SAMPLE_INTERNAL_ID.value)
    index: str = Field(..., alias=SampleSheetV2Sections.Data.INDEX_1.value)
    index2: str = Field("", alias=SampleSheetV2Sections.Data.INDEX_2.value)
    adapter_read_1: str = Field("", alias=SampleSheetV2Sections.Data.ADAPTER_READ_1.value)
    adapter_read_2: str = Field("", alias=SampleSheetV2Sections.Data.ADAPTER_READ_2.value)
    barcode_mismatches_1: int = Field(
        1, alias=SampleSheetV2Sections.Data.BARCODE_MISMATCHES_1.value
    )
    barcode_mismatches_2: int = Field(
        1, alias=SampleSheetV2Sections.Data.BARCODE_MISMATCHES_2.value
    )


class SampleSheet(BaseModel):
    samples: List[FlowCellSample]


class SampleSheetBcl2Fastq(SampleSheet):
    samples: List[FlowCellSampleBcl2Fastq]


class SampleSheetDragen(SampleSheet):
    samples: List[FlowCellSampleBCLConvert]
