"""This file tests the analyses_to_clean part of the status api"""

from datetime import datetime

from cg.constants import Workflow
from cg.store.models import CaseSample
from cg.store.store import Store


def test_analysis_included(
    analysis_store: Store, helpers, timestamp_now: datetime, timestamp_yesterday: datetime
):
    """Tests that analyses that are uploaded are returned."""

    # GIVEN an analysis that is uploaded
    analysis = helpers.add_analysis(
        analysis_store,
        started_at=timestamp_yesterday,
        uploaded_at=timestamp_yesterday,
        cleaned_at=None,
    )
    sample = helpers.add_sample(analysis_store, delivered_at=timestamp_yesterday)
    link: CaseSample = analysis_store.relate_sample(
        case=analysis.case, sample=sample, status="unknown"
    )
    analysis_store.session.add(link)

    # WHEN calling the analyses_to_clean
    analyses_to_clean = analysis_store.get_analyses_to_clean(before=timestamp_now)

    # THEN this analysis should be returned
    assert analysis in analyses_to_clean


def test_analysis_excluded(analysis_store: Store, helpers, timestamp_now: datetime):
    """Tests that analyses that are completed but lacks delivery report are returned."""

    # GIVEN an analysis that is not uploaded
    analysis = helpers.add_analysis(
        analysis_store, started_at=timestamp_now, uploaded_at=None, cleaned_at=None
    )
    sample = helpers.add_sample(analysis_store, delivered_at=timestamp_now)
    link: CaseSample = analysis_store.relate_sample(
        case=analysis.case, sample=sample, status="unknown"
    )
    analysis_store.session.add(link)

    # WHEN calling the analyses_to_clean
    analyses_to_clean = analysis_store.get_analyses_to_clean()

    # THEN this analysis should be returned
    assert analysis not in analyses_to_clean


def test_workflow_included(
    analysis_store: Store, helpers, timestamp_now: datetime, timestamp_yesterday: datetime
):
    """Tests that analyses that are included depending on workflow."""

    # GIVEN an analysis that is uploaded and workflow is specified
    workflow = Workflow.BALSAMIC
    analysis = helpers.add_analysis(
        analysis_store,
        started_at=timestamp_yesterday,
        uploaded_at=timestamp_yesterday,
        cleaned_at=None,
        workflow=workflow,
    )
    sample = helpers.add_sample(analysis_store, delivered_at=timestamp_yesterday)
    link: CaseSample = analysis_store.relate_sample(
        case=analysis.case, sample=sample, status="unknown"
    )
    analysis_store.session.add(link)

    # WHEN calling the analyses_to_clean specifying the used workflow
    analyses_to_clean = analysis_store.get_analyses_to_clean(
        before=timestamp_now, workflow=workflow
    )

    # THEN this analysis should be returned
    assert analysis in analyses_to_clean


def test_workflow_excluded(analysis_store: Store, helpers, timestamp_now: datetime):
    """Tests that analyses are excluded depending on workflow."""

    # GIVEN an analysis that is uploaded

    used_workflow = Workflow.BALSAMIC
    wrong_workflow = Workflow.MIP_DNA
    analysis = helpers.add_analysis(
        analysis_store,
        started_at=timestamp_now,
        uploaded_at=timestamp_now,
        cleaned_at=None,
        workflow=used_workflow,
    )
    sample = helpers.add_sample(analysis_store, delivered_at=timestamp_now)
    link: CaseSample = analysis_store.relate_sample(
        case=analysis.case, sample=sample, status="unknown"
    )
    analysis_store.session.add(link)

    # WHEN calling the analyses_to_clean specifying another workflow
    analyses_to_clean = analysis_store.get_analyses_to_clean(workflow=wrong_workflow)

    # THEN this analysis should not be returned
    assert analysis not in analyses_to_clean


def test_non_cleaned_included(
    analysis_store: Store, helpers, timestamp_now: datetime, timestamp_yesterday: datetime
):
    """Tests that analyses that are included depending on cleaned_at."""

    # GIVEN an analysis that is uploaded but not cleaned
    analysis = helpers.add_analysis(
        analysis_store,
        started_at=timestamp_yesterday,
        uploaded_at=timestamp_yesterday,
        cleaned_at=None,
    )
    sample = helpers.add_sample(analysis_store, delivered_at=timestamp_yesterday)
    link: CaseSample = analysis_store.relate_sample(
        case=analysis.case, sample=sample, status="unknown"
    )
    analysis_store.session.add(link)

    # WHEN calling the analyses_to_clean
    analyses_to_clean = analysis_store.get_analyses_to_clean(before=timestamp_now)

    # THEN this analysis should be returned
    assert analysis in analyses_to_clean


def test_cleaned_excluded(analysis_store: Store, helpers, timestamp_now: datetime):
    """Tests that analyses are excluded depending on cleaned_at."""

    # GIVEN an analysis that is cleaned
    analysis = helpers.add_analysis(
        analysis_store,
        started_at=timestamp_now,
        uploaded_at=timestamp_now,
        cleaned_at=timestamp_now,
    )
    sample = helpers.add_sample(analysis_store, delivered_at=timestamp_now)
    link: CaseSample = analysis_store.relate_sample(
        case=analysis.case, sample=sample, status="unknown"
    )
    analysis_store.session.add(link)

    # WHEN calling the analyses_to_clean
    analyses_to_clean = analysis_store.get_analyses_to_clean()

    # THEN this analysis should not be returned
    assert analysis not in analyses_to_clean
