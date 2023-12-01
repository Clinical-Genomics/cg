import logging
from pathlib import Path
from unittest import mock

from click.testing import CliRunner, Result

from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.hermes.models import CGDeliverables
from cg.cli.workflow.balsamic.base import (
    balsamic,
    start,
    start_available,
    store,
    store_available,
)
from cg.constants.constants import CaseActions, FileExtensions
from cg.io.json import write_json
from cg.io.yaml import write_yaml
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store import Store
from tests.conftest import create_process_response

EXIT_SUCCESS = 0


def test_balsamic_no_args(cli_runner: CliRunner, balsamic_context: CGConfig):
    """Test to see that running BALSAMIC without options prints help and doesn't result in an error"""
    # GIVEN no arguments or options besides the command call

    # WHEN running command
    result = cli_runner.invoke(balsamic, [], obj=balsamic_context)

    # THEN command runs successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN help should be printed
    assert "help" in result.output


def test_start(
    cli_runner: CliRunner,
    balsamic_context: CGConfig,
    mock_config,
    caplog,
    helpers,
    mock_analysis_flow_cell,
):
    """Test to ensure all parts of start command will run successfully given ideal conditions"""
    caplog.set_level(logging.INFO)

    # GIVEN case id for which we created a config file
    case_id = "balsamic_case_wgs_single"

    # WHEN dry running
    result = cli_runner.invoke(start, [case_id, "--dry-run"], obj=balsamic_context)

    # THEN command should execute successfully
    assert result.exit_code == EXIT_SUCCESS
    assert case_id in caplog.text


def test_store(
    cli_runner: CliRunner,
    balsamic_context: CGConfig,
    real_housekeeper_api,
    mock_config,
    mock_deliverable,
    caplog,
    hermes_deliverables,
    mocker,
):
    """Test to ensure all parts of store command are run successfully given ideal conditions"""
    caplog.set_level(logging.INFO)

    # GIVEN case-id for which we created a config file, deliverables file, and analysis_finish file
    case_id = "balsamic_case_wgs_single"

    # Set Housekeeper to an empty real Housekeeper store
    balsamic_context.housekeeper_api_ = real_housekeeper_api
    balsamic_context.meta_apis["analysis_api"].housekeeper_api = real_housekeeper_api

    # Make sure the bundle was not present in the store
    assert not balsamic_context.housekeeper_api.bundle(case_id)

    # Make sure  analysis not already stored in ClinicalDB
    assert not balsamic_context.status_db.get_case_by_internal_id(internal_id=case_id).analyses

    # GIVEN that HermesAPI returns a deliverables output
    mocker.patch.object(HermesApi, "convert_deliverables")
    HermesApi.convert_deliverables.return_value = CGDeliverables(**hermes_deliverables)

    # GIVEN that the latest analysis is completed
    mocker.patch.object(
        balsamic_context.meta_apis["analysis_api"].trailblazer_api,
        "is_latest_analysis_completed",
        return_value=True,
    )

    # WHEN running command
    result = cli_runner.invoke(store, [case_id, "--dry-run"], obj=balsamic_context)

    # THEN bundle should be successfully added to HK and STATUS
    assert result.exit_code == EXIT_SUCCESS
    assert "Analysis successfully stored in Housekeeper" in caplog.text
    assert "Analysis successfully stored in StatusDB" in caplog.text
    assert balsamic_context.status_db.get_case_by_internal_id(internal_id=case_id).analyses
    assert balsamic_context.housekeeper_api.bundle(case_id)


def test_start_available_dry(
    cli_runner: CliRunner, balsamic_context: CGConfig, caplog, mocker, mock_analysis_flow_cell
):
    """Test to ensure all parts of compound start-available command are executed given ideal conditions
    Test that start-available picks up eligible cases and does not pick up ineligible ones"""
    caplog.set_level(logging.INFO)

    # GIVEN CASE ID of sample where read counts pass threshold
    case_id_success = "balsamic_case_wgs_single"

    # GIVEN CASE ID where read counts did not pass the threshold
    case_id_not_enough_reads = "balsamic_case_tgs_paired"

    # Ensure the config is mocked to run compound command
    Path.mkdir(
        Path(
            balsamic_context.meta_apis["analysis_api"].get_case_config_path(case_id_success)
        ).parent,
        exist_ok=True,
    )
    Path(balsamic_context.meta_apis["analysis_api"].get_case_config_path(case_id_success)).touch(
        exist_ok=True
    )

    # GIVEN decompression is not needed
    mocker.patch.object(BalsamicAnalysisAPI, "resolve_decompression")
    BalsamicAnalysisAPI.resolve_decompression.return_value = None

    # WHEN running command
    result = cli_runner.invoke(start_available, ["--dry-run"], obj=balsamic_context)

    # THEN command exits with a successful exit code
    assert result.exit_code == EXIT_SUCCESS

    # THEN it should successfully identify the one case eligible for auto-start
    assert f"Starting analysis for {case_id_success}" in caplog.text

    # THEN the ineligible case should NOT be run
    assert case_id_not_enough_reads not in caplog.text


def assert_binary_called_with_correct_commands(sub_process_mock):
    assert " ".join(sub_process_mock.call_args_list[0].args[0]).startswith(
        "/bin/balsamic config case"
    )
    assert " ".join(sub_process_mock.call_args_list[1].args[0]).startswith(
        "/bin/balsamic run analysis"
    )


def assert_run_directory_contains_correct_files(case_directory: Path):
    case_id: str = case_directory.name
    assert Path(case_directory, "analysis").exists()
    assert Path(case_directory, "analysis", f"slurm_jobids{FileExtensions.YAML}").exists()
    assert Path(case_directory, f"{case_id}{FileExtensions.JSON}").exists()
    assert Path(case_directory, "fastq").exists()
    assert Path(case_directory, "fastq").glob("*R_1.fastq.gz")
    assert Path(case_directory, "fastq").glob("*R_2.fastq.gz")


