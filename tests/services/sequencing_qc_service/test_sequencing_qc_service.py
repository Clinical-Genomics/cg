from unittest.mock import Mock, create_autospec

from pytest_mock import MockerFixture

from cg.services import sequencing_qc_service as module
from cg.services.sequencing_qc_service import SequencingQCService
from cg.store.models import Case
from cg.store.store import Store


def test_run_sequencing_qc_handles_exception(mocker: MockerFixture):
    # GIVEN a store with a case ready for sequencing QC
    store: Store = create_autospec(Store)
    case: Case = create_autospec(Case)
    store.get_cases_for_sequencing_qc = Mock(return_value=[case])

    # GIVEN a sequencing qc service
    service = SequencingQCService(store=store)

    # GIVEN that an exception is raised during quality check
    mocker.patch.object(
        module,
        "get_sequencing_quality_check_for_case",
        return_value=Mock(side_effect=Exception("BOOM!")),
    )

    # WHEN calling run_sequencing_qc
    service.run_sequencing_qc()

    # THEN no exception was raised
