from datetime import datetime as dt
from pathlib import Path

import pytest
from click.testing import CliRunner, Result

from cg.cli.base import base
from cg.constants.constants import DataDelivery, Workflow
from cg.store.store import Store
from tests.integration.utils import IntegrationTestPaths
from tests.store_helpers import StoreHelpers


@pytest.mark.xdist_group(name="integration")
@pytest.mark.integration
def test_upload_raredisease_to_scout(
    status_db: Store,
    helpers: StoreHelpers,
    test_run_paths: IntegrationTestPaths,
):
    cli_runner = CliRunner()

    # GIVEN a config file with valid database URIs and directories
    config_path: Path = test_run_paths.cg_config_file
    # test_root_dir: Path = test_run_paths.test_root_dir

    # GIVEN a raredisease case
    case = helpers.add_case(
        store=status_db, data_analysis=Workflow.RAREDISEASE, data_delivery=DataDelivery.SCOUT
    )

    # GIVEN a completed raredisease analysis of that case
    analysis = helpers.add_analysis(
        store=status_db,
        case=case,
        workflow=Workflow.RAREDISEASE,
        data_delivery=DataDelivery.SCOUT,
        completed_at=dt.now(),
    )

    # GIVEN a housekeeper bundle for that analysis
    hk_bundle = helpers.ensure_hk_bundle()

    # WHEN running post-process all
    result: Result = cli_runner.invoke(
        base,
        ["--config", config_path.as_posix(), "upload", "scout", case.internal_id],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
