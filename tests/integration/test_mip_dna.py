from collections.abc import Callable
from pathlib import Path
from unittest.mock import ANY, Mock

import pytest
from click.testing import CliRunner, Result
from housekeeper.store.store import Store as HousekeeperStore
from pytest_httpserver import HTTPServer
from pytest_mock import MockerFixture

from cg.apps.environ import environ_email
from cg.cli.base import base
from cg.constants.constants import CaseActions, Workflow
from cg.constants.gene_panel import GenePanelMasterList
from cg.constants.tb import AnalysisType
from cg.services.analysis_starter.submitters.subprocess import submitter
from cg.store.models import Case, Order, Sample
from cg.store.store import Store
from cg.utils import commands
from tests.integration.utils import (
    IntegrationTestPaths,
    copy_integration_test_file,
    create_integration_test_sample,
    expect_file_contents,
    expect_to_add_pending_analysis_to_trailblazer,
    expect_to_get_latest_analysis_with_empty_response_from_trailblazer,
)
from tests.store_helpers import StoreHelpers


@pytest.fixture(autouse=True)
def current_workflow() -> Workflow:
    return Workflow.MIP_DNA


@pytest.fixture(autouse=True)
def mocked_commands_and_outputs(
    scout_export_manged_variants_stdout: bytes,
    scout_export_panel_stdout: bytes,
) -> dict[str, bytes]:
    return {
        "/scout/binary --config /scout/config export panel": scout_export_panel_stdout,
        "/scout/binary --config /scout/config export managed": scout_export_manged_variants_stdout,
    }


