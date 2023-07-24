import logging
from pathlib import Path
from typing import Dict, List, Type
from pydantic.v1 import parse_obj_as

from cg.apps.demultiplex.sample_sheet.models import FlowCellSample, SampleSheet
from cg.constants.constants import FileFormat
from cg.constants.demultiplexing import (
    SampleSheetNovaSeq6000Sections,
    SampleSheetNovaSeqXSections,
)

from cg.exc import SampleSheetError
from cg.io.controller import ReadFile
import re

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


def validate_samples_unique_per_lane(samples: List[FlowCellSample]) -> None:
    """Validate that each sample only exists once per lane in a sample sheet."""
    sample_by_lane: Dict[int, List[FlowCellSample]] = get_samples_by_lane(samples)
    for lane, lane_samples in sample_by_lane.items():
        LOG.info(f"Validate that samples are unique in lane {lane}")
        validate_samples_are_unique(samples=lane_samples)


def is_valid_sample_internal_id(sample_internal_id: str) -> bool:
    """
    Check if a sample internal id has the correct structure:
    starts with three letters followed by at least three digits.
    """
    return bool(re.search(r"^[A-Za-z]{3}\d{3}", sample_internal_id))


def get_sample_sheet_from_file(
    infile: Path,
    flow_cell_sample_type: Type[FlowCellSample],
) -> SampleSheet:
    """Parse and validate a sample sheet from file."""
    sample_sheet_content: List[List[str]] = ReadFile.get_content_from_file(
        file_format=FileFormat.CSV, file_path=infile
    )
    return get_validated_sample_sheet(
        sample_sheet_content=sample_sheet_content,
        sample_type=flow_cell_sample_type,
    )


def get_validated_sample_sheet(
    sample_sheet_content: List[List[str]],
    sample_type: Type[FlowCellSample],
) -> SampleSheet:
    """Return a validated sample sheet object."""
    raw_samples: List[Dict[str, str]] = get_raw_samples(sample_sheet_content=sample_sheet_content)
    samples = parse_obj_as(List[sample_type], raw_samples)
    validate_samples_unique_per_lane(samples=samples)
    return SampleSheet(samples=samples)


def get_raw_samples(sample_sheet_content: List[List[str]]) -> List[Dict[str, str]]:
    """Return the samples in a sample sheet as a list of dictionaries."""
    header: List[str] = []
    raw_samples: List[Dict[str, str]] = []

    for line in sample_sheet_content:
        # Skip lines that are too short to contain samples
        if len(line) <= 5:
            continue
        if line[0] in [
            SampleSheetNovaSeq6000Sections.Data.FLOW_CELL_ID.value,
            SampleSheetNovaSeqXSections.Data.LANE.value,
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
    samples: List[FlowCellSample],
) -> Dict[int, List[FlowCellSample]]:
    """Group and return samples by lane."""
    LOG.debug("Order samples by lane")
    sample_by_lane: Dict[int, List[FlowCellSample]] = {}
    for sample in samples:
        if sample.lane not in sample_by_lane:
            sample_by_lane[sample.lane] = []
        sample_by_lane[sample.lane].append(sample)
    return sample_by_lane


def get_sample_internal_ids_from_sample_sheet(
    sample_sheet_path: Path, flow_cell_sample_type: Type[FlowCellSample]
) -> List[str]:
    """Return the sample internal ids for samples in the sample sheet."""
    sample_sheet = get_sample_sheet_from_file(
        infile=sample_sheet_path, flow_cell_sample_type=flow_cell_sample_type
    )
    sample_internal_ids: List[str] = []
    for sample in sample_sheet.samples:
        sample_internal_id = sample.sample_id.split("_")[0]
        if is_valid_sample_internal_id(sample_internal_id=sample_internal_id):
            sample_internal_ids.append(sample_internal_id)
    return list(set(sample_internal_ids))
