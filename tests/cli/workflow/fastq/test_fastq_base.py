import logging
from datetime import datetime

from cg.cli.workflow.fastq.base import (
    store_available_fastq_analysis,
    store_fastq_analysis,
)
from cg.constants.constants import CaseActions, Workflow
from cg.store.models import Analysis, Case, Sample


def test_store_fastq_analysis(another_case_id: str, cli_runner, fastq_context, helpers):
    """Test for CLI command creating an analysis object for a fastq case"""
    # GIVEN a fastq context
    helpers.ensure_case(fastq_context.status_db, case_id=another_case_id)
    case_obj: Case = fastq_context.status_db.get_case_by_internal_id(another_case_id)
    assert not case_obj.analyses

    # WHEN a command is run to create an analysis for the case
    cli_runner.invoke(store_fastq_analysis, [another_case_id], obj=fastq_context)

    # THEN the analysis is created
    assert (
        len(
            fastq_context.status_db._get_query(table=Analysis)
            .filter(Analysis.case_id == case_obj.id)
            .all()
        )
        > 0
    )


def test_store_available_fastq_analysis(
    caplog, another_case_id: str, cli_runner, fastq_context, sample_id: str, helpers
):
    """Test for CLI command creating an analysis object for all fastq cases to be delivered"""
    caplog.set_level(logging.INFO)

    # GIVEN a case with no analysis, a sample that has been sequenced and a fastq context
    sample_obj: Sample = fastq_context.status_db.get_sample_by_internal_id(internal_id=sample_id)
    sample_obj.last_sequenced_at = datetime.now()

    # GIVEN a case with no analysis but which is to be analyzed, a sample that has been sequenced and a fastq context
    case_obj: Case = helpers.add_case_with_sample(
        fastq_context.status_db, case_id=another_case_id, sample_id="sample_for_another_case_id"
    )
    assert not case_obj.analyses
    case_obj.data_analysis = Workflow.FASTQ
    case_obj.action = CaseActions.ANALYZE
    case_obj.samples[0].last_sequenced_at = datetime.now()
    case_obj.samples[0].reads = 1

    # WHEN the store_available_fastq_analysis command is invoked
    cli_runner.invoke(store_available_fastq_analysis, ["--dry-run"], obj=fastq_context)

    # THEN the right case should be found and the store_fastq_analysis command should be reached
    assert f"Creating an analysis for case {another_case_id}" in caplog.text
