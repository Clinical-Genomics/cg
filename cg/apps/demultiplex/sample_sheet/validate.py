import logging
from pathlib import Path
from typing import Dict, List
from pydantic import parse_obj_as

from cg.apps.demultiplex.sample_sheet.models import SampleSheet, FlowCellSample
from cg.constants.constants import FileFormat
from cg.constants.demultiplexing import SampleSheetSections
from cg.exc import SampleSheetError
from cg.io.controller import ReadFile

LOG = logging.getLogger(__name__)


def validate_samples_are_unique(samples: List[FlowCellSample]) -> None:
    """Validate that each sample only exists once."""
    sample_ids: set = set()
    for sample in samples:
        sample_id: str = sample.sample_id.split("_")[0]
        if sample_id in sample_ids:
            message: str = f"Sample {sample.sample_id} exists multiple times in sample sheet"
            LOG.warning(message)
            raise SampleSheetError(message)
        sample_ids.add(sample_id)


def get_samples_by_lane(samples: List[FlowCellSample]) -> Dict[int, List[FlowCellSample]]:
    """Group and return samples by lane."""
    LOG.info("Order samples by lane")
    sample_by_lane: Dict[int, List[FlowCellSample]] = {}
    for sample in samples:
        if sample.lane not in sample_by_lane:
            sample_by_lane[sample.lane] = []
        sample_by_lane[sample.lane].append(sample)
    return sample_by_lane


def validate_samples_unique_per_lane(samples: List[FlowCellSample]) -> None:
    """Validate that each sample only exists once per lane in a sample sheet."""

    sample_by_lane: Dict[int, List[FlowCellSample]] = get_samples_by_lane(samples)
    for lane, lane_samples in sample_by_lane.items():
        LOG.info(f"Validate that samples are unique in lane {lane}")
        validate_samples_are_unique(samples=lane_samples)


def get_raw_samples(sample_sheet_content: List[List[str]]) -> List[Dict[str, str]]:
    """Return the samples in a sample sheet as a list of dictionaries."""
    header: List[str] = []
    raw_samples: List[Dict[str, str]] = []
    found_header: bool = False

    for line in sample_sheet_content:
        if found_header:
            header = line
            found_header = False
            continue
        if SampleSheetSections.Data.HEADER in line:
            found_header = True
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


def validate_sample_sheet(
    sample_sheet_content: List[List[str]],
) -> SampleSheet:
    """Return a validated sample sheet object."""
    raw_samples: List[Dict[str, str]] = get_raw_samples(sample_sheet_content=sample_sheet_content)
    samples = parse_obj_as(List[FlowCellSample], raw_samples)
    validate_samples_unique_per_lane(samples=samples)
    return SampleSheet(samples=samples)


def get_sample_sheet_from_file(infile: Path) -> SampleSheet:
    """Parse and validate a sample sheet from file."""
    sample_sheet_content: List[List[str]] = ReadFile.get_content_from_file(
        file_format=FileFormat.CSV, file_path=infile
    )
    return validate_sample_sheet(sample_sheet_content=sample_sheet_content)
