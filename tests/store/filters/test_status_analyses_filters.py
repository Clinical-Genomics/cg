from datetime import datetime, timedelta

from cg.store import Store
from cg.store.filters.status_analysis_filters import (
    filter_analyses_by_case_entry_id,
    filter_analyses_by_started_at,
    filter_analyses_not_cleaned,
    filter_analyses_started_before,
    filter_analyses_with_delivery_report,
    filter_analyses_with_pipeline,
    filter_analyses_without_delivery_report,
    filter_completed_analyses,
    filter_not_uploaded_analyses,
    filter_report_analyses_by_pipeline,
    filter_uploaded_analyses,
    filter_valid_analyses_in_production,
    order_analyses_by_completed_at_asc,
    order_analyses_by_uploaded_at_asc,
)
from cg.store.models import Analysis, Family
from cgmodels.cg.constants import Pipeline
from sqlalchemy.orm import Query
from tests.store_helpers import StoreHelpers


def test_filter_valid_analyses_in_production(
    base_store: Store,
    helpers: StoreHelpers,
    case: Family,
    timestamp_now: datetime,
    old_timestamp: datetime,
):
    """Test that an expected analysis is returned when it has a production valid completed_at date."""

    # GIVEN a set of mock analyses
    analysis: Analysis = helpers.add_analysis(store=base_store, completed_at=timestamp_now)
    outdated_analysis: Analysis = helpers.add_analysis(
        store=base_store, case=case, completed_at=old_timestamp
    )

    # WHEN retrieving valid in production analyses
    analyses: Query = filter_valid_analyses_in_production(
        analyses=base_store._get_query(table=Analysis)
    )

    # ASSERT that analyses is a query
    assert isinstance(analyses, Query)

    # THEN only the up-to-date analysis should be returned
    assert analysis in analyses
    assert outdated_analysis not in analyses


def test_filter_analyses_with_pipeline(base_store: Store, helpers: StoreHelpers, case: Family):
    """Test analyses filtering by pipeline."""

    # GIVEN a set of mock analyses
    balsamic_analysis: Analysis = helpers.add_analysis(store=base_store, pipeline=Pipeline.BALSAMIC)
    mip_analysis: Analysis = helpers.add_analysis(
        store=base_store, case=case, pipeline=Pipeline.MIP_DNA
    )

    # WHEN extracting the analyses
    analyses: Query = filter_analyses_with_pipeline(
        analyses=base_store._get_query(table=Analysis), pipeline=Pipeline.BALSAMIC
    )

    # ASSERT that analyses is a query
    assert isinstance(analyses, Query)

    # THEN only the BALSAMIC analysis should be retrieved
    assert balsamic_analysis in analyses
    assert mip_analysis not in analyses


