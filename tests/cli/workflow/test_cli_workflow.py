"""This script tests the cli method enable workflows"""
import logging
from datetime import datetime

from cg.cli.workflow.base import workflow as workflow_cmd
from cg.cli.workflow.commands import store_fastq_analysis, store_available_fastq_analysis
from cg.models.cg_config import CGConfig
from click.testing import CliRunner

from cg.store import models

EXIT_SUCCESS = 0


def test_no_options(cli_runner: CliRunner, base_context: CGConfig):
    """Test command with no options"""
    # GIVEN
    # WHEN dry running
    result = cli_runner.invoke(workflow_cmd, obj=base_context)

    # THEN command should have returned all pipelines that is supported
    assert result.exit_code == EXIT_SUCCESS
    assert "balsamic" in result.output
    assert "microsalt" in result.output
    assert "mip-dna" in result.output
    assert "mip-rna" in result.output


def test_store_fastq_analysis(caplog, case_id: str, cli_runner, fastq_context):
    """Test for CLI command creating an analysis object for a fastq case"""
    # GIVEN a fastq context
    caplog.set_level(logging.INFO)
    case_obj: models.Family = fastq_context.status_db.family(internal_id=case_id)
    case_obj.analyses = []

    # WHEN the store_fastq_analysis command is invoked
    cli_runner.invoke(store_fastq_analysis, [case_id], obj=fastq_context)

    # THEN the run command should be reached
    assert len(fastq_context.status_db.analyses(family=case_obj).all()) > 0


def test_store_available_fastq_analysis(
    caplog, case_id: str, cli_runner, fastq_context, sample_id: str
):
    """Test for CLI command creating an analysis object for all fastq cases to be delivered"""
    caplog.set_level(logging.INFO)
    # GIVEN a case with no analysis, a sample that has been sequenced and a fastq context
    case_obj: models.Family = fastq_context.status_db.family(internal_id=case_id)
    case_obj.analyses = []
    sample_obj: models.Sample = fastq_context.status_db.sample(internal_id=sample_id)
    sample_obj.sequenced_at = datetime.now()

    # WHEN the store_available_fastq_analysis command is invoked
    cli_runner.invoke(store_available_fastq_analysis, ["--dry-run"], obj=fastq_context)

    # THEN the right case should be found and the store_fastq_analysis command should be reached
    assert f"Creating an analysis for case {case_id}" in caplog.text
