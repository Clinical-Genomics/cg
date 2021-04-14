from cg.cli.add import add
from cg.models.cg_config import CGConfig
from cg.store import Store
from click.testing import CliRunner


def test_add_customer(cli_runner: CliRunner, base_context: CGConfig):
    # GIVEN database with some customers
    status_db: Store = base_context.status_db
    nr_customers: int = status_db.Customer.query.count()

    # WHEN adding a customer
    cli_runner.invoke(
        add,
        [
            "customer",
            "internal_id",
            "testcust",
            "--invoice-address",
            "Test adress",
            "--invoice-reference",
            "ABCDEF",
        ],
        obj=base_context,
    )

    # THEN it should be stored in the database
    assert status_db.Customer.query.count() == nr_customers + 1


def test_add_user(cli_runner: CliRunner, base_context: CGConfig):
    # GIVEN a database with a customer in it that we can connect the user to
    disk_store: Store = base_context.status_db
    customer_id = "custtest"
    customer_group = disk_store.add_customer_group("dummy_group", "dummy group")
    customer = disk_store.add_customer(
        internal_id=customer_id,
        name="Test Customer",
        scout_access=False,
        customer_group=customer_group,
        invoice_address="Street nr, 12345 Uppsala",
        invoice_reference="ABCDEF",
    )
    disk_store.add_commit(customer)
    # GIVEN that there is a certain number of users
    nr_users = disk_store.User.query.count()

    # WHEN adding a new user
    name, email = "Paul T. Anderson", "paul.anderson@magnolia.com"
    result = cli_runner.invoke(add, ["user", "-c", customer_id, email, name], obj=base_context)

    # THEN it should be stored in the database
    assert result.exit_code == 0
    assert disk_store.User.query.count() == nr_users + 1
