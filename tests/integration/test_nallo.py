from collections.abc import Callable
from pathlib import Path
from unittest.mock import Mock

import pytest
from click.testing import CliRunner, Result
from housekeeper.store.store import Store as HousekeeperStore
from pytest_httpserver import HTTPServer
from pytest_mock import MockerFixture

from cg.cli.base import base
from cg.constants.constants import CaseActions, Workflow
from cg.constants.tb import AnalysisType
from cg.store.models import Case, Order, Sample
from cg.store.store import Store
from cg.utils import commands
from tests.integration.utils import (
    IntegrationTestPaths,
    copy_integration_test_file,
    create_empty_file,
    create_integration_test_sample,
    expect_to_add_pending_analysis_to_trailblazer,
    expect_to_get_latest_analysis_with_empty_response_from_trailblazer,
)
from tests.store_helpers import StoreHelpers


@pytest.fixture(autouse=True)
def current_workflow() -> Workflow:
    return Workflow.NALLO


@pytest.fixture
def new_tower_id() -> str:
    return "1uxZE9JM7Tl58r"


@pytest.fixture(autouse=True)
def mocked_commands_and_outputs(
    new_tower_id: str, scout_export_manged_variants_stdout: bytes, scout_export_panel_stdout: bytes
) -> dict[str, bytes]:
    return {
        "scout_38_config_path export panel": scout_export_panel_stdout,
        "scout_38_config_path export managed": scout_export_manged_variants_stdout,
        "tower_binary_path launch": f"Workflow {new_tower_id} submitted at [<WORKSPACE>] workspace.".encode(),
    }


@pytest.mark.xdist_group(name="integration")
@pytest.mark.integration
def test_start_available_nallo(
    helpers: StoreHelpers,
    housekeeper_db: HousekeeperStore,
    httpserver: HTTPServer,
    status_db: Store,
    test_run_paths: IntegrationTestPaths,
    mock_run_commands: Callable,
    new_tower_id: str,
    mocker: MockerFixture,
):
    """Test a successful run of the command 'cg workflow nallo start-available'
    with one case to be analysed that has not been analysed before."""
    cli_runner = CliRunner()

    # GIVEN a config file with valid database URIs and directories
    config_path: Path = test_run_paths.cg_config_file

    # GIVEN the necessary configured directories exist
    test_root_dir = test_run_paths.test_root_dir
    copy_integration_test_file(
        from_path=Path("tests/integration/config/nallo-params.yaml"),
        to_path=Path(test_root_dir, "nallo_params.yaml"),
    )
    copy_integration_test_file(
        from_path=Path("tests/integration/config/platform.config"),
        to_path=Path(test_root_dir, "platform.config"),
    )
    create_empty_file(Path(test_root_dir, "nallo_config.config"))
    create_empty_file(Path(test_root_dir, "nallo_resources.config"))

    # GIVEN a case with existing qc files
    ticket_id = 12345
    case: Case = helpers.add_case(
        store=status_db, data_analysis=Workflow.NALLO, ticket=str(ticket_id)
    )

    # GIVEN an order associated with the case
    order: Order = helpers.add_order(
        store=status_db, ticket_id=ticket_id, customer_id=case.customer_id
    )
    status_db.link_case_to_order(order_id=order.id, case_id=case.id)

    # GIVEN a sample associated with the case, with:
    #  - flow cell and sequencing run stored in StatusDB
    #  - a gzipped-fastq file on disk
    #  - a bundle associated with the fastq file in Housekeeper
    sample: Sample = create_integration_test_sample(
        status_db=status_db,
        housekeeper_db=housekeeper_db,
        test_run_paths=test_run_paths,
        application_type=AnalysisType.WGS,
        flow_cell_id="nallo_flow_cell_id",
    )

    helpers.relate_samples(base_store=status_db, case=case, samples=[sample])

    # GIVEN that the Scout command returns exported panel data
    subprocess_mock = mocker.patch.object(commands, "subprocess")
    subprocess_mock.run = Mock(side_effect=mock_run_commands)

    # GIVEN the Trailblazer API returns no ongoing analysis for the case
    expect_to_get_latest_analysis_with_empty_response_from_trailblazer(
        trailblazer_server=httpserver, case_id=case.internal_id
    )

    # GIVEN a new pending analysis can be added to the Trailblazer API
    # case_path = Path(mip_dna_path, "cases", case.internal_id)
    expect_to_add_pending_analysis_to_trailblazer(
        analysis_type=AnalysisType.WGS,
        out_dir=Path(test_root_dir, "nallo_root_path", case.internal_id),
        case=case,
        config_path=Path(test_root_dir, "nallo_root_path", case.internal_id, "tower_ids.yaml"),
        ticket_id=ticket_id,
        trailblazer_server=httpserver,
        tower_workflow_id=new_tower_id,
        workflow=Workflow.NALLO,
        workflow_manager="nf_tower",
    )

    # WHEN running mip-dna start-available
    result: Result = cli_runner.invoke(
        base,
        [
            "--config",
            config_path.as_posix(),
            "workflow",
            "nallo",
            "start-available",
        ],
        catch_exceptions=False,
    )

    # THEN a successful exit code is returned
    assert result.exit_code == 0

    # THEN the analysis should be started in the correct way
    _first_call = subprocess_mock.mock_calls[0]
    second_call = subprocess_mock.mock_calls[1]

    expected_run_command: list[str] = [
        f"{test_root_dir}/tower_binary_path",
        "launch",
        "--work-dir",
        f"{test_root_dir}/nallo_root_path/{case.internal_id}/work",
        "--profile",
        "nallo_profile",
        "--params-file",
        f"{test_root_dir}/nallo_root_path/{case.internal_id}/{case.internal_id}_params_file.yaml",
        "--config",
        f"{test_root_dir}/nallo_root_path/{case.internal_id}/{case.internal_id}_nextflow_config.json",
        "--name",
        case.internal_id,
        "--revision",
        "nallo_revision",
        "--compute-env",
        "nallo_compute_env-normal",
        "nallo_tower_workflow",
    ]
    assert second_call.args[0] == expected_run_command

    # THEN an analysis has been created for the case
    assert len(case.analyses) == 1

    # THEN the case action is set to running
    status_db.session.refresh(case)
    assert case.action == CaseActions.RUNNING

    # TODO check that all files have been created with correct contents
