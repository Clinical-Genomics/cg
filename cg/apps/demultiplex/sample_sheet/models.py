import logging
from collections import defaultdict
from typing import List

from pydantic import BaseModel, ConfigDict, Extra, Field

from cg.apps.demultiplex.sample_sheet.validators import is_valid_sample_internal_id
from cg.constants.constants import GenomeVersion
from cg.constants.demultiplexing import (
    SampleSheetBcl2FastqSections,
    SampleSheetBCLConvertSections,
)

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

    flowcell_id: str = Field("", alias=SampleSheetBcl2FastqSections.Data.FLOW_CELL_ID.value)
    lane: int = Field(..., alias=SampleSheetBcl2FastqSections.Data.LANE.value)
    sample_ref: str = Field(
        GenomeVersion.hg19.value, alias=SampleSheetBcl2FastqSections.Data.SAMPLE_REFERENCE.value
    )
    index: str = Field(..., alias=SampleSheetBcl2FastqSections.Data.INDEX_1.value)
    index2: str = Field("", alias=SampleSheetBcl2FastqSections.Data.INDEX_2.value)
    sample_name: str = Field(..., alias=SampleSheetBcl2FastqSections.Data.SAMPLE_NAME.value)
    control: str = Field("N", alias=SampleSheetBcl2FastqSections.Data.CONTROL.value)
    recipe: str = Field("R1", alias=SampleSheetBcl2FastqSections.Data.RECIPE.value)
    operator: str = Field("script", alias=SampleSheetBcl2FastqSections.Data.OPERATOR.value)

    sample_id: str = Field(
        ..., alias=SampleSheetBcl2FastqSections.Data.SAMPLE_INTERNAL_ID_BCL2FASTQ.value
    )
    project: str = Field(
        ..., alias=SampleSheetBcl2FastqSections.Data.SAMPLE_PROJECT_BCL2FASTQ.value
    )


class FlowCellSampleBCLConvert(FlowCellSample):
    """Class that represents a NovaSeqX flow cell sample."""

    lane: int = Field(..., alias=SampleSheetBCLConvertSections.Data.LANE.value)
    sample_id: str = Field(..., alias=SampleSheetBCLConvertSections.Data.SAMPLE_INTERNAL_ID.value)
    index: str = Field(..., alias=SampleSheetBCLConvertSections.Data.INDEX_1.value)
    index2: str = Field("", alias=SampleSheetBCLConvertSections.Data.INDEX_2.value)
    override_cycles: str = Field("", alias=SampleSheetBCLConvertSections.Data.OVERRIDE_CYCLES.value)
    adapter_read_1: str = Field("", alias=SampleSheetBCLConvertSections.Data.ADAPTER_READ_1.value)
    adapter_read_2: str = Field("", alias=SampleSheetBCLConvertSections.Data.ADAPTER_READ_2.value)
    barcode_mismatches_1: int = Field(
        1, alias=SampleSheetBCLConvertSections.Data.BARCODE_MISMATCHES_1.value
    )
    barcode_mismatches_2: int = Field(
        1, alias=SampleSheetBCLConvertSections.Data.BARCODE_MISMATCHES_2.value
    )


class SampleSheet(BaseModel):
    samples: List[FlowCellSample]

    def get_non_pooled_samples(self) -> List[FlowCellSample]:
        """Return samples that are sequenced solo in their lane."""
        lane_samples = defaultdict(list)
        for sample in self.samples:
            lane_samples[sample.lane].append(sample)

        return [samples[0] for samples in lane_samples.values() if len(samples) == 1]

    def get_sample_ids(self) -> List[str]:
        """Return ids for samples in sheet."""
        sample_internal_ids: List[str] = []
        for sample in self.samples:
            sample_internal_id: str = sample.sample_id.split("_")[0]
            if is_valid_sample_internal_id(sample_internal_id):
                sample_internal_ids.append(sample_internal_id)
        return list(set(sample_internal_ids))


class SampleSheetBcl2Fastq(SampleSheet):
    samples: List[FlowCellSampleBcl2Fastq]


class SampleSheetBCLConvert(SampleSheet):
    samples: List[FlowCellSampleBCLConvert]
