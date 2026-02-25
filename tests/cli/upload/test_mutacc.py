from datetime import datetime
from unittest.mock import ANY, Mock, create_autospec

import pytest
from click.testing import CliRunner
from pytest_mock import MockerFixture

from cg.apps.mutacc_auto import MutaccAutoAPI
from cg.apps.scout.scout_export import ScoutExportCase
from cg.apps.scout.scoutapi import ScoutAPI
from cg.cli.upload import mutacc
from cg.cli.upload.mutacc import process_solved
from cg.constants.constants import BedVersionGenomeVersion
from cg.constants.process import EXIT_SUCCESS
from cg.meta.upload.mutacc import UploadToMutaccAPI
from cg.models.cg_config import CGConfig, IlluminaConfig, MutaccAutoConfig, RunInstruments


@pytest.mark.parametrize(
    "genome_version, expected_mutacc_auto_config",
    [
        (BedVersionGenomeVersion.HG19, "mutacc_auto_hg19"),
        (BedVersionGenomeVersion.HG38, "mutacc_auto_hg38"),
    ],
)
def test_process_solved_success(
    mocker: MockerFixture, genome_version: BedVersionGenomeVersion, expected_mutacc_auto_config: str
):
    # GIVEN a case can be exported from Scout
    scout_case = ScoutExportCase(
        _id="1", analysis_date=datetime.now(), owner="owner", individuals=[]
    )
    scout_api: ScoutAPI = create_autospec(ScoutAPI)
    scout_api.get_solved_cases = Mock(return_value=[scout_case])
    get_scout_api_call = mocker.patch.object(
        mutacc, "get_scout_api_by_genome_build", return_value=scout_api
    )

    mutacc_auto_init = mocker.spy(MutaccAutoAPI, "__init__")
    extract_reads_mock = mocker.patch.object(UploadToMutaccAPI, "extract_reads")

    # GIVEN a cg config
    cg_config: CGConfig = create_autospec(
        CGConfig,
        delivery_path="delivery/path",
        run_instruments=create_autospec(
            RunInstruments,
            illumina=create_autospec(IlluminaConfig, demultiplexed_runs_dir="some_dir"),
        ),
        mutacc_auto_hg19=MutaccAutoConfig(
            binary_path="crazy_path",
            config_path="a_path",
            padding=1337,
        ),
        mutacc_auto_hg38=MutaccAutoConfig(
            binary_path="what_in_the_world",
            config_path="no_path",
            padding=666,
        ),
    )

    # GIVEN a cli_runner
    cli_runner = CliRunner()

    # WHEN running process_solved
    result = cli_runner.invoke(
        process_solved, ["--genome-version", genome_version, "--days-ago", "1"], obj=cg_config
    )

    # THEN the command exits successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN the correct Scout instance was used for the export
    get_scout_api_call.assert_called_once_with(cg_config=cg_config, genome_build=genome_version)
    # THEN the mutacc auto api was used correctly
    mutacc_auto_init.assert_called_once_with(
        ANY, config=getattr(cg_config, expected_mutacc_auto_config)
    )
    # THEN the reads were extracted for the case returned by Scout
    extract_reads_mock.assert_called_once_with(scout_case)
