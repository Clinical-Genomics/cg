"""Test methods for cg cli set sample"""

import pytest
from click.testing import CliRunner

from cg.cli.set.base import sample
from cg.constants import EXIT_SUCCESS, Priority
from cg.constants.subject import Sex
from cg.models.cg_config import CGConfig
from cg.store.models import Sample
from cg.store.store import Store


def test_invalid_sample(cli_runner: CliRunner, base_context: CGConfig):
    # GIVEN an empty database

    # WHEN running set with a sample that does not exist
    sample_id = "dummy_sample_id"
    result = cli_runner.invoke(sample, [sample_id], obj=base_context)

    # THEN it should complain on invalid sample
    assert result.exit_code != EXIT_SUCCESS


def test_skip_lims(cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers):
    # GIVEN a database with a sample

    db_sample = helpers.add_sample(base_store, sex=Sex.FEMALE)
    key = "name"
    new_value = "new_value"

    # WHEN setting sample but skipping lims
    result = cli_runner.invoke(
        sample,
        [db_sample.internal_id, "-kv", "name", "dummy_value", "-y", "--skip-lims"],
        obj=base_context,
    )

    # THEN update sample should have no recorded update key and value
    assert result.exit_code == EXIT_SUCCESS
    assert base_context.lims_api.get_updated_sample_key() != key
    assert base_context.lims_api.get_updated_sample_value() != new_value


@pytest.mark.parametrize("key", ["name", "capture_kit"])
def test_set_sample(cli_runner: CliRunner, base_context: CGConfig, base_store: Store, key, helpers):
    # GIVEN a database with a sample

    db_sample = helpers.add_sample(base_store, sex=Sex.FEMALE)
    new_value = "new_value"
    assert getattr(db_sample, key) != new_value

    # WHEN setting key on sample to new_value
    result = cli_runner.invoke(
        sample,
        [db_sample.internal_id, "-kv", key, new_value, "-y"],
        obj=base_context,
    )

    # THEN it should have new_value as attribute key on the sample and in LIMS
    assert result.exit_code == EXIT_SUCCESS
    assert getattr(db_sample, key) == new_value
    assert base_context.lims_api.get_updated_sample_key() == key
    assert base_context.lims_api.get_updated_sample_value() == new_value


@pytest.mark.parametrize("new_value", ["false", "true", "True", "False"])
def test_set_boolean_sample(
    cli_runner: CliRunner, base_context: CGConfig, base_store: Store, new_value, helpers
):
    # GIVEN a database with a sample

    db_sample = helpers.add_sample(base_store, sex=Sex.FEMALE)
    value: bool = new_value.lower() == "true"

    # WHEN setting key on sample to new_value
    result = cli_runner.invoke(
        sample,
        [db_sample.internal_id, "-kv", "no_invoice", new_value, "-y", "--skip-lims"],
        obj=base_context,
    )

    # THEN it should have new_value as attribute key on the sample
    assert result.exit_code == EXIT_SUCCESS
    assert getattr(db_sample, "no_invoice") == value


def test_sex(cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers):
    # GIVEN a database with a sample

    db_sample = helpers.add_sample(base_store, sex=Sex.FEMALE)
    key = "sex"
    new_value = "male"
    assert getattr(db_sample, key) != new_value

    # WHEN setting key on sample to new_value
    result = cli_runner.invoke(
        sample, [db_sample.internal_id, "-kv", key, new_value, "-y"], obj=base_context
    )

    # THEN it should have new_value as attribute key on the sample and in LIMS
    assert result.exit_code == EXIT_SUCCESS
    assert getattr(db_sample, key) == new_value
    assert base_context.lims_api.get_updated_sample_key() == key
    assert base_context.lims_api.get_updated_sample_value() == new_value


def test_priority_text(cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers):
    # GIVEN a database with a sample
    db_sample = helpers.add_sample(base_store, sex=Sex.FEMALE)
    key = "priority"
    new_value = Priority.express.name
    assert db_sample.priority_human != new_value

    # WHEN setting key on sample to new_value
    result = cli_runner.invoke(
        sample, [db_sample.internal_id, "-kv", key, new_value, "-y"], obj=base_context
    )

    # THEN it should have new_value as attribute key on the sample and in LIMS
    assert result.exit_code == EXIT_SUCCESS
    assert db_sample.priority_human == new_value
    assert base_context.lims_api.get_updated_sample_key() == key
    assert base_context.lims_api.get_updated_sample_value() == db_sample.priority_human


def test_priority_number(cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers):
    # GIVEN a database with a sample
    db_sample = helpers.add_sample(base_store, sex=Sex.FEMALE)
    key = "priority"
    new_value = Priority.express
    assert db_sample.priority != new_value

    # WHEN setting key on sample to new_value
    result = cli_runner.invoke(
        sample,
        [db_sample.internal_id, "-kv", key, new_value.name, "-y"],
        obj=base_context,
    )

    # THEN it should have new_value as attribute key on the sample and in LIMS
    assert result.exit_code == EXIT_SUCCESS
    assert db_sample.priority == new_value
    assert base_context.lims_api.get_updated_sample_key() == key
    assert base_context.lims_api.get_updated_sample_value() == db_sample.priority_human


def test_sample_comment(cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers):
    # GIVEN a database with a sample without comment
    db_sample = helpers.add_sample(base_store, sex=Sex.FEMALE)
    key = "comment"

    # WHEN setting key on sample to new_value
    new_value = "test comment"
    result = cli_runner.invoke(
        sample, [db_sample.internal_id, "-kv", key, new_value, "-y"], obj=base_context
    )

    # THEN it should have new_value as attribute key on the sample and in LIMS
    assert result.exit_code == EXIT_SUCCESS
    assert getattr(db_sample, key).endswith(new_value)
    assert base_context.lims_api.get_updated_sample_key() == key
    assert base_context.lims_api.get_updated_sample_value() == new_value


