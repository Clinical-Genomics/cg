"""Fixtures for the workflow tests."""

import datetime
import shutil
from collections.abc import Generator
from pathlib import Path

import pytest

from cg.apps.crunchy.crunchy import CrunchyAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.constants.constants import CaseActions, FileExtensions, MicrosaltQC, Workflow
from cg.meta.compress.compress import CompressAPI
from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.compression_data import CompressionData
from cg.models.orders.sample_base import ControlEnum
from cg.store.models import Case, Sample
from tests.mocks.balsamic_analysis_mock import MockBalsamicAnalysis
from tests.mocks.tb_mock import MockTB
from tests.store_helpers import StoreHelpers


@pytest.fixture(scope="function")
def analysis_api_balsamic(cg_context: CGConfig) -> MockBalsamicAnalysis:
    """BALSAMIC ReportAPI fixture."""
    return MockBalsamicAnalysis(cg_context)


@pytest.fixture
def compress_api(
    illumina_demultiplexed_runs_directory: Path,
    real_crunchy_api: CrunchyAPI,
    housekeeper_api: HousekeeperAPI,
    project_dir: Path,
) -> Generator[CompressAPI, None, None]:
    """Return Compress API."""
    yield CompressAPI(
        crunchy_api=real_crunchy_api, hk_api=housekeeper_api, demux_root=project_dir.as_posix()
    )


@pytest.fixture(scope="session")
def deliverables_template_content() -> list[dict]:
    return [
        {
            "format": "yml",
            "id": "CASEID",
            "path": Path("PATHTOCASE", "pipeline_info", "software_versions.yml").as_posix(),
            "path_index": None,
            "step": "software-versions",
            "tag": "software-versions",
        },
        {
            "format": "json",
            "id": "CASEID",
            "path": Path("PATHTOCASE", "multiqc", "multiqc_data", "multiqc_data")
            .with_suffix(FileExtensions.JSON)
            .as_posix(),
            "path_index": None,
            "step": "multiqc-json",
            "tag": "multiqc-json",
        },
    ]


@pytest.fixture(scope="function")
def populated_compress_spring_api(
    compress_api: CompressAPI, only_spring_bundle: dict, helpers
) -> CompressAPI:
    """Populated compress api fixture with only spring compressed fastq."""
    helpers.ensure_hk_bundle(compress_api.hk_api, only_spring_bundle)

    return compress_api


@pytest.fixture(scope="function")
def populated_compress_api_fastq_spring(
    compress_api: CompressAPI, spring_fastq_mix: dict, helpers
) -> CompressAPI:
    """Populated compress api fixture with both spring and fastq."""
    helpers.ensure_hk_bundle(compress_api.hk_api, spring_fastq_mix)

    return compress_api


