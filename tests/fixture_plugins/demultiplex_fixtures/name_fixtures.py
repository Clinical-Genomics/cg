from pathlib import Path

import pytest

from cg.meta.demultiplex.housekeeper_storage_functions import (
    add_and_include_sample_sheet_path_to_housekeeper,
)


@pytest.fixture(scope="session")
def flow_cell_name_demultiplexed_with_bcl2fastq() -> str:
    """Return the name of a flow cell that has been demultiplexed with BCL2Fastq."""
    return "HHKVCALXX"


@pytest.fixture(scope="session")
def flow_cell_name_demultiplexed_with_bcl_convert() -> str:
    return "HY7FFDRX2"


@pytest.fixture
def bclconvert_flow_cell_dir_name(demux_post_processing_api) -> str:
    """Return a flow cell name that has been demultiplexed with bclconvert."""
    flow_cell_dir_name = "230504_A00689_0804_BHY7FFDRX2"
    flow_cell_path = Path(demux_post_processing_api.demultiplexed_runs_dir, flow_cell_dir_name)

    add_and_include_sample_sheet_path_to_housekeeper(
        flow_cell_directory=flow_cell_path,
        flow_cell_name="HY7FFDRX2",
        hk_api=demux_post_processing_api.hk_api,
    )
    return flow_cell_dir_name


@pytest.fixture
def flow_cell_name() -> str:
    """Return flow cell name."""
    return "HVKJCDRXX"


@pytest.fixture(scope="session")
def bcl2fastq_flow_cell_full_name() -> str:
    """Return full flow cell name."""
    return "201203_D00483_0200_AHVKJCDRXX"


@pytest.fixture(scope="session")
def bcl_convert_flow_cell_full_name() -> str:
    """Return the full name of a bcl_convert flow cell."""
    return "211101_A00187_0615_AHLG5GDRZZ"


@pytest.fixture(scope="session")
def hiseq_x_single_index_flow_cell_id() -> str:
    """Return the id of a HiSeqX single-index flow cell."""
    return "HJCFFALXX"


@pytest.fixture(scope="session")
def hiseq_x_single_index_flow_cell_name(hiseq_x_single_index_flow_cell_id) -> str:
    """Return the full name of a HiSeqX flow cell with only one index."""
    return f"170517_ST-E00266_0210_B{hiseq_x_single_index_flow_cell_id}"


@pytest.fixture(scope="session")
def hiseq_x_dual_index_flow_cell_id() -> str:
    """Return the id of a HiSeqX flow cell with two indexes."""
    return "HL32LCCXY"


@pytest.fixture(scope="session")
def hiseq_x_dual_index_flow_cell_name(hiseq_x_dual_index_flow_cell_id: str) -> str:
    """Return the full name of a HiSeqX flow cell with two indexes."""
    return f"180508_ST-E00269_0269_A{hiseq_x_dual_index_flow_cell_id}"


@pytest.fixture(scope="session")
def hiseq_2500_dual_index_flow_cell_id() -> str:
    """Return the id of a HiSeq2500 flow cell with double indexes."""
    return "HM2LNBCX2"


@pytest.fixture(scope="session")
def hiseq_2500_dual_index_flow_cell_name(hiseq_2500_dual_index_flow_cell_id: str) -> str:
    """Return the full name of a HiSeq2500 flow cell with double indexes."""
    return f"181005_D00410_0735_B{hiseq_2500_dual_index_flow_cell_id}"


@pytest.fixture(scope="session")
def hiseq_2500_custom_index_flow_cell_id() -> str:
    """Return the id of a HiSeq2500 flow cell with double indexes."""
    return "HGYFNBCX2"


@pytest.fixture(scope="session")
def hiseq_2500_custom_index_flow_cell_name(hiseq_2500_custom_index_flow_cell_id) -> str:
    """Return the full name of a HiSeq2500 flow cell with double indexes."""
    return f"180509_D00450_0598_B{hiseq_2500_custom_index_flow_cell_id}"


@pytest.fixture(scope="session")
def novaseq_6000_pre_1_5_kits_flow_cell_id() -> str:
    """Return the id of a NovaSeqX flow cell."""
    return "HLYWYDSXX"


@pytest.fixture(scope="session")
def novaseq_6000_pre_1_5_kits_flow_cell_full_name(
    novaseq_6000_pre_1_5_kits_flow_cell_id: str,
) -> str:
    """Return the full name of a NovaSeqX flow cell."""
    return f"190927_A00689_0069_B{novaseq_6000_pre_1_5_kits_flow_cell_id}"


@pytest.fixture(scope="session")
def novaseq_6000_post_1_5_kits_flow_cell_id() -> str:
    """Return the id of a NovaSeqX flow cell."""
    return "HK33MDRX3"


@pytest.fixture(scope="session")
def novaseq_6000_post_1_5_kits_flow_cell_full_name(
    novaseq_6000_post_1_5_kits_flow_cell_id: str,
) -> str:
    """Return the full name of a NovaSeqX flow cell."""
    return f"230912_A00187_1009_A{novaseq_6000_post_1_5_kits_flow_cell_id}"


@pytest.fixture(scope="session")
def novaseq_x_flow_cell_id() -> str:
    """Return the id of a NovaSeqX flow cell."""
    return "22F52TLT3"


@pytest.fixture(scope="session")
def novaseq_x_flow_cell_full_name(novaseq_x_flow_cell_id: str) -> str:
    """Return the full name of a NovaSeqX flow cell."""
    return f"20231108_LH00188_0028_B{novaseq_x_flow_cell_id}"


# Lists


@pytest.fixture(scope="session")
def bcl_convert_demultiplexed_flow_cell_sample_internal_ids() -> list[str]:
    """
    Sample id:s present in sample sheet for dummy flow cell demultiplexed with BCL Convert in
    cg/tests/fixtures/apps/demultiplexing/demultiplexed-runs/230504_A00689_0804_BHY7FFDRX2.
    """
    return ["ACC11927A2", "ACC11927A5"]


@pytest.fixture(scope="session")
def bcl2fastq_demultiplexed_flow_cell_sample_internal_ids() -> list[str]:
    """
    Sample id:s present in sample sheet for dummy flow cell demultiplexed with BCL Convert in
    cg/tests/fixtures/apps/demultiplexing/demultiplexed-runs/170407_A00689_0209_BHHKVCALXX.
    """
    return ["SVE2528A1"]
