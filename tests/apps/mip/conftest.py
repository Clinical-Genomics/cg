"""Fixtures for testing mip app"""

import pytest

from cg.constants import FileExtensions
from cg.constants.subject import Sex


def create_file(tmpdir, flowcell, lane, read, file_content):
    """actual file on disk"""

    file_name = f"S1_FC000{flowcell}_L00{lane}_R_{read}{FileExtensions.FASTQ}{FileExtensions.GZIP}"
    file_path = tmpdir / file_name
    file_path.write(file_content)
    return file_path


def create_file_data(file_path, flowcell, lane, read):
    """meta data about a file on disk"""
    return {
        "path": file_path,
        "lane": lane,
        "flowcell": flowcell,
        "read": read,
        "undetermined": False,
    }


class MockTB:
    """Trailblazer mock fixture"""

    def __init__(self):
        self._link_was_called = False

    def link(self, family: str, sample: str, analysis_type: str, files: list[dict]):
        """Link files mock"""

        del family, sample, analysis_type, files

        self._link_was_called = True

    def link_was_called(self):
        """Check if link has been called"""
        return self._link_was_called


@pytest.fixture
def valid_config():
    sample = dict(
        sample_id="sample",
        analysis_type="wes",
        father="0",
        mother="0",
        phenotype="affected",
        sex=Sex.MALE,
        expected_coverage=15,
        capture_kit="agilent_sureselect_cre.v1",
    )
    return dict(
        case="a_case",
        default_gene_panels=["a_panel"],
        samples=[sample],
    )


@pytest.fixture
def invalid_config_analysis_type():
    sample = dict(
        sample_id="sample",
        analysis_type="nonexisting",
        father="0",
        mother="0",
        phenotype="affected",
        sex=Sex.MALE,
        expected_coverage=15,
        capture_kit="agilent_sureselect_cre.v1",
    )

    return dict(
        case="a_case",
        default_gene_panels=["a_panel"],
        samples=[sample],
    )


@pytest.fixture
def invalid_config_unknown_field():
    sample = dict(
        sample_id="sample",
        sample_display_name="a_sample_name",
        analysis_type="wes",
        father="0",
        mother="0",
        phenotype="affected",
        sex=Sex.MALE,
        expected_coverage=15,
        capture_kit="agilent_sureselect_cre.v1",
        unknown_field="UNKNOWN",
    )

    return dict(
        case="a_case",
        default_gene_panels=["a_panel"],
        samples=[sample],
    )


@pytest.fixture
def invalid_config_unknown_field_sample_id():
    sample = dict(
        sample_display_name="a_sample_name",
        analysis_type="wes",
        father="0",
        mother="0",
        phenotype="affected",
        sex=Sex.MALE,
        expected_coverage=15,
        capture_kit="agilent_sureselect_cre.v1",
    )

    return dict(
        case="a_case",
        default_gene_panels=["a_panel"],
        samples=[sample],
    )


@pytest.fixture
def invalid_config_unknown_field_analysis_type():
    sample = dict(
        sample_id="sample",
        sample_display_name="a_sample_name",
        analysis_type="nonexisting",
        father="0",
        mother="0",
        phenotype="affected",
        sex=Sex.MALE,
        expected_coverage=15,
        capture_kit="agilent_sureselect_cre.v1",
    )
    return dict(case="a_case", default_gene_panels=["a_panel"], samples=[sample])