@pytest.fixture(name="only_spring_bundle")
def only_spring_bundle() -> dict:
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
def spring_fastq_mix(compression_object: CompressionData) -> dict:
    """Return a dictionary with bundle info including both fastq and spring files."""

    return {
        "name": "ADM1",
        "created": "2019-12-24",
        "files": [
            {
                "path": str(compression_object.spring_path),
                "archive": False,
                "tags": [SequencingFileTag.SPRING],
            },
            {
                "path": str(compression_object.fastq_first),
                "archive": False,
                "tags": [SequencingFileTag.FASTQ],
            },
            {
                "path": str(compression_object.fastq_second),
                "archive": False,
                "tags": [SequencingFileTag.FASTQ],
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


@pytest.fixture
def metrics_file_failing_qc(
    microsalt_qc_fail_run_dir_path: Path,
    microsalt_qc_fail_lims_project: str,
    tmp_path: Path,
) -> Path:
    """Return a metrics file that fails QC with corresponding samples in the database."""
    metrics_path = Path(microsalt_qc_fail_run_dir_path, f"{microsalt_qc_fail_lims_project}.json")
    temp_metrics_path = Path(tmp_path, metrics_path.name)
    shutil.copy(metrics_path, temp_metrics_path)
    return temp_metrics_path


@pytest.fixture
def metrics_file_passing_qc(
    microsalt_qc_pass_run_dir_path: Path,
    microsalt_qc_pass_lims_project: str,
    tmp_path: Path,
) -> Path:
    """Return a metrics file that pass QC with corresponding samples in the database."""
    metrics_path = Path(microsalt_qc_pass_run_dir_path, f"{microsalt_qc_pass_lims_project}.json")
    temp_metrics_path = Path(tmp_path, metrics_path.name)
    shutil.copy(metrics_path, temp_metrics_path)
    return temp_metrics_path


@pytest.fixture
def microsalt_metrics_file(
    microsalt_qc_fail_run_dir_path: Path, microsalt_qc_fail_lims_project: str
) -> Path:
    return Path(microsalt_qc_fail_run_dir_path, f"{microsalt_qc_fail_lims_project}.json")


@pytest.fixture(name="microsalt_case_qc_pass")
def microsalt_case_qc_pass() -> str:
    """Return a microsalt case to pass QC."""
    return "microsalt_case_qc_pass"


@pytest.fixture(name="microsalt_case_qc_fail")
def microsalt_case_qc_fail() -> str:
    """Return a microsalt case to fail QC."""
    return "microsalt_case_qc_fail"


@pytest.fixture(name="qc_pass_microsalt_samples")
def qc_pass_microsalt_samples() -> list[str]:
    """Return a list of 20 microsalt samples internal_ids."""
    return [f"ACC22222A{i}" for i in range(1, 21)]


@pytest.fixture(name="qc_fail_microsalt_samples")
def qc_fail_microsalt_samples() -> list[str]:
    """Return a list of 20 microsalt samples internal_ids."""
    return [f"ACC11111A{i}" for i in range(1, 21)]


@pytest.fixture(name="qc_microsalt_context")
def qc_microsalt_context(
    cg_context: CGConfig,
    helpers: StoreHelpers,
    microsalt_case_qc_pass: str,
    microsalt_case_qc_fail: str,
    qc_pass_microsalt_samples: list[str],
    qc_fail_microsalt_samples: list[str],
) -> CGConfig:
    """Return a Microsalt CG context."""
    cg_context.trailblazer_api_ = MockTB()
    analysis_api = MicrosaltAnalysisAPI(cg_context)
    store = analysis_api.status_db

    # Create MWR microsalt case that passes QC
    microsalt_case_qc_pass: Case = helpers.add_case(
        store=store,
        internal_id=microsalt_case_qc_pass,
        name=microsalt_case_qc_pass,
        data_analysis=Workflow.MICROSALT,
        action=CaseActions.RUNNING,
    )

    for sample in qc_pass_microsalt_samples[1:]:
        sample_to_add: Sample = helpers.add_sample(
            store=store,
            application_tag="MWRNXTR003",
            application_type="mic",
            internal_id=sample,
            reads=MicrosaltQC.TARGET_READS,
            last_sequenced_at=datetime.datetime.now(),
        )

        helpers.add_relationship(store=store, case=microsalt_case_qc_pass, sample=sample_to_add)

    # Add a negative control sample that passes the qc
    negative_control_sample: Sample = helpers.add_sample(
        store=store,
        internal_id=qc_pass_microsalt_samples[0],
        application_tag="MWRNXTR003",
        application_type="mic",
        reads=0,
        last_sequenced_at=datetime.datetime.now(),
        control=ControlEnum.negative,
    )
    helpers.add_relationship(
        store=store, case=microsalt_case_qc_pass, sample=negative_control_sample
    )

    # Create a microsalt MWX case that fails QC
    microsalt_case_qc_fail: Case = helpers.add_case(
        store=store,
        internal_id=microsalt_case_qc_fail,
        name=microsalt_case_qc_fail,
        data_analysis=Workflow.MICROSALT,
    )

    for sample in qc_fail_microsalt_samples:
        sample_to_add: Sample = helpers.add_sample(
            store=store,
            application_tag="MWXNXTR003",
            application_type="mic",
            internal_id=sample,
            reads=MicrosaltQC.TARGET_READS,
            last_sequenced_at=datetime.datetime.now(),
            control=ControlEnum.negative,
        )

        helpers.add_relationship(store=store, case=microsalt_case_qc_fail, sample=sample_to_add)

    # Setting the target reads to correspond with statusDB
    store.get_application_by_tag(tag="MWRNXTR003").target_reads = MicrosaltQC.TARGET_READS
    store.get_application_by_tag(tag="MWXNXTR003").target_reads = MicrosaltQC.TARGET_READS

    cg_context.meta_apis["analysis_api"] = analysis_api

    return cg_context


@pytest.fixture(name="rnafusion_metrics")
def rnafusion_metrics() -> dict[str, float]:
    """Return Rnafusion raw analysis metrics dictionary."""
    return {
        "after_filtering_gc_content": 0.516984,
        "after_filtering_q20_rate": 0.974834,
        "after_filtering_q30_rate": 0.929476,
        "after_filtering_read1_mean_length": 99.0,
        "before_filtering_total_reads": 149984042.0,
        "median_5prime_to_3prime_bias": 1.1211,
        "pct_adapter": 12.005654574904709,
        "pct_mrna_bases": 85.9731,
        "pct_ribosomal_bases": 0.6581,
        "pct_surviving": 99.42004630065911,
        "pct_duplication": 14.8643,
        "read_pairs_examined": 72391566.0,
        "uniquely_mapped_percent": 91.02,
    }


@pytest.fixture(name="mip_analysis_api")
def fixture_mip_analysis_api(
    cg_context: CGConfig, mip_hk_store, store_with_illumina_sequencing_data
) -> MipDNAAnalysisAPI:
    """Return a MIP analysis API."""
    analysis_api = MipDNAAnalysisAPI(cg_context)
    analysis_api.housekeeper_api = mip_hk_store
    analysis_api.status_db = store_with_illumina_sequencing_data
    return analysis_api


@pytest.fixture
def taxprofiler_metrics() -> dict[str, float]:
    """Return Taxprofiler raw analysis metrics dictionary."""
    return {
        "filtering_result_passed_filter_reads": 24810472.0,
        "reads_mapped": 19014950.0,
        "total_reads": 12400055,
        "paired_aligned_none": 1409340,
    }


@pytest.fixture(scope="function")
def nallo_metrics_deliverables(
    nallo_analysis_dir: Path,
) -> dict[str, list]:
    return {
        "metrics": [
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "mean_coverage",
                "step": "multiqc",
                "value": 32.18,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "min_coverage",
                "step": "multiqc",
                "value": 0.0,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "max_coverage",
                "step": "multiqc",
                "value": 63906.0,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "coverage_bases",
                "step": "multiqc",
                "value": 99366056494,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "length",
                "step": "multiqc",
                "value": 3088286377,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "1_x_pc",
                "step": "multiqc",
                "value": 94.0,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "5_x_pc",
                "step": "multiqc",
                "value": 94.0,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "10_x_pc",
                "step": "multiqc",
                "value": 93.0,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "30_x_pc",
                "step": "multiqc",
                "value": 65.0,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "50_x_pc",
                "step": "multiqc",
                "value": 2.0,
            },
            {
                "condition": {"norm": "gt", "threshold": 20.0},
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "median_coverage",
                "step": "multiqc",
                "value": 33,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "total_sequences",
                "step": "multiqc",
                "value": 2944513.0,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "percent_gc",
                "step": "multiqc",
                "value": 39.0,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "avg_sequence_length",
                "step": "multiqc",
                "value": 12792.931765117017,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "median_sequence_length",
                "step": "multiqc",
                "value": 12999,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "percent_duplicates",
                "step": "multiqc",
                "value": 1.7232745723252236,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "percent_fails",
                "step": "multiqc",
                "value": 30.0,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "family_id",
                "step": "multiqc",
                "value": "nallo",
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "paternal_id",
                "step": "multiqc",
                "value": 0.0,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "maternal_id",
                "step": "multiqc",
                "value": 0.0,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "sex",
                "step": "multiqc",
                "value": 1.0,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "predicted_sex_sex_check",
                "step": "multiqc",
                "value": "male",
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "phenotype",
                "step": "multiqc",
                "value": 2.0,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "somalier_family_id",
                "step": "multiqc",
                "value": "nallo",
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "somalier_paternal_id",
                "step": "multiqc",
                "value": 0.0,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "somalier_maternal_id",
                "step": "multiqc",
                "value": 0.0,
            },
            {
                "condition": {"norm": "eq", "threshold": 2.0},
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "somalier_sex",
                "step": "multiqc",
                "value": 2.0,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "somalier_phenotype",
                "step": "multiqc",
                "value": 2.0,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "somalier_original_pedigree_sex",
                "step": "multiqc",
                "value": "female",
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "somalier_gt_depth_mean",
                "step": "multiqc",
                "value": 20.4,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "somalier_gt_depth_sd",
                "step": "multiqc",
                "value": 6.5,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "somalier_depth_mean",
                "step": "multiqc",
                "value": 20.3,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "somalier_depth_sd",
                "step": "multiqc",
                "value": 6.6,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "somalier_ab_mean",
                "step": "multiqc",
                "value": 0.52,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "somalier_ab_std",
                "step": "multiqc",
                "value": 0.42,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "somalier_n_hom_ref",
                "step": "multiqc",
                "value": 4727.0,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "somalier_n_het",
                "step": "multiqc",
                "value": 6126.0,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "somalier_n_hom_alt",
                "step": "multiqc",
                "value": 5668.0,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "somalier_n_unknown",
                "step": "multiqc",
                "value": 863.0,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "somalier_p_middling_ab",
                "step": "multiqc",
                "value": 0.007,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "somalier_X_depth_mean",
                "step": "multiqc",
                "value": 12.24,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "somalier_X_n",
                "step": "multiqc",
                "value": 325.0,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "somalier_X_hom_ref",
                "step": "multiqc",
                "value": 148.0,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "somalier_X_het",
                "step": "multiqc",
                "value": 0.0,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "somalier_X_hom_alt",
                "step": "multiqc",
                "value": 177.0,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "somalier_Y_depth_mean",
                "step": "multiqc",
                "value": 12.73,
            },
            {
                "condition": None,
                "header": None,
                "id": "ADM1",
                "input": "multiqc_data.json",
                "name": "somalier_Y_n",
                "step": "multiqc",
                "value": 15.0,
            },
            {
                "condition": {"norm": "eq", "threshold": "False"},
                "header": None,
                "id": "ADM1-ADM2",
                "input": "multiqc_data.json",
                "name": "parent_error_ped_check",
                "step": "multiqc",
                "value": "False",
            },
        ]
    }
