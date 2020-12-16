"""Tests for uploading analysis results to housekeeper"""
from pathlib import Path

from click.testing import CliRunner

from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.cli.store.analysis import fluffy_cmd
from cg.meta.upload.analysis import UploadAnalysisApi
from tests.mocks.process_mock import ProcessMock


def test_upload_fluffy_analysis(
    fluffy_process: ProcessMock,
    housekeeper_api: HousekeeperAPI,
    case_id: str,
    fluffy_deliverables_file: Path,
):
    hermes_config = {"hermes": {"binary_path": "hermes"}}
    hermes_api = HermesApi(config=hermes_config)
    hermes_api.process = fluffy_process
    upload_api = UploadAnalysisApi(hk_api=housekeeper_api, hermes_api=hermes_api)
    # GIVEN a process with output from hermes where fluffy deliverables has been converted
    # GIVEN a housekeeper instance without the bundle in question
    assert not housekeeper_api.bundle(name=case_id)
    # GIVEN a cli runner
    runner = CliRunner()

    # WHEN uploading the analysis results to housekeper with cli
    runner.invoke(fluffy_cmd, [str(fluffy_deliverables_file)], obj={"upload_api": upload_api})

    # THEN assert that the new bundle exists in housekeeper
    assert housekeeper_api.bundle(name=case_id)
