"""Fixtures for testing mip app"""
import string
from typing import List

import pytest
from cg.apps.mip import MipAPI


@pytest.fixture
def valid_fastq_filename_pattern():
    """the pattern MIP file names should match"""
    # 'xxx_R_1.fastq.gz and xxx_R_2.fastq.gz'
    return r"^.+_R_[1-2]{1}\.fastq.gz$"


def _full_content():
    """The content the files are made of"""
    return string.ascii_letters


@pytest.fixture
def files_content(tmpdir):
    """The content the files are made of"""
    return _full_content()[0 : len(_simple_files(tmpdir))]


def simple(tmpdir):
    """Creates a dict with the data to use in the tests"""
    flowcells = [1, 2, 3, 4, 5, 6, 7, 8]
    lanes = [1, 2, 3]
    reads = [1, 2]

    _simple = {"files": [], "data": []}
    i = 0

    for read in reads:
        for flowcell in flowcells:
            for lane in lanes:
                content = _full_content()[i]
                file_path = create_file(tmpdir, flowcell, lane, read, content)

                _simple["files"].append(file_path)

                data = create_file_data(file_path, flowcell, lane, read)
                _simple["data"].append(data)
                i += 1

    return _simple


def _simple_files(tmpdir):
    """"Some files to test with"""
    return simple(tmpdir)["files"]


@pytest.fixture
def simple_files(tmpdir):
    """"Some files to test with"""
    return _simple_files(tmpdir)


@pytest.fixture
def simple_files_data(tmpdir):
    """Data for link method"""
    return simple(tmpdir)["data"]


def create_file(tmpdir, flowcell, lane, read, file_content):
    """actual file on disk"""

    file_name = f"S1_FC000{flowcell}_L00{lane}_R_{read}.fastq.gz"
    file_path = tmpdir / file_name
    file_path.write(file_content)
    return file_path


def create_file_data(file_path, flowcell, lane, read):
    """meta data about a file on disk"""
    data = {
        "path": file_path,
        "lane": lane,
        "flowcell": flowcell,
        "read": read,
        "undetermined": False,
    }
    return data


@pytest.fixture
def cg_config():
    """mock relevant parts of a cg-config"""
    return {}


@pytest.fixture
def link_family():
    """mock case name"""
    return "case"


@pytest.fixture
def link_sample():
    """mock sample name"""
    return "sample"


class MockTB:
    """Trailblazer mock fixture"""

    def __init__(self):
        self._link_was_called = False

    def link(self, family: str, sample: str, analysis_type: str, files: List[dict]):
        """Link files mock"""

        del family, sample, analysis_type, files

        self._link_was_called = True

    def link_was_called(self):
        """Check if link has been called"""
        return self._link_was_called


@pytest.fixture
def tb_api():
    """Trailblazer API fixture"""

    return MockTB()


@pytest.fixture(scope="session")
def mip_api():
    """MipAPI fixture"""
    _mip_api = MipAPI(
        script="test/fake_mip.pl",
        pipeline="analyse rd_dna",
        conda_env="S_mip_rd-rna",
        root="/var/empty",
    )
    return _mip_api


@pytest.fixture
def mip_config_path():
    """path to a mip config"""
    return "tests/fixtures/global_config.yaml"


@pytest.fixture
def case_id():
    """the name of a case"""
    return "angrybird"


@pytest.fixture
def valid_config():
    sample = dict(
        sample_id="sample",
        analysis_type="wes",
        father="0",
        mother="0",
        phenotype="affected",
        sex="male",
        expected_coverage=15,
        capture_kit="agilent_sureselect_cre.v1",
    )
    config = dict(
        case="a_case",
        default_gene_panels=["a_panel"],
        samples=[sample],
    )
    return config


@pytest.fixture
def invalid_config_analysis_type():
    sample = dict(
        sample_id="sample",
        analysis_type="nonexisting",
        father="0",
        mother="0",
        phenotype="affected",
        sex="male",
        expected_coverage=15,
        capture_kit="agilent_sureselect_cre.v1",
    )

    config = dict(
        case="a_case",
        default_gene_panels=["a_panel"],
        samples=[sample],
    )
    return config


@pytest.fixture
def invalid_config_unknown_field():
    sample = dict(
        sample_id="sample",
        sample_display_name="a_sample_name",
        analysis_type="wes",
        father="0",
        mother="0",
        phenotype="affected",
        sex="male",
        expected_coverage=15,
        capture_kit="agilent_sureselect_cre.v1",
        unknown_field="UNKNOWN",
    )

    config = dict(
        case="a_case",
        default_gene_panels=["a_panel"],
        samples=[sample],
    )
    return config


@pytest.fixture
def invalid_config_unknown_field_sample_id():
    sample = dict(
        sample_display_name="a_sample_name",
        analysis_type="wes",
        father="0",
        mother="0",
        phenotype="affected",
        sex="male",
        expected_coverage=15,
        capture_kit="agilent_sureselect_cre.v1",
    )

    config = dict(
        case="a_case",
        default_gene_panels=["a_panel"],
        samples=[sample],
    )
    return config


@pytest.fixture
def invalid_config_unknown_field_analysis_type():
    sample = dict(
        sample_id="sample",
        sample_display_name="a_sample_name",
        analysis_type="nonexisting",
        father="0",
        mother="0",
        phenotype="affected",
        sex="male",
        expected_coverage=15,
        capture_kit="agilent_sureselect_cre.v1",
    )
    config = dict(case="a_case", default_gene_panels=["a_panel"], samples=[sample])
    return config
