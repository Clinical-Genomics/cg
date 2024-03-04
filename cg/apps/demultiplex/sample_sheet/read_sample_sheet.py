import logging
from typing import Type

from pydantic import TypeAdapter

from cg.apps.demultiplex.sample_sheet.sample_models import (
    FlowCellSample,
    FlowCellSampleBcl2Fastq,
    FlowCellSampleBCLConvert,
)
from cg.constants.demultiplexing import SampleSheetBcl2FastqSections, SampleSheetBCLConvertSections
from cg.exc import SampleSheetError

LOG = logging.getLogger(__name__)


def validate_samples_are_unique(samples: list[FlowCellSample]) -> None:
    """Validate that each sample only exists once."""
    sample_ids: set = set()
    for sample in samples:
        sample_id: str = sample.sample_id.split("_")[0]
        if sample_id in sample_ids:
            message: str = f"Sample {sample.sample_id} exists multiple times in sample sheet"
            LOG.error(message)
            raise SampleSheetError(message)
        sample_ids.add(sample_id)


def validate_samples_unique_per_lane(samples: list[FlowCellSample]) -> None:
    """Validate that each sample only exists once per lane in a sample sheet."""
    sample_by_lane: dict[int, list[FlowCellSample]] = get_samples_by_lane(samples)
    for lane, lane_samples in sample_by_lane.items():
        LOG.debug(f"Validate that samples are unique in lane: {lane}")
        validate_samples_are_unique(samples=lane_samples)


def get_sample_type_from_content(sample_sheet_content: list[list[str]]) -> Type[FlowCellSample]:
    """Returns the sample type identified from the sample sheet content."""
    for row in sample_sheet_content:
        if not row:
            continue
        if SampleSheetBCLConvertSections.Data.HEADER in row[0]:
            LOG.info("Sample sheet was generated for BCL Convert")
            return FlowCellSampleBCLConvert
        if SampleSheetBcl2FastqSections.Data.HEADER in row[0]:
            LOG.info("Sample sheet was generated for BCL2FASTQ")
            return FlowCellSampleBcl2Fastq
    message: str = "Could not determine sample sheet type"
    LOG.error(message)
    raise SampleSheetError(message)


def get_raw_samples_from_content(sample_sheet_content: list[list[str]]) -> list[dict[str, str]]:
    """Return the samples in a sample sheet as a list of dictionaries."""
    header: list[str] = []
    raw_samples: list[dict[str, str]] = []

    for line in sample_sheet_content:
        # Skip lines that are too short to contain samples
        if len(line) <= 4:
            continue
        if line[0] in [
            SampleSheetBcl2FastqSections.Data.FLOW_CELL_ID.value,
            SampleSheetBCLConvertSections.Data.LANE.value,
        ]:
            header = line
            continue
        if not header:
            continue
        raw_samples.append(dict(zip(header, line)))
    if not header:
        message = "Could not find header in sample sheet"
        LOG.warning(message)
        raise SampleSheetError(message)
    if not raw_samples:
        message = "Could not find any samples in sample sheet"
        LOG.warning(message)
        raise SampleSheetError(message)
    return raw_samples


def get_samples_by_lane(
    samples: list[FlowCellSample],
) -> dict[int, list[FlowCellSample]]:
    """Group and return samples by lane."""
    LOG.debug("Order samples by lane")
    sample_by_lane: dict[int, list[FlowCellSample]] = {}
    for sample in samples:
        if sample.lane not in sample_by_lane:
            sample_by_lane[sample.lane] = []
        sample_by_lane[sample.lane].append(sample)
    return sample_by_lane


def get_flow_cell_samples_from_content(
    sample_sheet_content: list[list[str]],
    sample_type: Type[FlowCellSample] | None = None,
) -> list[FlowCellSample]:
    """
    Return the samples in a sample sheet as a list of FlowCellSample objects.
    Raises:
        ValidationError: if the samples do not have the correct attributes based on their model.
    """
    if not sample_type:
        sample_type: Type[FlowCellSample] = get_sample_type_from_content(sample_sheet_content)
    raw_samples: list[dict[str, str]] = get_raw_samples_from_content(
        sample_sheet_content=sample_sheet_content
    )
    adapter = TypeAdapter(list[sample_type])
    return adapter.validate_python(raw_samples)
