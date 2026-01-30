import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner, Result

from cg.cli.base import base
from tests.integration.utils import IntegrationTestPaths


@pytest.mark.xdist_group(name="integration")
@pytest.mark.integration
def test_post_processing(
    test_run_paths: IntegrationTestPaths,
):
    cli_runner = CliRunner()
    # GIVEN a config file with valid database URIs and directories
    config_path: Path = test_run_paths.cg_config_file
    test_root_dir: Path = test_run_paths.test_root_dir

    shutil.copytree(
        Path("tests/fixtures/devices/pacbio/SMRTcells/r84202_20240522_133539"),
        Path(test_root_dir, "pacbio_data_dir", "r84202_20240522_133539"),
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
