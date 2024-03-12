from click.testing import CliRunner

from cg.cli.add import add
from cg.constants import EXIT_SUCCESS, Priority
from cg.constants.subject import Sex
from cg.models.cg_config import CGConfig
from cg.store.models import Customer, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_add_sample_missing_customer(cli_runner: CliRunner, base_context: CGConfig):
    """Test adding a sample when customer id supplied does not match a customer in the database."""
    # GIVEN an empty database
    disk_store: Store = base_context.status_db

    # WHEN adding a sample
    application = "dummy_application"
    customer_id = "dummy_customer"
    name = "dummy_name"
    original_ticket = "dummy ticket"
    result = cli_runner.invoke(
        add,
        [
            "sample",
            "--sex",
            Sex.MALE,
            "--application-tag",
            application,
            "--original-ticket",
            original_ticket,
            customer_id,
            name,
        ],
        obj=base_context,
    )

    # THEN it should complain about missing customer instead of adding a sample
    assert result.exit_code == 1
    assert disk_store._get_query(table=Sample).count() == 0


def test_add_sample_bad_application(
    cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers
):
    """Test adding a sample when application tag supplied does not match an application tag in the database."""
    # GIVEN a database with a customer
    disk_store: Store = base_context.status_db

    # WHEN adding a sample
    application = "dummy_application"
    customer: Customer = helpers.ensure_customer(store=disk_store)
    name = "dummy_name"
    original_ticket = "dummy ticket"
    result = cli_runner.invoke(
        add,
        [
            "sample",
            "--sex",
            Sex.MALE,
            "--application-tag",
            application,
            "--original-ticket",
            original_ticket,
            customer.internal_id,
            name,
        ],
        obj=base_context,
    )

    # THEN it should complain about missing application instead of adding a sample
    assert result.exit_code == 1
    assert disk_store._get_query(table=Sample).count() == 0


def test_add_sample_required(cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers):
    """Test adding a sample."""
    # GIVEN a database with a customer and an application
    disk_store: Store = base_context.status_db
    application_tag = "dummy_tag"
    helpers.ensure_application(store=disk_store, tag=application_tag)
    helpers.ensure_application_version(store=disk_store, application_tag=application_tag)
    customer: Customer = helpers.ensure_customer(store=disk_store)
    name = "sample_name"
    original_ticket = "dummy ticket"
    # WHEN adding a sample
    result = cli_runner.invoke(
        add,
        [
            "sample",
            "--sex",
            Sex.MALE,
            "--application-tag",
            application_tag,
            "--original-ticket",
            original_ticket,
            customer.internal_id,
            name,
        ],
        obj=base_context,
    )

    # THEN it should be added
    assert result.exit_code == EXIT_SUCCESS
    sample_query = disk_store._get_query(table=Sample)
    assert sample_query.count() == 1
    assert sample_query.first().name == name
    assert sample_query.first().sex == Sex.MALE


def test_add_sample_lims_id(cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers):
    """Test adding a sample using a LIMS id."""
    # GIVEN a database with a customer and an application
    disk_store: Store = base_context.status_db
    application_tag = "dummy_tag"
    helpers.ensure_application(store=disk_store, tag=application_tag)
    helpers.ensure_application_version(store=disk_store, application_tag=application_tag)
    # WHEN adding a sample
    customer: Customer = helpers.ensure_customer(store=disk_store)
    name = "sample_name"
    lims_id = "sample_lims_id"
    original_ticket = "dummy ticket"
    result = cli_runner.invoke(
        add,
        [
            "sample",
            "--sex",
            Sex.MALE,
            "--application-tag",
            application_tag,
            "--original-ticket",
            original_ticket,
            "--lims",
            lims_id,
            customer.internal_id,
            name,
        ],
        obj=base_context,
    )

    # THEN it should be added
    assert result.exit_code == EXIT_SUCCESS
    sample_query = disk_store._get_query(table=Sample)
    assert sample_query.count() == 1
    assert sample_query.first().internal_id == lims_id


def test_add_sample_order(
    cli_runner: CliRunner,
    base_context: CGConfig,
    disk_store: Store,
    helpers: StoreHelpers,
    application_tag: str,
):
    """Test adding a sample using an external sample id."""
    # GIVEN a database with a customer and an application
    helpers.ensure_application(store=disk_store, tag=application_tag)
    helpers.ensure_application_version(store=disk_store, application_tag=application_tag)
    customer: Customer = helpers.ensure_customer(store=disk_store)
    name = "sample_name"
    order = "sample_order"
    original_ticket = "dummy ticket"
    # WHEN adding a sample
    result = cli_runner.invoke(
        add,
        [
            "sample",
            "--sex",
            Sex.MALE,
            "--application-tag",
            application_tag,
            "--original-ticket",
            original_ticket,
            "--order",
            order,
            customer.internal_id,
            name,
        ],
        obj=base_context,
    )

    # THEN it should be added
    assert result.exit_code == EXIT_SUCCESS
    sample_query = disk_store._get_query(table=Sample)
    assert sample_query.count() == 1
    assert sample_query.first().order == order


def test_add_sample_when_down_sampled(
    cli_runner,
    base_context: CGConfig,
    disk_store: Store,
    application_tag: str,
    helpers: StoreHelpers,
):
    """Test adding a sample when down sampled"""
    # GIVEN a database with a customer and an application
    helpers.ensure_application(store=disk_store, tag=application_tag)
    helpers.ensure_application_version(store=disk_store, application_tag=application_tag)
    customer: Customer = helpers.ensure_customer(store=disk_store)
    name = "sample_name"
    down_sampled_to = "123"
    original_ticket = "dummy ticket"
    # WHEN adding a sample
    result = cli_runner.invoke(
        add,
        [
            "sample",
            "--sex",
            Sex.MALE,
            "--application-tag",
            application_tag,
            "--original-ticket",
            original_ticket,
            "--down-sampled",
            down_sampled_to,
            customer.internal_id,
            name,
        ],
        obj=base_context,
    )

    # THEN it should be added
    assert result.exit_code == EXIT_SUCCESS
    sample_query = disk_store._get_query(table=Sample)
    assert sample_query.count() == 1
    assert str(sample_query.first().downsampled_to) == down_sampled_to


def test_add_sample_priority(
    cli_runner: CliRunner,
    base_context: CGConfig,
    disk_store: Store,
    application_tag: str,
    helpers: StoreHelpers,
):
    """Test adding a sample with priority."""
    # GIVEN a database with a customer and an application
    helpers.ensure_application(store=disk_store, tag=application_tag)
    helpers.ensure_application_version(store=disk_store, application_tag=application_tag)
    customer: Customer = helpers.ensure_customer(store=disk_store)
    name = "sample_name"
    original_ticket = "dummy ticket"
    # WHEN adding a sample
    result = cli_runner.invoke(
        add,
        [
            "sample",
            "--sex",
            Sex.MALE,
            "--application-tag",
            application_tag,
            "--original-ticket",
            original_ticket,
            "--priority",
            Priority.priority.name,
            customer.internal_id,
            name,
        ],
        obj=base_context,
    )

    # THEN it should be added
    assert result.exit_code == EXIT_SUCCESS
    sample_query = disk_store._get_query(table=Sample)
    assert sample_query.count() == 1
    assert sample_query.first().priority_human == Priority.priority.name
