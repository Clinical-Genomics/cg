from pathlib import Path
from typing import List

import pytest

from cg.apps.demultiplex.sample_sheet.index import Index
from cg.constants.demultiplexing import SampleSheetSections
from cg.apps.demultiplex.sample_sheet.novaseq_sample_sheet import SampleSheetCreator
from cg.apps.demultiplex.sample_sheet.models import FlowCellSample
from cg.models.demultiplex.flow_cell import FlowCell


@pytest.fixture(name="index_obj")
def fixture_index_obj() -> Index:
    return Index(name="C07 - UDI0051", sequence="AACAGGTT-ATACCAAG")


@pytest.fixture(name="flow_cell_samples")
def fixture_flow_cell_samples(
    lims_novaseq_samples_raw: List[dict],
) -> List[FlowCellSample]:
    """Return a list of parsed flow cell samples"""
    return [FlowCellSample(**sample) for sample in lims_novaseq_samples_raw]


@pytest.fixture(name="novaseq_bcl2fastq_sample_sheet_object")
def fixture_novaseq_bcl2fastq_sample_sheet_object(
    bcl2fastq_flow_cell: FlowCell,
    flow_cell_samples: List[FlowCellSample],
) -> SampleSheetCreator:
    return SampleSheetCreator(
        flow_cell=bcl2fastq_flow_cell,
        lims_samples=flow_cell_samples,
        bcl_converter="bcl2fastq",
    )


@pytest.fixture(name="sample_sheet_creator")
def fixture_sample_sheet_creator(
    novaseq_6000_flow_cell: FlowCell,
    flow_cell_samples: List[FlowCellSample],
) -> SampleSheetCreator:
    return SampleSheetCreator(
        flow_cell=novaseq_6000_flow_cell,
        lims_samples=flow_cell_samples,
        bcl_converter="dragen",
    )


@pytest.fixture(name="novaseq_dragen_sample_sheet_object")
def fixture_novaseq_dragen_sample_sheet_object(
    dragen_flow_cell: FlowCell,
    flow_cell_samples: List[FlowCellSample],
) -> SampleSheetCreator:
    return SampleSheetCreator(
        flow_cell=dragen_flow_cell,
        lims_samples=flow_cell_samples,
        bcl_converter="dragen",
    )


# Sample sheet validation


@pytest.fixture(name="sample_sheet_line_sample_1")
def fixture_sample_sheet_line_sample_1() -> List[str]:
    """Return the line in the sample sheet corresponding to a sample."""
    return [
        "6",
        "ACC11193A15",
        "GTAGTACAGT",
        "GAGACGGTTG",
        "Y151;I10;I10;Y151",
        "",
        "",
        0,
        0,
    ]


@pytest.fixture(name="sample_sheet_line_sample_2")
def fixture_sample_sheet_line_sample_2() -> List[str]:
    """Return the line in the sample sheet corresponding to a sample."""
    return [
        "2",
        "ACC11913A20",
        "GTAGTACAGT",
        "GAGACGGTTG",
        "Y151;I10;I10;Y151",
        "",
        "",
        0,
        0,
    ]


@pytest.fixture(name="sample_sheet_data_header")
def fixture_sample_sheet_data_header() -> List[List[str]]:
    """Return the content of a sample sheet data header without samples."""
    return [
        [SampleSheetSections.Data.HEADER],
        [
            "Lane",
            "Sample_ID",
            "Index",
            "Index2",
            "OverrideCycles",
            "AdapterRead1",
            "AdapterRead2",
            "BarcodeMismatchesIndex1",
            "BarcodeMismatchesIndex2",
        ],
    ]


@pytest.fixture(name="sample_sheet_samples_no_header")
def fixture_sample_sheet_no_sample_header(
    sample_sheet_line_sample_1: List[str], sample_sheet_line_sample_2: List[str]
) -> List[List[str]]:
    """Return the content of a sample sheet with samples but without a sample header."""
    return [
        sample_sheet_line_sample_1,
        sample_sheet_line_sample_2,
    ]


