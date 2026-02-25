from datetime import datetime
from unittest.mock import ANY, Mock, create_autospec

from click.testing import CliRunner
from pytest_mock import MockerFixture

from cg.apps.mutacc_auto import MutaccAutoAPI
from cg.apps.scout.scout_export import ScoutExportCase
from cg.apps.scout.scoutapi import ScoutAPI
from cg.cli.upload import mutacc
from cg.cli.upload.mutacc import process_solved
from cg.constants.process import EXIT_SUCCESS
from cg.meta.upload.mutacc import UploadToMutaccAPI
from cg.models.cg_config import CGConfig, IlluminaConfig, MutaccAutoConfig, RunInstruments


def test_process_solved_success(mocker: MockerFixture):
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
        mutacc_auto=MutaccAutoConfig(
            binary_path="crazy_path",
            config_path="a_path",
            padding=1337,
        ),
    )

    # GIVEN a cli_runner
    cli_runner = CliRunner()

    # WHEN running process_solved
    result = cli_runner.invoke(
        process_solved, ["--scout-instance", "hg19", "--days-ago", "1"], obj=cg_config
    )

    # THEN the command exits successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN the correct Scout instance was used for the export
    get_scout_api_call.assert_called_once_with(cg_config=cg_config, genome_build="hg19")
    # THEN the mutacc auto api was used correctly
    mutacc_auto_init.assert_called_once_with(ANY, config=cg_config.mutacc_auto)

    # THEN the reads were extracted for the case returned by Scout
    extract_reads_mock.assert_called_once_with(scout_case)
