from pathlib import Path

import pytest

from cg.constants import FileExtensions


@pytest.fixture(scope="session")
def analysis_starter_fixtures(fixtures_dir: Path) -> Path:
    """Return the path to the directory with analysis starter fixtures."""
    return Path(fixtures_dir, "services", "analysis_starter")


@pytest.fixture
def raredisease_case_path(raredisease_dir: Path, raredisease_case_id: str) -> Path:
    return Path(raredisease_dir, raredisease_case_id)


@pytest.fixture
def raredisease_case_path2(raredisease_dir: Path, raredisease_case_id: str) -> Path:
    return Path("case", "path")


@pytest.fixture
def raredisease_work_dir_path(raredisease_case_path: Path, raredisease_case_id: Path) -> Path:
    return Path(raredisease_case_path, "work")


@pytest.fixture(scope="function")
def raredisease_gene_panel_path(raredisease_case_path: Path) -> Path:
    """Path to gene panel file."""
    return Path(raredisease_case_path, "gene_panels").with_suffix(FileExtensions.BED)


@pytest.fixture(scope="function")
def raredisease_gene_panel_path2(raredisease_case_path2: Path) -> Path:
    """Path to gene panel file."""
    return Path(raredisease_case_path2, "gene_panels").with_suffix(FileExtensions.BED)


@pytest.fixture
def raredisease_managed_variants_path(raredisease_case_path2: Path) -> Path:
    return Path(raredisease_case_path2, "managed_variants").with_suffix(FileExtensions.VCF)


@pytest.fixture
def raredisease_params_file_path(raredisease_case_path: Path, raredisease_case_id: str) -> Path:
    return Path(raredisease_case_path, f"{raredisease_case_id}_params_file").with_suffix(
        FileExtensions.YAML
    )


@pytest.fixture
def raredisease_params_file_path_readable(
    analysis_starter_fixtures: Path, raredisease_case_path: Path, raredisease_case_id: str
) -> Path:
    return Path(analysis_starter_fixtures, f"{raredisease_case_id}_params_file").with_suffix(
        FileExtensions.YAML
    )


@pytest.fixture
def raredisease_nextflow_config_file_path(
    raredisease_case_path: Path, raredisease_case_id: str
) -> Path:
    return Path(raredisease_case_path, f"{raredisease_case_id}_nextflow_config").with_suffix(
        FileExtensions.JSON
    )


@pytest.fixture(scope="function")
def raredisease_sample_sheet_path(raredisease_case_path, raredisease_case_id) -> Path:
    """Path to sample sheet."""
    return Path(raredisease_case_path, f"{raredisease_case_id}_samplesheet").with_suffix(
        FileExtensions.CSV
    )


@pytest.fixture(scope="function")
def raredisease_sample_sheet_path2() -> Path:
    """Path to sample sheet."""
    return Path("samplesheet", "path")
