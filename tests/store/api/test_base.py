"""Tests for the BaseHandle class."""

from cg.constants.subject import PhenotypeStatus
from sqlalchemy.orm import Query


def test_get_latest_analyses_for_cases_query(
    analysis_store, helpers, timestamp_now, timestamp_yesterday
):
    """Tests that analyses that are not latest are not returned."""

    # GIVEN an analysis a newer analysis exists
    case = helpers.add_case(analysis_store)
    analysis_oldest = helpers.add_analysis(
        analysis_store,
        case=case,
        started_at=timestamp_yesterday,
        uploaded_at=timestamp_yesterday,
        delivery_reported_at=None,
    )
    analysis_store.session.add(analysis_oldest)
    analysis_store.session.commit()
    analysis_newest = helpers.add_analysis(
        analysis_store,
        case=case,
        started_at=timestamp_now,
        uploaded_at=timestamp_now,
        delivery_reported_at=None,
    )
    sample = helpers.add_sample(analysis_store, delivered_at=timestamp_now)
    analysis_store.relate_sample(
        family=analysis_oldest.family, sample=sample, status=PhenotypeStatus.UNKNOWN
    )

    # WHEN calling the analyses_to_delivery_report
    analyses: Query = analysis_store._get_latest_analyses_for_cases_query()

    # THEN analyses is a query
    assert isinstance(analyses, Query)

    # THEN only the newest analysis should be returned
    assert analysis_newest in analyses
    assert analysis_oldest not in analyses
