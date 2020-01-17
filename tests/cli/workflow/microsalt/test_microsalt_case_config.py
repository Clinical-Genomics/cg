""" This file groups all tests related to microsalt case config creation """

import logging
from snapshottest import Snapshot

from cg.cli.workflow.microsalt.base import case_config

EXIT_SUCCESS = 0


def test_no_arguments(cli_runner, base_context, caplog):
    """Test command without any options"""

    # GIVEN

    # WHEN dry running without anything specified
    result = cli_runner.invoke(case_config, obj=base_context)

    # THEN command should mention missing arguments
    assert result.exit_code != EXIT_SUCCESS
    assert "Aborted!" in result.output
    with caplog.at_level(logging.ERROR):
        assert "provide project and/or sample" in caplog.text


def test_dry_sample(cli_runner, base_context, microbial_sample_id, snapshot: Snapshot):
    """Test working dry command for sample"""

    # GIVEN

    # WHEN dry running a sample name
    result = cli_runner.invoke(
        case_config, ["--dry", microbial_sample_id], obj=base_context
    )

    # THEN command should give us a json dump
    assert result.exit_code == EXIT_SUCCESS
    snapshot.assert_match(result.output)


def test_no_sample_found(cli_runner, base_context, caplog):
    """Test missing sample command """

    # GIVEN a not existing sample
    microbial_sample_id = "not_existing_sample"

    # WHEN dry running a sample name
    result = cli_runner.invoke(
        case_config, [microbial_sample_id], obj=base_context
    )

    # THEN command should mention missing sample
    assert result.exit_code != EXIT_SUCCESS
    with caplog.at_level(logging.ERROR):
        assert f"Sample {microbial_sample_id} not found" in caplog.text


def test_no_project_found(cli_runner, base_context, caplog):
    """Test missing project command """

    # GIVEN a not existing project 
    microbial_project_id = "not_existing_project"

    # WHEN dry running a project name
    result = cli_runner.invoke(
        case_config, ['--project', microbial_project_id], obj=base_context
    )

    # THEN command should mention missing project
    assert result.exit_code != EXIT_SUCCESS
    with caplog.at_level(logging.ERROR):
        assert f"Project {microbial_project_id} not found" in caplog.text


def test_no_sample_project_found(cli_runner, base_context, caplog):
    """Test missing sample and project command """

    # GIVEN a not existing project 
    microbial_sample_id = "not_existing_sample"
    microbial_project_id = "not_existing_project"

    # WHEN dry running a project name
    result = cli_runner.invoke(
        case_config, ['--project', microbial_project_id, microbial_sample_id], obj=base_context
    )

    # THEN command should mention missing project
    assert result.exit_code != EXIT_SUCCESS
    with caplog.at_level(logging.ERROR):
        assert f"Samples {microbial_sample_id} not found in {microbial_project_id}" in caplog.text
