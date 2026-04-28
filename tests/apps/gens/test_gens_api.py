"""Tests for GensAPI."""

import subprocess
from pathlib import Path
from unittest.mock import ANY

from mock import create_autospec

from cg.apps.gens import GensAPI
from cg.constants.gene_panel import GENOME_BUILD_37
from cg.constants.process import EXIT_SUCCESS
from cg.models.cg_config import GENSConfig


def test_instantiate(gens_config: GENSConfig):
    """Test to instantiate GensAPI."""
    # GIVEN a Gens API config dictionary

    # WHEN instantiating a Gens API
    gens_api = GensAPI(gens_config)

    # THEN assert that the object was properly instantiated
    assert gens_api.config_path == gens_config.config_path
    assert gens_api.shell_env["CONFIG_FILE"] == gens_config.config_path
    assert gens_api.binary_path == gens_config.binary_path


def test_gens_api_load(
    case_id: str,
    gens_config: dict[str, dict[str, str]],
    gens_coverage_path: Path,
    gens_fracsnp_path: Path,
    mocker,
    sample_id: str,
):
    """Test load sample method."""
    # GIVEN a GENS API with mocked subprocess.run()
    api: GensAPI = GensAPI(gens_config)
    mocked_subprocess_run = mocker.patch.object(subprocess, "run")
    subprocess.run.return_value = create_autospec(
        subprocess.CompletedProcess, returncode=EXIT_SUCCESS
    )

    # WHEN uploading a sample
    api.load(
        sample_id=sample_id,
        genome_build=GENOME_BUILD_37,
        baf_path=gens_fracsnp_path.as_posix(),
        coverage_path=gens_coverage_path.as_posix(),
        case_id=case_id,
    )

    # THEN the subprocess.run() should be called with
    mocked_subprocess_run.assert_called_once_with(
        args=[
            api.binary_path,
            "load",
            "sample",
            "--force",
            "--sample-id",
            sample_id,
            "--genome-build",
            GENOME_BUILD_37,
            "--baf",
            gens_fracsnp_path.as_posix(),
            "--coverage",
            gens_coverage_path.as_posix(),
            "--case-id",
            case_id,
        ],
        check=False,
        env=ANY,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # THEN the subprocess.run() should have been invoked with a shell variable $CONFIG_FILE
    assert "CONFIG_FILE" in mocked_subprocess_run.call_args[1]["env"].keys()

    # THEN that shell variable should be the config path
    assert mocked_subprocess_run.call_args[1]["env"]["CONFIG_FILE"] == api.config_path
