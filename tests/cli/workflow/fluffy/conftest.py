import pytest

from cg.meta.workflow.fluffy import FluffyAnalysisAPI
from tests.mocks.process_mock import ProcessMock


@pytest.fixture()
def fluffy_case_id_existing():
    return "lovedkitten"


@pytest.fixture()
def fluffy_case_id_non_existing():
    return "nakedmolerat"


@pytest.fixture()
def fluffy_dir(tmpdir_factory):
    return tmpdir_factory.mktemp("fluffy")


@pytest.fixture()
def fluffy_cases_dir(tmpdir_factory, fluffy_dir):
    return tmpdir_factory.mktemp(f"{fluffy_dir}/cases")


@pytest.fixture()
def fluffy_context(
    real_housekeeper_api, trailblazer_api, hermes_api, lims_api, base_store, fluffy_cases_dir
):
    fluffy_analysis_api = FluffyAnalysisAPI(
        housekeeper_api=real_housekeeper_api,
        trailblazer_api=trailblazer_api,
        hermes_api=hermes_api,
        lims_api=lims_api,
        status_db=base_store,
        config={
            "root_dir": fluffy_cases_dir,
            "binary_path": "echo",
            "config_path": "/dev/null/config.json",
        },
    )
    fluffy_analysis_api.process = ProcessMock()
    return {"fluffy_analysis_api": fluffy_analysis_api}
