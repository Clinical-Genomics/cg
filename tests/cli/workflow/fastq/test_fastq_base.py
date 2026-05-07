from pathlib import Path
from unittest.mock import Mock, create_autospec

from cg.apps.tb.api import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.cli.workflow.raw_data.base import store_raw_data_analysis
from cg.store.models import Analysis, Case


def test_store_raw_data_analysis(another_case_id: str, cli_runner, raw_data_fastq_context, helpers):
    """Test for CLI command creating an analysis object for a fastq case"""
    trailblazer_api: TrailblazerAPI = create_autospec(TrailblazerAPI)
    trailblazer_api.add_pending_analysis = Mock(
        return_value=TrailblazerAnalysis(
            id=67,
            logged_at="1992-12-13",  # type: ignore pydantic model
            started_at="1992-12-13",  # type: ignore pydantic model
            completed_at=None,
            out_dir=Path("great_path"),
            config_path=Path("great_config_path"),
        )
    )
    raw_data_fastq_context.trailblazer_api_ = trailblazer_api

    # GIVEN a raw data fastq context
    order = helpers.add_order(
        store=raw_data_fastq_context.status_db, customer_id=666, ticket_id=666
    )
    helpers.ensure_case(raw_data_fastq_context.status_db, case_id=another_case_id, order=order)
    case_obj: Case = raw_data_fastq_context.status_db.get_case_by_internal_id(another_case_id)
    assert not case_obj.analyses

    # WHEN a command is run to create an analysis for the case
    cli_runner.invoke(
        store_raw_data_analysis,
        [another_case_id],
        obj=raw_data_fastq_context,
        catch_exceptions=False,
    )

    # THEN the analysis is created
    assert (
        raw_data_fastq_context.status_db._get_query(table=Analysis)
        .filter(Analysis.case_id == case_obj.id)
        .count()
    ) > 0
