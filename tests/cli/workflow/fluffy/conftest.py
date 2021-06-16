import datetime as dt
from pathlib import Path

import pytest
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.housekeeper.models import InputBundle
from cg.constants import Pipeline
from cg.meta.workflow.fluffy import FluffyAnalysisAPI
from cg.models.cg_config import CGConfig
from tests.store_helpers import StoreHelpers


@pytest.fixture(scope="function")
def fluffy_case_id_existing():
    return "norwegiangiraffe"


@pytest.fixture(scope="function")
def fluffy_case_id_non_existing():
    return "nakedmolerat"


@pytest.fixture(scope="function")
def fluffy_sample_lims_id():
    return "ACC1234A1"


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


@pytest.fixture(scope="function")
def samplesheet_fixture_path():
    return Path("tests/fixtures/data/SampleSheet.csv").absolute()


@pytest.fixture(scope="function")
def fastq_file_fixture_path(config_root_dir):
    fixture_path = Path(config_root_dir)
    fixture_path.mkdir(parents=True, exist_ok=True)
    fixture_fastq_path = Path(fixture_path, "fastq.fastq.gz")
    fixture_fastq_path.touch(exist_ok=True)
    return fixture_fastq_path


@pytest.fixture(scope="function")
def deliverables_yaml_fixture_path():
    return Path("tests/fixtures/apps/fluffy/deliverables.yaml")


@pytest.fixture()
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
def fluffy_fastq_hk_bundle_data(fastq_file_fixture_path, fluffy_sample_lims_id) -> dict:
    return {
        "name": fluffy_sample_lims_id,
        "created": dt.datetime.now(),
        "version": "1.0",
        "files": [
            {"path": fastq_file_fixture_path.as_posix(), "tags": ["fastq"], "archive": False}
        ],
    }


@pytest.fixture(scope="function")
def fluffy_samplesheet_bundle_data(samplesheet_fixture_path) -> dict:
    return {
        "name": "flowcell",
        "created": dt.datetime.now(),
        "version": "1.0",
        "files": [
            {"path": str(samplesheet_fixture_path), "tags": ["samplesheet"], "archive": False}
        ],
    }


@pytest.fixture(scope="function")
def fluffy_context(
    cg_context: CGConfig,
    helpers: StoreHelpers,
    real_housekeeper_api: HousekeeperAPI,
    fluffy_samplesheet_bundle_data,
    fluffy_fastq_hk_bundle_data,
    fluffy_case_id_existing,
    fluffy_sample_lims_id,
) -> CGConfig:
    cg_context.housekeeper_api_ = real_housekeeper_api
    fluffy_analysis_api = FluffyAnalysisAPI(config=cg_context)
    helpers.ensure_hk_version(
        fluffy_analysis_api.housekeeper_api, bundle_data=fluffy_samplesheet_bundle_data
    )
    helpers.ensure_hk_version(fluffy_analysis_api.housekeeper_api, fluffy_fastq_hk_bundle_data)
    example_fluffy_case = helpers.add_case(
        fluffy_analysis_api.status_db,
        internal_id=fluffy_case_id_existing,
        case_id=fluffy_case_id_existing,
        data_analysis=Pipeline.FLUFFY,
    )
    example_fluffy_sample = helpers.add_sample(
        fluffy_analysis_api.status_db,
        internal_id=fluffy_sample_lims_id,
        is_tumour=False,
        application_type="tgs",
        reads=100,
        sequenced_at=dt.datetime.now(),
    )
    helpers.add_flowcell(
        fluffy_analysis_api.status_db, flowcell_id="flowcell", samples=[example_fluffy_sample]
    )
    helpers.add_relationship(
        fluffy_analysis_api.status_db, case=example_fluffy_case, sample=example_fluffy_sample
    )
    cg_context.meta_apis["analysis_api"] = fluffy_analysis_api
    return cg_context
