from datetime import datetime
from unittest.mock import ANY, Mock, create_autospec

import pytest
from click.testing import CliRunner
from pytest_mock import MockerFixture

from cg.apps.mutacc_auto import MutaccAutoAPI
from cg.apps.scout.scout_export import ScoutExportCase
from cg.apps.scout.scoutapi import ScoutAPI
from cg.cli.upload import mutacc
from cg.cli.upload.mutacc import add_to_database, process_solved
from cg.constants import Workflow
from cg.constants.constants import BedVersionGenomeVersion
from cg.constants.process import EXIT_SUCCESS
from cg.meta.upload.mutacc import UploadToMutaccAPI
from cg.models.cg_config import CGConfig, IlluminaConfig, MutaccAutoConfig, RunInstruments
from cg.store.models import Case
from cg.store.store import Store


@pytest.fixture
def cg_config() -> CGConfig:
    return create_autospec(
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


@pytest.mark.parametrize(
    "genome_version, expected_mutacc_auto_config",
    [
        (BedVersionGenomeVersion.HG19, "mutacc_auto_hg19"),
        (BedVersionGenomeVersion.HG38, "mutacc_auto_hg38"),
    ],
)
def test_process_solved_success(
    mocker: MockerFixture,
    cg_config: CGConfig,
    genome_version: BedVersionGenomeVersion,
    expected_mutacc_auto_config: str,
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


def test_process_solved_exclude_nallo(
    mocker: MockerFixture,
    cg_config: CGConfig,
):
    # GIVEN a case can be exported from Scout
    rd_scout_case = ScoutExportCase(
        _id="case_id_raredisease", analysis_date=datetime.now(), owner="owner", individuals=[]
    )
    nallo_scout_case = ScoutExportCase(
        _id="case_id_nallo", analysis_date=datetime.now(), owner="owner", individuals=[]
    )
    scout_api: ScoutAPI = create_autospec(ScoutAPI)
    scout_api.get_solved_cases = Mock(return_value=[rd_scout_case, nallo_scout_case])
    get_scout_api_call = mocker.patch.object(
        mutacc, "get_scout_api_by_genome_build", return_value=scout_api
    )

    mutacc_auto_init = mocker.spy(MutaccAutoAPI, "__init__")
    extract_reads_mock = mocker.patch.object(UploadToMutaccAPI, "extract_reads")

    # GIVEN a mocked store with a Raredisease case and a Nallo case
    rd_statusdb_case: Case = create_autospec(
        Case, internal_id="case_id_raredisease", data_analysis=Workflow.RAREDISEASE
    )
    nallo_statusdb_case: Case = create_autospec(
        Case, internal_id="case_id_nallo", data_analysis=Workflow.NALLO
    )
    status_db: Store = create_autospec(Store)
    setattr(cg_config, "status_db", status_db)
    status_db.get_case_by_internal_id_strict = lambda internal_id: (
        rd_statusdb_case if internal_id == "case_id_raredisease" else nallo_statusdb_case
    )

    # GIVEN a cli_runner
    cli_runner = CliRunner()

    # WHEN running process_solved
    result = cli_runner.invoke(
        process_solved,
        ["--genome-version", BedVersionGenomeVersion.HG38, "--days-ago", "1"],
        obj=cg_config,
    )

    # THEN the command exits successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN the correct Scout instance was used for the export
    get_scout_api_call.assert_called_once_with(
        cg_config=cg_config, genome_build=BedVersionGenomeVersion.HG38
    )
    # THEN the mutacc auto api was used correctly
    mutacc_auto_init.assert_called_once_with(ANY, config=cg_config.mutacc_auto_hg38)
    # THEN the reads were extracted for the case returned by Scout
    extract_reads_mock.assert_called_once_with(rd_scout_case)


@pytest.mark.parametrize(
    "genome_version, expected_mutacc_auto_config",
    [
        (BedVersionGenomeVersion.HG19, "mutacc_auto_hg19"),
        (BedVersionGenomeVersion.HG38, "mutacc_auto_hg38"),
    ],
)
def test_add_to_database_success(
    cg_config: CGConfig,
    genome_version: BedVersionGenomeVersion,
    expected_mutacc_auto_config: str,
    mocker: MockerFixture,
):
    mutacc_auto_init = mocker.spy(MutaccAutoAPI, "__init__")
    import_reads_call = mocker.patch.object(MutaccAutoAPI, "import_reads")

    # GIVEN a cg config
    cli_runner = CliRunner()

    # WHEN calling mutacc function add_to_database
    result = cli_runner.invoke(
        add_to_database, args=["--genome-version", genome_version], obj=cg_config
    )

    # THEN the command exits successfully
    assert result.exit_code == EXIT_SUCCESS
    # THEN the mutacc auto api was used correctly
    mutacc_auto_init.assert_called_once_with(
        ANY, config=getattr(cg_config, expected_mutacc_auto_config)
    )
    # THEN the import reads method is called
    import_reads_call.assert_called_once()
