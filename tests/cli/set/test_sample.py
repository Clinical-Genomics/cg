"""Test methods for cg/cli/set/sample"""
import logging

import pytest
from click.testing import CliRunner

from cg.cli.set.base import sample
from cg.models.cg_config import CGConfig
from cg.store import Store

SUCCESS = 0


def test_invalid_sample(cli_runner: CliRunner, base_context: CGConfig):
    # GIVEN an empty database

    # WHEN running set with a sample that does not exist
    sample_id = "dummy_sample_id"
    result = cli_runner.invoke(sample, [sample_id], obj=base_context)

    # THEN then it should complain on invalid sample
    assert result.exit_code != SUCCESS


def test_skip_lims(cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers):
    # GIVEN a database with a sample

    sample_obj = helpers.add_sample(base_store, gender="female")
    key = "name"
    new_value = "new_value"

    # WHEN setting sample but skipping lims
    result = cli_runner.invoke(
        sample,
        [sample_obj.internal_id, "-kv", "name", "dummy_value", "-y", "--skip-lims"],
        obj=base_context,
    )

    # THEN update sample should have no recorded update key and value
    assert result.exit_code == SUCCESS
    assert base_context.lims_api.get_updated_sample_key() != key
    assert base_context.lims_api.get_updated_sample_value() != new_value


def test_help_without_sample(
    cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers, caplog
):
    # GIVEN a database with no sample

    # WHEN setting sample but asking for help
    with caplog.at_level(logging.INFO):
        result = cli_runner.invoke(sample, ["--help"], obj=base_context)

    # THEN it should fail on not having a sample as argument
    assert result.exit_code != SUCCESS

    # THEN the flags should have been mentioned in the output
    assert "-kv" in caplog.text
    assert "--skip-lims" in caplog.text
    assert "-y" in caplog.text

    # THEN the name property should have been mentioned
    assert "name" in caplog.text


def test_help_with_sample(
    cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers, caplog
):
    # GIVEN a database with a sample

    sample_obj = helpers.add_sample(base_store, gender="female")

    # WHEN setting sample but skipping lims
    with caplog.at_level(logging.INFO):
        result = cli_runner.invoke(sample, [sample_obj.internal_id, "--help"], obj=base_context)

    # THEN it should not fail on not having a sample as argument
    assert result.exit_code == SUCCESS

    # THEN the flags should have been mentioned in the output
    assert "-kv" in caplog.text
    assert "--skip-lims" in caplog.text
    assert "-y" in caplog.text

    # THEN the name property should have been mentioned
    assert "name" in caplog.text

    # THEN the name value should have been mentioned
    assert sample_obj.name in caplog.text


@pytest.mark.parametrize("key", ["name", "capture_kit"])
def test_set_sample(cli_runner: CliRunner, base_context: CGConfig, base_store: Store, key, helpers):
    # GIVEN a database with a sample

    sample_obj = helpers.add_sample(base_store, gender="female")
    new_value = "new_value"
    assert getattr(sample_obj, key) != new_value

    # WHEN setting key on sample to new_value
    result = cli_runner.invoke(
        sample,
        [sample_obj.internal_id, "-kv", key, new_value, "-y"],
        obj=base_context,
        catch_exceptions=False,
    )

    # THEN then it should have new_value as attribute key on the sample and in LIMS
    assert result.exit_code == SUCCESS
    assert getattr(sample_obj, key) == new_value
    assert base_context.lims_api.get_updated_sample_key() == key
    assert base_context.lims_api.get_updated_sample_value() == new_value


def test_sex(cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers):
    # GIVEN a database with a sample

    sample_obj = helpers.add_sample(base_store, gender="female")
    key = "sex"
    new_value = "male"
    assert getattr(sample_obj, key) != new_value

    # WHEN setting key on sample to new_value
    result = cli_runner.invoke(
        sample, [sample_obj.internal_id, "-kv", key, new_value, "-y"], obj=base_context
    )

    # THEN then it should have new_value as attribute key on the sample and in LIMS
    assert result.exit_code == SUCCESS
    assert getattr(sample_obj, key) == new_value
    assert base_context.lims_api.get_updated_sample_key() == key
    assert base_context.lims_api.get_updated_sample_value() == new_value


def test_priority_text(cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers):
    # GIVEN a database with a sample
    sample_obj = helpers.add_sample(base_store, gender="female")
    key = "priority"
    new_value = "express"
    assert sample_obj.priority_human != new_value

    # WHEN setting key on sample to new_value
    result = cli_runner.invoke(
        sample, [sample_obj.internal_id, "-kv", key, new_value, "-y"], obj=base_context
    )

    # THEN then it should have new_value as attribute key on the sample and in LIMS
    assert result.exit_code == SUCCESS
    assert sample_obj.priority_human == new_value
    assert base_context.lims_api.get_updated_sample_key() == key
    assert base_context.lims_api.get_updated_sample_value() == sample_obj.priority_human


