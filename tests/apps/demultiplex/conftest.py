from pathlib import Path

import pytest

from cg.apps.demultiplex.sample_sheet.sample_models import (
    FlowCellSampleBcl2Fastq,
    FlowCellSampleBCLConvert,
)
from cg.apps.demultiplex.sample_sheet.sample_sheet_creator import (
    SampleSheetCreatorBcl2Fastq,
    SampleSheetCreatorBCLConvert,
)
from cg.constants.demultiplexing import SampleSheetBcl2FastqSections
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData


@pytest.fixture
def bcl_convert_samples_similar_index1() -> list[FlowCellSampleBCLConvert]:
    """Return a list of three FlowCellSampleBCLConvert with updated indexes."""
    sample_1 = FlowCellSampleBCLConvert(
        lane=1, sample_id="ACC123", index="CAGAAGAT", index2="GCGCAAGC"
    )
    sample_2 = FlowCellSampleBCLConvert(
        lane=1, sample_id="ACC456", index="CAGAAGAG", index2="CAATGTAT"
    )
    sample_3 = FlowCellSampleBCLConvert(
        lane=2, sample_id="ACC789", index="AAGCGATA", index2="AACCGCAA"
    )
    return [sample_1, sample_2, sample_3]


@pytest.fixture
def bcl_convert_samples_similar_index2() -> list[FlowCellSampleBCLConvert]:
    """Return a list of three FlowCellSampleBCLConvert with updated indexes."""
    sample_1 = FlowCellSampleBCLConvert(
        lane=1, sample_id="ACC123", index="GCGCAAGC", index2="CAATGTAC"
    )
    sample_2 = FlowCellSampleBCLConvert(
        lane=1, sample_id="ACC456", index="CAATGTAT", index2="CAATGTAT"
    )
    sample_3 = FlowCellSampleBCLConvert(
        lane=2, sample_id="ACC789", index="AAGCGATA", index2="AACCGCAA"
    )
    return [sample_1, sample_2, sample_3]


@pytest.fixture
def bcl2fastq_sample_sheet_creator(
    novaseq_6000_pre_1_5_kits_flow_cell_bcl2fastq: FlowCellDirectoryData,
    novaseq_6000_pre_1_5_kits_bcl2fastq_lims_samples: list[FlowCellSampleBcl2Fastq],
) -> SampleSheetCreatorBcl2Fastq:
    """Returns a sample sheet creator for version 1 sample sheets with bcl2fastq format."""
    return SampleSheetCreatorBcl2Fastq(
        flow_cell=novaseq_6000_pre_1_5_kits_flow_cell_bcl2fastq,
        lims_samples=novaseq_6000_pre_1_5_kits_bcl2fastq_lims_samples,
    )


# Sample sheet validation


@pytest.fixture
def sample_sheet_line_sample_1() -> list[str]:
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
def sample_sheet_line_sample_2() -> list[str]:
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
def sample_sheet_bcl2fastq_data_header() -> list[list[str]]:
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
    sample_sheet_line_sample_1: list[str], sample_sheet_line_sample_2: list[str]
) -> list[list[str]]:
    """Return the content of a sample sheet with samples but without a sample header."""
    return [
        [SampleSheetBcl2FastqSections.Data.HEADER],
        sample_sheet_line_sample_1,
        sample_sheet_line_sample_2,
    ]


@pytest.fixture
def valid_sample_sheet_bcl2fastq(
    sample_sheet_bcl2fastq_data_header: list[list[str]],
    sample_sheet_line_sample_1: list[str],
    sample_sheet_line_sample_2: list[str],
) -> list[list[str]]:
    """Return the content of a valid Bcl2fastq sample sheet."""
    return sample_sheet_bcl2fastq_data_header + [
        sample_sheet_line_sample_1,
        sample_sheet_line_sample_2,
    ]


@pytest.fixture
def sample_sheet_bcl2fastq_duplicate_same_lane(
    valid_sample_sheet_bcl2fastq: list[list[str]], sample_sheet_line_sample_2: list[str]
) -> list[list[str]]:
    """Return the content of a Bcl2fastq sample sheet with a duplicated sample in the same lane."""
    valid_sample_sheet_bcl2fastq.append(sample_sheet_line_sample_2)
    return valid_sample_sheet_bcl2fastq


@pytest.fixture
def sample_sheet_bcl2fastq_duplicate_different_lane(
    valid_sample_sheet_bcl2fastq: list[list[str]],
) -> list[list[str]]:
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
    sample_sheet_line_sample_1: list[str], sample_sheet_line_sample_2: list[str]
) -> list[list[str]]:
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
    valid_sample_sheet_dragen: list[list[str]], sample_sheet_line_sample_2: list[str]
) -> list[list[str]]:
    """Return the content of a Dragen sample sheet with a duplicated sample in the same lane."""
    valid_sample_sheet_dragen.append(sample_sheet_line_sample_2)
    return valid_sample_sheet_dragen


@pytest.fixture
def sample_sheet_dragen_duplicate_different_lane(
    valid_sample_sheet_dragen: list[list[str]],
) -> list[list[str]]:
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


@pytest.fixture
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


@pytest.fixture
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


@pytest.fixture
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


@pytest.fixture
def index1_sequence_from_lims() -> str:
    """Return an index 1 sequence."""
    return "GTCTACAC"


@pytest.fixture
def index2_sequence_from_lims() -> str:
    """Return an index 2 sequence."""
    return "GCCAAGGT"


@pytest.fixture
def raw_index_sequence(index1_sequence_from_lims: str, index2_sequence_from_lims: str) -> str:
    """Return a raw index."""
    return f"{index1_sequence_from_lims}-{index2_sequence_from_lims}"


@pytest.fixture
def bcl_convert_flow_cell_sample(raw_index_sequence: str) -> FlowCellSampleBCLConvert:
    """Return a BCL Convert sample."""
    return FlowCellSampleBCLConvert(lane=1, index=raw_index_sequence, sample_id="ACC123")


@pytest.fixture
def bcl_convert_sample_sheet_path(demultiplexed_runs: Path):
    return Path(
        demultiplexed_runs,
        "230504_A00689_0804_BHY7FFDRX2",
        "SampleSheet.csv",
    )


@pytest.fixture
def bcl2fastq_sample_sheet_path(demultiplexed_runs: Path):
    return Path(
        demultiplexed_runs,
        "170407_ST-E00198_0209_BHHKVCALXX",
        "SampleSheet.csv",
    )
