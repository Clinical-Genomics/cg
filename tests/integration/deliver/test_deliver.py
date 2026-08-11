from datetime import datetime
from pathlib import Path

import pytest
from click.testing import CliRunner, Result
from pytest_httpserver import HTTPServer

import tests.integration.trailblazer_utils as tb_utils
from cg.cli.base import base
from cg.constants import Workflow
from cg.store.models import Case, Order, Sample
from cg.store.store import Store
from tests.integration.freshdesk_utils import (
    expect_freshdesk_get_ticket,
    expect_freshdesk_reply_to_ticket,
    expect_freshdesk_update_ticket,
)
from tests.integration.utils import IntegrationTestPaths
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

    # GIVEN that each case is linked to its order
    status_db.link_case_to_order(order_id=order_1.id, case_id=case_1.id)
    status_db.link_case_to_order(order_id=order_2.id, case_id=case_2.id)

    # GIVEN that each order has a pool that has not been delivered
    # (not realistic that a non-NIPT order has a pool but for testing purposes)
    pool_1 = helpers.ensure_pool(store=status_db, name="pool1", delivered_at=None, ticket="12345")
    pool_1.samples.append(sample_1)
    pool_2 = helpers.ensure_pool(store=status_db, name="pool2", delivered_at=None, ticket="67890")
    pool_2.samples.append(sample_2)

    status_db.commit_to_store()

    # GIVEN that Trailblazer has analyses ready to deliver for the analyses in StatusDB
    tb_utils.expect_to_get_all_analyses_to_deliver(
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
    tb_utils.expect_to_set_analyses_as_delivered(trailblazer_server=httpserver, analysis_ids=[101])
    tb_utils.expect_to_set_analyses_as_delivered(trailblazer_server=httpserver, analysis_ids=[102])

    # GIVEN that Trailblazer confirms each order's analyses are fully delivered, so the
    # orders can be closed
    tb_utils.expect_to_get_delivered_analyses_for_order(
        trailblazer_server=httpserver, order_id=order_1.id, case_ids=[case_1.internal_id]
    )
    tb_utils.expect_to_get_delivered_analyses_for_order(
        trailblazer_server=httpserver, order_id=order_2.id, case_ids=[case_2.internal_id]
    )

    # GIVEN that Freshdesk sends delivery messages correctly
    expect_freshdesk_get_ticket(freshdesk_server=httpserver, ticket_id=12345)
    expect_freshdesk_reply_to_ticket(freshdesk_server=httpserver, ticket_id=12345)
    expect_freshdesk_get_ticket(freshdesk_server=httpserver, ticket_id=67890)
    expect_freshdesk_reply_to_ticket(freshdesk_server=httpserver, ticket_id=67890)

    # GIVEN that Freshdesk can close the tickets correctly
    expect_freshdesk_update_ticket(freshdesk_server=httpserver, ticket_id=12345)
    expect_freshdesk_update_ticket(freshdesk_server=httpserver, ticket_id=67890)

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
    status_db.session.refresh(sample_1)
    status_db.session.refresh(sample_2)
    assert sample_1.delivered_at is not None
    assert sample_2.delivered_at is not None

    # THEN the orders are closed
    status_db.session.refresh(order_1)
    status_db.session.refresh(order_2)
    assert order_1.is_open is False
    assert order_2.is_open is False

    # THEN the pools are delivered
    status_db.session.refresh(pool_1)
    status_db.session.refresh(pool_2)
    assert pool_1.delivered_at is not None
    assert pool_2.delivered_at is not None
