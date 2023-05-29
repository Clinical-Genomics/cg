"""Fixtures for the workflow tests."""
import datetime
from pathlib import Path
from typing import List, Dict

import pytest
from cgmodels.cg.constants import Pipeline

from cg.constants.constants import MicrosaltAppTags, MicrosaltQC
from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI

from cg.meta.compress.compress import CompressAPI
from cg.models.compression_data import CompressionData
from cg.models.cg_config import CGConfig
from cg.store.models import Family, Sample
from tests.store_helpers import StoreHelpers
from tests.conftest import fixture_base_store
from tests.meta.compress.conftest import fixture_compress_api, fixture_real_crunchy_api
from tests.meta.upload.scout.conftest import fixture_another_sample_id
from tests.cli.workflow.balsamic.conftest import (
    fastq_file_l_1_r_1,
    fastq_file_l_2_r_1,
    fastq_file_l_2_r_2,
    balsamic_housekeeper_dir,
)


@pytest.fixture(scope="function", name="populated_compress_spring_api")
def fixture_populated_compress_spring_api(
    compress_api: CompressAPI, only_spring_bundle: dict, helpers
) -> CompressAPI:
    """Populated compress api fixture with only spring compressed fastq."""
    helpers.ensure_hk_bundle(compress_api.hk_api, only_spring_bundle)

    return compress_api


@pytest.fixture(scope="function", name="populated_compress_api_fastq_spring")
def fixture_populated_compress_api_fastq_spring(
    compress_api: CompressAPI, spring_fastq_mix: dict, helpers
) -> CompressAPI:
    """Populated compress api fixture with both spring and fastq."""
    helpers.ensure_hk_bundle(compress_api.hk_api, spring_fastq_mix)

    return compress_api


@pytest.fixture(name="only_spring_bundle")
def fixture_only_spring_bundle() -> dict:
    """Return a dictionary with bundle info in the correct format."""
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
    """Return a dictionary with bundle info including both fastq and spring files."""

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
def microsalt_qc_pass_run_dir_path(
    microsalt_qc_pass_lims_project: str, microsalt_analysis_dir: Path
) -> Path:
    """Return a microsalt run dir path fixture that passes QC."""
    return Path(microsalt_analysis_dir, microsalt_qc_pass_lims_project)


@pytest.fixture(name="microsalt_qc_fail_run_dir_path")
def microsalt_qc_fail_run_dir_path(
    microsalt_qc_fail_lims_project: str, microsalt_analysis_dir: Path
) -> Path:
    """Return a microsalt run dir path fixture that fails QC."""
    return Path(microsalt_analysis_dir, microsalt_qc_fail_lims_project)


@pytest.fixture(name="microsalt_qc_pass_lims_project")
def microsalt_qc_pass_lims_project() -> str:
    """Return a microsalt LIMS project id that passes QC."""
    return "ACC22222_qc_pass"


@pytest.fixture(name="microsalt_qc_fail_lims_project")
def microsalt_qc_fail_lims_project() -> str:
    """Return a microsalt LIMS project id that fails QC."""
    return "ACC11111_qc_fail"


@pytest.fixture(name="microsalt_case_qc_pass")
def microsalt_case_qc_pass() -> str:
    """Return a microsalt case to pass QC."""
    return "microsalt_case_qc_pass"


@pytest.fixture(name="microsalt_case_qc_fail")
def microsalt_case_qc_fail() -> str:
    """Return a microsalt case to fail QC."""
    return "microsalt_case_qc_fail"


@pytest.fixture(name="qc_pass_microsalt_samples")
def qc_pass_microsalt_samples() -> List[str]:
    """Return a list of 20 microsalt samples internal_ids."""
    return [f"ACC22222A{i}" for i in range(1, 21)]


@pytest.fixture(name="qc_fail_microsalt_samples")
def qc_fail_microsalt_samples() -> List[str]:
    """Return a list of 20 microsalt samples internal_ids."""
    return [f"ACC11111A{i}" for i in range(1, 21)]


@pytest.fixture(name="qc_microsalt_context")
def qc_microsalt_context(
    cg_context: CGConfig,
    helpers: StoreHelpers,
    microsalt_case_qc_pass: str,
    microsalt_case_qc_fail: str,
    qc_pass_microsalt_samples: List[str],
    qc_fail_microsalt_samples: List[str],
    microsalt_qc_pass_lims_project: str,
    microsalt_qc_fail_lims_project: str,
) -> CGConfig:
    """Return a Microsalt CG context."""
    analysis_api = MicrosaltAnalysisAPI(cg_context)
    store = analysis_api.status_db

    # Create MWR microsalt case that passes QC
    microsalt_case_qc_pass: Family = helpers.add_case(
        store=store,
        internal_id=microsalt_case_qc_pass,
        name=microsalt_case_qc_pass,
        data_analysis=Pipeline.MICROSALT,
    )

    for sample in qc_pass_microsalt_samples:
        sample_to_add: Sample = helpers.add_sample(
            store=store,
            internal_id=sample,
            application_tag=MicrosaltAppTags.MWRNXTR003,
            application_type=MicrosaltAppTags.PREP_CATEGORY,
            reads=MicrosaltQC.TARGET_READS,
            sequenced_at=datetime.datetime.now(),
        )

        helpers.add_relationship(store=store, case=microsalt_case_qc_pass, sample=sample_to_add)

    # Create a microsalt MWX case that fails QC
    microsalt_case_qc_fail: Family = helpers.add_case(
        store=store,
        internal_id=microsalt_case_qc_fail,
        name=microsalt_case_qc_fail,
        data_analysis=Pipeline.MICROSALT,
    )

    for sample in qc_fail_microsalt_samples:
        sample_to_add: Sample = helpers.add_sample(
            store=store,
            internal_id=sample,
            application_tag=MicrosaltAppTags.MWXNXTR003,
            application_type=MicrosaltAppTags.PREP_CATEGORY,
            reads=MicrosaltQC.TARGET_READS,
            sequenced_at=datetime.datetime.now(),
        )

        helpers.add_relationship(store=store, case=microsalt_case_qc_fail, sample=sample_to_add)

    # Setting the target reads to correspond with statusDB
    store.get_application_by_tag(
        tag=MicrosaltAppTags.MWRNXTR003
    ).target_reads = MicrosaltQC.TARGET_READS
    store.get_application_by_tag(
        tag=MicrosaltAppTags.MWXNXTR003
    ).target_reads = MicrosaltQC.TARGET_READS

    cg_context.meta_apis["analysis_api"] = analysis_api

    return cg_context


@pytest.fixture(name="rnafusion_metrics")
def fixture_rnafusion_metrics() -> Dict[str, float]:
    """Return Rnafusion raw analysis metrics dictionary."""
    return {
        "after_filtering_gc_content": 0.516984,
        "after_filtering_q20_rate": 0.974834,
        "after_filtering_q30_rate": 0.929476,
        "after_filtering_read1_mean_length": 99.0,
        "before_filtering_total_reads": 149984042.0,
        "bias_5_3": 1.07,
        "pct_adapter": 12.005654574904709,
        "pct_mrna_bases": 85.9731,
        "pct_ribosomal_bases": 0.6581,
        "pct_surviving": 99.42004630065911,
        "pct_duplication": 14.8643,
        "reads_aligned": 72391566.0,
        "uniquely_mapped_percent": 91.02,
    }
