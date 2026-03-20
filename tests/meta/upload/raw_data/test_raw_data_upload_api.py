from pathlib import Path
from unittest.mock import create_autospec

from click import Context
from pytest_mock import MockerFixture

from cg.meta.upload.raw_data.raw_data_upload_api import RawDataUploadAPI, deliver_raw_data
from cg.models.cg_config import CGConfig
from cg.services.deliver_files.factory import DeliveryServiceFactory
from cg.store.models import Analysis, Case
from cg.store.store import Store


def test_upload_delegates(mocker: MockerFixture):
    # GIVEN a raw data case with analyses
    analyses: list[Analysis] = [create_autospec(Analysis), create_autospec(Analysis)]
    case: Case = create_autospec(Case, analyses=analyses)

    # GIVEN a module for delivering raw data
    deliver_raw_data_mock = mocker.patch.object(deliver_raw_data, "deliver_analyses")

    # GIVEN a RawDataUploadAPI instance
    config: CGConfig = create_autospec(
        CGConfig,
        status_db=create_autospec(Store),
        delivery_path="delivery_path",
        delivery_service_factory=create_autospec(DeliveryServiceFactory),
    )
    raw_data_upload_api = RawDataUploadAPI(config=config)

    # WHEN uploading the case
    raw_data_upload_api.upload(ctx=create_autospec(Context), case=case, restart=False)

    # THEN deliver_raw_data.deliver_analyses is called with the case analyses
    deliver_raw_data_mock.assert_called_once_with(
        analyses=analyses,
        status_db=raw_data_upload_api.status_db,
        delivery_path=Path("delivery_path"),
        service_builder=raw_data_upload_api.delivery_service_factory,
        dry_run=False,
    )
