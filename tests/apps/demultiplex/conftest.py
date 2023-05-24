from pathlib import Path
from typing import List

import pytest

from cg.apps.demultiplex.sample_sheet.index import Index
from cg.apps.demultiplex.sample_sheet.novaseq_sample_sheet import SampleSheetCreator
from cg.apps.demultiplex.sample_sheet.models import FlowCellSampleBcl2Fastq, FlowCellSampleDragen
from cg.constants.demultiplexing import SampleSheetHeaderColumnNames
from cg.models.demultiplex.flow_cell import FlowCell
from cg.models.demultiplex.run_parameters import RunParameters


@pytest.fixture(name="output_dirs_bcl2fastq")
def fixture_output_dirs_bcl2fastq(demultiplexed_runs: Path) -> Path:
    """Return the output path a dir with flow cells that have finished demultiplexing using
    bcl2fastq."""
    return Path(demultiplexed_runs, "bcl2fastq")


@pytest.fixture(name="demux_run_dir_bcl2fastq")
def fixture_demux_run_dir_bcl2fastq(flow_cell_runs_dir: Path) -> Path:
    """Return the path to a dir with flowcells ready for demultiplexing"""
    return Path(flow_cell_runs_dir, "bcl2fastq")


@pytest.fixture(name="demux_run_dir_dragen")
def fixture_demux_run_dir_dragen(flow_cell_runs_dir: Path) -> Path:
    """Return the path to a dir with flowcells ready for demultiplexing"""
    return Path(flow_cell_runs_dir, "dragen")


@pytest.fixture(name="index_obj")
def fixture_index_obj() -> Index:
    return Index(name="C07 - UDI0051", sequence="AACAGGTT-ATACCAAG")


@pytest.fixture(name="lims_novaseq_bcl2fastq_samples")
def fixture_lims_novaseq_bcl2fastq_samples(
    lims_novaseq_samples_raw: List[dict],
) -> List[FlowCellSampleBcl2Fastq]:
    """Return a list of parsed flow cell samples"""
    return [FlowCellSampleBcl2Fastq(**sample) for sample in lims_novaseq_samples_raw]


@pytest.fixture(name="lims_novaseq_dragen_samples")
def fixture_lims_novaseq_dragen_samples(
    lims_novaseq_samples_raw: List[dict],
) -> List[FlowCellSampleDragen]:
    """Return a list of parsed flowcell samples"""
    return [FlowCellSampleDragen(**sample) for sample in lims_novaseq_samples_raw]


@pytest.fixture(name="novaseq_run_parameters_object")
def fixture_novaseq_run_parameters_object(novaseq_run_parameters: Path) -> RunParameters:
    return RunParameters(novaseq_run_parameters)


@pytest.fixture(name="novaseq_bcl2fastq_sample_sheet_object")
def fixture_novaseq_bcl2fastq_sample_sheet_object(
    bcl2fastq_flow_cell: FlowCell,
    lims_novaseq_bcl2fastq_samples: List[FlowCellSampleBcl2Fastq],
) -> SampleSheetCreator:
    return SampleSheetCreator(
        flow_cell=bcl2fastq_flow_cell,
        lims_samples=lims_novaseq_bcl2fastq_samples,
        bcl_converter="bcl2fastq",
    )


@pytest.fixture(name="novaseq_dragen_sample_sheet_object")
def fixture_novaseq_dragen_sample_sheet_object(
    dragen_flow_cell: FlowCell,
    lims_novaseq_dragen_samples: List[FlowCellSampleDragen],
    novaseq_run_parameters_object: RunParameters,
) -> SampleSheetCreator:
    return SampleSheetCreator(
        flow_cell=dragen_flow_cell,
        lims_samples=lims_novaseq_dragen_samples,
        bcl_converter="dragen",
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
        [SampleSheetHeaderColumnNames.DATA],
        [
            SampleSheetHeaderColumnNames.FLOW_CELL_ID,
            "Lane",
            "SampleID",
            "SampleRef",
            "index",
            "index2",
            "SampleName",
            "Control",
            "Recipe",
            "Operator",
            "Project",
        ],
    ]


@pytest.fixture(name="sample_sheet_samples_no_header")
def fixture_sample_sheet_no_sample_header(
    sample_sheet_line_sample_1: List[str], sample_sheet_line_sample_2: List[str]
) -> List[List[str]]:
    """Return the content of a sample sheet with samples but without a sample header."""
    return [
        [SampleSheetHeaderColumnNames.DATA],
        sample_sheet_line_sample_1,
        sample_sheet_line_sample_2,
    ]


@pytest.fixture(name="valid_sample_sheet_bcl2fastq")
def fixture_valid_sample_sheet_bcl2fastq(
    sample_sheet_line_sample_1: List[str], sample_sheet_line_sample_2: List[str]
) -> List[List[str]]:
    """Return the content of a valid Bcl2fastq sample sheet."""
    return [
        [SampleSheetHeaderColumnNames.DATA],
        [
            SampleSheetHeaderColumnNames.FLOW_CELL_ID,
            "Lane",
            "SampleID",
            "SampleRef",
            "index",
            "index2",
            "SampleName",
            "Control",
            "Recipe",
            "Operator",
            "Project",
        ],
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
        [SampleSheetHeaderColumnNames.DATA],
        [
            SampleSheetHeaderColumnNames.FLOW_CELL_ID,
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


@pytest.fixture(name="novaseq_sample_1")
def fixture_novaseq_sample_1() -> FlowCellSampleBcl2Fastq:
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


@pytest.fixture(name="novaseq_sample_2")
def fixture_novaseq_sample_2() -> FlowCellSampleBcl2Fastq:
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
