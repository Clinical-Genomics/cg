""" This file groups all tests related to microsalt start creation """
import logging

from cg.cli.workflow.microsalt.base import run

EXIT_SUCCESS = 0


def test_no_arguments(cli_runner, base_context):
    """Test command without any options"""

    # GIVEN

    # WHEN dry running without anything specified
    result = cli_runner.invoke(run, obj=base_context)

    # THEN command should mention missing arguments
    assert result.exit_code != EXIT_SUCCESS


def test_dry_arguments(
    cli_runner, base_context, microbial_ticket, queries_path, fastq_path, caplog
):
    """Test command dry """

    # GIVEN
    caplog.set_level(logging.INFO)

    # WHEN dry running without anything specified
    result = cli_runner.invoke(run, ["--dry-run", microbial_ticket], obj=base_context)

    # THEN command should mention missing arguments
    assert result.exit_code == EXIT_SUCCESS

    outfilename = queries_path / microbial_ticket
    outfilename = outfilename.with_suffix(".json")

    fastq_path = fastq_path / str(microbial_ticket)
    assert f"/bin/true analyse {outfilename} --input {fastq_path}" in caplog.text
