from pathlib import Path

import pytest
from click.testing import CliRunner, Result

from cg.cli.base import base
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

    # WHEN running post-process all
    result: Result = cli_runner.invoke(
        base,
        [
            "--config",
            config_path.as_posix(),
            "upload",
            "scout",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 1
