from datetime import datetime

from alchy import Query
from cgmodels.cg.constants import Pipeline

from cg.constants import DataDelivery
from cg.store import Store, models
from cg.store.status_analysis_filters import (
    filter_valid_analyses_in_production,
    filter_analyses_with_pipeline,
    filter_completed_analyses,
    filter_not_completed_analyses,
    filter_uploaded_analyses,
    filter_not_uploaded_analyses,
    filter_analyses_with_delivery_report,
    filter_analyses_without_delivery_report,
    filter_report_analyses_by_pipeline,
    order_analyses_by_uploaded_at,
    order_analyses_by_completed_at,
)
from tests.store_helpers import StoreHelpers


def test_filter_valid_analyses_in_production(
    base_store: Store,
    helpers: StoreHelpers,
    case_obj: models.Family,
    timestamp_now: datetime,
    old_timestamp: datetime,
):
    """Test that an expected analysis is returned when it has a production valid completed_at date."""

    # GIVEN a set of mock analyses
    analysis: models.Analysis = helpers.add_analysis(store=base_store, completed_at=timestamp_now)
    outdated_analysis: models.Analysis = helpers.add_analysis(
        store=base_store, case=case_obj, completed_at=old_timestamp
    )
    # GIVEN an analysis query
    analyses_query: Query = base_store.latest_analyses()

    # WHEN retrieving valid in production analyses
    analyses: Query = filter_valid_analyses_in_production(analyses_query)

    # THEN only the up-to-date analysis should be returned
    assert analysis in analyses
    assert outdated_analysis not in analyses


def test_filter_analyses_with_pipeline(
    base_store: Store, helpers: StoreHelpers, case_obj: models.Family
):
    """Test analyses filtering by pipeline."""

    # GIVEN a set of mock analyses
    balsamic_analysis: models.Analysis = helpers.add_analysis(
        store=base_store, pipeline=Pipeline.BALSAMIC
    )
    mip_analysis: models.Analysis = helpers.add_analysis(
        store=base_store, case=case_obj, pipeline=Pipeline.MIP_DNA
    )

    # GIVEN an analysis query
    analyses_query: Query = base_store.latest_analyses()

    # WHEN extracting the analyses
    analyses: Query = filter_analyses_with_pipeline(analyses_query, pipeline=Pipeline.BALSAMIC)

    # THEN only the BALSAMIC analysis should be retrieved
    assert balsamic_analysis in analyses
    assert mip_analysis not in analyses


