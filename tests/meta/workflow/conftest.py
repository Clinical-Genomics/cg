"""Fixtures for the prepare_fastq api tests"""
from pathlib import Path
from typing import List

import pytest
from cgmodels.cg.constants import Pipeline

from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI
from tests.meta.compress.conftest import fixture_compress_api, fixture_real_crunchy_api

from cg.meta.compress.compress import CompressAPI
from cg.models.compression_data import CompressionData
from cg.models.cg_config import CGConfig
from tests.store_helpers import StoreHelpers


@pytest.fixture(scope="function", name="populated_compress_spring_api")
def fixture_populated_compress_spring_api(
    compress_api: CompressAPI, only_spring_bundle: dict, helpers
) -> CompressAPI:
    """Populated compress api fixture with only spring compressed fastq"""
    helpers.ensure_hk_bundle(compress_api.hk_api, only_spring_bundle)

    return compress_api


@pytest.fixture(scope="function", name="populated_compress_api_fastq_spring")
def fixture_populated_compress_api_fastq_spring(
    compress_api: CompressAPI, spring_fastq_mix: dict, helpers
) -> CompressAPI:
    """Populated compress api fixture with both spring and fastq"""
    helpers.ensure_hk_bundle(compress_api.hk_api, spring_fastq_mix)

    return compress_api


@pytest.fixture(name="only_spring_bundle")
def fixture_only_spring_bundle() -> dict:
    """Return a dictionary with bundle info in the correct format"""
    return {
        "name": "ADM1",
        "created": "2019-12-24",
        "files": [
            {
                "path": "/path/HVCHCCCXY-l4t21_535422_S4_L004.spring",
                "archive": False,
                "tags": ["spring"],
            },
        ],
    }


@pytest.fixture(name="spring_fastq_mix")
def fixture_spring_fastq_mix(compression_object: CompressionData) -> dict:
    """Return a dictionary with bundle info including both fastq and spring files"""

    return {
        "name": "ADM1",
        "created": "2019-12-24",
        "files": [
            {
                "path": str(compression_object.spring_path),
                "archive": False,
                "tags": ["spring"],
            },
            {
                "path": str(compression_object.fastq_first),
                "archive": False,
                "tags": ["fastq"],
            },
            {
                "path": str(compression_object.fastq_second),
                "archive": False,
                "tags": ["fastq"],
            },
        ],
    }


@pytest.fixture(name="microsalt_qc_pass_run_dir_path")
def microsalt_qc_pass_run_dir_path(microsalt_qc_pass_lims_project: str) -> Path:
    """Return a microsalt run dir path fixture that passes QC."""
    return Path("tests/fixtures/analysis/microsalt", microsalt_qc_pass_lims_project)


@pytest.fixture(name="microsalt_qc_fail_run_dir_path")
def microsalt_qc_pass_run_dir_path(microsalt_qc_fail_lims_project: str) -> Path:
    """Return a microsalt run dir path fixture that fails QC."""
    return Path("tests/fixtures/analysis/microsalt", microsalt_qc_fail_lims_project)


@pytest.fixture(name="microsalt_qc_pass_lims_project")
def microsalt_qc_pass_lims_project() -> str:
    """Return a microsalt LIMS project id that passes QC."""
    return "ACC123456_qc_pass"


@pytest.fixture(name="microsalt_qc_fail_lims_project")
def microsalt_qc_fail_lims_project() -> str:
    """Return a microsalt LIMS project id that fails QC."""
    return "ACC123456_qc_fail"


@pytest.fixture(name="microsalt_case_qc_pass")
def microsalt_case_qc_pass() -> str:
    """Return a microsalt case to pass QC."""
    return "microsalt_case_qc_pass"


@pytest.fixture(name="microsalt_qc_fail_case")
def microsalt_qc_fail_case() -> str:
    """Return a microsalt case to fail QC."""
    return "microsalt_qc_fail_case"


@pytest.fixture(name="qc_microsalt_samples")
def qc_microsalt_samples() -> List[str]:
    """Return a list of 20 microsalt samples internal_ids."""
    return [f"ACC123456A{i}" for i in range(1, 21)]


@pytest.fixture(name="qc_microsalt_context")
def qc_microsalt_context(
    cg_context: CGConfig,
    helpers: StoreHelpers,
    microsalt_case_pass: str,
    qc_microsalt_samples: List[str],
) -> CGConfig:
    """Return a Microsalt CG context."""
    analysis_api = MicrosaltAnalysisAPI(cg_context)
    store = analysis_api.status_db

    # Create microsalt case that passes QC
    microsalt_case_qc_pass = helpers.add_case(
        store=store,
        internal_id=microsalt_case_pass,
        name=microsalt_case_pass,
        data_analysis=Pipeline.MICROSALT,
    )

    for sample in qc_microsalt_samples:
        helpers.add_sample()

    # Create microsalt case that fails QC
