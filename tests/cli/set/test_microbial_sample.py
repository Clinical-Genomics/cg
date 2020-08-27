"""Test methods for cg/cli/set/microbial_sample"""
from datetime import datetime

from cg.cli.set import microbial_sample
from cg.store import Store

SUCCESS = 0


def test_invalid_sample_empty_db(cli_runner, base_context):
    # GIVEN an empty database

    # WHEN running set with an sample that does not exist
    sample_id = "dummy_sample_id"
    result = cli_runner.invoke(microbial_sample, [sample_id, "sign"], obj=base_context)

    # THEN then it should complain on invalid sample
    assert result.exit_code != SUCCESS


def test_invalid_sample_non_empty_db(cli_runner, base_context, base_store: Store, helpers):
    # GIVEN a non empty database
    helpers.add_microbial_sample_and_order(base_store)

    # WHEN running set with an sample that does not exist
    sample_id = "dummy_sample_id"
    result = cli_runner.invoke(microbial_sample, [sample_id, "sign"], obj=base_context)

    # THEN then it should complain on invalid sample
    assert result.exit_code != SUCCESS


def test_valid_sample_no_apptag_option(cli_runner, base_context, base_store: Store, helpers):
    # GIVEN a non empty database
    sample = helpers.add_microbial_sample_and_order(base_store)

    # WHEN running set with an sample but without any options
    sample_id = sample.internal_id
    result = cli_runner.invoke(microbial_sample, [sample_id, "sign"], obj=base_context)

    # THEN then it should complain on missing options
    assert result.exit_code != SUCCESS


def test_invalid_application(cli_runner, base_context, base_store: Store, helpers):
    # GIVEN a database with a sample
    sample = helpers.add_microbial_sample_and_order(base_store)
    application_tag = "dummy_application"
    assert (
        base_store.MicrobialSample.query.first().application_version.application.tag
        != application_tag
    )

    # WHEN calling set sample with an invalid application
    result = cli_runner.invoke(
        microbial_sample,
        [sample.internal_id, "sign", "-a", application_tag],
        obj=base_context,
    )

    # THEN then it should complain about missing application instead of setting the value
    assert result.exit_code != SUCCESS
    assert (
        base_store.MicrobialSample.query.first().application_version.application.tag
        != application_tag
    )


def test_valid_application(cli_runner, base_context, base_store: Store, helpers):
    # GIVEN a database with a sample and two applications
    sample = helpers.add_microbial_sample_and_order(base_store)
    application_tag = helpers.ensure_application_version(
        base_store, "another_application"
    ).application.tag
    assert (
        base_store.MicrobialSample.query.first().application_version.application.tag
        != application_tag
    )

    # WHEN calling set sample with an valid application
    signature = "sign"
    result = cli_runner.invoke(
        microbial_sample,
        [sample.internal_id, "sign", "-a", application_tag],
        obj=base_context,
    )

    # THEN then the application should have been set
    assert result.exit_code == SUCCESS
    assert (
        base_store.MicrobialSample.query.first().application_version.application.tag
        == application_tag
    )
    assert signature in base_store.MicrobialSample.query.first().comment


def test_invalid_priority(cli_runner, base_context, base_store: Store, helpers):
    # GIVEN a database with a sample
    sample = helpers.add_microbial_sample_and_order(base_store)
    priority = "dummy_priority"
    assert base_store.MicrobialSample.query.first().priority != priority

    # WHEN calling set sample with an invalid priority
    result = cli_runner.invoke(
        microbial_sample, [sample.internal_id, "sign", "-p", priority], obj=base_context
    )

    # THEN then it should complain about bad priority instead of setting the value
    assert result.exit_code != SUCCESS
    assert base_store.MicrobialSample.query.first().priority_human != priority


def test_valid_priority(cli_runner, base_context, base_store: Store, helpers):
    # GIVEN a database with a sample
    sample = helpers.add_microbial_sample_and_order(base_store)
    priority = "priority"
    assert base_store.MicrobialSample.query.first().priority != priority

    # WHEN calling set sample with an valid priority
    signature = "sign"

    result = cli_runner.invoke(
        microbial_sample, [sample.internal_id, "sign", "-p", priority], obj=base_context
    )

    # THEN then the priority should have been set
    assert result.exit_code == SUCCESS
    assert base_store.MicrobialSample.query.first().priority_human == priority
    assert signature in base_store.MicrobialSample.query.first().comment