def test_filter_completed_analyses(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test filtering of completed analyses."""

    # GIVEN a mock analysis
    analysis: models.Analysis = helpers.add_analysis(store=base_store, completed_at=timestamp_now)

    # GIVEN an analysis query
    analyses_query: Query = base_store.latest_analyses()

    # WHEN retrieving the completed analyses
    analyses: Query = filter_completed_analyses(analyses_query)

    # THEN the completed analysis should be obtained
    assert analysis in analyses


def test_filter_not_completed_analyses(base_store: Store, helpers: StoreHelpers):
    """Test filtering of ongoing analyses."""

    # GIVEN a mock not completed analysis
    analysis_not_completed: models.Analysis = helpers.add_analysis(
        store=base_store, completed_at=None
    )

    # GIVEN an analysis query
    analyses_query: Query = base_store.latest_analyses()

    # WHEN retrieving the not completed analyses
    analyses: Query = filter_not_completed_analyses(analyses_query)

    # THEN the expected analysis should be retrieved
    assert analysis_not_completed in analyses


def test_filter_uploaded_analyses(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test filtering of analysis with an uploaded_at field."""

    # GIVEN a mock uploaded analysis
    analysis: models.Analysis = helpers.add_analysis(store=base_store, uploaded_at=timestamp_now)

    # GIVEN an analysis query
    analyses_query: Query = base_store.latest_analyses()

    # WHEN calling the upload filtering function
    analyses: Query = filter_uploaded_analyses(analyses_query)

    # THEN the uploaded analysis should be retrieved
    assert analysis in analyses


def test_filter_not_uploaded_analyses(base_store: Store, helpers: StoreHelpers):
    """Test filtering of analysis that has not been uploaded."""

    # GIVEN a mock not uploaded analysis
    not_uploaded_analysis: models.Analysis = helpers.add_analysis(
        store=base_store, uploaded_at=None
    )

    # GIVEN an analysis query
    analyses_query: Query = base_store.latest_analyses()

    # WHEN calling the upload filtering function
    analyses: Query = filter_not_uploaded_analyses(analyses_query)

    # THEN the uploaded analysis should be retrieved
    assert not_uploaded_analysis in analyses


def test_filter_analyses_with_delivery_report(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test filtering of analysis with a delivery report generated."""

    # GIVEN an analysis with a delivery report
    analysis: models.Analysis = helpers.add_analysis(
        store=base_store, delivery_reported_at=timestamp_now
    )

    # GIVEN an analysis query
    analyses_query: Query = base_store.latest_analyses()

    # WHEN calling the delivery report analysis filtering function
    analyses: Query = filter_analyses_with_delivery_report(analyses_query)

    # THEN the analysis containing the delivery report should be extracted
    assert analysis in analyses


def test_filter_analyses_without_delivery_report(base_store: Store, helpers: StoreHelpers):
    """Test filtering of analysis without a delivery report generated."""

    # GIVEN an analysis with a delivery report
    analysis_without_delivery_report: models.Analysis = helpers.add_analysis(
        store=base_store, delivery_reported_at=None
    )

    # GIVEN an analysis query
    analyses_query: Query = base_store.latest_analyses()

    # WHEN calling the delivery report analysis filtering function
    analyses: Query = filter_analyses_without_delivery_report(analyses_query)

    # THEN the analysis without a delivery report should be extracted
    assert analysis_without_delivery_report in analyses


def test_filter_report_analyses_by_pipeline(
    base_store: Store, helpers: StoreHelpers, case_obj: models.Family
):
    """Test filtering delivery report related analysis by pipeline."""

    # GIVEN a set of mock analysis
    balsamic_analysis: models.Analysis = helpers.add_analysis(
        store=base_store, pipeline=Pipeline.BALSAMIC
    )
    fluffy_analysis: models.Analysis = helpers.add_analysis(
        store=base_store, case=case_obj, pipeline=Pipeline.FLUFFY
    )

    # GIVEN an analysis query
    analyses_query: Query = base_store.latest_analyses()

    # WHEN filtering delivery report related analyses
    analyses: Query = filter_report_analyses_by_pipeline(analyses_query)

    # THEN only the delivery report supported analysis should be retrieved
    assert balsamic_analysis in analyses
    assert fluffy_analysis not in analyses


def test_order_analyses_by_completed_at(
    base_store: Store,
    helpers: StoreHelpers,
    case_obj: models.Family,
    timestamp_now: datetime,
    timestamp_yesterday: datetime,
):
    """Test sorting of analyses by the completed_at field."""

    # GIVEN a set of mock analyses
    new_analysis: models.Analysis = helpers.add_analysis(
        store=base_store, completed_at=timestamp_now
    )
    old_analysis: models.Analysis = helpers.add_analysis(
        store=base_store, case=case_obj, completed_at=timestamp_yesterday
    )

    # GIVEN an analysis query
    analyses_query: Query = base_store.latest_analyses()

    # WHEN ordering the analyses by the completed_at field
    analyses: Query = order_analyses_by_completed_at(analyses_query)

    # THEN the oldest analysis should be the first one in the list
    assert old_analysis == analyses.all()[0]
    assert new_analysis == analyses.all()[1]


def test_order_analyses_by_uploaded_at(
    base_store: Store,
    helpers: StoreHelpers,
    case_obj: models.Family,
    timestamp_now: datetime,
    timestamp_yesterday: datetime,
):
    """Test sorting of analyses by the uploaded_at field."""

    # GIVEN a set of mock analyses
    new_analysis: models.Analysis = helpers.add_analysis(
        store=base_store, completed_at=timestamp_now, uploaded_at=timestamp_now
    )
    old_analysis: models.Analysis = helpers.add_analysis(
        store=base_store,
        case=case_obj,
        completed_at=timestamp_yesterday,
        uploaded_at=timestamp_yesterday,
    )

    # GIVEN an analysis query
    analyses_query: Query = base_store.latest_analyses()

    # WHEN ordering the analyses by the uploaded_at field
    analyses: Query = order_analyses_by_uploaded_at(analyses_query)

    # THEN the oldest analysis should be the first one in the list
    assert old_analysis == analyses.all()[0]
    assert new_analysis == analyses.all()[1]
