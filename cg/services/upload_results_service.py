import logging
import os
from pathlib import Path
from typing import cast

from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.tb.api import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants import Workflow
from cg.constants.tb import AnalysisType
from cg.meta.workflow.utils.utils import MAP_TO_TRAILBLAZER_PRIORITY
from cg.services.deliver_files.rsync.service import DeliveryRsyncService
from cg.store.models import Analysis, Case, UploadKeys
from cg.store.store import Store

LOG = logging.getLogger(__name__)


def upload_results(
    analysis: Analysis,
    base_delivery_path: Path,
    housekeeper_api: HousekeeperAPI,
    rsync_service: DeliveryRsyncService,
    status_db: Store,
    trailblazer_api: TrailblazerAPI,
):
    _upload_to_customer_inbox(
        analysis=analysis,
        base_delivery_path=base_delivery_path,
        housekeeper_api=housekeeper_api,
        rsync_service=rsync_service,
        status_db=status_db,
        trailblazer_api=trailblazer_api,
    )


def _upload_to_customer_inbox(
    analysis: Analysis,
    base_delivery_path: Path,
    housekeeper_api: HousekeeperAPI,
    rsync_service: DeliveryRsyncService,
    status_db: Store,
    trailblazer_api: TrailblazerAPI,
):

    case_delivery_directory: Path = _create_case_delivery_directory(
        analysis=analysis, base_delivery_path=base_delivery_path
    )
    linked_analysis_files: list[Path] = _link_analysis_files(
        analysis=analysis,
        case_delivery_directory=case_delivery_directory,
        housekeeper_api=housekeeper_api,
        status_db=status_db,
    )

    if linked_analysis_files:
        slurm_job_id: int = rsync_service.run_rsync_for_analysis(
            analysis=analysis, folders_to_deliver={case_delivery_directory}
        )

        tb_rsync_analysis: TrailblazerAnalysis = trailblazer_api.add_pending_analysis(
            case_id=f"{analysis.case_internal_id}_rsync",
            analysis_type=AnalysisType.OTHER,
            config_path="",
            order_id=analysis.order_id,
            out_dir=rsync_service.log_dir.as_posix(),
            priority=MAP_TO_TRAILBLAZER_PRIORITY[analysis.case.priority],
            workflow=Workflow.RSYNC,
            ticket=str(analysis.order.ticket_id),
        )

        trailblazer_api.add_upload_job_to_analysis(
            analysis_id=tb_rsync_analysis.id, slurm_id=slurm_job_id
        )

        trailblazer_api.add_upload_job_to_analysis(
            analysis_id=cast(int, analysis.trailblazer_id), slurm_id=slurm_job_id
        )


def _create_case_delivery_directory(analysis: Analysis, base_delivery_path: Path) -> Path:
    case: Case = analysis.case
    case_delivery_directory = Path(
        base_delivery_path,
        case.customer.internal_id,
        "inbox",
        str(analysis.order.ticket_id),
        case.name,
    )
    case_delivery_directory.mkdir(parents=True, exist_ok=True)

    return case_delivery_directory


def _link_analysis_files(
    analysis: Analysis,
    case_delivery_directory: Path,
    housekeeper_api: HousekeeperAPI,
    status_db: Store,
) -> list[Path]:

    upload_keys_list: list[UploadKeys] = status_db.get_upload_keys(
        workflow=analysis.workflow, upload_to_customer_inbox=True
    )
    if not upload_keys_list:
        LOG.warning(
            f"No upload keys to upload to customer inbox found for case: {analysis.case_internal_id}"
        )
        return []

    file_types: list[str] = [upload_keys.file_type for upload_keys in upload_keys_list]

    files: list[File] = housekeeper_api.files(
        file_types=file_types, version=analysis.housekeeper_version_id
    ).all()

    linked_paths = list()
    for file in files:
        source_path = Path(file.full_path)
        destination_path = Path(case_delivery_directory, source_path.name)
        linked_paths.append(destination_path)
        os.link(src=source_path, dst=destination_path)
    return linked_paths
