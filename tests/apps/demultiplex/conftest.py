from typing import List

import pytest

from cg.apps.demultiplex.sample_sheet.index import Index
from cg.apps.demultiplex.sample_sheet.sample_sheet_creator import (
    SampleSheetCreatorBcl2Fastq,
    SampleSheetCreatorBCLConvert,
)
from cg.apps.demultiplex.sample_sheet.models import (
    FlowCellSampleBcl2Fastq,
    FlowCellSampleBCLConvert,
)
from cg.constants.demultiplexing import SampleSheetBcl2FastqSections
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData


@pytest.fixture
def valid_index() -> Index:
    """Return a valid index."""
    return Index(name="C07 - UDI0051", sequence="AACAGGTT-ATACCAAG")


@pytest.fixture
def lims_novaseq_bcl2fastq_samples(
    lims_novaseq_samples_raw: List[dict],
) -> List[FlowCellSampleBcl2Fastq]:
    """Return a list of parsed Bcl2fastq flow cell samples"""
    return [FlowCellSampleBcl2Fastq(**sample) for sample in lims_novaseq_samples_raw]


@pytest.fixture
def lims_novaseq_dragen_samples(
    lims_novaseq_samples_raw: List[dict],
) -> List[FlowCellSampleBCLConvert]:
    """Return a list of parsed Dragen flow cell samples"""
    return [FlowCellSampleBCLConvert(**sample) for sample in lims_novaseq_samples_raw]


@pytest.fixture
def lims_novaseq_x_samples(
    lims_novaseq_samples_raw: List[dict],
) -> List[FlowCellSampleBCLConvert]:
    """Return a list of parsed NovaSeqX flow cell samples"""
    return [FlowCellSampleBCLConvert(**sample) for sample in lims_novaseq_samples_raw]


@pytest.fixture
def bcl2fastq_sample_sheet_creator(
    bcl2fastq_flow_cell: FlowCellDirectoryData,
    lims_novaseq_bcl2fastq_samples: List[FlowCellSampleBcl2Fastq],
) -> SampleSheetCreatorBcl2Fastq:
    """Returns a sample sheet creator for version 1 sample sheets with bcl2fastq format."""
    return SampleSheetCreatorBcl2Fastq(
        flow_cell=bcl2fastq_flow_cell,
        lims_samples=lims_novaseq_bcl2fastq_samples,
    )


@pytest.fixture
def bcl_convert_sample_sheet_creator(
    bcl_convert_flow_cell: FlowCellDirectoryData,
    lims_novaseq_dragen_samples: List[FlowCellSampleBCLConvert],
) -> SampleSheetCreatorBCLConvert:
    """Returns a sample sheet creator for version 2 sample sheets with dragen format."""
    return SampleSheetCreatorBCLConvert(
        flow_cell=bcl_convert_flow_cell,
        lims_samples=lims_novaseq_dragen_samples,
    )


# Sample sheet validation


@pytest.fixture
def sample_sheet_line_sample_1() -> List[str]:
    """Return the line in the sample sheet corresponding to a sample."""
    return [
        "HWHMWDMXX",
        "1",
        "ACC7628A68",
        "hg19",
        "ATTCCACACT",
        "TGGTCTTGTT",
        "814206",
        "N",
        "R1",
        "script",
        "814206",
    ]


@pytest.fixture
def sample_sheet_line_sample_2() -> List[str]:
    """Return the line in the sample sheet corresponding to a sample."""
    return [
        "HWHMWDMXX",
        "1",
        "ACC7628A1",
        "hg19",
        "AGTTAGCTGG",
        "GATGAGAATG",
        "814206",
        "N",
        "R1",
        "script",
        "814206",
    ]


@pytest.fixture
def sample_sheet_bcl2fastq_data_header() -> List[List[str]]:
    """Return the content of a Bcl2fastq sample sheet data header without samples."""
    return [
        [SampleSheetBcl2FastqSections.Data.HEADER],
        [
            SampleSheetBcl2FastqSections.Data.FLOW_CELL_ID.value,
            SampleSheetBcl2FastqSections.Data.LANE.value,
            SampleSheetBcl2FastqSections.Data.SAMPLE_INTERNAL_ID_BCL2FASTQ.value,
            SampleSheetBcl2FastqSections.Data.SAMPLE_REFERENCE.value,
            SampleSheetBcl2FastqSections.Data.INDEX_1.value,
            SampleSheetBcl2FastqSections.Data.INDEX_2.value,
            SampleSheetBcl2FastqSections.Data.SAMPLE_NAME.value,
            SampleSheetBcl2FastqSections.Data.CONTROL.value,
            SampleSheetBcl2FastqSections.Data.RECIPE.value,
            SampleSheetBcl2FastqSections.Data.OPERATOR.value,
            SampleSheetBcl2FastqSections.Data.SAMPLE_PROJECT_BCL2FASTQ.value,
        ],
    ]


@pytest.fixture
def sample_sheet_samples_no_header(
    sample_sheet_line_sample_1: List[str], sample_sheet_line_sample_2: List[str]
) -> List[List[str]]:
    """Return the content of a sample sheet with samples but without a sample header."""
    return [
        [SampleSheetBcl2FastqSections.Data.HEADER],
        sample_sheet_line_sample_1,
        sample_sheet_line_sample_2,
    ]


@pytest.fixture
def valid_sample_sheet_bcl2fastq(
    sample_sheet_bcl2fastq_data_header: List[List[str]],
    sample_sheet_line_sample_1: List[str],
    sample_sheet_line_sample_2: List[str],
) -> List[List[str]]:
    """Return the content of a valid Bcl2fastq sample sheet."""
    return sample_sheet_bcl2fastq_data_header + [
        sample_sheet_line_sample_1,
        sample_sheet_line_sample_2,
    ]


