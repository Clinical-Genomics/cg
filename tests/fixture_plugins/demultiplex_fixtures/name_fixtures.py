import pytest


@pytest.fixture
def tmp_flow_cell_name_malformed_sample_sheet() -> str:
    """ "Returns the name of a flow cell directory ready for demultiplexing with BCL convert.
    Contains a sample sheet with malformed headers.
    """
    return "201203_A00689_0200_AHVKJCDRXY"


@pytest.fixture(name="tmp_flow_cell_name_ready_for_demultiplexing_bcl2fastq")
def tmp_flow_cell_name_ready_for_demultiplexing_bcl2fastq() -> str:
    """Returns the name of a flow cell directory ready for demultiplexing with bcl2fastq."""
    return "211101_D00483_0615_AHLG5GDRXY"


@pytest.fixture(scope="session")
def flow_cell_name_demultiplexed_with_bcl2fastq() -> str:
    """Return the name of a flow cell that has been demultiplexed with BCL2Fastq."""
    return "HHKVCALXX"


@pytest.fixture(scope="session")
def flow_cell_directory_name_demultiplexed_with_bcl2fastq(
    flow_cell_name_demultiplexed_with_bcl2fastq: str,
) -> str:
    """Return the name of a flow cell directory that has been demultiplexed with BCL2Fastq."""
    return f"170407_ST-E00198_0209_B{flow_cell_name_demultiplexed_with_bcl2fastq}"


@pytest.fixture(scope="session")
def flow_cell_name_demultiplexed_with_bcl_convert() -> str:
    return "HY7FFDRX2"


@pytest.fixture(scope="session")
def flow_cell_directory_name_demultiplexed_with_bcl_convert(
    flow_cell_name_demultiplexed_with_bcl_convert: str,
) -> str:
    return f"230504_A00689_0804_B{flow_cell_name_demultiplexed_with_bcl_convert}"


@pytest.fixture(scope="session")
def hiseq_x_single_index_flow_cell_name() -> str:
    """Return the full name of a HiSeqX flow cell with only one index."""
    return "170517_ST-E00266_0210_BHJCFFALXX"


@pytest.fixture(scope="session")
def hiseq_x_dual_index_flow_cell_name() -> str:
    """Return the full name of a HiSeqX flow cell with two indexes."""
    return "180508_ST-E00269_0269_AHL32LCCXY"


@pytest.fixture(scope="session")
def hiseq_2500_dual_index_flow_cell_name() -> str:
    """Return the full name of a HiSeq2500 flow cell with double indexes."""
    return "181005_D00410_0735_BHM2LNBCX2"


@pytest.fixture(scope="session")
def hiseq_2500_custom_index_flow_cell_name() -> str:
    """Return the full name of a HiSeq2500 flow cell with double indexes."""
    return "180509_D00450_0598_BHGYFNBCX2"


@pytest.fixture(scope="session")
def bcl2fastq_flow_cell_full_name() -> str:
    """Return full flow cell name."""
    return "201203_D00483_0200_AHVKJCDRXX"


@pytest.fixture(scope="session")
def bcl_convert_flow_cell_full_name() -> str:
    """Return the full name of a bcl_convert flow cell."""
    return "211101_A00187_0615_AHLG5GDRZZ"


@pytest.fixture(scope="session")
def novaseq_x_flow_cell_full_name() -> str:
    """Return the full name of a NovaSeqX flow cell."""
    return "20230508_LH00188_0003_A22522YLT3"


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