def test_filter_completed_analyses(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test filtering of completed analyses."""

    # GIVEN a mock analysis
    analysis: Analysis = helpers.add_analysis(store=base_store, completed_at=timestamp_now)

    # WHEN retrieving the completed analyses
    analyses: Query = filter_completed_analyses(analyses=base_store._get_query(table=Analysis))

    # ASSERT that analyses is a query
    assert isinstance(analyses, Query)

    # THEN the completed analysis should be obtained
    assert analysis in analyses


def test_filter_filter_uploaded_analyses(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test filtering of analysis with an uploaded_at field."""

    # GIVEN a mock uploaded analysis
    analysis: Analysis = helpers.add_analysis(store=base_store, uploaded_at=timestamp_now)

    # WHEN calling the upload filtering function
    analyses: Query = filter_uploaded_analyses(analyses=base_store._get_query(table=Analysis))

    # ASSERT that analyses is a query
    assert isinstance(analyses, Query)

    # THEN the uploaded analysis should be retrieved
    assert analysis in analyses


def test_filter_not_uploaded_analyses(base_store: Store, helpers: StoreHelpers):
    """Test filtering of analysis that has not been uploaded."""

    # GIVEN a mock not uploaded analysis
    not_uploaded_analysis: Analysis = helpers.add_analysis(store=base_store, uploaded_at=None)

    # WHEN calling the upload filtering function
    analyses: Query = filter_not_uploaded_analyses(analyses=base_store._get_query(table=Analysis))

    # ASSERT that analyses is a query
    assert isinstance(analyses, Query)

    # THEN the uploaded analysis should be retrieved
    assert not_uploaded_analysis in analyses


def test_filter_analyses_with_delivery_report(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test filtering of analysis with a delivery report generated."""

    # GIVEN an analysis with a delivery report
    analysis: Analysis = helpers.add_analysis(store=base_store, delivery_reported_at=timestamp_now)

    # WHEN calling the delivery report analysis filtering function
    analyses: Query = filter_analyses_with_delivery_report(
        analyses=base_store._get_query(table=Analysis)
    )

    # ASSERT that analyses is a query
    assert isinstance(analyses, Query)

    # THEN the analysis containing the delivery report should be extracted
    assert analysis in analyses


def test_filter_analyses_without_delivery_report(base_store: Store, helpers: StoreHelpers):
    """Test filtering of analysis without a delivery report generated."""

    # GIVEN an analysis with a delivery report
    analysis_without_delivery_report: Analysis = helpers.add_analysis(
        store=base_store, delivery_reported_at=None
    )

    # WHEN calling the delivery report analysis filtering function
    analyses: Query = filter_analyses_without_delivery_report(
        analyses=base_store._get_query(table=Analysis)
    )

    # ASSERT that analyses is a query
    assert isinstance(analyses, Query)

    # THEN the analysis without a delivery report should be extracted
    assert analysis_without_delivery_report in analyses


def test_filter_report_analyses_by_pipeline(base_store: Store, helpers: StoreHelpers, case: Family):
    """Test filtering delivery report related analysis by pipeline."""

    # GIVEN a set of mock analysis
    balsamic_analysis: Analysis = helpers.add_analysis(store=base_store, pipeline=Pipeline.BALSAMIC)
    fluffy_analysis: Analysis = helpers.add_analysis(
        store=base_store, case=case, pipeline=Pipeline.FLUFFY
    )

    # WHEN filtering delivery report related analyses
    analyses: Query = filter_report_analyses_by_pipeline(
        analyses=base_store._get_query(table=Analysis), pipeline=Pipeline.BALSAMIC
    )

    # ASSERT that analyses is a query
    assert isinstance(analyses, Query)

    # THEN only the delivery report supported analysis should be retrieved
    assert balsamic_analysis in analyses
    assert fluffy_analysis not in analyses


def test_order_analyses_by_completed_at_asc(
    store: Store,
    helpers: StoreHelpers,
    case: Family,
    timestamp_now: datetime,
    timestamp_yesterday: datetime,
):
    """Test sorting of analyses by the completed_at field."""

    # GIVEN a set of mock analyses
    helpers.add_analysis(store=store, completed_at=timestamp_now)
    helpers.add_analysis(store=store, case=case, completed_at=timestamp_yesterday)

    # WHEN ordering the analyses by the completed_at field
    analyses: Query = order_analyses_by_completed_at_asc(analyses=store._get_query(table=Analysis))

    # ASSERT that analyses is a query
    assert isinstance(analyses, Query)

    # THEN the oldest analysis should be the first one in the list
    for index in range(0, analyses.count() - 1):
        assert analyses.all()[index].completed_at <= analyses.all()[index + 1].completed_at


def test_order_analyses_by_uploaded_at_asc(
    store_with_older_and_newer_analyses: Store,
):
    """Test sorting of analyses by the uploaded_at field."""
    # GIVEN a store with mock analyses

    # WHEN ordering the analyses by the uploaded_at field
    analyses: Query = order_analyses_by_uploaded_at_asc(
        analyses=store_with_older_and_newer_analyses._get_query(table=Analysis)
    )

    # ASSERT that analyses is a query
    assert isinstance(analyses, Query)

    # THEN the oldest analysis should be the first one in the list
    for index in range(0, analyses.count() - 1):
        assert analyses.all()[index].uploaded_at <= analyses.all()[index + 1].uploaded_at


def test_filter_analysis_by_case(base_store: Store, helpers: StoreHelpers, case: Family):
    """Test filtering of analyses by case."""

    # GIVEN a set of mock analyses
    analysis: Analysis = helpers.add_analysis(store=base_store)
    analysis_other_case: Analysis = helpers.add_analysis(store=base_store, case=case)

    # WHEN filtering the analyses by case
    analyses: Query = filter_analyses_by_case_entry_id(
        analyses=base_store._get_query(table=Analysis), case_entry_id=case.id
    )

    # ASSERT that analyses is a query
    assert isinstance(analyses, Query)

    # THEN only the analysis belonging to the case should be retrieved
    assert analysis not in analyses
    assert analysis_other_case in analyses
    assert analysis_other_case.family == case


def test_filter_analysis_started_before(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test filtering of analyses started before a given date."""

    # GIVEN a set of mock analyses
    analysis_old: Analysis = helpers.add_analysis(
        store=base_store, started_at=timestamp_now - timedelta(days=1)
    )
    analysis: Analysis = helpers.add_analysis(
        store=base_store, started_at=timestamp_now, case=analysis_old.family
    )

    # WHEN filtering the analyses by started_at
    analyses: Query = filter_analyses_started_before(
        analyses=base_store._get_query(table=Analysis), started_at_date=timestamp_now
    )

    # ASSERT that analyses is a query
    assert isinstance(analyses, Query)

    # THEN all analyses started before the given date should be retrieved
    for analysis in analyses:
        assert analysis.started_at <= timestamp_now


def test_filter_analysis_not_cleaned(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test filtering of analyses that have not been cleaned."""

    # GIVEN a set of mock analyses
    analysis_cleaned: Analysis = helpers.add_analysis(store=base_store, cleaned_at=timestamp_now)
    analysis: Analysis = helpers.add_analysis(
        store=base_store, cleaned_at=None, case=analysis_cleaned.family
    )

    # WHEN filtering the analyses by cleaned_at
    analyses: Query = filter_analyses_not_cleaned(analyses=base_store._get_query(table=Analysis))

    # ASSERT that analyses is a query
    assert isinstance(analyses, Query)

    # THEN only the analysis that have not been cleaned should be retrieved
    assert analysis in analyses
    assert analysis_cleaned not in analyses


def test_filter_analyses_by_started_at(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime, timestamp_yesterday: datetime
):
    """Test filtering of analyses by started at."""

    # GIVEN a set of mock analyses
    analysis_started_now: Analysis = helpers.add_analysis(
        store=base_store, started_at=timestamp_now
    )
    analysis_started_old: Analysis = helpers.add_analysis(
        store=base_store,
        started_at=timestamp_yesterday,
        case=analysis_started_now.family,
    )

    # WHEN filtering the analyses by started_at
    analyses: Query = filter_analyses_by_started_at(
        analyses=base_store._get_query(table=Analysis), started_at_date=timestamp_yesterday
    )

    # ASSERT that analyses is a query
    assert isinstance(analyses, Query)

    # THEN only the analysis that have been started after the given date should be retrieved
    assert analysis_started_now not in analyses
    assert analysis_started_old in analyses
