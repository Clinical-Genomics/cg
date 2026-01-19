from unittest.mock import Mock, create_autospec

from pytest_mock import MockerFixture

from cg.services.sequencing_qc_service import SequencingQCService, sequencing_qc_service
from cg.store.models import Case
from cg.store.store import Store


def test_run_sequencing_qc_succeeds(mocker: MockerFixture):
    # GIVEN a store with a case ready for sequencing QC
    store: Store = create_autospec(Store)
    case: Case = create_autospec(Case)
    store.get_cases_for_sequencing_qc = Mock(return_value=[case])

    # GIVEN a sequencing qc service
    service = SequencingQCService(store=store)

    # GIVEN that all quality checks can run successfully
    mocker.patch.object(
        sequencing_qc_service,
        "get_sequencing_quality_check_for_case",
        return_value=Mock(),
    )

    # WHEN calling run_sequencing_qc
    result = service.run_sequencing_qc()

    # THEN the result is True
    assert result


def test_run_sequencing_qc_handles_exception(mocker: MockerFixture):
    # GIVEN a store with a case ready for sequencing QC
    store: Store = create_autospec(Store)
    case: Case = create_autospec(Case)
    store.get_cases_for_sequencing_qc = Mock(return_value=[case])

    # GIVEN a sequencing qc service
    service = SequencingQCService(store=store)

    # GIVEN that an exception is raised during quality check
    mocker.patch.object(
        sequencing_qc_service,
        "get_sequencing_quality_check_for_case",
        return_value=Mock(side_effect=Exception("BOOM!")),
    )

    # WHEN calling run_sequencing_qc
    result = service.run_sequencing_qc()

    # THEN no exception was raised
    # THEN the result is False
    assert not result