@pytest.fixture
def sample_sheet_bcl2fastq_duplicate_same_lane(
    valid_sample_sheet_bcl2fastq: List[List[str]], sample_sheet_line_sample_2: List[str]
) -> List[List[str]]:
    """Return the content of a Bcl2fastq sample sheet with a duplicated sample in the same lane."""
    valid_sample_sheet_bcl2fastq.append(sample_sheet_line_sample_2)
    return valid_sample_sheet_bcl2fastq


@pytest.fixture
def sample_sheet_bcl2fastq_duplicate_different_lane(
    valid_sample_sheet_bcl2fastq: List[List[str]],
) -> List[List[str]]:
    """Return the content of a Bcl2fastq sample sheet with a duplicated sample in a different lane."""
    valid_sample_sheet_bcl2fastq.append(
        [
            "HWHMWDMXX",
            "2",
            "ACC7628A1",
            "hg19",
            "AGTTAGCTGG",
            "GATGAGAATG",
            "814206",
            "N",
            "R1",
            "script",
            "814206",
        ]
    )
    return valid_sample_sheet_bcl2fastq


@pytest.fixture
def valid_sample_sheet_dragen(
    sample_sheet_line_sample_1: List[str], sample_sheet_line_sample_2: List[str]
) -> List[List[str]]:
    """Return the content of a valid Dragen sample sheet."""
    return [
        [SampleSheetBcl2FastqSections.Data.HEADER],
        [
            SampleSheetBcl2FastqSections.Data.FLOW_CELL_ID.value,
            "Lane",
            "Sample_ID",
            "SampleRef",
            "index",
            "index2",
            "SampleName",
            "Control",
            "Recipe",
            "Operator",
            "Sample_Project",
        ],
        sample_sheet_line_sample_1,
        sample_sheet_line_sample_2,
    ]


@pytest.fixture
def sample_sheet_dragen_duplicate_same_lane(
    valid_sample_sheet_dragen: List[List[str]], sample_sheet_line_sample_2: List[str]
) -> List[List[str]]:
    """Return the content of a Dragen sample sheet with a duplicated sample in the same lane."""
    valid_sample_sheet_dragen.append(sample_sheet_line_sample_2)
    return valid_sample_sheet_dragen


@pytest.fixture
def sample_sheet_dragen_duplicate_different_lane(
    valid_sample_sheet_dragen: List[List[str]],
) -> List[List[str]]:
    """Return the content of a Dragen sample sheet with a duplicated sample in a different lane."""
    valid_sample_sheet_dragen.append(
        [
            "HWHMWDMXX",
            "2",
            "ACC7628A1",
            "hg19",
            "AGTTAGCTGG",
            "GATGAGAATG",
            "814206",
            "N",
            "R1",
            "script",
            "814206",
        ]
    )
    return valid_sample_sheet_dragen


@pytest.fixture
def novaseq6000_flow_cell_sample_1() -> FlowCellSampleBcl2Fastq:
    """Return a NovaSeq sample."""
    return FlowCellSampleBcl2Fastq(
        FCID="HWHMWDMXX",
        Lane=1,
        SampleID="ACC7628A68",
        SampleRef="hg19",
        index="ATTCCACACT",
        index2="TGGTCTTGTT",
        SampleName="814206",
        Control="N",
        Recipe="R1",
        Operator="script",
        Project="814206",
    )


@pytest.fixture(name="novaseq6000_flow_cell_sample_2")
def novaseq6000_flow_cell_sample_2() -> FlowCellSampleBcl2Fastq:
    """Return a NovaSeq sample."""
    return FlowCellSampleBcl2Fastq(
        FCID="HWHMWDMXX",
        Lane=2,
        SampleID="ACC7628A1",
        SampleRef="hg19",
        index="ATTCCACACT",
        index2="TGGTCTTGTT",
        SampleName="814206",
        Control="N",
        Recipe="R1",
        Operator="script",
        Project="814206",
    )


@pytest.fixture(name="novaseq_x_flow_cell_sample_before_adapt_indexes")
def novaseq_x_flow_cell_sample_before_adapt_indexes() -> FlowCellSampleBCLConvert:
    """Return a NovaSeqX sample."""
    return FlowCellSampleBCLConvert(
        Lane=2,
        Sample_ID="ACC7628A1",
        index="ATTCCACACT-TGGTCTTGTT",
    )


@pytest.fixture(name="novaseq6000_flow_cell_sample_no_dual_index")
def novaseq6000_flow_cell_sample_no_dual_index() -> FlowCellSampleBcl2Fastq:
    """Return a NovaSeq sample without dual indexes."""
    return FlowCellSampleBcl2Fastq(
        FCID="HWHMWDMXX",
        Lane=2,
        SampleID="ACC7628A1",
        index="ATTCCACACT",
        SampleName="814206",
        Project="814206",
    )


@pytest.fixture(name="novaseq6000_flow_cell_sample_before_adapt_indexes")
def novaseq6000_flow_cell_sample_before_adapt_indexes() -> FlowCellSampleBcl2Fastq:
    """Return a NovaSeq sample without dual indexes."""
    return FlowCellSampleBcl2Fastq(
        FCID="HWHMWDMXX",
        Lane=2,
        SampleID="ACC7628A1",
        index="ATTCCACACT-TGGTCTTGTT",
        SampleName="814206",
        Project="814206",
    )
