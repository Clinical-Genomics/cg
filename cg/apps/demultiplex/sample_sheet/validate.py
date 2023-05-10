import logging
from pathlib import Path
from typing import Dict, List, Union
from pydantic import parse_obj_as
from typing_extensions import Literal

from cg.apps.demultiplex.sample_sheet.models import (
    NovaSeqSample,
    SampleSheet,
    SampleBcl2Fastq,
    SampleDragen,
)
from cg.constants.constants import FileFormat
from cg.constants.demultiplexing import BclConverter
from cg.exc import SampleSheetError
from cg.io.controller import ReadFile

LOG = logging.getLogger(__name__)


def validate_samples_are_unique(samples: List[NovaSeqSample]) -> None:
    """Validate that each sample only exists once."""
    sample_ids: set = set()
    for sample in samples:
        sample_id: str = sample.sample_id.split("_")[0]
        if sample_id in sample_ids:
            message: str = f"Sample {sample.sample_id} exists multiple times in sample sheet"
            LOG.warning(message)
            raise SampleSheetError(message)
        sample_ids.add(sample_id)


def get_samples_by_lane(samples: List[NovaSeqSample]) -> Dict[int, List[NovaSeqSample]]:
    """Group and return samples by lane."""
    LOG.info("Order samples by lane")
    sample_by_lane: Dict[int, List[NovaSeqSample]] = {}
    for sample in samples:
        if sample.lane not in sample_by_lane:
            sample_by_lane[sample.lane] = []
        sample_by_lane[sample.lane].append(sample)
    return sample_by_lane


def validate_samples_unique_per_lane(samples: List[NovaSeqSample]) -> None:
    """Validate that each sample only exists once per lane in a sample sheet."""

    sample_by_lane: Dict[int, List[NovaSeqSample]] = get_samples_by_lane(samples)
    for lane, lane_samples in sample_by_lane.items():
        LOG.info(f"Validate that samples are unique in lane {lane}")
        validate_samples_are_unique(samples=lane_samples)


def get_raw_samples(sample_sheet: List[List[str]]) -> List[Dict[str, str]]:
    """Return the samples in a sample sheet as a list of dictionaries."""
    header: List[str] = []
    raw_samples: List[Dict[str, str]] = []

    for line in sample_sheet:
        # Skip lines that are too short to contain samples
        if len(line) <= 5:
            continue
        if line[0] == "FCID":
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


def get_sample_sheet(
    sample_sheet: List[List[str]], sheet_type: Literal["2500", "SP", "S2", "S4"], bcl_converter: str
) -> SampleSheet:
    """Parse and validate a sample sheet.

    return the information as a SampleSheet object
    """
    novaseq_sample = {BclConverter.BCL2FASTQ: SampleBcl2Fastq, BclConverter.DRAGEN: SampleDragen}
    raw_samples: List[Dict[str, str]] = get_raw_samples(sample_sheet=sample_sheet)
    sample_type: Union[SampleBcl2Fastq, SampleDragen] = novaseq_sample[bcl_converter]
    samples = parse_obj_as(List[sample_type], raw_samples)
    validate_samples_unique_per_lane(samples)
    return SampleSheet(type=sheet_type, samples=samples)


def get_sample_sheet_from_file(
    infile: Path, sheet_type: Literal["2500", "SP", "S2", "S4"], bcl_converter: str
) -> SampleSheet:
    """Parse and validate a sample sheet from file."""
    csv_file_content: List[List[str]] = ReadFile.get_content_from_file(
        file_format=FileFormat.CSV, file_path=infile
    )
    return get_sample_sheet(
        sample_sheet=csv_file_content, sheet_type=sheet_type, bcl_converter=bcl_converter
    )
