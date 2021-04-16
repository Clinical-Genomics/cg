from cg.cli.add import add
from cg.models.cg_config import CGConfig
from cg.store import Store, models
from click.testing import CliRunner
from tests.store_helpers import StoreHelpers


def test_add_sample_bad_customer(cli_runner: CliRunner, base_context: CGConfig):
    # GIVEN an empty database
    disk_store: Store = base_context.status_db

    # WHEN adding a sample
    sex = "male"
    application = "dummy_application"
    customer_id = "dummy_customer"
    name = "dummy_name"
    result = cli_runner.invoke(
        add,
        [
            "sample",
            "--sex",
            sex,
            "--application",
            application,
            customer_id,
            name,
        ],
        obj=base_context,
    )

    # THEN then it should complain about missing customer instead of adding a sample
    assert result.exit_code == 1
    assert disk_store.Sample.query.count() == 0


def test_add_sample_bad_application(
    cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers
):
    # GIVEN a database with a customer
    disk_store: Store = base_context.status_db

    # WHEN adding a sample
    sex = "male"
    application = "dummy_application"
    customer: models.Customer = helpers.ensure_customer(store=disk_store)
    customer_id = customer.internal_id
    name = "dummy_name"
    result = cli_runner.invoke(
        add,
        [
            "sample",
            "--sex",
            sex,
            "--application",
            application,
            customer_id,
            name,
        ],
        obj=base_context,
    )

    # THEN then it should complain about missing application instead of adding a sample
    assert result.exit_code == 1
    assert disk_store.Sample.query.count() == 0


def test_add_sample_required(cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers):
    # GIVEN a database with a customer and an application
    disk_store: Store = base_context.status_db
    sex = "male"
    application_tag = "dummy_tag"
    helpers.ensure_application(store=disk_store, tag=application_tag)
    helpers.ensure_application_version(store=disk_store, application_tag=application_tag)
    customer: models.Customer = helpers.ensure_customer(store=disk_store)
    customer_id = customer.internal_id
    name = "sample_name"

    # WHEN adding a sample
    result = cli_runner.invoke(
        add,
        [
            "sample",
            "--sex",
            sex,
            "--application",
            application_tag,
            customer_id,
            name,
        ],
        obj=base_context,
    )

    # THEN then it should be added
    assert result.exit_code == 0
    assert disk_store.Sample.query.count() == 1
    assert disk_store.Sample.query.first().name == name
    assert disk_store.Sample.query.first().sex == sex


def test_add_sample_lims_id(cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers):
    # GIVEN a database with a customer and an application
    disk_store: Store = base_context.status_db
    application_tag = "dummy_tag"
    helpers.ensure_application(store=disk_store, tag=application_tag)
    helpers.ensure_application_version(store=disk_store, application_tag=application_tag)
    # WHEN adding a sample
    sex = "male"
    customer: models.Customer = helpers.ensure_customer(store=disk_store)
    customer_id = customer.internal_id
    name = "sample_name"
    lims_id = "sample_lims_id"

    result = cli_runner.invoke(
        add,
        [
            "sample",
            "--sex",
            sex,
            "--application",
            application_tag,
            "--lims",
            lims_id,
            customer_id,
            name,
        ],
        obj=base_context,
    )

    # THEN then it should be added
    assert result.exit_code == 0
    assert disk_store.Sample.query.count() == 1
    assert disk_store.Sample.query.first().internal_id == lims_id


def test_add_sample_order(
    cli_runner: CliRunner,
    base_context: CGConfig,
    disk_store: Store,
    helpers: StoreHelpers,
    application_tag: str,
):
    # GIVEN a database with a customer and an application
    helpers.ensure_application(store=disk_store, tag=application_tag)
    helpers.ensure_application_version(store=disk_store, application_tag=application_tag)
    sex = "male"
    customer: models.Customer = helpers.ensure_customer(store=disk_store)
    customer_id = customer.internal_id
    name = "sample_name"
    order = "sample_order"

    # WHEN adding a sample
    result = cli_runner.invoke(
        add,
        [
            "sample",
            "--sex",
            sex,
            "--application",
            application_tag,
            "--order",
            order,
            customer_id,
            name,
        ],
        obj=base_context,
    )

    # THEN then it should be added
    assert result.exit_code == 0
    assert disk_store.Sample.query.count() == 1
    assert disk_store.Sample.query.first().order == order


def test_add_sample_downsampled(
    cli_runner,
    base_context: CGConfig,
    disk_store: Store,
    application_tag: str,
    helpers: StoreHelpers,
):
    # GIVEN a database with a customer and an application
    helpers.ensure_application(store=disk_store, tag=application_tag)
    helpers.ensure_application_version(store=disk_store, application_tag=application_tag)
    customer: models.Customer = helpers.ensure_customer(store=disk_store)
    customer_id = customer.internal_id
    sex = "male"
    name = "sample_name"
    downsampled_to = "123"

    # WHEN adding a sample
    result = cli_runner.invoke(
        add,
        [
            "sample",
            "--sex",
            sex,
            "--application",
            application_tag,
            "--downsampled",
            downsampled_to,
            customer_id,
            name,
        ],
        obj=base_context,
    )

    # THEN then it should be added
    assert result.exit_code == 0
    assert disk_store.Sample.query.count() == 1
    assert str(disk_store.Sample.query.first().downsampled_to) == downsampled_to


def test_add_sample_priority(
    cli_runner: CliRunner,
    base_context: CGConfig,
    disk_store: Store,
    application_tag: str,
    helpers: StoreHelpers,
):
    # GIVEN a database with a customer and an application
    helpers.ensure_application(store=disk_store, tag=application_tag)
    helpers.ensure_application_version(store=disk_store, application_tag=application_tag)
    customer: models.Customer = helpers.ensure_customer(store=disk_store)
    customer_id = customer.internal_id
    sex = "male"
    name = "sample_name"
    priority = "priority"

    # WHEN adding a sample
    result = cli_runner.invoke(
        add,
        [
            "sample",
            "--sex",
            sex,
            "--application",
            application_tag,
            "--priority",
            priority,
            customer_id,
            name,
        ],
        obj=base_context,
    )

    # THEN then it should be added
    assert result.exit_code == 0
    assert disk_store.Sample.query.count() == 1
    assert disk_store.Sample.query.first().priority_human == priority
