from unittest import mock

import pytest

from cg.apps.lims import LimsAPI
from cg.constants import Workflow
from cg.services.orders.storing.implementations.nallo_order_service import StoreNalloOrderService
from cg.services.orders.validation.order_types.nallo.models.order import NalloOrder
from cg.store.models import Order


@pytest.fixture(autouse=True)
def mock_file_creation(nallo_order: NalloOrder):
    """Mocks run before each test in the module."""
    sample_names: list[str] = [sample.name for _, _, sample in nallo_order.enumerated_new_samples]
    name_to_id_map: dict = {
        sample_name: f"{sample_name}_internal_id" for sample_name in sample_names
    }
    with (
        mock.patch.object(LimsAPI, "submit_project", return_value={"id": 1}),
        mock.patch.object(LimsAPI, "get_samples", return_value=name_to_id_map),
    ):
        yield


def test_nallo_storing_service_success(
    nallo_order: NalloOrder, store_nallo_order_service: StoreNalloOrderService
):
    # GIVEN a valid Nallo order

    # WHEN storing the order
    store_nallo_order_service.store_order(nallo_order)

    # THEN the data should have been persisted
    order: Order | None = store_nallo_order_service.status_db.get_order_by_ticket_id(
        nallo_order._generated_ticket_id
    )
    assert order
    assert order.workflow == Workflow.NALLO
    case_names = [case.name for case in nallo_order.cases]
    assert case_names == [case.name for case in order.cases]
    sample_names = [sample.name for _, _, sample in nallo_order.enumerated_new_samples]
    assert sample_names == [sample.name for case in order.cases for sample in case.samples]
