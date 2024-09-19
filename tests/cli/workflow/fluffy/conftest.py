import datetime as dt
from pathlib import Path

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.housekeeper.models import InputBundle
from cg.constants import SequencingFileTag, Workflow
from cg.constants.constants import CaseActions
from cg.meta.workflow.fluffy import FluffyAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Case, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture(scope="function")
def fluffy_case_id_existing(selected_novaseq_6000_post_1_5_kits_case_ids):
    return selected_novaseq_6000_post_1_5_kits_case_ids[0]


@pytest.fixture(scope="function")
def fluffy_case_id_non_existing():
    return "nakedmolerat"


@pytest.fixture(scope="function")
def fluffy_sample_lims_id(selected_novaseq_6000_post_1_5_kits_sample_ids):
    return selected_novaseq_6000_post_1_5_kits_sample_ids[0]


@pytest.fixture(scope="function")
def fluffy_success_output_summary(tmpdir_factory):
    output_dir = tmpdir_factory.mktemp("output")
    file_path = Path(output_dir, "summary.csv")
    file_path.touch(exist_ok=True)
    return file_path


@pytest.fixture(scope="function")
def fluffy_success_output_aberrations(tmpdir_factory):
    output_dir = tmpdir_factory.mktemp("output")
    file_path = Path(output_dir, "WCXpredict_aberrations.filt.bed")
    file_path.touch(exist_ok=True)
    return file_path


@pytest.fixture
def bcl_convert_samplesheet_path() -> Path:
    return Path("tests", "fixtures", "data", "bcl_convert_sample_sheet.csv")


@pytest.fixture
def sample() -> Sample:
    return Sample(
        name="sample_name",
        order="sample_project",
        control="positive",
        last_sequenced_at=dt.datetime.now(),
    )


@pytest.fixture(scope="function")
def fluffy_fastq_file_path(config_root_dir):
    path = Path(config_root_dir)
    path.mkdir(parents=True, exist_ok=True)
    fastq_path = Path(path, "fastq.fastq.gz")
    fastq_path.touch(exist_ok=True)
    return fastq_path


@pytest.fixture(scope="function")
def deliverables_yaml_path():
    return Path("tests/fixtures/apps/fluffy/deliverables.yaml")


@pytest.fixture
def fluffy_hermes_deliverables_response_data(
    create_multiqc_html_file,
    fluffy_case_id_existing,
    fluffy_sample_lims_id,
    fluffy_success_output_summary,
    fluffy_success_output_aberrations,
    timestamp_yesterday,
):
    return InputBundle(
        **{
            "files": [
                {
                    "path": fluffy_success_output_summary.as_posix(),
                    "tags": ["metrics", fluffy_case_id_existing, "nipt"],
                },
                {
                    "path": create_multiqc_html_file.as_posix(),
                    "tags": ["multiqc-html", fluffy_case_id_existing, "nipt"],
                },
                {
                    "path": fluffy_success_output_aberrations.as_posix(),
                    "tags": ["wisecondor", "cnv", fluffy_sample_lims_id, "nipt"],
                },
            ],
            "created": timestamp_yesterday,
            "name": fluffy_case_id_existing,
        }
    )


@pytest.fixture(scope="function")
def fluffy_fastq_hk_bundle_data(
    fluffy_fastq_file_path: Path,
    fluffy_sample_lims_id: str,
    novaseq_6000_post_1_5_kits_flow_cell_id: str,
) -> dict:
    return {
        "name": fluffy_sample_lims_id,
        "created": dt.datetime.now(),
        "version": "1.0",
        "files": [
            {
                "path": fluffy_fastq_file_path.as_posix(),
                "tags": [SequencingFileTag.FASTQ, novaseq_6000_post_1_5_kits_flow_cell_id],
                "archive": False,
            }
        ],
    }


@pytest.fixture(scope="function")
def fluffy_samplesheet_bundle_data(
    novaseq_6000_post_1_5_kits_correct_sample_sheet_path: Path,
    novaseq_6000_post_1_5_kits_flow_cell_id: str,
) -> dict:
    return {
        "name": novaseq_6000_post_1_5_kits_flow_cell_id,
        "created": dt.datetime.now(),
        "version": "1.0",
        "files": [
            {
                "path": str(novaseq_6000_post_1_5_kits_correct_sample_sheet_path),
                "tags": [novaseq_6000_post_1_5_kits_flow_cell_id, "samplesheet"],
                "archive": False,
            }
        ],
    }


@pytest.fixture(scope="function")
def fluffy_store(
    store_with_illumina_sequencing_data: Store,
    fluffy_case_id_existing: str,
    fluffy_sample_lims_id: str,
) -> Store:
    case: Case = store_with_illumina_sequencing_data.get_case_by_internal_id(
        internal_id=fluffy_case_id_existing
    )
    case.data_analysis = Workflow.FLUFFY
    case.links[0].sample.last_sequenced_at = dt.datetime.now()
    case.links[0].sample.reads = 50
    case.action = CaseActions.ANALYZE
    return store_with_illumina_sequencing_data


@pytest.fixture(scope="function")
def fluffy_context(
    cg_context: CGConfig,
    helpers: StoreHelpers,
    real_housekeeper_api: HousekeeperAPI,
    fluffy_samplesheet_bundle_data: dict,
    fluffy_fastq_hk_bundle_data: dict,
    fluffy_case_id_existing: str,
    fluffy_sample_lims_id: str,
    fluffy_store: Store,
) -> CGConfig:
    cg_context.housekeeper_api_ = real_housekeeper_api
    cg_context.status_db_ = fluffy_store
    fluffy_analysis_api = FluffyAnalysisAPI(config=cg_context)
    helpers.ensure_hk_version(
        fluffy_analysis_api.housekeeper_api, bundle_data=fluffy_samplesheet_bundle_data
    )
    helpers.ensure_hk_version(fluffy_analysis_api.housekeeper_api, fluffy_fastq_hk_bundle_data)
    cg_context.meta_apis["analysis_api"] = fluffy_analysis_api
    return cg_context
