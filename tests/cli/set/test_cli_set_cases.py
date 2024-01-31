"""This script tests the cli methods to set values of several cases in status-db."""

import logging

import pytest
from _pytest.logging import LogCaptureFixture
from click.testing import CliRunner

from cg.cli.set.cases import set_cases
from cg.models.cg_config import CGConfig
from cg.store.models import Case, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.mark.parametrize("identifier_key", ["original_ticket", "order"])
def test_set_cases_by_sample_identifiers(
    cli_runner: CliRunner,
    base_context: CGConfig,
    identifier_key: str,
    helpers: StoreHelpers,
    caplog: LogCaptureFixture,
    ticket_id: str,
):
    # GIVEN a database with a case with a sample
    base_store: Store = base_context.status_db
    new_sample: Sample = helpers.add_sample(base_store)
    new_sample.original_ticket: str = ticket_id
    new_sample.order: str = "An order"
    case: Case = helpers.add_case(base_store)
    helpers.add_relationship(base_store, sample=new_sample, case=case)
    identifier_value = getattr(new_sample, identifier_key)

    caplog.set_level(logging.INFO)

    # WHEN calling set families with valid sample identifiers
    cli_runner.invoke(
        set_cases,
        ["--sample-identifier", identifier_key, identifier_value],
        obj=base_context,
    )

    # THEN it should name the case to be changed
    assert case.internal_id in caplog.text
    assert case.name in caplog.text
