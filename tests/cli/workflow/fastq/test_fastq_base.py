import logging
from datetime import datetime

from cg.cli.workflow.fastq.base import store_fastq_analysis, store_available_fastq_analysis
from cg.store import models


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
