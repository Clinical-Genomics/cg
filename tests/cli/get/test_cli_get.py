from cg.cli.get import get
from cg.models.cg_config import CGConfig
from cg.store import Store, models
from click.testing import CliRunner
from tests.store_helpers import StoreHelpers


def test_get_family_by_name(cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers):
    # GIVEN A database with a customer in it
    status_db: Store = base_context.status_db
    customer: models.Customer = helpers.ensure_customer(store=status_db)
    customer_id = customer.internal_id

    # WHEN trying to get a non-existing case by name
    result = cli_runner.invoke(
        get,
        [
            "family",
            "-c",
            customer_id,
            "-n",
            "dummy-case-name",
        ],
        obj=base_context,
    )

    # THEN it should not crash
    assert result.exit_code == 0
