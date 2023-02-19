from typing import List, Union

from alchy import Query
from cgmodels.cg.constants import Pipeline
from datetime import datetime

from cg.constants.constants import CaseActions, DataDelivery
from cg.constants.sequencing import SequencingMethod
from cg.constants.subject import PhenotypeStatus
from cg.store import Store, models
from cg.store.models import Family
from cg.store.status_case_filters import (
    get_cases_with_pipeline,
    get_cases_has_sequence,
    get_cases_for_analysis,
    get_cases_with_scout_data_delivery,
    get_report_supported_data_delivery_cases,
    get_cases_with_loqusdb_supported_pipeline,
    get_cases_with_loqusdb_supported_sequencing_method,
    get_inactive_analysis_cases,
    get_new_cases,
)
from tests.store_helpers import StoreHelpers


def test_get_cases_has_sequence(base_store: Store, helpers: StoreHelpers, timestamp_now: datetime):
    """Test that a case is returned when there is a cases with a sequenced sample."""

    # GIVEN a sequenced sample
    test_sample: models.Sample = helpers.add_sample(base_store, sequenced_at=timestamp_now)

    # GIVEN a case
    test_case = helpers.add_case(base_store)

    # GIVEN a database with a case with one sequenced samples for specified analysis
    base_store.relate_sample(test_case, test_sample, PhenotypeStatus.UNKNOWN)

    # GIVEN a cases Query
    cases: Query = base_store.get_families_with_analyses()

    # WHEN getting cases to analyse
    cases: List[Query] = list(get_cases_has_sequence(cases=cases))

    # THEN cases should contain the test case
    assert cases


def test_get_cases_has_sequence_when_external(base_store: Store, helpers: StoreHelpers):
    """Test that a case is returned when there is a case with an externally sequenced sample."""

    # GIVEN a sequenced sample
    test_sample: models.Sample = helpers.add_sample(base_store, sequenced_at=None, is_external=True)

    # GIVEN a case
    test_case = helpers.add_case(base_store)

    # GIVEN a database with a case with one sequenced samples for specified analysis
    base_store.relate_sample(test_case, test_sample, PhenotypeStatus.UNKNOWN)

    # GIVEN a cases Query
    cases: Query = base_store.get_families_with_analyses()

    # WHEN getting cases to analyse
    cases: List[Query] = list(get_cases_has_sequence(cases=cases))

    # THEN cases should contain the test case
    assert cases


def test_get_cases_has_sequence_when_not_sequenced(base_store: Store, helpers: StoreHelpers):
    """Test that no case is returned when there is a cases with sample that has not been sequenced."""

    # GIVEN a sequenced sample
    test_sample: models.Sample = helpers.add_sample(base_store, sequenced_at=None)

    # GIVEN a case
    test_case = helpers.add_case(base_store)

    # GIVEN a database with a case with one sequenced samples for specified analysis
    base_store.relate_sample(test_case, test_sample, PhenotypeStatus.UNKNOWN)

    # GIVEN a cases Query
    cases: Query = base_store.get_families_with_analyses()

    # WHEN getting cases to analyse
    cases: List[Query] = list(get_cases_has_sequence(cases=cases))

    # THEN cases should not contain the test case
    assert not cases


def test_get_cases_has_sequence_when_not_external_nor_sequenced(
    base_store: Store, helpers: StoreHelpers
):
    """Test that no case is returned when there is a cases with sample that has not been sequenced nor is external."""

    # GIVEN a sequenced sample
    test_sample: models.Sample = helpers.add_sample(
        base_store, sequenced_at=None, is_external=False
    )

    # GIVEN a case
    test_case = helpers.add_case(base_store)

    # GIVEN a database with a case with one sequenced samples for specified analysis
    base_store.relate_sample(test_case, test_sample, PhenotypeStatus.UNKNOWN)

    # GIVEN a cases Query
    cases: Query = base_store.get_families_with_analyses()

    # WHEN getting cases to analyse
    cases: List[Query] = list(get_cases_has_sequence(cases=cases))

    # THEN cases should not contain the test case
    assert not cases


