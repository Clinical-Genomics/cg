from pathlib import Path
from typing import List

import pytest

from cg.apps.demultiplex.sample_sheet.index import Index
from cg.apps.demultiplex.sample_sheet.sample_sheet_creator import (
    SampleSheetCreatorV1,
    SampleSheetCreatorV2,
)
from cg.apps.demultiplex.sample_sheet.models import (
    FlowCellSampleNovaSeq6000Bcl2Fastq,
    FlowCellSampleNovaSeq6000Dragen,
    FlowCellSampleNovaSeqX,
)
from cg.constants.demultiplexing import BclConverter, SampleSheetNovaSeq6000Sections
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData


@pytest.fixture(name="output_dirs_bcl2fastq")
def fixture_output_dirs_bcl2fastq(demultiplexed_runs: Path) -> Path:
    """Return the output path a dir with flow cells that have finished demultiplexing using
    bcl2fastq."""
    return Path(demultiplexed_runs, BclConverter.BCL2FASTQ)


@pytest.fixture(name="demux_run_dir_bcl2fastq")
def fixture_demux_run_dir_bcl2fastq(flow_cell_runs_dir: Path) -> Path:
    """Return the path to a dir with flowcells ready for demultiplexing"""
    return Path(flow_cell_runs_dir, BclConverter.BCL2FASTQ)


@pytest.fixture(name="demux_run_dir_dragen")
def fixture_demux_run_dir_dragen(flow_cell_runs_dir: Path) -> Path:
    """Return the path to a dir with flowcells ready for demultiplexing"""
    return Path(flow_cell_runs_dir, BclConverter.DRAGEN)


@pytest.fixture(name="index_obj")
def fixture_index_obj() -> Index:
    return Index(name="C07 - UDI0051", sequence="AACAGGTT-ATACCAAG")


@pytest.fixture(name="valid_index")
def fixture_valid_index_() -> Index:
    """Return a valid index."""
    return Index(name="C07 - UDI0051", sequence="AACAGGTT-ATACCAAG")


@pytest.fixture(name="lims_novaseq_bcl2fastq_samples")
def fixture_lims_novaseq_bcl2fastq_samples(
    lims_novaseq_samples_raw: List[dict],
) -> List[FlowCellSampleNovaSeq6000Bcl2Fastq]:
    """Return a list of parsed Bcl2fastq flow cell samples"""
    return [FlowCellSampleNovaSeq6000Bcl2Fastq(**sample) for sample in lims_novaseq_samples_raw]


@pytest.fixture(name="lims_novaseq_dragen_samples")
def fixture_lims_novaseq_dragen_samples(
    lims_novaseq_samples_raw: List[dict],
) -> List[FlowCellSampleNovaSeq6000Dragen]:
    """Return a list of parsed Dragen flow cell samples"""
    return [FlowCellSampleNovaSeq6000Dragen(**sample) for sample in lims_novaseq_samples_raw]


@pytest.fixture(name="lims_novaseq_x_samples")
def fixture_lims_novaseq_x_samples(
    lims_novaseq_samples_raw: List[dict],
) -> List[FlowCellSampleNovaSeqX]:
    """Return a list of parsed NovaSeqX flow cell samples"""
    return [FlowCellSampleNovaSeqX(**sample) for sample in lims_novaseq_samples_raw]


@pytest.fixture(name="novaseq_bcl2fastq_sample_sheet_creator")
def fixture_novaseq_bcl2fastq_sample_sheet_creator(
    bcl2fastq_flow_cell: FlowCellDirectoryData,
    lims_novaseq_bcl2fastq_samples: List[FlowCellSampleNovaSeq6000Bcl2Fastq],
) -> SampleSheetCreatorV1:
    """Returns a sample sheet creator for version 1 sample sheets with bcl2fastq format."""
    return SampleSheetCreatorV1(
        flow_cell=bcl2fastq_flow_cell,
        lims_samples=lims_novaseq_bcl2fastq_samples,
        bcl_converter=BclConverter.BCL2FASTQ,
    )


