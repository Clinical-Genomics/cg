"""This script tests the cli methods to add families to status-db"""

from cg.cli.status import cases
from cg.store import Store


def test_lists_sample_in_unreceived_samples(cli_runner, base_context, base_store: Store, helpers):
    """Test to that cases displays family in database"""

    # GIVEN a database with a family
    family = helpers.add_family(base_store)
    sample1 = helpers.add_sample(base_store, "sample1")
    helpers.add_relationship(base_store, family=family, sample=sample1)

    # WHEN listing cases
    result = cli_runner.invoke(cases, ["-o", "count"], obj=base_context)

    # THEN the family should be listed
    assert result.exit_code == 0
    assert family.internal_id in result.output
    assert "0/1" in result.output


def test_lists_samples_in_unreceived_samples(cli_runner, base_context, base_store: Store, helpers):
    """Test to that cases displays family in database"""

    # GIVEN a database with a family
    family = helpers.add_family(base_store)
    sample1 = helpers.add_sample(base_store, "sample1")
    sample2 = helpers.add_sample(base_store, "sample2")
    helpers.add_relationship(base_store, family=family, sample=sample1)
    helpers.add_relationship(base_store, family=family, sample=sample2)

    # WHEN listing cases
    result = cli_runner.invoke(cases, ["-o", "count"], obj=base_context)

    # THEN the family should be listed
    assert result.exit_code == 0
    assert family.internal_id in result.output
    assert "0/2" in result.output


def test_lists_family(cli_runner, base_context, base_store: Store, helpers):
    """Test to that cases displays family in database"""

    # GIVEN a database with a family
    family = helpers.add_family(base_store)

    # WHEN listing cases
    result = cli_runner.invoke(cases, obj=base_context)

    # THEN the family should be listed
    assert result.exit_code == 0
    assert family.internal_id in result.output