def test_get_cases_with_pipeline_when_correct_pipline(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that no case is returned when there are no cases with the  specified pipeline."""

    # GIVEN a sequenced sample
    test_sample: models.Sample = helpers.add_sample(base_store, sequenced_at=timestamp_now)

    # GIVEN a cancer case
    test_case = helpers.add_case(base_store, data_analysis=Pipeline.BALSAMIC)

    # GIVEN a database with a case with one sequenced samples for specified analysis
    base_store.relate_sample(test_case, test_sample, PhenotypeStatus.UNKNOWN)

    # GIVEN a cases Query
    cases: Query = base_store.get_families_with_analyses()

    # WHEN getting cases to analyse for another pipeline
    cases: List[Query] = list(get_cases_with_pipeline(cases=cases, pipeline=Pipeline.BALSAMIC))

    # THEN cases should contain the test case
    assert cases


def test_get_cases_with_pipeline_when_incorrect_pipline(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that no case is returned when there are no cases with the  specified pipeline."""

    # GIVEN a sequenced sample
    test_sample: models.Sample = helpers.add_sample(base_store, sequenced_at=timestamp_now)

    # GIVEN a cancer case
    test_case: models.Family = helpers.add_case(base_store, data_analysis=Pipeline.BALSAMIC)

    # GIVEN a database with a case with one sequenced samples for specified analysis
    base_store.relate_sample(test_case, test_sample, PhenotypeStatus.UNKNOWN)

    # GIVEN a cases Query
    cases: Query = base_store.get_families_with_analyses()

    # WHEN getting cases to analyse for another pipeline
    cases: List[Query] = list(get_cases_with_pipeline(cases=cases, pipeline=Pipeline.MIP_DNA))

    # THEN cases should not contain the test case
    assert not cases


def test_get_cases_with_loqusdb_supported_pipeline(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test retrieval of cases that support Loqusdb upload."""

    # GIVEN a sequenced sample
    test_sample: models.Sample = helpers.add_sample(base_store, sequenced_at=timestamp_now)

    # GIVEN a MIP-DNA and a FLUFFY case
    test_mip_case: models.Family = helpers.add_case(base_store, data_analysis=Pipeline.MIP_DNA)
    test_mip_case.customer.loqus_upload = True
    test_fluffy_case: models.Family = helpers.add_case(
        base_store, name="test", data_analysis=Pipeline.FLUFFY
    )
    test_fluffy_case.customer.loqus_upload = True

    # GIVEN a database with a case with one sequenced samples for specified analysis
    base_store.relate_sample(test_mip_case, test_sample, PhenotypeStatus.UNKNOWN)
    base_store.relate_sample(test_fluffy_case, test_sample, PhenotypeStatus.UNKNOWN)

    # GIVEN a cases Query
    cases: Query = base_store.get_families_with_analyses()

    # WHEN getting cases with pipeline
    cases: List[Query] = list(get_cases_with_loqusdb_supported_pipeline(cases=cases))

    # THEN only the Loqusdb supported case should be extracted
    assert test_mip_case in cases
    assert test_fluffy_case not in cases


def test_get_cases_with_loqusdb_supported_sequencing_method(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test retrieval of cases with a valid Loqusdb sequencing method."""

    # GIVEN a sample with a valid Loqusdb sequencing method
    test_sample_wes: models.Sample = helpers.add_sample(
        base_store, sequenced_at=timestamp_now, application_type=SequencingMethod.WES
    )

    # GIVEN a MIP-DNA associated test case
    test_case_wes: models.Family = helpers.add_case(base_store, data_analysis=Pipeline.MIP_DNA)
    base_store.relate_sample(test_case_wes, test_sample_wes, PhenotypeStatus.UNKNOWN)

    # GIVEN a cases Query
    cases: Query = base_store.get_families_with_analyses()

    # WHEN retrieving the available cases
    cases: List[Query] = list(
        get_cases_with_loqusdb_supported_sequencing_method(cases=cases, pipeline=Pipeline.MIP_DNA)
    )

    # THEN the expected case should be retrieved
    assert test_case_wes in cases


def test_get_cases_with_loqusdb_supported_sequencing_method_empty(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test retrieval of cases with a valid Loqusdb sequencing method."""

    # GIVEN a not supported loqusdb sample
    test_sample_wts: models.Sample = helpers.add_sample(
        base_store, name="sample_wts", sequenced_at=timestamp_now, is_rna=True
    )

    # GIVEN a MIP-DNA associated test case
    test_case_wts: models.Family = helpers.add_case(base_store, data_analysis=Pipeline.MIP_DNA)
    base_store.relate_sample(test_case_wts, test_sample_wts, PhenotypeStatus.UNKNOWN)

    # GIVEN a cases Query
    cases: Query = base_store.get_families_with_analyses()

    # WHEN retrieving the valid cases
    cases: List[Query] = list(
        get_cases_with_loqusdb_supported_sequencing_method(cases=cases, pipeline=Pipeline.MIP_DNA)
    )

    # THEN no cases should be returned
    assert not cases


def test_get_cases_for_analysis(base_store: Store, helpers: StoreHelpers, timestamp_now: datetime):
    """Test that a case is returned when there is a cases with an action set to analyse."""

    # GIVEN a sequenced sample
    test_sample: models.Sample = helpers.add_sample(base_store, sequenced_at=timestamp_now)

    # GIVEN a completed analysis
    test_analysis: models.Analysis = helpers.add_analysis(
        base_store, completed_at=timestamp_now, pipeline=Pipeline.MIP_DNA
    )

    # Given an action set to analyze
    test_analysis.family.action: str = CaseActions.ANALYZE

    # GIVEN a database with a case with one sequenced samples for specified analysis
    base_store.relate_sample(test_analysis.family, test_sample, PhenotypeStatus.UNKNOWN)

    # GIVEN a cases Query
    cases: Query = base_store.get_families_with_analyses()

    # WHEN getting cases to analyse
    cases: List[Query] = list(get_cases_for_analysis(cases=cases))

    # THEN cases should contain the test case
    assert cases


def test_get_cases_for_analysis_when_sequenced_sample_and_no_analysis(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a case is returned when there are internally created cases with no action set and no prior analysis."""

    # GIVEN a sequenced sample
    test_sample: models.Sample = helpers.add_sample(
        base_store, sequenced_at=timestamp_now, is_external=False
    )

    # GIVEN a case
    test_case = helpers.add_case(base_store)

    # GIVEN a database with a case with one sequenced samples for specified analysis
    base_store.relate_sample(test_case, test_sample, PhenotypeStatus.UNKNOWN)

    # GIVEN a cases Query
    cases: Query = base_store.get_families_with_analyses()

    # WHEN getting cases to analyse
    cases: List[Query] = list(get_cases_for_analysis(cases=cases))

    # THEN cases should contain the test case
    assert cases


def test_get_cases_for_analysis_when_cases_with_no_action_and_new_sequence_data(
    base_store: Store,
    helpers: StoreHelpers,
    timestamp_yesterday: datetime,
    timestamp_now: datetime,
):
    """Test that a case is returned when cases with no action, but new sequence data."""

    # GIVEN a sequenced sample
    test_sample: models.Sample = helpers.add_sample(
        base_store, sequenced_at=timestamp_now, is_external=False
    )

    # GIVEN a completed analysis
    test_analysis: models.Analysis = helpers.add_analysis(base_store, pipeline=Pipeline.MIP_DNA)

    # Given an action set to None
    test_analysis.family.action: Union[None, str] = None

    # GIVEN a database with a case with one sequenced samples for specified analysis
    base_store.relate_sample(test_analysis.family, test_sample, PhenotypeStatus.UNKNOWN)

    # GIVEN an old analysis
    test_analysis.created_at = timestamp_yesterday

    # GIVEN a cases Query
    cases: Query = base_store.get_families_with_analyses()

    # WHEN getting cases to analyse
    cases: List[Query] = list(get_cases_for_analysis(cases=cases))

    # THEN cases should contain the test case
    assert cases


def test_get_cases_for_analysis_when_cases_with_no_action_and_old_sequence_data(
    base_store: Store, helpers: StoreHelpers, timestamp_yesterday: datetime
):
    """Test that a case is not returned when cases with no action, but old sequence data."""

    # GIVEN a sequenced sample
    test_sample: models.Sample = helpers.add_sample(
        base_store, sequenced_at=timestamp_yesterday, is_external=True
    )

    # GIVEN a completed analysis
    test_analysis: models.Analysis = helpers.add_analysis(base_store, pipeline=Pipeline.MIP_DNA)

    # Given an action set to None
    test_analysis.family.action: Union[None, str] = None

    # GIVEN a database with a case with one sequenced samples for specified analysis
    base_store.relate_sample(test_analysis.family, test_sample, PhenotypeStatus.UNKNOWN)

    # GIVEN a cases Query
    cases: Query = base_store.get_families_with_analyses()

    # WHEN getting cases to analyse
    cases: List[Query] = list(get_cases_for_analysis(cases=cases))

    # THEN cases should not contain the test case
    assert not cases


def test_get_cases_with_scout_data_delivery(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a case is returned when Scout is specified as a data delivery option."""

    # GIVEN a sequenced sample
    test_sample: models.Sample = helpers.add_sample(base_store)

    # GIVEN a case with Scout as data delivery
    test_case = helpers.add_case(base_store, data_delivery=DataDelivery.FASTQ_ANALYSIS_SCOUT)

    # GIVEN a database with a case with one sequenced samples for specified analysis
    base_store.relate_sample(test_case, test_sample, PhenotypeStatus.UNKNOWN)

    # GIVEN a cases Query
    cases: Query = base_store.get_families_with_analyses()

    # WHEN getting cases with Scout as data delivery option
    cases: List[Query] = list(get_cases_with_scout_data_delivery(cases=cases))

    # THEN cases should contain the test case
    assert cases


def test_get_report_supported_data_delivery_cases(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a case is returned for a delivery report supported data delivery option."""

    # GIVEN a sequenced sample
    test_sample: models.Sample = helpers.add_sample(base_store)

    # GIVEN a case with Scout and a not supported option as data deliveries
    test_case = helpers.add_case(base_store, data_delivery=DataDelivery.FASTQ_ANALYSIS_SCOUT)
    test_invalid_case = helpers.add_case(base_store, name="test", data_delivery=DataDelivery.FASTQ)

    # GIVEN a database with the test cases
    base_store.relate_sample(test_case, test_sample, PhenotypeStatus.UNKNOWN)
    base_store.relate_sample(test_invalid_case, test_sample, PhenotypeStatus.UNKNOWN)

    # GIVEN a cases Query
    cases: Query = base_store.get_families_with_analyses()

    # WHEN retrieving the delivery report supported cases
    cases: List[Query] = list(get_report_supported_data_delivery_cases(cases=cases))

    # THEN only the delivery report supported case should be retrieved
    assert test_case in cases
    assert test_invalid_case not in cases


def test_get_inactive_analysis_cases(base_store: Store, helpers: StoreHelpers):
    """Test that an inactive case is returned when there is case which has no action set."""

    # GIVEN a case
    test_case = helpers.add_case(base_store)

    # GIVEN a cases Query
    cases: Query = base_store._get_case_query()

    # WHEN getting completed cases
    cases: List[Family] = list(get_inactive_analysis_cases(cases=cases))

    # THEN cases should contain the test case
    assert cases

    assert cases[0].internal_id == test_case.internal_id


def test_get_inactive_analysis_cases_when_on_hold(base_store: Store, helpers: StoreHelpers):
    """Test that an inactivated case is returned when there is case which has action set to hold."""

    # GIVEN a case
    test_case = helpers.add_case(base_store, action=CaseActions.HOLD)

    # GIVEN a cases Query
    cases: Query = base_store._get_case_query()

    # WHEN getting completed cases
    cases: List[Family] = list(get_inactive_analysis_cases(cases=cases))

    # THEN cases should contain the test case
    assert cases

    assert cases[0].internal_id == test_case.internal_id


def test_get_inactive_analysis_cases_when_not_completed(base_store: Store, helpers: StoreHelpers):
    """Test that no case is returned when there is case which action set to running."""

    # GIVEN a case
    helpers.add_case(base_store, action=CaseActions.RUNNING)

    # GIVEN a cases Query
    cases: Query = base_store._get_case_query()

    # WHEN getting completed cases
    cases: List[Family] = list(get_inactive_analysis_cases(cases=cases))

    # THEN cases should not contain the test case
    assert not cases


def test_get_new_cases(base_store: Store, helpers: StoreHelpers, timestamp_in_2_weeks: datetime):
    """Test that an old case is returned when a future date is supplied."""

    # GIVEN a case
    test_case = helpers.add_case(base_store)

    # GIVEN a cases Query
    cases: Query = base_store._get_case_query()

    # WHEN getting completed cases
    cases: List[Family] = list(get_new_cases(cases=cases, date=timestamp_in_2_weeks))

    # THEN cases should contain the test case
    assert cases

    assert cases[0].internal_id == test_case.internal_id


def test_get_new_cases_when_too_new(
    base_store: Store, helpers: StoreHelpers, timestamp_yesterday: datetime
):
    """Test that old case is returned when a past date is supplied."""

    # GIVEN a case
    helpers.add_case(base_store)

    # GIVEN a cases Query
    cases: Query = base_store._get_case_query()

    # WHEN getting completed cases
    cases: List[Family] = list(get_new_cases(cases=cases, date=timestamp_yesterday))

    # THEN cases should not contain the test case
    assert not cases
