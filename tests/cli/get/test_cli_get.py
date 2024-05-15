from click.testing import CliRunner

from cg.cli.get import get
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from cg.store.models import Customer
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_get_case_by_name(cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers):
    # GIVEN A database with a customer in it
    status_db: Store = base_context.status_db
    customer: Customer = helpers.ensure_customer(store=status_db)

    # WHEN trying to get a non-existing case by name
    result = cli_runner.invoke(
        get,
        [
            "case",
            "-c",
            customer.internal_id,
            "-n",
            "dummy-case-name",
        ],
        obj=base_context,
    )

    # THEN it should not crash
    assert result.exit_code == EXIT_SUCCESS
