from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from housekeeper.store.models import File
from pyfakefs.fake_filesystem import FakeFilesystem
from pytest_mock import MockerFixture
from sqlalchemy.orm import Query

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.tb.api import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants.constants import Workflow
from cg.constants.priority import Priority, TrailblazerPriority
from cg.constants.tb import AnalysisStatus, AnalysisType
from cg.exc import MissingFilesError
from cg.services import upload_results_service
from cg.services.deliver_files.rsync.service import DeliveryRsyncService
from cg.services.upload_results_service import os as upload_os
from cg.store.models import Analysis, Case, Customer, Order, UploadKeys
from cg.store.store import Store
from tests.services.analysis_starter.tracker.test_microsalt_tracker import trailblazer_api
from tests.services.file_delivery.rsync.conftest import rsync_service
from tests.typed_mock import TypedMock, create_typed_mock


def test_upload_results_trana(fs: FakeFilesystem):
    # GIVEN an analysis ready to be uploaded
    customer: Customer = create_autospec(Customer, internal_id="cust000")
    order: Order = create_autospec(Order, ticket_id=123456)
    case: Case = create_autospec(
        Case, customer=customer, internal_id="case_1", priority=Priority.priority
    )
    case.name = "test-case"
    analysis: Analysis = create_autospec(
        Analysis,
        case=case,
        case_internal_id="case_1",
        housekeeper_version_id=123666,
        order=order,
        order_id=12,
        trailblazer_id=53,
        workflow=Workflow.TRANA_16S,
    )

    # GIVEN HK files
    file_one: File = create_autospec(File, full_path="/path/to/file_one")
    fs.create_file("/path/to/file_one")
    file_two: File = create_autospec(File, full_path="/path/to/file_two")
    fs.create_file("/path/to/file_two")

    # GIVEN a HousekeeperAPI
    housekeeper_api: HousekeeperAPI = create_autospec(HousekeeperAPI)
    file_query: Query = create_autospec(Query)
    file_query.all = Mock(return_value=[file_one, file_two])
    housekeeper_api.files = Mock(return_value=file_query)

    # GIVEN a StatusDB with the upload keys for the files
    status_db: Store = create_autospec(Store)
    status_db.get_upload_keys = Mock(
        return_value=[
            create_autospec(UploadKeys, file_type="file-type-1"),
            create_autospec(UploadKeys, file_type="file-type-2"),
        ]
    )

    # GIVEN a TrailblazerAPI
    trailblazer_api: TypedMock[TrailblazerAPI] = create_typed_mock(TrailblazerAPI)
    trailblazer_api.as_type.add_pending_analysis = Mock(
        return_value=create_autospec(TrailblazerAnalysis, id=1)
    )

    # GIVEN an DeliveryRsyncService
    rsync_service: TypedMock[DeliveryRsyncService] = create_typed_mock(
        DeliveryRsyncService, log_dir=Path("/path/to/rsync/log/dir")
    )
    rsync_service.as_type.run_rsync_for_analysis = Mock(return_value=93)

    # WHEN uploading the Trana results
    upload_results_service.upload_results(
        analysis=analysis,
        base_delivery_path=Path("base/delivery/path"),
        housekeeper_api=housekeeper_api,
        rsync_service=rsync_service.as_type,
        status_db=status_db,
        trailblazer_api=trailblazer_api.as_type,
    )

    # THEN the case_delivery_directory should have been created
    assert Path("base/delivery/path/cust000/inbox/123456/test-case").exists()

    # THEN the expected files were linked to the customer directory
    assert Path("base/delivery/path/cust000/inbox/123456/test-case/file_one").exists()
    assert Path("base/delivery/path/cust000/inbox/123456/test-case/file_two").exists()

    # THEN we query housekeeper with the correct parameters
    housekeeper_api.files.assert_called_once_with(
        file_types=["file-type-1", "file-type-2"], version=123666
    )

    # THEN the files were submitted to be rsynced to the delivery server
    rsync_service.as_mock.run_rsync_for_analysis.assert_called_once_with(
        analysis=analysis,
        folders_to_deliver={Path("base/delivery/path/cust000/inbox/123456/test-case")},
    )

    # THEN an RSYNC "analysis" should have been created in Trailblazer
    trailblazer_api.as_mock.add_pending_analysis.assert_called_once_with(
        case_id="case_1_rsync",
        analysis_type=AnalysisType.OTHER,
        config_path="",
        order_id=12,
        out_dir="/path/to/rsync/log/dir",
        priority=TrailblazerPriority.HIGH,
        workflow=Workflow.RSYNC,
        ticket="123456",
    )

    # THEN the upload job was added to the RSYNC "analysis" in Trailblazer
    trailblazer_api.as_mock.add_upload_job_to_analysis.assert_any_call(analysis_id=1, slurm_id=93)

    # THEN the upload job was added to the Trana-16s analysis in Trailblazer
    trailblazer_api.as_mock.add_upload_job_to_analysis.assert_any_call(analysis_id=53, slurm_id=93)


def test_upload_results_no_upload_keys(mocker: MockerFixture):
    # GIVEN a store without upload keys for the analysis
    status_db: Store = create_autospec(Store)
    status_db.get_upload_keys = Mock(return_value=[])

    # GIVEN a HousekeeperAPI
    housekeeper_api: TypedMock[HousekeeperAPI] = create_typed_mock(HousekeeperAPI)

    # GIVEN a TrailblazerAPI
    trailblazer_api: TypedMock[TrailblazerAPI] = create_typed_mock(TrailblazerAPI)

    # GIVEN a spy on link
    link_spy = mocker.spy(upload_os, "link")

    # GIVEN
    rsync_service: TypedMock[DeliveryRsyncService] = create_typed_mock(DeliveryRsyncService)

    # WHEN uploading the results
    # THEN a MissingFilesError should be raised
    with pytest.raises(MissingFilesError):
        upload_results_service.upload_results(
            analysis=create_autospec(Analysis, case_internal_id="case_1"),
            base_delivery_path=Path("base/delivery/path"),
            housekeeper_api=housekeeper_api.as_type,
            rsync_service=rsync_service.as_type,
            status_db=status_db,
            trailblazer_api=trailblazer_api.as_type,
        )

    # THEN Housekeeper is not called
    housekeeper_api.as_mock.files.assert_not_called()

    # THEN link is not called
    link_spy.assert_not_called()

    # THEN there is no rsync
    rsync_service.as_mock.run_rsync_for_analysis.assert_not_called()

    # THEN no Trailblazer request was made
    trailblazer_api.as_mock.add_pending_analysis.assert_not_called()
    trailblazer_api.as_mock.add_upload_job_to_analysis.assert_not_called()

    # THEN the Trailblazer status should have been set to failed
    trailblazer_api.as_mock.set_analysis_status.assert_called_once_with(
        case_id="case_1", status=AnalysisStatus.FAILED
    )
