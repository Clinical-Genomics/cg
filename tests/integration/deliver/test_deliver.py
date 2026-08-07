from datetime import datetime
from pathlib import Path

import pytest
from click.testing import CliRunner, Result
from pytest_httpserver import HTTPServer

from cg.cli.base import base
from cg.constants.constants import Workflow
from cg.store.models import Case
from cg.store.store import Store
from tests.integration.utils import (
    IntegrationTestPaths,
    expect_to_get_all_analyses_to_deliver_from_trailblazer,
)
from tests.store_helpers import StoreHelpers


@pytest.mark.xdist_group(name="integration")
@pytest.mark.integration
def test_deliver_all_available(
    httpserver: HTTPServer,
    helpers: StoreHelpers,
    status_db: Store,
    test_run_paths: IntegrationTestPaths,
):
    cli_runner = CliRunner()

    # GIVEN a config file with valid database URIs and directories
    config_path: Path = test_run_paths.cg_config_file

    # GIVEN that StatusDB has analyses to deliver
    case_1: Case = helpers.add_case(store=status_db, internal_id="case1", name="Case 1")
    analysis_1 = helpers.add_analysis(
        store=status_db, case=case_1, trailblazer_id=101, uploaded_at=datetime.now()
    )
    analysis_1.order = helpers.add_order(
        store=status_db, ticket_id=12345, customer_id=case_1.customer.id
    )
    case_2: Case = helpers.add_case(store=status_db, internal_id="case2", name="Case 2")
    analysis_2 = helpers.add_analysis(
        store=status_db, case=case_2, trailblazer_id=102, uploaded_at=datetime.now()
    )
    cust2 = case_2.customer
    analysis_2.order = helpers.add_order(
        store=status_db, ticket_id=67890, customer_id=case_2.customer.id
    )

    # GIVEN that Trailblazer has analyses ready for delivery
    expect_to_get_all_analyses_to_deliver_from_trailblazer(
        trailblazer_server=httpserver,
        exclude_workflows=[
            Workflow.MICROSALT,
            Workflow.TAXPROFILER,
            Workflow.DEMULTIPLEX,
            Workflow.RSYNC,
        ],
    )

    # WHEN running deliver all available
    result: Result = cli_runner.invoke(
        base,
        [
            "--config",
            config_path.as_posix(),
            "deliver",
            "all-available",
        ],
        catch_exceptions=False,
    )

    # THEN the delivery was successful
    assert result.exit_code == 0
