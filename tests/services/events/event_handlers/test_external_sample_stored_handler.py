from unittest.mock import Mock, call, create_autospec

from housekeeper.store.models import Bundle
import pytest
from pytest_mock import MockerFixture

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.exc import CaseNotFoundError
from cg.models.cg_config import CGConfig
from cg.services.analysis_starter.analysis_starter import AnalysisStarter
from cg.services.analysis_starter.factories.starter_factory import AnalysisStarterFactory
from cg.services.events.event_handlers import external_sample_stored_handler
from cg.store.models import Case, Sample
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


def test_handle_starts_case(mocker: MockerFixture):
    # GIVEN a valid event payload
    event_payload: dict = {"status_db.sample_internal_id": "ACC123"}

    # GIVEN that the sample belongs to a purely external case
    status_db: Store = create_autospec(Store)
    case: Case = create_autospec(Case)
    stored_sample: Sample = create_autospec(
        Sample, case_that_delivers=case, internal_id="ACC123", is_external=True
    )
    other_sample: Sample = create_autospec(
        Sample, case_that_delivers=case, internal_id="ACC234", is_external=True
    )
    case.samples = [stored_sample, other_sample]  # type: ignore
    status_db.get_sample_by_internal_id_strict = Mock(return_value=stored_sample)

    # GIVEN that all samples in the case are stored
    housekeeper_api: TypedMock[HousekeeperAPI] = create_typed_mock(HousekeeperAPI)
    housekeeper_api.as_type.bundle = Mock(return_value=create_autospec(Bundle))

    # GIVEN a CG config
    cg_config: CGConfig = create_autospec(
        CGConfig, housekeeper_api=housekeeper_api.as_type, status_db=status_db
    )

    analysis_starter: TypedMock[AnalysisStarter] = create_typed_mock(AnalysisStarter)
    mocker.patch.object(
        AnalysisStarterFactory,
        "get_analysis_starter_for_case",
        return_value=analysis_starter.as_type,
    )

    # WHEN handling the event
    external_sample_stored_handler.handle(config=cg_config, event_payload=event_payload)

    # THEN we should have checked that all samples were indeed stored
    stored_sample_call = call("ACC123")
    other_sample_call = call("ACC234")
    assert stored_sample_call in housekeeper_api.as_mock.bundle.call_args_list
    assert other_sample_call in housekeeper_api.as_mock.bundle.call_args_list

    # THEN the case was started
    analysis_starter.as_mock.start.assert_called_once_with(case.internal_id)


def test_handle_fails_with_no_case(mocker: MockerFixture):
    # GIVEN a valid event payload
    event_payload: dict = {"status_db.sample_internal_id": "ACC123"}

    # GIVEN that the sample does not have a linked case that should deliver it
    status_db: Store = create_autospec(Store)
    sample: Sample = create_autospec(
        Sample, case_that_delivers=None, internal_id="ACC123", is_external=True
    )
    status_db.get_sample_by_internal_id_strict = Mock(return_value=sample)

    # GIVEN a CG config
    cg_config: CGConfig = create_autospec(CGConfig, status_db=status_db)

    # WHEN handling the event
    # THEN the appropraite error is raised
    with pytest.raises(CaseNotFoundError):
        external_sample_stored_handler.handle(config=cg_config, event_payload=event_payload)


# TODO: Not all samples external

# TODO: Not all samples stored

# TODO: Not all samples deliverable for case
