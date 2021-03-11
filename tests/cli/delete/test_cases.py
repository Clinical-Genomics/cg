"""Test methods for cg/cli/delete/cases"""
import logging

import pytest

from cg.cli.delete.cases import cases
from cg.store import Store

SUCCESS = 0


@pytest.mark.parametrize("identifier_key", ["ticket_number", "order"])
def test_set_cases_by_sample_identifiers(
    cli_runner, base_context, base_store: Store, identifier_key, helpers, caplog
):
    # GIVEN a database with a case with a sample
    sample_obj = helpers.add_sample(base_store)
    sample_obj.ticket_number = 123456
    sample_obj.order = "An order"
    case = helpers.add_case(base_store)
    helpers.add_relationship(base_store, sample=sample_obj, case=case)
    identifier_value = getattr(sample_obj, identifier_key)

    caplog.set_level(logging.INFO)

    # WHEN calling delete cases with valid sample identifiers
    cli_runner.invoke(
        cases,
        ["--sample-identifier", identifier_key, identifier_value],
        obj=base_context,
    )

    # THEN it should name the case to be changed
    assert case.internal_id in caplog.text
    assert case.name in caplog.text


def test_delete_cases_with_dry_run(cli_runner, base_context, base_store: Store, helpers, caplog):
    """Test that the delete cases will not delete the cases in dry-run mode """
    # GIVEN a database with a case
    case_obj = helpers.add_case(base_store)
    case_id = case_obj.internal_id
    sample = helpers.add_sample(base_store)
    helpers.add_relationship(store=base_store, case=case_obj, sample=sample)

    # WHEN deleting a case
    caplog.set_level(logging.DEBUG)
    cli_runner.invoke(
        cases,
        ["--sample-identifier", "name", sample.name, "--dry-run"],
        obj=base_context,
    )

    # THEN then it should not have been deleted
    assert "Cases (that will NOT be deleted due to --dry-run):" in caplog.text
    assert case_id in caplog.text