@pytest.fixture(name="valid_sample_sheet_content")
def fixture_valid_sample_sheet_content(
    sample_sheet_line_sample_1: List[str],
    sample_sheet_line_sample_2: List[str],
) -> List[List[str]]:
    """Return the content of a valid Bcl2fastq sample sheet."""
    return [
        ["[Header],"],
        ["FileFormatVersion", "2"],
        ["RunName", "HYG7YDSXX"],
        ["InstrumentPlatform", "NovaSeq6000Series"],
        ["IndexOrientation", "Forward"],
        ["[Reads]"],
        ["Read1Cycles", 151],
        ["Read2Cycles", 151],
        ["Index1Cycles", 10],
        ["Index2Cycles", 10],
        ["[BCLConvert_Settings]"],
        ["SoftwareVersion", "4.1.5"],
        ["FastqCompressionFormat", "gzip"],
        SampleSheetSections.Data.HEADER,
        [
            "Lane",
            "Sample_ID",
            "Index",
            "Index2",
            "OverrideCycles",
            "AdapterRead1",
            "AdapterRead2",
            "BarcodeMismatchesIndex1",
            "BarcodeMismatchesIndex2",
        ],
        sample_sheet_line_sample_1,
        sample_sheet_line_sample_2,
    ]


@pytest.fixture(name="sample_sheet_duplicate_same_lane")
def fixture_sample_sheet_duplicate_same_lane(
    valid_sample_sheet_content: List[List[str]], sample_sheet_line_sample_2: List[str]
) -> List[List[str]]:
    """Return the content of a sample sheet with a duplicated sample in the same lane."""
    valid_sample_sheet_content.append(sample_sheet_line_sample_2)
    return valid_sample_sheet_content


@pytest.fixture(name="sample_sheet_duplicate_different_lane")
def fixture_sample_sheet_duplicate_different_lane(
    valid_sample_sheet_content: List[List[str]],
) -> List[List[str]]:
    """Return the content of a sample sheet with a duplicated sample in a different lane."""
    valid_sample_sheet_content.append(
        [
            "1",
            "ACC11913A20",
            "GTAGTACAGT",
            "GAGACGGTTG",
            "Y151;I10;I10;Y151",
            "",
            "",
            0,
            0,
        ]
    )
    return valid_sample_sheet_content


@pytest.fixture(name="valid_sample_sheet_bcl2fastq_path")
def fixture_valid_sample_sheet_bcl2fastq_path() -> Path:
    """Return the path to a NovaSeq S2 sample sheet, used in bcl2fastq demultiplexing."""
    return Path("tests", "fixtures", "apps", "demultiplexing", "SampleSheetS2_Bcl2Fastq.csv")


@pytest.fixture(name="valid_sample_sheet_dragen_path")
def fixture_valid_sample_sheet_dragen_path() -> Path:
    """Return the path to a NovaSeq S2 sample sheet, used in dragen demultiplexing."""
    return Path("tests", "fixtures", "apps", "demultiplexing", "SampleSheetS2_Dragen.csv")


@pytest.fixture(name="novaseq_sample_1")
def fixture_novaseq_sample_1() -> FlowCellSample:
    """Return a NovaSeq sample."""
    return FlowCellSample(
        lane=1,
        sample_id="ACC7628A68",
        index="ATTCCACACT",
        index2="TGGTCTTGTT",
        override_cycles="Y151;I10;I10;Y151",
    )


@pytest.fixture(name="novaseq_sample_2")
def fixture_novaseq_sample_2() -> FlowCellSample:
    """Return a NovaSeq sample."""
    return FlowCellSample(
        lane=2,
        sample_id="ACC7628A1",
        index="ATTCCACACT",
        index2="TGGTCTTGTT",
        override_cycles="Y151;I10;I10;Y151",
    )
