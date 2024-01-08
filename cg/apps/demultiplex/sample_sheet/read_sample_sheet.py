import logging
from pathlib import Path
from typing import Type

from pydantic import TypeAdapter

from cg.apps.demultiplex.sample_sheet.sample_models import (
    FlowCellSample,
    FlowCellSampleBcl2Fastq,
    FlowCellSampleBCLConvert,
)
from cg.apps.demultiplex.sample_sheet.sample_sheet_models import SampleSheet
from cg.constants.constants import FileFormat
from cg.constants.demultiplexing import SampleSheetBcl2FastqSections, SampleSheetBCLConvertSections
from cg.exc import SampleSheetError
from cg.io.controller import ReadFile

LOG = logging.getLogger(__name__)


def validate_samples_are_unique(samples: list[FlowCellSample]) -> None:
    """Validate that each sample only exists once."""
    sample_ids: set = set()
    for sample in samples:
        sample_id: str = sample.sample_id.split("_")[0]
        if sample_id in sample_ids:
            message: str = f"Sample {sample.sample_id} exists multiple times in sample sheet"
            LOG.warning(message)
            raise SampleSheetError(message)
        sample_ids.add(sample_id)


def validate_samples_unique_per_lane(samples: list[FlowCellSample]) -> None:
    """Validate that each sample only exists once per lane in a sample sheet."""
    sample_by_lane: dict[int, list[FlowCellSample]] = get_samples_by_lane(samples)
    for lane, lane_samples in sample_by_lane.items():
        LOG.debug(f"Validate that samples are unique in lane: {lane}")
        validate_samples_are_unique(samples=lane_samples)


def get_sample_sheet_from_file(infile: Path) -> SampleSheet:
    """Parse and validate a sample sheet from file."""
    sample_sheet_content: list[list[str]] = ReadFile.get_content_from_file(
        file_format=FileFormat.CSV, file_path=infile
    )
    sample_type: Type[FlowCellSample] = get_sample_type(infile)

    return get_validated_sample_sheet(
        sample_sheet_content=sample_sheet_content,
        sample_type=sample_type,
    )


def get_sample_type(sample_sheet_path: Path) -> Type[FlowCellSample]:
    """Returns the sample type based on the header of the given sample sheet."""
    sample_sheet_content: list[list[str]] = ReadFile.get_content_from_file(
        file_format=FileFormat.CSV, file_path=sample_sheet_path
    )
    for row in sample_sheet_content:
        if not row:
            continue
        if SampleSheetBCLConvertSections.Data.HEADER in row[0]:
            LOG.info("Sample sheet was generated for BCL Convert")
            return FlowCellSampleBCLConvert
        if SampleSheetBcl2FastqSections.Data.HEADER in row[0]:
            LOG.info("Sample sheet was generated for BCL2FASTQ")
            return FlowCellSampleBcl2Fastq
    raise SampleSheetError("Could not determine sample sheet type")


def get_validated_sample_sheet(
    sample_sheet_content: list[list[str]],
    sample_type: Type[FlowCellSample],
) -> SampleSheet:
    """Return a validated sample sheet object."""
    raw_samples: list[dict[str, str]] = get_raw_samples(sample_sheet_content=sample_sheet_content)
    adapter = TypeAdapter(list[sample_type])
    samples = adapter.validate_python(raw_samples)
    validate_samples_unique_per_lane(samples=samples)
    return SampleSheet(samples=samples)


def get_raw_samples(sample_sheet_content: list[list[str]]) -> list[dict[str, str]]:
    """Return the samples in a sample sheet as a list of dictionaries."""
    header: list[str] = []
    raw_samples: list[dict[str, str]] = []

    for line in sample_sheet_content:
        # Skip lines that are too short to contain samples
        if len(line) <= 5:
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
