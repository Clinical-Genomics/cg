from pathlib import Path
from unittest.mock import Mock, create_autospec

from housekeeper.store.models import File
from pyfakefs.fake_filesystem import FakeFilesystem
from sqlalchemy.orm import Query

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.constants import Workflow
from cg.services import upload_results_service
from cg.services.deliver_files.rsync.service import DeliveryRsyncService
from cg.store.models import Analysis, Case, Customer, Order
from cg.store.store import Store


def test_upload_results_trana(fs: FakeFilesystem):
    # GIVEN an analysis ready to be uploaded
    customer: Customer = create_autospec(Customer, internal_id="cust000")
    order: Order = create_autospec(Order, ticket_id=123456)
    case: Case = create_autospec(Case, customer=customer)
    case.name = "test-case"
    analysis: Analysis = create_autospec(
        Analysis, case=case, order=order, workflow=Workflow.TRANA_16S
    )


    # GIVEN HK files
    file_one: File = create_autospec(File, full_path="/path/to/file_one")
    fs.create_file("/path/to/file_one")
    file_two: File = create_autospec(File, full_path="/path/to/file_two")
    fs.create_file("/path/to/file_two")

    # GIVEN a HousekeeperAPI
    housekeeper_api: HousekeeperAPI = create_autospec(HousekeeperAPI)
    file_query: Query = create_autospec(Query)
    file_query.all = Mock(
        return_value=[file_one, file_two]
    )
    housekeeper_api.files = Mock(return_value=file_query)

    # GIVEN a StatusDB with the upload keys for the files
    status_db: Store = create_autospec(Store)
    #TODO: add two file types
    status_db.get_upload_keys = Mock(return_value=[])


    # GIVEN an DeliveryRsyncService
    rsync_service: DeliveryRsyncService = create_autospec(DeliveryRsyncService)

    # WHEN uploading the Trana results
    upload_results_service.upload_results(
        analysis=analysis,
        base_delivery_path=Path("base/delivery/path"),
        housekeeper_api=housekeeper_api,
        rsync_service=rsync_service,
        status_db=status_db,
    )

    # THEN the case_delivery_directory should have been created
    assert Path("base/delivery/path/cust000/inbox/123456/test-case").exists()

    # THEN the expected files were linked to the customer directory
    assert Path("base/delivery/path/cust000/inbox/123456/test-case/file_one").exists()
    assert Path("base/delivery/path/cust000/inbox/123456/test-case/file_two").exists()

    # THEN
    housekeeper_api.files.assert_called_once_with(file_types=[], version=)

    # THEN the files were submitted to be rsynced to the delivery server

    # THEN an RSYNC "analysis" should have been created in Trailblazer

    # THEN the upload job was added to the RSYNC "analysis" in Trailblazer

    # THEN the upload job was added to the Trana-16s analysis in Trailblazer
