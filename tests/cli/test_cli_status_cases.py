"""This script tests the cli methods to add families to status-db"""

from cg.cli.status import cases
from cg.store import Store
from click.testing import CliRunner
from cg.models.cg_config import CGConfig
from tests.store_helpers import StoreHelpers


def test_lists_sample_in_unreceived_samples(
    cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers
):
    """Test to that cases displays case in database"""

    # GIVEN a database with a case
    base_store: Store = base_context.status_db
    case = helpers.add_case(base_store)
    sample1 = helpers.add_sample(base_store, "sample1")
    helpers.add_relationship(base_store, case=case, sample=sample1)

    # WHEN listing cases
    result = cli_runner.invoke(cases, ["-o", "count"], obj=base_context)

    # THEN the case should be listed
    assert result.exit_code == 0
    assert case.internal_id in result.output
    assert "0/1" in result.output


def test_lists_samples_in_unreceived_samples(
    cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers
):
    """Test to that cases displays case in database"""

    # GIVEN a database with a case
    base_store: Store = base_context.status_db
    case = helpers.add_case(base_store)
    sample1 = helpers.add_sample(base_store, "sample1")
    sample2 = helpers.add_sample(base_store, "sample2")
    helpers.add_relationship(base_store, case=case, sample=sample1)
    helpers.add_relationship(base_store, case=case, sample=sample2)

    # WHEN listing cases
    result = cli_runner.invoke(cases, ["-o", "count"], obj=base_context)

    # THEN the case should be listed
    assert result.exit_code == 0
    assert case.internal_id in result.output
    assert "0/2" in result.output


def test_lists_family(cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers):
    """Test to that cases displays case in database"""

    # GIVEN a database with a case
    base_store: Store = base_context.status_db
    case = helpers.add_case(base_store)

    # WHEN listing cases
    result = cli_runner.invoke(cases, obj=base_context)

    # THEN the case should be listed
    assert result.exit_code == 0
    assert case.internal_id in result.output
