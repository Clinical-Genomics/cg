"""Tests for running the delivery command"""

import logging
from pathlib import Path

from cg.cli.deliver.base import deliver_analysis, deliver_ticket
from cg.constants.process import EXIT_SUCCESS
from cg.models.cg_config import CGConfig
from cg.store import Store
from click.testing import CliRunner


def test_run_deliver_with_help(cli_runner: CliRunner, base_context: CGConfig):
    # GIVEN a cli runner and a base context
    # WHEN running the deliver command with help text
    result = cli_runner.invoke(deliver_analysis, ["--help"], obj=base_context)

    # THEN assert the command exits without problems
    assert result.exit_code == 0
    # THEN assert that the help text is displayed
    assert "Deliver analysis files to customer inbox" in result.output


def test_run_deliver_without_specifying_case_or_ticket(
    cli_runner: CliRunner, base_context: CGConfig, caplog
):
    caplog.set_level(logging.INFO)
    # GIVEN a cli runner and a base context
    # WHEN running the deliver command with help text
    result = cli_runner.invoke(deliver_analysis, ["--delivery-type", "mip-dna"], obj=base_context)

    # THEN assert the command exits without problems
    assert result.exit_code == 0
    # THEN assert that the help text is displayed
    assert "Please provide a case-id or ticket-id" in caplog.text


def test_run_deliver_non_existing_case(
    cli_runner: CliRunner, base_context: CGConfig, case_id: str, caplog
):
    """Test to run the deliver command when the provided case does not exist"""
    caplog.set_level(logging.WARNING)
    # GIVEN a cli runner and a base context
    # GIVEN a case_id that does not exist in the database
    store: Store = base_context.status_db
    assert store.get_case_by_internal_id(internal_id=case_id) is None

    # WHEN running the deliver command with the non existing case
    result = cli_runner.invoke(
        deliver_analysis, ["--case-id", case_id, "--delivery-type", "mip-dna"], obj=base_context
    )

    # THEN assert the command exits without problems
    assert result.exit_code == 0
    # THEN assert that the correct warning is displayed
    assert f"Could not find case {case_id}" in caplog.text


