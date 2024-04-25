import datetime as dt

import pytest

from cg.constants import Workflow
from cg.constants.constants import PrepCategory
from cg.constants.subject import PhenotypeStatus
from cg.store.models import CaseSample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture(name="store_failing_sequencing_qc")
def store_failing_sequencing_qc(
    novaseq_6000_pre_1_5_kits_flow_cell_id: str,
    sample_id: str,
    ticket_id: str,
    timestamp_now: dt.datetime,
    helpers,
    store: Store,
) -> Store:
    """Populate a store with a Fluffy case, with a sample that has been sequenced on two flow cells."""
    store_case = helpers.add_case(
        store=store,
        internal_id="fluffy_case",
        name="fluffy_case",
        data_analysis=Workflow.FLUFFY,
    )

    store_sample = helpers.add_sample(
        store=store,
        application_type=PrepCategory.READY_MADE_LIBRARY.value,
        customer_id="fluffy_customer",
        is_tumour=False,
        internal_id="fluffy_sample",
        reads=5,
        original_ticket=ticket_id,
        last_sequenced_at=timestamp_now,
    )

    helpers.add_flow_cell(
        store=store,
        flow_cell_name=novaseq_6000_pre_1_5_kits_flow_cell_id,
        samples=[store_sample],
        date=timestamp_now,
    )

    helpers.add_relationship(store=store, case=store_case, sample=store_sample)
    helpers.ensure_sample_lane_sequencing_metrics(
        store=store,
        sample_internal_id=store_sample.internal_id,
        flow_cell_name=novaseq_6000_pre_1_5_kits_flow_cell_id,
        flow_cell_lane_number=1,
        sample_total_reads_in_lane=5,
        sample_base_percentage_passing_q30=30,
    )
    return store


@pytest.fixture(name="store_with_analyses_for_cases")
def store_with_analyses_for_cases(
    analysis_store: Store,
    helpers: StoreHelpers,
    timestamp_now: dt.datetime,
    timestamp_yesterday: dt.datetime,
) -> Store:
    """Return a store with two analyses for two cases."""
    case_one = analysis_store.get_case_by_internal_id("yellowhog")
    case_two = helpers.add_case(analysis_store, internal_id="test_case_1")

    cases = [case_one, case_two]
    for case in cases:
        oldest_analysis = helpers.add_analysis(
            analysis_store,
            case=case,
            started_at=timestamp_yesterday,
            completed_at=timestamp_yesterday,
            uploaded_at=timestamp_yesterday,
            delivery_reported_at=None,
        )
        helpers.add_analysis(
            analysis_store,
            case=case,
            started_at=timestamp_now,
            completed_at=timestamp_now,
            uploaded_at=timestamp_now,
            delivery_reported_at=None,
        )
        sample = helpers.add_sample(analysis_store, delivered_at=timestamp_now)
        link: CaseSample = analysis_store.relate_sample(
            case=oldest_analysis.case, sample=sample, status=PhenotypeStatus.UNKNOWN
        )
        analysis_store.session.add(link)

    return analysis_store
