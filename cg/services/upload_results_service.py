import os
from pathlib import Path

from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.tb.api import TrailblazerAPI
from cg.services.deliver_files.rsync.service import DeliveryRsyncService
from cg.store.models import Analysis, Case, UploadKeys
from cg.store.store import Store


def upload_results(
    analysis: Analysis,
    base_delivery_path: Path,
    housekeeper_api: HousekeeperAPI,
    rsync_service: DeliveryRsyncService,
    status_db: Store,
    trailblazer_api: TrailblazerAPI
):
    _upload_to_customer_inbox(
        analysis=analysis,
        base_delivery_path=base_delivery_path,
        housekeeper_api=housekeeper_api,
        rsync_service=rsync_service,
        status_db=status_db,
    )


def _upload_to_customer_inbox(
    analysis: Analysis,
    base_delivery_path: Path,
    housekeeper_api: HousekeeperAPI,
    rsync_service: DeliveryRsyncService,
    status_db: Store,
):
    case: Case = analysis.case
    case_delivery_directory = Path(
        base_delivery_path,
        case.customer.internal_id,
        "inbox",
        str(analysis.order.ticket_id),
        case.name,
    )

    _link_analysis_files(
        analysis=analysis,
        case_delivery_directory=case_delivery_directory,
        housekeeper_api=housekeeper_api,
        status_db=status_db,
    )

    rsync_service.run_rsync_for_analysis(
        analysis=analysis, folders_to_deliver={case_delivery_directory}
    )
    # TODO Add RSYNC analysis to Trailblazer
    # TODO Add upload job to the new rsync trailblazer analysis
    # TODO Add upload job to the main trailblazer analysis


def _link_analysis_files(
    analysis: Analysis,
    case_delivery_directory: Path,
    housekeeper_api: HousekeeperAPI,
    status_db: Store,
) -> None:

    case_delivery_directory.mkdir(parents=True, exist_ok=True)

    upload_keys: list[UploadKeys] = status_db.get_upload_keys(
        workflow=analysis.workflow, upload_to_customer_inbox=True
    )
    file_types: list[str] = [key.file_type for key in upload_keys]

    files: list[File] = housekeeper_api.files(
        file_types=file_types, version=analysis.housekeeper_version_id
    ).all()

    for file in files:
        source_path = Path(file.full_path)
        destination_path = Path(case_delivery_directory, source_path.name)
        os.link(src=source_path, dst=destination_path)
