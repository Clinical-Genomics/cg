"""Test add customer CLI."""

from cg.cli.add import add
from cg.constants import EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from cg.store import Store
from click.testing import CliRunner

from cg.store.models import Customer

NEW_TEST_CUST_NAME: str = "new_test_cust"
NEW_TEST_CUST_INTERNAL_ID: str = "new_test_cust_internal_id"


def test_add_customer(
    base_context: CGConfig, cli_runner: CliRunner, invoice_address: str, invoice_reference: str
):
    """Test add customer command."""
    # GIVEN database with some customers
    status_db: Store = base_context.status_db
    nr_customers: int = status_db._get_query(table=Customer).count()

    # WHEN adding a customer
    result = cli_runner.invoke(
        add,
        [
            "customer",
            "--invoice-address",
            invoice_address,
            "--invoice-reference",
            invoice_reference,
            NEW_TEST_CUST_INTERNAL_ID,
            NEW_TEST_CUST_NAME,
        ],
        obj=base_context,
    )

    # THEN exit successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN it should be stored in the database
    assert status_db._get_query(table=Customer).count() == nr_customers + 1


def test_add_customer_with_collaboration(
    base_context: CGConfig,
    cli_runner: CliRunner,
    collaboration_id: str,
    invoice_address: str,
    invoice_reference: str,
):
    """Test add customer with collaborator."""
    # GIVEN database with customers
    status_db: Store = base_context.status_db
    nr_customers: int = status_db._get_query(table=Customer).count()

    # WHEN adding a customer
    result = cli_runner.invoke(
        add,
        [
            "customer",
            "--invoice-address",
            invoice_address,
            "--invoice-reference",
            invoice_reference,
            "--collaboration-internal-ids",
            collaboration_id,
            NEW_TEST_CUST_INTERNAL_ID,
            NEW_TEST_CUST_NAME,
        ],
        obj=base_context,
    )

    new_customer: Customer = status_db.get_customer_by_internal_id(
        customer_internal_id=NEW_TEST_CUST_INTERNAL_ID
    )

    # THEN exit successfully
    assert result.exit_code == EXIT_SUCCESS

    # THEN it should be stored in the database
    assert status_db._get_query(table=Customer).count() == nr_customers + 1

    # THEN a collaborator should have been added
    assert new_customer.collaborations[0].internal_id == collaboration_id
