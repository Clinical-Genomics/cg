from cg.cli.workflow.raw_data.base import store_raw_data_analysis
from cg.store.models import Analysis, Case


def test_store_raw_data_analysis(another_case_id: str, cli_runner, raw_data_fastq_context, helpers):
    """Test for CLI command creating an analysis object for a fastq case"""

    # GIVEN a raw data fastq context
    helpers.ensure_case(raw_data_fastq_context.status_db, case_id=another_case_id)
    case_obj: Case = raw_data_fastq_context.status_db.get_case_by_internal_id(another_case_id)
    assert not case_obj.analyses

    # WHEN a command is run to create an analysis for the case
    cli_runner.invoke(store_raw_data_analysis, [another_case_id], obj=raw_data_fastq_context)

    # THEN the analysis is created
    assert (
        len(
            raw_data_fastq_context.status_db._get_query(table=Analysis)
            .filter(Analysis.case_id == case_obj.id)
            .all()
        )
        > 0
    )
