"""Test methods for cg cli set list_keys"""

import logging

from click.testing import CliRunner

from cg.cli.set.base import list_keys
from cg.constants import EXIT_SUCCESS
from cg.constants.subject import Sex
from cg.models.cg_config import CGConfig
from cg.store.store import Store


def test_list_keys_without_sample(
    cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers, caplog
):
    # GIVEN a database with no sample

    # WHEN setting sample but asking for help
    with caplog.at_level(logging.INFO):
        result = cli_runner.invoke(list_keys, obj=base_context)

    # THEN it should not fail on not having a sample as argument
    assert result.exit_code == EXIT_SUCCESS

    # THEN the flags should have been mentioned in the output
    assert "-kv" in caplog.text

    # THEN the name property should have been mentioned
    assert "name" in caplog.text


def test_list_keys_with_sample(
    cli_runner: CliRunner, base_context: CGConfig, base_store: Store, helpers, caplog
):
    # GIVEN a database with a sample

    sample = helpers.add_sample(base_store, sex=Sex.FEMALE)

    # WHEN setting sample but skipping lims
    with caplog.at_level(logging.INFO):
        result = cli_runner.invoke(list_keys, ["--sample_id", sample.internal_id], obj=base_context)

    # THEN it should not fail on having a sample as argument
    assert result.exit_code == EXIT_SUCCESS

    # THEN the flags should have been mentioned in the output
    assert "-kv" in caplog.text

    # THEN the name property should have been mentioned
    assert "name" in caplog.text

    # THEN the name value should have been mentioned
    assert sample.name in caplog.text
