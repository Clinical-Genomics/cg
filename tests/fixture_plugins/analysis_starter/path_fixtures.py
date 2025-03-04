from pathlib import Path

import pytest

from cg.constants import FileExtensions


@pytest.fixture
def raredisease_work_dir_path(raredisease_dir: Path, raredisease_case_id: Path) -> Path:
    return Path(raredisease_dir, raredisease_case_id, "work")


@pytest.fixture(scope="function")
def raredisease_gene_panel_path(raredisease_dir: Path, raredisease_case_id) -> Path:
    """Path to gene panel file."""
    return Path(raredisease_dir, raredisease_case_id, "gene_panels").with_suffix(FileExtensions.BED)


@pytest.fixture
def raredisease_params_file_path(raredisease_dir: Path, raredisease_case_id: str) -> Path:
    return Path(
        raredisease_dir, raredisease_case_id, f"{raredisease_case_id}_params_file"
    ).with_suffix(FileExtensions.YAML)


@pytest.fixture
def raredisease_nextflow_config_file_path(raredisease_dir: Path, raredisease_case_id: str) -> Path:
    return Path(
        raredisease_dir, raredisease_case_id, f"{raredisease_case_id}_nextflow_config"
    ).with_suffix(FileExtensions.JSON)


@pytest.fixture(scope="function")
def raredisease_sample_sheet_path(raredisease_dir, raredisease_case_id) -> Path:
    """Path to sample sheet."""
    return Path(
        raredisease_dir, raredisease_case_id, f"{raredisease_case_id}_samplesheet"
    ).with_suffix(FileExtensions.CSV)