@pytest.mark.xdist_group(name="integration")
@pytest.mark.integration
def test_start_available_mip_dna(
    test_run_paths: IntegrationTestPaths,
    helpers: StoreHelpers,
    housekeeper_db: HousekeeperStore,
    httpserver: HTTPServer,
    mock_run_commands: Callable,
    scout_export_panel_stdout: bytes,
    scout_export_manged_variants_stdout: bytes,
    status_db: Store,
    mocker: MockerFixture,
):
    """Test a successful run of the command 'cg workflow mip-dna start-available'
    with one case to be analysed that has not been analysed before."""
    cli_runner = CliRunner()

    # GIVEN a MIP-DNA root directory
    test_root_dir: Path = test_run_paths.test_root_dir

    # GIVEN a config file with valid database URIs and directories
    config_path: Path = test_run_paths.cg_config_file

    mip_dna_path = Path(test_root_dir, "mip-dna")

    # GIVEN a case with existing qc files
    ticket_id = 12345
    case: Case = helpers.add_case(
        store=status_db, data_analysis=Workflow.MIP_DNA, ticket=str(ticket_id)
    )
    _create_qc_file(test_root_dir, case)

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
        flow_cell_id="mip-dna-flow-cell",
    )

    helpers.relate_samples(base_store=status_db, case=case, samples=[sample])

    # GIVEN that the Scout command returns exported panel data
    subprocess_mock = mocker.patch.object(commands, "subprocess")
    subprocess_mock.run = Mock(side_effect=mock_run_commands)

    # GIVEN an email address can be determined from the environment
    email: str = environ_email()

    # GIVEN the Trailblazer API returns no ongoing analysis for the case
    expect_to_get_latest_analysis_with_empty_response_from_trailblazer(
        trailblazer_server=httpserver, case_id=case.internal_id
    )

    # GIVEN a new pending analysis can be added to the Trailblazer API
    analysis_path = Path(mip_dna_path, "cases", case.internal_id, "analysis")
    expect_to_add_pending_analysis_to_trailblazer(
        trailblazer_server=httpserver,
        case=case,
        ticket_id=ticket_id,
        out_dir=analysis_path,
        config_path=Path(analysis_path, "slurm_job_ids.yaml"),
        workflow=Workflow.MIP_DNA,
        analysis_type=AnalysisType.WGS,
    )

    # GIVEN the analysis can be started as a sub process
    analysis_subprocess_mock = mocker.patch.object(submitter, "subprocess")

    # WHEN running mip-dna start-available
    result: Result = cli_runner.invoke(
        base,
        [
            "--config",
            config_path.as_posix(),
            "workflow",
            "mip-dna",
            "start-available",
        ],
        catch_exceptions=False,
    )

    # THEN a scout command is called to export panel beds
    subprocess_mock.run.assert_any_call(
        [
            "/scout/binary",
            "--config",
            "/scout/config",
            "export",
            "panel",
            "--bed",
            ANY,
            ANY,
            ANY,
            "--build",
            "37",
        ],
        check=False,
        stdout=ANY,
        stderr=ANY,
    )

    # The order of the bed arguments is not deterministic, so we need to look at them as a set
    # this will be fixed so that the order is always the same in the new implementation of
    # starting MIP-DNA pipelines
    bed_args = subprocess_mock.run.call_args_list[0][0][0][6:9]
    assert set(bed_args) == {
        GenePanelMasterList.OMIM_AUTO,
        GenePanelMasterList.PANELAPP_GREEN,
        "panel_test",
    }

    # THEN a scout command is called to export managed variants
    subprocess_mock.run.assert_any_call(
        [
            "/scout/binary",
            "--config",
            "/scout/config",
            "export",
            "managed",
            "--build",
            "37",
        ],
        check=False,
        stdout=ANY,
        stderr=ANY,
    )

    # THEN a MIP-DNA analysis is started with the expected parameters
    expected_command = (
        f"{mip_dna_path}/conda_bin run --name S_mip12.1 "
        f"{mip_dna_path}/bin analyse rd_dna --config {mip_dna_path}/config/mip12.1-dna-stage.yaml "
        f"{case.internal_id} --slurm_quality_of_service normal --email {email}"
    )

    analysis_subprocess_mock.run.assert_any_call(
        args=expected_command,
        check=False,
        shell=True,
        stdout=ANY,
        stderr=ANY,
    )

    # THEN a successful exit code is returned
    assert result.exit_code == 0

    # THEN an analysis has been created for the case
    assert len(case.analyses) == 1

    # THEN the case action is set to running
    status_db.session.refresh(case)
    assert case.action == CaseActions.RUNNING

    # THEN the pedigree file has been created with the correct contents
    case_dir = Path(test_root_dir, "mip-dna", "cases", case.internal_id)

    expected_pedigree_content: str = f"""---
case: {case.internal_id}
default_gene_panels:
- panel_test
samples:
- analysis_type: wgs
  capture_kit: twistexomecomprehensive_10.2_hg19_design.bed
  expected_coverage: 30
  father: '0'
  mother: '0'
  phenotype: unaffected
  sample_display_name: sample_test
  sample_id: {sample.internal_id}
  sex: female
"""
    expect_file_contents(
        file_path=Path(case_dir, "pedigree.yaml"), expected_file_contents=expected_pedigree_content
    )

    # THEN the managed_variants file has been created with the correct contents
    expect_file_contents(
        file_path=Path(case_dir, "managed_variants.vcf"),
        expected_file_contents=scout_export_manged_variants_stdout.decode(),
    )

    # THEN the gene_panels file has been created with the correct contents
    expect_file_contents(
        file_path=Path(case_dir, "gene_panels.bed"),
        expected_file_contents=scout_export_panel_stdout.decode().removesuffix("\n"),
    )


def _create_qc_file(test_root_dir: Path, case: Case) -> Path:
    filepath = Path(
        f"{test_root_dir}/mip-dna/cases/{case.internal_id}/analysis/{case.internal_id}_qc_sample_info.yaml"
    )
    copy_integration_test_file(
        from_path=Path("tests/fixtures/apps/mip/dna/store/case_qc_sample_info.yaml"),
        to_path=filepath,
    )

    return filepath
