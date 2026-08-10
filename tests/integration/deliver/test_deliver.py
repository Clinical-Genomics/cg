from datetime import datetime
from pathlib import Path

import pytest
from click.testing import CliRunner, Result
from pytest_httpserver import HTTPServer

from cg.cli.base import base
from cg.constants.constants import Workflow
from cg.store.models import Case, Order, Sample
from cg.store.store import Store
from tests.integration.utils import (
    IntegrationTestPaths,
    expect_to_get_all_analyses_to_deliver_from_trailblazer,
    expect_to_set_analyses_as_delivered,
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

    # GIVEN a store

    # GIVEN two cases in the store
    case_1: Case = helpers.add_case(store=status_db, internal_id="case1", name="Case 1")
    case_2: Case = helpers.add_case(store=status_db, internal_id="case2", name="Case 2")

    # GIVEN that each case has a linked sample
    sample_1: Sample = helpers.add_sample(store=status_db, name="sample1")
    helpers.relate_samples(base_store=status_db, case=case_1, samples=[sample_1])
    sample_2: Sample = helpers.add_sample(store=status_db, name="sample2")
    helpers.relate_samples(base_store=status_db, case=case_2, samples=[sample_2])

    # GIVEN that there is an undelivered analysis per case
    analysis_1 = helpers.add_analysis(
        store=status_db, case=case_1, trailblazer_id=101, uploaded_at=datetime.now()
    )
    analysis_2 = helpers.add_analysis(
        store=status_db, case=case_2, trailblazer_id=102, uploaded_at=datetime.now()
    )

    # GIVEN that each analysis comes from an order currently open
    order_1: Order = helpers.add_order(
        store=status_db, ticket_id=12345, customer_id=case_1.customer.id
    )
    analysis_1.order = order_1
    order_2: Order = helpers.add_order(
        store=status_db, ticket_id=67890, customer_id=case_2.customer.id
    )
    analysis_2.order = order_2

    status_db.commit_to_store()

    # GIVEN that Trailblazer has analyses ready to deliver for the correponsing analyses in StatusDB
    expect_to_get_all_analyses_to_deliver_from_trailblazer(
        trailblazer_server=httpserver,
        exclude_workflows=[
            Workflow.MICROSALT,
            Workflow.TAXPROFILER,
            Workflow.DEMULTIPLEX,
            Workflow.RSYNC,
        ],
    )

    # GIVEN that Trailblazer sets the statuses of analyses to delivered
    # Each case belongs to its own order, so DeliverService calls Trailblazer once per order
    expect_to_set_analyses_as_delivered(trailblazer_server=httpserver, analysis_ids=[101])
    expect_to_set_analyses_as_delivered(trailblazer_server=httpserver, analysis_ids=[102])

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

    # THEN samples are delivered
    assert sample_1.delivered_at is not None
    assert sample_2.delivered_at is not None

    # THEN the orders are closed
    assert analysis_1.order.is_open is False
    assert analysis_2.order.is_open is False
