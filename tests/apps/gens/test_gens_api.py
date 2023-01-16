"""
    Tests for GensAPI
"""

from pathlib import Path
from typing import Dict

from cg.apps.gens import GensAPI
from cg.utils.commands import Process


def test_instantiate(gens_config: dict):
    """Test to instantiate GensAPI."""
    # GIVEN a gens api config dictionary

    # WHEN instantiating a gens api
    gens_api = GensAPI(gens_config)

    # THEN assert that the adapter was properly instantiated
    assert gens_api.process.config == gens_config["gens"]["config_path"]
    assert gens_api.process.binary == gens_config["gens"]["binary_path"]


def test_gens_api_load(
    gens_config: Dict[str, Dict[str, str]],
    mocker,
    sample_id: str,
    genome_build: str,
    baf_path: Path,
    coverage_path: Path,
    case_id: str,
):
    """Test load sample method."""
    # GIVEN sample_id, genome_build, baf_path, coverage_path, and case_id

    # WHEN uploading a sample with the api, using a mocked Process.run_command method
    api = GensAPI(gens_config)
    mocked_run_command = mocker.patch.object(Process, "run_command")
    api.upload(
        sample_id=sample_id,
        genome_build=genome_build,
        baf_path=baf_path,
        coverage_path=coverage_path,
        case_id=case_id
    )

    # THEN run_command should be called with the list
    mocked_run_command.assert_called_once_with(
        parameters=[
            "load",
            "sample",
            "--sample-id",
            sample_id,
            "--genome-build",
            genome_build,
            "--baf",
            baf_path.as_posix(),
            "--coverage",
            coverage_path.as_posix(),
            "--case-id",
            case_id,
        ]
    )

