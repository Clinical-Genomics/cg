import logging
from pathlib import Path
from typing import Dict, List, Union
from pydantic import parse_obj_as
from typing_extensions import Literal

from cg.apps.demultiplex.sample_sheet.base import (
    Sample,
    SampleSheet,
    NovaSeqSampleBcl2Fastq,
    NovaSeqSampleDragen,
    SampleSheetError,
)
from cg.constants.demultiplexing import BclConverter

LOG = logging.getLogger(__name__)


def validate_unique_sample(samples: List[Sample]) -> None:
    """Validate that each sample only exists once."""
    sample_ids: set = set()
    for sample in samples:
        sample_id: str = sample.sample_id.split("_")[0]
        if sample_id in sample_ids:
            message: str = f"Sample {sample.sample_id} exists multiple times in sample sheet"
            LOG.warning(message)
            raise SampleSheetError(message)
        sample_ids.add(sample_id)


def samples_by_lane(samples: List[Sample]) -> Dict[int, List[Sample]]:
    """Group samples by lane."""
    LOG.info("Order samples by lane")
    sample_by_lane: Dict[int, List[Sample]] = {}
    for sample in samples:
        if sample.lane not in sample_by_lane:
            sample_by_lane[sample.lane] = []
        sample_by_lane[sample.lane].append(sample)
    return sample_by_lane


def validate_samples_unique_per_lane(samples: List[Sample]) -> None:
    """Validate that each sample only exists once per lane in a sample sheet."""

    sample_by_lane: Dict[int, List[Sample]] = samples_by_lane(samples)
    for lane, lane_samples in sample_by_lane.items():
        LOG.info("Validate that samples are unique in lane %s", lane)
        validate_unique_sample(lane_samples)


def get_raw_samples(sample_sheet: str) -> List[Dict[str, str]]:
    sample_sheet_rows: List[str] = sample_sheet.split("\n")
    header: List[str] = []
    raw_samples: List[Dict[str, str]] = []
    for line in sample_sheet_rows:
        # Skip empty lines
        if not len(line) > 5:
            continue
        # Check if we are on the header row
        line = line.strip()
        if line.startswith("FCID"):
            header = line.split(",")
            continue
        # Skip rows until header is found
        if not header:
            continue
        raw_samples.append(dict(zip(header, line.split(","))))
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
    sample_sheet: str, sheet_type: Literal["2500", "SP", "S2", "S4"], bcl_converter: str
) -> SampleSheet:
    """Parse and validate a sample sheet

    return the information as a SampleSheet object
    """
    # Skip the [data] header
    novaseq_sample = {"bcl2fastq": NovaSeqSampleBcl2Fastq, "dragen": NovaSeqSampleDragen}
    raw_samples: List[Dict[str, str]] = get_raw_samples(sample_sheet)
    sample_type = Sample if sheet_type == "2500" else novaseq_sample[bcl_converter]
    samples = parse_obj_as(List[sample_type], raw_samples)
    validate_samples_unique_per_lane(samples)
    return SampleSheet(type=sheet_type, samples=samples)


def get_sample_sheet_from_file(
    infile: Path, sheet_type: Literal["2500", "SP", "S2", "S4"], bcl_converter: str
) -> SampleSheet:
    """Parse and validate a sample sheet from file."""
    with open(infile, "r") as csv_file:
        # Skip the [data] header
        sample_sheet: SampleSheet = get_sample_sheet(
            sample_sheet=csv_file.read(), sheet_type=sheet_type, bcl_converter=bcl_converter
        )

    return sample_sheet
