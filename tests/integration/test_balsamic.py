from datetime import datetime
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import ANY, Mock, create_autospec

import pytest
from click.testing import CliRunner, Result
from pytest_mock import MockerFixture

from cg.cli.base import base
from cg.constants.constants import Workflow
from cg.constants.process import EXIT_SUCCESS
from cg.constants.tb import AnalysisType
from cg.store.models import Case, Order, Sample
from cg.store.store import Store
from cg.utils import commands
from tests.store_helpers import StoreHelpers


@pytest.mark.integration
def test_start_config_case(
    helpers: StoreHelpers,
    cg_config_file: Path,
    mocker: MockerFixture,
    status_db: Store,
):
    """."""
    cli_runner = CliRunner()

    # GIVEN a config file with valid database URIs and directories

    test_root_dir = cg_config_file.parent

    # GIVEN a case with existing qc files
    ticket_id = 12345
    case: Case = helpers.add_case(
        store=status_db, data_analysis=Workflow.MIP_DNA, ticket=str(ticket_id)
    )

    # GIVEN an order associated with the case
    order: Order = helpers.add_order(
        store=status_db, ticket_id=ticket_id, customer_id=case.customer_id
    )
    status_db.link_case_to_order(order_id=order.id, case_id=case.id)

    # GIVEN a sample associated with the case
    sample: Sample = helpers.add_sample(
        store=status_db, last_sequenced_at=datetime.now(), application_type=AnalysisType.WGS
    )
    helpers.relate_samples(base_store=status_db, case=case, samples=[sample])

    # GIVEN that a sub process can be started and run successfully
    subprocess_mock = mocker.patch.object(commands, "subprocess")
    subprocess_mock.run = Mock(
        return_value=create_autospec(
            CompletedProcess, returncode=EXIT_SUCCESS, stdout=b"", stderr=b""
        )
    )

    # WHEN running balsamic config-case
    result: Result = cli_runner.invoke(
        base,
        [
            "--config",
            cg_config_file.as_posix(),
            "workflow",
            "balsamic",
            "config-case",
            case.internal_id,
        ],
    )

    assert result.exception is None
    subprocess_mock.run.assert_called_once_with(
        f"{test_root_dir}/balsamic_conda_binary run --name conda_env_balsamic "
        f"{test_root_dir}/balsamic_binary_path config case "
        f"--analysis-dir {test_root_dir}/balsamic_root_path "
        f"--analysis-workflow balsamic --balsamic-cache {test_root_dir}/balsamic_cache "
        f"--cadd-annotations {test_root_dir}/balsamic_cadd_path --case-id {case.internal_id} "
        f"--fastq-path {test_root_dir}/balsamic_root_path/{case.internal_id}/fastq "
        f"--gender female --genome-interval {test_root_dir}/balsamic_genome_interval_path "
        f"--genome-version hg19 "
        f"--gens-coverage-pon {test_root_dir}/balsamic_gens_coverage_female_path "
        f"--gnomad-min-af5 {test_root_dir}/balsamic_gnomad_af5_path "
        f"--sentieon-install-dir {test_root_dir}/balsamic_sention_licence_path "
        f"--sentieon-license localhost --tumor-sample-name {sample.internal_id}",
        check=False,
        shell=True,
        stderr=ANY,
        stdout=ANY,
    )