def test_delivery_with_dry_run(
    cli_runner: CliRunner,
    populated_mip_context: CGConfig,
    case_id: str,
    delivery_inbox: Path,
    caplog,
):
    """Test to run the delivery command with dry run enabled"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a cli runner
    # GIVEN a context with a case that have files in housekeeper to deliver
    # GIVEN that the delivery path does not exist
    assert delivery_inbox.exists() is False

    # WHEN running the deliver analysis command in dry run mode
    cli_runner.invoke(
        deliver_analysis,
        ["--case-id", case_id, "--delivery-type", "mip-dna", "--dry-run"],
        obj=populated_mip_context,
    )

    # THEN assert that the path to the delivery folder was not created
    assert delivery_inbox.exists() is False

    # THEN assert that it is communicated that at least one file would be linked
    assert "Would hard link file" in caplog.text


def test_delivery_path_created(
    cli_runner: CliRunner, populated_mip_context: CGConfig, case_id: str, delivery_inbox: Path
):
    """Test that the delivery path is created when running the deliver analysis command"""
    # GIVEN a context with a case that have files in housekeeper to deliver
    # GIVEN a cli runner
    # GIVEN that the delivery file does not exist
    assert delivery_inbox.exists() is False

    # WHEN running the deliver analysis command
    cli_runner.invoke(
        deliver_analysis,
        ["--case-id", case_id, "--delivery-type", "mip-dna"],
        obj=populated_mip_context,
    )

    # THEN assert that the path to the delivery folder was created
    assert delivery_inbox.exists() is True


def test_delivery_ticket_id(
    cli_runner: CliRunner,
    populated_mip_context: CGConfig,
    delivery_inbox: Path,
    ticket_id: str,
):
    """Test that to run the deliver command with ticket nr"""
    # GIVEN a context with a case that have files in housekeeper to deliver
    # GIVEN a cli runner
    # GIVEN that the delivery file does not exist
    assert delivery_inbox.exists() is False

    # WHEN running the deliver analysis command
    cli_runner.invoke(
        deliver_analysis,
        ["--ticket", ticket_id, "--delivery-type", "mip-dna"],
        obj=populated_mip_context,
    )

    # THEN assert that the path to the delivery folder was created
    assert delivery_inbox.exists() is True


def test_run_deliver_multiple_delivery_flags(
    cli_runner: CliRunner,
    populated_mip_context: CGConfig,
    case_id: str,
    deliver_vcf_path: Path,
    deliver_fastq_path: Path,
    caplog,
):
    """Test to run the deliver command when the provided case does not exist"""
    caplog.set_level(logging.WARNING)
    # GIVEN a context with a case that has files and a sample with a file, in housekeeper to deliver
    # GIVEN a cli runner
    # WHEN running the deliver command with multiple delivery flags

    assert deliver_vcf_path.exists() is False
    assert deliver_fastq_path.exists() is False

    result = cli_runner.invoke(
        deliver_analysis,
        ["--case-id", case_id, "--delivery-type", "fastq", "--delivery-type", "mip-dna"],
        obj=populated_mip_context,
    )

    # THEN assert the command exits without problems
    assert result.exit_code == 0
    # THEN assert that the case file was delivered to the inbox
    assert deliver_vcf_path.exists() is True
    # THEN assert that the sample file was delivered to the inbox
    assert deliver_fastq_path.exists() is True


def test_case_file_is_delivered(
    populated_mip_context: CGConfig, case_id: str, deliver_vcf_path: Path, cli_runner: CliRunner
):
    """Test that the a case file is delivered when running the delivery command"""
    # GIVEN a context with a case that have files in housekeeper to deliver
    # GIVEN a cli runner
    # GIVEN that a case vcf does not exist
    assert deliver_vcf_path.exists() is False

    # WHEN running the deliver analysis command
    cli_runner.invoke(
        deliver_analysis,
        ["--case-id", case_id, "--delivery-type", "mip-dna"],
        obj=populated_mip_context,
    )

    # THEN assert that the case file was delivered to the inbox
    assert deliver_vcf_path.exists() is True


def test_delivering_analysis_with_missing_bundle_errors(
    cli_runner: CliRunner,
    context_with_missing_bundle: CGConfig,
    ticket_id: str,
):
    """Test that the deliver command fails when a bundle is missing."""
    # GIVEN a context with a case that does not have files in housekeeper to deliver.
    # GIVEN a cli runner
    # WHEN running the deliver analysis command
    result = cli_runner.invoke(
        deliver_analysis,
        ["--ticket", ticket_id, "--delivery-type", "mip-dna"],
        obj=context_with_missing_bundle,
    )

    # THEN assert that the command failed
    assert result.exit_code is not EXIT_SUCCESS


def test_delivering_analysis_with_missing_bundle_ignoring_errors(
    cli_runner: CliRunner,
    context_with_missing_bundle: CGConfig,
    delivery_inbox: Path,
    ticket_id: str,
):
    """Test that it is possible to deliver analysis with a missing bundle using the --ignore-missing-bundles flag."""
    # GIVEN a context without files in housekeeper to deliver.
    # GIVEN a cli runner
    # GIVEN that the delivery file does not exist
    assert delivery_inbox.exists() is False

    # WHEN running the deliver analysis command
    cli_runner.invoke(
        deliver_analysis,
        ["--ticket", ticket_id, "--ignore-missing-bundles", "--delivery-type", "mip-dna"],
        obj=context_with_missing_bundle,
    )

    # THEN assert that the path to the delivery folder was created
    assert delivery_inbox.exists() is True


def test_deliver_ticket_with_missing_bundle(
    cli_runner: CliRunner, context_with_missing_bundle: CGConfig, caplog, ticket_id
):
    caplog.set_level(logging.INFO)

    # GIVEN a cli runner
    # WHEN running cg deliver ticket
    result = cli_runner.invoke(
        deliver_ticket,
        [
            "--ticket",
            ticket_id,
            "--dry-run",
            "--ignore-missing-bundles",
            "--delivery-type",
            "mip-dna",
        ],
        obj=context_with_missing_bundle,
    )

    # THEN assert that the command succeeded and files are delivered
    assert result.exit_code is EXIT_SUCCESS
    assert "Delivering files to customer inbox on the HPC" in caplog.text