@pytest.fixture(name="novaseq_dragen_sample_sheet_creator")
def fixture_novaseq_dragen_sample_sheet_creator(
    dragen_flow_cell: FlowCellDirectoryData,
    lims_novaseq_dragen_samples: List[FlowCellSampleNovaSeq6000Dragen],
) -> SampleSheetCreatorV1:
    """Returns a sample sheet creator for version 1 sample sheets with dragen format."""
    return SampleSheetCreatorV1(
        flow_cell=dragen_flow_cell,
        lims_samples=lims_novaseq_dragen_samples,
        bcl_converter=BclConverter.DRAGEN,
    )


@pytest.fixture(name="novaseq_x_sample_sheet_creator")
def fixture_novaseq_x_sample_sheet_creator(
    novaseq_x_flow_cell: FlowCellDirectoryData,
    lims_novaseq_x_samples: List[FlowCellSampleNovaSeqX],
) -> SampleSheetCreatorV2:
    """Returns a sample sheet creator for version 2 sample sheets."""
    return SampleSheetCreatorV2(
        flow_cell=novaseq_x_flow_cell,
        lims_samples=lims_novaseq_x_samples,
        bcl_converter=BclConverter.DRAGEN,
    )


# Sample sheet validation


@pytest.fixture(name="sample_sheet_line_sample_1")
def fixture_sample_sheet_line_sample_1() -> List[str]:
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


@pytest.fixture(name="sample_sheet_line_sample_2")
def fixture_sample_sheet_line_sample_2() -> List[str]:
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


@pytest.fixture(name="sample_sheet_bcl2fastq_data_header")
def fixture_sample_sheet_bcl2fastq_data_header() -> List[List[str]]:
    """Return the content of a Bcl2fastq sample sheet data header without samples."""
    return [
        [SampleSheetNovaSeq6000Sections.Data.HEADER],
        [
            SampleSheetNovaSeq6000Sections.Data.FLOW_CELL_ID.value,
            SampleSheetNovaSeq6000Sections.Data.LANE.value,
            SampleSheetNovaSeq6000Sections.Data.SAMPLE_INTERNAL_ID_BCL2FASTQ.value,
            SampleSheetNovaSeq6000Sections.Data.SAMPLE_REFERENCE.value,
            SampleSheetNovaSeq6000Sections.Data.INDEX_1.value,
            SampleSheetNovaSeq6000Sections.Data.INDEX_2.value,
            SampleSheetNovaSeq6000Sections.Data.SAMPLE_NAME.value,
            SampleSheetNovaSeq6000Sections.Data.CONTROL.value,
            SampleSheetNovaSeq6000Sections.Data.RECIPE.value,
            SampleSheetNovaSeq6000Sections.Data.OPERATOR.value,
            SampleSheetNovaSeq6000Sections.Data.SAMPLE_PROJECT_BCL2FASTQ.value,
        ],
    ]


@pytest.fixture(name="sample_sheet_samples_no_header")
def fixture_sample_sheet_no_sample_header(
    sample_sheet_line_sample_1: List[str], sample_sheet_line_sample_2: List[str]
) -> List[List[str]]:
    """Return the content of a sample sheet with samples but without a sample header."""
    return [
        [SampleSheetNovaSeq6000Sections.Data.HEADER],
        sample_sheet_line_sample_1,
        sample_sheet_line_sample_2,
    ]


@pytest.fixture(name="valid_sample_sheet_bcl2fastq")
def fixture_valid_sample_sheet_bcl2fastq(
    sample_sheet_bcl2fastq_data_header: List[List[str]],
    sample_sheet_line_sample_1: List[str],
    sample_sheet_line_sample_2: List[str],
) -> List[List[str]]:
    """Return the content of a valid Bcl2fastq sample sheet."""
    return sample_sheet_bcl2fastq_data_header + [
        sample_sheet_line_sample_1,
        sample_sheet_line_sample_2,
    ]


@pytest.fixture(name="sample_sheet_bcl2fastq_duplicate_same_lane")
def fixture_sample_sheet_bcl2fastq_duplicate_same_lane(
    valid_sample_sheet_bcl2fastq: List[List[str]], sample_sheet_line_sample_2: List[str]
) -> List[List[str]]:
    """Return the content of a Bcl2fastq sample sheet with a duplicated sample in the same lane."""
    valid_sample_sheet_bcl2fastq.append(sample_sheet_line_sample_2)
    return valid_sample_sheet_bcl2fastq


