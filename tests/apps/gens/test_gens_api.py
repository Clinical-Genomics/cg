"""Tests for GensAPI."""

from pathlib import Path

from cg.apps.gens import GensAPI
from cg.constants.gene_panel import GENOME_BUILD_37
from cg.utils.commands import Process


def test_instantiate(gens_config: dict[str, dict[str, str]]):
    """Test to instantiate GensAPI."""
    # GIVEN a Gens API config dictionary

    # WHEN instantiating a Gens API
    gens_api = GensAPI(gens_config)

    # THEN assert that the object was properly instantiated
    assert gens_api.process.config == gens_config["gens"]["config_path"]
    assert gens_api.process.binary == gens_config["gens"]["binary_path"]


def test_gens_api_load(
    case_id: str,
    gens_config: dict[str, dict[str, str]],
    gens_coverage_path: Path,
    gens_fracsnp_path: Path,
    mocker,
    sample_id: str,
):
    """Test load sample method."""
    # WHEN uploading a sample with the API, using a mocked Process.run_command method
    api: GensAPI = GensAPI(gens_config)
    mocked_run_command = mocker.patch.object(Process, "run_command")
    api.load(
        sample_id=sample_id,
        genome_build=GENOME_BUILD_37,
        baf_path=gens_fracsnp_path.as_posix(),
        coverage_path=gens_coverage_path.as_posix(),
        case_id=case_id,
    )

    # THEN run_command should be called with the list
    mocked_run_command.assert_called_once_with(
        dry_run=False,
        parameters=[
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
    )