def test_start_available(balsamic_context: CGConfig, cli_runner, balsamic_config_raw):
    status_db: Store = balsamic_context.status_db
    analysis_api: BalsamicAnalysisAPI = balsamic_context.meta_apis["analysis_api"]

    # GIVEN a case with enough reads to start
    case_to_be_started = status_db.get_case_by_internal_id("balsamic_case_wgs_single")

    # GIVEN a case with top few reads to start
    case_that_will_not_be_started = status_db.get_case_by_internal_id("balsamic_case_tgs_paired")

    with mock.patch(
        "cg.utils.commands.subprocess.run",
        side_effect=SideEffect(balsamic_config_raw, create_config_file, create_slurm_id_file),
    ) as sub_process_mock:
        # WHEN starting the cases that are ready
        result: Result = cli_runner.invoke(start_available, obj=balsamic_context)

    # THEN the command should run successfully
    assert result.exit_code == 0

    # THEN the case directory should contain the correct files
    assert_run_directory_contains_correct_files(
        analysis_api.get_case_path(case_to_be_started.internal_id)
    )

    # THEN the balsamic binary should be called with the correct commands
    assert_binary_called_with_correct_commands(sub_process_mock)

    # THEN trailblazer should be called with the correct arguments
    # TODO add some assert here

    # THEN the case action should be set to running
    assert case_to_be_started.action == CaseActions.RUNNING
    assert case_that_will_not_be_started.action != CaseActions.RUNNING


def test_store_available(
    cli_runner: CliRunner,
    balsamic_context: CGConfig,
    real_housekeeper_api,
    mock_config,
    mock_deliverable,
    caplog,
    mocker,
    hermes_deliverables,
    mock_analysis_flow_cell,
):
    """Test to ensure all parts of compound store-available command are executed given ideal conditions
    Test that sore-available picks up eligible cases and does not pick up ineligible ones"""
    caplog.set_level(logging.INFO)

    # GIVEN CASE ID of sample where read counts pass threshold
    case_id_success = "balsamic_case_wgs_single"

    # GIVEN CASE ID where analysis finish is not mocked
    case_id_fail = "balsamic_case_wgs_paired"

    # Ensure the config is mocked for fail case to run compound command
    Path.mkdir(
        Path(balsamic_context.meta_apis["analysis_api"].get_case_config_path(case_id_fail)).parent,
        exist_ok=True,
    )
    Path(balsamic_context.meta_apis["analysis_api"].get_case_config_path(case_id_fail)).touch(
        exist_ok=True
    )
    # GIVEN that the latest analysis is completed
    mocker.patch.object(
        balsamic_context.meta_apis["analysis_api"].trailblazer_api,
        "is_latest_analysis_completed",
        return_value=True,
    )
    # GIVEN that the report file is created
    mocker.patch.object(BalsamicAnalysisAPI, "report_deliver", return_value=None)

    # GIVEN that HermesAPI returns a deliverables output
    hermes_deliverables["bundle_id"] = case_id_success
    mocker.patch.object(HermesApi, "convert_deliverables")
    HermesApi.convert_deliverables.return_value = CGDeliverables(**hermes_deliverables)

    # Ensure case was successfully picked up by start-available and status set to running
    result = cli_runner.invoke(start_available, ["--dry-run"], obj=balsamic_context)
    balsamic_context.status_db.get_case_by_internal_id(case_id_success).action = "running"
    balsamic_context.status_db.session.commit()

    # THEN command exit with success
    assert result.exit_code == EXIT_SUCCESS
    assert case_id_success in caplog.text
    assert balsamic_context.status_db.get_case_by_internal_id(case_id_success).action == "running"

    balsamic_context.housekeeper_api_ = real_housekeeper_api
    balsamic_context.meta_apis["analysis_api"].housekeeper_api = real_housekeeper_api

    # WHEN running command
    result = cli_runner.invoke(store_available, obj=balsamic_context)

    # THEN command exits successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN case id with analysis_finish gets picked up
    assert case_id_success in caplog.text

    # THEN case has analyses
    assert balsamic_context.status_db.get_case_by_internal_id(case_id_success).analyses

    # THEN bundle can be found in Housekeeper
    assert balsamic_context.housekeeper_api.bundle(case_id_success)

    # THEN bundle added successfully and action set to None
    assert balsamic_context.status_db.get_case_by_internal_id(case_id_success).action is None


class SideEffect:
    def __init__(self, balsamic_config_content, *functions):
        self.functions = iter(functions)
        self.balsamic_config_content = balsamic_config_content

    def __call__(self, *args, **kwargs):
        function = next(self.functions)
        return function(self.balsamic_config_content, *args, **kwargs)


def create_config_file(config_content, command, **kwargs):
    case_id = command[command.index("--case-id") + 1]
    parent_dir = Path(command[command.index("--analysis-dir") + 1])
    config_file: Path = Path(parent_dir, case_id, f"{case_id}{FileExtensions.JSON}")
    write_json(file_path=config_file, content=config_content)
    return create_process_response()


def create_slurm_id_file(_, command, **kwargs):
    case_directory: Path = Path(command[command.index("--sample-config") + 1]).parent
    case_id: str = case_directory.name
    Path(case_directory, "analysis").mkdir()
    job_id_file: Path = Path(case_directory, "analysis", f"slurm_jobids{FileExtensions.YAML}")
    write_yaml(file_path=job_id_file, content={case_id: ["1234", "5678", "9012"]})
    return create_process_response()
