from datetime import datetime

import pytest

from cg.constants.constants import SequencingQCStatus
from cg.exc import CaseNotFoundError
from cg.store.models import Case, IlluminaFlowCell, IlluminaSequencingRun
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.mark.parametrize(
    "store_with_cases",
    [
        "store_with_rna_and_dna_samples_and_cases",
        "store_with_multiple_rna_and_dna_samples_and_cases",
    ],
    ids=["single_rna_sample", "multiple_rna_samples"],
)
def test_get_uploaded_related_dna_case(
    store_with_cases: str,
    rna_case: Case,
    uploaded_related_dna_case: list[Case],
    related_dna_cases: list[Case],
    request: pytest.FixtureRequest,
):
    # GIVEN a database with an RNA case and several related DNA cases
    # GIVEN that some of the DNA cases are uploaded and others not
    store: Store = request.getfixturevalue(store_with_cases)

    # WHEN getting the related DNA cases that are uploaded
    fetched_uploaded_related_dna_case: list[Case] = store.get_uploaded_related_dna_cases(
        rna_case=rna_case,
    )

    # THEN the correct set of cases is returned
    assert set(fetched_uploaded_related_dna_case) == set(uploaded_related_dna_case)
    assert set(fetched_uploaded_related_dna_case) != set(related_dna_cases)


def test_get_case_by_internal_id_strict_works(store_with_cases_and_customers: Store):
    """Test that get_case_by_internal_id_strict returns the correct case."""
    # GIVEN a store with a case
    internal_id: str = store_with_cases_and_customers.get_cases()[0].internal_id

    # WHEN fetching the case by internal id
    case: Case = store_with_cases_and_customers.get_case_by_internal_id_strict(internal_id)

    # THEN it returns a case
    assert isinstance(case, Case)
    # THEN no errors should be raised


def test_get_case_by_internal_id_strict_fails(store_with_cases_and_customers: Store):
    """Test that looking for a case with a non-existent internal id raises an error."""

    # GIVEN a fake internal id
    internal_id: str = "fake"

    # WHEN fetching a case using the fake internal id

    # THEN the method should raise a CaseNotFoundError
    with pytest.raises(CaseNotFoundError) as error:
        store_with_cases_and_customers.get_case_by_internal_id_strict(internal_id)

    # THEN the error message should be as expected
    assert str(error.value) == f"Case with internal id {internal_id} was not found in the database."


def _add_case_for_sequencing_qc(
    store: Store,
    helpers: StoreHelpers,
    case_id: str,
    aggregated_sequencing_qc: SequencingQCStatus,
    is_external: bool,
    downsampled_to: int | None,
    last_sequenced_at: datetime | None,
    add_metrics: bool,
    sequencing_run: IlluminaSequencingRun | None = None,
    lane: int | None = None,
) -> Case:
    """Create a single case/sample setup for sequencing qc filtering tests."""
    case: Case = helpers.add_case(
        store=store,
        internal_id=case_id,
        name=case_id,
        aggregated_sequencing_qc=aggregated_sequencing_qc,
    )
    sample = helpers.add_sample(
        store=store,
        internal_id=f"{case_id}_sample",
        name=f"{case_id}_sample",
        application_tag=f"{case_id}_tag",
        is_external=is_external,
        last_sequenced_at=last_sequenced_at,
        downsampled_to=downsampled_to,
    )
    helpers.add_relationship(store=store, sample=sample, case=case)
    if add_metrics and sequencing_run and lane is not None:
        helpers.add_illumina_sample_sequencing_metrics_object(
            store=store,
            sample_id=sample.internal_id,
            sequencing_run=sequencing_run,
            lane=lane,
        )
    return case