def test_sample_comment_append(
    cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers
):
    # GIVEN a database with a sample with a comment
    old_value = "test comment"
    sample_obj = helpers.add_sample(
        base_store, sex=Sex.FEMALE, comment=f"2022-06-13 10:16-test.user: {old_value}"
    )
    key = "comment"

    # WHEN setting key again on sample this time to new_value
    new_value = "another test comment"
    result = cli_runner.invoke(
        sample, [sample_obj.internal_id, "-kv", key, new_value, "-y"], obj=base_context
    )

    # THEN it should have new_value above old_value as attribute key on the sample and in LIMS
    comments = getattr(sample_obj, key).split("\n")
    assert result.exit_code == EXIT_SUCCESS
    assert comments[0].endswith(new_value)
    assert comments[1].endswith(old_value)
    assert base_context.lims_api.get_updated_sample_key() == key
    assert base_context.lims_api.get_updated_sample_value() == new_value


def test_invalid_customer(
    cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers
):
    # GIVEN a database with a sample
    sample_id = helpers.add_sample(base_store).internal_id
    customer_id = "dummy_customer_id"
    sample_query = base_store._get_query(table=Sample)

    assert sample_query.first().customer.internal_id != customer_id

    # WHEN calling set sample with an invalid customer
    result = cli_runner.invoke(
        sample, [sample_id, "-kv", "customer", customer_id, "-y", "--skip-lims"], obj=base_context
    )

    # THEN it should error about missing customer instead of setting the value
    assert result.exit_code != EXIT_SUCCESS
    assert sample_query.first().customer.internal_id != customer_id


def test_customer(cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers):
    # GIVEN a database with a sample and two customers
    sample_id = helpers.add_sample(base_store).internal_id
    customer_id = helpers.ensure_customer(base_store, "another_customer").internal_id
    sample_query = base_store._get_query(table=Sample)

    assert sample_query.first().customer.internal_id != customer_id

    # WHEN calling set sample with a valid customer
    result = cli_runner.invoke(
        sample, [sample_id, "-kv", "customer", customer_id, "-y", "--skip-lims"], obj=base_context
    )

    # THEN it should set the customer of the sample
    assert result.exit_code == EXIT_SUCCESS
    assert sample_query.first().customer.internal_id == customer_id


def test_invalid_downsampled_to(cli_runner: CliRunner, base_context: CGConfig):
    # GIVEN a database with a sample
    downsampled_to = "downsampled_to"

    # WHEN calling set sample with an invalid value of downsampled to
    result = cli_runner.invoke(
        sample, ["dummy_sample_id", "-kv", "downsampled_to", downsampled_to, "-y"], obj=base_context
    )

    # THEN wrong data type
    assert result.exit_code != EXIT_SUCCESS


def test_downsampled_to(cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers):
    # GIVEN a database with a sample
    sample_id = helpers.add_sample(base_store).internal_id
    downsampled_to = 111111
    sample_query = base_store._get_query(table=Sample)

    assert sample_query.first().downsampled_to != downsampled_to

    # WHEN calling set sample with a valid value of downsampled to
    result = cli_runner.invoke(
        sample, [sample_id, "-kv", "downsampled_to", downsampled_to, "-y"], obj=base_context
    )

    # THEN the value should have been set on the sample
    assert result.exit_code == EXIT_SUCCESS
    assert sample_query.first().downsampled_to == downsampled_to


def test_reset_downsampled_to(
    cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers
):
    # GIVEN a database with a sample
    sample_id = helpers.add_sample(base_store).internal_id
    downsampled_to = 0
    sample_query = base_store._get_query(table=Sample)

    assert sample_query.first().downsampled_to != downsampled_to

    # WHEN calling set sample with a valid reset value of downsampled to
    result = cli_runner.invoke(
        sample, [sample_id, "-kv", "downsampled_to", "", "-y"], obj=base_context
    )

    # THEN the value should have been set on the sample
    assert result.exit_code == EXIT_SUCCESS
    assert not sample_query.first().downsampled_to


def test_invalid_application(
    cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers
):
    # GIVEN a database with a sample
    sample_id = helpers.add_sample(base_store).internal_id
    application_tag = "dummy_application"
    sample_query = base_store._get_query(table=Sample)

    assert sample_query.first().application_version.application.tag != application_tag

    # WHEN calling set sample with an invalid application
    result = cli_runner.invoke(
        sample,
        [sample_id, "-kv", "application_version", application_tag, "-y", "--skip-lims"],
        obj=base_context,
    )

    # THEN it should error about missing application instead of setting the value
    assert result.exit_code != EXIT_SUCCESS
    assert sample_query.first().application_version.application.tag != application_tag


def test_application(cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers):
    # GIVEN a database with a sample and two applications
    sample_obj = helpers.add_sample(base_store)
    application_tag = helpers.ensure_application_version(
        base_store, "another_application"
    ).application.tag
    sample_query = base_store._get_query(table=Sample)

    assert sample_query.first().application_version.application.tag != application_tag

    # WHEN calling set sample with an invalid application
    result = cli_runner.invoke(
        sample,
        [
            sample_obj.internal_id,
            "-kv",
            "application_version",
            application_tag,
            "-y",
        ],
        obj=base_context,
    )

    # THEN the application should have been set in status db
    assert result.exit_code == EXIT_SUCCESS
    assert sample_obj.application_version.application.tag == application_tag
    # THEN the application should have been set in LIMS
    assert base_context.lims_api.get_updated_sample_key() == "application"
    assert base_context.lims_api.get_updated_sample_value() == application_tag
