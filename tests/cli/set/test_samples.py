"""Test methods for cg/cli/set/samples"""
import logging

import pytest
from cg.cli.set.base import samples
from cg.models.cg_config import CGConfig
from cg.store import Store

SUCCESS = 0


@pytest.mark.parametrize("identifier_key", ["name", "internal_id"])
def test_set_samples_by_identifiers(
    cli_runner, base_context, base_store: Store, identifier_key, helpers, caplog
):
    # GIVEN a database with a sample
    sample_obj = helpers.add_sample(base_store)
    identifier_value = getattr(sample_obj, identifier_key)

    # WHEN calling set samples with valid identifiers
    with caplog.at_level(logging.INFO):
        result = cli_runner.invoke(
            samples,
            ["-id", identifier_key, identifier_value, "-y", "--skip-lims"],
            obj=base_context,
        )

    # THEN it should name the sample to be changed
    assert result.exit_code == SUCCESS
    assert sample_obj.internal_id in caplog.text
    assert sample_obj.name in caplog.text


def test_set_samples_by_invalid_identifier(
    cli_runner, base_context, base_store: Store, helpers, caplog
):
    # GIVEN a database with a sample that belongs to a case
    sample_obj = helpers.add_sample(base_store)

    # WHEN calling set samples with an identifier not existing on sample
    bad_identifier = "bad_identifier"
    assert not hasattr(sample_obj, bad_identifier)
    with caplog.at_level(logging.INFO):
        result = cli_runner.invoke(
            samples, ["-id", bad_identifier, "any_value", "-y", "--skip-lims"], obj=base_context
        )

    # THEN it should fail and not name the sample to be changed
    assert sample_obj.internal_id not in caplog.text
    assert sample_obj.name not in caplog.text
    assert result.exit_code != SUCCESS


def test_set_samples_by_case_id(cli_runner, base_context, base_store: Store, helpers, caplog):
    # GIVEN a database with a sample that belongs to a case
    case_obj = helpers.add_case(store=base_store)
    sample_obj = helpers.add_sample(base_store)
    helpers.add_relationship(store=base_store, case=case_obj, sample=sample_obj)

    # WHEN calling set samples with case_id
    with caplog.at_level(logging.INFO):
        result = cli_runner.invoke(
            samples, [case_obj.internal_id, "-y", "--skip-lims"], obj=base_context
        )

    # THEN it should name the sample to be changed
    assert result.exit_code == SUCCESS
    assert sample_obj.internal_id in caplog.text
    assert sample_obj.name in caplog.text


def test_set_samples_by_invalid_case_id(
    cli_runner, base_context, base_store: Store, helpers, caplog
):
    # GIVEN a database with a sample that belongs to a case
    sample_obj = helpers.add_sample(base_store)

    # WHEN calling set samples with an identifier not existing on sample
    non_existing_case = "not_a_case"
    assert not base_store.family(non_existing_case)
    with caplog.at_level(logging.INFO):
        result = cli_runner.invoke(
            samples, [non_existing_case, "-y", "--skip-lims"], obj=base_context
        )

    # THEN it should fail and not name the sample to be changed
    assert result.exit_code != SUCCESS
    assert sample_obj.internal_id not in caplog.text
    assert sample_obj.name not in caplog.text


def test_set_samples_by_valid_case_id_and_valid_identifier(
    cli_runner, base_context, base_store: Store, helpers, caplog
):
    # GIVEN a database with a sample that belongs to a case
    case_obj = helpers.add_case(store=base_store)
    sample_obj = helpers.add_sample(base_store)
    helpers.add_relationship(store=base_store, case=case_obj, sample=sample_obj)

    # WHEN calling set samples with case_id for sample and valid identifier for sample
    with caplog.at_level(logging.INFO):
        result = cli_runner.invoke(
            samples,
            [
                case_obj.internal_id,
                "-id",
                "internal_id",
                sample_obj.internal_id,
                "-y",
                "--skip-lims",
            ],
            obj=base_context,
        )

    # THEN it should name the sample to be changed
    assert sample_obj.internal_id in caplog.text
    assert sample_obj.name in caplog.text
    assert result.exit_code == SUCCESS


def test_set_samples_by_invalid_case_id_and_valid_identifier(
    cli_runner, base_context: CGConfig, helpers, caplog
):
    # GIVEN a database with a sample that belongs to a case
    base_store: Store = base_context.status_db
    case_obj = helpers.add_case(store=base_store)
    sample_obj = helpers.add_sample(base_store)
    helpers.add_relationship(store=base_store, case=case_obj, sample=sample_obj)

    # WHEN calling set samples with bad case_id for sample and valid identifier for sample
    with caplog.at_level(logging.INFO):
        result = cli_runner.invoke(
            samples,
            ["wrong_caseid", "-id", "internal_id", sample_obj.internal_id, "-y", "--skip-lims"],
            obj=base_context,
        )

    # THEN it should not name the sample to be changed
    assert sample_obj.internal_id not in caplog.text
    assert sample_obj.name not in caplog.text
    assert result.exit_code != SUCCESS


def test_set_samples_by_valid_case_id_and_invalid_identifier(
    cli_runner, base_context: CGConfig, helpers, caplog
):
    # GIVEN a database with a sample that belongs to a case
    base_store: Store = base_context.status_db
    case_obj = helpers.add_case(store=base_store)
    sample_obj = helpers.add_sample(base_store)
    helpers.add_relationship(store=base_store, case=case_obj, sample=sample_obj)

    # WHEN calling set samples with valid case_id for sample and wrong valid identifier for sample
    with caplog.at_level(logging.INFO):
        result = cli_runner.invoke(
            samples,
            [case_obj.internal_id, "-id", "internal_id", "wrong_internal_id", "-y", "--skip-lims"],
            obj=base_context,
        )

    # THEN it should not name the sample to be changed
    assert sample_obj.internal_id not in caplog.text
    assert sample_obj.name not in caplog.text
    assert result.exit_code != SUCCESS
