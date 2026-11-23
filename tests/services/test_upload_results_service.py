from pathlib import Path
from unittest.mock import Mock, create_autospec

from pyfakefs.fake_filesystem import FakeFilesystem

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

    # GIVEN

    # GIVEN a HousekeeperAPI
    housekeeper_api: HousekeeperAPI = create_autospec(HousekeeperAPI)
    housekeeper_api.files = Mock(return_value="")

    # GIVEN a StatusDB
    status_db: Store = create_autospec(Store)

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

    # THEN the files were submitted to be rsynced to the delivery server

    # THEN an RSYNC "analysis" should have been created in Trailblazer

    # THEN the upload job was added to the RSYNC "analysis" in Trailblazer

    # THEN the upload job was added to the Trana-16s analysis in Trailblazer
