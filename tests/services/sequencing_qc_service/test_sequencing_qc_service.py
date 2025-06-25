from cg.constants.constants import SequencingQCStatus
from cg.services.sequencing_qc_service import SequencingQCService
from cg.store.models import Case, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_case_pass_sequencing_qc_microSALT_prio(base_store: Store, helpers: StoreHelpers):
    """Test that a microSALT priority case with passes sequencing QC when only one sample has data."""
    # GIVEN a microSALT priority case with two samples
    case: Case = helpers.add_case(
        base_store,
        data_analysis="microsalt",
        priority="priority",
        aggregated_sequencing_qc=SequencingQCStatus.PENDING,
    )

    # GIVEN one sample has data and one does not
    sequenced_sample: Sample = helpers.add_sample(base_store, reads=50000000)
    non_sequenced_sample: Sample = helpers.add_sample(base_store, reads=0)
    helpers.relate_samples(base_store, case, samples=[sequenced_sample, non_sequenced_sample])

    # WHEN running the sequencing QC
    service = SequencingQCService(store=base_store)
    passes_qc: bool = service.case_pass_sequencing_qc(case)

    # THEN the case should pass QC
    assert passes_qc


def test_case_pass_sequencing_qc_microSALT_resarch(base_store: Store, helpers: StoreHelpers):
    """Test that a microSALT priority case does not pass sequencing QC when only one sample has data."""
    # GIVEN a microSALT priority case with two samples
    case: Case = helpers.add_case(
        base_store,
        data_analysis="microsalt",
        priority="research",
        aggregated_sequencing_qc=SequencingQCStatus.PENDING,
    )

    # GIVEN one sample has data and one does not
    sequenced_sample: Sample = helpers.add_sample(base_store, reads=50000000)
    non_sequenced_sample: Sample = helpers.add_sample(base_store, reads=0)
    helpers.relate_samples(base_store, case, samples=[sequenced_sample, non_sequenced_sample])

    # WHEN running the sequencing QC
    service = SequencingQCService(store=base_store)
    passes_qc: bool = service.case_pass_sequencing_qc(case)

    # THEN the case should not pass QC
    assert not passes_qc
