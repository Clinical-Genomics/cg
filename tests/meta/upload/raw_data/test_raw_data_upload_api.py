from pathlib import Path
from unittest.mock import Mock, create_autospec

from click import Context
from pytest_mock import MockerFixture

from cg.meta.upload.raw_data.raw_data_upload_api import RawDataUploadAPI, deliver_raw_data
from cg.models.cg_config import CGConfig
from cg.services.deliver_files.factory import DeliveryServiceFactory
from cg.store.models import Analysis, Case
from cg.store.store import Store


def test_upload_delegates_to_module(mocker: MockerFixture):
    # GIVEN a connection to status db
    status_db: Store = create_autospec(Store)

    # GIVEN a raw data case with a completed analysis
    analysis: Analysis = create_autospec(Analysis)
    case: Case = create_autospec(Case)
    status_db.get_latest_completed_analysis_for_case = Mock(return_value=analysis)

    # GIVEN a module for delivering raw data
    deliver_raw_data_mock = mocker.spy(deliver_raw_data, "deliver_analyses")

    # GIVEN a RawDataUploadAPI instance
    config: CGConfig = create_autospec(
        CGConfig,
        status_db=status_db,
        delivery_path="delivery_path",
        delivery_service_factory=create_autospec(DeliveryServiceFactory),
    )
    raw_data_upload_api = RawDataUploadAPI(config=config)

    # WHEN uploading the case
    raw_data_upload_api.upload(ctx=create_autospec(Context), case=case, restart=False)

    # THEN deliver_raw_data.deliver_analyses is called with the case analyses
    deliver_raw_data_mock.assert_called_once_with(
        analyses=[analysis],
        status_db=status_db,
        delivery_path=Path("delivery_path"),
        service_builder=raw_data_upload_api.delivery_service_factory,
        dry_run=False,
        raise_on_fail=True,
    )
