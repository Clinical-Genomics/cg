import logging
from collections import defaultdict

from pydantic import BaseModel, ConfigDict, Field

from cg.apps.demultiplex.sample_sheet.validators import SampleId
from cg.constants.constants import GenomeVersion
from cg.constants.demultiplexing import (
    SampleSheetBcl2FastqSections,
    SampleSheetBCLConvertSections,
)

LOG = logging.getLogger(__name__)


class FlowCellSample(BaseModel):
    """Base class for flow cell samples."""

    lane: int
    sample_id: SampleId
    index: str
    index2: str = ""
    model_config = ConfigDict(populate_by_name=True, extra="ignore")


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

    sample_id: SampleId = Field(
        ..., alias=SampleSheetBcl2FastqSections.Data.SAMPLE_INTERNAL_ID_BCL2FASTQ.value
    )
    project: str = Field(
        ..., alias=SampleSheetBcl2FastqSections.Data.SAMPLE_PROJECT_BCL2FASTQ.value
    )


class FlowCellSampleBCLConvert(FlowCellSample):
    """Class that represents a NovaSeqX flow cell sample."""

    lane: int = Field(..., alias=SampleSheetBCLConvertSections.Data.LANE.value)
    sample_id: SampleId = Field(
        ..., alias=SampleSheetBCLConvertSections.Data.SAMPLE_INTERNAL_ID.value
    )
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
    samples: list[FlowCellSample]

    def get_non_pooled_lanes_and_samples(self) -> list[tuple[int, str]]:
        """Return tuples of non-pooled lane and sample ids."""
        non_pooled_lane_sample_id_pairs: list[tuple[int, str]] = []
        non_pooled_samples: list[FlowCellSample] = self.get_non_pooled_samples()
        for sample in non_pooled_samples:
            non_pooled_lane_sample_id_pairs.append((sample.lane, sample.sample_id))
        return non_pooled_lane_sample_id_pairs

    def get_non_pooled_samples(self) -> list[FlowCellSample]:
        """Return samples that are sequenced solo in their lane."""
        lane_samples = defaultdict(list)
        for sample in self.samples:
            lane_samples[sample.lane].append(sample)
        return [samples[0] for samples in lane_samples.values() if len(samples) == 1]

    def get_sample_ids(self) -> list[str]:
        """Return ids for samples in sheet."""
        sample_internal_ids: list[str] = []
        for sample in self.samples:
            sample_internal_ids.append(sample.sample_id)
        return list(set(sample_internal_ids))


class SampleSheetBcl2Fastq(SampleSheet):
    samples: list[FlowCellSampleBcl2Fastq]


class SampleSheetBCLConvert(SampleSheet):
    samples: list[FlowCellSampleBCLConvert]