def test_get_cases_for_sequencing_qc_filters_all_supported_scenarios(
    store: Store, helpers: StoreHelpers
):
    """Test include/exclude behavior for all sequencing qc query conditions."""

    # GIVEN one sequencing run with sample run metrics for internal samples
    flow_cell: IlluminaFlowCell = helpers.add_illumina_flow_cell(
        store=store, flow_cell_id="flow_cell_qc"
    )
    sequencing_run: IlluminaSequencingRun = helpers.add_illumina_sequencing_run(
        store=store, flow_cell=flow_cell
    )

    # GIVEN a case with PENDING QC and a sample with an internal application tag,
    # sequencing metrics, last sequenced at, and no downsampling
    included_pending_internal: Case = _add_case_for_sequencing_qc(
        store=store,
        helpers=helpers,
        case_id="case_pending_internal_processed",
        aggregated_sequencing_qc=SequencingQCStatus.PENDING,
        is_external=False,
        downsampled_to=None,
        last_sequenced_at=datetime.now(),
        add_metrics=True,
        sequencing_run=sequencing_run,
        lane=1,
    )

    # GIVEN a case with FAILED QC and a sample with an internal application tag,
    # sequencing metrics, last sequenced at, and no downsampling
    included_failed_internal: Case = _add_case_for_sequencing_qc(
        store=store,
        helpers=helpers,
        case_id="case_failed_internal_processed",
        aggregated_sequencing_qc=SequencingQCStatus.FAILED,
        is_external=False,
        downsampled_to=None,
        last_sequenced_at=datetime.now(),
        add_metrics=True,
        sequencing_run=sequencing_run,
        lane=2,
    )

    # GIVEN a case with PENDING QC and a sample with an external application tag,
    # sequencing metrics, last sequenced at, and no downsampling
    included_pending_external: Case = _add_case_for_sequencing_qc(
        store=store,
        helpers=helpers,
        case_id="case_pending_external",
        aggregated_sequencing_qc=SequencingQCStatus.PENDING,
        is_external=True,
        downsampled_to=None,
        last_sequenced_at=None,
        add_metrics=False,
        sequencing_run=sequencing_run,
        lane=3,
    )

    # GIVEN a case with PASSED QC and a sample with an external application tag,
    # sequencing metrics, last sequenced at, and no downsampling
    _add_case_for_sequencing_qc(
        store=store,
        helpers=helpers,
        case_id="case_passed_external",
        aggregated_sequencing_qc=SequencingQCStatus.PASSED,
        is_external=True,
        downsampled_to=None,
        last_sequenced_at=None,
        add_metrics=False,
        sequencing_run=sequencing_run,
        lane=4,
    )

    # GIVEN a case with PENDING QC and a sample with an internal application tag,
    # sequencing metrics, last sequenced at, and downsampling
    _add_case_for_sequencing_qc(
        store=store,
        helpers=helpers,
        case_id="case_pending_downsampled",
        aggregated_sequencing_qc=SequencingQCStatus.PENDING,
        is_external=False,
        downsampled_to=123,
        last_sequenced_at=datetime.now(),
        add_metrics=True,
        sequencing_run=sequencing_run,
        lane=5,
    )

    # GIVEN a case with FAILED QC and a sample with an internal application tag,
    # sequencing metrics, no last sequenced at, and no downsampling
    _add_case_for_sequencing_qc(
        store=store,
        helpers=helpers,
        case_id="case_failed_internal_no_last_sequenced",
        aggregated_sequencing_qc=SequencingQCStatus.FAILED,
        is_external=False,
        downsampled_to=None,
        last_sequenced_at=None,
        add_metrics=True,
        sequencing_run=sequencing_run,
        lane=6,
    )

    # GIVEN a case with PENDING QC and a sample with an internal application tag,
    # no sequencing metrics, last sequenced at, and no downsampling
    _add_case_for_sequencing_qc(
        store=store,
        helpers=helpers,
        case_id="case_pending_internal_no_metrics",
        aggregated_sequencing_qc=SequencingQCStatus.PENDING,
        is_external=False,
        downsampled_to=None,
        last_sequenced_at=datetime.now(),
        add_metrics=False,
    )

    # WHEN querying cases for sequencing qc
    fetched_cases: list[Case] = store.get_cases_for_sequencing_qc()
    fetched_case_ids: set[str] = {case.internal_id for case in fetched_cases}

    # THEN only pending/failed, non-downsampled, and post-processed internal or external cases are returned
    assert fetched_case_ids == {
        included_pending_internal.internal_id,
        included_failed_internal.internal_id,
        included_pending_external.internal_id,
    }