@pytest.fixture(name="sample_sheet_bcl2fastq_duplicate_different_lane")
def fixture_sample_sheet_bcl2fastq_duplicate_different_lane(
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


@pytest.fixture(name="valid_sample_sheet_dragen")
def fixture_valid_sample_sheet_dragen(
    sample_sheet_line_sample_1: List[str], sample_sheet_line_sample_2: List[str]
) -> List[List[str]]:
    """Return the content of a valid Dragen sample sheet."""
    return [
        [SampleSheetNovaSeq6000Sections.Data.HEADER],
        [
            SampleSheetNovaSeq6000Sections.Data.FLOW_CELL_ID.value,
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


@pytest.fixture(name="sample_sheet_dragen_duplicate_same_lane")
def fixture_sample_sheet_dragen_duplicate_same_lane(
    valid_sample_sheet_dragen: List[List[str]], sample_sheet_line_sample_2: List[str]
) -> List[List[str]]:
    """Return the content of a Dragen sample sheet with a duplicated sample in the same lane."""
    valid_sample_sheet_dragen.append(sample_sheet_line_sample_2)
    return valid_sample_sheet_dragen


@pytest.fixture(name="sample_sheet_dragen_duplicate_different_lane")
def fixture_sample_sheet_dragen_duplicate_different_lane(
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


@pytest.fixture(name="valid_sample_sheet_bcl2fastq_path")
def fixture_valid_sample_sheet_bcl2fastq_path() -> Path:
    """Return the path to a NovaSeq S2 sample sheet, used in bcl2fastq demultiplexing."""
    return Path("tests", "fixtures", "apps", "demultiplexing", "SampleSheetS2_Bcl2Fastq.csv")


@pytest.fixture(name="valid_sample_sheet_dragen_path")
def fixture_valid_sample_sheet_dragen_path() -> Path:
    """Return the path to a NovaSeq S2 sample sheet, used in dragen demultiplexing."""
    return Path("tests", "fixtures", "apps", "demultiplexing", "SampleSheetS2_Dragen.csv")


@pytest.fixture(name="novaseq6000_flow_cell_sample_1")
def fixture_novaseq6000_flow_cell_sample_1() -> FlowCellSampleNovaSeq6000Bcl2Fastq:
    """Return a NovaSeq sample."""
    return FlowCellSampleNovaSeq6000Bcl2Fastq(
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
def fixture_novaseq6000_flow_cell_sample_2() -> FlowCellSampleNovaSeq6000Bcl2Fastq:
    """Return a NovaSeq sample."""
    return FlowCellSampleNovaSeq6000Bcl2Fastq(
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
def fixture_novaseq_x_flow_cell_sample_before_adapt_indexes() -> FlowCellSampleNovaSeqX:
    """Return a NovaSeqX sample."""
    return FlowCellSampleNovaSeqX(
        Lane=2,
        Sample_ID="ACC7628A1",
        index="ATTCCACACT-TGGTCTTGTT",
    )


@pytest.fixture(name="novaseq6000_flow_cell_sample_no_dual_index")
def fixture_novaseq6000_flow_cell_sample_no_dual_index() -> FlowCellSampleNovaSeq6000Bcl2Fastq:
    """Return a NovaSeq sample without dual indexes."""
    return FlowCellSampleNovaSeq6000Bcl2Fastq(
        FCID="HWHMWDMXX",
        Lane=2,
        SampleID="ACC7628A1",
        index="ATTCCACACT",
        SampleName="814206",
        Project="814206",
    )


@pytest.fixture(name="novaseq6000_flow_cell_sample_before_adapt_indexes")
def fixture_novaseq6000_flow_cell_sample_before_adapt_indexes() -> (
    FlowCellSampleNovaSeq6000Bcl2Fastq
):
    """Return a NovaSeq sample without dual indexes."""
    return FlowCellSampleNovaSeq6000Bcl2Fastq(
        FCID="HWHMWDMXX",
        Lane=2,
        SampleID="ACC7628A1",
        index="ATTCCACACT-TGGTCTTGTT",
        SampleName="814206",
        Project="814206",
    )
