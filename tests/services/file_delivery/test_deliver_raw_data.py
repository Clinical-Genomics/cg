from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, call, create_autospec

import pytest

from cg.constants.constants import DataDelivery
from cg.services.deliver_files import deliver_raw_data
from cg.services.deliver_files.deliver_files_service.deliver_files_service import (
    DeliverFilesService,
)
from cg.services.deliver_files.factory import DeliveryServiceFactory
from cg.store.models import Analysis, Case
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


@pytest.mark.freeze_time
def test_deliver_analyses_succeeds():
    # GIVEN two raw data cases with corresponding analyses
    raw_data_case_1: Case = create_autospec(Case, data_delivery=DataDelivery.RAW_DATA_SCOUT)
    raw_data_case_2: Case = create_autospec(Case, data_delivery=DataDelivery.RAW_DATA_SCOUT)

    analysis_1: Analysis = create_autospec(Analysis, id=1, case=raw_data_case_1)
    analysis_2: Analysis = create_autospec(Analysis, id=2, case=raw_data_case_2)

    # GIVEN a deliver files service
    deliver_files_service: TypedMock[DeliverFilesService] = create_typed_mock(DeliverFilesService)

    # GIVEN a delivery service factory that builds the service
    delivery_service_factory: DeliveryServiceFactory = create_autospec(DeliveryServiceFactory)
    delivery_service_factory.build_delivery_service = Mock(
        return_value=deliver_files_service.as_type
    )

    # GIVEN a delivery path
    delivery_path = Path("delivery")

    # GIVEN a status_db
    status_db: TypedMock[Store] = create_typed_mock(Store)

    # WHEN delivering analyses
    deliver_raw_data.deliver_analyses(
        [analysis_1, analysis_2],
        status_db=status_db.as_type,
        delivery_path=delivery_path,
        service_builder=delivery_service_factory,
        dry_run=False,
    )

    # THEN files are delivered for each case
    deliver_files_service.as_mock.deliver_files_for_case.assert_has_calls(
        [
            call(case=raw_data_case_1, delivery_base_path=delivery_path, dry_run=False),
            call(case=raw_data_case_2, delivery_base_path=delivery_path, dry_run=False),
        ]
    )

    # THEN upload started at is updated for each analysis
    status_db.as_mock.update_analysis_upload_started_at.assert_has_calls(
        [
            call(analysis_id=1, upload_started_at=datetime.now()),
            call(analysis_id=2, upload_started_at=datetime.now()),
        ]
    )


def test_deliver_analyses_file_delivery_fails():
    # GIVEN a raw data case with a corresponding analysis
    raw_data_case: Case = create_autospec(Case, data_delivery=DataDelivery.RAW_DATA_SCOUT)

    analysis: Analysis = create_autospec(Analysis, id=1, case=raw_data_case)

    # GIVEN a deliver files service that raises an exception
    deliver_files_service: TypedMock[DeliverFilesService] = create_typed_mock(DeliverFilesService)
    deliver_files_service.as_type.deliver_files_for_case = Mock(
        side_effect=Exception("Some random error")
    )

    # GIVEN a delivery service factory
    delivery_service_factory = create_autospec(DeliveryServiceFactory)
    delivery_service_factory.build_delivery_service = Mock(
        return_value=deliver_files_service.as_type
    )

    # GIVEN a delivery path
    delivery_path = Path("delivery")

    # GIVEN a status_db
    status_db: TypedMock[Store] = create_typed_mock(Store)

    # WHEN delivering analyses
    deliver_raw_data.deliver_analyses(
        [analysis],
        status_db=status_db.as_type,
        delivery_path=delivery_path,
        service_builder=delivery_service_factory,
        dry_run=False,
    )

    # THEN upload started at is reset to None for the failed analysis
    status_db.as_mock.update_analysis_upload_started_at.assert_called_with(
        analysis_id=1, upload_started_at=None
    )
