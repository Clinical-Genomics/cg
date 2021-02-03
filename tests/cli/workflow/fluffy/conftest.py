from pathlib import Path

import pytest

from cg.constants import Pipeline
from cg.meta.workflow.fluffy import FluffyAnalysisAPI
from tests.mocks.process_mock import ProcessMock
import datetime as dt


@pytest.fixture(scope="function")
def fluffy_case_id_existing():
    return "lovedkitten"


@pytest.fixture(scope="function")
def fluffy_case_id_non_existing():
    return "nakedmolerat"


@pytest.fixture(scope="function")
def fluffy_sample_lims_id():
    return "ACC9001A1"


@pytest.fixture(scope="function")
def fluffy_dir(tmpdir_factory):
    return tmpdir_factory.mktemp("fluffy")


@pytest.fixture(scope="function")
def fluffy_cases_dir(tmpdir_factory, fluffy_dir):
    return tmpdir_factory.mktemp("cases")


@pytest.fixture(scope="function")
def samplesheet_fixture_path():
    return Path("tests/fixtures/apps/fluffy/SampleSheet.csv")


@pytest.fixture(scope="function")
def fastq_file_fixture_path():
    return Path("tests/fixtures/apps/fluffy/fluffy_fastq.fastq.gz")


@pytest.fixture(scope="function")
def deliverables_yaml_fixture_path():
    return Path("tests/fixtures/apps/fluffy/deliverables.yaml")


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
            {"path": samplesheet_fixture_path.as_posix(), "tags": ["samplesheet"], "archive": False}
        ],
    }


@pytest.fixture(scope="function")
def fluffy_populated_status_db(base_store, helpers, fluffy_case_id_existing, fluffy_sample_lims_id):
    example_fluffy_case = helpers.add_case(
        base_store,
        internal_id=fluffy_case_id_existing,
        case_id=fluffy_case_id_existing,
        data_analysis=Pipeline.FLUFFY,
    )
    example_fluffy_sample = helpers.add_sample(
        base_store,
        internal_id=fluffy_sample_lims_id,
        is_tumour=False,
        application_type="tgs",
        reads=100,
        sequenced_at=dt.datetime.now(),
    )
    helpers.add_flowcell(base_store, flowcell_id="flowcell", samples=[example_fluffy_sample])
    helpers.add_relationship(base_store, case=example_fluffy_case, sample=example_fluffy_sample)
    return base_store


@pytest.fixture(scope="function")
def fluffy_populated_housekeeper_store(
    real_housekeeper_api, helpers, fluffy_fastq_hk_bundle_data, fluffy_samplesheet_bundle_data
):
    helpers.ensure_hk_bundle(
        store=real_housekeeper_api,
        bundle_data=fluffy_fastq_hk_bundle_data,
    )
    helpers.ensure_hk_bundle(store=real_housekeeper_api, bundle_data=fluffy_samplesheet_bundle_data)
    return real_housekeeper_api


@pytest.fixture(scope="function")
def fluffy_context(
    fluffy_populated_housekeeper_store,
    trailblazer_api,
    hermes_api,
    fluffy_populated_status_db,
    fluffy_cases_dir,
    lims_api,
) -> dict:
    fluffy_analysis_api = FluffyAnalysisAPI(
        housekeeper_api=fluffy_populated_housekeeper_store,
        trailblazer_api=trailblazer_api,
        hermes_api=hermes_api,
        lims_api=lims_api,
        status_db=fluffy_populated_status_db,
        config={
            "root_dir": fluffy_cases_dir,
            "binary_path": "echo",
            "config_path": "/dev/null/config.json",
        },
    )
    fluffy_analysis_api.process = ProcessMock()
    return {"fluffy_analysis_api": fluffy_analysis_api}
