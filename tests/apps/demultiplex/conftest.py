import pytest

from cg.apps.demultiplex.sample_sheet.override_cycles_validator import OverrideCyclesValidator
from cg.apps.demultiplex.sample_sheet.sample_models import FlowCellSample


@pytest.fixture
def bcl_convert_samples_similar_index1() -> list[FlowCellSample]:
    """Return a list of three FlowCellSampleBCLConvert with updated indexes."""
    sample_1 = FlowCellSample(lane=1, sample_id="ACC123", index="CAGAAGAT", index2="GCGCAAGC")
    sample_2 = FlowCellSample(lane=1, sample_id="ACC456", index="CAGAAGAG", index2="CAATGTAT")
    sample_3 = FlowCellSample(lane=2, sample_id="ACC789", index="AAGCGATA", index2="AACCGCAA")
    return [sample_1, sample_2, sample_3]


@pytest.fixture
def bcl_convert_samples_similar_index2() -> list[FlowCellSample]:
    """Return a list of three FlowCellSampleBCLConvert with updated indexes."""
    sample_1 = FlowCellSample(lane=1, sample_id="ACC123", index="GCGCAAGC", index2="CAATGTAC")
    sample_2 = FlowCellSample(lane=1, sample_id="ACC456", index="CAATGTAT", index2="CAATGTAT")
    sample_3 = FlowCellSample(lane=2, sample_id="ACC789", index="AAGCGATA", index2="AACCGCAA")
    return [sample_1, sample_2, sample_3]


# Sample sheet validation


@pytest.fixture
def novaseq6000_flow_cell_sample_1() -> FlowCellSample:
    """Return a NovaSeq sample."""
    return FlowCellSample(
        lane=1,
        sample_id="ACC7628A68",
        index="ATTCCACACT",
        index2="TGGTCTTGTT",
    )


@pytest.fixture
def novaseq6000_flow_cell_sample_2() -> FlowCellSample:
    """Return a NovaSeq sample."""
    return FlowCellSample(
        lane=2,
        sample_id="ACC7628A1",
        index="ATTCCACACT",
        index2="TGGTCTTGTT",
    )


@pytest.fixture
def novaseq6000_flow_cell_sample_no_dual_index() -> FlowCellSample:
    """Return a NovaSeq sample without dual indexes."""
    return FlowCellSample(
        lane=2,
        sample_id="ACC7628A1",
        index="ATTCCACACT",
    )


@pytest.fixture
def index1_8_nt_sequence_from_lims() -> str:
    """Return an index 1 sequence."""
    return "GTCTACAC"


@pytest.fixture
def index2_8_nt_sequence_from_lims() -> str:
    """Return an index 2 sequence."""
    return "GCCAAGGT"


@pytest.fixture
def index1_10_nt_sequence_from_lims() -> str:
    """Return an index 1 sequence."""
    return "CCGGTTCATG"


@pytest.fixture
def index2_10_nt_sequence_from_lims() -> str:
    """Return an index 2 sequence."""
    return "CAAGACGTCT"


@pytest.fixture
def raw_index_sequence(
    index1_8_nt_sequence_from_lims: str, index2_8_nt_sequence_from_lims: str
) -> str:
    """Return a raw index."""
    return f"{index1_8_nt_sequence_from_lims}-{index2_8_nt_sequence_from_lims}"


@pytest.fixture
def bcl_convert_flow_cell_sample(raw_index_sequence: str) -> FlowCellSample:
    """Return a BCL Convert sample."""
    return FlowCellSample(lane=1, index=raw_index_sequence, sample_id="ACC123")


@pytest.fixture
def override_cycles_validator() -> OverrideCyclesValidator:
    """Return an override cycles validator without any initialised attribute."""
    return OverrideCyclesValidator()


@pytest.fixture
def processed_flow_cell_sample_8_index(
    index1_8_nt_sequence_from_lims: str, index2_8_nt_sequence_from_lims: str
) -> dict[str, str]:
    """Return a BCL Convert sample with processed 8-nt indexes and no override cycles."""
    return {
        "Lane": 1,
        "Sample_ID": "ACC123",
        "Index": index1_8_nt_sequence_from_lims,
        "Index2": index2_8_nt_sequence_from_lims,
    }


@pytest.fixture
def processed_flow_cell_sample_10_index(
    index1_10_nt_sequence_from_lims: str, index2_10_nt_sequence_from_lims: str
) -> dict[str, str]:
    """Return a BCL Convert sample with processed 10-nt indexes and no override cycles."""
    return {
        "Lane": 1,
        "Sample_ID": "ACC123",
        "Index": index1_10_nt_sequence_from_lims,
        "Index2": index2_10_nt_sequence_from_lims,
    }


@pytest.fixture
def forward_index2_cycle_processed_flow_cell_8_nt_sample(
    processed_flow_cell_sample_8_index: dict[str, str],
) -> dict[str, str]:
    """Return a BCL Convert sample with processed 8-nt indexes and forward index 2 cycle."""
    processed_flow_cell_sample_8_index["OverrideCycles"] = "Y151;I8N2;I8N2;Y151"
    return processed_flow_cell_sample_8_index


@pytest.fixture
def reverse_index2_cycle_processed_flow_cell_8_nt_sample(
    processed_flow_cell_sample_8_index: dict[str, str],
) -> dict[str, str]:
    """Return a BCL Convert sample with processed 8-nt indexes and reversed index 2 cycle."""
    processed_flow_cell_sample_8_index["OverrideCycles"] = "Y151;I8N2;N2I8;Y151"
    return processed_flow_cell_sample_8_index


@pytest.fixture
def processed_flow_cell_10_nt_sample(
    processed_flow_cell_sample_10_index: dict[str, str],
) -> dict[str, str]:
    """Return a BCL Convert sample with processed 10-nt indexes."""
    processed_flow_cell_sample_10_index["OverrideCycles"] = "Y151;I10;I10;Y151"
    return processed_flow_cell_sample_10_index