def test_priority_number(cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers):
    # GIVEN a database with a sample
    sample_obj = helpers.add_sample(base_store, gender="female")
    key = "priority"
    new_value = 2
    assert sample_obj.priority != new_value

    # WHEN setting key on sample to new_value
    result = cli_runner.invoke(
        sample,
        [sample_obj.internal_id, "-kv", key, new_value, "-y"],
        obj=base_context,
        catch_exceptions=False,
    )

    # THEN then it should have new_value as attribute key on the sample and in LIMS
    assert result.exit_code == SUCCESS
    assert sample_obj.priority == new_value
    assert base_context.lims_api.get_updated_sample_key() == key
    assert base_context.lims_api.get_updated_sample_value() == sample_obj.priority_human


def test_invalid_customer(
    cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers
):
    # GIVEN a database with a sample
    sample_id = helpers.add_sample(base_store).internal_id
    customer_id = "dummy_customer_id"
    assert base_store.Sample.query.first().customer.internal_id != customer_id

    # WHEN calling set sample with an invalid customer
    result = cli_runner.invoke(
        sample, [sample_id, "-kv", "customer", customer_id, "-y", "--skip-lims"], obj=base_context
    )

    # THEN then it should error about missing customer instead of setting the value
    assert result.exit_code != SUCCESS
    assert base_store.Sample.query.first().customer.internal_id != customer_id


def test_customer(cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers):
    # GIVEN a database with a sample and two customers
    sample_id = helpers.add_sample(base_store).internal_id
    customer_id = helpers.ensure_customer(base_store, "another_customer").internal_id
    assert base_store.Sample.query.first().customer.internal_id != customer_id

    # WHEN calling set sample with a valid customer
    result = cli_runner.invoke(
        sample, [sample_id, "-kv", "customer", customer_id, "-y", "--skip-lims"], obj=base_context
    )

    # THEN then it should set the customer of the sample
    assert result.exit_code == SUCCESS
    assert base_store.Sample.query.first().customer.internal_id == customer_id


def test_invalid_downsampled_to(cli_runner: CliRunner, base_context: CGConfig):
    # GIVEN a database with a sample
    downsampled_to = "downsampled_to"

    # WHEN calling set sample with an invalid value of downsampled to
    result = cli_runner.invoke(
        sample, ["dummy_sample_id", "-kv", "downsampled_to", downsampled_to, "-y"], obj=base_context
    )

    # THEN wrong data type
    assert result.exit_code != SUCCESS


def test_downsampled_to(cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers):
    # GIVEN a database with a sample
    sample_id = helpers.add_sample(base_store).internal_id
    downsampled_to = 111111
    assert base_store.Sample.query.first().downsampled_to != downsampled_to

    # WHEN calling set sample with a valid value of downsampled to
    result = cli_runner.invoke(
        sample, [sample_id, "-kv", "downsampled_to", downsampled_to, "-y"], obj=base_context
    )

    # THEN then the value should have been set on the sample
    assert result.exit_code == SUCCESS
    assert base_store.Sample.query.first().downsampled_to == downsampled_to


def test_reset_downsampled_to(
    cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers
):
    # GIVEN a database with a sample
    sample_id = helpers.add_sample(base_store).internal_id
    downsampled_to = 0
    assert base_store.Sample.query.first().downsampled_to != downsampled_to

    # WHEN calling set sample with a valid reset value of downsampled to
    result = cli_runner.invoke(
        sample, [sample_id, "-kv", "downsampled_to", "", "-y"], obj=base_context
    )

    # THEN then the value should have been set on the sample
    assert result.exit_code == SUCCESS
    assert not base_store.Sample.query.first().downsampled_to


def test_invalid_application(
    cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers
):
    # GIVEN a database with a sample
    sample_id = helpers.add_sample(base_store).internal_id
    application_tag = "dummy_application"
    assert base_store.Sample.query.first().application_version.application.tag != application_tag

    # WHEN calling set sample with an invalid application
    result = cli_runner.invoke(
        sample,
        [sample_id, "-kv", "application_version", application_tag, "-y", "--skip-lims"],
        obj=base_context,
    )

    # THEN then it should error about missing application instead of setting the value
    assert result.exit_code != SUCCESS
    assert base_store.Sample.query.first().application_version.application.tag != application_tag


def test_application(cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers):
    # GIVEN a database with a sample and two applications
    sample_obj = helpers.add_sample(base_store)
    application_tag = helpers.ensure_application_version(
        base_store, "another_application"
    ).application.tag
    assert base_store.Sample.query.first().application_version.application.tag != application_tag

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

    # THEN then the application should have been set in status db
    assert result.exit_code == SUCCESS
    assert sample_obj.application_version.application.tag == application_tag
    # THEN then the application should have been set in LIMS
    assert base_context.lims_api.get_updated_sample_key() == "application"
    assert base_context.lims_api.get_updated_sample_value() == application_tag
