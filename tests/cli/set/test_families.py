"""Test methods for cg/cli/set/families"""
import logging

import pytest
from cg.cli.set.families import families
from cg.models.cg_config import CGConfig
from cg.store import Store, models

SUCCESS = 0


@pytest.mark.parametrize("identifier_key", ["ticket_number", "order"])
def test_set_families_by_sample_identifiers(
    cli_runner, base_context: CGConfig, identifier_key, helpers, caplog
):
    # GIVEN a database with a case with a sample
    base_store: Store = base_context.status_db
    sample_obj: models.Sample = helpers.add_sample(base_store)
    sample_obj.ticket_number = 123456
    sample_obj.order = "An order"
    case: models.Family = helpers.add_case(base_store)
    helpers.add_relationship(base_store, sample=sample_obj, case=case)
    identifier_value = getattr(sample_obj, identifier_key)

    caplog.set_level(logging.INFO)

    # WHEN calling set families with valid sample identifiers
    cli_runner.invoke(
        families,
        ["--sample-identifier", identifier_key, identifier_value],
        obj=base_context,
    )

    # THEN it should name the case to be changed
    assert case.internal_id in caplog.text
    assert case.name in caplog.text
