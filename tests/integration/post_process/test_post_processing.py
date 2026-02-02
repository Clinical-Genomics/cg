import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner, Result
from housekeeper.store.store import Store as HousekeeperStore

from cg.cli.base import base
from cg.store.store import Store
from tests.integration.utils import IntegrationTestPaths
from tests.store_helpers import StoreHelpers


@pytest.mark.xdist_group(name="integration")
@pytest.mark.integration
def test_post_processing(
    status_db: Store,
    helpers: StoreHelpers,
    housekeeper_db: HousekeeperStore,
    test_run_paths: IntegrationTestPaths,
):
    cli_runner = CliRunner()
    # GIVEN a config file with valid database URIs and directories
    config_path: Path = test_run_paths.cg_config_file
    test_root_dir: Path = test_run_paths.test_root_dir

    helpers.add_sample(store=status_db, internal_id="ACC15752A3")

    shutil.copytree(
        Path("tests/fixtures/devices/pacbio/SMRTcells/r84202_20240522_133539"),
        Path(test_root_dir, "pacbio_data_dir", "r84202_20240522_133539"),
        ignore=lambda src, names: [".DS_Store"],
    )

    # WHEN running nallo start-available
    result: Result = cli_runner.invoke(
        base,
        [
            "--config",
            config_path.as_posix(),
            "post-process",
            "all",
        ],
        catch_exceptions=False,
    )

    assert result == "?"
    assert result == "?"
